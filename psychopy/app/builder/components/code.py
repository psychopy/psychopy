# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'code.png')
tooltip = 'Code: insert python commands into an experiment'

class CodeComponent(BaseComponent):
    categories = ['Custom']#an attribute of the class, determines the section in the components panel
    """An event class for inserting arbitrary code into Builder experiments"""
    def __init__(self, exp, parentName, name='code',beginExp="",beginRoutine="",eachFrame="",endRoutine="",endExperiment=""):
        self.type='Code'
        self.url="http://www.psychopy.org/builder/components/code.html"
        self.exp=exp#so we can access the experiment if necess
        #params
        self.categories=['misc']
        self.order = ['name','Begin Experiment', 'Begin Routine', 'Each Frame', 'End Routine', 'End Experiment'] # want a copy, else codeParamNames list gets mutated
        self.params={}
        self.params['name']=Param(name, valType='code', allowedTypes=[],
            hint="",
            label="Name") #This name does not actually need to be independent of the others.
        self.params['Begin Experiment']=Param(beginExp, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code at the start of the experiment (initialization); right-click checks syntax")
        self.params['Begin Routine']=Param(beginRoutine, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code to be run at the start of each repeat of the Routine (e.g. each trial); right-click checks syntax")
        self.params['Each Frame']=Param(eachFrame, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code to be run on every video frame during for the duration of this Routine; right-click checks syntax")
        self.params['End Routine']=Param(endRoutine, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code at the end of this repeat of the Routine (e.g. getting/storing responses); right-click checks syntax")
        self.params['End Experiment']=Param(endRoutine, valType='extendedCode', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code at the end of the entire experiment (e.g. saving files, resetting computer); right-click checks syntax")
    def writeInitCode(self,buff):
        buff.writeIndentedLines(unicode(self.params['Begin Experiment'])+'\n')
    def writeRoutineStartCode(self,buff):
        buff.writeIndentedLines(unicode(self.params['Begin Routine'])+'\n')
    def writeFrameCode(self,buff):
        buff.writeIndentedLines(unicode(self.params['Each Frame'])+'\n')
    def writeRoutineEndCode(self,buff):
        buff.writeIndentedLines(unicode(self.params['End Routine'])+'\n')
    def writeExperimentEndCode(self,buff):
        buff.writeIndentedLines(unicode(self.params['End Experiment'])+'\n')
