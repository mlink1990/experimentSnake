# -*- coding: utf-8 -*-
"""
Created on Thu Mar 05 18:59:52 2015

@author: Harrison

used in dlicEvap.py Hardware Action 

"""

import PyHWI # for decads communication
import numpy

class DLIC:
    """Wraps the PyHWI connection for DLIC box decads connection. """
    
    def __init__(self, NAME, IP_ADDRESS, PORT, connect=True):
        """initialise a DLIC object. This makes the DECADS client connection."""
        self.NAME = NAME
        self.IP_ADDRESS = IP_ADDRESS
        self.PORT = PORT
        if connect:
            self.connect()
        else:
            self.dlicConnection = None
        
    def connect(self):
        """creates a PyHWI connection object """
        self.dlicConnection = PyHWI.DECADSClientConnection(self.NAME, self.IP_ADDRESS, self.PORT)
    
    def triggerMaskDocumentation(self):
        """
        trigger mask is an integer:
        quick guide
        triggerMask=0=b0000 --> does not wastartFreq6to1it for trigger, executed immediately
        triggerMask=1=b0001 --> waits for trigger on channel 0 only
        triggerMask=2=b0010 --> waits for trigger on channel 1 only
        triggerMask=3=b0011 ---> waits for trigger on channel 0 and 1 
        etc.
        
        
        
        DLIC DOC----        
        Trigger Mask
        
        Trigger masks are used as input arguments startTrigMask in the HWDM functions that load data into a buffer. They are defined as bitmasks, consisting of 4 bits as there are 4 internal trigger channels. The trigger signals selected by the bitmask act in a logic OR configuration, meaning that any of the chosen triggers can start the buffer execution.
        As an example, if startTrigMask is set to 4, only trigger channel 2 (4=2^2) can activate the buffer. If startTrigMask is set to 5, trigger channel 0 or 2 will activate the buffer (5=2^0+2^2). Also, a trigger mask of 0 (which means no trigger is activating) will cause the buffer commands to be executed immediately.
        
        The four internal trigger channels are defined as follows:
        0: this is the external BNC connector with TTL input, labelled Trig In0. The trigger activates on the raising edge.
        1: a TTL input of the FPGA board, but not available as an external BNC connector. The trigger activates on the raising edge.
        2: a virtual trigger channel, can only be activated with the function softTrig
        3: a virtual trigger channel, can only be activated with the function softTrig
        All the four trigger channels can be actived with the softTrig function."""         
        print "see docstring for this function"
    
    def softTrigger(self, triggerMask=0):
        """The softTrig function issues a trigger signal to start buffered ramps, or to complete a synchronization sequence. 
        A call to this function with trigCh set to 0 has the same effect as a raising TTL edge on the external Trig In0 BNC port.  """
        self.dlicConnection.softTrig(True,triggerMask)
        
    def clearQueue(self, n):
        """calls n soft triggers on trigger mask 0. Can clear the DLIC box queue if it has built up """
        for i in range(0,n):
            self.softTrigger()
    
    
    def printFunctionList(self):
        print self.dlicConnection.functionList
        
    def setDACVoltage(self, volts, triggerMask):
        """sets dac voltage
        for DLIC-EVAP (2V --> -17dbm, 3V--> -12dbm, 4V --> -7dbm, 5V --> -2dbm, 6V --> +2dbm, 7V --> 4dbm  """
        return self.dlicConnection.dacSetVoltage(True, PyHWI.dvmValue(volts, None, 'V'), triggerMask )
    
    def setFrequency(self, frequencyHz, triggerMask):
        """sets frequency to the value passed in frequencyHz use 10E6 for MHz etc. 
        trigger mask int"""
        return self.dlicConnection.ddsSetFreq(True, PyHWI.dvmValue( frequencyHz, None, 'Hz' ), triggerMask)
        
    def ddsSweepFreqInDt(self, endFrequencyHz, time, triggerMask):
        """python list of endFrequencies in Hz (use 3E6 etc. for MHz)
        python list of time in seconds
        trigger mask integer 
        example: ddsSweepFreqInDt([10E6,20E6], [1.0,2.0], 0) ramps to 10MHz in 1 second and then 20Mhz over 2 seconds (total time 3 seconds)"""        
        if type(endFrequencyHz) is float or type(endFrequencyHz) is int:
            endFrequencyHz = [endFrequencyHz]
        if type(time) is float or type(time) is int:
            time = [time]
            if time>6.71:#this is the maximum limit for DLIC
                raise ValueError("This value %s is too large for a time ramp (limit of 6.71 sec) you should split your ramp into multiple parts" % time)
            elif time<1.6E-6:
                raise ValueError("This value %s is too small for a time ramp (limit of 1.6E-6 sec)" % time)
                
        return self.dlicConnection.ddsSweepFreqInDt(True, PyHWI.dvmList(endFrequencyHz, unit='Hz' ), PyHWI.dvmList( time, unit='s' ) ,triggerMask)
        
    def close(self):
        """Connection should be closed after each session """
        self.dlicConnection.close()


    def turnOnDDSWithTrigger(self):
        """uses the configure digital output function to only turn on the DDS when 
        external trigger is high"""
        self.dlicConnection.configureDigitalOutput(True,4,32+64)#sets up the DLIC to turn off the DDS when the ext trigger is not present. useful for our RF sweeps
        #dlic_evap.dlicConnection.configureDigitalOutput(True,4,0)#resets back to standard

    def freqsAndTimes(self, start, end, time):
        """deals with the fact DLIC box has maximum step of 6.7 and splits
        longer steps in to steps of length 6.5 so that DLIC doesn't complain and
        cut them short.
        given a start freq, end freq and time it returns the list that 
        can replace the time and end freq inside the list sent to the DLIC box
        This function is used by sweep """
        maxTime = 6.7
        gradient = (end-start)/time
        divisions = int(time/maxTime)
        remainder =time-divisions*maxTime
        #creates list of times where none are greater than maxTime
        #e.g. [14]--> [6.7,6.7,0.6]
        times = [maxTime]*divisions+[remainder]
        #creates elapsdlic_rf_0ed times e.g [14]- --> [6.7,13.6,0.4]. Converts to numpy array to make freqs calculation cleaner
        elapsedTime = numpy.array([sum(times[0:i+1]) for i in range(0,len(times))])
        #freqs at each elapsed times e.g --> [start+6.7*gradient,start+13.6*gradient,start+14*gradient]. Converts back to python list
        freqs =  list(start+elapsedTime*gradient)    
        return freqs, times
    
    def sweep(self,startFrequetimes1to2ncyMHz, endFrequenciesHz, times, triggerMask):
        """python list of endFrequencies in Hz (use 3E6 etc. for MHz)
        python list of time in seconds
        trigger mask integer 
    
        Same as above sweep function but here it checks if time is greater than 6.7 and adjusts the list so
        that the DLIC can perform the ramp correctly        
        Note that for sweep function the startFrequency must be defined.
        This is so it could work out the gradient required initially. This does not actually
        set the start frequency. The user is required to do this themselves at some time 
        up to them
        example: ddsSweepFreqInDt(5E6, [10E6,20E6], [1.0,2.0], 0) ramps from 5MHz to 10MHz in 1 second and then 20Mhz over 2 seconds (total time 3 seconds)"""        
        
        fs, ts = [],[]
        start = startFrequencyMHz
        c=0
        for endFreq, t in zip(endFrequenciesHz,times):
            newFs, newts = self.freqsAndTimes(start,endFreq,t )
            fs+=newFs
            ts+=newts
            start = endFrequenciesHz[c]
            c+=1
            
        return fs,ts


