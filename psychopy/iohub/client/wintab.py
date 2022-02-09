# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from collections import deque
import math
import numpy as np

from . import ioHubDeviceView, ioEvent, DeviceRPC
from ..devices import Computer
from ..devices.wintab import WintabSampleEvent
from ..constants import EventConstants

if Computer.platform == 'win32':
    import win32api
    FRAC = LOWORD = win32api.LOWORD
    INT = HIWORD = win32api.HIWORD
else:
    FRAC = lambda x: x & 0x0000ffff
    INT = lambda x: x >> 16

def FIX_DOUBLE(x):
    return INT(x) + FRAC(x) / 65536.0

#
### Patch psychopy.platform_specific.sendStayAwake
### so that it does not cause psychopy window to consume
### events needed by iohub.devices.wintab.
#
def _noOpFunc():
    pass

from psychopy import platform_specific
_sendStayAwake = platform_specific.sendStayAwake
platform_specific.sendStayAwake=_noOpFunc
_sendStayAwake()
print(">> iohub.wintab device patching platform_specific.sendStayAwake.")

# TabletPen Device and Events Types


class PenSampleEvent(ioEvent):
    """Represents a tablet pen position / pressure event."""
    STATES = dict()
    STATES[1] = 'FIRST_ENTER'
    STATES[2] = 'FIRST_HOVER'
    STATES[4] = 'HOVERING'
    STATES[8] = 'FIRST_PRESS'
    STATES[16] = 'PRESSED'

    wtsample_attrib_names = WintabSampleEvent.CLASS_ATTRIBUTE_NAMES
    _attrib_index = dict()
    _attrib_index['x'] = wtsample_attrib_names.index('x')
    _attrib_index['y'] = wtsample_attrib_names.index('y')
    _attrib_index['z'] = wtsample_attrib_names.index('z')
    _attrib_index['buttons'] = wtsample_attrib_names.index('buttons')
    _attrib_index['pressure'] = wtsample_attrib_names.index('pressure')
    _attrib_index['altitude'] = wtsample_attrib_names.index('orient_altitude')
    _attrib_index['azimuth'] = wtsample_attrib_names.index('orient_azimuth')
    _attrib_index['status'] = wtsample_attrib_names.index('status')

    def __init__(self, ioe_array, device):
        super(PenSampleEvent, self).__init__(ioe_array, device)
        for efname, efvalue in list(PenSampleEvent._attrib_index.items()):
            if efvalue >= 0:
                setattr(self, '_' + efname, ioe_array[efvalue])
        self._velocity = 0.0
        self._acceleration = 0.0

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    def getPixPos(self, win):
        sw, sh = win.winHandle.width, win.winHandle.height
        return (int(self._x / self.device.axis['x']['range'] * sw - sw / 2),
                int(self._y / self.device.axis['y']['range'] * sh - sh / 2))


    def getNormPos(self):
        return (-1.0 + (self._x / self.device.axis['x']['range']) * 2.0,
                -1.0 + (self._y / self.device.axis['y']['range']) * 2.0)

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
        return [v for k, v in list(self.STATES.items()) if self._status & k == k]

    @property
    def tilt(self):
        """Get the pen horizontal & vertical tilt for the sample.

        horizontal tilt (azimuth)
        vertical tilt (altitude)
        """
        axis = self.device.axis
        altitude_axis = axis['orient_altitude']
        azimuth_axis = axis['orient_azimuth']
        if altitude_axis['supported'] and azimuth_axis['supported']:
            tilt1 = altitude_axis['adjust']
            tilt1 -= abs(self.altitude) / altitude_axis['factor']
            #/* adjust azimuth */
            tilt2 = float(self.azimuth / azimuth_axis['factor'])
            return tilt1, tilt2
        return 0, 0

    @property
    def velocity(self):
        """Returns the calculated x, y, and xy velocity for the current sample.

        :return: (float, float, float)

        """
        return self._velocity

    @property
    def acceleration(self):
        """Returns the calculated x, y, and xy acceleration for the current
        sample.

        :return: (float, float, float)

        """
        return self._acceleration

    @property
    def accelleration(self):  # deprecated, use acceleration instead
        return self._acceleration

    @velocity.setter
    def velocity(self, v):
        """Returns the calculated x, y, and xy velocity for the current sample.

        :return: (float, float, float)

        """
        self._velocity = v

    @acceleration.setter
    def acceleration(self, a):
        """Returns the calculated x, y, and xy acceleration for the current
        sample.

        :return: (float, float, float)

        """
        self._acceleration = a

    @accelleration.setter
    def accelleration(self, a):  # deprecated, use acceleration instead
        self._acceleration = a

    def __str__(self):
        sargs = [ioEvent.__str__(self), self.x, self.y, self.z, self.pressure,
                 self.tilt]
        return '{}, x,y,z: {}, {}, {} pressure: {}, tilt: {}'.format(*sargs)


class PenEnterRegionEvent(ioEvent):
    """Occurs when Stylus enters the tablet region."""

    def __init__(self, ioe_array, device):
        super(PenEnterRegionEvent, self).__init__(ioe_array, device)


class PenLeaveRegionEvent(ioEvent):
    """Occurs when Stylus leaves the tablet region."""

    def __init__(self, ioe_array, device):
        super(PenLeaveRegionEvent, self).__init__(ioe_array, device)


