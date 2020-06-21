# -*- coding: utf-8 -*-
"""
Created on Fri Oct 03 10:11:33 2014

@author: tharrison
"""
import visa
import time
import decimal
import scipy
import logging

logger=logging.getLogger("ExperimentSnake.hardwareAction.agilentSCPI")


class Agilent34411AError(Exception):
    pass


class Agilent34411A(object):

    def __init__(self, name="USBInstrument1", trigSource='IMM',timeout=60.0,safetyTimeOn=False, safetyTime =0.05):
        """Initialise agilent34411A over USB. Also automatically sets triggering to immediate
        DOCUMENT http://www.keysight.com/owc_discussions/servlet/JiveServlet/download/124-35351-107364-5847/34410A_11A_SCPI_Reference.pdf        
        
        """
        logger.debug( "connecting to instrument")
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
        self.trigSource=trigSource
        self.safetyTimeOn = safetyTimeOn
        self.safetyTime = safetyTime
        #TRIG SOURCE can be IMM, BUS, EXT, INT
        # EXT can be used if you have for example the atomic clock hooked to the device
        #bus will trigger whenever the *TRG command is sent via SCPI
        #IMM will trigger as soon as it is put in wait for trigger mode
        # INTernal can trigger on a level on the internal signal
        #for most cases with SCPI IMM is what you want unless things are timing critical
        if trigSource not in ["IMM", "EXT","BUS","INT"]:
            Agilent34411AError('trigSource value not in ["IMM", "EXT","BUS","INT"]')
        
        else:
            logger.debug(  "setting trigger source to %s " % trigSource   )         
            self.instrument.write("TRIG:SOURCE %s" % trigSource)
            if trigSource == "EXT":
                self.instrument.write("TRIG:SLOPE POS")
                logger.debug(  "set the trigger slope to positive")
            logger.debug(  "Trigger source has been set to %s with %s slope" % (self.ask("TRIG:SOURCE?"),self.ask("TRIG:SLOPE?")))
        
        
    def triggerCount(self, n):
        """a.For the BUS source, the trigger count sets the number of *TRG
        commands that will be accepted before returning to the "idle" trigger
        state.
        b. For the IMMediate source, the trigger count just controls the number of
        readings to be taken.
        c. For the EXTernal source, the trigger count sets the number of external
        pulses that will be accepted before returning to the "idle" trigger state """
        return self.write("TRIG:COUNT %s" % n)
    
    def sampleCount(self, n):
        """This command selects the number of readings (samples) the meter will take
        per trigger.You can use the specified sample count in conjunction with a trigger count
        (see TRIGger:COUNt command) which sets the number of triggers to be
        accepted before returning to the "idle" trigger state. In this case, the total
        number of readings returned will be the product of the sample count and
        trigger count.
        Number of Readings = Sample Count x Trigger Count
        If more than 50,000 readings for the 34410A, or 1,000,000 readings for
        the 34411A/L4411A are to be taken, the data must be read from reading
        memory fast enough to avoid a memory overflow. The most recent
        readings are preserved. The oldest readings are overwritten in reading
        memory if an overflow occurs.
        You can use the SAMPle:COUNt:PRETrigger command (34411A/L4411A) to
        set a pretrigger count, which reserves memory for a specified number of
        pretrigger samples.
        The CONFigure and MEASure? commands automatically set the sample
        count to "1". """
        if n>1000000:
            logger.warning(  "warning sample count should not be greater than 1 million!")
        return self.write("SAMPLE:COUNT %s" % n)
        
    def setSampleSourceTime(self, timeStep):
        """makes the sample source use the timer. Then sets sample time to 
        requested value. Important for regularly spaced time samples: (pg 787)
        This command works in conjunction with the TRIGger:DELay command and
        the SAMPle:TIMer command to determine sample timing when the sample
        count is greater than one. In all cases, the first sample is taken one trigger
        delay time after the trigger (the delay being set with the TRIGger:DELay
        command). Beyond that, the timing mechanism depends on whether you
        select IMMediate or TIMer as the source:
        """
        self.write("SAMPLE:SOURCE TIM")
        return self.write("SAMPLE:TIMER %s" % timeStep)
        
    def setSampleSourceImmediate(self):
        """trigger delay time defines time between each measurement in sample """
        return self.write("SAMPLE:SOURCE TIM")
        
    def setIntegrationTimeNPLC(self, nplc):
        """defines the time it integrates for for a measurement in units of number
        of power line cycles.Setting the integration time also sets"VOLT:DC:NPLC the resolution for the measurement.
        The following table shows the relationship between integration time and
        resolution.
        """
        validValues = [0.001, 0.002, 0.006, 0.02, 0.06,0.2,1,2,10,100]
        if nplc not in validValues :
            logger.error("invalid nplc value. Must be one of %s " % validValues )
            return
        return self.write("VOLT:DC:NPLC %s" % nplc)
        
        
    def setTriggerDelay(self, timeStep):
        """This command sets the delay between the trigger signal and the first
        measurement. This may be useful in applications where you want to allow
        the input to settle before taking a reading or for pacing a burst of readings.
        The programmed trigger delay overrides the default trigger delay that the
        instrument automatically adds.
        """
        return self.write("TRIG:DEL %s" % timeStep)
        
    def setAutoZero(self,on):
        """This command disables or enables the autozero mode for dc voltage
        measurements.
        When autozero is ON (default), the instrument internally disconnects the
        input signal following each measurement, and takes a zero reading. It
        then subtracts the zero reading from the preceding reading. This prevents
        offset voltages present on the instrument's input circuitry from affecting
        measurement accuracy.
        When autozero is OFF, the instrument uses the last measured zero
        reading and subtracts it from each measurement. It takes a new zero
        reading each time you change the function, range, or integration time.
        In the ONCE mode, the instrument takes one zero reading, and then sets
        autozero to off. The zero reading taken is used for all subsequent
        measurements until the next change to the function, range, or integration
        time. If the specified integration time is less than 1 PLC, the one zero
        reading is taken at 1 PLC to ensure best noise rejection in the zero
        reading, and then the subsequent measurements are taken at the
        specified fast integration time (for example 0.02 PLC). """
        if on == "once":
            return self.write("VOLT:ZERO:AUTO ONCE")
        if on:
            return self.write("VOLT:ZERO:AUTO ON")
        else:
            return self.write("VOLT:ZERO:AUTO OFF")
        
        
    def startStatistics(self):
        """In order to use the statistics functions below, you need to initialise
        the statistics CALC function average. This gives access to the following
        commands some of which are wrapped below.
        
        CALCulate:AVERage:AVERage?
        CALCulate:AVERage:CLEar
        CALCulate:AVERage:COUNt?
        CALCulate:AVERage:MAXimum?
        CALCulate:AVERage:MINimum?
        CALCulate:AVERage:PTPeak? CALCulate:AVERage:SDEViation?
         
         Send CALCulate:FUNCtion AVERage to enable statistics. When statistics
        are enabled, the average (mean), minimum, maximum, peak-to-peak,
        count, and standard deviation values are calculated and carried in the
        statistical data registers, available to be read with the statistics
        (CALCulate:AVERage) commands such as CALCulate:AVERage:AVERage?
        and CALCulate:AVERage:SDEViation?.
        The CALCulate subsystem (math operations) must be enabled using the
        CALCulate:STATe command.
        The instrument clears the calculation function selection, reverting to the
        default after a Factory Reset (*RST command) or an Instrument Preset
        (SYSTem:PRESet command).
        """
        self.write("CALC:STAT ON")
        self.write("CALC:FUNC AVER")
    
    def calcAverageCount(self):
        """
        You can read the statistical values at any time.
        The instrument clears the stored statistical data when statistics are
        enabled, when the CALCulate:FUNCtion command is sent while
        CALCulate:STATe is ON, when the power has been off, when the
        CALCulate:AVERage:CLEar command is executed, after a Factory Reset
        (*RST command), after an Instrument Preset (SYSTem:PRESet command),
        or after a function change.
        The command returns the average of the readings taken, or "0" if no data is
        available.
        
        
        """
        return self.ask("CALC:AVER:COUNT?")
        
    def calcAverageMaximum(self):
        """This command returns the maximum value found since statistics were
        enabled."""
        return self.ask("CALC:AVER:MAX?")
        
    def calcAverageMinimum(self):
        """This command returns the minimum value found since statistics were
        enabled."""
        return self.ask("CALC:AVER:MIN?")
    
    
    def configureDCVoltage(self,rangeV, resolution="MIN"):
        """
        see SCPI Reference for ways to configure. Really depends on what you want to measure
        
        """
        rangeV = str(rangeV)
        resolution = str(resolution)
        if rangeV not in ["0.1","1","10","100","1000","MIN","MAX","AUTO"]:
            Agilent34411AError('range not valid option. rangeV must be in ["0.1","1","10","100","1000","MIN","MAX","AUTO"]')
        #THIS SEEMS TO RESET TRIG:SOURCE TO IMM!!!!
        result = self.write("CONF:VOLT:DC %s,%s" % (rangeV, resolution))
        self.instrument.write("TRIG:SOURCE %s" % self.trigSource)
        return result
        
    def configureResistance(self,rangeR, resolution="MIN"):
        rangeR = str(rangeR)
        resolution = str(resolution)
        if rangeR not in ["100","1000","10000","1000000","10000000","100000000","1000000000","MIN","MAX","AUTO"]:
            Agilent34411AError('range not valid option. rangeR must be in ["100","1000","10000","1000000","10000000","100000000","1000000000","MIN","MAX","AUTO"]')
        return self.write("CONF:RES %s,%s" % (rangeR, resolution))
        
    def sampleMeasurement(self,voltageRange=10, voltageResolutionPPM = "3", totalSampleTime=0.1, logFile = None, autozero = False ):
        """helper function for creating a sampled measurement i.e. sample count measurements equally spaced by sampletime from one trigger
        This method is improved from old. It calculates more correct values for you. 
        most important input is resolution ppm which must be one of the allowed values. Then it sets the correct nplc and sample time for you        
        """
        self.setAutoZero(autozero)#fermi say this makes it much faster sampling        
        voltageResolution = float(voltageResolutionPPM)*1.0e-6*float(voltageRange)

        #configure dc voltage. this also sets the nplc         
        self.configureDCVoltage(voltageRange, voltageResolution)
        
        #get nplc and smallest possible sample time
        nplc = self.ask("VOLT:DC:NPLC?")
        sampleTime = self.ask("SAMPLE:TIMER? MIN")
        
        #create time array for data
        ts = scipy.arange(0.0, totalSampleTime,float(sampleTime))
        #sample count is the number of data points
        sampleCount = ts.shape[0]
        
        self.setTriggerDelay(0.0)
        self.write("TRIG:SOURCE EXT")
        self.triggerCount(1)

        #set sample count and sample time        
        self.sampleCount(sampleCount)
        self.setSampleSourceTime(sampleTime)
        
        logger.debug("beginning to wait for trigger")
        self.READ()#starts measurements (stored in volatile memory)   must be fetched
        ys=self.cleanFETCH()
        
        if logFile is not None:        
            scipy.savetxt(logFile,scipy.transpose(scipy.array([ts,ys])),delimiter=",")
        return [ts,ys, float(nplc),float(sampleTime)]
        
    def INIT(self):
        """This command changes the state of the triggering system from the "idle"
        state to the "wait-for-trigger" state. Measurements will begin when the
        specified trigger conditions are satisfied following the receipt of the INITiate
        command. Note that the INITiate command also clears the previous set of
        readings from memory.
        
        Be careful when using init as it begins the measurement which might have  many
        samples and you can then start getting incomplete results back if you fetch
        to soon. A safer command is READ which waits till the measurement finishes
        before FETCHing.
        """
        return self.write("INIT")
        
    def FETCH(self):
        """retrieve the readings from memory, """
        return self.ask("FETCH?")
        
    def clean(self, returnString):
        """converts a string delimited with commas into a numpy array  """
        return scipy.fromstring(returnString,sep=',')
        
    def cleanFETCH(self):
        """fetches data, cleans it to a numpy array and the nreturns """
        return self.clean(self.FETCH())
        
    def DATAREMOVE(self):
        """to remove data points from memory """
        return self.ask("DATA:REMOVE?")
        
    def R(self):
        """read and remove all of the available data. """
        return self.ask("R?")
        
    def READ(self):
        """ INIT and FETCH"""
        return self.ask("READ?")
    
    def cleanREAD(self):
        """ INIT and FETCH"""
        return self.clean(self.READ())
        
    def ask(self, question):
        """ wrapper for visa.instrument.ask. remeber ask queries must end with a question mark"""
        if self.safetyTimeOn:
            time.sleep(self.safetyTime)
        return self.instrument.ask(question)

    def write(self, statement):
        """ wrapper for visa.instrument.write. remeber write queries do something to the system and do not end a question mark"""
        if self.safetyTimeOn:
            time.sleep(self.safetyTime)
        return self.instrument.write(statement)

    def scpi(self, command):
        """Intelligent wrapper for ask and write. uses ask if the last character is a question mark."""
        if command[-1]=="?":
            return self.instrument.ask(command)
        else:
            return self.instrument.write(command)
            
    def close(self):
        logger.info(  "closing device")
        self.instrument.close()
        try:
            if float(visa.__version__)>1.5:
                self.rm.close()
        except AttributeError:
            pass
    def __del__(self):
        super(Agilent34411A, self).__del__()
        logger.info(  "deleting device")
        self.close()
        try:
            if float(visa.__version__)>1.5:
                self.rm.close()
        except AttributeError:
            pass



