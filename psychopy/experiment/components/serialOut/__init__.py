#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from copy import copy
from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate, getInitVals
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# only use _localized values for label values, nothing functional:
_localized.update({'address': _translate('Port address'),
                   'register': _translate('U3 Register'),
                   'startData': _translate("Start data"),
                   'stopData': _translate("Stop data"),
                   'syncScreenRefresh': _translate('Sync to screen')})


class SerialOutComponent(BaseComponent):
    """A class for sending signals from the parallel port"""

    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'serial.png'
    tooltip = _translate('Serial out: send signals from a serial port')
    beta = True

    def __init__(self, exp, parentName, name='serialPort',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 port="COM3", baudrate=9600, bytesize=8, stopbits=1, parity='None',
                 startdata=1, stopdata=0,
                 timeout="", getResponse=False,
                 syncScreenRefresh=False):
        super(SerialOutComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            syncScreenRefresh=syncScreenRefresh)

        self.type = 'SerialOut'
        self.url = "https://www.psychopy.org/builder/components/serialout.html"
        self.exp.requireImport('serial')

        self.params['port'] = Param(
            port, valType='str', inputType="single", categ='Basic',
            hint=_translate("Serial port to connect to"),
            label=_translate("Port")
        )
        self.params['baudrate'] = Param(
            baudrate, valType='int', inputType="int", categ='Hardware',
            hint=_translate("The baud rate, or speed, of the connection."),
            label=_translate("Baud rate")
        )
        self.params['bytesize'] = Param(
            bytesize, valType='int', inputType="int", categ='Hardware',
            hint=_translate("Size of bits to be sent."),
            label=_translate("Data bits")
        )
        self.params['stopbits'] = Param(
            stopbits, valType='int', inputType="int", categ='Hardware',
            hint=_translate("Size of bits to be sent on stop."),
            label=_translate("Stop bits")
        )
        self.params['parity'] = Param(
            parity, valType='str', inputType="choice", categ='Hardware',
            allowedVals=('N', 'E', 'O', 'M', 'S'),
            allowedLabels=("None", "Even", "Off", "Mark", "Space"),
            hint=_translate("Parity mode."),
            label=_translate("Parity")
        )

        self.params['timeout'] = Param(
            timeout, valType='int', inputType="single", allowedTypes=[], categ='Hardware',
            hint=_translate("Time at which to give up listening for a response (leave blank for no limit)"),
            label=_translate('Timeout'))

        self.params['startdata'] = Param(
            startdata, valType='str', inputType="single", allowedTypes=[], categ='Basic',
            hint=_translate("Data to be sent at start of pulse. Data will be converted to bytes, so to specify a"
                            "numeric value directly use $chr(...)."),
            label=_translate('Start data'))
        self.params['stopdata'] = Param(
            stopdata, valType='str', inputType="single", allowedTypes=[], categ='Basic',
            hint=_translate("String data to be sent at end of pulse. Data will be converted to bytes, so to specify a"
                            "numeric value directly use $chr(...)."),
            label=_translate('Stop data'))
        self.params['getResponse'] = Param(
            getResponse, valType='bool', inputType='bool', categ="Data",
            hint=_translate("After sending a signal, should PsychoPy read and record a response from the port?"),
            label=_translate("Get response?")
        )

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")

        code = (
            "# Create serial object for Component \"%(name)s\"\n"
            "%(name)s = serial.Serial(\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(+1, relative=True)
        for key in ('port', 'baudrate', 'bytesize', 'parity', 'stopbits', 'timeout'):
            code = (
                f"{key}=%({key})s,\n"
            )
            if self.params[key].val is not None:
                buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
            "%(name)s.status = NOT_STARTED\n"
        )
        buff.writeIndented(code % inits)
        # Open the port
        code = (
            "if not %(name)s.is_open:\n"
            "    %(name)s.open()\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        params = copy(self.params)
        # Get containing loop
        params['loop'] = self.currentLoop

        # On component start, send start bits
        self.writeStartTestCode(buff)
        if self.params['syncScreenRefresh']:
            code = (
                "win.callOnFlip(%(name)s.write, bytes(%(startdata)s, 'utf8'))\n"
            )
        else:
            code = (
                "%(name)s.write(bytes(%(startdata)s, 'utf8'))\n"
            )
        buff.writeIndented(code % params)
        # Update status
        code = (
            "%(name)s.status = STARTED\n"
        )
        buff.writeIndented(code % params)
        # If we want responses, get them
        if self.params['getResponse']:
            code = (
                "%(loop)s.addData('%(name)s.startResp', %(name)s.read())\n"
            )
            buff.writeIndented(code % params)
        # Dedent
        buff.setIndentLevel(-1, relative=True)

        # On component stop, send stop pulse
        self.writeStopTestCode(buff)
        if self.params['syncScreenRefresh']:
            code = (
                "win.callOnFlip(%(name)s.write, bytes(%(stopdata)s, 'utf8'))\n"
            )
        else:
            code = (
                "%(name)s.write(bytes(%(stopdata)s, 'utf8'))\n"
            )
        buff.writeIndented(code % params)
        # Update status
        code = (
            "%(name)s.status = FINISHED\n"
        )
        buff.writeIndented(code % params)
        # If we want responses, get them
        if self.params['getResponse']:
            code = (
                "%(loop)s.addData('%(name)s.stopResp', %(name)s.read())\n"
            )
            buff.writeIndented(code % params)
        # Dedent
        buff.setIndentLevel(-2, relative=True)

    def writeExperimentEndCode(self, buff):
        # Close the port
        code = (
            "# Close %(name)s\n"
            "if %(name)s.is_open:\n"
            "    %(name)s.close()\n"
        )
        buff.writeIndentedLines(code % self.params)
