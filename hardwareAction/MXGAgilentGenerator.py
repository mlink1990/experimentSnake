# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 17:31:24 2015

@author: tharrison
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Oct 03 10:11:33 2014

@author: tharrison
"""
import visa
import scipy
import logging

#http://cp.literature.agilent.com/litweb/pdf/N5180-90004.pdf
#N5183A MXG
logger=logging.getLogger("ExperimentSnake.hardwareAction.MXGAgilentGenerator")

class Agilent34411AError(Exception):
    pass


class MXG:

    def __init__(self, name="USBInstrument1",timeout=30.0):
        """Initialise agilent34411A over USB. Also automatically sets triggering to immediate"""
        logger.info("connecting to MXG")
        try:
            if float(visa.__version__)>1.5:
                self.rm = visa.ResourceManager()
                self.instrument = self.rm.open_resource(name)
                self.instrument.timeout = timeout*1000#changed to ms in newer version!
            else:#version >=1.5
                self.instrument = visa.instrument(name, timeout=timeout) # name of USB instrument
                self.instrument.timeout = timeout
        except AttributeError:#early versions have no __version__ attribute
            self.instrument = visa.instrument(name, timeout=timeout) # name of USB instrument
            self.instrument.timeout = timeout
            
    
    def setCWMode(self):
        self.write("FREQ:MODE CW")
        #see FREQ:MODE LIST for sweeps
    
    def setFreqGHz(self, freq):
        self.write("FREQ:CW %sGHz"%freq)
        
    def setFreqMHz(self, freq):
        self.write("FREQ:CW %sMHz"%freq)
    
    def getFreq(self):
        return self.ask("FREQ:CW?")
        
    def setPower(self, powerdBm):
        return self.write(":POWER:AMPL %sdbm"%powerdBm)
        
    def ask(self, question):
        """ wrapper for visa.instrument.ask. remeber ask queries must end with a question mark"""
        return self.instrument.ask(question)

    def write(self, statement):
        """ wrapper for visa.instrument.write. remeber write queries do something to the system and do not end a question mark"""
        return self.instrument.write(statement)

    def scpi(self, command):
        """Intelligent wrapper for ask and write. uses ask if the last character is a question mark."""
        if command[-1]=="?":
            return self.instrument.ask(command)
        else:
            return self.instrument.write(command)
            
    def close(self):
        self.instrument.close()
  
if __name__=="__main__":
    mxg = MXG(name="TCPIP0::192.168.16.90::inst0::INSTR")