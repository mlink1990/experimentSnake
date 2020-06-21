# -*- coding: utf-8 -*-
"""
Hardware action to use JDS6600 with experiment snake
"""
from __future__ import division
import logging
import socket

import hardwareAction

logger=logging.getLogger("ExperimentSnake.hardwareAction.jds6600")

class JDS6600Client:    
    def __init__(self, port=8888, IP_ADDRESS = "192.168.16.77"):
        self.PORT = port
        self.bufferSize = 1024
        self.IP_ADDRESS = IP_ADDRESS
        self.timeoutTime = 5.0 #seconds
               
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.IP_ADDRESS, self.PORT))
        self.socket.settimeout(self.timeoutTime)
        # return self.receive() # TODO: add some error handlers
    def close(self):
        # Python wrapper for closing connection (socket) with controller.
        self.socket.close()
    def reconnect(self):
        # Python wrapper for reconnecting connection with the controller.
        self.close()
        self.connect()
        
    def send(self, commandString):
        self.socket.sendall(commandString)

    def receive(self):
        try:
            data=self.socket.recv(self.bufferSize)
            return data
        except socket.timeout:
            return "SOCKET TIMEOUT"


class JDS6600HWA(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(JDS6600HWA,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"JDSFrequency":"JDSFrequency","JDSBurstCount":"JDSBurstCount"}
        self.hardwareActionName = 'jds6600-quenchcoilModulation'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.connection = JDS6600Client()
        self.connection.connect()
        self.connection.send("<init_awg()>")
        ret = self.connection.receive()
        self.connection.close()
        if ret == "True" or True:
            self.initialised=True
            return "%s init successful" % self.hardwareActionName
        return '<font color="red">%s init error, received message:%s</font>' % (self.hardwareActionName, ret)

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "connection"):
            self.connection.send("<close_awg()>")
            self.connection.close()
            self.initialised=False
            logger.info( "%s closed" % self.hardwareActionName)
        else:
            logger.warning("could not find connection attribute to close")
        return "%s closed" % self.hardwareActionName
        
    def callback(self):
        """This is the function that is called every sequence at the callbackTime. 
        IT SHOULD NOT HANG as this is a blocking function call. You need to handle
        threading yourself if the callback function would take a long time to return.
        Return value should be a string to be printed in terminal"""
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            self.snakeReference.mainLog.addLine("%s not initialised" % (self.NAME) ,4)
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:#YOUR CALLBACK CODE SHOULD GO IN THIS TRY BLOCK!
            # read variables
            self.finalVariables = self.mapVariables()
            frequency = self.finalVariables["JDSFrequency"]
            burstCount = self.finalVariables["JDSBurstCount"]
            # send to jds-rpi
            self.connection.connect()
            self.connection.send(
                "<set_params({},0,0,{})>".format(frequency,burstCount)
            ) # TODO: Add some checks, if commands were successful
            self.connection.close()
            return "callback on %s completed" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        