def getDevice():
    return Agilent34411A(name="TCPIP0::192.168.16.21::inst0::INSTR", trigSource="EXT", timeout=30.0)

def sampleHelper(device=None,voltageRange=10, voltageResolution = 0.001, sampleCount=100,sampleTime = 0.01,logFile = None):
    """helper function for when you want to DC voltage sample after a trigger"""
    try:
        if device is None:
            device = Agilent34411A(name="TCPIP0::192.168.16.21::inst0::INSTR", trigSource="EXT", timeout=30.0)
        device.configureDCVoltage(voltageRange, voltageResolution)
        logger.debug( device.write("TRIG:SOURCE EXT"))
        logger.debug(  device.triggerCount(1))
        logger.debug(  device.sampleCount(sampleCount))
        logger.debug(  device.setSampleSourceTime(sampleTime))
        logger.debug(  "beginning to wait for trigger")
        device.READ()#starts measurements (stored in volatile memory)   must be fetched
        ys=device.cleanFETCH()
        ts = scipy.linspace(0.0, sampleCount*sampleTime,sampleCount)
        if logFile is not None:        
            scipy.savetxt(logFile,scipy.transpose(scipy.array([ts,ys])),delimiter=",")
    finally:
        if device is None:
            device.close()
    return ts,ys
        
        
def statisticsExample():
    agg = Agilent34411A(name="TCPIP0::192.168.16.21::inst0::INSTR", trigSource="EXT", timeout=60.0)
    print agg.configureDCVoltage("1", resolution = "0.001")
    print agg.write("TRIG:SOURCE EXT")
    print agg.triggerCount(1)
    print agg.sampleCount(1000)
    print agg.startStatistics()
    print agg.ask("TRIG:SOURCE?")
    print "starting init"
    agg.READ()#starts measurements (stored in memory)    
    #time.sleep(5.0)
    print agg.calcAverageCount()
    print agg.calcAverageMaximum()
    #print agg.clean(agg.FETCH())
    return agg
    
if __name__=="__main__":
    agg = getDevice()