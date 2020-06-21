# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""
import pyArdDAC
import hardwareAction
import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.hardwareActionTemplate")

class AOMChannel(hardwareAction.HardwareAction,object):
    """Helpful parent class so that you can quickly write a hardware action
    that controls an AOM channel"""
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(AOMChannel,self).__init__(callbackTimeInSequence,**traitsDict)
#       THESE VARIABLES MUST BE DEFINED BY CHILD
#       self.variableName 
#       self.hardwareActionName 
#       self.channelNumber 
#       self.VCOName
#       self.channelType
#       self.AOMBox_IP
#       self.AOMBox_Name
        self.variableMappings = {self.variableName:"AOMChannelVoltage"} #maps name in experiment control to names used in python callback. Make sure all required variables are defined!
        logger.info( "%s object created successfully" % self.hardwareActionName )

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.AOMBoxConnection = pyArdDAC.ARD_DAC(HOST=self.AOMBox_IP, PORT=8888, DEBUG=False)#connects to arduino in High frequency Na AOM box
        #channel number should be defined in subclass
        self.INTEGER_MIN = 0
        self.INTEGER_MAX = 65535
        self.VOLTAGE_MIN = 0.0
        self.VOLTAGE_MAX = 5.0
        self.initialised=True
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "AOMBoxConnection" ):
            del self.AOMBoxConnection
        return "%s closed" % self.hardwareActionName
   
    def callback(self):
        """This is the function that is called every sequence at the callbackTime. 
        IT SHOULD NOT HANG as this is a blocking function call. You need to handle
        threading yourself if the callback function would take a long time to return.
        Return value should be a string to be printed in terminal"""
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:
            self.finalVariables = self.mapVariables()
            logger.debug("final variables = %s" % self.finalVariables)
            setpointInteger = self.getIntegerFromVoltage(self.finalVariables["AOMChannelVoltage"])
            self.AOMBoxConnection.SetDAC(self.channelNumber, setpointInteger)#sends to AOM box via UDP see pyArdDAC for details. External triggering not supported
            return "%s: %s voltage on %s (%s) set to %g Volts" % (self.hardwareActionName, self.channelType, self.VCOName,self.AOMBox_Name, self.finalVariables["AOMChannelVoltage"])
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        
    def getIntegerFromVoltage(self, voltage):
        """used in the AOM box callbacks. It simply converts a 0-5V to a DAC integer """
        if voltage>5.0 or voltage<0.0:
            raise ValueError("voltage value sent to attenuation channel was invalid. voltage must be 0<Voltage<5 but received voltage = %s "% voltage)
        return int(voltage*self.INTEGER_MAX/self.VOLTAGE_MAX)
        