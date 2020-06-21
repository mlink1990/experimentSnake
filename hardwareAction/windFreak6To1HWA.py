# -*- coding: utf-8 -*-
"""
windFreak6To1HWA for 6to1 transition. This is a magnetic landau-zener-sweep. The windfreak provides a fixed frequency and fixed power.
"""

import hardwareAction
import logging
import windFreakClient
import highFieldImaging.highFieldImaging 

logger=logging.getLogger("ExperimentSnake.hardwareAction.windFreak")

class WindFreak(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(WindFreak,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"RFSweep61WindFreakency":"RFSweep61WindFreakency",
        "RFSweep61WindFreakPower":"RFSweep61WindFreakPower"} 
        self.hardwareActionName = 'windFreak-6to1'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.IP_ADDRESS = "192.168.16.55"
        self.PORT = 8888
        self.windFreakConnection = windFreakClient.ConnectionConstantFrequency(IP_ADDRESS=self.IP_ADDRESS, port=self.PORT)        
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
            frequency = self.finalVariables["RFSweep61WindFreakency"]
            power = self.finalVariables["RFSweep61WindFreakPower"]

            returnCheck = self.windFreakConnection.connect()
            logger.debug("connect ret value %s" % returnCheck)
            retval1 = self.windFreakConnection.setPower(power)
            logger.debug("setPower ret value %s" % retval1)
            retval2 = self.windFreakConnection.setFrequency(frequency)
            logger.debug("setFrequency ret value %s" % retval2)
            Message = "{}: Power set to {:.2f}, frequency set to {:.6f}".format(self.hardwareActionName, power, frequency)
            self.snakeReference.mainLog.addLine(Message,2)
            self.windFreakConnection.close()
            return "callback on %s completed" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)

    
if __name__=="__main__":
    print "example usage: imagingFieldShift(6, 100)"
