#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from copy import copy
from pathlib import Path
from psychopy.tools import stringtools as st
from psychopy.experiment.components import BaseDeviceComponent, Param, _translate, getInitVals


# cache known ports so we only have to check once
_knownPorts = None


class SerialOutComponent(BaseDeviceComponent):
    """A class for sending signals from the parallel port"""

    categories = ['I/O', 'EEG']
    targets = ['PsychoPy']
    version = "2022.2.0"
    iconFile = Path(__file__).parent / 'serial.png'
    tooltip = _translate('Serial out: send signals from a serial port')
    beta = False
    

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
        self.exp.requireImport('serial')

        # functions to get available ports
        from psychopy.hardware.serialdevice import SerialDevice
        global _knownPorts
        if _knownPorts is None:
                _knownPorts = SerialDevice.getAvailableDevices()

        def getPorts():
            ports = []
            for profile in _knownPorts:
                ports.append(profile['port'])
            
            return ports
        
        def getPortLabels():
            ports = []
            for profile in _knownPorts:
                ports.append("%(port)s (%(deviceName)s)" % profile)
            
            return ports
        
        self.params['port'] = Param(
            "", valType="str", inputType="choice", categ="Device",
            allowedVals=getPorts,
            allowedLabels=getPortLabels,
            hint=_translate("Serial port to connect to"),
            label=_translate("Port")
        )
        self.params['baudrate'] = Param(
            baudrate, valType='int', inputType="single", categ="Device",
            hint=_translate("The baud rate, or speed, of the connection."),
            label=_translate("Baud rate")
        )
        self.params['bytesize'] = Param(
            bytesize, valType='int', inputType="single", categ="Device",
            hint=_translate("Size of bits to be sent."),
            label=_translate("Data bits")
        )
        self.params['stopbits'] = Param(
            stopbits, valType='int', inputType="single", categ="Device",
            hint=_translate("Size of bits to be sent on stop."),
            label=_translate("Stop bits")
        )
        self.params['parity'] = Param(
            parity, valType='str', inputType="choice", categ="Device",
            allowedVals=('N', 'E', 'O', 'M', 'S'),
            allowedLabels=("None", "Even", "Off", "Mark", "Space"),
            hint=_translate("Parity mode."),
            label=_translate("Parity")
        )

        self.params['timeout'] = Param(
            timeout, valType='int', inputType="single", allowedTypes=[], categ="Device",
            hint=_translate("Time at which to give up listening for a response (leave blank for no limit)"),
            label=_translate("Timeout"))
        
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
                label=_translate("Start data type")
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
    
    def writeDeviceCode(self, buff):
        inits = getInitVals(self.params)

        # initialise device
        code = (
            "# initialise serial device\n"
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy.hardware.serialdevice.SerialDevice',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    port=%(port)s,\n"
            "    baudrate=%(baudrate)s,\n"
            "    byteSize=%(bytesize)s,\n"
            "    stopBits=%(stopbits)s,\n"
            "    parity=%(parity)s,\n"
            "    pauseDuration=%(timeout)s / 3,\n"            
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")
        # point component name to device object
        code = (
            "\n"
            "# point %(name)s to device named %(deviceLabel)s and make sure it's open\n"
            "%(name)s = devicemanager.getDevice(%(deviceLabel)s)\n"
            "%(name)s.status = NOT_STARTED\n"
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
                params['startData'] = "bytes(chr(%(startDataNumeric)s), 'utf-8')" % params
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
                params['stopData'] = "bytes(bytearray([%(stopDataNumeric)s]))" % params
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
            # update status
            code = (
                "%(name)s.status = FINISHED\n"
            )
            buff.writeIndented(code % params)
            # if we want responses, get them
            if self.params['getResponse']:
                code = (
                    "%(loop)s.addData('%(name)s.stopResp', %(name)s.read())\n"
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
