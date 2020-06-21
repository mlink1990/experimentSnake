# -*- coding: utf-8 -*-
"""
Created on Thu May 28 09:22:05 2015

@author: tharrison

This defines the actual HWA for controlling an AOM channel on
one of Akos's box through the snake. All the automation is taken 
care of by the parent class. All the child class must do is define some
obvious but required variables

"""

from AOMChannelParentClass import AOMChannel
import logging
logger = logging.getLogger("ExperimentSnake.hardwareAction.AOMChannelHWAs")

IP_AOM_NaHigh = "192.168.16.6"
IP_AOM_NaLow = "192.168.16.7"
IP_AOM_Li = "192.168.16.8"
IP_AOM_Dipole = "192.168.16.22"

NAME_AOM_NaHigh = "Na High Freq"
NAME_AOM_NaLow = "Na Low Freq"
NAME_AOM_Li = "Li "
NAME_AOM_Dipole = "Dipole and Lattice"

def getChannelNumber(VCOLetter, VCOType):
    """Helper function to return a channel number.
    VCO letter should be a single letter in alphabet. Capitalised or not. 
    VCO Type should be either frequency or attenuation."""
    VCOLetter = VCOLetter.upper().strip()
    VCOType = VCOType.upper().strip()
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if VCOLetter not in alphabet:
        logger.error("unrecognised AOMChannel %s" %VCOLetter)
        return None
    if VCOType not in ["FREQUENCY", "ATTENUATION"]:
        logger.error("VCOType %s must be in[FREQUENCY, ATTENUATION] " %VCOType)
        return None
    if VCOType=="FREQUENCY":
        c=0
    elif VCOType=="ATTENUATION":
        c=1
    index = alphabet.index(VCOLetter)
    return index*2+c
        

