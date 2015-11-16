from __future__ import division
# -*- coding: utf-8 -*-
# ioHub Python Module
# .. file: psychopy/iohub/client/wintabtablet.py
#
# fileauthor: Sol Simpson <sol@isolver-software.com>
#
# Copyright (C) 2012-2015 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License
# (GPL version 3 or any later version).

from collections import deque
import math
import numpy as np

from psychopy.iohub.client import ioHubDeviceView, ioEvent, DeviceRPC
from psychopy.iohub.devices import Computer
from psychopy.iohub.devices.wintab import WintabTabletSampleEvent, WintabTabletEnterRegionEvent, WintabTabletLeaveRegionEvent
from psychopy.iohub.constants import EventConstants

if Computer.system == 'win32':
    from win32api import LOWORD, HIWORD
    FRAC = LOWORD
    INT = HIWORD
else:
    FRAC = lambda x: x & 0x0000ffff
    INT = lambda x: x >> 16

def FIX_DOUBLE(x):
    return INT(x) + FRAC(x)/65536.0

"""
TabletPen Device and Events Types

"""


class PenSampleEvent(ioEvent):
    """
    Represents a tablet pen position / pressure event.
    """
    STATES=dict()
    # A sample that is the first sample following a time gap in the sample stream
    STATES[1] = 'FIRST_ENTER'
    # A sample that is the first sample with pressure == 0
    # following a sample with pressure > 0
    STATES[2] = 'FIRST_HOVER'
    # A sample that has pressure == 0, and previous sample also had pressure  == 0
    STATES[4] = 'HOVERING'
    # A sample that is the first sample with pressure > 0
    # following a sample with pressure == 0
    STATES[8] = 'FIRST_PRESS'
    #  A sample that has pressure > 0
    # following a sample with pressure > 0
    STATES[16] = 'PRESSED'

    _attrib_index = dict()
    _attrib_index['x'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('x')
    _attrib_index['y'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('y')
    _attrib_index['z'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('z')
    _attrib_index['buttons'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index('buttons')
    _attrib_index['pressure'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'pressure')
    _attrib_index['altitude'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'orient_altitude')
    _attrib_index['azimuth'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'orient_azimuth')
    _attrib_index['status'] = WintabTabletSampleEvent.CLASS_ATTRIBUTE_NAMES.index(
        'status')
    def __init__(self, ioe_array, device):
        super(PenSampleEvent, self).__init__(ioe_array, device)
        for efname, efvalue in PenSampleEvent._attrib_index.items():
            if efvalue>=0:
                setattr(self,'_'+efname,ioe_array[efvalue])
        self._velocity=0.0
        self._accelleration=0.0

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def getPixPos(self, win):
        sw, sh = win.winHandle.width, win.winHandle.height
        nx, ny = self._x/self.device.axis['x']['range'], self._y/self.device.axis['y']['range']
        return int(nx*sw-sw/2), int(ny*sh-sh/2)

    def getNormPos(self):
        return (-1.0+(self._x/ self.device.axis['x']['range'])*2.0,
                -1.0+(self._y/ self.device.axis['y']['range'])*2.0)

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
    def buttons(self):
        return self._buttons

    @property
    def status(self):
        return [v for k, v in self.STATES.items() if self._status&k==k]

    @property
    def tilt(self):
        '''
        Get the pen horizontal & vertical tilt for the sample.

        horizontal tilt (azimuth) is in radians,
        vertical tilt (altitude) is in ????.

        Note: wintab.h defines .orAltitude as a UINT but documents .orAltitude
        as positive for upward angles and negative for downward angles.
        WACOM uses negative altitude values to show that the pen is inverted;
        therefore we cast .orAltitude as an (int) and then use the absolute
        value.
        '''
        axis = self.device.axis
        if axis['orient_altitude']['supported'] and axis['orient_azimuth']['supported']:
            tilt1 = axis['orient_altitude']['adjust'] - \
                    abs(self.altitude)/axis['orient_altitude']['factor']
            # below line would normalize the altitude to approx. between 0 and 1.0
            #
            #tilt1 = (1.0 -(self.altitude/axis['orient_altitude']['axMax']))

            #/* adjust azimuth */
            tilt2 = float(self.azimuth/axis['orient_azimuth']['factor'])

            return tilt1, tilt2
        return 0,0

    @property
    def velocity(self):
        '''
        Returns the calculated x, y, and xy velocity for the current sample.
        :return: (float, float, float)
        '''
        return self._velocity

    @property
    def accelleration(self):
        '''
        Returns the calculated x, y, and xy accelleration
        for the current sample.
        :return: (float, float, float)
        '''
        return self._accelleration

    @velocity.setter
    def velocity(self, v):
        '''
        Returns the calculated x, y, and xy velocity for the current sample.
        :return: (float, float, float)
        '''
        self._velocity = v

    @accelleration.setter
    def accelleration(self, a):
        '''
        Returns the calculated x, y, and xy accelleration
        for the current sample.
        :return: (float, float, float)
        '''
        self._accelleration = a

    def __str__(self):
        return "{}, x,y,z: {}, {}, {} pressure: {}, tilt: {}".format(
            ioEvent.__str__(self), self.x, self.y, self.z, self.tilt)


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

        self._prev_sample=None

        self._events = dict()
        self._reporting = False
        self._device_config = device_config
        self._event_buffer_length = self._device_config.get(
            'event_buffer_length')
        self._clearEventsRPC = DeviceRPC(self.hubClient._sendToHubServer, self.device_class, 'clearEvents')
        self._context = {'Context': {'status': 'Device not Initialized'}}
        self._axis = {'Axis': {'status': 'Device not Initialized'}}
        self._hw_model = {'ModelInfo': {'status': 'Device not Initialized'}}

        if self.getInterfaceStatus() == "HW_OK":
            wthw = self.getHardwareConfig()
            self._context = wthw['Context']
            self._axis = wthw['Axis']
            self._hw_model = wthw['ModelInfo']

            # Add extra axis info
            for axis in self._axis.values():
                axis['range'] = axis['max']-axis['min']
                axis['supported'] = axis['range'] != 0


            # Add tilt related calc constants to orient_azimuth
            # and orient_altitude axis
            #
            if self._axis['orient_azimuth']['supported'] and self._axis['orient_altitude']['supported']:
                azimuth_axis = self._axis['orient_azimuth']
                azimuth_axis['factor'] = FIX_DOUBLE(azimuth_axis['resolution'])/(2*math.pi)

                altitude_axis = self._axis['orient_altitude']
                # convert altitude resolution to double
                altitude_axis['factor'] = FIX_DOUBLE(altitude_axis['resolution'])
                # adjust for maximum value at vertical */
                altitude_axis['adjust'] = altitude_axis['max']/altitude_axis['factor']

    def _calculateVelAccel(self,s):
        curr_samp = self._type2class[self.SAMPLE](s, self)
        if 'FIRST_ENTER' in curr_samp.status:
            self._prev_sample=None
        prev_samp = self._prev_sample
        if prev_samp:
            dx=curr_samp.x-prev_samp.x
            dy=curr_samp.y-prev_samp.y
            dt=(curr_samp.time-prev_samp.time)#*1000.0
            cvx, cvy, cvxy = curr_samp.velocity = dx/dt, dy/dt, np.sqrt(dx*dx+dy*dy)/dt

            pvx, pvy, pvxy = prev_samp.velocity
            if prev_samp.velocity != (0, 0, 0):
                curr_samp.accelleration = (cvx-pvx)/dt, (cvy-pvy)/dt, np.sqrt((cvx-pvx)*(cvx-pvx)+(cvy-pvy)*(cvy-pvy))/dt
            else:
                curr_samp.accelleration = (0, 0, 0)
        else:
            curr_samp.velocity = (0, 0, 0)
            curr_samp.accelleration = (0, 0, 0)
        self._prev_sample = curr_samp
        return curr_samp

    def _syncDeviceState(self):
        """
        An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None
        """
        kb_state = self.getCurrentDeviceState()
        self._reporting = kb_state.get('reporting_events')

        for etype, event_arrays in kb_state.get('events').items():
            et_queue = self._events.setdefault(etype, deque(maxlen=self._event_buffer_length))

            if etype == self.SAMPLE:
                for s in event_arrays:
                    et_queue.append(self._calculateVelAccel(s))
            else:
                et_queue.extend([self._type2class[etype](e, self) for e in event_arrays])

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
        if r is True:
            self._prev_sample=None
        self._reporting = self.enableEventReporting(r)
        return self._reporting

    @property
    def axis(self):
        return self._axis

    @property
    def context(self):
        return self._context

    @property
    def model(self):
        return self._hw_model

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
