# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 11:27:11 2015

@author: User
"""
import hardwareAction
import DLIC
import logging
logger=logging.getLogger("ExperimentSnake.hardwareAction.EvaporationRamp")

class EvaporationRamp(hardwareAction.HardwareAction):
    """Handles access to the DLIC box for evaporative cooling
    variables control start and end point of ramp"""
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(EvaporationRamp,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"EvapSnakeStep0FreqMHz":"EvapStep0FreqMHz",
                                "EvapSnakeStep1FreqMHz":"EvapStep1FreqMHz",
                                "EvapSnakeStep2FreqMHz":"EvapStep2FreqMHz",
                                "EvapSnakeStep3FreqMHz":"EvapStep3FreqMHz",
                                "EvapSnakeStep4FreqMHz":"EvapStep4FreqMHz",
                                "EvapSnakeTimeStep1":"EvaporationTimeStep1",
                                "EvapSnakeTimeStep2":"EvaporationTimeStep2", 
                                "EvapSnakeTimeStep3":"EvaporationTimeStep3", 
                                "EvapSnakeTimeStep4":"EvaporationTimeStep4"} # maps name in experiment control to names used in python callback
        self.hardwareActionName = 'dlic-evap'
        logger.info( "dlic-evap object created successfully")

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.NAME= 'DLIC-EVAP'
        self.IP_ADDRESS = '192.168.16.2'
        self.PORT = 22000
        if not self.initialised:
#            try:
            self.DLIC_EVAP=DLIC.DLIC(self.NAME,self.IP_ADDRESS,self.PORT)#create the connection and the DLIC object
#            except Exception as e:
#                logger.error("failed to initialise DLIC %s. Error message %s" % (self.NAME, e.message) )
#                self.snakeReference.mainLog.addLine("failed to initialise DLIC %s. Error message %s... try restarting DLIC / DECADS server?" % (self.NAME, e.message) ,4)
#                return "%s init failed with error %s... try restarting DLIC / DECADS server?" % (self.hardwareActionName, e.message)
        else:
            self.snakeReference.mainLog.addLine("%s was already initialised will not reconnect to DLIC" % (self.NAME),4)
        self.DLIC_EVAP.setDACVoltage(1.5,0) # original: 1.5
        self.referenceFrequency = 2200# 2GHz in MHz = 2000MHz
        self.initialised = True
        self.MHz = 1.0E6 #converts MHz to Hz
        logger.info( "dlic-evap init successful")
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """called to close the hardware down when user stops Snake or exits. Should
        safely close the hardware. It should be able to restart again when the 
        init function is called (e.g. user then presses start"""
        if hasattr(self, "DLIC_EVAP"):
            self.DLIC_EVAP.close()
            self.initialised=False
            logger.info( "dlic-evap closed")
        else:
            logger.warning("could not find DLIC_EVAP attribute to close")
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
            self.snakeReference.mainLog.addLine("%s not initialised" % (self.NAME) ,4)
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:
            self.finalVariables = self.mapVariables()
            dlicStep0Frequency = (self.referenceFrequency-self.finalVariables["EvapStep0FreqMHz"])*self.MHz # gives number in Hz
            dlicStep1Frequency = (self.referenceFrequency-self.finalVariables["EvapStep1FreqMHz"])*self.MHz # gives number in Hz
            dlicStep2Frequency = (self.referenceFrequency-self.finalVariables["EvapStep2FreqMHz"])*self.MHz # gives number in Hz
            dlicStep3Frequency = (self.referenceFrequency-self.finalVariables["EvapStep3FreqMHz"])*self.MHz # gives number in Hz
            dlicStep4Frequency = (self.referenceFrequency-self.finalVariables["EvapStep4FreqMHz"])*self.MHz # gives number in Hz
            
            
            step1Time = self.finalVariables["EvaporationTimeStep1"]
            step2Time = self.finalVariables["EvaporationTimeStep2"]            
            step3Time = self.finalVariables["EvaporationTimeStep3"]
            step4Time = self.finalVariables["EvaporationTimeStep4"]
            
            #now create the appropriate lists for each ramp . note we have to use freqsAndTimes as some timesteps might be > 6.7 secs which makes DLIC :**(
            f1s, t1s = self.freqsAndTimes(dlicStep0Frequency,dlicStep1Frequency,step1Time )
            f2s, t2s = self.freqsAndTimes(dlicStep1Frequency,dlicStep2Frequency,step2Time )
            f3s, t3s = self.freqsAndTimes(dlicStep2Frequency,dlicStep3Frequency,step3Time )
            f4s, t4s = self.freqsAndTimes(dlicStep3Frequency,dlicStep4Frequency,step4Time )
                
            freqs = f1s+f2s+f3s+f4s
            times= t1s+t2s+t3s+t4s
            
            self.DLIC_EVAP.setFrequency(dlicStep0Frequency,0) # do this without a trigger to get frequency in the correct position before we turn on mixer
            self.DLIC_EVAP.ddsSweepFreqInDt(freqs, times,1)# 1 means it waits for ext trigger
            return "%s ramp %s freqs, %s secs" % (self.hardwareActionName,freqs, times)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        
