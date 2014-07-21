# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import _base
from os import path
from psychopy.app.builder.experiment import Param
from psychopy.constants import *

__author__ = 'Jon Peirce'

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'static.png')
tooltip = 'Static screen period (e.g. an ISI). Useful for pre-loading stimuli.'

class StaticComponent(_base.BaseComponent):
    """A Static Component, allowing frame rendering to pause while disk is accessed"""
    #override the categories property below
    categories = ['Custom']#an attribute of the class, determines the section in the components panel
    def __init__(self, exp, parentName, name='ISI',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=0.5,
                startEstim='', durationEstim=''):
        _base.BaseComponent.__init__(self,exp,parentName,name=name)
        self.updatesList=[] # a list of dicts {compParams, fieldName}
        self.type='Static'
        self.url = "http://www.psychopy.org/builder/components/static.html"
        self.params['code']=Param("", valType='code',
            hint="Custom code to be run during the static period (after updates)",
            label="Custom code")
        self.order=['name']#make name come first (others don't matter)
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N'],
            hint="How do you want to define your end point?")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the stimulus start?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When does the stimulus end?")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s) of stimulus, purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s) of stimulus, purely for representing in the timeline")
    def addComponentUpdate(self, routine, compName, fieldName):
        self.updatesList.append({'compName':compName,'fieldName':fieldName, 'routine':routine})
    def remComponentUpdate(self, routine, compName, fieldName):
        #we have to do this in a loop rather than using the simple remove, because we
        for item in self.updatesList:
            if item=={'compName':compName,'fieldName':fieldName, 'routine':routine}:
                self.updatesList.remove(item)
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s = core.StaticPeriod(win=win, screenHz=expInfo['frameRate'], name='%(name)s')\n" %(self.params))
    def writeFrameCode(self,buff):
        self.writeStartTestCode(buff)
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        self.writeStopTestCode(buff)
    def writeStartTestCode(self,buff):
        """This will be executed as the final component in the routine
        """
        buff.writeIndented("# *%s* period\n" %(self.params['name']))
        _base.BaseComponent.writeStartTestCode(self, buff)

        if self.params['stopType'].val=='time (s)':
            durationSecsStr = "%(stopVal)s-t" %(self.params)
        elif self.params['stopType'].val=='duration (s)':
            durationSecsStr = "%(stopVal)s" %(self.params)
        elif self.params['stopType'].val=='duration (frames)':
            durationSecsStr = "%(stopVal)s*frameDur" %(self.params)
        elif self.params['stopType'].val=='frame N':
            durationSecsStr = "(%(stopVal)s-frameN)*frameDur" %(self.params)
        else:
            raise "Couldn't deduce end point for startType=%(startType)s, stopType=%(stopType)s" %(self.params)
        buff.writeIndented("%s.start(%s)\n" %(self.params['name'], durationSecsStr))
    def writeStopTestCode(self,buff):
        """Test whether we need to stop
        """
        buff.writeIndented("elif %(name)s.status == STARTED: #one frame should pass before updating params and completing\n" %(self.params))
        buff.setIndentLevel(+1, relative=True)#entered an if statement
        self.writeParamUpdates(buff)
        buff.writeIndented("%(name)s.complete() #finish the static period\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement

        pass #the clock.StaticPeriod class handles its own stopping
    def writeParamUpdates(self,buff, updateType=None):
        """Write updates. Unlike most components, which us this method to update
        themselves, the Static Component uses this to update *other* components
        """
        if updateType=='set every repeat':
            return #the static component doesn't need to change itself
        if len(self.updatesList):
            buff.writeIndented("# updating other components during *%s*\n" %(self.params['name']))
            for update in self.updatesList:
                #update = {'compName':compName,'fieldName':fieldName, 'routine':routine}
                compName = update['compName']
                fieldName = update['fieldName']
                routine = self.exp.routines[update['routine']]
                params = routine.getComponentFromName(unicode(compName)).params
                self.writeParamUpdate(buff, compName=compName,
                    paramName=fieldName,
                    val = params[fieldName], updateType=params[fieldName].updates, params=params)
            buff.writeIndented("# component updates done\n" %(self.params['name']))