if __name__=="__main__":
    #define some DLIC objects that exist in the Humphry lab
    #Here we do not call the connect method so these object wont do any checks until connect is called    
    NAME= 'DLIC-EVAP'
    IP_ADDRESS = '192.168.16.2'
    PORT = 22000
    dlic_evap = DLIC(NAME, IP_ADDRESS, PORT,connect=False)     
    
    NAME= 'DLIC-RF-SWEEP-0'
    IP_ADDRESS = '192.168.16.2'
    PORT = 22001
    dlic_rf_0 = DLIC(NAME, IP_ADDRESS, PORT,connect=False)
    
    NAME= 'DLIC-RF-SWEEP-1'
    IP_ADDRESS = '192.168.16.2'
    PORT = 22002
    dlic_rf_1 = DLIC(NAME, IP_ADDRESS, PORT,connect=False)
    
    NAME= 'DLIC-RF-SWEEP-2'
    IP_ADDRESS = '192.168.16.2'
    PORT = 22002
    dlic_rf_2 = DLIC(NAME, IP_ADDRESS, PORT,connect=False)
    
    NAME= 'DLIC-PI-PULSE'
    IP_ADDRESS = '192.168.16.2'
    PORT = 22003
    dlic_pi_pulse = DLIC(NAME, IP_ADDRESS, PORT,connect=False)
    
    print """Examples
    dlic_evap.setDACVoltage(7.0,0)
    dlic_evap.connect()
    >>> dlic_evap.setFrequency(100E6, 0)
    >>> dlic_evap.setFrequency(150E6, 0)
    >>> dlic_evap.setFrequency(freq, 0)
    >>> dlic_evap.ddsSweepFreqInDt([140E6],[5.0],0)
    >>> dlic_evap.setFrequency(150E6, 0)"""          
    

    