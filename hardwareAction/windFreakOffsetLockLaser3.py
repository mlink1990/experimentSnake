# -*- coding: utf-8 -*-
"""
Hardware module which connects to raspberry pi, which talks to windfreak-1to6. 
"""
import logging
import xmlrpclib
import socket # handle timeouts

import hardwareAction

logger=logging.getLogger("ExperimentSnake.hardwareAction.windFreak")

class WindFreak(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(WindFreak,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"LiLaser3OffsetLockFreqMHz":"LiLaser3OffsetLockFreqMHz"}
        self.hardwareActionName = 'windFreak-li-laser3-offsetLock'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.ADDRESS = 'http://192.168.16.79:2324'
        self.windFreakConnectionRC = xmlrpclib.ServerProxy(self.ADDRESS)
        # read frequency to test connection
        oldTimeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(2) # 2 s timeout
        try:
            freq = self.windFreakConnectionRC.getFrequency("A")
            self.initialised=True
            return "{} init successful; getFrequency() returned {} (This can be inaccurate, since we use sweeps)".format(self.hardwareActionName, freq)
        except Exception as e:
            self.snakeReference.mainLog.addLine("{} failed init.".format(self.hardwareActionName),3)
            self.initialised=False
            return "{} - exception: {}".format( self.hardwareActionName, str(e) )
        finally:
            socket.setdefaulttimeout(oldTimeout)

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        self.initialised=False
        return "%s closed" % self.hardwareActionName
        
    def callback(self):
        """This is the function that is called every sequence at the callbackTime. 
        IT SHOULD NOT HANG as this is a blocking function call. You need to handle
        threading yourself if the callback function would take a long time to return.
        Return value should be a string to be printed in terminal"""
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:#YOUR CALLBACK CODE SHOULD GO IN THIS TRY BLOCK!
            self.finalVariables = self.mapVariables()
            response = self.windFreakConnectionRC.sweep_to("A", self.finalVariables["LiLaser3OffsetLockFreqMHz"])
            self.snakeReference.mainLog.addLine(str(response),2)
            return "callback on %s completed" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        