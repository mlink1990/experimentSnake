# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""

import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.hardwareAction")

#GUI Imports
import traits.api as traits
import traitsui.api as traitsui 
import pyface

import os

class HardwareAction(traits.HasTraits):
    """Parent class for all hardware actions. User must make a subclass of this for each
    hardware action and overwrite init, close and callback methods where necessary. Other
    functions can use the parent class implementation directly"""
    callbackTime = traits.Float()
    variables = traits.List()
    variablesReference = {}# leave empty. This will be set to the experiment control variables before the call back is executed. This is all taken care of by the snake
    hardwareActionName = traits.Str()
    examineVariablesButton = traits.Button()
    enabled = traits.Bool(True)
    callbackTimeVariableDependent = False # if true the calbackTime argument is a variable to be parsed in the snake
    callbackTimeString = None # gets populated if callbackTimeInSequence is a string
    snakeReference = None# reference to the snake object so that we can call update functions for e.g. examineVariablesDict pane
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(HardwareAction,self).__init__(**traitsDict)
        if type(callbackTimeInSequence) is float:
            self.callbackTime = callbackTimeInSequence # time in the sequence when call back should be performed passed during constructions
        elif type(callbackTimeInSequence) is str:#here we check if callback time is a timing edge or a variable
            self.callbackTimeVariableDependent = True
            self.callbackTimeString = callbackTimeInSequence
            logger.info( "CallbackTime string detected attempting to parse string as timing edge or variable" )
        else:
            self.callbackTime = callbackTimeInSequence # time in the sequence when call back should be performed passed during constructions
        self.awaitingCallback = True # goes to False after it has been called back for the final time in a sequence (usually once)
        self.callbackCounter = 0 # number of times called back this sequence
        self.initialised = False # set to true if init run. set to false if close run
        logger.info( "HardwareAction Super class __init__ completed" )
    
    def _variables_default(self):
        """uses the variable mappings dictionary defined in the subclass """
        return self.variableMappings.keys()

    def setVariablesDictionary(self, variables):
        """sets the variables reference to the latest variables dictionary. simply sets the variables reference attribute """        
        self.variablesReference=variables
    
    def mapVariables(self):
        """returns a dictionary of python variable names used in the callback function
        with their correct values for this run. Raises an error if a variable is missing.
        Could potentially implement default values here"""
        logger.debug( "variables in %s: %s" % (self.hardwareActionName,self.variablesReference))
        try:
            return {self.variableMappings[key]:self.variablesReference[key] for key in self.variableMappings.iterkeys()}
        except KeyError as e:
            raise e # defaults handling TODO  
            
    def parseCallbackTime(self):
        """if callback Time is a string we comprehend it as a timing edge name or variable name"""
        if self.callbackTimeString in self.snakeReference.timingEdges:
            self.callbackTime = self.snakeReference.timingEdges[self.callbackTimeString]
        elif self.callbackTimeString in self.snakeReference.variables:
            self.callbackTime = self.snakeReference.variables[self.callbackTimeString]
        else:
            raise KeyError("callbackTime %s was not found in either the timing edges or variables dictionary. Check Spelling? Could not initialise %s object" % (self.callbackTimeString, self.hardwareActionName))

    #####USER SHOULD OVERWRITE THE BELOW FUNCTIONS IN SUBCLASS AS REQUIRED
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.initialised=True
        logger.warning("Using default init as no init method has been defined in Hardware Action Subclass")
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        logger.warning("Using default close as no close method has been defined in Hardware Action Subclass")
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
            raise NotImplementedError("the callback function needs to be implemented in your subclass")
            return "callback on %s completed" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        
    def _enabled_changed(self):
        """traitsui handler function (is automatically called when enabled changes during interaction with user interface """
        if self.enabled:
            self.snakeReference.mainLog.addLine("%s was just enabled. Will perform its init method" % self.hardwareActionName,1)
            self.awaitingCallback=False # by setting this to False we prevent the action being performed till the next sequence begins. This is usually desireable            
            self.init()
        elif not self.enabled:
            if self.snakeReference.isRunning:#only print to log if it's disabled while snake is running
                self.snakeReference.mainLog.addLine("%s was just disabled. Will perform its close method" % self.hardwareActionName,1)
            self.close()#close method always performed for safety
            
    def _examineVariablesButton_fired(self):
        """Called when user clicks on book item near hardware action name. This makes a pop up
        which shows all the variables that the hardware action defines. later it might let users
        edit certain parameters"""
        self.snakeReference.updateExamineVariablesDictionary(self)# pass the update this hardwareAction object as the argument
        logger.info("variables = %s" % self.variables)
    
    #traits_view for all hardware actions. Just shows the name and lets the user enable or disable        
    traits_view = traitsui.View(
                    traitsui.HGroup(traitsui.Item("hardwareActionName", show_label=False, style="readonly"),
                                    traitsui.Item("enabled",show_label=False),
                                    traitsui.Item("examineVariablesButton",show_label=False,
                                                  editor=traitsui.ButtonEditor(image = pyface.image_resource.ImageResource( os.path.join(os.getcwd(), 'icons', 'book.png' ))),
                                                   style="custom"), 
                                   )
                               )