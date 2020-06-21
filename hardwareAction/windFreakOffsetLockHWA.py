# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""

import hardwareAction
import logging
import windFreakClient

logger=logging.getLogger("ExperimentSnake.hardwareAction.windFreak")

class WindFreak(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(WindFreak,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"LiOffsetLockStartFreqMHz":"LiOffsetLockStartFreqMHz","LiOffsetLockEndFreqMHz":"LiOffsetLockEndFreqMHz","LiOffsetLockSweepTimeSec":"LiOffsetLockSweepTimeSec","LiOffsetLockResolutionMHz":"LiOffsetLockResolutionMHz"} # CHANGE THIS LINE!  maps name in experiment control to names used in python callback. Make sure all required variables are defined!
        self.hardwareActionName = 'windFreak-offsetLock'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.IP_ADDRESS = "192.168.16.34"
        self.PORT = 8888
        self.windFreakConnection = windFreakClient.Connection(IP_ADDRESS=self.IP_ADDRESS, port=self.PORT)
        self.initialised=True
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "windFreakConnection"):
            self.windFreakConnection.close()
            self.initialised=False
            logger.info( "%s closed" % self.hardwareActionName)
        else:
            logger.warning("could not find windFreakConnection attribute to close")
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
            startFrequencyMHz = self.finalVariables["LiOffsetLockStartFreqMHz"]
            endFrequencyMHz = self.finalVariables["LiOffsetLockEndFreqMHz"]
            stepSizeMHz = self.finalVariables["LiOffsetLockResolutionMHz"]
            sweepLengthTime = self.finalVariables["LiOffsetLockSweepTimeSec"]
            returnCheck = self.windFreakConnection.connect()
            logger.debug("return check value was %s " %  returnCheck)
            self.windFreakConnection.clearQueue()
            retval1 = self.windFreakConnection.sweep2(startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime)
            logger.info("sweep1 ret value %s" % retval1)
            retval2 = self.windFreakConnection.sweep2(endFrequencyMHz,startFrequencyMHz,stepSizeMHz,sweepLengthTime)
            logger.info("sweep2 ret value %s" % retval2)
            sweepMessage = "WindFreak sweep startFrequencyMHz=%s,endFrequencyMHz=%s,stepSizeMHz=%s,sweepLengthTime=%s on 1st trigger and back on 2nd trigger" % (startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime)
            self.snakeReference.mainLog.addLine(sweepMessage,2)
            self.windFreakConnection.close()
            return "callback on %s completed" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        