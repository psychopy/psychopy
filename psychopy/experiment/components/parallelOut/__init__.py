#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy import prefs

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'parallelOut.png')
tooltip = _translate('Parallel out: send signals from the parallel port')

# only use _localized values for label values, nothing functional:
_localized = {'address': _translate('Port address'),
              'startData': _translate("Start data"),
              'stopData': _translate("Stop data"),
              'syncScreen': _translate('Sync to screen')}


class ParallelOutComponent(BaseComponent):
    """A class for sending signals from the parallel port"""
    categories = ['I/O']

    def __init__(self, exp, parentName, name='p_port',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 address=None, startData="1", stopData="0",
                 syncScreen=True):
        super(ParallelOutComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'ParallelOut'
        self.url = "http://www.psychopy.org/builder/components/parallelout.html"
        self.categories = ['I/O']
        self.exp.requirePsychopyLibs(['parallel'])

        # params
        self.order = ['address', 'startData', 'stopData']

        # main parameters
        addressOptions = prefs.hardware['parallelPorts'] + [u'LabJack U3']
        if not address:
            address = addressOptions[0]

        msg = _translate("Parallel port to be used (you can change these "
                         "options in preferences>general)")
        self.params['address'] = Param(
            address, valType='str', allowedVals=addressOptions,
            hint=msg,
            label=_localized['address'])

        self.params['startData'] = Param(
            startData, valType='code', allowedTypes=[],
            hint=_translate("Data to be sent at 'start'"),
            label=_localized['startData'])

        self.params['stopData'] = Param(
            stopData, valType='code', allowedTypes=[],
            hint=_translate("Data to be sent at 'end'"),
            label=_localized['stopData'])

        msg = _translate("If the parallel port data relates to visual "
                         "stimuli then sync its pulse to the screen refresh")
        self.params['syncScreen'] = Param(
            syncScreen, valType='bool',
            allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['syncScreen'])

    def writeInitCode(self, buff):
        if self.params['address'].val == 'LabJack U3':
            code = ("from psychopy.hardware import labjacks\n"
                    "%(name)s = labjacks.U3()\n"
                    "%(name)s.status = None\n"
                    % self.params)
            buff.writeIndentedLines(code)
        else:
            code = ("%(name)s = parallel.ParallelPort(address=%(address)s)\n" %
                    self.params)
            buff.writeIndented(code)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        routineClockName = self.exp.flow._currentRoutine._clockName

        buff.writeIndented("# *%s* updates\n" % (self.params['name']))
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)

        if not self.params['syncScreen'].val:
            code = "%(name)s.setData(int(%(startData)s))\n" % self.params
        else:
            code = ("win.callOnFlip(%(name)s.setData, int(%(startData)s))\n" %
                    self.params)

        buff.writeIndented(code)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)

            if not self.params['syncScreen'].val:
                code = "%(name)s.setData(int(%(stopData)s))\n" % self.params
            else:
                code = ("win.callOnFlip(%(name)s.setData, int(%(stopData)s))\n" %
                        self.params)

            buff.writeIndented(code)

            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # dedent
# buff.setIndentLevel(-dedentAtEnd, relative=True)#'if' statement of the
# time test and button check

    def writeRoutineEndCode(self, buff):
        # make sure that we do switch to stopData if the routine has been
        # aborted before our 'end'
        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        if not self.params['syncScreen'].val:
            code = "    %(name)s.setData(int(%(stopData)s))\n" % self.params
        else:
            code = ("    win.callOnFlip(%(name)s.setData, int(%(stopData)s))\n" %
                    self.params)

        buff.writeIndented(code)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)