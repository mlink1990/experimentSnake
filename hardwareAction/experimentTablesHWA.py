# -*- coding: utf-8 -*-
"""
You can use the below as a standard template for a new hardware Action to be 
tied to experiment wizard using the experiment snake
"""

import hardwareAction
import logging
import threading
import os
import sqlite3
import datetime
import time

logger=logging.getLogger("ExperimentSnake.hardwareAction.experimentTables")

class SQLThread(threading.Thread):
    """This thread opens the DB connection and writes to the tables. it
    is a thread so that it does not block any other aspects of the snakes
    HWAs"""
    
    def run(self):
        logger.debug("beginning SQL Thread")
        #self.tables is a reference back to ExperimentTables object. Used to refer to useful attributes
        tables = self.tables
        snake = tables.snakeReference
        self.connection = sqlite3.connect(self.tables.database)
        self.cursor = self.connection.cursor()
        
        #table: times
        timeFormatControl = '%d/%m/%Y %H:%M:%S'
        timeFormatSQL = '%Y%m%d %H%M%S'
        timeBegin = datetime.datetime.strptime(snake.statusList[2],timeFormatControl )
        timestampString = timeBegin.strftime(timeFormatSQL)
        timeInteger = int(time.mktime(timeBegin.timetuple()))
        self.cursor.execute("INSERT INTO times VALUES (?,?);", (timestampString, timeInteger))
        
        #table: xml
        self.cursor.execute("INSERT INTO fullXML VALUES (?,?);", (timeInteger, snake.xmlString))
        
        #table: variables
        variableRows = [(timeInteger, variableName, variableValue) for variableName, variableValue in snake.variables.iteritems()]
        self.cursor.executemany("INSERT INTO variables VALUES (?,?,?);", variableRows )

        self.connection.commit()
        #table: changedVariables

        #table: images        

        self.connection.close()
        snake.mainLog.addLine("callback on %s finished (thread complete)" % (tables.hardwareActionName),2)


class ExperimentTables(hardwareAction.HardwareAction):
    
    def __init__(self, callbackTimeInSequence, **traitsDict):
        super(ExperimentTables,self).__init__(callbackTimeInSequence,**traitsDict)
        self.variableMappings = {}
        self.hardwareActionName = 'experiment-tables'
        
        #experiment tables variables
        self.groupFolder = os.path.join("\\\\ursa","AQOGroupFolder")
        self.database = os.path.join(self.groupFolder,"Experiment Humphry", "Data", "Experiment Tables", "experimentTables.sqlite3")
        
        logger.info( "%s object created successfully" % self.hardwareActionName)

    def init(self):
        """no init necessary for experiment tables we create and close the connection
        during each sequence call"""
        self.initialised=True
        return "%s init successful" % self.hardwareActionName

    def close(self):
        """no close necessary for experiment tables we create and close the connection
        during each sequence call"""

        return "%s closed" % self.hardwareActionName
        
    def callback(self):
        """Kicks off a thread that writes rows to the Experiment tables
        sqllite3 database"""
        logger.debug( "beginning %s callback" % self.hardwareActionName)        
        if not self.initialised:
            return "%s not initialised with init function. Cannot be called back until initialised. Doing nothing" % self.hardwareActionName
        try:#YOUR CALLBACK CODE SHOULD GO IN THIS TRY BLOCK!
            self.finalVariables = self.mapVariables()
            self.sqlThread = SQLThread()
            self.sqlThread.tables = self
            self.sqlThread.start()
            return "callback on %s started (thread begun)" % (self.hardwareActionName)
        except KeyboardInterrupt:
            raise
        except KeyError as e:
            return "Failed to find variable %s in variables %s. Check variable is defined in experiment control " % (e.message, self.variablesReference.keys())
        except Exception as e:
            return "Failed to perform callback on %s. Error message %s" % (self.hardwareActionName, e.message)
        
        