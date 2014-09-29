# -*- coding: utf-8 -*-
"""
ioHub Python Module
.. file: ioHub/devices/xinput/__init__.py

fileauthor: Sol Simpson <sol@isolver-software.com>

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> +
contributors, please see credits section of documentation.
"""

import xinput
import numpy as N
import gevent
from .. import Computer, Device, DeviceEvent, ioDeviceError
from ...constants import XInputGamePadConstants, DeviceConstants,EventConstants


def enableXInput():
    # Enables xinput on the system
    if not hasattr(xinput,'xinput_dll'):
        xinput.loadDLL()
    xinput._xinput_dll.XInputEnable(True)

def disableXInput():
    # Disables xinput on the system
    if not hasattr(xinput,'xinput_dll'):
        xinput.loadDLL()
    xinput._xinput_dll.XInputEnable(False)

class XInputDevice(Device):
    _ASSIGNED_USER_IDS=[]
    _USER2DEVICE=dict()

    _newDataTypes=[]

    DEVICE_TYPE_ID=DeviceConstants.XINPUT
    DEVICE_LABEL = 'XINPUT'
    __slots__=[e[0] for e in _newDataTypes]+['_device_state',
                                            '_device_state_buffer',
                                            '_state_time','_time_ci']
    def __init__(self, *args,**kwargs):
        Device.__init__(self,*args,**kwargs['dconfig'])

        if not hasattr(xinput,'xinput_dll'):
            xinput.loadDLL()


