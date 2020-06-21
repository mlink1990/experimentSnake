# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""

import hardwareAction
import logging
import threading
import os
import agilentSCPI
import scipy
import time
import csv

logger=logging.getLogger("ExperimentSnake.hardwareAction.experimentTables")

class AgilentThread(threading.Thread):
    """"""
    
    def run(self):
        logger.debug("beginning Agilent Thread")
        snake = self.dmm.snakeReference
        device = self.dmm.device
        resolutionPPM = self.dmm.resolutionPPM
        totalSampleTime = self.dmm.totalSampleTime
        snake.mainLog.addLine("callback on %s - prepared to measure on dmm with trigger" % (self.dmm.hardwareActionName),2)
        currentDataFile  = os.path.join(self.dmm.rawSeqFolder,"dmm-latestSequence-%.2d.csv" % (self.dmm.logCounter))#iterative file
        dateLogFolder = os.path.join(self.dmm.rawSeqFolderNAS,time.strftime("%Y-%m-%d", time.localtime()))
        if not os.path.exists(dateLogFolder):
            os.mkdir(dateLogFolder)
        rawFile = os.path.join(dateLogFolder,time.strftime("%Y-%m-%d-%H-%M-%S.csv", time.localtime()) )#hard copy of a sequence file
        try:
            [ts,ys, nplc,sampleTime]=device.sampleMeasurement(voltageRange=10,voltageResolutionPPM=resolutionPPM,totalSampleTime=totalSampleTime, autozero="once",logFile=rawFile)
        except agilentSCPI.visa.VisaIOError as e:
            logger.error("received VisaIOError, could it be snake was stopped before thread finished")
            logger.error("%s" % e.message)
            snake.mainLog.addLine("%s VisaIOError (during thread)...This is OK if you just stopped snake" % (self.dmm.hardwareActionName),4)

        ITN_RESISTOR_VALUE = 5.0  # OHMS
        ITN_CONVERSION_FACTOR = 1500.0 # 1A-> 1/1500 A
        CURRENT_TO_FIELD = 1.89329 # G/A
        currents = ys*ITN_CONVERSION_FACTOR/ITN_RESISTOR_VALUE # ITN 600-S STAB , 1:1500 conversion of current and 5 Ohm resistor gives 1A--> 1/300V
        Bs = currents*CURRENT_TO_FIELD
        
        stdev=scipy.std(ys)
        avg = scipy.average(ys)
        relative = stdev/avg
        
        stdevCurrent = ITN_CONVERSION_FACTOR/ITN_RESISTOR_VALUE*stdev
        avgCurrent = ITN_CONVERSION_FACTOR/ITN_RESISTOR_VALUE*avg
        relativeCurrent = ITN_CONVERSION_FACTOR/ITN_RESISTOR_VALUE*relative
        
        stdevBs = stdevCurrent*CURRENT_TO_FIELD
        avgBs = avgCurrent*CURRENT_TO_FIELD
        relativeBs = relativeCurrent*CURRENT_TO_FIELD
        
        scipy.savetxt(currentDataFile,scipy.transpose(scipy.array([ts,ys, currents, Bs])),delimiter=",", header="time,voltage(V),current(A),field(G)")#hard copy 
        
        #logging aggregate data
        dailyLogFile = os.path.join(self.dmm.dailyLogsFolder,time.strftime("%Y-%m-%d.csv", time.localtime()))
        latestLogFile = os.path.join(self.dmm.dailyLogsFolder,"latestValues.csv")        
        
        if not os.path.exists(dailyLogFile):
            with open(dailyLogFile, "a+") as logFile:
                writer = csv.writer(logFile)
                writer.writerow(["epoch seconds","avgVoltage","stdevVoltage","relativeVoltage","avgCurrent","stdevCurrent","relativeCurrent","avgField","stdevField","relativeField"])
        
        with open(dailyLogFile, "a+") as logFile:
            writer = csv.writer(logFile)
            writer.writerow([time.time(),avg,stdev,relative,avgCurrent,stdevCurrent,relativeCurrent,avgBs,stdevBs,relativeBs])
            
        with open(dailyLogFile, "a+") as logFile:
            writer = csv.writer(logFile)
            writer.writerow([time.time(),avg,stdev,relative,avgCurrent,stdevCurrent,relativeCurrent,avgBs,stdevBs,relativeBs])
            
        with open(latestLogFile, "wb") as logFile:
            writer = csv.writer(logFile)
            writer.writerow(["epoch seconds","avgVoltage","stdevVoltage","relativeVoltage","avgCurrent","stdevCurrent","relativeCurrent","avgField","stdevField","relativeField"])
            writer.writerow([time.time(),avg,stdev,relative,avgCurrent,stdevCurrent,relativeCurrent,avgBs,stdevBs,relativeBs])

                
        snake.mainLog.addLine("callback on %s finished (thread complete) over %g sec: average = %g, stdev = %g, relativeError = %g. (For resolution %s PPM, NPLC=%g, sample time = %g)" % (self.dmm.hardwareActionName,totalSampleTime, avg,stdev,relative,resolutionPPM,nplc,sampleTime),2)

