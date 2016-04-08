# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

#
# TODO List
#
#   1) Refactor code so that wintab.__init__.py and win32.py are separated
#      in a more sensible way
#
#   2) Check for missing serial numbers in PACKET evt stream.
#
_is_epydoc = False

# Pen digitizers /tablets that support Wintab API
from .. import Device, Computer
from ...constants import EventConstants, DeviceConstants
from ...errors import print2err, printExceptionDetailsToStdErr
import numpy as N
import copy


class WintabTablet(Device):
    """The Wintab class docstr TBC."""
    EVENT_CLASS_NAMES = ['WintabTabletSampleEvent',
                         'WintabTabletEnterRegionEvent',
                         'WintabTabletLeaveRegionEvent']

    DEVICE_TYPE_ID = DeviceConstants.WINTABTABLET
    DEVICE_TYPE_STRING = 'WINTABTABLET'

    __slots__ = ['_wtablets',
                 '_wtab_shadow_windows',
                 '_wtab_canvases',
                 '_last_sample',
                 '_first_hw_and_hub_times'
                 ]

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs['dconfig'])
        self._wtablets = []
        self._wtab_shadow_windows = []
        self._wtab_canvases = []
        self._init_wintab()

        # Following are used for sample status tracking
        self._last_sample = None
        self._first_hw_and_hub_times = None

    def _init_wintab(self):

        if Computer.platform == 'win32' and Computer.is_iohub_process:
            try:
                from .win32 import get_tablets
            except:
                self._setHardwareInterfaceStatus(
                    False, u"Error: ioHub Wintab Device "
                    u"requires wintab32.dll to be "
                    u"installed.")

                def get_tablets(display=None):
                    return []

        else:
            def get_tablets(display=None):
                print2err('Error: iohub.devices.wintab only supports '
                          'Windows OS at this time.')
                return []

            self._setHardwareInterfaceStatus(False,
                                             u"Error:ioHub Wintab Device "
                                             u"only supports Windows OS "
                                             u"at this time.")

        self._wtablets = get_tablets()

        index = self.getConfiguration().get('device_number', 0)

        if self._wtablets is None:
            return False
        if len(self._wtablets) == 0:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: No WinTab Devices"
                                             u" Detected.")
            return False
        if index >= len(self._wtablets):
            self._setHardwareInterfaceStatus(
                False, u"Error: device_number {} "
                u"is out of range. Only {} "
                u"WinTab devices detected.". format(
                    index, len(
                        self._wtablets)))
            return False

        exp_screen_info = self._display_device.getRuntimeInfo()
        swidth, sheight = exp_screen_info.get('pixel_resolution', [None, None])
        screen_index = exp_screen_info.get('index', 0)
        if swidth is None:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: Wintab device is"
                                             u" unable to query experiment "
                                             u"screen pixel_resolution.")
            return False

        from pyglet.window import Window
        self._wtab_shadow_windows.append(
            Window(
                width=swidth,
                height=sheight,
                visible=False,
                fullscreen=True,
                vsync=False,
                screen=screen_index))
        self._wtab_shadow_windows[0].set_mouse_visible(False)
        self._wtab_shadow_windows[0].switch_to()

        from pyglet import app
        app.windows.remove(self._wtab_shadow_windows[0])

        try:
            self._wtab_canvases.append(
                self._wtablets[index].open(self._wtab_shadow_windows[0], self))
        except Exception as e:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: Unable to create"
                                             u"WintabTabletCanvas for device."
                                             u"Exception: {}".
                                             format(e))
            return False

        self._setHardwareInterfaceStatus(True)
        return True

    def getHardwareConfig(self, index=0):
        hw_model_info = self._wtablets[index].hw_model_info
        return {'Context': self._wtab_canvases[index].getContextInfo(),
                'Axis': self._wtablets[index].hw_axis_info,
                'ModelInfo': hw_model_info
                }

    def enableEventReporting(self, enabled=True):
        for wtc in self._wtab_canvases:
            wtc.enable(enabled)

        if self.isReportingEvents() != enabled:
            self._last_sample = None
            self._first_hw_and_hub_times = None

        return Device.enableEventReporting(self, enabled)

    def _poll(self):
        try:
            for swin in self._wtab_shadow_windows:
                swin.dispatch_events()
            logged_time = Computer.getTime()

            if not self.isReportingEvents():
                self._last_poll_time = logged_time
                for wtc in self._wtab_canvases:
                    del wtc._iohub_events[:]
                return False

            confidence_interval = logged_time - self._last_poll_time
            # Using 0 delay for now as it is unknown.
            delay = 0.0

            for wtc in self._wtab_canvases:
                wintab_events = copy.deepcopy(wtc._iohub_events)
                del wtc._iohub_events[:]
                for wte in wintab_events:
                    if wte and wte[0] != EventConstants.WINTAB_TABLET_SAMPLE:
                        # event is enter or leave region type, so clear
                        # last sample as a flag that next sample should
                        # be FIRST_ENTER
                        self._last_sample = None
                    else:
                        if self._first_hw_and_hub_times is None:
                            self._first_hw_and_hub_times = wte[1], logged_time

                        status = 0
                        cur_press_state = wte[8]
                        if self._last_sample is None:
                            status += WintabTabletSampleEvent.STATES[
                                'FIRST_ENTER']
                            if cur_press_state > 0:
                                status += WintabTabletSampleEvent.STATES[
                                    'FIRST_PRESS']
                                status += WintabTabletSampleEvent.STATES[
                                    'PRESSED']
                            else:
                                status += WintabTabletSampleEvent.STATES[
                                    'FIRST_HOVER']
                                status += WintabTabletSampleEvent.STATES[
                                    'HOVERING']
                        else:
                            prev_press_state = self._last_sample[8]
                            if cur_press_state > 0:
                                status += WintabTabletSampleEvent.STATES[
                                    'PRESSED']
                            else:
                                status += WintabTabletSampleEvent.STATES[
                                    'HOVERING']

                            if cur_press_state > 0 and prev_press_state == 0:
                                status += WintabTabletSampleEvent.STATES[
                                    'FIRST_PRESS']
                            elif cur_press_state == 0 and prev_press_state > 0:
                                status += WintabTabletSampleEvent.STATES[
                                    'FIRST_HOVER']
                        # Fill in status field based on previous sample.......
                        wte[-1] = status
                        self._last_sample = wte

                    self._addNativeEventToBuffer((logged_time,
                                                  delay,
                                                  confidence_interval,
                                                  wte))
            self._last_poll_time = logged_time
            return True
        except Exception as e:
            print2err('ERROR in WintabTabletDevice._poll: ', e)
            printExceptionDetailsToStdErr()

    def _getIOHubEventObject(self, native_event_data):
        '''

        :param native_event_data:
        :return:
        '''
        logged_time, delay, confidence_interval, wt_event = native_event_data
        evt_type = wt_event[0]
        device_time = wt_event[1]
        evt_status = wt_event[2]

        # TODO: Correct for polling interval / CI when calculating iohub_time
        iohub_time = logged_time
        if self._first_hw_and_hub_times:
            hwtime, iotime = self._first_hw_and_hub_times
            iohub_time = iotime + (wt_event[1] - hwtime)
            #print2err('STIME: ',[iohub_time, logged_time, logged_time-iohub_time])

        ioevt = [0, 0, 0, Device._getNextEventID(),
                 evt_type,
                 device_time,
                 logged_time,
                 iohub_time,
                 confidence_interval,
                 delay,
                 0
                 ]
        ioevt.extend(wt_event[3:])
        return ioevt

    def _close(self):
        for wtc in self._wtab_canvases:
            wtc.close()
        for swin in self._wtab_shadow_windows:
            swin.close()
        Device._close()

