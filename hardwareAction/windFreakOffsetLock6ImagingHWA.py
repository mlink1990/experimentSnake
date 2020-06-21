# -*- coding: utf-8 -*-
"""
windFreakOffsetLock for high field imaging. Same as our standard windfreak
hardware action but the end frequency is calculated based on the feshbach field
and 0 field resonance parameters.You can also put in an additional detuning. 

At the moment it is set up to only work for the 3/2 3/2 (6 state). It would be easy
 to get the equations from the Mathematica sheet and make it work for any state 
 e.g. a variable = 1 to 6 which is the state we want to image

The ramp structure (start to end and back is the same as always)
"""

import hardwareAction
import logging
import windFreakClient
import highFieldImaging.highFieldImaging 
import time

logger=logging.getLogger("ExperimentSnake.hardwareAction.windFreak")

class WindFreak(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(WindFreak,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"LiOffsetLockLaser3ImagingFreqMHz":"LiOffsetLockLaser3ImagingFreqMHz",
                                 "LiOffsetLockLaser3PowerdB":"LiOffsetLockLaser3PowerdB",
                                 "DipoleTrapImagingFieldBGauss":"DipoleTrapImagingFieldBGauss"}
#        {"LiOffsetLockSnakeImagingDetuningMHz":"LiOffsetLockSnakeImagingDetuningMHz",
#        "LiOffsetLockSnakeImaging0FieldResonanceMHz":"LiOffsetLockSnakeImaging0FieldResonanceMHz",
#        "LiOffsetLockSweepTimeSec":"LiOffsetLockSweepTimeSec",
#        "LiOffsetLockResolutionMHz":"LiOffsetLockResolutionMHz",
#        "DipoleTrapImagingFieldBGauss":"DipoleTrapImagingFieldBGauss",
#        "LiOffsetLockSnakeState":"LiOffsetLockSnakeState",
#        "LiOffsetLockSnakePolarisation":"LiOffsetLockSnakePolarisation"} 
        self.hardwareActionName = 'windFreak-offsetLock-laser3-6imaging'
        logger.info( "%s object created successfully" % self.hardwareActionName)
        
    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.IP_ADDRESS = "192.168.16.58"
        self.PORT = 8888
        self.windFreakConnection = windFreakClient.Connection(IP_ADDRESS=self.IP_ADDRESS, port=self.PORT)
        self.windFreakConnection.connect()
        self.initialised=True
        self.validStates = [1,2,3,4,5,6]
        self.validPolarisations = [-1,0,1]
        self.highFieldImaging = highFieldImaging.highFieldImaging.HighFieldImaging()
        self.highFieldImaging.load()
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
            endFrequencyMHz = self.finalVariables["LiOffsetLockLaser3ImagingFreqMHz"]
            power = self.finalVariables["LiOffsetLockLaser3PowerdB"] 
            BFieldGauss = self.finalVariables["DipoleTrapImagingFieldBGauss"] 
            self.windFreakConnection.send("POWER %s" % power)
            self.windFreakConnection.send("SWPTo %s 0.5 4 True" % endFrequencyMHz)
            time.sleep(0.1)
            self.windFreakConnection.send("EXECUTE")
            fittedFieldBGauss = self.highFieldImaging.fittedField(BFieldGauss)
            requiredBeatFreq = 1372.5+self.highFieldImaging.imagingFrequency(785.8390544441137, 6,1)-self.highFieldImaging.imagingFrequency(fittedFieldBGauss,6,1)
            commentString = "Laser 6 windfreak power (%s) and sweep sent to %s MHz. To image the |6> state with sigma+ polarisation you require : %s MHz for beat signal" % (power,endFrequencyMHz, requiredBeatFreq)
################USE THE  BELOW BLOCK TO DO FIELD DEPENDENT CALCULATIONS#######################
#            startFrequencyMHz = self.finalVariables["LiOffsetLockStartFreqMHz"]
#            detuningMHz = self.finalVariables["LiOffsetLockSnakeImagingDetuningMHz"]
#            resonance0GaussMHz = self.finalVariables["LiOffsetLockSnakeImaging0FieldResonanceMHz"]
#            BfieldGauss = self.finalVariables["DipoleTrapImagingFieldBGauss"]
#            state = int(self.finalVariables["LiOffsetLockSnakeState"])
#            polarisation = int(self.finalVariables["LiOffsetLockSnakePolarisation"])
#            if state not in self.validStates:
#                logger.error("Unrecognised state %s in Windfreak High field imaging" % state)
#                self.snakeReference.mainLog.addLine("Unrecognised state %s in Windfreak High field imaging" % state,4)
#                fieldShiftMHz = 0
#            elif polarisation not in self.validPolarisations:
#                logger.error("Unrecognised polarisation %s in Windfreak High field imaging" % polarisation)
#                self.snakeReference.mainLog.addLine("Unrecognised polarisation %s in Windfreak High field imaging" % polarisation,4)
#                fieldShiftMHz = 0
#            else:
#                try:
#                    fieldShiftMHz = self.highFieldImaging.imagingFrequency(BfieldGauss, state, polarisation)
#                    imagingStrength = self.highFieldImaging.imagingStrength(BfieldGauss, state, polarisation)
#                except Exception as e:
#                    logger.error("error when using interpolation functions in Windfreak high field imaging. %s " % e.message)
#                    self.snakeReference.mainLog.addLine("error when using interpolation functions in Windfreak high field imaging. %s " % e.message,4)
#            
#            endFrequencyMHz = resonance0GaussMHz+detuningMHz+fieldShiftMHz # minus definition comes from original mathematica sheet. Because we changed EOM order lock on 2016 02 22 I changed this to a plus
#            endFrequencyMHz = round(endFrequencyMHz, 1)
#            stepSizeMHz = self.finalVariables["LiOffsetLockResolutionMHz"]
#            sweepLengthTime = self.finalVariables["LiOffsetLockSweepTimeSec"]
#            returnCheck = self.windFreakConnection.connect()
#            logger.debug("return check value was %s " %  returnCheck)
#            self.windFreakConnection.clearQueue()
#            retval1 = self.windFreakConnection.sweep2(startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime)
#            logger.info("sweep1 ret value %s" % retval1)
#            retval2 = self.windFreakConnection.sweep2(endFrequencyMHz,startFrequencyMHz,stepSizeMHz,sweepLengthTime)
#            logger.info("sweep2 ret value %s" % retval2)
#            BFieldMessage = "Windfreak: Li Imaging set for |%s> state polarisation %s,  %s G , %s MHz detuned--> %s+%s+%s=%s MHz imaging frequency. (strength=%s)" % (state,polarisation, BfieldGauss, detuningMHz,resonance0GaussMHz,fieldShiftMHz,detuningMHz,endFrequencyMHz,imagingStrength)
#            sweepMessage =  "WindFreak: sweep startFrequencyMHz=%s,endFrequencyMHz=%s,stepSizeMHz=%s,sweepLengthTime=%s on 1st trigger and back on 2nd trigger" % (startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime)
#            self.snakeReference.mainLog.addLine(BFieldMessage,2)            
#            self.snakeReference.mainLog.addLine(sweepMessage,2)
            #self.windFreakConnection.close()
            return commentString
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)

    
if __name__=="__main__":
    print "example usage: imagingFieldShift(6, 100)"