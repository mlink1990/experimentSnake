# -*- coding: utf-8 -*-
"""
Created on Sat Feb 06 16:31:49 2016


@author: tim

simple script that when run defines python functions
that can be used to return the appropriate imaging frequency
for Li6 in a magnetic field. User must supply to the function
the polarisation and the field size.

If more than one imaging resonance exists for a given field/polarisation
the strongest transition frequency is given

calculations were done using : mathematica sheets in this directory

csv files for interpolation are stored in data

data structure in files is
BField (G),freq polarisation=-1,rel. intensity polarisation=-1,freq polarisation=0,rel. intensity polarisation=0,freq polarisation=1,rel. intensity polarisation=1

importing this file might take a while as it reads all data and makes interpolation functions.

Hence it should be part of the init of a HWA
"""
import os
import scipy
import scipy.interpolate
import logging

logger =logging.getLogger("ExperimentSnake.hardwareAction.highFieldImaging")

class HighFieldImaging:
    """class that loads interpolation functions for high field imaging.
    class structure means module can be imported quickly without creating all the 
    interpolation functions...

    +ve frequency on this graph is red detuning from 0 field resonance

    -ve frequency on this graph is blue detuning from 0 field resonance

    """

    def __init__(self):
        logger.debug("high field imaging initialised")
        
        
    def load(self, loadInverse=False):
        """call this function to calculate/load all the interpolation functions.
        Can be recalled if the data files are redefined without closing or destroying
        object"""
        
        fullPath = os.path.join("\\\\ursa", "AQOGroupFolder", "Experiment Humphry", "Experiment Control And Software","experimentSnake", "hardwareAction", "highFieldImaging")
        dataFolder = "data"
        dataFolder = os.path.join(fullPath, dataFolder)
        
        dataFileState1 = "Li6-transistions-BField-state1.csv"
        dataFileState2 = "Li6-transistions-BField-state2.csv"
        dataFileState3 = "Li6-transistions-BField-state3.csv"
        dataFileState4 = "Li6-transistions-BField-state4.csv"
        dataFileState5 = "Li6-transistions-BField-state5.csv"
        dataFileState6 = "Li6-transistions-BField-state6.csv"
        
        #maps state numbers to filenames
        self.states = [1,2,3,4,5,6]
        dataFiles = {1:dataFileState1,2:dataFileState2,3:dataFileState3,4:dataFileState4,5:dataFileState5,6:dataFileState6}
        
        self.frequencyFunctions = {} #state--> [functionSigmaMinus, functionPi, functionSigmaPlus]
        self.strengthFunctions = {} #state--> [functionSigmaMinus, functionPi, functionSigmaPlus]
        self.inverseFrequencyFunctions = {}
        self.BfieldsDict = {}
        for state in self.states:
            
            path = os.path.join(dataFolder,dataFiles[state])
            data = scipy.loadtxt(path,skiprows=1,delimiter=",")    
            
            Bfields = data[:,0]
            freqSigmaMinus = data[:,1] 
            strengthSigmaMinus = data[:,2] 
            freqPi = data[:,3] 
            strengthPi = data[:,4] 
            freqSigmaPlus = data[:,5] 
            strengthSigmaPlus = data[:,6] 
        
            self.BfieldsDict[state]= Bfields   
            
            freqSigmaMinusFunction=scipy.interpolate.UnivariateSpline(Bfields, freqSigmaMinus)
            freqPiFunction=scipy.interpolate.UnivariateSpline(Bfields, freqPi)
            freqSigmaPlusFunction=scipy.interpolate.UnivariateSpline(Bfields, freqSigmaPlus)
            
            strengthSigmaMinusFunction=scipy.interpolate.UnivariateSpline(Bfields, strengthSigmaMinus)
            strengthPiFunction=scipy.interpolate.UnivariateSpline(Bfields, strengthPi)
            strengthSigmaPlusFunction=scipy.interpolate.UnivariateSpline(Bfields, strengthSigmaPlus)
            
            self.frequencyFunctions[state] = [freqSigmaMinusFunction,freqPiFunction,freqSigmaPlusFunction]
            self.strengthFunctions[state]  = [strengthSigmaMinusFunction,strengthPiFunction,strengthSigmaPlusFunction]
            
            if loadInverse:
                #if true then we create inverse functions as well e.g freq --> field
                invFreqSigmaMinusFunction=scipy.interpolate.UnivariateSpline( freqSigmaMinus,Bfields)
                invFreqPiFunction=scipy.interpolate.UnivariateSpline( freqPi,Bfields)
                invFreqSigmaPlusFunction=scipy.interpolate.UnivariateSpline( freqSigmaPlus,Bfields)
                self.inverseFrequencyFunctions[state] = [invFreqSigmaMinusFunction,invFreqPiFunction,invFreqSigmaPlusFunction]
                
    def plotFrequencies(self,polarisation):
        import matplotlib.pyplot as plt
        for state in self.states:
            plt.plot(self.BfieldsDict[state],self.frequencyFunctions[state][polarisation+1](self.BfieldsDict[state]),label="|%s>"% state)
        plt.legend()
        plt.show()
        
    def plotStrengths(self,polarisation):
        import matplotlib.pyplot as plt
        for state in self.states:
            plt.plot(self.BfieldsDict[state],self.strengthFunctions[state][polarisation+1](self.BfieldsDict[state]),label="|%s>"% state)
        plt.legend()
        plt.show()
        
    def plotStrengths2(self,state):
        import matplotlib.pyplot as plt
        for polarisation in [-1,0,1]:
            plt.plot(self.BfieldsDict[state],self.strengthFunctions[state][polarisation](self.BfieldsDict[state]),label="polarisation=%s"% polarisation)
        plt.legend()
        plt.show()
        
    def plotFrequencies2(self,state):
        import matplotlib.pyplot as plt
        for polarisation in [-1,0,1]:
            plt.plot(self.BfieldsDict[state],self.frequencyFunctions[state][polarisation](self.BfieldsDict[state]),label="polarisation=%s"% polarisation)
        plt.legend()
        plt.show()
    
    def imagingFrequency(self, BField, state, polarisation):
        """BField = float B field in Gauss
        state  = integer 1 to 6 represents state you are trying to image
        polarisation = -1, 0, 1 for sigma minus, pi and sigmaPlus"""
        return float(self.frequencyFunctions[state][polarisation+1](BField))
        
    def imagingStrength(self, BField, state, polarisation):
        """BField = float B field in Gauss
        state  = integer 1 to 6 represents state you are trying to image
        polarisation = -1, 0, 1 for sigma minus, pi and sigmaPlus"""
        return float(self.strengthFunctions[state][polarisation+1](BField))
        
    def fittedField(self, BFieldExperimentControl):
        """insert the experiment control field value and get a value close to the real field value  """
        return  0.1394343058461323 + 0.9878021530914608*BFieldExperimentControl - 0.000013629201702565624*(BFieldExperimentControl)**2 + 8.165208505353147E-9*BFieldExperimentControl**3
        

    
if __name__=="__main__":
    BGauss = 1200.
    state = 1
    polarisation = -1
    f0=0.
    hfi = HighFieldImaging()
    hfi.load(loadInverse = True)
    deltaf = hfi.imagingFrequency(BGauss, state, polarisation)
    extraShift = 0
    freq = f0-deltaf+extraShift
    print "state |%s> polarisation=%s @ %s G ---> final freq = %s" % (state,polarisation,BGauss,freq )
    
    temp=[-226.8694378,
    -203.9393098,
    -184.3332797,
    -146.0449003,
    -43.69418218,
    30.58189384,
    104.0091274,
    246.1693459,
    317.594834,
    387.5564862,
    456.2276615,
    526.2817193,
    595.3582484,
    663.9617572,
    734.0629836,
    804.6326656,
    871.6415415,
    941.060349,
    1009.859826,
    1078.510712,
    1147.483743,
    1217.249657,
    1285.779194,
    1354.543091,
    1422.012086
    ]
