# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param
from psychopy import prefs

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'parallelOut.png')
tooltip = 'Parallel out: send signals from the parallel port'

class ParallelOutComponent(BaseComponent):
    """A class for sending signals from the parallel port"""
    categories = ['I/O']
    def __init__(self, exp, parentName, name='p_port',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim='',
                address=None, startData="1", stopData="0",
                syncScreen = True):
        self.type='ParallelOut'
        self.url="http://www.psychopy.org/builder/components/parallelout.html"
        self.parentName=parentName
        self.exp=exp#so we can access the experiment if necess
        self.categories=['I/O']
        self.exp.requirePsychopyLibs(['parallel'])
        #params
        self.params={}
        self.order=['address', 'startData', 'stopData']
        self.params['name']=Param(name, valType='code', allowedTypes=[],
            hint="Everything needs a name",
            label="Name")
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the 'start' data get sent?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When does the 'end' data get sent?")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        #main parameters
        addressOptions = prefs.general['parallelPorts']
        self.params['address'] = Param(address, valType='str', allowedVals=addressOptions,
            hint="Parallel port to be used (you can change these options in preferences>general)")
        self.params['startData'] = Param(startData, valType='code', allowedTypes=[],
            hint="Data to be sent at 'start'")
        self.params['stopData'] = Param(stopData, valType='code', allowedTypes=[],
            hint="Data to be sent at 'end'")
        self.params['syncScreen']=Param(syncScreen, valType='bool',
            allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint="If the parallel port data relates to visual stimuli then sync its pulse to the screen refresh",
            label="Sync to screen")
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s = parallel.ParallelPort(address=%(address)s)\n" %(self.params))
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        routineClockName = self.exp.flow._currentRoutine._clockName

        buff.writeIndented("# *%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.status = STARTED\n" %(self.params))
        if not self.params['syncScreen'].val:
            buff.writeIndented("%(name)s.setData(int(%(startData)s))\n" %(self.params))
        else:
            buff.writeIndented("win.callOnFlip(%(name)s.setData, int(%(startData)s))\n" %(self.params))


        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.status = STOPPED\n" %(self.params))
            if not self.params['syncScreen'].val:
                buff.writeIndented("%(name)s.setData(int(%(stopData)s))\n" %(self.params))
            else:
                buff.writeIndented("win.callOnFlip(%(name)s.setData, int(%(stopData)s))\n" %(self.params))
            buff.setIndentLevel(-1, relative=True)#to get out of the if statement

        #dedent
#        buff.setIndentLevel(-dedentAtEnd, relative=True)#'if' statement of the time test and button check

    def writeRoutineEndCode(self,buff):
        #make sure that we do switch to stopData if the routine has been aborted before our 'end'
        buff.writeIndented("if %(name)s.status == STARTED:\n" %(self.params))
        if not self.params['syncScreen'].val:
            buff.writeIndented("    %(name)s.setData(int(%(stopData)s))\n" %(self.params))
        else:
            buff.writeIndented("    win.callOnFlip(%(name)s.setData, int(%(stopData)s))\n" %(self.params))
