#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy import prefs


class ParallelOutComponent(BaseComponent):
    """A class for sending signals from the parallel port"""

    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'parallel.png'
    tooltip = _translate('Parallel out: send signals from the parallel port')

    def __init__(self, exp, parentName, name='p_port',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 address=None, register='EIO', startData="1", stopData="0",
                 syncScreen=True):
        super(ParallelOutComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'ParallelOut'
        self.url = "https://www.psychopy.org/builder/components/parallelout.html"
        self.exp.requirePsychopyLibs(['parallel'])

        # params
        self.order += [
            'startData', 'stopData',  # Data tab
            'address',  'register',   # Hardware tab
        ]

        # main parameters
        addressOptions = prefs.hardware['parallelPorts'] + [u'LabJack U3'] + [u'USB2TTL8'] 
        if not address:
            address = addressOptions[0]

        msg = _translate("Parallel port to be used (you can change these "
                         "options in preferences>general)")
        self.params['address'] = Param(
            address, valType='str', inputType="choice", allowedVals=addressOptions,
            categ='Hardware', hint=msg, label=_translate("Port address"))

        self.depends.append(
            {"dependsOn": "address",  # must be param name
             "condition": "=='LabJack U3'",  # val to check for
             "param": "register",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        msg = _translate("U3 Register to write byte to")
        self.params['register'] = Param(register, valType='str',
                                        inputType="choice", allowedVals=['EIO', 'FIO'],
                                        categ='Hardware', hint=msg, label=_translate("U3 register"))

        self.params['startData'] = Param(
            startData, valType='code', inputType="single", allowedTypes=[], categ='Data',
            hint=_translate("Data to be sent at 'start'"),
            label=_translate("Start data"))

        self.params['stopData'] = Param(
            stopData, valType='code', inputType="single", allowedTypes=[], categ='Data',
            hint=_translate("Data to be sent at 'end'"),
            label=_translate("Stop data"))

        msg = _translate("If the parallel port data relates to visual "
                         "stimuli then sync its pulse to the screen refresh")
        self.params['syncScreen'] = Param(
            syncScreen, valType='bool', inputType="bool", categ='Data',
            allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Sync to screen"))

    def writeInitCode(self, buff):
        if self.params['address'].val == 'LabJack U3':
            code = ("from psychopy.hardware import labjacks\n"
                    "%(name)s = labjacks.U3()\n"
                    "%(name)s.status = None\n"
                    % self.params)
            buff.writeIndentedLines(code)
        elif self.params['address'].val == 'USB2TTL8':
            code = ("from psychopy.hardware import labhackers\n"
                    "%(name)s = labhackers.USB2TTL8()\n"
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
        indented = self.writeStartTestCode(buff)
        if indented:
            buff.writeIndented("%(name)s.status = STARTED\n" % self.params)

            if self.params['address'].val == 'LabJack U3':
                if not self.params['syncScreen'].val:
                    code = "%(name)s.setData(int(%(startData)s), address=%(register)s)\n" % self.params
                else:
                    code = ("win.callOnFlip(%(name)s.setData, int(%(startData)s), address=%(register)s)\n" %
                            self.params)
            else:
                if not self.params['syncScreen'].val:
                    code = "%(name)s.setData(int(%(startData)s))\n" % self.params
                else:
                    code = ("win.callOnFlip(%(name)s.setData, int(%(startData)s))\n" %
                            self.params)

            buff.writeIndented(code)

        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        if indented:
            if self.params['address'].val == 'LabJack U3':
                if not self.params['syncScreen'].val:
                    code = "%(name)s.setData(int(%(stopData)s), address=%(register)s)\n" % self.params
                else:
                    code = ("win.callOnFlip(%(name)s.setData, int(%(stopData)s), address=%(register)s)\n" %
                            self.params)
            else:
                if not self.params['syncScreen'].val:
                    code = "%(name)s.setData(int(%(stopData)s))\n" % self.params
                else:
                    code = ("win.callOnFlip(%(name)s.setData, int(%(stopData)s))\n" %
                            self.params)

            buff.writeIndented(code)

        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # dedent
# buff.setIndentLevel(-dedentAtEnd, relative=True)#'if' statement of the
# time test and button check

    def writeRoutineEndCode(self, buff):
        # make sure that we do switch to stopData if the routine has been
        # aborted before our 'end'
        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        if self.params['address'].val == 'LabJack U3':
            if not self.params['syncScreen'].val:
                code = "    %(name)s.setData(int(%(stopData)s), address=%(register)s)\n" % self.params
            else:
                code = ("    win.callOnFlip(%(name)s.setData, int(%(stopData)s), address=%(register)s)\n" %
                        self.params)
        else:
            if not self.params['syncScreen'].val:
                code = "    %(name)s.setData(int(%(stopData)s))\n" % self.params
            else:
                code = ("    win.callOnFlip(%(name)s.setData, int(%(stopData)s))\n" % self.params)

        buff.writeIndented(code)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)