class Wintab(ioHubDeviceView):
    """The Wintab device provides access to PenSampleEvent events."""
    SAMPLE = EventConstants.WINTAB_SAMPLE
    ENTER = EventConstants.WINTAB_ENTER_REGION
    LEAVE = EventConstants.WINTAB_LEAVE_REGION
    _type2class = {SAMPLE: PenSampleEvent,
                   ENTER: PenEnterRegionEvent,
                   LEAVE: PenLeaveRegionEvent}
    def __init__(self, ioclient, dev_cls_name, dev_config):
        super(Wintab, self).__init__(ioclient, 'client.Wintab', dev_cls_name, dev_config)

        self._prev_sample = None
        self._events = dict()
        self._reporting = False
        self._device_config = dev_config
        self._event_buffer_length = dev_config.get('event_buffer_length')
        self._clearEventsRPC = DeviceRPC(self.hubClient._sendToHubServer,
                                         self.device_class, 'clearEvents')
        self._context = {'Context': {'status': 'Device not Initialized'}}
        self._axis = {'Axis': {'status': 'Device not Initialized'}}
        self._hw_model = {'ModelInfo': {'status': 'Device not Initialized'}}

        if self.getInterfaceStatus() == 'HW_OK':
            wthw = self.getHardwareConfig()
            self._context = wthw['Context']
            self._axis = wthw['Axis']
            self._hw_model = wthw['ModelInfo']

            # Add extra axis info
            for axis in list(self._axis.values()):
                axis['range'] = axis['max'] - axis['min']
                axis['supported'] = axis['range'] != 0

            # Add tilt related calc constants to orient_azimuth
            # and orient_altitude axis
            #
            azi_axis = self._axis['orient_azimuth']
            alt_axis = self._axis['orient_altitude']
            if azi_axis['supported'] and alt_axis['supported']:
                azi_axis['factor'] = FIX_DOUBLE(azi_axis['resolution'])
                azi_axis['factor'] = azi_axis['factor'] / (2 * math.pi)

                # convert altitude resolution to double
                alt_axis['factor'] = FIX_DOUBLE(alt_axis['resolution'])
                # adjust for maximum value at vertical
                alt_axis['adjust'] = alt_axis['max'] / alt_axis['factor']

    def _calculateVelAccel(self, s):
        curr_samp = self._type2class[self.SAMPLE](s, self)
        if 'FIRST_ENTER' in curr_samp.status:
            self._prev_sample = None
        prev_samp = self._prev_sample
        if prev_samp:
            try:
                dx = curr_samp.x - prev_samp.x
                dy = curr_samp.y - prev_samp.y
                dt = (curr_samp.time - prev_samp.time)
                if dt <= 0:
                    print(
                        'Warning: dt == 0: {}, {}, {}'.format(
                            dt, curr_samp.time, prev_samp.time))
                    curr_samp.velocity = (0, 0, 0)
                    curr_samp.acceleration = (0, 0, 0)
                else:
                    cvx = dx / dt
                    cvy = dy / dt
                    cvxy = np.sqrt(dx * dx + dy * dy) / dt
                    curr_samp.velocity = cvx, cvy, cvxy
                    pvx, pvy, _ = prev_samp.velocity
                    if prev_samp.velocity != (0, 0, 0):
                        dx = cvx - pvx
                        dy = cvy - pvy
                        cax = dx / dt
                        cay = dy / dt
                        cayx = np.sqrt(dx * dx + dy * dy) / dt
                        curr_samp.acceleration = cax, cay, cayx
                    else:
                        curr_samp.acceleration = (0, 0, 0)
            except ZeroDivisionError:
                print("ERROR: wintab._calculateVelAccel ZeroDivisionError "
                      "occurred. prevId: %d, currentId: %d" % (curr_samp.id,
                                                               prev_samp.id))
                curr_samp.velocity = (0, 0, 0)
                curr_samp.acceleration = (0, 0, 0)
            except Exception as e: #pylint: disable=broad-except
                print("ERROR: wintab._calculateVelAccel error [%s] occurred."
                      "prevId: %d, currentId: %d" % (str(e), curr_samp.id,
                                                     prev_samp.id))
                curr_samp.velocity = (0, 0, 0)
                curr_samp.acceleration = (0, 0, 0)
        else:
            curr_samp.velocity = (0, 0, 0)
            curr_samp.acceleration = (0, 0, 0)
        self._prev_sample = curr_samp
        return curr_samp

    def _syncDeviceState(self):
        """An optimized iohub server request that receives all device state and
        event information in one response.

        :return: None

        """
        kb_state = self.getCurrentDeviceState()
        self._reporting = kb_state.get('reporting_events')

        for etype, event_arrays in list(kb_state.get('events').items()):
            etype = int(etype)
            ddeque = deque(maxlen=self._event_buffer_length)
            et_queue = self._events.setdefault(etype, ddeque)

            if etype == self.SAMPLE:
                for s in event_arrays:
                    et_queue.append(self._calculateVelAccel(s))
            else:
                for evt in event_arrays:
                    et_queue.append(self._type2class[etype](evt, self))

    @property
    def reporting(self):
        """Specifies if the the device is reporting / recording events.

          * True:  events are being reported.
          * False: events are not being reported.
        """
        return self._reporting

    @reporting.setter
    def reporting(self, r):
        """Sets the state of keyboard event reporting / recording."""
        if r is True:
            self._prev_sample = None
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
        result = self._clearEventsRPC(event_type=event_type,
                                      filter_id=filter_id)
        for etype, elist in list(self._events.items()):
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
            self._events.get(self.SAMPLE).clear()

        return sorted(return_events, key=lambda x: x.time)

    def getEnters(self, clear=True):
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.ENTER, [])]
        if return_events and clear is True:
            self._events.get(self.ENTER).clear()
        return sorted(return_events, key=lambda x: x.time)

    def getLeaves(self, clear=True):
        self._syncDeviceState()
        return_events = [e for e in self._events.get(self.LEAVE, [])]
        if return_events and clear is True:
            self._events.get(self.LEAVE).clear()
        return sorted(return_events, key=lambda x: x.time)
