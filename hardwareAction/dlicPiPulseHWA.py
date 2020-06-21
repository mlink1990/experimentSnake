# -*- coding: utf-8 -*-
"""
Created on Mon Apr 18 13:08:04 2016

@author: user
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 11:27:11 2015

@author: User
"""
import hardwareAction
import DLIC
import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.EvaporationRamp")

class DLICPiPulse(hardwareAction.HardwareAction):
    """Handles access to the DLIC box that we use for pi pulse or for spare RF ramps"""
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(DLICPiPulse,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"RFSweepPiPulseCentreMHz":"RFSweepPiPulseCentreMHz",
                                "RFSweepPiPulseDeltaFreqMHz":"RFSweepPiPulseDeltaFreqMHz",
                                "RFSweepPiPulseDurationTime":"RFSweepPiPulseDurationTime",
                                "RFSweepPiPulseDACVoltage":"RFSweepPiPulseDACVoltage"} # maps name in experiment control to names used in python callback
        self.hardwareActionName = 'dlic-pi-pulse'
        logger.info( "dlic-pi-pulse object created successfully")

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.NAME= 'DLIC-PI-PULSE'
        self.IP_ADDRESS = '192.168.16.2'
        self.PORT = 22003
        if not self.initialised:
            try:
                self.DLICObject=DLIC.DLIC(self.NAME,self.IP_ADDRESS,self.PORT)#create the connection and the DLIC object
            except Exception as e:
                logger.error("failed to initialise DLIC %s. Error message %s" % (self.NAME, e.message) )
                self.snakeReference.mainLog.addLine("failed to initialise DLIC %s. Error message %s" % (self.NAME, e.message) ,4)
        else:
            self.snakeReference.mainLog.addLine("%s was already initialised will not reconnect to DLIC" % (self.NAME),4)
        
        self.DLICObject.setDACVoltage(-8.0,0)
        self.initialised = True
        self.MHz = 1.0E6 #converts MHz to Hz
        logger.info( "dlic-lz-sweep init successful")
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "DLICObject"):
            self.DLICObject.close()
            self.initialised=False
            logger.info( "dlic-lz-sweep closed")
        else:
            logger.warning("could not find DLICObject attribute to close")
        return "%s closed" % self.hardwareActionName
         

    def freqsAndTimes(self, start, end, time):
        """deals with the fact DLIC box has maximum step of 6.7 and splits
        longer steps in to steps of length 6.5 so that DLIC doesn't complain and
        cut them short"""
        if time<6.7:
                times = [time]
                freqs = [end]
        else:
            gradient = (end-start)/time
            
            TIME_STEP = 6.5
            elapsedTime =TIME_STEP
            remainingTime =time-TIME_STEP
            times = [TIME_STEP]
            freqs = [gradient*TIME_STEP+start]
            while remainingTime>6.7:                                        
                elapsedTime+=TIME_STEP
                times.append(TIME_STEP)
                freqs.append(elapsedTime*gradient+start)
                remainingTime-=TIME_STEP
            times.append(remainingTime)
            elapsedTime+=remainingTime
            freqs.append(elapsedTime*gradient+start)        
        return freqs, times
        
    def callback(self):
        """Our callback gets final variables calculates start and end freqeuencies
        that need to be sent to the DLIC. then sets the frequency to start frequency
        immediately (trig mask 0). It then sends a ramp which waits for a trigger (trig mask 1)."""
        logger.debug( "beginning dlic-pi-pulse callback")        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:
            mixerFrequencyMHz = 2200.0
            self.DLICObject.clearQueue(4)
                
            self.finalVariables = self.mapVariables()
            dacVoltage = self.finalVariables["RFSweepPiPulseDACVoltage"]
            self.DLICObject.setDACVoltage(dacVoltage,0)
            
            freq0     = (self.finalVariables["RFSweepPiPulseCentreMHz"]-mixerFrequencyMHz)*self.MHz
            freqDelta = self.finalVariables["RFSweepPiPulseDeltaFreqMHz"]*self.MHz
            sweepTime =  self.finalVariables["RFSweepPiPulseDurationTime"]
            
            startFreq = freq0-freqDelta/2.0
            endFreq = freq0+freqDelta/2.0
            logger.debug("startFreq6to1=%s" % startFreq )            
            logger.debug("endFreq6to1=%s" % endFreq ) 
            
            freqs, times = [endFreq],[sweepTime]
            if abs(startFreq)>500*self.MHz:
                self.snakeReference.mainLog.addLine("DLIC pi pulse frequency %s Hz would be out of range. check variables and mixer frequency!" % startFreq,4)
            self.DLICObject.setFrequency(startFreq,0) # do this without a trigger to get frequency in the correct position before we turn on mixer
            self.DLICObject.ddsSweepFreqInDt(freqs, times,1)# 1 means it waits for ext trigger
            return "%s: sweep from %s to %s in %s secs" % (self.hardwareActionName,startFreq,endFreq,sweepTime)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        