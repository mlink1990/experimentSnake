#!/usr/bin/env python

"""Arduino DAC controll
 * pyArdDAC.py
 * Python module for the Arduino DAC
 *
 * Author: Akos Hoffmann <akos.hoffmann@gmail.com>
 * 
 * 
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details. 
"""
 
__version__ = '1.0.0'
__date__ = '2014-06-20'
__all__ = ["ArdDAC"]

import socket
import sys
import struct
import time

class ARD_DAC:
    """Use this class to communicate with the Arduino DAC"""
    def __init__(self, HOST='192.168.16.6', PORT = 8888, DEBUG = False):
        self.host = HOST
        self.port = PORT
        self.timeout = 1
        self.debug = DEBUG
        #self.sock=''
        
    def calcCrc16Str(self,inputstring):
        """Adapted from MinimalModbus"""
        POLY = 0xA001                  # Constant for MODBUS CRC-16
        register = 0xFFFF              # Preload a 16-bit register with ones
        for character in inputstring:
            register = register ^ ord(character)           # XOR with each character
            for i in range(8):                             # Rightshift 8 times, and XOR with polynom if carry overflows
                carrybit = register & 1
                register = register >> 1
                if carrybit == 1:
                    register = register ^ POLY
        result = struct.pack('<H', register)
        return result
        
    def SendUDP(self, function=chr(128), data='\xff\xff\x00\x00'): 
        try:
            if self.debug:
                print "DEBUG>>> function", function
                print "DEBUG>>> data", function
            message = function + data 
            message = self.calcCrc16Str(message) + message  
            if self.debug:
                print 'DEBUG>>> '+ 'Sending "%s"' % ':'.join(hex(ord(x))[2:] for x in message)
                print "UDP target IP:", self.host
                print "UDP target port:", self.port
            
            sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
            if self.debug:
                print 'DEBUG>>> socket opened...' 
                print 'message = ', message
            sock.sendto(message, (self.host, self.port))
            
            if self.debug:
                print 'DEBUG>>> message sent...'
        except Exception as e:
           print e.message
           print 'error'
                       
    def SetSubnetMask(self, ip='255.255.0.0'): 
        self.SendUDP(function=chr(128), data= ''.join([chr(int(x)) for x in ip.split('.')]))      

    def SetIP(self, ip='192.168.1.99'): 
        self.SendUDP(function=chr(129), data= ''.join([chr(int(x)) for x in ip.split('.')]))
        
    def SetGW(self, ip='0.0.0.0'): 
        self.SendUDP(function=chr(130), data= ''.join([chr(int(x)) for x in ip.split('.')]))

    def SetDNS(self, ip='0.0.0.0'): 
        self.SendUDP(function=chr(131), data= ''.join([chr(int(x)) for x in ip.split('.')]))
        
    def SetMAC(self, mac='90-A2-DA-0F-46-EE'): 
        self.SendUDP(function=chr(132), data= ''.join([chr(int('0x'+x,16)) for x in mac.split('-')]))
        
    def SetPort(self, p=8888): 
        self.SendUDP(function=chr(135), data= ''.join([chr(p & 0xff),chr((p & 0xff00)>>8) ]))     

    def SetSerialNum(self, s=1): 
        self.SendUDP(function=chr(133), data= struct.pack('l', s))  

    def DebugOn(self): 
        self.SendUDP(function=chr(140), data='')  

    def DebugOff(self): 
        self.SendUDP(function=chr(141), data='')  

    def Reset(self):
        self.SendUDP(function=chr(136), data='')  
        
    def Write_New_Config(self):
        self.SendUDP(function=chr(137), data='')  
          
    def SetName(self, name='DAC V0.1'): 
        self.SendUDP(function=chr(134), data= name+chr(0))  

    def SetDACdefaults(self, ch=0, value=123): 
        self.SendUDP(function=chr(2), data=''.join([chr(ch),chr(value & 0xff),chr((value & 0xff00)>>8) ])) 
        
    def SetDAC(self, ch=0, value=123): 
        self.SendUDP(function=chr(1), data=''.join([chr(ch),chr(value & 0xff),chr((value & 0xff00)>>8) ])) 
     
    def WriteDACdefaults(self): 
        self.SendUDP(function=chr(138), data='') 
        

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-ch", type=int, help="the DAC channel", default=0)
    parser.add_argument("-v", type=int, help="the value", default=32768)
    parser.add_argument("-ip",  help="the IP (default: 192.168.1.99)", default="192.168.16.7")
    parser.add_argument("-port", type=int, help="the UDP port (default: 8888)", default=8888)
    args = parser.parse_args()

    DAC = ARD_DAC( HOST=args.ip, PORT = args.port, DEBUG=False)

    #DAC = ARD_DAC( HOST='192.168.1.100', PORT = 8888, DEBUG=False)

    from Tkinter import * 
    class App:                                 #to understand: http://effbot.org/tkinterbook/tkinter-hello-again.htm
        def __init__(self, master):
            frame = Frame(master)
            frame.pack()

            self.ch_sel = LabelFrame(master, text="Channel", padx=5, pady=5)
            self.ch_sel.place(x = 10, y = 5)
            self.chselect = Spinbox(self.ch_sel, from_=0, to=16, width = 3)
            self.chselect.pack()
            self.chselect.delete(0,"end")
            self.chselect.insert(0, ("%d" % (args.ch))) 
            
            self.var = IntVar()
            
            self.ch_val = LabelFrame(master, text="Value", padx=5, pady=5)
            self.ch_val.place(x = 80, y = 5)
            self.valselect = Spinbox(self.ch_val, from_=0, to=65535, width = 6, command=self.setdac2, textvariable=self.var)
            self.valselect.pack()

            
            self.ch_valV = LabelFrame(master, text="Value in Volt", padx=5, pady=5)
            self.ch_valV.place(x = 160, y = 5)
            self.valVselect = Spinbox(self.ch_valV, from_=0, to=5, format='%.4f', width = 7, command=self.setdac_in_volt, increment=0.01)
            self.valVselect.pack()
            
            self.scale = Scale( root, variable = self.var ,from_=0, to=65535, orient=HORIZONTAL, length=680, command=self.setdac)
            self.scale.set(32768);
            self.scale.place(x = 10, y = 60)
            self.scale.set(args.v)
            
            self.iplab = Label(root, text="IP: " + args.ip + "  Port: " + ("%d" %(args.port)))
            self.iplab.place(x = 540, y = 5)
 
        def setdac(self, newvalue):
             print "DEBUG>>> newvalue", newvalue
             DAC.SetDAC(ch=int(self.chselect.get()), value=int(newvalue))   
             self.valVselect.delete(0,"end")
             self.valVselect.insert(0, ("%.4f" % (5.0/65535*int(newvalue))))
        
        def setdac2(self):
             v=int(self.valselect.get())
             DAC.SetDAC(ch=int(self.chselect.get()), value=v)   
             self.scale.set(v)
             self.valVselect.delete(0,"end")
             self.valVselect.insert(0, ("%.4f" % (5.0/65535*v))) 
         
        def setdac_in_volt(self):
             v=int(65535/5*float(self.valVselect.get()))
             self.scale.set(v);

    root = Tk()
    root.title("Set Arduino DAC")
    root.geometry("700x120")
    app = App(root)
    root.mainloop()

