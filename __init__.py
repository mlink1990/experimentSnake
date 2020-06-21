# -*- coding: utf-8 -*-
"""
Created on Fri Mar 13 07:08:10 2015

@author: tharrison
"""

try:
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'
except ValueError as e:
    print "Error loading QT4. QT4 is required for CSVMaster"
    print "error was: "+ str(e.message)
    pass

import logging
from logging.handlers import TimedRotatingFileHandler
import os

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] [%(threadName)s] [%(name)s] [func=%(funcName)s:line=%(lineno)d] %(message)s")
#see https://docs.python.org/2/library/logging.html#logrecord-attributes for formatting options
logger=logging.getLogger("ExperimentSnake")
logger.setLevel(logging.WARNING)

if __file__ is None:
    logger.critical("Experiment Snake was not able to resolve the __file__ attribute. This means it won't be able to find the config and log folders. Are you sure you are starting CSVMaster correctly? Just double click on __init__.py")

configPath = os.path.join( os.path.dirname(__file__), 'config' )
if os.path.exists( configPath ) is False:
    logger.warning("Did not find a folder called config. Attempting to create folder config.")
    # If the config directory does not exist, create it
    os.mkdir( configPath )

logPath = os.path.join( os.path.dirname(__file__), 'log' )
if os.path.exists( logPath ) is False:
    logger.warning("Did not find a folder called log. Attempting to create folder log.")
    # If the log directory does not exist, create it
    os.mkdir( logPath )

#ENABLE TO LOG TO FILE
LOG_TO_FILE = False
if LOG_TO_FILE:
    logFilePath = os.path.join( logPath, 'ExperimentSnake.log' )
    timedRotatingFileHandler = TimedRotatingFileHandler( logFilePath , when='D', interval=1, backupCount=14)
    timedRotatingFileHandler.setFormatter(logFormatter)
    logger.addHandler(timedRotatingFileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

version = "1.0"
author = "Timothy Harrison"
__version__ = "1.0"

welcomeString= """Welcome to Experiment Snake version %s written by %s. Report bugs to 
%s. See text at beginning of __init__.py for more information.""" % (version, author,author)


if __name__ == '__main__':
    logger.info(welcomeString)
    consoleHandler.flush()
    
    import experimentSnake
    snake = experimentSnake.ExperimentSnake()
    
    if os.name == 'nt':
        import ctypes
        logger.debug("changing to use a seperate process (Windows 7 only)")
        myappid = str(snake) # arbitrary string
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            logger.error("Failed to start a seperate process. This will only work on Windows 7 or later. Are you running on XP? If so everything works but can't create a new process window")
            pass
    snake.configure_traits()
