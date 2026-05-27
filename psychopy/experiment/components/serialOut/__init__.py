#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from copy import copy
from pathlib import Path
from psychopy.experiment.devices import DeviceBackend
from psychopy.tools import stringtools as st
from psychopy.experiment.components import BaseDeviceComponent, Param, _translate, getInitVals


class SerialOutComponent(BaseDeviceComponent):
    """A class for sending signals from the parallel port"""

    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    version = "2022.2.0"
    iconFile = Path(__file__).parent / 'serial.png'
    iconSVG = Path(__file__).parent / 'SerialOutComponent.svg'
    tooltip = _translate('Serial out: send signals from a serial port')
    beta = False
    legacyParams = [
        # superceded by "startDataChar", "startDataCode", et al.
        "startdata",
        "stopdata",
        # old device setup params, no longer needed as this is handled by DeviceManager
        "port",
        "baudrate",
        "bytesize",
        "stopbits",
        "parity",
        "timeout"
    ]
    

    def __init__(self, exp, parentName, name='serialPort',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 port="COM3", baudrate=9600, bytesize=8, stopbits=1, parity='N',
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
        
        for prefix, label, titleLabel, default in (
            ("start", _translate("start"), _translate("Start"), b"r"),
            ("stop", _translate("stop"), _translate("Stop"), b"x"),
        ):

            self.params[prefix + 'DataType'] = Param(
                "str", valType="str", inputType="choice", categ="Basic",
                allowedVals=["str", "num", "binary", "char", "code"],
                allowedLabels=[
                    _translate("String"), _translate("Numeric (0-255)"), 
                    _translate("Binary"), _translate("Character (Byte)"), _translate("Code")
                ],
                hint=_translate(
                    "Type of data to be sent: A number, a binary sequence, a character byte, or custom code ($)"
                ),
                label=_translate("{} data type").format(titleLabel)
            )

            self.params[prefix + 'DataStr'] = Param(
                default.decode("utf-8"), valType="str", inputType="single", categ="Basic",
                hint=_translate("Send a regular string (which will be converted to binary) on {}").format(label),
                label=_translate("{} data (string)").format(titleLabel)
            )
            self.depends.append({
                'dependsOn': prefix + "DataType",  # if...
                'condition': "== 'str'",  # meets...
                'param': prefix + "DataStr",  # then...
                'true': "show",  # should...
                'false': "hide",  # otherwise...
            })

            self.params[prefix + 'DataNumeric'] = Param(
                ord(default), valType="code", inputType="single", categ="Basic",
                hint=_translate("Send a number between 0-255 on {}").format(label),
                label=_translate("{} data (numeric)").format(titleLabel)
            )
            self.depends.append({
                'dependsOn': prefix + "DataType",  # if...
                'condition': "== 'num'",  # meets...
                'param': prefix + "DataNumeric",  # then...
                'true': "show",  # should...
                'false': "hide",  # otherwise...
            })

            self.params[prefix + 'DataBinary'] = Param(
                bin(ord(default))[2:], valType="code", inputType="single", categ="Basic",
                hint=_translate("Send a binary sequence (1s and 0s) on {}").format(label),
                label=_translate("{} data (binary)").format(titleLabel)
            )
            self.depends.append({
                'dependsOn': prefix + "DataType",  # if...
                'condition': "== 'binary'",  # meets...
                'param': prefix + "DataBinary",  # then...
                'true': "show",  # should...
                'false': "hide",  # otherwise...
            })

            self.params[prefix + 'DataChar'] = Param(
                "\\x" + hex(ord(default))[2:], valType="str", inputType="single", categ="Basic",
                hint=_translate("Send a character byte (e.g. \\x73) on {}").format(label),
                label=_translate("{} data (char)").format(titleLabel)
            )
            self.depends.append({
                'dependsOn': prefix + "DataType",  # if...
                'condition': "== 'char'",  # meets...
                'param': prefix + "DataChar",  # then...
                'true': "show",  # should...
                'false': "hide",  # otherwise...
            })

            self.params[prefix + 'DataCode'] = Param(
                repr(default), valType="code", inputType="single", categ="Basic",
                hint=_translate("Send custom code (e.g. from a variable) on {}").format(label),
                label=_translate("{} data (code)").format(titleLabel)
            )
            self.depends.append({
                'dependsOn': prefix + "DataType",  # if...
                'condition': "== 'code'",  # meets...
                'param': prefix + "DataCode",  # then...
                'true': "show",  # should...
                'false': "hide",  # otherwise...
            })
          
        self.params['getResponse'] = Param(
            getResponse, valType='bool', inputType='bool', categ="Data",
            hint=_translate("After sending a signal, should PsychoPy read and record a response from the port?"),
            label=_translate("Get response?")
        )

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")
        # point component name to device object
        code = (
            "\n"
            "# point %(name)s to device named %(deviceLabel)s and make sure it's open\n"
            "%(name)s = SerialOut(\n"
            "    device=%(deviceLabel)s\n"
            ")\n"
            "if not %(name)s.com.is_open:\n"
            "    %(name)s.com.open()\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        params = copy(self.params)
        # Get containing loop
        params['loop'] = self.currentLoop
        # On component start, send start bits
        indented = self.writeStartTestCode(buff)
        if indented:
            # get data string to write
            if params['startDataType'] == "str":
                params['startData'] = params['startDataStr']
            elif params['startDataType'] == "num":
                params['startData'] = params['startDataNumeric']
            elif params['startDataType'] == "binary":
                params['startData'] = "0b%(startDataBinary)s" % params
            elif params['startDataType'] == "char":
                params['startData'] = "b%(startDataChar)s" % params
            elif params['startDataType'] == "code":
                params['startData'] = params['startDataCode']
            else:
                raise TypeError(f"Unknown data type {params['startDataType']}")
            # write code to send it (immediately or on refresh)
            if self.params['syncScreenRefresh']:
                code = (
                    "win.callOnFlip(%(name)s.sendMessage, %(startData)s)\n"
                )
            else:
                code = (
                    "%(name)s.sendMessage(%(startData)s)\n"
                )
            buff.writeIndented(code % params)
            # store code that was sent
            code = (
                "%(loop)s.addData('%(name)s.startData', %(startData)s)\n"
            )
            buff.writeIndented(code % params)
            # update status
            code = (
                "%(name)s.status = STARTED\n"
            )
            buff.writeIndented(code % params)
            # if we want responses, get them
            if self.params['getResponse']:
                code = (
                    "%(loop)s.addData('%(name)s.startResp', %(name)s.getResponse())\n"
                )
                buff.writeIndented(code % params)
        # Dedent
        buff.setIndentLevel(-indented, relative=True)

        # On component stop, send stop pulse
        indented = self.writeStopTestCode(buff)
        if indented:
            # get data string to write
            if params['stopDataType'] == "str":
                params['stopData'] = params['stopDataStr']
            elif params['stopDataType'] == "num":
                params['stopData'] = params['stopDataNumeric']
            elif params['stopDataType'] == "binary":
                params['stopData'] = "0b%(stopDataBinary)s" % params
            elif params['stopDataType'] == "char":
                params['stopData'] = "b'%(stopDataChar)s'" % params
            elif params['stopDataType'] == "code":
                params['stopData'] = params['stopDataCode']
            else:
                raise TypeError(f"Unknown data type {params['stopDataType']}")
            # write code to send it (immediately or on refresh)
            if self.params['syncScreenRefresh']:
                code = (
                    "win.callOnFlip(%(name)s.sendMessage, %(stopData)s)\n"
                )
            else:
                code = (
                    "%(name)s.sendMessage(%(stopData)s)\n"
                )
            buff.writeIndented(code % params)
            # store code that was sent
            code = (
                "%(loop)s.addData('%(name)s.stopData', %(stopData)s)\n"
            )
            buff.writeIndented(code % params)
            # update status
            code = (
                "%(name)s.status = FINISHED\n"
            )
            buff.writeIndented(code % params)
            # if we want responses, get them
            if self.params['getResponse']:
                code = (
                    "%(loop)s.addData('%(name)s.stopResp', %(name)s.getResponse())\n"
                )
                buff.writeIndented(code % params)
        # Dedent
        buff.setIndentLevel(-indented, relative=True)

    def writeExperimentEndCode(self, buff):
        # Close the port
        code = (
            "# close %(name)s\n"
            "if %(name)s.com.is_open:\n"
            "    %(name)s.com.close()\n"
        )
        buff.writeIndentedLines(code % self.params)


class SerialDeviceBackend(DeviceBackend):
    backendLabel = "Serial Device"
    deviceClass = "psychopy.hardware.serialdevice.SerialDevice"
    icon = "light/serial.png"

    def __init__(self, profile):
        # init parent class
        DeviceBackend.__init__(self, profile)

        # define order
        self.order += [
            "timeout",
            "eol"
        ]

        self.params['timeout'] = Param(
            "", valType='code', inputType="single",
            hint=_translate("Time at which to give up listening for a response (leave blank for no limit)"),
            label=_translate("Timeout")
        )

        self.params['eol'] = Param(
            "$'\\n'", valType="str", inputType="single", categ="Basic",
            label=_translate("EOL (end-of-line) character"),
            hint=_translate("Character automatically added to end of each message - leave blank for no EOL")
        )

        # -- Override params ---

        self.params['overrideBaudrate'] = Param(
            "", valType='code', inputType="single",
            categ="Overrides",
            hint=_translate("Override the device's reported baudrate"),
            label=_translate("Baudrate override")
        )
        self.params['overrideByteSize'] = Param(
            "", valType='code', inputType="single",
            categ="Overrides",
            hint=_translate("Override the device's reported byte size"),
            label=_translate("Byte size override")
        )
        self.params['overrideStopBits'] = Param(
            "", valType='code', inputType="single",
            categ="Overrides",
            hint=_translate("Override the device's reported stop bits"),
            label=_translate("Stop bits override")
        )
        self.params['overrideParity'] = Param(
            None, valType='str', inputType="choice",
            allowedVals=[
                None, "N", "E", "O", "M"
            ],
            allowedLabels=[
                "", _translate("N (none)"), _translate("E (even)"), _translate("O (odd)"), _translate("M (mask)")
            ],
            categ="Overrides",
            hint=_translate("Override the device's reported parity settings"),
            label=_translate("Parity override")
        )
    
    def writeDeviceCode(self, buff):
        """
        Code to setup a device with this backend.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        inits = getInitVals(self.params)
        # replace any overridden items from profile
        profile = self.profile.copy()
        for key, override in [
            ("baudrate", "overrideBaudrate"),
            ("byteSize", "overrideByteSize"),
            ("stopBits", "overrideStopBits"),
            ("parity", "overrideParity")
        ]:
            if self.params[override]:
                profile[key] = self.params[override].val
        # write init call with device label
        code = (
            "# initialize %(name)s\n"
            "deviceManager.addDevice(\n"
            "    deviceName=%(name)s,\n"
        )
        buff.writeIndentedLines(code % inits)
        # add options from profile
        code = ""
        for key, value in profile.items():
            # skip attributes already covered by a param
            if key in self.params or key in ("deviceName", ):
                continue
            code += f"    {key}={repr(value)},\n"
        buff.writeIndentedLines(code)
        # add pause and close
        code = (
            "    eol=%(eol)s,\n"
            "    pauseDuration=(%(timeout)s or 0.1) / 3,\n"  
            ")\n"
        )
        buff.writeIndentedLines(code % inits)


# register backend with Component
SerialOutComponent.registerBackend(SerialDeviceBackend)
