# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 17:39:56 2015

@author: tharrison
"""

# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""

import hardwareAction
import MXGAgilentGenerator
import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.GreyMollassesOffsetFreq")

class GreyMollassesOffset(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(GreyMollassesOffset,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"SnakeGreyMollassesOffsetFreq":"SnakeGreyMollassesOffsetFreq"} # CHANGE THIS LINE!  maps name in experiment control to names used in python callback. Make sure all required variables are defined!
        self.hardwareActionName = 'grey-mollasses-offset'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.initialised=True
        self.agilentMixer = MXGAgilentGenerator.MXG(name="TCPIP0::192.168.16.90::inst0::INSTR")
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "agilentMixer"):
            self.agilentMixer.close()
        else:
            logger.info("Agilent Mixer was not initialised so I will not close it")
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
            freq = self.finalVariables["SnakeGreyMollassesOffsetFreq"]
            self.agilentMixer.setFreqGHz(freq)
            return "frequency changed to %s GHz. callback on %s completed" % (freq,self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        