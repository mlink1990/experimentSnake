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
    
class DECADSServer():
    def __init__( self, myHWI, clientSocket ):
        # store the HWI class
        self.myHWI = myHWI
        
        # store the socket connected to the client
        self.clientSocket = clientSocket 
        
        # store a stream representation of this socket
        self.clientStream = clientSocket.makefile()

        # Lock to stop a response from being sent simultaniously from multiple threads
        self.sendResponseLock = threading.Lock()
        
        self.localTimeOffset = 0
        
        # start the server loop
        self.start()

    def start( self ):
        # read the incoming null terminated string (the first thing that is sent)
        incomingName = readUntilZero( self.clientStream )
        incomingName = incomingName[:-1] # remove the zero termination character for pythonic convenience
        
        # check that the name matches the name of the instance
        if( self.myHWI.hwiName != "" and incomingName != self.myHWI.hwiName ):
            print "Received bad HWI name: " + incomingName
            self.reportError( "Bad HWI name: " + incomingName + " vs " + self.myHWI.hwiName )
            print "Resetting instance..."
        else:
            
            print "Connection accepted: " + incomingName
            self.clientStream.write( pack( "26s", "HIMOL Connection Accepted" ) ) # reply handshake
            self.clientStream.write( pack( "6s", "" ) ) # send six zeros? important?
            self.clientStream.flush()           
            
            # move into the main loop
            self.mainLoop()

    def mainLoop( self ):
        # this loop is where the server spends all its idle time
        while(1):       
            # here we set no timeout for the packet length:
            #  if we get data, continue on with the rest of the loop
            #  if we receive struct.error: terminate connection
            self.clientSocket.settimeout( None ) 
            try:
                # the first 4 bytes of a communication is the length of the following packet
                # recv is used on the socket so that closing works smoothly (instead of read on stream)
                packetLength = unpack( "I", self.clientSocket.recv(4) ) [0]
                assert packetLength > 0, "Received zero length packet... strange."
            except struct.error: # this exception is thrown when the socket reads EOF,
                # i.e. the socket is closed by the client
                print "EOF received. Terminating connection."
                break;
            except Exception as e: # If any other exception happen, die gracefully
                print "Unexpected exception: "
                print type(e), e
                print "Terminating connection."
                break;

            
            # set a 1 second timeout to read entire packet
            # under normal circumstances the client should not take this long during transfer
            # so this probably means something is wrong with my implementation
            self.clientSocket.settimeout( 1.0 ) 
            
            # init an empty stream to buffer the packet
            packetStream = StringIO.StringIO()
            try:
                # try to read the whole packet into the buffer
                packetStream.write( self.clientStream.read( packetLength ) )
                # then seek to the start again for convenience
                packetStream.seek( 0 )
            except socket.timeout:
                # if this exception is thrown, then we have timed out, so terminate connection.
                print "Data transfer timed out before complete packet was sent. Terminating connection."
                break
                
            # now the whole packet has been read in, parse it:
            
            packetHeader = unpack( "B", packetStream.read(1) )[0] # read the header byte
            
            if( packetHeader == packetHeader_functionListRequest ): # Console asks for the list of functions
                # initilise a packet buffer
                outputBuffer = self.startPacket( packetHeader_functionListAnswer )
                # load the function list (defined in the HWI) into the buffer
                self.myHWI.functionList.encodeStructure( outputBuffer )
                # send the packet
                self.flushPacket( outputBuffer )
                
            elif packetHeader == packetHeader_executeFunctionRequest: # Console requests us to execute a function
                # call our execute method in a new thread
                # this means that the HWI function can spend as long as it wants doing whatever
                # and the server will still respond
                # ... python threads are pretty cool :3
                executionThread = threading.Thread( target = self.executeFunction, args = ( packetStream, ) )
                executionThread.start() # this doesn't block
        
            elif packetHeader == packetHeader_resetRequest: # reset server
                print "Received reset command."

                if "reset" in dir( self.myHWI ):
                    self.myHWI.reset()
                
                
            elif packetHeader == packetHeader_terminateRequest: # terminate connection
                print "Received terminate command. Resetting instance..."
                # breaking here takes us out of the main loop
                break
                
            elif packetHeader == packetHeader_syncClock: # sync local clock
                # the first byte determines the mode of operation
                mode = unpack( "B", packetStream.read(1) )[0]
            
                if( mode == 1 ):
                    # syncPutTo
                    self.syncPutTo( packetStream )
                    
                    
                elif( mode == 2 ):
                    # syncGetFrom
                    print "not done"
                else:
                    print "Unidentified mode in syncClock: %r" % mode
                
            else: # unknown command
                print "Received unknown command. Doing nothing."
                self.reportError( "Received unknown command: " + repr( packetHeader ) + ". Doing nothing." )


    def executeFunction( self, packetStream ):
        # this method is called whenever the client asks us to execute a function
        
        # read the function index to be executed
        n = unpack( "I", packetStream.read(4) )[0]  
        assert n < self.myHWI.functionList.n, "DECADSServer.execute function %r is out of range" % n

        inputs = None

        # read in the inputs
        if( self.myHWI.functionList.functions[ n ].inputs != None ):
            inputs = self.myHWI.functionList.functions[ n ].inputs.newDataInstanceFromStream( packetStream ) 
    
        # execute function
        try:
            self.myHWI.functionList.functions[ n ].execute( self, inputs )
        except Exception, e:
            print "Error in execution of function %r" % self.myHWI.functionList.functions[ n ].name
            raise

        # finish thread execution
    
    
    def syncPutTo( self, packetStream ):

        # 1 uint16 of year
        year = unpack( "H", packetStream.read(2) )[0]
    
        # 1 uint16 of month
        month = unpack( "H", packetStream.read(2) )[0]
        
        # 1 uint16 of day
        day = unpack( "H", packetStream.read(2) )[0]

        # 1 uint16 of hour
        hour = unpack( "H", packetStream.read(2) )[0]

        # 1 uint16 of minute
        minute = unpack( "H", packetStream.read(2) )[0]

        # 1 uint16 of second
        second = unpack( "H", packetStream.read(2) )[0]     
        
        # 1 uint16 of millisecond
        millisecond = unpack( "H", packetStream.read(2) )[0]    
    
        newTime = [ year, month, day, hour, minute, second, 0,0,-1]
        newEpochTime = time.mktime( newTime ) + millisecond*0.001
        
        nowEpochTime = time.time()
        self.localTimeOffset = newEpochTime - nowEpochTime
        print "Offset = %r"%self.localTimeOffset

    
        print str(day)+"/"+str(month)+"/"+str(year)+" "+str(hour)+":"+str(minute)+":"+str(second)+"."+str(millisecond)
    
        
    def startPacket( self, packetHeader ):
        "This method provides a stream and writes the packetHeader to the first byte. Returns the init'd stream"
        outputBuffer = StringIO.StringIO()
        outputBuffer.write( pack( "B", packetHeader ) )
        return outputBuffer
    
    def flushPacket( self, outputBuffer ):
        "This method sends the data within the provided packetBuffer, calculating the length and sending it first."
        messageLength = outputBuffer.tell()
        # send length
        self.clientStream.write( pack( "I", messageLength ) )
        # send data
        self.clientStream.write( outputBuffer.getvalue() )
        # flush stream
        self.clientStream.flush()
        
    def reportError( self, errorMessage ):
        "This method sends an error message to the DECADS client."
        print "Sending error: " + errorMessage
        outputBuffer = self.startPacket( packetHeader_errorMessage )
        outputBuffer.write( errorMessage )
        self.flushPacket( outputBuffer )
        

