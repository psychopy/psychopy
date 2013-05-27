# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
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
        self.params['code']=Param("", valType='code',
            hint="Custom code to be run during the static period (after updates)",
            label="Custom code")
        self.order=['name']#make name come first (others don't matter)
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
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
        pass
    def writeFrameCode(self,buff):
        self.writeStartTestCode(buff)
        self.writeParamUpdates(buff)
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        self.writeStopTestCode(buff)
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
    def writeStartTestCode(self,buff):
        """This will be executed as the final component in the routine
        """
        buff.writeIndented("# *%s* period\n" %(self.params['name']))
        _base.BaseComponent.writeStartTestCode(self, buff)
    def writeStopTestCode(self,buff):
        """Test whether we need to stop
        """
        if self.params['stopType'].val=='time (s)':
            buff.writeIndented("elif %(name)s.status == STARTED and (%(stopVal)s-frameDur) < t <= %(stopVal)s:\n" %(self.params))
            buff.writeIndented("    # successfully within one frame of finish - our work is done\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("elif %(name)s.status == STARTED and t > %(stopVal)s:\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("    logging.warn('We overshot the intended duration of %(name)s." %(self.params) +
                "Probably the associated Component updates took too long.')\n" )
        #duration in time (s)
        elif self.params['stopType'].val=='duration (s)' and self.params['startType'].val=='time (s)':
            buff.writeIndented("elif %(name)s.status == STARTED and (%(startVal)s+%(stopVal)s-frameDur) < t <= (%(startVal)s+%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    # successfully within one frame of finish - our work is done\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("elif %(name)s.status == STARTED and t > (%(startVal)s+%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("    logging.warn('We overshot the intended duration of %(name)s." %(self.params) +
                "Probably the associated Component updates took too long.')\n" )
        #start at frame and end with duration (need to use approximate)
        elif self.params['stopType'].val=='duration (s)':
            buff.writeIndented("elif %(name)s.status == STARTED and (%(name)s.tStart+%(stopVal)s-frameDur) t <= (%(name)s.tStart+%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    # successfully within one frame of finish - our work is done\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("elif %(name)s.status == STARTED and t > (%(name)s.tStart+%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("    logging.warn('We overshot the intended duration of %(name)s." %(self.params) +
                "Probably the associated Component updates took too long.')\n" )
        #duration in frames
        elif self.params['stopType'].val=='duration (frames)':
            buff.writeIndented("elif %(name)s.status == STARTED and (%(name)s.frameNStart+%(stopVal)s-1) < frameN <= (%(name)s.frameNStart+%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    # successfully within one frame of finish - our work is done\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("elif %(name)s.status == STARTED and frameN > (%(name)s.frameNStart+%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("    logging.warn('We overshot the intended duration of %(name)s." %(self.params) +
                "Probably the associated Component updates took too long.')\n" )
        #stop frame number
        elif self.params['stopType'].val=='frame N':
            buff.writeIndented("elif %(name)s.status == STARTED and (%(stopVal)s-1) < frameN <= %(stopVal)s:\n" %(self.params))
            buff.writeIndented("    # successfully within one frame of finish - our work is done\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("elif %(name)s.status == STARTED and frameN > %(stopVal)s:\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
            buff.writeIndented("    logging.warn('We overshot the intended duration of %(name)s." %(self.params) +
                "Probably the associated Component updates took too long.')\n" )
        #end according to a condition
        elif self.params['stopType'].val=='condition':
            logging.warn("The Static Component '%s' has been set to stop according to a condition rather than a set time. This is not recommended" %self.params['name'])
            buff.writeIndented("elif %(name)s.status == STARTED and (%(stopVal)s):\n" %(self.params))
            buff.writeIndented("    %(name)s.status == FINISHED\n" %(self.params))
        else:
            raise "Didn't write any stop line for startType=%(startType)s, stopType=%(stopType)s" %(self.params)
        buff.setIndentLevel(+1,relative=True)
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
            params = routine.getComponentFromName(compName.val).params
            self.writeParamUpdate(buff, compName=compName,
                paramName=fieldName,
                val = params[fieldName], updateType=params[fieldName].updates, params=params)