class Gamepad(XInputDevice):
    """
    The ioHub xinput.Gamepad Device supports monitoring events from a Windows XInput
    complient device. Due to the nature of the XInput interface, these events can
    be provided regardless of whether a PsychoPy Window is currently created or has focus.

    The ioHub XInput interface supports the full XInput 1.3 specification. XInput
    events can be read, the capabilities of the connected bevice can be queried, as
    well as the current battery level for wireless devices. On device hardware that
    supports vibration / rubble feedback support, this can be controlled via the ioHub
    xinput.Gamepad.setRumble(lowFrequencyValue,highFrequencyValue,duration) method.

    XInput compatible gamepad's which have been tested are:

        #. XBOX 360 for Windows Wireless controller.+
        #. Logitech F710 Wireless controller.+
        #. Logitech F310 Wired controller.

    **+** These controllers support the rumble (vibration) setting feature supported by the ioHub XInput Interface.
    """
    DEVICE_TYPE_ID=DeviceConstants.GAMEPAD
    DEVICE_LABEL = 'GAMEPAD'
    EVENT_CLASS_NAMES=['GamepadStateChangeEvent',]

    __slots__=['_capabilities','_battery_information','_keystroke','_rumble','_last_read_capabilities_dict']
    def __init__(self, *args,**kwargs):
        XInputDevice.__init__(self,*args,**kwargs)

        # check that the specified device_number (i.e. user_id) for the device is available and valid.

        if self.device_number in self._ASSIGNED_USER_IDS:
            raise ioDeviceError(self,"XInputDevice with device_number %d already in use."%(self.device_number))

        if len(self._ASSIGNED_USER_IDS) == xinput.XUSER_MAX_COUNT:
            raise ioDeviceError(self,"XInputDevice max user count reached: %d."%(xinput.XUSER_MAX_COUNT))

        if self.device_number >= 0 and self.device_number < xinput.XUSER_MAX_COUNT:
            connectedOK=_initializeGamePad(self,self.device_number)
            if not connectedOK:
                raise ioDeviceError(self,"XInputDevice with device_number %d is not connected."%(self.device_number))
        else:
            self.device_number=-1
            for i in [i for i in range(xinput.XUSER_MAX_COUNT) if i not in self._ASSIGNED_USER_IDS]:
                connectedOK=_initializeGamePad(self,i)
                if connectedOK:
                    break
                else:
                    raise ioDeviceError(self,"No XInputDevice is Available for Use. Please check Connections.")

        self._last_read_capabilities_dict=None

        self._rumble=xinput.XINPUT_VIBRATION(0,0)
        self._battery_information=xinput.XINPUT_BATTERY_INFORMATION(0,0)
        self._capabilities=xinput.XINPUT_CAPABILITIES(0,0,0,
                                        xinput.XINPUT_GAMEPAD(0,0,0,0,0,0,0),
                                        xinput.XINPUT_VIBRATION(0,0))
        self.setRumble(0,0)

        if XInputGamePadConstants._initialized is False:
            XInputGamePadConstants.initialize()

    def getButtons(self,gamepad_state=None):
        """
        Returns a dictionary providing the button states from the last
        GamepadStateChangeEvent read. The dictionary contains the following key: value pairs:

        * time : float. The sec.msecusec time when the button states being reported were read.
        * confidence_interval : float. The sec.msecusec difference between the device poll that contained the event data being used, and the previous device poll time. Therefore, it is possible that the device event time reported could have been between the time reported and reported time - confidence_interval.
        * button_name : button_state. These key: value pair will be included multiple times in the dict; where each key is a button label constant as defined in XInputGamePadConstants, and the value is a bool indicating if the button is Pressed (True) or in a released (False) state.


        Args:
            None

        Returns:
            dict: Button state information dict as described in the method doc.
        """
        if gamepad_state is None:
            gamepad_state=self._device_state.Gamepad

        buttonStates=self._getButtonNameList(gamepad_state.wButtons)
        buttonStates['time']=self._state_time,
        buttonStates['confidence_interval']=self._time_ci
        return buttonStates

    def getTriggers(self,gamepad_state=None):
        """
        Returns a dictionary providing the left and right gamepad trigger states from the last
        GamepadStateChangeEvent read. The dictionary contains the following key: value pairs:

        * time : float. The sec.msecusec time when the trigger states being reported were read.
        * confidence_interval : float. The sec.msecusec difference between the device poll that contained the event data being used, and the previous device poll time. Therefore, it is possible that the device event time reported could have been between the time reported and reported time - confidence_interval.
        * left_trigger: float. The state of the left trigger, normalized between 0.0 and 1.0 . 0.0 indicates the trigger is not pressed in at all; 1.0 indicates the trigger has been fully pulled in. The value has 8 bit resolution.
        * right_trigger: float. The state of the right trigger, normalized between 0.0 and 1.0 . 0.0 indicates the trigger is not pressed in at all; 1.0 indicates the trigger has been fully pulled in. The value has 8 bit resolution.

        Args:
            None

        Returns:
            dict: Trigger state information dict as described in the method doc.
        """
        if gamepad_state is None:
            gamepad_state=self._device_state.Gamepad
        return dict(time=self._state_time, confidence_interval=self._time_ci,left_trigger=gamepad_state.bLeftTrigger/255.0,right_trigger=gamepad_state.bRightTrigger/255.0)

    def getPressedButtons(self):
        return self._device_state.Gamepad.wButtons

    def getPressedButtonList(self):
        """
        Returns a list of button names, as defined in XInputGamePadConstants, that are currently pressed.

        Args:
            None

        Returns:
            list: Names of buttons currently pressed.
        """
        bdict=self._getButtonNameList(self._device_state.Gamepad.wButtons)
        blist=[]
        for k,v in bdict.iteritems():
            if v:
                blist.append(k)
        return blist

    def getThumbSticks(self,gamepad_state=None):
        """
        Returns a dictionary providing the state of the left and right thumbsticks on the gamepad.
        based on data from last GamepadStateChangeEvent read.
        The dictionary contains the following key:value pairs:

        * time : float. The sec.msecusec time when the thumbstick states being reported were read.
        * confidence_interval : float. The sec.msecusec difference between the device poll that contained the event data being used, and the previous device poll time. Therefore, it is possible that the device event time reported could have been between the time reported and reported time - confidence_interval.
        * left_stick: (x, y, magnitude). The state of the left thumbstick as a tuple of three float values, each with 12 bit resolution. x and y can range between -1.0 and 1.0, representing the position each dimention of the current thumbstick position (- values are leftward or downward, + values are rightward or upward). The magnitude can be between 0.0 and 1.0, representing the amount the thumbstick has been moved in the combined 2D movement space. 0.0 equals no movement, 1.0 equals the thumbstick being pushed fully to the edge of motion.
        * right_stick: (x, y, magnitude). The state of the right thumbstick as a tuple of three float values, each with 12 bit resolution. x and y can range between -1.0 and 1.0,  representing the position each dimention of the current thumbstick position (- values are leftward or downward, + values are rightward or upward). The magnitude can be between 0.0 and 1.0, representing the amount the thumbstick has been moved in the combined 2D movement space. 0.0 equals no movement, 1.0 equals the thumbstick being pushed fully to the edge of motion.

        Args:
            None

        Returns:
            dict: Thumbstick state information dict as described in the method doc.
        """
        if gamepad_state is None:
            gamepad_state=self._device_state.Gamepad
        leftStick=xinput.normalizeThumbStickValues(gamepad_state.sThumbLX,gamepad_state.sThumbLY,xinput.XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE)
        rightStick=xinput.normalizeThumbStickValues(gamepad_state.sThumbRX,gamepad_state.sThumbRY,xinput.XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE)
        return dict(time=self._state_time, confidence_interval=self._time_ci,left_stick=leftStick,right_stick=rightStick)

    def getRumbleState(self):
        """
        Returns the current amount the low and high frequency rumble motors are
        engaged as a (low,high) tuple, returned as the % of possible intensitity for each motor.
        The resolution of the value for each motor is 16 bits.

        Args:
            None

        Returns:
            tuple: (low_frequency, high_frequency) rumble motor stats on devices that support vibration / rumble settings. Each value is returned as a percentage between 0.0 and 100.0.
        """
        NormalizedLowFrequencyValue= 100.0*(self._rumble.wLeftMotorSpeed/65535.0)
        NormalizedHighFrequencyValue= 100.0*(self._rumble.wRightMotorSpeed/65535.0)
        return NormalizedLowFrequencyValue, NormalizedHighFrequencyValue

    def setRumble(self,lowFrequencyValue=0,highFrequencyValue=0,duration=1.0):
        """
        Sets the xinput.Gamepad device's vibration / rumble feedback state for each of the
        low and high requency vibration motors. This ethod is only supported
        on devices that physically support rumble setting.

        By using different low and high drequence settings and duraations, different
        vibration feedback effects can be achieved. This can be further enhanced by
        adjusting each motors output state in steps over a period of time.

        The percentage provided for each vibration motor indicates how string the
        motor should be enabled relative to the full range of vitration strengths supported.

        This method runs asyncronously to the PsychoPy experiment script, so
        regardless of the duration set, the method returns when the vibration
        command has been issued to the device by the ioHub Process.

        If the experiment script sets the rumble state again before the last rumble state's
        duration is complete, then the new setRumble updates the rumble state and the
        previous state is ended prior to the full duration specified by the earlier command.

        Args:
            lowFrequencyValue (float): Percentage that the low frequency rumble motor should be set to within it's possible output range. 0.0 is Off. 100.0 is full power. The underlying rumble API uses 16 bit resolution values for setting rumble state.

            highFrequencyValue (float): Percentage that the high frequency rumble motor should be set to within it's possible output range. 0.0 is Off. 100.0 is full power. The underlying rumble API uses 16 bit resolution values for setting rumble state.

            duration (float): sec.msec duration that the rumble settings should be acctive for. When the duration had passed, the rumble states are set to 0. REgardless of the duration value, the method is run asyncronously and returns to the PsychoPy script as soon as the sate changes have been issues to the native device.

        Returns:
            (float,float): (command_return_time, command_call_duration), where command_return_time is the sec.msec time that the call to the native device to update vibration setting returned to the ioHub process, and command_call_duration is the sec.msec time taken for the native device call to return to the ioHub process.
        """
        DeNormalizedLowFrequencyValue= int(65535.0*(lowFrequencyValue/100.0))
        DeNormalizedHighFrequencyValue= int(65535.0*(highFrequencyValue/100.0))

        if DeNormalizedLowFrequencyValue < 0:
            self._rumble.wLeftMotorSpeed=0
        elif DeNormalizedLowFrequencyValue > 65535:
            self._rumble.wLeftMotorSpeed=65535
        else:
            self._rumble.wLeftMotorSpeed=DeNormalizedLowFrequencyValue

        if DeNormalizedHighFrequencyValue < 0:
            self._rumble.wRightMotorSpeed=0
        elif DeNormalizedHighFrequencyValue > 65535:
            self._rumble.wRightMotorSpeed=65535
        else:
            self._rumble.wRightMotorSpeed=DeNormalizedHighFrequencyValue

        t1=Computer.getTime()
        xinput._xinput_dll.XInputSetState(self.device_number, xinput.pointer(self._rumble))
        t2=Computer.getTime()

        gevent.spawn(self._delayedRumble,delay=duration)
        return t2, t2-t1

    def updateBatteryInformation(self):
        """
        Informs the xinput gamepad to read the battery status information
        from the native device and return the latest battery status information.

        Given the possible uses of the returned information, it is unlikely that
        the status needs to be read from the native device every time the calling
        program needs battery status. Therefore using the getLastReadBatteryInfo()
        can be called instead as needed.

        Args: None

        Returns:
            tuple: (battery_level, battery_type) where battery_level is a string constant indicating if the device's battery is at a low, medium, or high charge level. battery_type indicates if the gamepad actually uses a battery, or if it is a wired device and is powered via USB. In the latter case, ['BATTERY_LEVEL_FULL', 'BATTERY_TYPE_WIRED'] is always returned.
        """
        xinput._xinput_dll.XInputGetBatteryInformation(
            self.device_number, # Index of the gamer associated with the device
            xinput.BATTERY_DEVTYPE_GAMEPAD,# Which device on this user index
            xinput.pointer(self._battery_information)) # Contains the level
                                                       # and types of batteries

        bl=XInputGamePadConstants._batteryLevels.getName(self._battery_information.BatteryLevel)
        bt=XInputGamePadConstants._batteryTypes.getName(self._battery_information.BatteryType)
        return bl,bt

    def getLastReadBatteryInfo(self):
        """
        Return the last read battery status information from the xinput.Gamepad device.
        This method does not query the native device for the most recent battery
        status data, and instead returns the values read the last time the native
        device was actually queried.

        To have the battery status information updated and return this latest status data, use
        updateBatteryInformation()

        Args: None

        Returns:
            tuple: (battery_level, battery_type) where battery_level is a string constant indicating if the device's battery was at a low, medium, or high charge level the last time the device was queried for this information. battery_type indicates if the gamepad actually uses a battery, or if it is a wired device and is powered via USB. In the latter case,  ['BATTERY_LEVEL_FULL', 'BATTERY_TYPE_WIRED'] is always returned.
        """
        bl=XInputGamePadConstants._batteryLevels.getName(self._battery_information.BatteryLevel)
        bt=XInputGamePadConstants._batteryTypes.getName(self._battery_information.BatteryType)
        return bl,bt

    def updateCapabilitiesInformation(self):
        """
        Informs the xinput gamepad to read the capability information available
        from the native device and return this data in a dictionary format.

        Given the possible uses of the returned information, it is unlikely that
        the  capability information needs to be read from the native device
        every time the calling program needs to know what capabilities the device
        supports. Therefore using the getLastReadCapabilitiesInfo() method
        will likely be a better choice to use during the runtime of your
        program. An even better option would be to read the device capabilities
        from the ioHub Process once, cache them in your script as local variables,
        and use the local variables you created during the rest of the experiment. ;)

        The return value is a dict, keys represent different reported capability types,
        and the associated value is what the current deive supports for the given capability:

            * type : either XBOX360_GAMEPAD or OTHER_XINPUT_GAMEPAD
            * subtype : either XINPUT_GAMEPAD or XINPUT_UNKNOWN_SUBTYPE
            * supported_buttons : list of the supported buttons in string form, as specified in the XInputGamePadConstants class.
            * left_trigger_support : True == supported, False otherwise
            * right_trigger_support :  True == supported, False otherwise
            * low_frequency_vibration_support :  True == supported, False otherwise
            * high_frequency_vibration_support :  True == supported, False otherwise

        Args: None

        Returns:
            tuple: The device capabilities in dict format.
        """
        xinput._xinput_dll.XInputGetCapabilities(
            self.device_number,
            xinput.XINPUT_FLAG_GAMEPAD,
            xinput.pointer(self._capabilities))

        capabilities_dict=dict()

        capabilities_dict['type']=XInputGamePadConstants._capabilities.getName(self._capabilities.Type)


        s=self._capabilities.SubType
        if s == xinput.XINPUT_DEVSUBTYPE_GAMEPAD:
            capabilities_dict['subtype']=XInputGamePadConstants._capabilities.getName(XInputGamePadConstants._capabilities.XINPUT_GAMEPAD)
        else:
            capabilities_dict['subtype']=XInputGamePadConstants._capabilities.getName(XInputGamePadConstants._capabilities.XINPUT_UNKNOWN_SUBTYPE)

        f=self._capabilities.Flags

        g=self._capabilities.Gamepad
        b=g.wButtons
        capabilities_dict['supported_buttons']=[k for k,v in self._getButtonNameList(b).iteritems() if v is True]


        capabilities_dict['left_trigger_support']=g.bLeftTrigger==255
        capabilities_dict['right_trigger_support']=g.bRightTrigger==255

        capabilities_dict['left_thumbstick_x_support']=g.sThumbLX==-64
        capabilities_dict['left_thumbstick_y_support']=g.sThumbLY==-64
        capabilities_dict['right_thumbstick_x_support']=g.sThumbRX==-64
        capabilities_dict['right_thumbstick_x_support']=g.sThumbRY==-64

        v=self._capabilities.Vibration
        capabilities_dict['low_frequency_vibration_support']=v.wLeftMotorSpeed==255
        capabilities_dict['high_frequency_vibration_support']=v.wRightMotorSpeed==255

        self._last_read_capabilities_dict=capabilities_dict

        return self._last_read_capabilities_dict

    def getLastReadCapabilitiesInfo(self):
        """
        Return the last read capability information for the xinput.Gamepad device connected.

        This method does not query the native device for this data, and instead
        returns the data read the last time the native device was actually queried,
        using updateCapabilitiesInformation().

        Given the possible uses of the returned information, it is unlikely that
        the capability information needs to be read from the native device
        every time the calling program needs to know what capabilities the device
        supports. Therefore using this method conpared to updateCapabilitiesInformation()
        will likely be a better choice during the runtime of your program.

        An even better option would be to read the device capabilities
        from the ioHub Process once, cache them in your script as local variables,
        and use the local variables you created during the rest of the experiment. ;)

        The return value is a dict, keys represent different reported capability types,
        and the associated value is what the current deive supports for the given capability:

            * type : either XBOX360_GAMEPAD or OTHER_XINPUT_GAMEPAD
            * subtype : either XINPUT_GAMEPAD or XINPUT_UNKNOWN_SUBTYPE
            * supported_buttons : list of the supported buttons in string form, as specified in the XInputGamePadConstants class.
            * left_trigger_support : True == supported, False otherwise
            * right_trigger_support :  True == supported, False otherwise
            * low_frequency_vibration_support :  True == supported, False otherwise
            * high_frequency_vibration_support :  True == supported, False otherwise

        Args: None

        Returns:
            tuple: The device capabilities in dict format.
        """

        if self._last_read_capabilities_dict is None:
            updateCapabilitiesInformation()

        return self._last_read_capabilities_dict

    def _poll(self):
        t=Computer.getTime()
        result = xinput._xinput_dll.XInputGetState(self.device_number, xinput.pointer(self._device_state_buffer))
        t2=Computer.getTime()


        if result == xinput.ERROR_SUCCESS:
            changed = self._checkForStateChange()
            if len(changed) > 0:
                temp=self._device_state
                self._device_state = self._device_state_buffer
                self._state_time=t2
                self._time_ci=t2-t
                self._device_state_buffer=temp

                delay=(t-self._last_poll_time)/2.0 # assuming normal distribution, on average delay will be 1/2 the
                                                 # inter poll interval
                buttons=0
                if len(changed.get('Buttons',[])) > 0:
                    buttons=self._device_state.Gamepad.wButtons

                gpe= [
                    0,                                      # experiment_id filled in by ioHub
                    0,                                      # session_id filled in by ioHub
                    self.device_number,                     # device id : number 0-3 representing which controller event is from.
                    Computer._getNextEventID(),             # unique event id
                    GamepadStateChangeEvent.EVENT_TYPE_ID,  # id representation of event type
                    self._state_time,                       # device Time
                    t,                                      # logged time
                    self._state_time,                       # time (i.e. ioHub Time)
                    self._time_ci,                          # confidence Interval
                    delay,                                  # delay
                    0,
                    buttons,                                # buttons id's that were pressed at the time of the state change.
                    'B',                                    # buttons 1 char placeholder
                    changed.get('LeftThumbStick',(0.0,0.0,0.0)),   # normalized x,y, and magnitude value for left thumb stick
                    changed.get('RightThumbStick',(0.0,0.0,0.0)),  # normalized x,y, and magnitude value for right thumb stick
                    changed.get('LeftTrigger',0.0),      # normalized degree pressed for left trigger button
                    changed.get('RightTrigger',0.0)     # normalized degree pressed for left trigger button
                    ]
                self._addNativeEventToBuffer(gpe)
        else:
            # TODO: device has disconnected, create a special event.....
            temp=self._device_state
            self._device_state = self._device_state_buffer
            self._state_time=t
            self._time_ci=t2-t
            self._device_state_buffer=temp

            delay=(t-self._last_poll_time)/2.0 # assuming normal distribution, on average delay will be 1/2 the
                                             # inter poll interval
            gpe= [
                0,                                      # experiment_id filled in by ioHub
                0,                                      # session_id filled in by ioHub
                self.device_number,                          # number 0-3 representing which controller event is from.
                Computer._getNextEventID(),             # unique event id
                GamepadDisconnectEvent.EVENT_TYPE_ID,  # id representation of event type
                self._state_time,                       # device Time
                t,                                      # logged time
                self._state_time,                       # time (i.e. ioHub Time)
                self._time_ci,                          # confidence Interval
                delay,                                  # delay
                0,                                      #filter_id 0 by default
                0,                                      # buttons id's that were pressed at the time of the state change.
                'B',                                      # buttons 1 char placeholder
                0,                                      # normalized x,y, and magnitude value for left thumb stick
                0,                                      # normalized x,y, and magnitude value for right thumb stick
                0,                                      # normalized degree pressed for left trigger button
                0                                       # normalized degree pressed for left trigger button
                ]

            self._addNativeEventToBuffer(gpe)
            self._close()

        self._last_poll_time=t
        return True

    @staticmethod
    def _getButtonNameList(wbuttons=0):
        buttonStates=dict()
        if wbuttons!=0:
            for k in XInputGamePadConstants._keys:
                if wbuttons&k == k:
                    buttonStates[XInputGamePadConstants._names[k]]=True
                else:
                    buttonStates[XInputGamePadConstants._names[k]]=False
        return buttonStates

    def _checkForStateChange(self):
        g1=self._device_state.Gamepad
        g2=self._device_state_buffer.Gamepad
        changed={}

        if g1.wButtons!=g2.wButtons:
            buttonNameList=[]
            if g2.wButtons!=0:
                for k in XInputGamePadConstants._keys:
                    if g2.wButtons&k == k:
                        buttonNameList.append(XInputGamePadConstants._names[k])
            changed['Buttons']=buttonNameList


        if g1.bLeftTrigger!=g2.bLeftTrigger:
            changed['LeftTrigger']=g2.bLeftTrigger/255.0
        if g1.bRightTrigger!=g2.bRightTrigger:
            changed['RightTrigger']=g2.bRightTrigger/255.0


        if g1.sThumbLX!=g2.sThumbLX or g1.sThumbLY!=g2.sThumbLY:
            nl1=xinput.normalizeThumbStickValues(g1.sThumbLX,g1.sThumbLY,xinput.XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE)
            nl2=xinput.normalizeThumbStickValues(g2.sThumbLX,g2.sThumbLY,xinput.XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE)
            if (nl1 != nl2):
                changed['LeftThumbStick']=nl2
        if g1.sThumbRX!=g2.sThumbRX or g1.sThumbRY!=g2.sThumbRY:
            nr1=xinput.normalizeThumbStickValues(g1.sThumbRX,g1.sThumbRY,xinput.XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE)
            nr2=xinput.normalizeThumbStickValues(g2.sThumbRX,g2.sThumbRY,xinput.XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE)
            if (nr1 != nr2):
                changed['RightThumbStick']=nr2

        return changed

    def _delayedRumble(self,lowFrequencyValue=0,highFrequencyValue=0,delay=0):
        gevent.sleep(delay)
        self._rumble.wLeftMotorSpeed=0
        self._rumble.wRightMotorSpeed=0
        xinput._xinput_dll.XInputSetState(self.device_number, xinput.pointer(self._rumble))

    def _close(self):
        self.setRumble(0,0)
        XInputDevice._ASSIGNED_USER_IDS.remove(self.device_number)
        del XInputDevice._USER2DEVICE[self.device_number]
        self.device_number=None
        self._device_state=None

    def __del__(self):
        self._close()
        self.clearEvents()


