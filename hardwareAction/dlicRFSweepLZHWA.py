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
        self.variableMappings = {"RFSweepLZFreqCentreMHz6to1":"RFSweepLZFreqCentreMHz6to1",
                                "RFSweepLZFreqDeltaMHz6to1":"RFSweepLZFreqDeltaMHz6to1",
                                "RFSweepLZTime6to1":"RFSweepLZTime6to1",

                                
                                "RFSweepLZFreqCentreMHz1to2":"RFSweepLZFreqCentreMHz1to2",
                                "RFSweepLZFreqDeltaMHz1to2":"RFSweepLZFreqDeltaMHz1to2",
                                "RFSweepLZTime1to2":"RFSweepLZTime1to2",
                                
                                "RFSweepSnakePowerVoltage6to1":"RFSweepSnakePowerVoltage6to1",
                                "RFSweepSnakePowerVoltage1to2":"RFSweepSnakePowerVoltage1to2"} # maps name in experiment control to names used in python callback
        self.hardwareActionName = 'dlic-lz-sweep'
        logger.info( "dlic-lz-sweep object created successfully")

    def init(self):
        """only called once when the user presses the start button. This should perform
        any hardware specific initialisation. E.g opening sockets / decads connections. Return 
        string is printed to main log terminal"""
        self.NAME= 'DLIC-RF-SWEEP-0'
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
        logger.debug( "beginning dlic-lz-sweep callback")        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:
            
            self.DLICObject.clearQueue(4)
                
            
            self.finalVariables = self.mapVariables()
            dacVoltage6to1 = self.finalVariables["RFSweepSnakePowerVoltage6to1"]
            dacVoltage1to2 = self.finalVariables["RFSweepSnakePowerVoltage1to2"]#COMMENT
            self.DLICObject.setDACVoltage(dacVoltage6to1,0)
            
            freq06to1     = self.finalVariables["RFSweepLZFreqCentreMHz6to1"]*self.MHz
            freqDelta6to1 = self.finalVariables["RFSweepLZFreqDeltaMHz6to1"]*self.MHz
            sweepTime6to1 =  self.finalVariables["RFSweepLZTime6to1"]
            
            startFreq6to1 = freq06to1-freqDelta6to1/2.0
            endFreq6to1 = freq06to1+freqDelta6to1/2.0
            logger.debug("startFreq6to1=%s" % startFreq6to1 )            
            logger.debug("endFreq6to1=%s" % endFreq6to1 ) 
            jumpToNextRampTime = 0.001
            
            freq01to2 = self.finalVariables["RFSweepLZFreqCentreMHz1to2"]*self.MHz
            freqDelta1to2 = self.finalVariables["RFSweepLZFreqDeltaMHz1to2"]*self.MHz
            sweepTime1to2 = self.finalVariables["RFSweepLZTime1to2"]
                        
            startFreq1to2 = freq01to2-freqDelta1to2/2.0
            endFreq1to2 = freq01to2+freqDelta1to2/2.0
            
            #now create the list for sweeps. We don't use freqs and times as time should never be greater than 6.7 seconds here
            #we sweep 1 to 6 and then jump to the start frequency of 1 to 2
            freqs6to1, times6to1 = [endFreq6to1,startFreq1to2],[sweepTime6to1,jumpToNextRampTime]
            
            freqs1to2, times1to2 = [endFreq1to2],[sweepTime1to2]
            
            self.DLICObject.setFrequency(startFreq6to1,0) # do this without a trigger to get frequency in the correct position before we turn on mixer
            #self.DLICObject.setDACVoltage(dacVoltage6to1,1)#1 means it waits for ext trigger #COMMNET
            self.DLICObject.ddsSweepFreqInDt(freqs6to1, times6to1,1)# 1 means it waits for ext trigger
            
            #self.DLICObject.setDACVoltage(dacVoltage1to2,1)#1 means it waits for ext trigger #COMMNET
            self.DLICObject.ddsSweepFreqInDt(freqs1to2, times1to2,1)# 1 means it waits for ext trigger
            return "%s: |6> to |1> = %s MHz to %s MHz in %s sec & |1> to |2> = %s to %s in %s secs" % (self.hardwareActionName,startFreq6to1,endFreq6to1,sweepTime6to1,
                                                                                                       startFreq1to2,endFreq1to2,sweepTime1to2)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        