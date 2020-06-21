# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 10:42:27 2015

@author: tharrison
"""

import socket
import logging

logger=logging.getLogger("ExperimentSnake.hardwareAction.windFreakClient")
   
class Connection:
    """provides a wrapper to all the socket calls to request information
    from experiment runner. """
    
    def __init__(self, port=8888, IP_ADDRESS = "192.168.16.34"):
        self.PORT = port
        self.bufferSize = 1024
        self.IP_ADDRESS = IP_ADDRESS
        self.timeoutTime = 5.0 #seconds
               
    def connect(self):
        # Python wrapper class for connecting to controller.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.IP_ADDRESS, self.PORT))
        return self.receive()
        #time.sleep(0.1)
        
    def close(self):
        # Python wrapper for closing connection (socket) with controller.
        self.socket.close()
        
    def reconnect(self):
        # Python wrapper for reconnecting connection with the controller.
        self.close()
        self.connect()
        
    def send(self, commandString):
        # Python wrapper for sending command to controller.
        logger.debug("sending command: %s" % commandString)        
        commandString += '\n'        
        self.socket.sendall(commandString)
        #time.sleep(0.1)

    def receive(self):
        # Python wrapper for receiving information from controller.
        data=self.socket.recv(self.bufferSize)
        return data
        
    def sweep(self,startFrequencyMHz,endFrequencyMHz,stepSizeMHz,stepTimems ):
        """wrapper for producing the commandString for interepret  """
        cmd = "SWP %s %s %s %s" % (startFrequencyMHz,endFrequencyMHz,stepSizeMHz,stepTimems)
        self.send(cmd)
        return self.receive()
        
    def sweep2(self,startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime ):
        cmd = "SWP2 %s %s %s %s" % (startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime)
        self.send(cmd)
        return self.receive()
        
    def clearQueue(self):
        self.send("CLR")

class ConnectionConstantFrequency:
    """ WindFreak connection, where windFreak provides just a constant frequency """
    
    def __init__(self, port=8888, IP_ADDRESS = "192.168.16.55"):
        self.PORT = port
        self.bufferSize = 1024
        self.IP_ADDRESS = IP_ADDRESS
        self.timeoutTime = 5.0 #seconds
               
    def connect(self):
        # Python wrapper class for connecting to controller.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.IP_ADDRESS, self.PORT))
        return self.receive()
        #time.sleep(0.1)
        
    def close(self):
        # Python wrapper for closing connection (socket) with controller.
        self.socket.close()
        
    def reconnect(self):
        # Python wrapper for reconnecting connection with the controller.
        self.close()
        self.connect()
        
    def send(self, commandString):
        # Python wrapper for sending command to controller.
        logger.debug("sending command: %s" % commandString)        
        commandString += '\n'        
        self.socket.sendall(commandString)
        #time.sleep(0.1)

    def receive(self):
        # Python wrapper for receiving information from controller.
        data=self.socket.recv(self.bufferSize)
        return data

    def setPower(self,power):
        """wrapper for producing the commandString for interepret  """
        cmd = "POWER {:.2f}".format(power)
        self.send(cmd)
        return self.receive()
    
    def setFrequency(self,frequency):
        """wrapper for producing the commandString for interepret  """
        cmd = "FREQUENCY {:.6f}".format(frequency)
        self.send(cmd)
        return self.receive()
        
    # def sweep(self,startFrequencyMHz,endFrequencyMHz,stepSizeMHz,stepTimems ):
    #     """wrapper for producing the commandString for interepret  """
    #     cmd = "SWP %s %s %s %s" % (startFrequencyMHz,endFrequencyMHz,stepSizeMHz,stepTimems)
    #     self.send(cmd)
    #     return self.receive()
        
    # def sweep2(self,startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime ):
    #     cmd = "SWP2 %s %s %s %s" % (startFrequencyMHz,endFrequencyMHz,stepSizeMHz,sweepLengthTime)
    #     self.send(cmd)
    #     return self.receive()
        
    # def clearQueue(self):
    #     self.send("CLR")
        
if __name__=="__main__":
    conn = Connection(IP_ADDRESS="192.168.16.58")
    