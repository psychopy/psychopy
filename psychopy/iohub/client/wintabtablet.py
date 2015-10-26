# -*- coding: utf-8 -*-
# ioHub Python Module
# .. file: psychopy/iohub/client/tabletpen.py
#
# fileauthor: Sol Simpson <sol@isolver-software.com>
#
# Copyright (C) 2012-2015 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License
# (GPL version 3 or any later version).

from collections import deque
import time, math
from win32api import LOWORD, HIWORD
from psychopy.iohub.client import ioHubDeviceView, ioEvent, DeviceRPC
from psychopy.iohub.devices import DeviceEvent
from psychopy.iohub.devices.wintab import WintabTabletSampleEvent, WintabTabletEnterRegionEvent, WintabTabletLeaveRegionEvent
from psychopy.iohub.constants import EventConstants
from psychopy.core import getTime
from psychopy.visual.window import Window

FRAC = LOWORD
INT = HIWORD

def FIX_DOUBLE(x):
    return INT(x) + FRAC(x)/65536.0

"""
TabletPen Device and Events Types

"""


class PenSampleEvent(ioEvent):
    """
    Represents a tablet pen position / pressure event.
    """
    _attrib_index = dict()
    _attrib_index['x'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('x')
    _attrib_index['y'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('y')
    _attrib_index['z'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('z')
    _attrib_index['pressure'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'pressure_normal')
    _attrib_index['altitude'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'orient_altitude')
    _attrib_index['azimuth'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'orient_azimuth')
    def __init__(self, ioe_array, device):
        super(PenSampleEvent, self).__init__(ioe_array, device)
        self._x = ioe_array[PenSampleEvent._attrib_index['x']]
        self._y = ioe_array[PenSampleEvent._attrib_index['y']]
        self._z = ioe_array[PenSampleEvent._attrib_index['z']]
        self._pressure = ioe_array[PenSampleEvent._attrib_index['pressure']]
        self._altitude = ioe_array[PenSampleEvent._attrib_index['altitude']]
        self._azimuth = ioe_array[PenSampleEvent._attrib_index['azimuth']]


    @property
    def x(self):
        return self._x


    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    @property
    def pressure(self):
        return self._pressure

    @property
    def altitude(self):
        return self._altitude

    @property
    def azimuth(self):
        return self._azimuth

    @property
    def tilt(self):
        '''
        Get the dx,dy screen position in norm units that should be used
        when drawing the pen titl line graphic end point.

        Note: wintab.h defines .orAltitude as a UINT but documents .orAltitude as
        positive for upward angles and negative for downward angles.
        WACOM uses negative altitude values to show that the pen is inverted;
        therefore we cast .orAltitude as an (int) and then use the absolute value.
        '''
        # TODO: move constants to device or event class, do not recompute
        # for each sample.
        tablet = self.device
        azimuth_res = tablet.axis['orient_azimuth_axis']['axResolution']
        tpvar = FIX_DOUBLE(azimuth_res)
        # convert from resolution to radians
        aziFactor = tpvar/(2*math.pi)

        # convert altitude resolution to double
        tpvar = FIX_DOUBLE(tablet.axis['orient_altitude_axis']['axResolution'])
        # scale to arbitrary value to get decent line length
        altFactor = tpvar #/1000.0
        # adjust for maximum value at vertical */
        altAdjust = tablet.axis['orient_altitude_axis']['axMax']/altFactor

        ZAngle  = self.altitude
        ZAngle2 = altAdjust - float(abs(ZAngle)/altFactor)

        # below line would normalize the altitude to approx. between 0 and 1.0
        #
        #ZAngle2 = (1.0 -(tablet_event.altitude/tablet_event.device._axis['orient_altitude_axis']['axMax']))

        #/* adjust azimuth */
        Thata  = self.azimuth
        Thata2 = float(Thata/aziFactor)

        return ZAngle2, Thata2

    def __str__(self):
        return "{}, x,y,z: {}, {}, {} pressure: {}".format(
            ioEvent.__str__(self), self.x, self.y, self.z, self.pressure)


class PenEnterRegionEvent(ioEvent):
    """
    Occurs when Stylus enters the tablet region.
    """
    def __init__(self, ioe_array, device):
        super(PenEnterRegionEvent, self).__init__(ioe_array, device)

class PenLeaveRegionEvent(ioEvent):
    """
    Occurs when Stylus leaves the tablet region.
    """
    def __init__(self, ioe_array, device):
        super(PenLeaveRegionEvent, self).__init__(ioe_array, device)

class WintabTablet(ioHubDeviceView):
    """
    The WintabTablet device provides access to PenSampleEvent events.
    """
    SAMPLE = EventConstants.WINTAB_TABLET_SAMPLE
    ENTER = EventConstants.WINTAB_TABLET_ENTER_REGION
    LEAVE = EventConstants.WINTAB_TABLET_LEAVE_REGION
    _type2class = {SAMPLE: PenSampleEvent, ENTER: PenEnterRegionEvent,
                   LEAVE: PenLeaveRegionEvent}
    # TODO: name and class args should just be auto generated in init.
    def __init__(self, ioclient, device_class_name, device_config):
        super(WintabTablet, self).__init__(ioclient, device_class_name,
                                       device_config)
        self._events = dict()
        self._reporting = False
        self._device_config = device_config
        self._event_buffer_length = self._device_config.get(
            'event_buffer_length')

        self._clearEventsRPC = DeviceRPC(self.hubClient._sendToHubServer, self.device_class, 'clearEvents')

        wthw = self.getHarwareConfig()
        self._context = wthw['WinTabContext']
        self._axis = wthw['WintabHardwareInfo']

    def _syncDeviceState(self):
        """
        An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None
        """
        kb_state = self.getCurrentDeviceState()
        self._reporting = kb_state.get('reporting_events')

        for etype, event_arrays in kb_state.get('events').items():
            self._events.setdefault(etype, deque(
                maxlen=self._event_buffer_length)).extend(
                [self._type2class[etype](e, self) for e in event_arrays])

    @property
    def reporting(self):
        """
        Specifies if the the keyboard device is reporting / recording events.
          * True:  keyboard events are being reported.
          * False: keyboard events are not being reported.

        By default, the Keyboard starts reporting events automatically when the
        ioHub process is started and continues to do so until the process is
        stopped.

        This property can be used to read or set the device reporting state::

          # Read the reporting state of the keyboard.
          is_reporting_keyboard_event = keyboard.reporting

          # Stop the keyboard from reporting any new events.
          keyboard.reporting = False

        """
        return self._reporting


    @reporting.setter
    def reporting(self, r):
        """
        Sets the state of keyboard event reporting / recording.
        """
        self._reporting = self.enableEventReporting(r)
        return self._reporting

    @property
    def axis(self):
        return self._axis

    @property
    def context(self):
        return self._context

    def clearEvents(self, event_type=None, filter_id=None):
        result = self._clearEventsRPC(event_type=event_type,filter_id=filter_id)
        for etype, elist in self._events.items():
            if event_type is None or event_type == etype:
                elist.clear()
        return result

    def getSamples(self, clear=True):
        """
        Return a list of any Tablet sample events that have
        occurred since the last time either:

        * this method was called with the kwarg clear=True (default)
        * the tablet.clear() method was called.
        """
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.SAMPLE, [])]

        if return_events and clear is True:
            self._events[e._type]=[]

        return sorted(return_events, key=lambda x: x.time)

    def getEnters(self, clear=True):
        """
        """
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.ENTER, [])]

        if return_events and clear is True:
            self._events[e._type]=[]

        return sorted(return_events, key=lambda x: x.time)

    def getLeaves(self, clear=True):
        """
        """
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.LEAVE, [])]

        if return_events and clear is True:
            self._events[e._type]=[]

        return sorted(return_events, key=lambda x: x.time)
