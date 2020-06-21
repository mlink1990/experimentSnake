# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 15:05:12 2015

@author: tharrison
"""
import socket
import os
        
class Connection:
    """provides a wrapper to all the socket calls to request information
    from experiment runner. """
    
    def __init__(self, port=8093, IP_ADDRESS = "192.168.16.2"):
        self.PORT = port
        self.BUFFER_SIZE = 4096
        self.BUFFER_SIZE_XML= 1048576  # what limit does Experiment runner use? TODO change this to value used by runner internally. If sequence gets big this can fail!#used to be 200000. Now I have set it to 2**20. Experiment snake wil print red error if this is a problem
        self.IP_ADDRESS = IP_ADDRESS
        self.timeoutTime = 80.0 #seconds
               
    def connect(self):
        # Python wrapper class for connecting to controller.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.IP_ADDRESS, self.PORT))
        #time.sleep(0.1)
        
    def close(self):
        # Python wrapper for closing connection (socket) with controller.
        #self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        
    def reconnect(self):
        # Python wrapper for reconnecting connection with the controller.
        self.close()
        self.connect()
        
    def send(self, commandString):
        # Python wrapper for sending command to controller.
        commandString += '\n'
        self.socket.sendall(commandString)
        #time.sleep(0.1)

    def receive(self, bufferSize):
        # Python wrapper for receiving information from controller.
        data=self.socket.recv(bufferSize)
        return data
    
    def getStatus(self):
        """returns the full status string to be parsed """
        try:
            self.connect()        
            self.send("GETSTATUS")
            response = self.receive(self.BUFFER_SIZE)
        finally:
            self.close()
        return response
        
    def getCurrent(self):
        """returns the full status string to be parsed """
        try:
            self.connect()
            #self.socket.settimeout(self.timeoutTime)
            self.send("GETCURRENT")
            response = self.receive(self.BUFFER_SIZE_XML)
        finally:
            self.close()
        return response
        
    def enqueue(self, xml):
        """uses the enqueue command to send an xml experiment control sequence to the runner """
        try:
            self.connect()
            filename = os.path.join("\\\\ursa","AQOGroupFolder","Experiment Humphry", "Experiment Control And Software", "currentSequence", "generatedSequence.xml")
            self.send("ENQUEUE\n"+filename+"\n"+xml)
        finally:
            self.close()
    