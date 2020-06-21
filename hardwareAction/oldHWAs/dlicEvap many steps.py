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
        self.variableMappings = {"EvaporationTimeStep1":"EvaporationTimeStep1","EvaporationTimeStep2":"EvaporationTimeStep2","EvaporationTimeStep3":"EvaporationTimeStep3","EvaporationTimeStep4":"EvaporationTimeStep4","EvapStartFreqMHz":"EvapStartFreqMHz","EvapMiddleFreqMHz":"EvapMiddleFreqMHz","EvapMiddle2FreqMHz":"EvapMiddle2FreqMHz","EvapMiddle3FreqMHz":"EvapMiddle3FreqMHz", "EvapEndFreqMHz":"EvapEndFreqMHz", "EvaporationTimeStep5":"EvaporationTimeStep5","EvapMiddle4FreqMHz":"EvapMiddle4FreqMHz" } # maps name in experiment control to names used in python callback
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
            self.DLIC_EVAP=DLIC.DLIC(self.NAME,self.IP_ADDRESS,self.PORT)#create the connection and the DLIC object
        else:
            self.snakeReference.mainLog.addLine("%s was already initialised will not reconnect to DLIC")
        self.DLIC_EVAP.setDACVoltage(7.0,0)
        self.referenceFrequency = 2000# 2GHz in MHz = 2000MHz
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
         
    def callback(self):
        """Our callback gets final variables calculates start and end freqeuencies
        that need to be sent to the DLIC. then sets the frequency to start frequency
        immediately (trig mask 0). It then sends a ramp which waits for a trigger (trig mask 1)."""
        logger.debug( "beginning dlic-evap callback")        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:
            self.finalVariables = self.mapVariables()
            dlicStartFrequency = (self.referenceFrequency-self.finalVariables["EvapStartFreqMHz"])*self.MHz # gives number in Hz
            dlicMiddleFrequency = (self.referenceFrequency-self.finalVariables["EvapMiddleFreqMHz"])*self.MHz # gives number in Hz
            dlicMiddle2Frequency = (self.referenceFrequency-self.finalVariables["EvapMiddle2FreqMHz"])*self.MHz # gives number in Hz
            dlicMiddle3Frequency = (self.referenceFrequency-self.finalVariables["EvapMiddle3FreqMHz"])*self.MHz # gives number in Hz
            dlicMiddle4Frequency = (self.referenceFrequency-self.finalVariables["EvapMiddle4FreqMHz"])*self.MHz # gives number in Hz
            dlicEndFrequency = (self.referenceFrequency-self.finalVariables["EvapEndFreqMHz"])*self.MHz # gives number in Hz
            step1Time = self.finalVariables["EvaporationTimeStep1"]
            step2Time = self.finalVariables["EvaporationTimeStep2"]
            step3Time = self.finalVariables["EvaporationTimeStep3"]
            step4Time = self.finalVariables["EvaporationTimeStep4"]
            step5Time = self.finalVariables["EvaporationTimeStep5"]
            
            self.DLIC_EVAP.setFrequency(dlicStartFrequency,0) # do this without a trigger to get frequency in the correct position before we turn on mixer
            self.DLIC_EVAP.ddsSweepFreqInDt([dlicMiddleFrequency,dlicMiddle2Frequency,dlicMiddle3Frequency,dlicMiddle4Frequency,dlicEndFrequency],[step1Time,step2Time,step3Time, step4Time,step5Time],1)# 1 means it waits for ext trigger
            logger.debug("%s ramp from %g Hz to %g Hz in %g secs and then to %g Hz in %g seconds" % (self.hardwareActionName, dlicStartFrequency,dlicMiddleFrequency, dlicEndFrequency,step1Time,step2Time))
            fs = [self.finalVariables["EvapStartFreqMHz"],self.finalVariables["EvapMiddleFreqMHz"],self.finalVariables["EvapMiddle2FreqMHz"],self.finalVariables["EvapMiddle3FreqMHz"],self.finalVariables["EvapMiddle4FreqMHz"], self.finalVariables["EvapEndFreqMHz"]]
            return "%s ramp %s freqs, %s secs" % (self.hardwareActionName,fs,[step1Time,step2Time,step3Time, step4Time])
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        