def _initializeGamePad(gamepad,device_number):
    dwResult, gamepadState, stime, ci=xinput.createXInputGamePadState(device_number)
    if dwResult == xinput.ERROR_SUCCESS:
        gamepad.device_number=device_number
        gamepad._device_state=gamepadState
        gamepad._state_time=stime
        gamepad._time_ci=ci
        XInputDevice._ASSIGNED_USER_IDS.append(device_number)
        dwResult2, gamepadState2, stime2, ci2=xinput.createXInputGamePadState(device_number)
        gamepad._device_state_buffer=gamepadState2
        XInputDevice._USER2DEVICE[device_number]=gamepad
        return True
    return False

class GamepadStateChangeEvent(DeviceEvent):
    """
    GamepadStateChangeEvent events are generated when ever any aspect of the gamepad's
    state changes (i.e. when a button event occurs, and trigger value changes,
    or a thumbstick value changes).

    The event includes fields to hold the updated information for all the possible
    state changes that can occur. Fields that have a value of 0.0 indicate no change has occurred
    for that aspect of the gamepad's fucntionality. Non zero values indicate the
    gamepad controls that have had a state change.

    Note that multiple gamepad controls can report a state change in one event.
    For example, the left thumbstick can move, the right trigger can be released a bit, and
    a button can be pressed all at the same time; in which case a GamepadStateChangeEvent
    will be returned that represents all of these changes and the time the device reported
    all of the changes as occurring simultaniously.

    Event Type ID: EventConstants.GAMEPAD_STATE_CHANGE

    Event Type String: 'GAMEPAD_STATE_CHANGE'
    """
    PARENT_DEVICE=Gamepad
    EVENT_TYPE_ID=EventConstants.GAMEPAD_STATE_CHANGE
    EVENT_TYPE_STRING='GAMEPAD_STATE_CHANGE'
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING
    _newDataTypes = [

                      ('button_ids',N.uint32),     # the buttons that were pressed at the time of the state change.
                                                  # All buttons that are pressed are & together into this field.
                                                  # Use buttons to get a list of the text representation for
                                                  # each button that was pressed in list form
                      ('buttons',N.str,1),        # placeholder for button name list when event is viewed as NamedTuple

                      # Thumbsticks are represented in normalized units between 0.0 and 1.0 for x direction, y direction
                      # and magnitude of the thumbstick. x and y are the horizontal and vertical position of the stick
                      # around the center point. Magnitude is how far from the center point the stick location is: 0.0
                      # would equal the stick being in the center position, not moved. 1.0 would indicate the stick
                      # is pushed all the way to the outer rail of the thumbstick movement circle. The resolution of
                      # each thumbstick is about 16 bits for each measure.
                      ('left_thumb_stick',N.dtype([('x',N.float32),('y',N.float32),('magnitude',N.float32)])),
                      ('right_thumb_stick',N.dtype([('x',N.float32),('y',N.float32),('magnitude',N.float32)])),

                      ('left_trigger',N.float32),   # the triggers are the two pistol finger analog buttons on the
                                                   # XInput gamepad. The value is normalized to between 0.0 (not pressed)
                                                   # and 1.0 (fully depressed). The resolution of the triggers are 8 bits.
                      ('right_trigger',N.float32)
                    ]
    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):

        #: All the buttons that were pressed at the time of the state change,
        #: represented as an unsigned int of the pressed button ID constants logically & together.
        self.button_ids=None

        #: All the buttons that were pressed at the time of the state change,
        #: represented as a list of button name string constants.
        self.buttons=None

        #: The state of the left thumbstick if it changed at the time the device event was created.
        #: Thumbstick data is represented in normalized units between
        #: -1.0 and 1.0 for x direction, y direction and between 0.0 and 1.0 for magnitude of the thumbstick.
        #: x and y are the horizontal and vertical position of the stick
        #: around the center point. Magnitude is how far from the center point
        #: the stick location is:
        #:
        #: * 0.0 equals the stick being in the center resting position.
        #: * -1.0 indicates the stick is pushed all the way to the outer rail of the thumbstick movement circle (left for x dimension, bottom for y dimension).
        #: * 1.0 indicates the stick is pushed all the way to the outer rail of the thumbstick movement circle (right for x dimension, top for y dimension).
        #:
        #: The resolution of each thumbstick is about 16 bits for each measure.
        self.left_thumb_stick=None

        #: The state of the right thumbstick if it changed at the time the device event was created.
        #: Thumbstick data is represented in normalized units between
        #: -1.0 and 1.0 for x direction, y direction and between 0.0 and 1.0 for magnitude of the thumbstick.
        #: x and y are the horizontal and vertical position of the stick
        #: around the center point. Magnitude is how far from the center point
        #: the stick location is:
        #:
        #: * 0.0 equals the stick being in the center resting position.
        #: * -1.0 indicates the stick is pushed all the way to the outer rail of the thumbstick movement circle (left for x dimension, bottom for y dimension).
        #: * 1.0 indicates the stick is pushed all the way to the outer rail of the thumbstick movement circle (right for x dimension, top for y dimension).
        #:
        #: The resolution of each thumbstick is about 16 bits for each measure.
        self.right_thumb_stick=None

        #: The state of the left trigger if it changed at the time the device event was created.
        #: A trigger is a pistol finger analog buttons on XInput gamepads.
        #: The position value is normalized to between 0.0 (not pressed)
        #: and 1.0 (fully depressed). The resolution of the trigger position is 8 bits.
        self.left_trigger=None

        #: The state of the right trigger if it changed at the time the device event was created.
        #: A trigger is a pistol finger analog buttons on XInput gamepads.
        #: The position value is normalized to between 0.0 (not pressed)
        #: and 1.0 (fully depressed). The resolution of the trigger position is 8 bits.
        self.right_trigger=None

        DeviceEvent.__init__(self,*args,**kwargs)

    @classmethod
    def createEventAsDict(cls,values):
        ed=super(DeviceEvent,cls).createEventAsDict(values)
        if ed['button_ids'] == 0:
            ed['buttons']={}
            return ed
        ed['buttons']=Gamepad._getButtonNameList(ed['button_ids'])
        return ed

    #noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls,valueList):
        if valueList[-6] == 0:
            valueList[-5]={}
            return cls.namedTupleClass(*valueList)

        valueList[-5]=Gamepad._getButtonNameList(valueList[-6])
        return cls.namedTupleClass(*valueList)

class GamepadDisconnectEvent(GamepadStateChangeEvent):
    EVENT_TYPE_ID=EventConstants.GAMEPAD_DISCONNECT
    EVENT_TYPE_STRING='.GAMEPAD_DISCONNECT'
    IOHUB_DATA_TABLE=GamepadStateChangeEvent.EVENT_TYPE_STRING
    __slots__=[]
    def __init__(self,*args,**kwargs):
        GamepadStateChangeEvent.__init__(self,*args,**kwargs)