class AOMChannelExample(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "ExperimentControlVariableName" # must match exactly the variable defined in experiment control
    hardwareActionName = "Hardware-Action-Name in snake e.g. Zeeman Slower Freq Control" # should be short but descriptive
    channelLetter="A" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO ZS"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelNaZSFreq(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaZSFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-ZS-Freq-Control" # should be short but descriptive
    channelLetter="A" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO ZS"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)       

class AOMChannelNaZSAtten(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaZSAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-ZS-Atten-Control" # should be short but descriptive
    channelLetter="A" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO ZS"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelNaMOTFreq(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaMOTFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-MOT-Freq-Control" # should be short but descriptive
    channelLetter="E" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO MOT"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)
    
class AOMChannelNaSpecFreq(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaSpecFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-Spec-Freq-Control" # should be short but descriptive
    channelLetter="D" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO Spectroscopy"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)     

class AOMChannelNaMOTAtten(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaMOTAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-MOT-Atten-Control" # should be short but descriptive
    channelLetter="E" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO MOT"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)


class AOMChannelNaZSEOMFreq(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaZSEOMFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-ZSEOM-Freq-Control" # should be short but descriptive
    channelLetter="B" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO ZS EOM"
    AOMBox_IP = IP_AOM_NaHigh  # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaHigh # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)   
    
class AOMChannelNaZSEOMAtten(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaZSEOMAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-ZSEOM-Atten-Control" # should be short but descriptive
    channelLetter="B" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO ZS EOM"
    AOMBox_IP = IP_AOM_NaHigh # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaHigh # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelNaDarkSpotAOMFreq(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaDSAOMFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-DSAOM-Freq-Control" # should be short but descriptive
    channelLetter="D" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO DSPOT AOM"
    AOMBox_IP = IP_AOM_NaHigh  # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaHigh # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)   
    
class AOMChannelNaDarkSpotAOMAtten(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaDSAOMAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-DSAOM-Atten-Control" # should be short but descriptive
    channelLetter="D" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO DSPOT AOM"
    AOMBox_IP = IP_AOM_NaHigh # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaHigh # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelNaMOTEOMAtten(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomNaMOTEOMAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-MOT-EOM-Atten-Control" # should be short but descriptive
    channelLetter="C" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO MOT EOM"
    AOMBox_IP = IP_AOM_NaHigh # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaHigh # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType) 
    
  

class AOMChannelLiOpticalPump(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomLiOptPumpFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-Opt-Pump-Freq-Control" # should be short but descriptive
    channelLetter="E" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO Optical Pump"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)


class AOMChannelLiMOTRep(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomLiMOTRepAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-MOT-Rep-Atten-Control" # should be short but descriptive
    channelLetter="A" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO MOT Repumper"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelLiMOTCool(AOMChannel):
    """Example of how to create a new HWA AOM Channel """
    variableName = "SnakeAomLiZSCoolAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-ZS-Cool-Atten-Control" # should be short but descriptive
    channelLetter="C" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO ZS Cool"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)
    
    
class AOMChannelNaImagingDP(AOMChannel):
    """Na double pass imaging"""
    variableName = "SnakeAomNaImagingDoublePassFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-Imaging-DP-Freq-Control" # should be short but descriptive
    channelLetter="H" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO Imaging"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)
    
class AOMChannelNa2to2OpticalPumpingFreq(AOMChannel):
    """Na 2 to 2 optical pumping """
    variableName = "SnakeAomNaOpticalPump2to2FreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-opt-pump-2to2-Freq-Control" # should be short but descriptive
    channelLetter="F" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO 2-2 Optical Pumping"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)
    
class AOMChannelNa2to2OpticalPumpingAtt(AOMChannel):
    """Na 2 to 2 optical pumping """
    variableName = "SnakeAomNaOpticalPump2to2AttVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-opt-pump-2to2-Att-Control" # should be short but descriptive
    channelLetter="F" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO 2-2 Optical Pumping"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)
    
    
class AOMChannelLiImaging(AOMChannel):
    """ Li imaging intensity """
    variableName = "SnakeAomLiImagingAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-Imaging-Atten-Control" # should be short but descriptive
    channelLetter="F" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO Imaging"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelLiImagingDetuning(AOMChannel):
    """ Li imaging detuning """
    variableName = "SnakeAomLiImagingFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-Imaging-Freq-Control" # should be short but descriptive
    channelLetter="F" # use capital letters please
    channelType = "FREQUENCY" # "FREQUENCY" or "ATTENUATION"
    VCOName = "VCO Imaging"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelLiPushPulseAttenuation(AOMChannel):
    """ Li imaging intensity """
    variableName = "SnakeAomLiPushPulseAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-Push-Pulse-Atten-Control" # should be short but descriptive
    channelLetter="G" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO Imaging"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelLiPushPulseDetuning(AOMChannel):
    """ Li imaging detuning """
    variableName = "SnakeAomLiPushPulseFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Li-Push-Pulse-Freq-Control" # should be short but descriptive
    channelLetter="G" # use capital letters please
    channelType = "FREQUENCY" # "FREQUENCY" or "ATTENUATION"
    VCOName = "VCO Imaging"
    AOMBox_IP = IP_AOM_Li # use definitions at top of script
    AOMBox_Name = NAME_AOM_Li # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

# class AOMChannelForceVerticalDipolePowerToZero(AOMChannel):
#     """ Sometimes the dipole AOM box crashes and sets the software part to full power. This HWA reminds it every cycle to stay at zero. """
#     variableName = "_" # must match exactly the variable defined in experiment control
#     hardwareActionName = "Dipole-Vertical-Force-To-Zero" # should be short but descriptive
#     channelLetter="B" # use capital letters please
#     channelType = "ATTENUATION" # "FREQUENCY" or "ATTENUATION"
#     VCOName = "VCO Dipole Vertical"
#     AOMBox_IP = IP_AOM_Dipole # use definitions at top of script
#     AOMBox_Name = NAME_AOM_Dipole # use definitions at top of script
#     channelNumber = getChannelNumber(channelLetter, channelType)
#     def mapVariables(self):
#         # we don't need a variable, since we want the attenuation to stay at zero => monkey-patch the variable look-up
#         return {"AOMChannelVoltage":0.0}
#     def __init__(self, callbackTimeInSequence, **traitsDict):
#         super(AOMChannelForceVerticalDipolePowerToZero,self).__init__(callbackTimeInSequence,**traitsDict)
#         self.variableMappings = {} # we don't need a variable, overwrite mappings

class AOMChannelNaHighFieldImagingFreq(AOMChannel):
    """Na 2 to 2 optical pumping """
    variableName = "SnakeAomNaHighFieldImagingFreqVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-high-field-imag-Freq-Control" # should be short but descriptive
    channelLetter="B" # use capital letters please
    channelType = "FREQUENCY" # or "ATTENUATION"
    VCOName = "VCO High Field Imaging"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)

class AOMChannelNaHighFieldImagingAtt(AOMChannel):
    """Na 2 to 2 optical pumping """
    variableName = "SnakeAomNaHighFieldImagingAttenVoltage" # must match exactly the variable defined in experiment control
    hardwareActionName = "Na-high-field-imag-Atten-Control" # should be short but descriptive
    channelLetter="B" # use capital letters please
    channelType = "ATTENUATION" # or "ATTENUATION"
    VCOName = "VCO High Field Imaging"
    AOMBox_IP = IP_AOM_NaLow # use definitions at top of script
    AOMBox_Name = NAME_AOM_NaLow # use definitions at top of script
    channelNumber = getChannelNumber(channelLetter, channelType)
