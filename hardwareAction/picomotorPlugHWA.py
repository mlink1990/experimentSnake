"""
This Hardware Action talks to the Picomotor mirror controlling the optical plug
picomotor mirror
"""

import hardwareAction
import picomotorCommunication
import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.hardwareActionTemplate")

class PicomotorPlug(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(PicomotorPlug,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"SnakePicoPlugHorizontalPosition":"SnakePicoPlugHorizontalPosition","SnakePicoPlugVerticalPosition":"SnakePicoPlugVerticalPosition"} # CHANGE THIS LINE!  maps name in experiment control to names used in python callback. Make sure all required variables are defined!
        self.hardwareActionName = 'pico-plug-position'
        self.picomotor=None
        self.horizontalAxis = 1
        self.verticalAxis = 2
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.picomotor = picomotorCommunication.Picomotor(picomotorCommunication.TCP_IP_PICOMOTOR_PLUG)
        connectionResult = self.picomotor.connect()
        self.originalPositionH = self.picomotor.askPosition(self.horizontalAxis)
        self.originalPositionV = self.picomotor.askPosition(self.verticalAxis)
        if connectionResult:
            self.initialised=True
            return "%s init successful. (original position = (%s,%s))" % (self.hardwareActionName, self.originalPositionH, self.originalPositionV)
        else:
            return "%s init failed. Most likely a socket error. see above" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        try:
            if self.picomotor is not None:
                self.picomotor.close()
                return "%s closed" % self.hardwareActionName
        except AttributeError as e:
            return "%s was never created, could not be closed "  % self.hardwareActionName
        else:
            return "%s was never created, could not be closed "  % self.hardwareActionName
        
    def callback(self):
        """This is the function that is called every sequence at the callbackTime. 
        IT SHOULD NOT HANG as this is a blocking function call. You need to handle
        threading yourself if the callback function would take a long time to return.
        Return value should be a string to be printed in terminal"""
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:#could update so that it doesn't send the message if the position is the samee, but the motor does that check automatically
            self.finalVariables = self.mapVariables()
            horizontalPosition = int(self.finalVariables["SnakePicoPlugHorizontalPosition"])
            verticalPosition = int(self.finalVariables["SnakePicoPlugVerticalPosition"])
                        
            self.picomotor.absoluteMove(self.horizontalAxis, horizontalPosition)
            self.picomotor.absoluteMove(self.verticalAxis, verticalPosition)
            return " %s : moved horizontal axis to pos=%s and vertical axis to pos=%s" % (self.hardwareActionName,horizontalPosition,verticalPosition)            
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        