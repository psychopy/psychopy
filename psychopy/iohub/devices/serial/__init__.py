# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import serial
import sys
import numpy as N
import struct
from ... import EXP_SCRIPT_DIRECTORY
from .. import Device, DeviceEvent, Computer
from ...errors import print2err, printExceptionDetailsToStdErr
from ...constants import DeviceConstants, EventConstants
getTime = Computer.getTime


class Serial(Device):
    """A general purpose serial input interface device.

    Configuration options are used to define how the serial input data
    should be parsed, and what conditions create a serial input event to
    be generated.

    """
    _bytesizes = {
        5: serial.FIVEBITS,
        6: serial.SIXBITS,
        7: serial.SEVENBITS,
        8: serial.EIGHTBITS,
    }

    _parities = {
        'NONE': serial.PARITY_NONE,
        'EVEN': serial.PARITY_EVEN,
        'ODD': serial.PARITY_ODD,
        'MARK': serial.PARITY_MARK,
        'SPACE': serial.PARITY_SPACE
    }

    _stopbits = {
        'ONE': serial.STOPBITS_ONE,
        'ONE_AND_HALF': serial.STOPBITS_ONE_POINT_FIVE,
        'TWO': serial.STOPBITS_TWO
    }

    DEVICE_TIMEBASE_TO_SEC = 1.0
    _newDataTypes = [('port', '|S32'), ('baud', '|S32'), ]
    EVENT_CLASS_NAMES = ['SerialInputEvent', 'SerialByteChangeEvent']
    DEVICE_TYPE_ID = DeviceConstants.SERIAL
    DEVICE_TYPE_STRING = 'SERIAL'
    _serial_slots = [
        'port', 'baud', 'bytesize', 'parity', 'stopbits', '_serial',
        '_timeout', '_rx_buffer', '_parser_config', '_parser_state',
        '_event_count', '_byte_diff_mode', '_custom_parser',
        '_custom_parser_kwargs'
    ]
    __slots__ = [e for e in _serial_slots]

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs['dconfig'])
        self._serial = None
        self.port = self.getConfiguration().get('port')
        if self.port.lower() == 'auto':
            pports = self.findPorts()
            if pports:
                self.port = pports[0]
                if len(pports) > 1:
                    print2err(
                        'Warning: Serial device port configuration set '
                        "to 'auto'.\nMultiple serial ports found:\n",
                        pports, '\n** Using port ', self.port
                    )
        self.baud = self.getConfiguration().get('baud')
        self.bytesize = self._bytesizes[
            self.getConfiguration().get('bytesize')]
        self.parity = self._parities[self.getConfiguration().get('parity')]
        self.stopbits = self._stopbits[self.getConfiguration().get('stopbits')]

        self._parser_config = self.getConfiguration().get('event_parser')
        self._byte_diff_mode = None
        self._custom_parser = None
        self._custom_parser_kwargs = {}
        custom_parser_func_str = self._parser_config.get('parser_function')
        if custom_parser_func_str:
            # print2err("CUSTOM SERIAL PARSER FUNC STR: ", custom_parser_func_str)
            # Function referenced by string must have the following signature:
            #
            # evt_list = someCustomParserName(read_time, rx_data, parser_state, **kwargs)
            #
            # where:
            #     read_time: The time when the serial device read() returned
            #             with the new rx_data.
            #     rx_data: The new serial data received. Any buffering of data
            #             across function calls must be done by the function
            #             logic itself. parser_state could be used to hold
            #             such a buffer if needed.
            #     parser_state: A dict which can be used by the function to
            #             store any values that need to be accessed
            #             across multiple calls to the function. The dict
            #             is initially empty.
            #     kwargs: The parser_kwargs preference dict read from
            #             the event_parser preferences; or an empty dict if
            #             parser_kwargs was not found.
            #
            # The function must return a list like object, used to provide ioHub
            # with any new serial events that have been found.
            # Each element of the list must be a dict like object, representing
            # a single serial device event found by the parsing function.
            # A dict can contain the following key, value pairs:
            #    data: The string containing the parsed event data. (REQUIRED)
            #    time: The timestamp for the event (Optional). If not provided,
            #          the return time of the latest serial.read() is used.
            # Each event returned by the function generates a SerialInputEvent
            # with the data field = the dict data value.
            import importlib
            import sys
            try:
                #print2err("EXP_SCRIPT_DIRECTORY: ",EXP_SCRIPT_DIRECTORY)
                if EXP_SCRIPT_DIRECTORY not in sys.path:
                    sys.path.append(EXP_SCRIPT_DIRECTORY)
                mod_name, func_name = custom_parser_func_str.rsplit('.', 1)
                mod = importlib.import_module(mod_name)
                self._custom_parser = getattr(mod, func_name)
            except Exception:
                print2err(
                    'ioHub Serial Device Error: could not load '
                    'custom_parser function: ', custom_parser_func_str)
                printExceptionDetailsToStdErr()

            if self._custom_parser:
                self._custom_parser_kwargs = self._parser_config.get(
                    'parser_kwargs', {})
        else:
            self._byte_diff_mode = self._parser_config.get('byte_diff')

        if self._byte_diff_mode:
            self._rx_buffer = None
        else:
            self._resetParserState()
            self._rx_buffer = ''

        self._event_count = 0
        self._timeout = None
        self._serial = None
        self.setConnectionState(True)

    @classmethod
    def findPorts(cls):
        """Finds serial ports that are available."""
        import os
        available = []
        if os.name == 'nt':  # Windows
            for i in range(1, 256):
                try:
                    sport = 'COM' + str(i)
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
        parser_config = self._parser_config
        if parser_config:
            if self._custom_parser:
                self._parser_state = dict()
                return

            self._parser_state = dict(parsed_event='')
            parser_state = self._parser_state

            fixed_length = parser_config.setdefault('fixed_length', None)
            if fixed_length:
                parser_state['bytes_needed'] = fixed_length
            else:
                parser_state['bytes_needed'] = 0

            prefix = parser_config.setdefault('prefix', None)
            if prefix == r'\n':
                parser_config['prefix'] = '\n'
            elif prefix == r'\t':
                parser_config['prefix'] = '\t'
            elif prefix == r'\r':
                parser_config['prefix'] = '\r'
            elif prefix == r'\r\n':
                parser_config['prefix'] = '\r\n'

            if prefix:
                parser_state['prefix_found'] = False
            else:
                parser_state['prefix_found'] = True

            delimiter = parser_config.setdefault('delimiter', None)
            if delimiter == r'\n':
                parser_config['delimiter'] = '\n'
            elif delimiter == r'\t':
                parser_config['delimiter'] = '\t'
            elif delimiter == r'\r':
                parser_config['delimiter'] = '\r'
            elif delimiter == r'\r\n':
                parser_config['delimiter'] = '\r\n'
            if delimiter:
                parser_state['delimiter_found'] = False
            else:
                parser_state['delimiter_found'] = True

    def setConnectionState(self, enable):
        if enable is True:
            if self._serial is None:
                self._connectSerial()

        elif enable is False:
            if self._serial:
                self._serial.close()

        return self.isConnected()

    def isConnected(self):
        return self._serial is not None

    def getDeviceTime(self):
        return getTime()

    def getSecTime(self):
        """Returns current device time in sec.msec format.

        Relies on a functioning getDeviceTime() method.

        """
        return self.getTime()

    def enableEventReporting(self, enabled=True):
        """
        Specifies if the device should be reporting events to the ioHub Process
        (enabled=True) or whether the device should stop reporting events to the
        ioHub Process (enabled=False).


        Args:
            enabled (bool):  True (default) == Start to report device events to the ioHub Process. False == Stop Reporting Events to the ioHub Process. Most Device types automatically start sending events to the ioHUb Process, however some devices like the EyeTracker and AnlogInput device's do not. The setting to control this behavior is 'auto_report_events'

        Returns:
            bool: The current reporting state.
        """
        if enabled and not self.isReportingEvents():
            if not self.isConnected():
                self.setConnectionState(True)
            self.flushInput()
        if self._byte_diff_mode:
            self._rx_buffer = None
        else:
            self._rx_buffer = ''
        self._event_count = 0
        return Device.enableEventReporting(self, enabled)

    def isReportingEvents(self):
        """Returns whether a Device is currently reporting events to the ioHub
        Process.

        Args: None

        Returns:
            (bool): Current reporting state.

        """
        return Device.isReportingEvents(self)

    def _connectSerial(self):
        self._serial = serial.Serial(
            self.port, self.baud, timeout=self._timeout)
        if self._serial is None:
            raise ValueError(
                'Error: Serial Port Connection Failed: %d' %
                (self.port))
        self._serial.flushInput()
        inBytes = self._serial.inWaiting()
        if inBytes > 0:
            self._serial.read(inBytes)  # empty buffer and discard
        if self._byte_diff_mode:
            self._rx_buffer = None
        else:
            self._rx_buffer = ''

    def flushInput(self):
        self._serial.flushInput()

    def flushOutput(self):
        self._serial.flush()

    def write(self, bytestring):
        if type(bytestring) != bytes:
            bytestring = bytestring.encode('utf-8')
        tx_count = self._serial.write(bytestring)
        self._serial.flush()
        return tx_count

    def read(self):
        returned = self._serial.read(self._serial.inWaiting())
        returned = returned.decode('utf-8')
        return returned
		
    def closeSerial(self):
        if self._serial:
            self._serial.close()
            self._serial = None
            return True
        return False

    def close(self):
        try:
            self.flushInput()
        except Exception:
            pass
        try:
            self.closeSerial()
        except Exception:
            pass
        self._serial_port = None

    def _createSerialEvent(self, logged_time, read_time, event_data):
        self._event_count += 1
        confidence_interval = read_time - self._last_poll_time
        elist = [0, 0, 0, Device._getNextEventID(),
                 EventConstants.SERIAL_INPUT,
                 read_time,
                 logged_time,
                 read_time,
                 confidence_interval,
                 0.0,
                 0,
                 self.port,
                 event_data
                 ]
        self._addNativeEventToBuffer(elist)
        self._resetParserState()

    def _createMultiByteSerialEvent(self, logged_time, read_time):
        self._event_count += 1
        confidence_interval = read_time - self._last_poll_time
        elist = [0, 0, 0, Device._getNextEventID(),
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

    def _createByteChangeSerialEvent(
            self,
            logged_time,
            read_time,
            prev_byte,
            new_byte):
        self._event_count += 1
        confidence_interval = read_time - self._last_poll_time
        elist = [0, 0, 0, Device._getNextEventID(),
                 EventConstants.SERIAL_BYTE_CHANGE,
                 read_time,
                 logged_time,
                 read_time,
                 confidence_interval,
                 0.0,
                 0,
                 self.port,
                 ord(prev_byte),
                 ord(new_byte)
                 ]
        self._addNativeEventToBuffer(elist)

    def _poll(self):
        try:
            logged_time = getTime()
            if not self.isReportingEvents():
                self._last_poll_time = logged_time
                return False

            if self.isConnected():
                if self._custom_parser:
                    parser_state = self._parser_state
                    newrx = self.read()
                    read_time = getTime()
                    if newrx:
                        try:
                            serial_events = self._custom_parser(
                                read_time, newrx, parser_state, **self._custom_parser_kwargs)

                            for evt in serial_events:
                                if isinstance(evt, dict):
                                    evt_time = evt.get('time', read_time)
                                    evt_data = evt.get(
                                        'data', 'NO DATA FIELD IN EVENT DICT.')
                                    self._createSerialEvent(
                                        logged_time, evt_time, evt_data)
                                else:
                                    print2err(
                                        "ioHub Serial Device Error: Events returned from custom parser must be dict's. Skipping: ",
                                        str(evt))

                        except Exception:
                            print2err(
                                'ioHub Serial Device Error: Exception during parsing function call.')
                            import traceback
                            import sys
                            traceback.print_exc(file=sys.stderr)
                            print2err('---')

                elif self._byte_diff_mode:
                    rx = self.read()
                    read_time = getTime()
                    for c in rx:
                        if self._rx_buffer is not None and c != self._rx_buffer:
                            self._createByteChangeSerialEvent(logged_time,
                                                              read_time,
                                                              self._rx_buffer,
                                                              c)
                        self._rx_buffer = c
                else:
                    parser_state = self._parser_state
                    rx_buffer = self._rx_buffer + self.read()
                    read_time = getTime()
                    prefix = self._parser_config['prefix']
                    delimiter = self._parser_config['delimiter']

                    if parser_state['prefix_found'] is False:
                        if prefix and rx_buffer and len(
                                rx_buffer) >= len(prefix):
                            pindex = rx_buffer.find(prefix)
                            if pindex >= 0:
                                rx_buffer = rx_buffer[pindex + len(prefix):]
                                parser_state['prefix_found'] = True

                    if parser_state['delimiter_found'] is False:
                        if delimiter and self._rx_buffer and len(
                                rx_buffer) >= len(delimiter):
                            dindex = rx_buffer.find(delimiter)
                            if dindex >= 0:
                                parser_state['delimiter_found'] = True
                                sindex = dindex
                                eindex = dindex + len(delimiter)
                                parser_state[
                                    'parsed_event'] += rx_buffer[:sindex]
                                if len(rx_buffer) > eindex:
                                    rx_buffer = rx_buffer[eindex:]
                                else:
                                    rx_buffer = ''
                                self._rx_buffer = rx_buffer
                                self._createMultiByteSerialEvent(
                                    logged_time, read_time)
                                return True

                    if parser_state['bytes_needed'] > 0 and rx_buffer:
                        rxlen = len(rx_buffer)
                        #takebytes = rxlen - parser_state['bytes_needed']
                        if rxlen > parser_state['bytes_needed']:
                            parser_state[
                                'parsed_event'] += rx_buffer[:parser_state['bytes_needed']]
                            parser_state['bytes_needed'] = 0
                            rx_buffer = rx_buffer[
                                parser_state['bytes_needed']:]
                        else:
                            parser_state['parsed_event'] += rx_buffer
                            parser_state['bytes_needed'] -= rxlen
                            rx_buffer = ''

                        if parser_state['bytes_needed'] == 0:
                            self._rx_buffer = rx_buffer
                            self._createMultiByteSerialEvent(
                                logged_time, read_time)
                            return True

                    self._rx_buffer = rx_buffer
            else:
                read_time = logged_time
            self._last_poll_time = read_time
            return True
        except Exception as e:
            print2err('--------------------------------')
            print2err('ERROR in Serial._poll: ', e)
            printExceptionDetailsToStdErr()
            print2err('---------------------')

    def _close(self):
        self.setConnectionState(False)
        Device._close(self)


class Pstbox(Serial):
    """Provides convenient access to the PST Serial Response Box."""
    EVENT_CLASS_NAMES = ['PstboxButtonEvent', ]
    DEVICE_TYPE_ID = DeviceConstants.PSTBOX
    DEVICE_TYPE_STRING = 'PSTBOX'
    # Only add new attributes for the subclass, the device metaclass
    # pulls them together.
    _serial_slots = [
        '_nlamps', '_lamp_state',
        '_streaming_state', '_button_query_state', '_state',
        '_button_bytes', '_nbuttons'
    ]
    __slots__ = [e for e in _serial_slots]

    def __init__(self, *args, **kwargs):
        Serial.__init__(self, *args, **kwargs)

        self._nbuttons = 7
        # Buttons 0--4, from left to right:
        # [1, 2, 4, 8, 16]
        self._button_bytes = 2**N.arange(self._nbuttons, dtype='uint8')

        self._nlamps = 5
        self._lamp_state = N.repeat(False, self._nlamps)
        self._streaming_state = True
        self._button_query_state = True

        update_lamp_state = True
        self._state = N.r_[
            self._lamp_state, self._button_query_state, update_lamp_state,
            self._streaming_state
        ]

        self._update_state()

    def _update_state(self):
        update_lamp_state = True

        # `state` is an array of bools.
        state = N.r_[
            self._lamp_state, self._button_query_state, update_lamp_state,
            self._streaming_state
        ]

        # Convert the new state into a bitmask, collapse it into a
        # single byte and send it to the response box.
        state_bits = (2**N.arange(8))[state]
        self.write(struct.pack("B",(N.sum(state_bits))))

        # Set the `update lamp` bit to LOW again.
        state[6] = False
        self._state = state

    def getState(self):
        """Return the current state of the response box.

        Returns
        -------
        array
            An array of 8 boolean values will be returned, corresponding to
            the following properties:
            - state of lamp 0 (on/off)
            - state of lamp 1 (on/off)
            - state of lamp 2 (on/off)
            - state of lamp 3 (on/off)
            - state of lamp 4 (on/off)
            - button query state (on/off)
            - update lamp state (yes/no)
            - streaming state (on/off)

        See Also
        --------
        setState

        """
        return self._state

    def getLampState(self):
        """Return the current state of the lamps.

        Returns
        -------
        array
            An array of 5 boolean values will be returned, corresponding to
            the following properties:
            - state of lamp 0 (on/off)
            - state of lamp 1 (on/off)
            - state of lamp 2 (on/off)
            - state of lamp 3 (on/off)
            - state of lamp 4 (on/off)

        See Also
        --------
        setLampState

        """
        return self._lamp_state

    def setLampState(self, state):
        """Change the state of the lamps (on/off).

        Parameters
        ----------
        state : array_like
            The requested lamp states, from left to right. `0` or `False`
            means off, and `1` or `True` means on. This method expects
            an array of 5 boolean values, each corresponding to the
            following properties:
            - state of lamp 0 (on/off)
            - state of lamp 1 (on/off)
            - state of lamp 2 (on/off)
            - state of lamp 3 (on/off)
            - state of lamp 4 (on/off)

        See Also
        --------
        getLampState

        """
        if len(state) != self._nlamps:
            raise ValueError('Please specify a number of states that is '
                             'equal to the number of lamps on the '
                             'response box.')

        state = N.array(state).astype('bool')
        self._lamp_state = state
        self._update_state()

    def getStreamingState(self):
        """Get the current streaming state.

        Returns
        -------
        bool
            `True` if the box is streaming data, and `False` otherwise.

        See Also
        --------
        setStreamingState

        """
        return self._streaming_state

    def setStreamingState(self, state):
        """Switch on or off streaming mode.

        If streaming mode is disabled, the box will not send anything
        to the computer.

        Parameters
        ----------
        state : bool
            ``True`` will enable streaming, ``False`` will disable it.

        See Also
        --------
        getStreamingState

        """
        self._streaming_state = bool(state)
        self._update_state()

    def getButtonQueryState(self):
        """Get the current button query state.

        If the box is not querying buttons, no button presses will
        be reported.

        Returns
        -------
        bool
            `True` if the box is streaming data, and `False` otherwise.

        See Also
        --------
        getButtonQueryState

        """
        return self._button_query_state

    def setButtonQueryState(self, state):
        """Switch on or off button querying.

        Parameters
        ----------
        state : bool
            ``True`` will enable querying, ``False`` will disable it.

        See Also
        --------
        getButtonQueryState

        """
        self._button_query_state = bool(state)
        self._update_state()

    def _createByteChangeSerialEvent(self, logged_time, read_time,
                                     prev_byte, new_byte):
        self._event_count += 1
        confidence_interval = read_time - self._last_poll_time

        prev_byte = ord(prev_byte)
        new_byte = ord(new_byte)

        try:
            if new_byte != 0:  # Button was pressed
                button = N.where(self._button_bytes == new_byte)[0][0]
                button_event = 'press'
            else:  # Button was released
                button = N.where(self._button_bytes == prev_byte)[0][0]
                button_event = 'release'
        except Exception:
            # Handles when data rx does not match either N.where within the try
            return
        events = [
            0, 0, 0, Device._getNextEventID(),
            EventConstants.PSTBOX_BUTTON,
            read_time,
            logged_time,
            read_time,
            confidence_interval,
            0.0,
            0,
            self.port,
            button,
            button_event
        ]
        self._addNativeEventToBuffer(events)


class SerialInputEvent(DeviceEvent):
    _newDataTypes = [
        ('port', '|S32'),
        ('data', '|S256')
    ]
    PARENT_DEVICE = Serial
    EVENT_TYPE_ID = EventConstants.SERIAL_INPUT
    EVENT_TYPE_STRING = 'SERIAL_INPUT'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING
    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)


class SerialByteChangeEvent(DeviceEvent):
    _newDataTypes = [
        ('port', '|S32'),
        ('prev_byte', N.uint8),
        ('current_byte', N.uint8)
    ]
    PARENT_DEVICE = Serial
    EVENT_TYPE_ID = EventConstants.SERIAL_BYTE_CHANGE
    EVENT_TYPE_STRING = 'SERIAL_BYTE_CHANGE'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING
    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)


class PstboxButtonEvent(DeviceEvent):
    # Add new fields for PstboxButtonEvent
    _newDataTypes = [
        ('port', '|S32'),  # could be needed to identify events
                              # from >1 connected button box; if that is
                              # ever supported.
        ('button', N.uint8),
        ('button_event', '|S7')
    ]

    PARENT_DEVICE = Pstbox
    EVENT_TYPE_ID = EventConstants.PSTBOX_BUTTON
    EVENT_TYPE_STRING = 'PSTBOX_BUTTON'
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING

    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)
