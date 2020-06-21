# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime, timedelta

import pandas as pd

import hardwareAction

logger=logging.getLogger("ExperimentSnake.hardwareAction.Watchdog")

flagPath = os.path.join("N:","Lab Monitoring","Flags","Watchdog","Flag.csv")

class WatchdogHWA(hardwareAction.HardwareAction):
    """ Not a real HWA, this just checks if the last flag of our watchdog is recent and if it contains any errors.
    If this is the case, give out a warning to the snake console."""
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(WatchdogHWA,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {} # no variables needed
        self.hardwareActionName = 'watchdog'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.initialised=True
        self.variables = []
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""

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
            if not os.path.exists(flagPath):
                self.snakeReference.mainLog.addLine("{}: Flag not found.".format(self.hardwareActionName) ,4)
                return "Please debug path!"
            if datetime.fromtimestamp( os.path.getmtime(flagPath) ) - datetime.now() > timedelta(days=2):
                self.snakeReference.mainLog.addLine("{}: Flag older than two days.".format(self.hardwareActionName) ,4)
                return "Please debug watchdog script or raspberrypi!"
            df = pd.read_csv(flagPath)
            logger.info( "Watchdog flag: "+ str(df) )
            df = df[df["Status"]!="Nominal"]
            if len(df):
                self.snakeReference.mainLog.addLine("{}: Issues detected:".format(self.hardwareActionName) ,4)
                for row in df:
                    self.snakeReference.mainLog.addLine( row["Category"] + ": " + row["Message"] ,4)
                return "Please review issues!"
            return "callback on %s completed, no issues detected" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        