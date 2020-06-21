# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 07:09:49 2015

@author: tharrison
"""

#standard python imports
import socket # For sockets.
import time # For sockets.
import datetime #for time delta analysis
import os
import logging
import threading
import xml.etree.ElementTree as ET # for xml comprehension of experiment runner files
import experimentRunnerConnection

#GUI Imports
import traits.api as traits
import traitsui.api as traitsui 
import pyface
#from pyface.progress_dialog import ProgressDialog
from pyface.timer.api import Timer


#experimentSnake imports
import outputStream
import hardwareAction.hardwareAction
import hardwareAction.sequenceLoggerHWA
import hardwareAction.dlicEvapHWA
import hardwareAction.dlicRFSweepHWA
import hardwareAction.evapAttenuationHWA
import hardwareAction.evapAttenuation2HWA
import hardwareAction.picomotorPlugHWA
import hardwareAction.windFreakOffsetLockHWA
import hardwareAction.AOMChannelHWAs
import hardwareAction.experimentTablesHWA
import hardwareAction.windFreakOffsetLockHighFieldImagingHWA
import hardwareAction.windFreakOffsetLock6ImagingHWA
import hardwareAction.windFreak6To1HWA
import hardwareAction.windFreakOffsetLockLaser3
import hardwareAction.greyMollassesOffsetFreqHWA
import hardwareAction.dlicRFSweepLZHWA
import hardwareAction.dlicRFSweepLZWithPowerCtrlHWA
import hardwareAction.dlicRFSweepLZWithPowerCtrl13PreparationHWA
import hardwareAction.dlicPiPulseHWA
import hardwareAction.digitalMultimeterCurrentMeasureHWA
import hardwareAction.MXGPiPulseHWA
import hardwareAction.variableExplorerHWA
import hardwareAction.jds6600HWA
import hardwareAction.watchdogHWA

import variableDictionary

logger=logging.getLogger("ExperimentSnake.experimentSnake")

class ExperimentSnakeHandler(traitsui.Handler):
    """ Handler for the experiment snake"""
    def closed(self, info, is_ok):
        """ Handles a dialog-based user interface being closed by the user.
        Overridden here to stop the timer once the window is destroyed.
        """
        try:
            #stop any previous timer, should only have 1 timer at a time
            info.object._stopSnake()
            logger.info("attempting to stop timers")
        except Exception as e:
            logger.error("couldn't stop current timer before starting new one: %s" % e.message)
        return
        
class SocketThread(threading.Thread):
    """wrapper for blocking socket call to make it effectively non-blocking.
    This is required for the experiment runner GETCURRENT command which blocks 
    the socket get command until the sequence ends. At the beginning of the next
    sequence it returns the entire XML file of the next sequence"""
    def run(self):
        logger.info( "starting getCurrent")
        try:
            self.xmlString = self.snakeReference.connection.getCurrent() # only returns at the beginning of a sequence! Experiment runner then returns the entire XML file
            xmlStringLength = len(self.xmlString)
            if xmlStringLength>0.9*1048576:
                logger.warning("90\% of xml buffer used. Increase buffer size! length of xml string = %s " % xmlStringLength)
            logger.info("end of xml file is like [-30:]= %s" % self.xmlString[-30:])
        except socket.error as e:
            logger.error( "failed to get current -   message=%s . errno=%s . errstring=%s " % (e.message, e.errno, e.strerror))
            return #dont try and do xml processing as we don't have the xml file
        logger.info( "received XML of length %s " % len(self.xmlString))
        try:
            root = ET.fromstring(self.xmlString)        
            variables = root.find("variables")
            self.snakeReference.variables = {child[0].text:float(child[1].text) for child in variables}
            self.snakeReference.xmlString = self.xmlString
            logger.debug( "vars %s " % self.snakeReference.variables)
            #timing edges dictionary : name--> value
            self.snakeReference.timingEdges = {timingEdge.find("name").text:float(timingEdge.find("value").text) for timingEdge in root.find("timing")}
            self.snakeReference.newSequenceStarted()
        except ET.ParseError as e: 
            self.snakeReference.mainLog.addLine("Error. Could not parse XML: %s" % e.message,3)
            self.snakeReference.mainLog.addLine("Possible cause is that buffer is full. is XML length %s>= limit %s ????" % (len(self.xmlString),self.snakeReference.connection.BUFFER_SIZE_XML) ,3)
            logger.error( "could not parse XML: %s " % self.xmlString)
            logger.error(e.message)

class ExperimentSnake(traits.HasTraits):
    """Main Experiment Snake GUI that sends arbitrary actions based on the 
    experiment runner sequence and actions that have been set up."""
    
    #mainLog = utilities.TextDisplay()
    mainLog = outputStream.OutputStream()
    statusString = traits.String("Press Start Snake to begin...")
    isRunning = traits.Bool(False) # true when the snake is running
    sequenceStarted = traits.Bool(False) # flashes true for ~1ms when sequence starts
    queue = traits.Int(0)
    
    variables = traits.Dict(key_trait=traits.Str, value_trait = traits.Float) #dictionary mapping variable names in Exp control to their values in this sequence    
    timingEdges = traits.Dict(key_trait=traits.Str, value_trait = traits.Float) #dictionary mapping timing Edge names in Exp control to their values in this sequence    
    statusList = []#eventually will contain the information gathered from experiment Runner each time we poll
    
    startAction = traitsui.Action(name   = 'start', action = '_startSnake', image  = pyface.image_resource.ImageResource( os.path.join( 'icons', 'start.png' )))
    stopAction = traitsui.Action(name   = 'stop', action = '_stopSnakeToolbar', image  = pyface.image_resource.ImageResource( os.path.join( 'icons', 'stop.png' )))
    reloadHWAsAction = traitsui.Action(name   = 'reload', action = '_reloadHWAsToolbar', image  = pyface.image_resource.ImageResource( os.path.join( 'icons', 'reload.png' )))


    connectionTimer = traits.Instance(Timer) # polls the experiment runner and starts off callbacks at appropriate times
    statusStringTimer = traits.Instance(Timer) #updates status bar at regular times (less freque)
    getCurrentTimer = traits.Instance(Timer) #waits for get current to return which marks the beginning of a sequence
    
    getCurrentThread = traits.Instance(SocketThread)
    
    connectionPollFrequency = traits.Float(1000.0) #milliseconds defines accuracy you will perform callbacks at
    statusStringFrequency = traits.Float(2000.0)#milliseconds
    getCurrentFrequency = traits.Float(1000.0)#milliseconds should be shorter than the sequence
    
    timeRunning = traits.Float(0.0)#how long the sequence has been running
    totalTime = traits.Float(0.0)# total length of sequence
    runnerHalted = traits.Bool(True)# true if runner is halted
    haltedCount = 0
    progress = traits.Float(0.0)# % of cycle complete
    #progressBar = ProgressDialog()
    hardwareActions = traits.List(hardwareAction.hardwareAction.HardwareAction)
    
    examineVariablesDictionary = traits.Instance(variableDictionary.ExamineVariablesDictionary)    
    xmlString = "" # STRING that will contain entire XML File
    
    menubar = traitsui.MenuBar(
            traitsui.Menu(
                traitsui.Action(name='Start Snake', action='_startSnake'),
                traitsui.Action(name='Stop Snake', action='_stopSnake'),
                traitsui.Action(name='Reload', action='_reloadHWAs'),
                traitsui.Menu(
                              traitsui.Action(name='DEBUG', action='_changeLoggingLevelDebug'),
                              traitsui.Action(name='INFO', action='_changeLoggingLevelInfo'),
                              traitsui.Action(name='WARNING', action='_changeLoggingLevelWarning'),
                              traitsui.Action(name='ERROR', action='_changeLoggingLevelError'),name="Log Level"), 
            name='Menu')
            )
            
    toolbar = traitsui.ToolBar(startAction,stopAction, reloadHWAsAction)
    
    mainSnakeGroup = traitsui.VGroup(
                        traitsui.Item('statusString',show_label=False,style='readonly'),
                        traitsui.Item('mainLog',show_label=False, springy=True, style='custom',editor=traitsui.InstanceEditor()))    
    
    hardwareActionsGroup = traitsui.Group( 
                                    traitsui.Item('hardwareActions', show_label=False,style = 'custom', editor= traitsui.ListEditor(style="custom")),
                                    label="Hardware Actions", show_border=True
                                    )
                                    
    variableExaminerGroup = traitsui.Group(
                                    traitsui.Item("examineVariablesDictionary",editor=traitsui.InstanceEditor(), style="custom", show_label=False),
                                    label = "Variable Examiner")
    
    sidePanelGroup = traitsui.VSplit(hardwareActionsGroup, variableExaminerGroup)
    
    traits_view = traitsui.View( 
                                traitsui.HSplit(sidePanelGroup, 
                                                     mainSnakeGroup, show_labels=True ),
                    
                            resizable=True, menubar = menubar, toolbar=toolbar, width = 0.5, height=0.75,
                            title="Experiment Snake", 
                            icon=pyface.image_resource.ImageResource( os.path.join( 'icons', 'snakeIcon.ico' ))
                            )
                 
    def __init__(self, **traits):
        """ takes no  arguments to construct the snake. Everything is done through GUI.
        Snake construction makes a ExperimentSnakeConnection object and writes to the 
        main log window"""
        
        super(ExperimentSnake, self).__init__(**traits)
        self.connection = experimentRunnerConnection.Connection()#can override default ports and IP
        self.hardwareActions = [hardwareAction.sequenceLoggerHWA.SequenceLogger(0.0, snakeReference = self),
                                hardwareAction.experimentTablesHWA.ExperimentTables(0.0, snakeReference = self,enabled=False),
                                hardwareAction.dlicEvapHWA.EvaporationRamp(1.0, snakeReference = self),
                                #hardwareAction.dlicRFSweepHWA.DLICRFSweep(1.0, snakeReference = self,enabled=False),
                                hardwareAction.dlicRFSweepLZHWA.DLICRFSweep(1.0, snakeReference = self,enabled=False),
                                hardwareAction.dlicRFSweepLZWithPowerCtrlHWA.DLICRFSweep(1.0, snakeReference = self,enabled=False),
                                hardwareAction.dlicRFSweepLZWithPowerCtrl13PreparationHWA.DLICRFSweep(1.0, snakeReference = self,enabled=True),
                                hardwareAction.dlicPiPulseHWA.DLICPiPulse(1.0,snakeReference = self,enabled=False ),
                                hardwareAction.evapAttenuationHWA.EvapAttenuation(1.0, snakeReference = self),
                                hardwareAction.greyMollassesOffsetFreqHWA.GreyMollassesOffset(1.0, snakeReference=self, enabled=False),
                                hardwareAction.evapAttenuation2HWA.EvapAttenuation("EvapSnakeAttenuationTimeFinal", snakeReference = self, enabled=False),
                                hardwareAction.picomotorPlugHWA.PicomotorPlug(1.0, snakeReference=self, enabled=False),
                                hardwareAction.windFreakOffsetLockHWA.WindFreak(0.0, snakeReference = self, enabled=False),
                                hardwareAction.windFreakOffsetLockHighFieldImagingHWA.WindFreak(0.0, snakeReference = self, enabled=True),
                                hardwareAction.windFreakOffsetLock6ImagingHWA.WindFreak(2.0, snakeReference = self, enabled=False),
                                hardwareAction.windFreak6To1HWA.WindFreak(2.0, snakeReference = self, enabled=False),
                                hardwareAction.windFreakOffsetLockLaser3.WindFreak(3.0, snakeReference = self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaZSFreq(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaZSAtten(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaZSEOMFreq(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaZSEOMAtten(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaSpecFreq(1.0, snakeReference=self, enabled=False),

                                hardwareAction.AOMChannelHWAs.AOMChannelLiImaging(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelLiImagingDetuning(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelLiPushPulseAttenuation(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelLiPushPulseDetuning(1.0, snakeReference=self, enabled=False),
                                
                                hardwareAction.AOMChannelHWAs.AOMChannelNaDarkSpotAOMFreq(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaDarkSpotAOMAtten(1.0, snakeReference=self, enabled=False),

                                hardwareAction.AOMChannelHWAs.AOMChannelNaMOTFreq(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaMOTAtten(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaMOTEOMAtten(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaImagingDP(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelLiMOTRep(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelLiMOTCool(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelLiOpticalPump(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNa2to2OpticalPumpingFreq(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNa2to2OpticalPumpingAtt(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaHighFieldImagingFreq(1.0, snakeReference=self, enabled=False),
                                hardwareAction.AOMChannelHWAs.AOMChannelNaHighFieldImagingAtt(1.0, snakeReference=self, enabled=False),
                                hardwareAction.digitalMultimeterCurrentMeasureHWA.DigitalMultimeterMeasurement(1.0, snakeReference=self, enabled=True),
                                hardwareAction.MXGPiPulseHWA.PiPulse(1.0, snakeReference=self, enabled=False),
                                hardwareAction.variableExplorerHWA.VariableExplorer(2.0, snakeReference = self, enabled=False),
                                hardwareAction.jds6600HWA.JDS6600HWA(1.0, snakeReference = self, enabled=False),
                                hardwareAction.watchdogHWA.WatchdogHWA(18.0, snakeReference = self, enabled=True)
                                ]        
        introString = """Welcome to experiment snake."""
        
        self.mainLog.addLine(introString, 1)
        
        
    def initialiseHardwareActions(self):
        for hdwAct in self.hardwareActions:
            if hdwAct.enabled:
                returnString = hdwAct.init()
                hdwAct.variablesReference = self.variables
                self.mainLog.addLine(returnString)
            

    def closeHardwareActions(self):
        """ this function is called when the user presses stop key. it should cleanly close or 
        shutdown all hardware. user must appropriately implement the hardware action close function"""
        for hdwAct in self.hardwareActions:
            if hdwAct.initialised:            
                returnString = hdwAct.close()
                self.mainLog.addLine(returnString)
    
    def _startSnake(self):
        """action call back from menu or toolbar. Simply starts the timer that
        polls the runner and makes the isRunning bool true  """
        self.mainLog.addLine("Experiment Snake Started", 1)
        self.isRunning=True
        self.getCurrentBlocking()        
        self.initialiseHardwareActions()
        self.startTimers()


    def newSequenceStarted(self):
        """called by GetCurrent Thread at the beginning of every sequence """
        if self.isRunning:#otherwise we have already stopped before new sequence began again
            self.getStatusUpdate()            
            self.mainLog.addLine("New cycle started: %s" % self.statusList[0],1)
            self.refreshExamineVariablesDictionary()# update the examine variables dictionary to reflect the latest values
            self.refreshVariableDependentCallbackTimes() # if a callback time is a timing edge name or variable name we must pull the value here
        else:
            self.mainLog.addLine("final connection closed")
        for hdwAct in self.hardwareActions:
            hdwAct.awaitingCallback=True
        
    def _stopSnakeToolbar(self):
        """if snake is stopped, addLine to main log and then run stopSnake """
        self.mainLog.addLine("Experiment Snake Stopped (you should still wait till the end of this sequence before continuing)",1)
        self._stopSnake()
        
    def _reloadHWAsToolbar(self):
        """if snake is stopped, addLine to main log and then run stopSnake """
        self.mainLog.addLine("Experiment Snake Stopped (you should still wait till the end of this sequence before continuing)",1)
        self._reloadHWAs()
        
    def _reloadHWAs(self):
        """if snake is stopped, addLine to main log and then run stopSnake """
        self.mainLog.addLine("Reloading hardware actions (advanced feature)",3)
        reload( hardwareAction.hardwareAction)
        reload( hardwareAction.sequenceLoggerHWA)
        reload( hardwareAction.dlicEvapHWA)
        reload( hardwareAction.dlicRFSweepHWA)
        reload( hardwareAction.dlicRFSweepHWA)
        reload( hardwareAction.evapAttenuationHWA)
        reload( hardwareAction.evapAttenuation2HWA)
        reload( hardwareAction.picomotorPlugHWA)
        reload( hardwareAction.windFreakOffsetLockHWA)
        #reload( hardwareAction.AOMChannelHWAs)#CAUSES REFERENCING PROBLEMS!
        reload( hardwareAction.experimentTablesHWA)
        reload( hardwareAction.windFreakOffsetLockHighFieldImagingHWA)
        reload( hardwareAction.greyMollassesOffsetFreqHWA)
        reload( hardwareAction.dlicRFSweepLZHWA)
        reload(hardwareAction.digitalMultimeterCurrentMeasureHWA)
        self.__init__()
        
    def stopTimers(self):
        """stops all timers with error catching """
        try:
            #stop any previous timer, should only have 1 timer at a time
            if self.connectionTimer is not None:
                self.connectionTimer.stop()
        except Exception as e:
            logger.error("couldn't stop current timer before starting new one: %s" % e.message)
        try:
            #stop any previous timer, should only have 1 timer at a time
            if self.statusStringTimer is not None:
                self.statusStringTimer.stop()
        except Exception as e:
            logger.error("couldn't stop current timer before starting new one: %s" % e.message)
        try:
            #stop any previous timer, should only have 1 timer at a time
            if self.getCurrentTimer is not None:
                self.getCurrentTimer.stop()
        except Exception as e:
            logger.error("couldn't stop current timer before starting new one: %s" % e.message)
            
    def _stopSnake(self):
        """Simply stops the timers, shuts down hardware and sets isRunning bool false  """
        self.stopTimers()
        self.closeHardwareActions()
        self.isRunning=False
        
    def startTimers(self):
        """This timer object polls the experiment runner regularly polling at any time"""
        #stop any previous timers
        self.stopTimers()
        #start timer 
        self.connectionTimer=Timer(self.connectionPollFrequency, self.getStatus)
        time.sleep(0.1)
        self.statusStringTimer=Timer(self.statusStringFrequency, self.updateStatusString)
        time.sleep(0.1)
        self.getCurrentTimer = Timer(self.getCurrentFrequency, self.getCurrent)
        """Menu action function to change logger level """
        logger.info("timers started")
    
    def getStatus(self):
        """calls the connection objects get status function and updates the statusList """
        logger.debug("starting getStatus")
        try:
            self.getStatusUpdate()
            self.checkForCallback()
        except Exception as e:
            logger.error("error in getStatus Function")
            logger.error("error: %s " % e.message)
            self.mainLog.addLine("error in getStatus Function. Error: %s" % e.message, 4)
            
    def getStatusUpdate(self):
        """Calls get status and updates times """
        try:
            statusString = self.connection.getStatus()
        except socket.error as e:
            logger.error("failed to get status . message=%s . errno=%s . errstring=%s " % (e.message, e.errno, e.strerror))
            self.mainLog.addLine("Failed to get status from Experiment Runner. message=%s . errno=%s . errstring=%s" % (e.message, e.errno, e.strerror),3)
            self.mainLog.addLine("Cannot update timeRunning - callbacks could be wrong this sequence!",4)
            return
        self.statusList = statusString.split("\n")
        timeFormat = '%d/%m/%Y %H:%M:%S'
        timeBegin = datetime.datetime.strptime(self.statusList[2],timeFormat )
        timeCurrent =  datetime.datetime.strptime(self.statusList[3],timeFormat )
        self.timeRunning = (timeCurrent-timeBegin).total_seconds()
        logger.debug("time Running = %s " % self.timeRunning)
        
    def checkForCallback(self):
        """if we've received a sequence, we check through all callback times and
        send off a callback on a hardware action if appropriate"""
        try:
            for hdwAct in [hdwA for hdwA in self.hardwareActions if hdwA.enabled]:#only iterate through enable hardware actions
                if hdwAct.awaitingCallback and self.timeRunning>=hdwAct.callbackTime:#callback should be started!
                    try:
                        logger.debug( "attempting to callback %s " % hdwAct.hardwareActionName)
                        hdwAct.setVariablesDictionary(self.variables)
                        logger.debug("vars dictionary set to %s " % self.variables)
                        callbackReturnString=hdwAct.callback()
                        self.mainLog.addLine("%s @ %s secs : %s" % (hdwAct.hardwareActionName, self.timeRunning, callbackReturnString),2)
                        hdwAct.awaitingCallback=False
                        hdwAct.callbackCounter += 1
                    except Exception as e:
                        logger.error("error while performing callback on %s. see error message below" % (hdwAct.hardwareActionName))
                        logger.error("error: %s " % e.message)
                        self.mainLog.addLine("error while performing callback on %s. Error: %s" % (hdwAct.hardwareActionName, e.message), 4)
        except Exception as e:
            logger.error("error in checkForCallbackFunction")
            logger.error("error: %s " % e.message)
            self.mainLog.addLine("error in checkForCallbackFunction. Error: %s" % e.message, 4)
            
            
    def getCurrent(self):
        """calls the connection objects get status function and updates the variables dictionary """
        if self.getCurrentThread and self.getCurrentThread.isAlive():
            #logger.debug( "getCurrent - already waiting - will not start new thread")
            #removed the above as it fills the log without any useful information
            self.sequenceStarted = False
            return
        else:
            logger.info( "starting getCurrent Thread")
            self.getCurrentThread = SocketThread()
            self.getCurrentThread.snakeReference = self # for calling functions of the snake
            self.getCurrentThread.start()
                      
    def getCurrentBlocking(self):
        """calls getCurrent and won't return until XML parsed. unlike above threaded function
        This is useful when starting up the snake so that we don't start looking for hardware events
        until a sequence has started and we have received XML"""        
        self.mainLog.addLine("Waiting for next sequence to start")
        self.xmlString = self.connection.getCurrent() # only returns at the beginning of a sequence! Experiment runner then returns the entire XML file
        logger.debug("length of xml string = %s " % len(self.xmlString))
        logger.debug("end of xml file is like [-30:]= %s" % self.xmlString[-30:])
        try:
            root = ET.fromstring(self.xmlString)        
            variables = root.find("variables")
            self.variables = {child[0].text:float(child[1].text) for child in variables}
            #timing edges dictionary : name--> value
            self.timingEdges = {timingEdge.find("name").text:float(timingEdge.find("value").text) for timingEdge in root.find("timing")}
            self.newSequenceStarted()
        except ET.ParseError as e: 
            self.mainLog.addLine("Error. Could not parse XML: %s" % e.message,3)
            self.mainLog.addLine("Possible cause is that buffer is full. is XML length %s>= limit %s ????" % (len(self.xmlString),self.connection.BUFFER_SIZE_XML),3 )
            logger.error( "could not parse XML: %s " % self.xmlString)
            logger.error(e.message)

    def updateStatusString(self):
        """update the status string with first element of return of GETSTATUS. 
        similiar to experiment control and camera control. It also does the analysis
        of progress that doesn't need to be as accurate (e.g. progress bar)"""
        logger.info("starting update status string")
        self.statusString = self.statusList[0] + "- Time Running = %s " % self.timeRunning
        self.queue = int(self.statusList[1])
        timeFormat = '%d/%m/%Y %H:%M:%S'
        timeBegin = datetime.datetime.strptime(self.statusList[2],timeFormat )
        timeEnd = datetime.datetime.strptime(self.statusList[4],timeFormat )
        self.timeTotal = (timeEnd-timeBegin).total_seconds()
        if self.timeRunning>self.timeTotal:
            self.haltedCount += 1
            self.runnerHalted = True
            if self.haltedCount ==0:
                logger.critical("runner was stopped.")
                self.mainLog.addLine("Runner stopped!",3)
                self.closeHardwareActions()
        else:
            if self.haltedCount>0:
                self.initialiseHardwareActions()
            self.haltedCount  = 0
            self.runnerHalted = False
        self.progress = 100.0 * self.timeRunning / self.timeTotal
        
    def _examineVariablesDictionary_default(self):
        if len(self.hardwareActions)>0:
            logger.debug("returning first hardware action %s for examineVariablesDictionary default" % self.hardwareActions[0].hardwareActionName)
            return variableDictionary.ExamineVariablesDictionary(hdwA=self.hardwareActions[0])#default is the first in the list
        else:
            logger.warning("hardwareActions list was empty. how should I populate variable examiner...?!.")
            return None
        
    def updateExamineVariablesDictionary(self, hdwA):
        """Populates the examineVariablesDictionary Pane appropriately. It is passed the 
        hdwA so that it can find the necessary variables"""
        self.examineVariablesDictionary.hdwA = hdwA
        self.examineVariablesDictionary.hardwareActionName = hdwA.hardwareActionName
        self.examineVariablesDictionary.updateDisplayList()
        logger.critical("examineVariablesDictionary changed")
        
    def refreshExamineVariablesDictionary(self):
        """calls the updateDisplayList function of examineVariables Dictionary 
        this updates the values in the display list to the latest values in variables
        dictionary. useful for refereshing at the beginning of a sequence"""
        self.examineVariablesDictionary.updateDisplayList()
        logger.info("refreshed examine variables dictionary")

    def refreshVariableDependentCallbackTimes(self):
        """if a HWA is variable dependent call back time, we refresh the value 
        using this function. THis should be called in each sequence"""
        [hdwA.parseCallbackTime() for hdwA in self.hardwareActions if hdwA.callbackTimeVariableDependent]
        

    def _changeLoggingLevelDebug(self):
        """Menu action function to change logger level """
        logger.setLevel(logging.DEBUG)


    def _changeLoggingLevelInfo(self):
        """Menu action function to change logger level """
        logger.setLevel(logging.INFO)


    def _changeLoggingLevelWarning(self):
        """Menu action function to change logger level """
        logger.setLevel(logging.WARNING)


    def _changeLoggingLevelError(self):
        """Menu action function to change logger level """
        logger.setLevel(logging.ERROR)
      
