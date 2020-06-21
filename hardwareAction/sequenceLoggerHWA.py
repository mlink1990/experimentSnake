# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""

import hardwareAction
import logging
import os
import shutil
import traceback
logger=logging.getLogger("ExperimentSnake.hardwareAction.hardwareActionTemplate")

class SequenceLogger(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(SequenceLogger,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {} # CHANGE THIS LINE!  maps name in experiment control to names used in python callback. Make sure all required variables are defined!
        self.hardwareActionName = 'sequence-logger'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal

        For sequence logger we do not need to do any initialisation        
        """
        self.currentSequenceFile = os.path.join("\\\\ursa","AQOGroupFolder","Experiment Humphry","Experiment Control And Software","currentSequence", "latestSequence.xml")
        self.lastSequenceFile = os.path.join("\\\\ursa","AQOGroupFolder","Experiment Humphry","Experiment Control And Software","currentSequence", "secondLatestSequence.xml")
        self.initialised=True
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start

        For sequence logger we do not need to do any closing        
        """
        return "%s closed" % self.hardwareActionName
        
    def callback(self):
        """This is the function that is called every sequence at the callbackTime. 
        IT SHOULD NOT HANG as this is a blocking function call. You need to handle
        threading yourself if the callback function would take a long time to return.
        Return value should be a string to be printed in terminal

        Takes the xmlString attribute from snake reference and writes it to file        
        """
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:#YOUR CALLBACK CODE SHOULD GO IN THIS TRY BLOCK!
            #self.finalVariables = self.mapVariables()#DO NOT need any variables for this HWA
            logger.debug("attempting to open latestSequence.xml and write xml data")
            if os.path.exists(self.currentSequenceFile):
                shutil.copy(self.currentSequenceFile, self.lastSequenceFile) # buffer latest sequence
            with open(self.currentSequenceFile, "wb") as latestXMLFile:
                latestXMLFile.write(self.snakeReference.xmlString)
            return "Full XML file of this sequence written to latestSequence.xml"
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            traceback.print_exc()
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        