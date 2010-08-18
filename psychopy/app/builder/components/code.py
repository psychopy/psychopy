# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'code.png')

class CodeComponent(BaseComponent):
    """An event class for inserting arbitrary code into Builder experiments"""
    def __init__(self, exp, parentName, name='code',beginExp="",beginRoutine="",eachFrame="",endRoutine="",endExperiment=""):
        self.type='Code'
        self.url="http://www.psychopy.org/builder/components/code.html"
        self.exp=exp#so we can access the experiment if necess
        #params
        self.order = ['name', 'Begin Experiment', 'Begin Routine', 'Each Frame', 'End Routine', 'End Experiment']#make sure that 'name' is at top of dlg
        self.params={}
        self.params['name']=Param(name, valType='code', allowedTypes=[],
            hint="This name does not actually need to be independent of the others.")
        self.params['Begin Experiment']=Param(beginExp, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code at the start of the experiment (initialization)")
        self.params['Begin Routine']=Param(beginRoutine, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code to be run at the start of each repeat of the Routine (e.g. each trial)")
        self.params['Each Frame']=Param(eachFrame, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code to be run on every video frame during for the duration of this Routine")
        self.params['End Routine']=Param(endRoutine, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code at the end of this repeat of the Routine (e.g. getting/storing responses)")
        self.params['End Experiment']=Param(endRoutine, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Code at the end of the entire experiment (e.g. saving files, resetting computer)")
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