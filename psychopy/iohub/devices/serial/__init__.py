# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/serial/__init__.py

Copyright (C) 2012-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from psychopy.iohub import print2err,printExceptionDetailsToStdErr,Computer
import serial
from .. import Device, DeviceEvent
from ...constants import DeviceConstants, EventConstants
import numpy as N
getTime = Computer.getTime

class Serial(Device):
    """
    A general purpose serial input interface device. Configuration options
    are used to define how the serial input data should be parsed, and what
    conditions create a serial input event to be generated.
    """
    DEVICE_TIMEBASE_TO_SEC = 1.0
    _newDataTypes = [('port', N.str, 32), ('baud', N.str, 32),]
    EVENT_CLASS_NAMES = ['SerialInputEvent',]
    DEVICE_TYPE_ID = DeviceConstants.SERIAL
    DEVICE_TYPE_STRING = "SERIAL"
    _mcu_slots = ['port', 'baud', '_serial', '_timeout', '_rx_buffer',
                  '_parser_config', '_parser_state', '_event_count']
    __slots__ = [e for e in _mcu_slots]
    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs['dconfig'])
        self._serial = None
        self.port = self.getConfiguration().get('port')
        if self.port.lower() == 'auto':
            pports = self.findPorts()
            if pports:
                self.port = pports[0]
                if len(pports) > 1:
                    print2err("Warning: Serial device port configuration set to 'auto'.\nMultiple serial ports found:\n", pports, "\n** Using port ", self.port)
        self.baud = self.getConfiguration().get('baud')

        self._parser_config = self.getConfiguration().get('event_parser')
        self._resetParserState()

        self._rx_buffer = ''
        self._event_count = 0

        self._timeout = None
        self._serial = None
        self.setConnectionState(True)

    @classmethod
    def findPorts(cls):
        """
        Finds serial ports that are available.
        """
        import os
        available = []
        if os.name == 'nt':  # Windows
            for i in range(1, 256):
                try:
                    sport = 'COM'+str(i)
                    s = serial.Serial(sport)
                    available.append(sport)
                    s.close()
                except serial.SerialException:
                    pass
        else:  # Mac / Linux
            from serial.tools import list_ports
            available = [port[0] for port in list_ports.comports()]

        if len(available) < 1:
            print2err('Error: unable to find any serial ports on the computer.')
            return []
        return available

    def _resetParserState(self):
        self._parser_state = dict(parsed_event='')
        if self._parser_config:
            fixed_length = self._parser_config.setdefault('fixed_length',None)
            if fixed_length:
                self._parser_state['bytes_needed'] = fixed_length
            else:
                self._parser_state['bytes_needed'] = 0

            prefix=self._parser_config.setdefault('prefix', None)
            if prefix == r'\n':
               self._parser_config['prefix'] = '\n'
            elif prefix == r'\t':
               self._parser_config['prefix'] = '\t'
            elif prefix == r'\r':
               self._parser_config['prefix'] = '\r'
            elif prefix == r'\r\n':
               self._parser_config['prefix'] = '\r\n'

            if prefix:
                self._parser_state['prefix_found'] = False
            else:
                self._parser_state['prefix_found'] = True

            delimiter = self._parser_config.setdefault('delimiter', None)
            if delimiter == r'\n':
               self._parser_config['delimiter'] = '\n'
            elif delimiter  == r'\t':
               self._parser_config['delimiter'] = '\t'
            elif delimiter == r'\r':
               self._parser_config['delimiter'] = '\r'
            elif delimiter == r'\r\n':
               self._parser_config['delimiter'] = '\r\n'
            if delimiter:
                self._parser_state['delimiter_found'] = False
            else:
                self._parser_state['delimiter_found'] = True

    def setConnectionState(self, enable):
        if enable is True:
            if self._serial is None:
                self._connectSerial()

        elif enable is False:
            if self._serial:
                self._serial.close()

        return self.isConnected()

    def isConnected(self):
        return self._serial != None

    def getDeviceTime(self):
        return getTime()

    def getSecTime(self):
        """
        Returns current device time in sec.msec format.
        Relies on a functioning getDeviceTime() method.
        """
        return self.getTime()

    def enableEventReporting(self, enabled=True):
        """
        Specifies if the device should be reporting events to the ioHub Process
        (enabled=True) or whether the device should stop reporting events to the
        ioHub Process (enabled=False).


        Args:
            enabled (bool):  True (default) == Start to report device events to the ioHub Process. False == Stop Reporting Events to the ioHub Process. Most Device types automatically start sending events to the ioHUb Process, however some devices like the EyeTracker and AnlogInput device's do not. The setting to control this behavour is 'auto_report_events'

        Returns:
            bool: The current reporting state.
        """
        if enabled and not self.isReportingEvents():
            if not self.isConnected():
                self.setConnectionState(True)
            self.flushInput()
        self._rx_buffer = ''
        self._event_count = 0
        return Device.enableEventReporting(self, enabled)

    def isReportingEvents(self):
        """
        Returns whether a Device is currently reporting events to the ioHub Process.

        Args: None

        Returns:
            (bool): Current reporting state.
        """
        return Device.isReportingEvents(self)

    def _connectSerial(self):
        self._serial = serial.Serial(self.port, self.baud, timeout=self._timeout)
        if self._serial is None:
            raise ValueError("Error: Serial Port Connection Failed: %d"%(self.port))
        self._serial.flushInput()
        inBytes = self._serial.inWaiting()
        if inBytes > 0:
          self._serial.read(inBytes)
        self._rx_buffer = ''

    def flushInput(self):
        self._serial.flushInput()

    def flushOutput(self):
        self._serial.flush()

    def write(self, bytestring):
        tx_count = self._serial.write(bytestring)
        self._serial.flush()
        return tx_count

    def read(self):
        rx = ''
        while self._serial.inWaiting() > 0:
            rx += self._serial.read(self._serial.inWaiting())
        return rx

    def closeSerial(self):
        if self._serial:
            self._serial.close()
            self._serial = None
            return True
        return False

    def close(self):
        try:
            self.flushInput()
        except:
            pass
        try:
            self.closeSerial()
        except:
            pass
        self._serial_port = None

    def _createSerialEvent(self, logged_time, read_time):
        #TODO Generate Serial Event
        self._event_count += 1
        confidence_interval = read_time - self._last_poll_time
        elist=[0, 0, 0, Computer._getNextEventID(),
               EventConstants.SERIAL_INPUT,
               read_time,
               logged_time,
               read_time,
               confidence_interval,
               0.0,
               0,
               self.port,
               self._parser_state['parsed_event']
            ]
        self._addNativeEventToBuffer(elist)
        self._resetParserState()

    def _poll(self):
        try:
            logged_time = getTime()
            if not self.isReportingEvents():
                self._last_poll_time = logged_time
                return False

            if self.isConnected():
                self._rx_buffer += self.read()
                read_time = getTime()
                prefix = self._parser_config['prefix']
                delimiter = self._parser_config['delimiter']

                if self._parser_state['prefix_found'] is False:
                    if prefix and self._rx_buffer and len(self._rx_buffer) >= len(prefix):
                        pindex = self._rx_buffer.find(prefix)
                        if pindex >= 0:
                            self._rx_buffer = self._rx_buffer[pindex+len(prefix):]
                            self._parser_state['prefix_found'] = True

                if self._parser_state['delimiter_found'] is False:
                    if delimiter and self._rx_buffer and len(self._rx_buffer) >= len(delimiter):
                        dindex = self._rx_buffer.find(delimiter)
                        if dindex >= 0:
                            self._parser_state['delimiter_found'] = True
                            sindex = dindex
                            eindex = dindex+len(delimiter)
                            self._parser_state['parsed_event'] += self._rx_buffer[:sindex]
                            if len(self._rx_buffer) > eindex:
                                self._rx_buffer = self._rx_buffer[eindex:]
                            else:
                                self._rx_buffer = ''
                            self._createSerialEvent(logged_time, read_time)
                            return True

                if self._parser_state['bytes_needed'] > 0 and self._rx_buffer:
                    rxlen = len(self._rx_buffer)
                    #takebytes = rxlen - self._parser_state['bytes_needed']
                    if rxlen > self._parser_state['bytes_needed']:
                        self._parser_state['parsed_event'] += self._rx_buffer[:self._parser_state['bytes_needed']]
                        self._parser_state['bytes_needed'] = 0
                        self._rx_buffer = self._rx_buffer[self._parser_state['bytes_needed']:]
                    else:
                        self._parser_state['parsed_event'] += self._rx_buffer
                        self._parser_state['bytes_needed'] -= rxlen
                        self._rx_buffer = ''

                    if self._parser_state['bytes_needed'] == 0:
                            self._createSerialEvent(logged_time, read_time)
                            return True
            else:
                read_time = logged_time
            self._last_poll_time = read_time
            return True
        except Exception, e:
            print2err("--------------------------------")
            print2err("ERROR in Serial._poll: ",e)
            printExceptionDetailsToStdErr()
            print2err("---------------------")

    def _close(self):
        self.setConnectionState(False)
        Device._close(self)

class SerialInputEvent(DeviceEvent):
    _newDataTypes = [
            ('port', N.str, 32),
            ('data', N.str, 256)
            ]
    EVENT_TYPE_ID = EventConstants.SERIAL_INPUT
    EVENT_TYPE_STRING = 'SERIAL_INPUT'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING
    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)
