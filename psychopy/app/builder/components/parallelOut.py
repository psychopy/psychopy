# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param
from psychopy import prefs

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'parallelOut.png')
tooltip = _translate('Parallel out: send signals from the parallel port')

# only use _localized values for label values, nothing functional:
_localized = {'address': _translate('Port address'), 'startData': _translate("Start data"),
              'stopData': _translate("Stop data"), 'syncScreen': _translate('Sync to screen')
              }

class ParallelOutComponent(BaseComponent):
    """A class for sending signals from the parallel port"""
    categories = ['I/O']
    def __init__(self, exp, parentName, name='p_port',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim='',
                address=None, startData="1", stopData="0",
                syncScreen = True):
        super(ParallelOutComponent, self).__init__(exp, parentName, name,
                startType=startType,startVal=startVal,
                stopType=stopType, stopVal=stopVal,
                startEstim=startEstim, durationEstim=durationEstim)
        self.type='ParallelOut'
        self.url="http://www.psychopy.org/builder/components/parallelout.html"
        self.categories=['I/O']
        self.exp.requirePsychopyLibs(['parallel'])
        #params
        self.order=['address', 'startData', 'stopData']

        #main parameters
        addressOptions = prefs.general['parallelPorts']+[u'LabJack U3']
        if not address:
            address = addressOptions[0]
        self.params['address'] = Param(address, valType='str', allowedVals=addressOptions,
            hint=_translate("Parallel port to be used (you can change these options in preferences>general)"),
            label=_localized['address'])
        self.params['startData'] = Param(startData, valType='code', allowedTypes=[],
            hint=_translate("Data to be sent at 'start'"),
            label=_localized['startData'])
        self.params['stopData'] = Param(stopData, valType='code', allowedTypes=[],
            hint=_translate("Data to be sent at 'end'"),
            label=_localized['stopData'])
        self.params['syncScreen']=Param(syncScreen, valType='bool',
            allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint=_translate("If the parallel port data relates to visual stimuli then sync its pulse to the screen refresh"),
            label=_localized['syncScreen'])
    def writeInitCode(self,buff):
        if self.params['address'].val == 'LabJack U3':
            buff.writeIndented("from psychopy.hardware import labjacks\n")
            buff.writeIndented("%(name)s = labjacks.U3()\n" %(self.params))
        else:
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