def sendFunctionResponse( server, functionDefinition ):
        "Sends a DECADS function response containing the output data of the supplied function"

        # Acquire the lock so that we know we are the only ones sending data now
        server.sendResponseLock.acquire()
        
        # initialise a packet buffer
        outputBuffer = server.startPacket( packetHeader_executeFunctionAnswer ) 
        # encode a uint32 of the function index
        outputBuffer.write( pack( "I", functionDefinition.functionIndex ) )
        # encode the function data
        functionDefinition.encodeOutputData( outputBuffer )
        # send the packet
        server.flushPacket( outputBuffer )

        # Release the lock
        server.sendResponseLock.release()


#######################
### Simple server code
#######################

import signal

_terminate = False


def simpleServer( hwiObject ):
    # Starts a DECADS server with 'no frills'.
    # hwiObject needs to have the following members:
    #
    #   hwiObject.hwiName : the name that this associated with this HWDM. \
    #                       Can be "" in order to accept everything.
    #
    #   hwiObject.hwiPort : the port that this HWDM will listen on.
    #
    #   hwiObject.hwiMaxConnections : the maximum number of concurrent \
    #                       connections that this HWDM will support.
    #
    #   hwiObject.functionList : a hwiFunctionList object containing the \
    #       DECADS functions that this HWDM provides.


    # Helper function to start a server thread used within simpleServer
    def startServer( hwiObject, clientSocket ):

        # If the hwi object does not have this field, then create it
        if hasattr( hwiObject, 'hwiOpenConnections' ) is False:
            hwiObject.hwiOpenConnections = 0

        # Check if we are not at the connection limit
        if( hwiObject.hwiOpenConnections < hwiObject.hwiMaxConnections ):
            print "starting connection"
            hwiObject.hwiOpenConnections = hwiObject.hwiOpenConnections + 1
            myServer = DECADSServer( hwiObject, clientSocket )
            print "stopping connection"
            hwiObject.hwiOpenConnections = hwiObject.hwiOpenConnections - 1
            clientSocket.close()
            del clientSocket
        else:
            print "Maximum number of connections reached, closing connection."
            del clientSocket

    # Helper function to initialise the listening socket
    def initServerSocket( port ):

        try:
            listeningSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        except socket.error, message:
            print "Couldn't create socket: " + str( message[0] ) + ", " + message[1]
            input("Press enter to close.")
            exit


        listeningSocket.bind( ( "", port ) ) # bind the socket to our port
        listeningSocket.listen( 1 ) # set the socket to listen
        
        return listeningSocket



    # Handler called when the user tries to quit the program
    def SIGINT_Handler( signal, frame ):
        global _terminate
        print "Received SIGINT. Exiting gracefully..."
        _terminate = True

    # Register the ctrl-c interrupt handler
    signal.signal( signal.SIGINT, SIGINT_Handler )

    print "Starting server socket"

    # Initialise the listening socket
    listeningSocket = initServerSocket( hwiObject.hwiPort )
    # Set a 1 second timeout on the listening socket so that when the user tries to quit
    # it will quit within this timeout
    listeningSocket.settimeout( 1.0 ) 
    

    # Keep looping unless the hwi is terminating
    while( 1 ):
        try:
            # Wait for a client to connect, 'accept' will block until a client connects
            clientSocket, address = listeningSocket.accept()

            # If a client connects, remove the timeout
            clientSocket.settimeout( None )
            # Print a message
            print "Incoming connection from " + repr( address )
            
            # Start execution of the server instance in a new thread
            clientThread = threading.Thread( target = startServer, args = ( hwiObject, clientSocket, ) )
            #clientThread.daemon = True
            clientThread.start()

            # Return back into the loop, ready to accept another connection
        
        except socket.timeout:
            # If the 'accept' receives a timeout, check the terminate status
            # If terminate is true, then we should leave the loop
            if( _terminate == True ):
                break
            else:
                continue

    # Finish up
    print "Stopping server socket"  
    listeningSocket.close()

    print "Server thread exiting"



