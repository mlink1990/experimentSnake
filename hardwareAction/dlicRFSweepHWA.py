# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 11:27:11 2015

@author: User
"""
import hardwareAction
import DLIC
import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.EvaporationRamp")

class DLICRFSweep(hardwareAction.HardwareAction):
    """Handles access to the DLIC box for evaporative cooling
    variables control start and end point of ramp"""
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(DLICRFSweep,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"RFSweepSnakeFreq0MHz":"RFSweepSnakeFreq0MHz",
                                "RFSweepSnakeFreq1MHz":"RFSweepSnakeFreq1MHz",
                                "RFSweepSnakePowerVoltage":"RFSweepSnakePowerVoltage",
                                "RFSweepSnakeRampTime":"RFSweepSnakeRampTime"} # maps name in experiment control to names used in python callback
        self.hardwareActionName = 'dlic-rf-sweep'
        logger.info( "dlic-rf-sweep object created successfully")

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.NAME= 'DLIC-RF-SWEEP'
        self.IP_ADDRESS = '192.168.16.2'
        self.PORT = 22001
        if not self.initialised:
            try:
                self.DLICObject=DLIC.DLIC(self.NAME,self.IP_ADDRESS,self.PORT)#create the connection and the DLIC object
            except Exception as e:
                logger.error("failed to initialise DLIC %s. Error message %s" % (self.NAME, e.message) )
                self.snakeReference.mainLog.addLine("failed to initialise DLIC %s. Error message %s" % (self.NAME, e.message) ,4)
        else:
            self.snakeReference.mainLog.addLine("%s was already initialised will not reconnect to DLIC" % (self.NAME),4)
        
        self.DLICObject.turnOnDDSWithTrigger()
        self.DLICObject.setDACVoltage(-8.0,0)
        self.initialised = True
        self.MHz = 1.0E6 #converts MHz to Hz
        logger.info( "dlic-rf-sweep init successful")
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "DLICObject"):
            self.DLICObject.close()
            self.initialised=False
            logger.info( "dlic-rf-sweep closed")
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
        logger.debug( "beginning dlic-evap callback")        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:
            self.finalVariables = self.mapVariables()
            dacVoltage = self.finalVariables["RFSweepSnakePowerVoltage"]
            self.DLICObject.setDACVoltage(dacVoltage,0)
            dlicStep0Frequency = self.finalVariables["RFSweepSnakeFreq0MHz"]*self.MHz
            dlicStep1Frequency = self.finalVariables["RFSweepSnakeFreq1MHz"]*self.MHz
            
            step1Time = self.finalVariables["RFSweepSnakeRampTime"]
            
            #now create the appropriate lists for each ramp . note we have to use freqsAndTimes as some timesteps might be > 6.7 secs which makes DLIC :**(
            f1s, t1s = self.freqsAndTimes(dlicStep0Frequency,dlicStep1Frequency,step1Time )
                
            freqs = f1s
            times= t1s
            
            self.DLICObject.setFrequency(dlicStep0Frequency,0) # do this without a trigger to get frequency in the correct position before we turn on mixer
            self.DLICObject.ddsSweepFreqInDt(freqs, times,1)# 1 means it waits for ext trigger
            return " %s, DAC Voltage %s - %s startFreq - ramp %s freqs, %s secs" % (self.hardwareActionName,dacVoltage,dlicStep0Frequency,freqs, times)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        