class DigitalMultimeterMeasurement(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(DigitalMultimeterMeasurement,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {"DMMResolutionPPM":"DMMResolutionPPM",
                                "DMMTotalSampleTime":"DMMTotalSampleTime"}
        self.hardwareActionName = 'digital-mm-measurement'
        
        #experiment tables variables
        groupFolder = os.path.join("\\\\ursa","AQOGroupFolder")
        logFolder = os.path.join(groupFolder,"Experiment Humphry", "Data", "field stability measurements")
        logFolderNAS = os.path.join("N:",os.sep,"Lab Monitoring", "Field Stability Measurements")
        self.rawSeqFolder = os.path.join(logFolder, "rawSequenceData") # stores "dmm-latestSequence-0x.csv", which is on URSA (we don't have to change this now) and is usually displayed with CSVMaster
        self.rawSeqFolderNAS = os.path.join(logFolderNAS, "Raw Sequence Data") # stores all files sorted by date, creates lots of data, so we want to move this to the NAS!
        # self.currentDataFile  = os.path.join(self.logFolder,"rawSequenceData","dmm-latestSequence.csv")
        self.dailyLogsFolder  = os.path.join(logFolder,"dailyLogs") # Saves average values of each sequence in one file for every day; I don't move it to the NAS, I don't want to break anything and this is not so much data
        self.logCounter = 0#we keep last maxLogs of traces stored with special file name for plotting
        self.maxLogs = 5
        self.currentLocalTime = time.localtime()
        self.currentYear = self.currentLocalTime.tm_year
        self.currentMonth = self.currentLocalTime.tm_mon    
        self.currentDay =  self.currentLocalTime.tm_mday
        
        logger.info( "%s object created successfully" % self.hardwareActionName)

    def init(self):
        """no init necessary for experiment tables we create and close the connection
        during each sequence call"""
        if self.initialised:
            return "%s has already been initialised. I will not initialise again" % self.hardwareActionName
        self.device = agilentSCPI.getDevice()
        self.initialised=True
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """no close necessary for experiment tables we create and close the connection
        during each sequence call"""
        if hasattr(self, "device"):       
            self.device.close()
        self.initialised=False
        return "%s closed" % self.hardwareActionName
        
    def callback(self):
        """Kicks off a thread that writes rows to the Experiment tables
        sqllite3 database"""
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:#YOUR CALLBACK CODE SHOULD GO IN THIS TRY BLOCK!
            self.finalVariables = self.mapVariables()
            self.logCounter = (self.logCounter+1)%self.maxLogs
            self.agilentThread = AgilentThread()
            self.resolutionPPM = self.finalVariables["DMMResolutionPPM"]
            self.totalSampleTime = self.finalVariables["DMMTotalSampleTime"]
            self.agilentThread.dmm = self
            self.agilentThread.start()
            return "callback on %s started (thread begun)" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        