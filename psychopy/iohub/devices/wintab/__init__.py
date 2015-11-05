# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/wintab/__init__.py

Copyright (C) 2012-2015 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

#
### TODO List
#
#   1) Use full screen psychopy experiment window info when creating
#      wintab shadow window
#
#   2) Add settings to device that allow user to specify hardware config values
#      for tablet and tablet context.
#
#   3) Refactor code so that wintab.__init__.py and win32.py are separated
#      in a more sensible way
##
#   4) Check for missing serial numbers in PACKET evt stream.
#
_is_epydoc=False

# Pen digitizers /tablets that support Wintab API
from psychopy.iohub import Computer, Device,print2err
from ...constants import EventConstants, DeviceConstants
import numpy as N

class WintabTablet(Device):
    """
    The Wintab class docstr TBC

    """
    EVENT_CLASS_NAMES=['WintabTabletSampleEvent',
                       'WintabTabletEnterRegionEvent',
                       'WintabTabletLeaveRegionEvent']

    DEVICE_TYPE_ID=DeviceConstants.WINTABTABLET
    DEVICE_TYPE_STRING='WINTABTABLET'

    __slots__=['_wtablets',
               '_wtab_shadow_windows',
               '_wtab_canvases'
    ]

    def __init__(self,*args,**kwargs):
        Device.__init__(self,*args,**kwargs['dconfig'])
        self._wtablets=[]
        self._wtab_shadow_windows=[]
        self._wtab_canvases=[]
        self._init_wintab()

    def _init_wintab(self):
        self._wtablets = get_tablets()
        if Computer.system != 'win32':
            self._setHardwareInterfaceStatus(False,
                                             u"Error:ioHub Wintab Device only"
                                             u" supports Windows OS "
                                             u"at this time.")
            return False

        index = self.getConfiguration().get('device_number',0)

        if len(self._wtablets) == 0:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: No WinTab Devices"
                                             u" Detected.")
            return False
        if index >= len(self._wtablets):
            self._setHardwareInterfaceStatus(False,
                                             u"Error: device_number {} "
                                             u"is out of range. Only {} "
                                             u"WinTab devices detected.".
                                             format(index, len(self._wtablets)))
            return False

        exp_screen_info = self._display_device.getRuntimeInfo()
        swidth, sheight = exp_screen_info.get('pixel_resolution',[None, None])
        screen_index = exp_screen_info.get('index',0)
        if swidth is None:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: Wintab device is"
                                             u" unable to query experiment "
                                             u"screen pixel_resolution.")
            return False

        from pyglet.window import Window
        self._wtab_shadow_windows.append(
            Window(width=swidth, height=sheight, visible=False, fullscreen=True,
                   vsync=False, screen=screen_index))
        self._wtab_shadow_windows[0].set_mouse_visible(False)
        self._wtab_shadow_windows[0].switch_to()

        from pyglet import app
        app.windows.remove(self._wtab_shadow_windows[0])

        try:
            self._wtab_canvases.append(
                self._wtablets[index].open(self._wtab_shadow_windows[0],self ))
        except Exception, e:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: Unable to create"
                                             u"WintabTabletCanvas for device."
                                             u"Exception: {}".
                                             format(e))
            return False

        self._setHardwareInterfaceStatus(True)
        return True

    def getHardwareConfig(self, index=0):
        return {"Context":self._wtab_canvases[index].getContextInfo(),
                 "Axis":self._wtablets[index].hw_axis_info,
                 "ModelInfo":self._wtablets[index].hw_model_info
                }

    def enableEventReporting(self,enabled=True):
        for wtc in self._wtab_canvases:
            wtc.enable(enabled)
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
            #TODO: Determine if delay can be calculated.
            #      Using 0 for now as it is unknown.
            delay = 0.0

            for wtc in self._wtab_canvases:
                for wte in wtc._iohub_events:
                    self._addNativeEventToBuffer((logged_time,
                                                  delay,
                                                  confidence_interval,
                                                  wte))

                del wtc._iohub_events[:]
            self._last_poll_time = logged_time
            return True
        except Exception, e:
            print2err("ERROR in WintabTabletDevice._poll: ",e)

    def _getIOHubEventObject(self,native_event_data):
        '''

        :param native_event_data:
        :return:
        '''
        logged_time, delay, confidence_interval, wt_event = native_event_data
        evt_type = wt_event.pop(0)
        device_time = wt_event.pop(0)
        evt_status = wt_event.pop(0)

        #TODO: Correct for polling interval / CI when calculating iohub_time
        iohub_time = logged_time

        ioevt=[0, 0, 0, Computer._getNextEventID(),
               evt_type,
               device_time,
               logged_time,
               iohub_time,
               confidence_interval,
               delay,
               0
            ]
        ioevt.extend(wt_event)
        return ioevt

    def _close(self):
        for wtc in self._wtab_canvases:
            wtc.close()
        for swin in self._wtab_shadow_windows:
            swin.close()
        Device._close()

