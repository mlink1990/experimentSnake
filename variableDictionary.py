# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 13:41:26 2015

@author: User
"""
#GUI Imports
import traits.api as traits
import traitsui.api as traitsui 
import hardwareAction.hardwareAction

import logging
logger=logging.getLogger("ExperimentSnake.variableDictionary")


class ExamineVariablesDictionary(traits.HasTraits):
    """simple wrapper class for displaying the contents of the variables dictionary
    for a particular hardware action"""
    hdwA = traits.Instance(hardwareAction.hardwareAction.HardwareAction)
    displayList = traits.List(traits.Str)
    hardwareActionName = traits.Str
    
    def __init__(self, **traitsDict):
        super(ExamineVariablesDictionary, self).__init__(**traitsDict)
    
    
    def generateDisplayList(self):
        """return a new python lis that is ready for display """
        dispList = []
        for v in self.hdwA.variables:
            if v in self.hdwA.variablesReference:
                value  = "%G" % self.hdwA.variablesReference[v] # string formatted float
            else:
                logger.warning("we are missing variable %s for hardware %s  in variable definitions" % (v, self.hardwareActionName))
                value = "?" # key not found could be we haven't loaded the dictionary or that the variable is missing in control
            dispList.append("%s = %s" % (v, value) )
        return dispList
        
    def updateDisplayList(self):
        """updates display list to be a list that contains the keys and values 
        of variablesList in nice strings for user to see"""
        self.displayList = self.generateDisplayList()
        
        
    def _displayList_default(self):
        return self.generateDisplayList()
        
    def _hardwareActionName_default(self):
        return self.hdwA.hardwareActionName
        
    traits_view = traitsui.View(
                    traitsui.VGroup(
                        traitsui.Item("hardwareActionName",show_label=False, style="readonly"),
                        traitsui.Item("displayList", editor=traitsui.ListEditor(style="readonly"), show_label=False)        
                                    )
                                )