############# Wintab Event Classes ####################

from .. import DeviceEvent


class WintabTabletInputEvent(DeviceEvent):
    """The WintabTabletInputEvent is an abstract class that ......."""
    PARENT_DEVICE = WintabTablet
    _newDataTypes = []

    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)


class WintabTabletSampleEvent(WintabTabletInputEvent):
    """WintabTabletSampleEvent's occur when....."""
    EVENT_TYPE_STRING = 'WINTAB_TABLET_SAMPLE'
    EVENT_TYPE_ID = EventConstants.WINTAB_TABLET_SAMPLE
    IOHUB_DATA_TABLE = EVENT_TYPE_STRING

    STATES = dict()
    # A sample that is the first sample following a time gap in the sample
    # stream
    STATES['FIRST_ENTER'] = 1
    # A sample that is the first sample with pressure == 0
    # following a sample with pressure > 0
    STATES['FIRST_HOVER'] = 2
    # A sample that has pressure == 0, and previous sample also had pressure
    # == 0
    STATES['HOVERING'] = 4
    # A sample that is the first sample with pressure > 0
    # following a sample with pressure == 0
    STATES['FIRST_PRESS'] = 8
    #  A sample that has pressure > 0
    # following a sample with pressure > 0
    STATES['PRESSED'] = 16
    for k, v in STATES.items():
        STATES[v] = k

    _newDataTypes = [
        ('serial_number', N.uint32),
        ('buttons', N.int32),
        ('x', N.int32),
        ('y', N.int32),
        ('z', N.int32),
        ('pressure', N.uint32),
        ('orient_azimuth', N.int32),
        ('orient_altitude', N.int32),
        ('orient_twist', N.int32),
        ('status', N.uint8)
    ]

    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        #: serial_number Hardware assigned PACKET serial number
        self.serial_number = None

        #: TODO: buttons
        self.buttons = None

        #: x Horizontal position of stylus on tablet surface.
        self.x = None

        #: y Vertical position of stylus on tablet surface.
        self.y = None

        #: z Distance of stylus tip from tablet surface
        #: Supported on Wacom Intuos4; other device support unknown.
        #: Value will between 0 and max_val, where max_val is usually 1024.
        #: A value of 0 = tip touching surface, while
        #: max_val = tip height above surface before events stop being reported.
        self.z = None

        #: pressure: Pressure of stylus tip on tablet surface.
        self.pressure = None

        #: orient_azimuth
        self.orient_azimuth = None

        #: orient_altitude
        self.orient_altitude = None

        #: orient_twist
        self.orient_twist = None
        WintabTabletInputEvent.__init__(self, *args, **kwargs)


class WintabTabletEnterRegionEvent(WintabTabletSampleEvent):
    """
    TODO: WintabTabletEnterRegionEvent doc str
    """
    EVENT_TYPE_STRING = 'WINTAB_TABLET_ENTER_REGION'
    EVENT_TYPE_ID = EventConstants.WINTAB_TABLET_ENTER_REGION
    IOHUB_DATA_TABLE = WintabTabletSampleEvent.EVENT_TYPE_STRING

    def __init__(self, *args, **kwargs):
        WintabTabletSampleEvent.__init__(self, *args, **kwargs)


class WintabTabletLeaveRegionEvent(WintabTabletSampleEvent):
    """
    TODO: WintabTabletLeaveRegionEvent doc str
    """
    EVENT_TYPE_STRING = 'WINTAB_TABLET_LEAVE_REGION'
    EVENT_TYPE_ID = EventConstants.WINTAB_TABLET_LEAVE_REGION
    IOHUB_DATA_TABLE = WintabTabletSampleEvent.EVENT_TYPE_STRING

    def __init__(self, *args, **kwargs):
        WintabTabletSampleEvent.__init__(self, *args, **kwargs)
