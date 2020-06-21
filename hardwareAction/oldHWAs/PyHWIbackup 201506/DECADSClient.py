#!/usr/bin/python

# This file contains confidential information regarding the inner workings of
# DECADS which is property of SCONDAQ GmbH. Do not copy without express
# permission from either the SCONDAQ GmbH or the author (T. Ballance). This file
# is not to be distributed under any circumstances.
# Copyright Tim Ballance 2013



import array
import struct
import StringIO
import time
import sys

import socket
import threading

from DECADSTypes import *



def readUntilZero( stream ):
    "Read from a stream until a null byte is sent. Returns null terminated string."
    data = ""
    while len( data ) == 0 or data[-1] != unichr(0):
        data = data + stream.read(1)
    return data


    
# These are the packet header constants defined by Zipkes
packetHeader_functionListRequest = 9
packetHeader_functionListAnswer = 10
packetHeader_executeFunctionRequest = 11
packetHeader_executeFunctionAnswer = 12
packetHeader_errorMessage = 13
packetHeader_resetRequest = 16
packetHeader_terminateRequest = 17
packetHeader_syncClock = 21

# postInitExecute is a function pointer which will be executed once when the functionList has been initialised
# This function is executed in a separate thread.
class DECADSClientConnection():
    def __init__( self, name, address, port, blocking=True, postInitExecute=None ):
    
        # server name, not null terminated
        self.serverName = name
        self.serverAddress = address
        self.serverPort = port
        self.connected = False
        self.functionListInitialised = False
        
        self.quit = 0
        
        self.connect( blocking, postInitExecute )

    def __del__ ( self ):
        self.close()
        

    def connect( self, blocking=True, postInitExecute=None ):
        # Initiated the decads connection
        self.serverSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        
        # Set timeout for connection
        self.serverSocket.settimeout( 1.0 ) 
        
        # Attempt a connection
        try:
            self.serverSocket.connect( (self.serverAddress, self.serverPort) )
        except socket.error as e:
            print "Connection error, check server address and port"
            return
        except socket.timeout:
            print "Connection timeout, check server is working properly"
            return
            
        self.serverStream = self.serverSocket.makefile()

        # Send server name, need to add single null termination
        self.serverSocket.send( self.serverName + "\0" )
        
        # Wait of 32bytes of "HIMOL connection accepted..."
        try:
            acceptedResponse = self.serverSocket.recv( 32 ) 
        except socket.error:
            print "Connection not accepted by remote server, terminating connection"
            self.serverSocket.close()
            return
    
        if( acceptedResponse[0:26] != "HIMOL Connection Accepted\0" ):
            print "Incorrect response from server, terminating connection"
            print acceptedResponse
            for c in acceptedResponse:
                print hex(ord(c)),
            print "\n",
            self.serverSocket.shutdown(1)
            self.serverSocket.close()
            return
        
        # Send the function list request
        packetBuffer = self.startPacket( packetHeader_functionListRequest )
        self.flushPacket( packetBuffer )
        
        self.connected = True
        
        # Create a condition object and make sure we acquire it before the recv
        # thread can get it
        self.initCondition = threading.Condition()

        if postInitExecute is not None:
            waitThread = threading.Thread( target=self.waitForInitThreadFunction, args=(postInitExecute,) )
            waitThread.daemon = True
            waitThread.start()
        
        if blocking is True:
            self.initCondition.acquire()
        
        # Start the receive thread
        self.recvThread = threading.Thread( target = self.recvThreadFunction, args = () )
        self.recvThread.daemon = True
        self.recvThread.start()

        # If we are supposed to wait until the server responds with a function list, do so
        if blocking is True:
            self.initCondition.wait()
            self.initCondition.release()
        
    def close( self ):
        # Terminate the connection
        
        if self.connected:
            self.connected = False
            self.functionListInitialised = False
            self.serverSocket.shutdown(1)
            self.serverSocket.close()

    # This function is executed in a separate thread. WHen the functionList is initialised
    # the postInitExecute function will be called then the thread will exit.
    def waitForInitThreadFunction( self, postInitExecute ):
        if self.functionListInitialised is False:
            self.initCondition.acquire()
            self.initCondition.wait()
            self.initCondition.release()
        postInitExecute()
        return
        
    def startPacket( self, packetHeader ):
        "This method provides a stream and writes the packetHeader to the first byte. Returns the init'd stream"
        outputBuffer = StringIO.StringIO()
        outputBuffer.write( pack( "B", packetHeader ) )
        return outputBuffer
    
    def flushPacket( self, outputBuffer ):
        "This method sends the data within the provided packetBuffer, calculating the length and sending it first."
        messageLength = outputBuffer.tell()
        # send length
        self.serverStream.write( pack( "I", messageLength ) )
        # send data
        self.serverStream.write( outputBuffer.getvalue() )
        # flush stream
        self.serverStream.flush()    
        
    def executeFunction( self, function, inputs, blocking=True ):
        # This executes a function on the server. The function argument
        # needs to match the function definition in the functionList
        
        # Start preparing the packet
        packetBuffer = self.startPacket( packetHeader_executeFunctionRequest )
        
        # Send the function index
        packetBuffer.write( pack("I", function.functionIndex ) )
        
        # Now send the input data
        function.encodeInputData( packetBuffer, inputs )
        
        if blocking is True:
            self.functionConditionList[ function.functionIndex ].acquire()
        try:
            # Send the packet
            self.flushPacket( packetBuffer )
        except socket.error:
            print "Socket error in executeFunction %s", function.name
            return
        
        if blocking is True:
            self.functionConditionList[ function.functionIndex ].wait()
            self.functionConditionList[ function.functionIndex ].release()
        
    def recvThreadFunction( self ):
        # This function is executed by the recv thread
        # After connection, all data reception is handled here
        
        if self.connected == False:
            # If there isn't a connection, don't do anything
            return
        
        self.serverSocket.settimeout( 1.0 )
    
        while(1):
            #  if we get data, continue on with the rest of the loop
            #  if we receive struct.error: terminate connection
    
            if self.quit == 1:
                self.quit = 2
                break
    
            try:
                # the first 4 bytes of a communication is the length of the following packet
                a = self.serverSocket.recv(4)
                packetLength = unpack( "I", a ) [0]
                assert packetLength > 0, "Received zero length packet... strange."
            except struct.error as e: # this exception is thrown when the socket reads EOF,
                # i.e. the socket is closed by the server
                print "%s connection closed." % (self.serverName)
                break
            except socket.timeout:
                continue
            except Exception as e: # If any other exception happen, die gracefully
                if self.connected == False and type(e) is socket.error:
                    # If this client has been told to disconnect and we get a socket.error
                    # this is expected because I cannot find a nice way of signalling to this
                    # thread that it should close. In the mean time, die without complaining
                    # an error
                    break;
                else:
                    print "Unexpected exception: "
                    print type(e), e
                    print "Terminating connection."
                    break;

            # set a 5 second timeout to read entire packet
            # under normal circumstances the client should not take this long during transfer
            # so this probably means something is wrong with my implementation
            self.serverSocket.settimeout( 5.0 )     

            # init an empty stream to buffer the packet
            packetStream = StringIO.StringIO()
            try:
                # try to read the whole packet into the buffer
                packetStream.write( self.serverStream.read( packetLength ) )
                # then seek to the start again for convenience
                packetStream.seek( 0 )
            except socket.timeout:
                # if this exception is thrown, then we have timed out, so terminate connection.
                print "Data transfer timed out before complete packet was received. Terminating connection."
                break
                
            # now the whole packet has been read in, parse it:
            
            packetHeader = unpack( "B", packetStream.read(1) )[0] # read the header byte
            
            if( packetHeader == packetHeader_functionListAnswer ): # Server replying with its list of functions

                # Process the received function list
                self.processFunctionList( packetStream )
            
            elif packetHeader == packetHeader_executeFunctionAnswer: # Server optionally sends the response of a function
                
                # Read in the function index
                functionIndex = unpack( "I", packetStream.read(4) )[0]
                
                # Parse in the data
                self.functionList.functions[ functionIndex ].decodeOutputData( packetStream )
                #print "Got function response"
                # First call any callbacks
                for callback in self.functionCallbackList[ functionIndex ]:
                    #print "Callback"
                    callback( self.functionList.functions[ functionIndex ] )
                
                # Trigger any waiting threads
                self.functionConditionList[ functionIndex ].acquire()
                self.functionConditionList[ functionIndex ].notifyAll()
                self.functionConditionList[ functionIndex ].release()

            elif packetHeader == packetHeader_errorMessage:
                print "Server sent error message: ",
                try:
                    print str(packetStream.read())
                except Exception, e:
                    print "<could not print error message>"
                    print str(e)
                    packetStream.seek(0)
                    for c in packetStream.read():
                        print "%0.2x " % ord(c),
                    print "\n",

    # Called to process a received function list
    def processFunctionList( self, packetStream ):
                        
        # Parse the function list data
        self.functionList = hwiFunctionList.decodeStructure( packetStream )

        # Create function lock list
        self.functionConditionList = []
        for i in range( 0, self.functionList.n ):
            self.functionConditionList.append( threading.Condition() )

        # Create function callback list
        self.functionCallbackList =  [ [] for i in range(0,self.functionList.n) ]

        # Fefine function prototype
        def makeFunctionPrototype( n ):

            def functionPrototype( self, blocking=True, *args ):

                # Check that the number of args is correct
                if self.functionList.functions[n].inputs.n != len(args):
                    print 'Bad number of arguments for function %s. (%i needed, vs %i given)' \
                          % (self.functionList.functions[n].name,
                           self.functionList.functions[n].inputs.n,
                           len(args) )
                    return

                # Set the inputs
                inputs = self.functionList.functions[n].inputs.copy()
                for i in range( 0, len(args) ):
                    # Set the i'th argument
                    inputs.args[i].set( args[i] )

                # Execute the function
                self.executeFunction( self.functionList.functions[n], inputs, blocking )

                outputs = self.functionList.functions[n].outputs
                # If there are no output arguments, return nothing
                if outputs.n == 0:
                    return

                # Otherwise return the args
                returnTuple = ()
                for i in range( 0, outputs.n ):
                    returnTuple = returnTuple + ( outputs.args[i].get(), )
                                                 
                return returnTuple
            return functionPrototype                                    
                
        # Now define all the function prototypes
        for i in range( 0, self.functionList.n ):

            # Make the prototype                                     
            functionPrototype = makeFunctionPrototype( i )

            # Check if the function name is already in use
            if self.functionList.functions[i].name in dir(self):
                # If it is, warn the user and return without employing it
                print 'Bad function name for python API: %s. It is safe to ignore this message.' \
                      % self.functionList.functions[i].name

            self.__dict__[ self.functionList.functions[i].name ] = \
                types.MethodType( functionPrototype, self, DECADSClientConnection )

        self.functionListInitialised = True

        # Now notify any listeners that we have finished reading in the function list
        self.initCondition.acquire()
        self.initCondition.notifyAll()
        self.initCondition.release()
        
            
    def waitForFunction( self, function ):
        # This function will sleep until the decads server sends a response to the specified function.
        # N.B. This could be never.
        
        # Wait for the function response event
        #self.functionEventList[ function.functionIndex ].wait()

        self.functionConditionList[ functionIndex ].acquire()
        self.functionConditionList[ functionIndex ].wait()
        self.functionConditionList[ functionIndex ].release()
        
        return
        
    def registerFunctionReturnCallback( self, function, callback ):

        if isinstance(function, hwiFunction):
            locatedFunction = function
        else:
            locatedFunction = self.findFunctionFromName( function )

        self.functionCallbackList[ locatedFunction.functionIndex ].append( callback )
        
    def unregisterFunctionReturnCallback( self, function, callback ):
        
        print callback
        print self.functionCallbackList[ function.functionIndex ]
        print (callback == self.functionCallbackList[ function.functionIndex ][0] )
        
        self.functionCallbackList[ function.functionIndex ] = filter(lambda item: item != callback, self.functionCallbackList[ function.functionIndex ] )
        
        print callback
        print self.functionCallbackList[ function.functionIndex ]

    def findFunctionFromName( self, functionName ):
        # Returns the function descriptor corresponding to the given name

        for function in self.functionList.functions:   
            if function.name == functionName:
                return function

        # If we get here, there is no function with this name
        raise Exception("NameError","No DECADS function with given name")

    def reset( self ):
        # Call this to send a reset request to the server
        
        # Init a reset request
        packetBuffer = self.startPacket( packetHeader_resetRequest )

        # No data required
        
        # Send the packet
        self.flushPacket( packetBuffer )

