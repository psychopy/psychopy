#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseDeviceComponent, Param, _translate
from psychopy.experiment.devices import DeviceBackend
import sys

class ParallelOutComponent(BaseDeviceComponent):
    """A class for sending signals from the parallel port"""

    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'parallel.png'
    iconSVG = Path(__file__).parent / 'ParallelOutComponent.svg'
    tooltip = _translate('Parallel out: send signals from the parallel port')
    legacyParams = [
        # old device setup params, no longer needed as this is handled by DeviceManager
        "address",
        "register",
    ]

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
        self.exp.requirePsychopyLibs([
            "hardware"
        ])

        # params
        self.order += [
            'startData', 'stopData',  # Data tab
        ]

        self.params['startData'] = Param(
            startData, valType='code', inputType="single", allowedTypes=[], categ='Basic',
            hint=_translate("Data to be sent at 'start'"),
            label=_translate("Start data"))

        self.params['stopData'] = Param(
            stopData, valType='code', inputType="single", allowedTypes=[], categ='Basic',
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

        code = (
            "%(name)s = hardware.parallel.Parallel(\n"
            "    device=%(deviceLabel)s\n"
            ")\n"
        )
        buff.writeIndented(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            # set start data
            code = (
                "# set %(name)s start data\n"
            )
            if not self.params['syncScreen'].val:
                code += (
                    "%(name)s.setData(\n"
                    "    int(%(startData)s)\n"
                    ")\n"
                )
            else:
                code += (
                    "win.callOnFlip(\n"
                    "    %(name)s.setData, \n"
                    "    int(%(startData)s)\n"
                    ")\n"
                )
            buff.writeIndentedLines(code % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        if indented:
            # set stop data
            code = (
                "# set %(name)s stop data\n"
            )
            if not self.params['syncScreen'].val:
                code += (
                    "%(name)s.setData(\n"
                    "    int(%(stopData)s)\n"
                    ")\n"
                )
            else:
                code += (
                    "win.callOnFlip(\n"
                    "    %(name)s.setData, \n"
                    "    int(%(stopData)s)\n"
                    ")\n"
                )
            buff.writeIndentedLines(code % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

    def writeRoutineEndCode(self, buff):
        # set stop data at end of Routine (in case Routine ended before Component)
        code = (
            "# set %(name)s stop data\n"
        )
        if not self.params['syncScreen'].val:
            code += (
                "%(name)s.setData(\n"
                "    int(%(stopData)s)\n"
                ")\n"
            )
        else:
            code += (
                "win.callOnFlip(\n"
                "    %(name)s.setData, \n"
                "    int(%(stopData)s)\n"
                ")\n"
            )
        buff.writeIndentedLines(code % self.params)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)


class ParallelDeviceBackend(DeviceBackend):
    backendLabel = "Parallel Port"
    deviceClass = "psychopy.hardware.parallel.ParallelDevice"
    icon = "light/parallel.png"

    def __init__(self, profile):
        # init parent class
        DeviceBackend.__init__(self, profile)

        # different default address options for Windows vs Linux...
        addressOptions = [
            "USB2TTL8",
            "custom"
        ]
        if sys.platform == "win32":
            addressOptions = [
                "0x0378", 
                "0x03BC"
            ] + addressOptions
        if sys.platform == "linux":
            addressOptions = [
                "/dev/parport0", 
                "/dev/parport1"
            ] + addressOptions

        self.params['address'] = Param(
            addressOptions[0],
            valType="str",
            inputType="choice",
            allowedVals=addressOptions,
            label=_translate("Port address"),
            hint=_translate(
                "Parallel port to be used (choose 'custom' to specify any address)"
            )
        )
        self.params['customAddress'] = Param(
            "",
            valType="str",
            inputType="single",
            label=_translate("Custom port address"),
            hint=_translate(
                "Specify any address for the port"
            )
        )
        self.depends.append({
            "dependsOn": "address",  # if...
            "condition": "== 'custom'",  # meets...
            "param": "customAddress",  # then...
            "true": "show",  # should...
            "false": "hide",  # otherwise...
        })
        

    def writeDeviceCode(self, buff):
        # handle special case (USB2TTL)
        if self.params['address'] == 'USB2TTL8':
            code = (
                "# initialize %(name)s\n"
                "from psychopy.hardware import labhackers\n"
                "deviceManager.devices[%(name)s] = labhackers.USB2TTL8()\n"
            )
            buff.writeIndentedLines(code % self.params)
            return

        # open init call
        code = (
            "# initialize %(name)s\n"
            "deviceManager.addDevice(\n"
            "    deviceName=%(name)s,\n"
            "    deviceClass='psychopy.hardware.parallel.ParallelDevice',\n"
        )
        
        # add address (handle custom)
        if self.params['address'] == "custom":
            code += (
            "    address=%(customAddress)s\n"
            )
        else:
            code += (
            "    address=%(address)s\n"
            )
        # close init call and write
        code += (
            ")\n"
        )
        buff.writeIndentedLines(code % self.params)


# register backend with Component
ParallelOutComponent.registerBackend(ParallelDeviceBackend)
