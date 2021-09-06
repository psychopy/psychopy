# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

_is_epydoc = False

# Pen digitizers /tablets that support Wintab API
from .. import Device, Computer
from ...constants import EventConstants, DeviceConstants
from ...errors import print2err, printExceptionDetailsToStdErr
import numpy as N
import copy

from psychopy import platform_specific
_sendStayAwake = platform_specific.sendStayAwake

class SimulatedWinTabPacket:
    _next_pkt_id = 1
    def __init__(self, time, x, y, press, buttons=0):
        self.pkTime=time*1000.0
        self.pkStatus=0
        self.pkSerialNumber=self.getNextID()
        self.pkButtons=buttons
        self.pkX = x                 
        self.pkY = y                 
        self.pkZ = 0                 
        self.pkNormalPressure=press          #('pressure',N.uint32),
        
        class Orientation:
            def __init__(self):
                self.orAzimuth=0         #('orient_azimuth',N.int32),
                self.orAltitude=0        #('orient_altitude;',N.int32),
                self.orTwist=0           #('orient_twist',N.int32),
                
        self.pkOrientation=Orientation()
        self.pkOrientation.orAzimuth=0         #('orient_azimuth',N.int32),
        self.pkOrientation.orAltitude=0        #('orient_altitude;',N.int32),
        self.pkOrientation.orTwist=0           #('orient_twist',N.int32),
    
    @classmethod    
    def getNextID(cls):
        v = cls._next_pkt_id
        cls._next_pkt_id+=1
        return v
    