if Computer.system == 'win32':
    from .win32 import get_tablets
else:
    def get_tablets(display=None):
        print2err("Error: iohub.devices.wintab only supports Windows OS at this time.")
        return []
############# Wintab Event Classes ####################

from .. import DeviceEvent

class WintabTabletInputEvent(DeviceEvent):
    """
    The WintabTabletInputEvent is an abstract class that .......
    """
    PARENT_DEVICE=WintabTablet
    _newDataTypes = []

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)

class WintabTabletSampleEvent(WintabTabletInputEvent):
    """
    WintabTabletSampleEvent's occur when.....
    """
    EVENT_TYPE_STRING='WINTAB_TABLET_SAMPLE'
    EVENT_TYPE_ID=EventConstants.WINTAB_TABLET_SAMPLE
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    _newDataTypes = [
                     ('serial_number', N.uint32),
                     ('buttons',N.int32),
                     ('x',N.int32),
                     ('y',N.int32),
                     ('z',N.int32),
                     ('pressure',N.uint32),
                     ('orient_azimuth',N.int32),
                     ('orient_altitude',N.int32),
                     ('orient_twist',N.int32)
                     ]

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self, *args, **kwargs):
        #: serial_number Hardware assigned PACKET serial number
        self.serial_number=None

        #: TODO: buttons
        self.buttons=None

        #: x Horizontal position of stylus on tablet surface.
        self.x=None

        #: y Vertical position of stylus on tablet surface.
        self.y=None

        #: z Distance of stylus tip from tablet surface
        #: Supported on Wacom Intuos4; other device support unknown.
        #: Value will between 0 and max_val, where max_val is usually 1024.
        #: A value of 0 = tip touching surface, while
        #: max_val = tip height above surface before events stop being reported.
        self.z=None

        #: pressure: Pressure of stylus tip on tablet surface.
        self.pressure=None

        #: orient_azimuth
        self.orient_azimuth=None

        #: orient_altitude
        self.orient_altitude=None

        #: orient_twist
        self.orient_twist=None
        WintabTabletInputEvent.__init__(self, *args, **kwargs)

class WintabTabletEnterRegionEvent(WintabTabletSampleEvent):
    """
    TODO: WintabTabletEnterRegionEvent doc str
    """
    EVENT_TYPE_STRING='WINTAB_TABLET_ENTER_REGION'
    EVENT_TYPE_ID=EventConstants.WINTAB_TABLET_ENTER_REGION
    IOHUB_DATA_TABLE=WintabTabletSampleEvent.EVENT_TYPE_STRING
    def __init__(self, *args, **kwargs):
        WintabTabletSampleEvent.__init__(self, *args, **kwargs)    
        
class WintabTabletLeaveRegionEvent(WintabTabletSampleEvent):
    """
    TODO: WintabTabletLeaveRegionEvent doc str
    """
    EVENT_TYPE_STRING='WINTAB_TABLET_LEAVE_REGION'
    EVENT_TYPE_ID=EventConstants.WINTAB_TABLET_LEAVE_REGION
    IOHUB_DATA_TABLE=WintabTabletSampleEvent.EVENT_TYPE_STRING
    def __init__(self, *args, **kwargs):
        WintabTabletSampleEvent.__init__(self, *args, **kwargs)    
    