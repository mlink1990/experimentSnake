# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 09:42:22 2015

@author: User
"""
import socket # For sockets.
import time # For sockets.
import logging

logger=logging.getLogger("ExperimentSnake.hardwareAction.picomotorCommunication")

TCP_IP_PICOMOTOR_PLUG = '192.168.16.30'

class Picomotor:
    # Python wrapper class for Newport Picomotor 8742.
    def __init__(self, IP_ADDRESS):
        self.PORT = 23
        self.BUFFER_SIZE = 1024
        self.IP_ADDRESS = IP_ADDRESS
               
    def connect(self):
        # Python wrapper class for connecting to controller.
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.IP_ADDRESS, self.PORT))
            time.sleep(0.1)
            self.receive()
            logger.info( "Connected to %s on port %s " % (self.IP_ADDRESS, self.PORT))
            return True
        except socket.error as e:
            logger.error("socket error trying to connect to picomotor %s error message: %s " % (TCP_IP_PICOMOTOR_PLUG, e.message))
            return False
            
    def close(self):
        # Python wrapper for closing connection (socket) with controller.
        self.socket.close()
        
    def reconnect(self):
        # Python wrapper for reconnecting connection with the controller.
        self.close()
        self.connect()
        
    def send(self, commandString):
        # Python wrapper for sending command to controller.
        commandString += '\n'
        self.socket.send(commandString)
        time.sleep(0.1)

    def receive(self):
        # Python wrapper for receiving information from controller.
        data=self.socket.recv(self.BUFFER_SIZE)
        return data

    def ask(self, commandString):
        # Python wrapper for sending a a command intended to get information
        # from controller (with ? mark) and recieving that information.
        if commandString[-1] != '?':
            print 'this was not a question! command should end in ?.'
            return None
        self.send(commandString)
        return self.receive()
    
    def basicSettings(self):
        # Prints all revelent settings of controller/mirrors.
        print "Settings of the connected controller."
        print "IP: ", self.ask('IPADDR?'),
        print "ID: ", self.ask('*IDN?'),TCP_IP_PICOMOTOR_PLUG
        print "Motor status:"
        self.send('MC')
        motors = {0 : 'not connected!',
                  1 : 'of unknown type.',
                  2 : 'a tiny motor.',
                  3 : 'standart motor.'}
        for i in range(1,5):
            print "Motor %s is %s" % (i, motors[int(self.ask(str(i) + 'QM?'))])
        print "Motor acceleration:"
        for i in range(1,5):
            print "Motor %s set at %s steps/sec2." % (i, int(self.ask(str(i) + 'AC?')))
        print "Motor velocity:"
        for i in range(1,5):
            print "Motor %s set at %s steps/sec." % \
                    (i, int(self.ask(str(i) + 'VA?')))
            
    def move(self, axis, value, relative):
        # Wraps abstract move function (relative or absolute) to python function.
        if relative:
            command = 'PR'
        else:
            command = 'PA'
        if axis not in range(1,5):
            logger.error( 'Axis not between 1 and 4. NOT VALID!')
            return None
        if int(value) < -2**31 or int(value) > 2**31-1:
            logger.error( 'Absolute position is out of range.')
            return None
        if value > 0:
            value = '+' + str(value)
        self.send(str(axis) + command + str(value))

    def absoluteMove(self, axis, absPosition):
        # Wraps the PA (absolute move) command into a python function.
        self.move(axis, absPosition, False)
        
    def relativeMove(self, axis, distanceInSteps):
        # Wraps  the PR (relative move) command into a python function.
        self.move(axis, distanceInSteps, True)
        
    def setAcceleration(self, axis, accValue):
        # Sets a new acceleration for the specified axis.
        if axis not in range(1,5):
            logger.error(  'Axis not between 1 and 4. NOT VALID!')
            return None
        if int(accValue) < 0 or int(accValue) > 100000:
            logger.error(  'Acceleration value is invalid!')
            return None
        self.send(str(axis) + 'AC' + str(accValue))      
        
    def setVelocity(self, axis, velValue):
        # Sets a new velocity for the specified axis.
        if axis not in range(1,5):
            logger.error(  'Axis not between 1 and 4. NOT VALID!')
            return None
        if int(velValue) < 0 or int(velValue) > 2000:
            logger.error(  'Acceleration value is invalid!')
            return None
        self.send(str(axis) + 'VA' + str(velValue)) 
        
    def askPosition(self, axis):
        # Gets position of a motor from the controller.
        if axis not in range(1,5):
            logger.error(  'Axis not between 1 and 4. NOT VALID!')
            return None
        return int(self.ask(str(axis) + 'TP?'))
        
    def askAcceleration(self, axis):
        # Gets acceleration of a motor from the controller.
        if axis not in range(1,5):
            logger.error(  'Axis not between 1 and 4. NOT VALID!')
            return None
        return int(self.ask(str(axis) + 'AC?'))
        
    def askVelocity(self, axis):
        # Gets velocity of a motor from the controller.
        if axis not in range(1,5):
            logger.error(  'Axis not between 1 and 4. NOT VALID!')
            return None
        return int(self.ask(str(axis) + 'VA?'))
        
    def stopMotion(self):
        # Stops any mirror axis in motion.
        self.send('ST')
        
    def writeSettings(self):
        # Writes all set settings to non-volatile memory of controller.
        self.send('SM')
        
    def getHome(self, axis):
        # Gets a home position of an axis.
        return int(self.ask(str(axis) + 'DH?'))
        
    def setHome(self, axis, position):
        # Sets a home position of an axis.
        self.send(str(axis) + 'DH' + str(position))
        
    def restCheck(self, axis):
        # Checks if an axis is moving.
        return int(self.ask(str(axis) + 'MD?'))
        
if __name__=="__main__":
    pico = Picomotor(TCP_IP_PICOMOTOR_PLUG)
    #pico.absoluteMove(1,-9095)