class Wintab(Device):
    """The Wintab class docstr TBC."""
    EVENT_CLASS_NAMES = ['WintabSampleEvent',
                         'WintabEnterRegionEvent',
                         'WintabLeaveRegionEvent']

    DEVICE_TYPE_ID = DeviceConstants.WINTAB
    DEVICE_TYPE_STRING = 'WINTAB'

    __slots__ = ['_wtablets',
                 '_wtab_shadow_windows',
                 '_wtab_canvases',
                 '_last_sample',
                 '_first_hw_and_hub_times',
                 '_mouse_sim',
                 '_ioMouse',
                 '_simulated_wintab_events',
                 '_last_simulated_evt',
                 '_mouse_leave_region_timeout'
                 ]

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs['dconfig'])
        self._wtablets = []
        self._wtab_shadow_windows = []
        self._wtab_canvases = []
        
        self._ioMouse = self._last_simulated_evt = None
        self._mouse_sim = self.getConfiguration().get('mouse_simulation').get('enable')
        self._mouse_leave_region_timeout = self.getConfiguration().get('mouse_simulation').get('leave_region_timeout')
        self._simulated_wintab_events = []
        if self._mouse_sim:        
            self._registerMouseMonitor()
            self._setHardwareInterfaceStatus(True)
        else:
            self._init_wintab()

        # Following are used for sample status tracking
        self._last_sample = None
        self._first_hw_and_hub_times = None

    def _init_wintab(self):

        if Computer.platform == 'win32' and Computer.is_iohub_process:
            try:
                from .win32 import get_tablets
            except Exception:
                self._setHardwareInterfaceStatus(
                    False, u"Error: ioHub Wintab Device "
                    u"requires wintab32.dll to be "
                    u"installed.")

                def get_tablets():
                    return []

        else:
            def get_tablets():
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
        self._wtab_shadow_windows[0].switch_to()
        self._wtab_shadow_windows[0].set_mouse_visible(False)

        from pyglet import app
        app.windows.remove(self._wtab_shadow_windows[0])

        try:
            self._wtab_canvases.append(
                self._wtablets[index].open(self._wtab_shadow_windows[0], self))
        except Exception as e:
            self._setHardwareInterfaceStatus(False,
                                             u"Error: Unable to create"
                                             u"WintabCanvas for device."
                                             u"Exception: {}".
                                             format(e))
            return False

        self._setHardwareInterfaceStatus(True)
        return True

    def getHardwareConfig(self, index=0):
        if self._ioMouse is None:
            hw_model_info = self._wtablets[index].hw_model_info
            return {'Context': self._wtab_canvases[index].getContextInfo(),
                    'Axis': self._wtablets[index].hw_axis_info,
                    'ModelInfo': hw_model_info
                    }

        swidth, sheight = self._display_device.getRuntimeInfo().get('pixel_resolution',[None, None])

        # running in mouse sim mode, so create hw config
        axis_info = {'orient_altitude': {'min': 0, 'max': 0,  'adjust': 0.0, 'factor': 0.0, 'units': 0,
                                         'resolution': 0},
                     'orient_azimuth': {'min': 0, 'max': 0, 'factor': 0.0, 'units': 0, 'resolution': 0}, 
                     'pressure': {'min': 0, 'max': 1, 'units': 0, 'resolution': 0}, 
                     'orient_twist': {'min': 0, 'max': 0, 'units': 0, 'resolution': 0}, 
                     'y': {'min': 0, 'max': sheight, 'units': 0, 'resolution': 0}, 
                     'x': {'min': 0, 'max': swidth, 'units': 0, 'resolution': 0}, 
                     'z': {'min': 0, 'max': 0, 'units': 0, 'resolution': 0}}
        context =  {'lcPktMode': 0, 'lcMoveMask': 0, 'lcLocks': 0, 'lcOptions': 0, 'lcInExtX': 0, 'lcSysOrgY': 0,
                    'lcSysOrgX': -0, 'lcPktRate': 0, 'lcBtnDnMask': 0, 'lcSysSensY': 0, 'lcSysSensX': 0,
                    'lcBtnUpMask': 0, 'lcSensY': 0, 'lcSensX': 0, 'lcSensZ': 0, 'lcInOrgX': 0, 'lcInOrgY': 0,
                    'lcInOrgZ': 0, 'lcOutExtX': 0, 'lcOutOrgX': 0, 'lcSysMode': 0, 'lcPktData': 0, 'lcOutOrgZ': 0,
                    'lcOutExtZ': 0, 'lcOutExtY': 0, 'lcOutOrgY': 0, 'lcInExtY': 0, 'lcStatus': 0, 'lcInExtZ': 0,
                    'lcName': '', 'lcDevice': 0, 'lcSysExtX': 0, 'lcMsgBase': 0, 'lcSysExtY': 0}
        model_info =  {'type': 0, 'handle': 0, 'name': 'Mouse Simulation Mode', 'id': ''}
                    
        return {"Context":context,
                 "Axis":axis_info,
                 "ModelInfo":model_info
                }

    def enableEventReporting(self, enabled=True):
        for wtc in self._wtab_canvases:
            wtc.enable(enabled)

        _sendStayAwake()
        
        if self.isReportingEvents() != enabled:
            self._simulated_wintab_events = []
            self._last_sample = None
            self._first_hw_and_hub_times = None
            self._last_simulated_evt = None

        return Device.enableEventReporting(self, enabled)

    def _addSimulatedWintabEvent(self,packet):            
        w, h = self._display_device.getRuntimeInfo().get('pixel_resolution')
        w = w/2
        h=h/2
        cevt = [EventConstants.WINTAB_SAMPLE,
                packet.pkTime/1000.0,
                packet.pkStatus,
                packet.pkSerialNumber,
                packet.pkButtons,
                packet.pkX+w,                 #('x',N.int32),
                packet.pkY+h,                 #('y',N.int32),
                packet.pkZ,                 #('z',N.int32),
                packet.pkNormalPressure,          #('pressure',N.uint32),
                packet.pkOrientation.orAzimuth,         #('orient_azimuth',N.int32),
                packet.pkOrientation.orAltitude,        #('orient_altitude;',N.int32),
                packet.pkOrientation.orTwist,           #('orient_twist',N.int32),
                0          #('status', N.uint8)
                ]                
        self._simulated_wintab_events.append(cevt)

    def _injectEventsIfNeeded(self, events):
        """
        """
        if len(events):
            if self._last_simulated_evt is None:
                events.insert(0, [EventConstants.WINTAB_ENTER_REGION,
                              0,
                              0,
                              0,
                              0,
                              0,                 #('x',N.int32),
                              0,                 #('y',N.int32),
                              0,                 #('z',N.int32),
                              0,          #('pressure',N.uint32),
                              0,         #('orient_azimuth',N.int32),
                              0,        #('orient_altitude;',N.int32),
                              0,           #('orient_twist',N.int32),
                              0])
            self._last_simulated_evt = events[-1]
            
        elif self._last_simulated_evt:
            epress = self._last_simulated_evt[8]            
            if not epress:
                ctime = Computer.getTime()
                etime = self._last_simulated_evt[1]  
                if ctime-etime > self._mouse_leave_region_timeout:
                    events.append([EventConstants.WINTAB_LEAVE_REGION,
                                        0,
                                        0,
                                        0,
                                        0,
                                        0,                 #('x',N.int32),
                                        0,                 #('y',N.int32),
                                        0,                 #('z',N.int32),
                                        0,          #('pressure',N.uint32),
                                        0,         #('orient_azimuth',N.int32),
                                        0,        #('orient_altitude;',N.int32),
                                        0,           #('orient_twist',N.int32),
                                        0])
                    self._last_simulated_evt = None
        return events
    
    def _poll(self):
        try:
            for swin in self._wtab_shadow_windows:
                swin.switch_to()
                swin.dispatch_events()
            logged_time = Computer.getTime()

            if not self.isReportingEvents():
                self._last_poll_time = logged_time
                self._simulated_wintab_events = []
                for wtc in self._wtab_canvases:
                    del wtc._iohub_events[:]
                return False

            confidence_interval = logged_time - self._last_poll_time
            # Using 0 delay for now as it is unknown.
            delay = 0.0

            wintab_events = []
            if self._ioMouse:
                wintab_events = self._simulated_wintab_events
                wintab_events = self._injectEventsIfNeeded(wintab_events)
                self._simulated_wintab_events = []
            else: 
                for wtc in self._wtab_canvases:
                    wintab_events.extend(copy.deepcopy(wtc._iohub_events))
                    del wtc._iohub_events[:]


            for wte in wintab_events:
                if wte and wte[0] != EventConstants.WINTAB_SAMPLE:
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
                        status += WintabSampleEvent.STATES[
                            'FIRST_ENTER']
                        if cur_press_state > 0:
                            status += WintabSampleEvent.STATES[
                                'FIRST_PRESS']
                            status += WintabSampleEvent.STATES[
                                'PRESSED']
                        else:
                            status += WintabSampleEvent.STATES[
                                'FIRST_HOVER']
                            status += WintabSampleEvent.STATES[
                                'HOVERING']
                    else:
                        prev_press_state = self._last_sample[8]
                        if cur_press_state > 0:
                            status += WintabSampleEvent.STATES[
                                'PRESSED']
                        else:
                            status += WintabSampleEvent.STATES[
                                'HOVERING']

                        if cur_press_state > 0 and prev_press_state == 0:
                            status += WintabSampleEvent.STATES[
                                'FIRST_PRESS']
                        elif cur_press_state == 0 and prev_press_state > 0:
                            status += WintabSampleEvent.STATES[
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
            print2err('ERROR in WintabDevice._poll: ', e)
            printExceptionDetailsToStdErr()

    def _getIOHubEventObject(self, native_event_data):
        '''

        :param native_event_data:
        :return:
        '''
        logged_time, delay, confidence_interval, wt_event = native_event_data
        evt_type = wt_event[0]
        device_time = wt_event[1]
        #evt_status = wt_event[2]

        # TODO: Correct for polling interval / CI when calculating iohub_time
        iohub_time = logged_time
        if self._first_hw_and_hub_times:
            hwtime, iotime = self._first_hw_and_hub_times
            iohub_time = iotime + (wt_event[1] - hwtime)

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
        if self._ioMouse:
            self._unregisterMouseMonitor()
            self._ioMouse=None
            self._last_simulated_evt=None
        Device._close(self)

    def _registerMouseMonitor(self):
        self._ioMouse=mouseDevice=None
        self._last_simulated_evt=None
        if self._iohub_server:
            for dev in self._iohub_server.devices:
                if dev.__class__.__name__ == 'Mouse':
                    mouseDevice=dev

        if mouseDevice:
            eventIDs=[EventConstants.MOUSE_BUTTON_PRESS,
                      EventConstants.MOUSE_BUTTON_RELEASE,
                      EventConstants.MOUSE_MOVE,
                      EventConstants.MOUSE_DRAG                      
                      ]
            self._ioMouse=mouseDevice
            self._ioMouse._addEventListener(self,eventIDs)
        else:
            print2err("Warning: elCG could not connect to Mouse device for events.")

    def _unregisterMouseMonitor(self):
        if self._ioMouse:
            self._ioMouse._removeEventListener(self)

    def _handleEvent(self, event):
        """
        """
        event_type_index = DeviceEvent.EVENT_TYPE_ID_INDEX
        tix = DeviceEvent.EVENT_HUB_TIME_INDEX
        bix = 14
        xix = 15
        yix = 16
        if event[event_type_index] == EventConstants.MOUSE_BUTTON_PRESS:
            if event[-10]==1:
                self._addSimulatedWintabEvent(SimulatedWinTabPacket(time=event[tix],
                                                                x=event[xix],
                                                                y=event[yix],
                                                                press=1.0,
                                                                buttons=event[bix]))                                                                
        elif event[event_type_index] == EventConstants.MOUSE_BUTTON_RELEASE:
            if event[-10]==1:
                self._addSimulatedWintabEvent(SimulatedWinTabPacket(time=event[tix],
                                                                x=event[xix],
                                                                y=event[yix],
                                                                press=0.0,
                                                                buttons=event[bix]))
        elif event[event_type_index] == EventConstants.MOUSE_MOVE:
            self._addSimulatedWintabEvent(SimulatedWinTabPacket(time=event[tix],
                                                                x=event[xix],
                                                                y=event[yix],
                                                                press=0.0,
                                                                buttons=event[bix]))
        elif event[event_type_index] == EventConstants.MOUSE_DRAG:
            if event[-10]==1 or event[bix]==1:
                self._addSimulatedWintabEvent(SimulatedWinTabPacket(time=event[tix],
                                                                    x=event[xix],
                                                                    y=event[yix],
                                                                    press=1.0,
                                                                    buttons=event[bix]))
        else:
            Device._handleEvent(self, event)

############# Wintab Event Classes ####################

from .. import DeviceEvent


class WintabInputEvent(DeviceEvent):
    """The WintabInputEvent is an abstract class that ......."""
    PARENT_DEVICE = Wintab
    _newDataTypes = []

    __slots__ = [e[0] for e in _newDataTypes]

    def __init__(self, *args, **kwargs):
        DeviceEvent.__init__(self, *args, **kwargs)


class WintabSampleEvent(WintabInputEvent):
    """WintabSampleEvent's occur when....."""
    EVENT_TYPE_STRING = 'WINTAB_SAMPLE'
    EVENT_TYPE_ID = EventConstants.WINTAB_SAMPLE
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
	
    tstates = dict()
    for k, v in STATES.items():
        tstates[v] = k
    for k, v in tstates.items():
        STATES[k] = v

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
        WintabInputEvent.__init__(self, *args, **kwargs)


class WintabEnterRegionEvent(WintabSampleEvent):
    """
    TODO: WintabEnterRegionEvent doc str
    """
    EVENT_TYPE_STRING = 'WINTAB_ENTER_REGION'
    EVENT_TYPE_ID = EventConstants.WINTAB_ENTER_REGION
    IOHUB_DATA_TABLE = WintabSampleEvent.EVENT_TYPE_STRING

    def __init__(self, *args, **kwargs):
        WintabSampleEvent.__init__(self, *args, **kwargs)


class WintabLeaveRegionEvent(WintabSampleEvent):
    """
    TODO: WintabLeaveRegionEvent doc str
    """
    EVENT_TYPE_STRING = 'WINTAB_LEAVE_REGION'
    EVENT_TYPE_ID = EventConstants.WINTAB_LEAVE_REGION
    IOHUB_DATA_TABLE = WintabSampleEvent.EVENT_TYPE_STRING

    def __init__(self, *args, **kwargs):
        WintabSampleEvent.__init__(self, *args, **kwargs)
