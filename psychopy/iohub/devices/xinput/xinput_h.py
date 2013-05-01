# -*- coding: utf-8 -*-
"""
ioHub Python Module
.. file: ioHub/devices/xinput/xinput_h.py

fileauthor: Sol Simpson <sol@isolver-software.com>

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + 
contributors, please see credits section of documentation.
"""


import ctypes,ctypes.wintypes
from ctypes.wintypes import WORD, SHORT, DWORD, WCHAR, c_ubyte


UNICODE = False
XINPUT_USE_9_1_0 = False

if XINPUT_USE_9_1_0 is False:
    XINPUT_DLL_A  = "xinput1_3"
    XINPUT_DLL_W = u"xinput1_3"
else:
    XINPUT_DLL_A = "xinput9_1_0"
    XINPUT_DLL_W = u"xinput9_1_0"

if UNICODE:
    XINPUT_DLL = XINPUT_DLL_W
else:
    XINPUT_DLL = XINPUT_DLL_A


#
# Device Type
#
XINPUT_DEVTYPE_GAMEPAD = 0x01

#
# Device SubTypes
#
#XINPUT_DEVSUBTYPE_UNKNOWN	# The controller type is unknown.
XINPUT_DEVSUBTYPE_GAMEPAD = 0x01	# Gamepad controller.
                             # Includes Left and Right Sticks, 
                             # Left and Right Triggers, Directional Pad,
                             # and all standard buttons (A, B, X, Y, 
                             # START, BACK, LB, RB, LSB, RSB).
                             
if XINPUT_USE_9_1_0 is False:
    
    XINPUT_DEVSUBTYPE_WHEEL	= 0x02 # Racing wheel controller.
                             # Left Stick X reports the wheel rotation, 
                             # Right Trigger is the acceleration pedal, 
                             # and Left Trigger is the brake pedal. 
                             # Includes Directional Pad and most standard 
                             # buttons (A, B, X, Y, START, BACK, LB, RB).
                             # LSB and RSB are optional.

    XINPUT_DEVSUBTYPE_ARCADE_STICK = 0x03	# Arcade stick controller.
                             # Includes a Digital Stick that reports as 
                             # a DPAD (up, down, left, right), and most 
                             # standard buttons (A, B, X, Y, START, BACK). 
                             # The Left and Right Triggers are implemented 
                             # as digital buttons and report either 0 or 0xFF.
                             # LB, LSB, RB, and RSB are optional.

    XINPUT_DEVSUBTYPE_FLIGHT_STICK = 0x04	# Flight stick controller.
                             # Includes a pitch and roll stick that reports 
                             # as the Left Stick, a POV Hat which reports 
                             # as the Right Stick, a rudder (handle twist 
                             # or rocker) that reports as Left Trigger, 
                             # and a throttle control as the Right Trigger. 
                             # Includes support for a primary weapon (A), 
                             # secondary weapon (B), and other standard 
                             # buttons (X, Y, START, BACK). LB, LSB, RB, 
                             # and RSB are optional.

    XINPUT_DEVSUBTYPE_DANCE_PAD = 0x05 	# Dance pad controller.
                             # Includes the Directional Pad and 
                             # standard buttons (A, B, X, Y) on the pad, 
                             # plus BACK and START.

    XINPUT_DEVSUBTYPE_GUITAR = 0x06    # Guitar controller.
                             # The strum bar maps to DPAD (up and down), 
                             # and the frets are assigned to A (green), 
                             # B (red), Y (yellow), X (blue), and LB (orange).
                             # Right Stick Y is associated with a vertical 
                             # orientation sensor; Right Stick X is the 
                             # whammy bar. Includes support for BACK, START, 
                             # DPAD (left, right). Left Trigger 
                             # (pickup selector), Right Trigger, RB, LSB 
                             # (fret modifier), RSB are optional.
                             
#XINPUT_DEVSUBTYPE_GUITAR_BASS # Guitar Bass is identical to Guitar, with the 
                             # distinct subtype to simplify setup.
                             
#XINPUT_DEVSUBTYPE_GUITAR_ALTERNATE # Guitar Alt supports a larger range of 
                             # movement for the vertical orientation sensor.

    XINPUT_DEVSUBTYPE_DRUM_KIT	= 0.08# Drum controller.
                             # The drum pads are assigned to buttons: 
                             # A for green (Floor Tom), B for red (Snare Drum), 
                             # X for blue (Low Tom), Y for yellow (High Tom),
                             # and LB for the pedal (Bass Drum). 
                             # Includes Directional-Pad, BACK, and START. 
                             # RB, LSB, and RSB are optional.

#XINPUT_DEVSUBTYPE_ARCADE_PAD	 # Arcade pad controller.
                             # Includes Directional Pad and most standard 
                             # buttons (A, B, X, Y, START, BACK, LB, RB). 
                             # The Left and Right Triggers are implemented 
                             # as digital buttons and report either 0 or 0xFF.
                             # Left Stick, Right Stick, LSB, and RSB are optional.


# Note:
# Older XUSB Windows drivers report incomplete capabilities information, 
# particularly for wireless devices. The latest XUSB Windows driver provides 
# full support for wired and wireless devices, and more complete and accurate 
# capabilties flags.
XINPUT_CAPS_VOICE_SUPPORTED = 0x0004 # Device has an integrated voice device.

#XINPUT_CAPS_FFB_SUPPORTED =     # Device supports force feedback functionality.
                                # Note that these force-feedback features 
                                # beyond rumble are not currently supported 
                                # through XINPUT on Windows.

#XINPUT_CAPS_WIRELESS =          # Device is wireless.

#XINPUT_CAPS_PMD_SUPPORTED =     # Device supports plug-in modules. 
                                # Note that plug-in modules like the text 
                                # input device (TID) are not supported 
                                # currently through XINPUT on Windows.

#XINPUT_CAPS_NO_NAVIGATION =     # Device lacks menu navigation buttons 
                                # (START, BACK, DPAD).

#
# XINPUT_GAMEPAD struct - wButtons masks
#
XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000

#
# Gamepad thresholds
#
XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE = 7849
XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE = 8689
XINPUT_GAMEPAD_TRIGGER_THRESHOLD = 30

#
# Flags to pass to XInputGetCapabilities
#
XINPUT_FLAG_GAMEPAD = 0x00000001


if XINPUT_USE_9_1_0 is False:
    #
    # Devices that support batteries
    #
    BATTERY_DEVTYPE_GAMEPAD = 0x00
    BATTERY_DEVTYPE_HEADSET = 0x01
    
    # BatteryTypes
    BATTERY_TYPE_DISCONNECTED = 0x00       # The device is not connected. 
    BATTERY_TYPE_WIRED = 0x01              # The device is a wired device and does not 
                                           # have a battery. 
    BATTERY_TYPE_ALKALINE = 0x02           # The device has an alkaline battery. 
    BATTERY_TYPE_NIMH = 0x03	               # The device has a nickel metal hydride battery. 
    BATTERY_TYPE_UNKNOWN = 0xFF            # The device has an unknown battery type. 
    
    # BatteryLevels
    BATTERY_LEVEL_EMPTY = 0x00
    BATTERY_LEVEL_LOW = 0x01
    BATTERY_LEVEL_MEDIUM = 0x02
    BATTERY_LEVEL_FULL = 0x03

    #
    # Multiple Controller Support 
    #
    XINPUT_USER_0=DWORD(0)
    XINPUT_USER_1=DWORD(1)
    XINPUT_USER_2=DWORD(2)
    XINPUT_USER_3=DWORD(3)
    XUSER_MAX_COUNT=4
    XINPUT_USERS=(XINPUT_USER_0,XINPUT_USER_1,XINPUT_USER_2,XINPUT_USER_3)
    XUSER_INDEX_ANY = 0x000000FF
    
    XINPUT_GAMEPAD_TL_LIT=DWORD(0)
    XINPUT_GAMEPAD_TR_LIT=DWORD(1)
    XINPUT_GAMEPAD_BR_LIT=DWORD(2)
    XINPUT_GAMEPAD_BL_LIT=DWORD(3)
        
    #
    # Codes returned for the gamepad keystroke
    #

    VK_PAD_A = 0x5800
    VK_PAD_B = 0x5801
    VK_PAD_X = 0x5802
    VK_PAD_Y = 0x5803
    VK_PAD_RSHOULDER = 0x5804
    VK_PAD_LSHOULDER = 0x5805
    VK_PAD_LTRIGGER = 0x5806
    VK_PAD_RTRIGGER  =  0x5807
    
    VK_PAD_DPAD_UP = 0x5810
    VK_PAD_DPAD_DOWN = 0x5811
    VK_PAD_DPAD_LEFT = 0x5812
    VK_PAD_DPAD_RIGHT = 0x5813
    VK_PAD_START = 0x5814
    VK_PAD_BACK = 0x5815
    VK_PAD_LTHUMB_PRESS = 0x5816
    VK_PAD_RTHUMB_PRESS = 0x5817
    
    VK_PAD_LTHUMB_UP = 0x5820
    VK_PAD_LTHUMB_DOWN = 0x5821
    VK_PAD_LTHUMB_RIGHT = 0x5822
    VK_PAD_LTHUMB_LEFT = 0x5823
    VK_PAD_LTHUMB_UPLEFT = 0x5824
    VK_PAD_LTHUMB_UPRIGHT = 0x5825
    VK_PAD_LTHUMB_DOWNRIGHT = 0x5826
    VK_PAD_LTHUMB_DOWNLEFT = 0x5827
    
    VK_PAD_RTHUMB_UP = 0x5830
    VK_PAD_RTHUMB_DOWN = 0x5831
    VK_PAD_RTHUMB_RIGHT = 0x5832
    VK_PAD_RTHUMB_LEFT = 0x5833
    VK_PAD_RTHUMB_UPLEFT = 0x5834
    VK_PAD_RTHUMB_UPRIGHT = 0x5835
    VK_PAD_RTHUMB_DOWNRIGHT = 0x5836
    VK_PAD_RTHUMB_DOWNLEFT = 0x5837

    # 
    # Flags used in XINPUT_KEYSTROKE
    #
    XINPUT_KEYSTROKE_KEYDOWN = 0x0001       # The key was pressed. 
    XINPUT_KEYSTROKE_KEYUP  = 0x0002         # The key was released. 
    XINPUT_KEYSTROKE_REPEAT = 0x0004         # A repeat of a held key. 

#
# Return Values
#

ERROR_SUCCESS = 0
ERROR_DEVICE_NOT_CONNECTED = 0x048F

if XINPUT_USE_9_1_0 is False:
    ERROR_EMPTY = 2 # made this up, need to confirm .... # 

#
## Structures
#

#
## XINPUT_GAMEPAD
#

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ('wButtons', WORD),      # See button masks above for possible values
        
        ('bLeftTrigger', c_ubyte),  # left analog control has values between 0 and 255
        
        ('bRightTrigger', c_ubyte), # right analog control has values between 0 and 255
        
        ('sThumbLX', SHORT),     # Left thumbstick x-axis value. Each of the 
                                 # thumbstick axis members is a signed value 
                                 # between -32768 and 32767 describing the 
                                 # position of the thumbstick. A value of 0 is 
                                 # centered. Negative values signify down or to
                                 # the left. Positive values signify up or to the
                                 # right. The constants 
                                 # XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE or 
                                 # XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE 
                                 # can be used as a positive and negative 
                                 # value to filter a thumbstick input.
    
        ('sThumbLY', SHORT),     # Left thumbstick y-axis value. The value is 
                                 # between -32768 and 32767.
                                 
        ('sThumbRX', SHORT),     # Right thumbstick x-axis value. The value is 
                                 # between -32768 and 32767. 
                                 
        ('sThumbRY', SHORT)     # Right thumbstick y-axis value. 
                                 # The value is between -32768 and 32767
        ]
    


# Notes:
# The constant XINPUT_GAMEPAD_TRIGGER_THRESHOLD may be used as the value 
# which bLeftTrigger and bRightTrigger must be greater than to register 
# as pressed. This is optional, but often desirable. Xbox 360 Controller 
# buttons do not manifest crosstalk.


#
## XINPUT_STATE
#
class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
    ('dwPacketNumber', DWORD),
    ('Gamepad', XINPUT_GAMEPAD)
                ]
                

    def printState(self):
        print "XINPUT_GAMEPAD (packet %d):"%(self.dwPacketNumber)
        print "\twButtons: ",self.Gamepad.wButtons
        print "\tbLeftTrigger: ",self.Gamepad.bLeftTrigger
        print "\tbRightTrigger: ",self.Gamepad.bRightTrigger
        print "\tsThumbLX: ",self.Gamepad.sThumbLX
        print "\tsThumbLY: ",self.Gamepad.sThumbLY
        print "\tsThumbRX: ",self.Gamepad.sThumbRX
        print "\tsThumbRY: ",self.Gamepad.sThumbRY
        
#
# XINPUT_VIBRATION
#
class XINPUT_VIBRATION (ctypes.Structure):
    _fields_ = [
    ('wLeftMotorSpeed', WORD), # Speed of the left motor. Valid values are 
                            # in the range 0 to 65,535. Zero signifies no 
                            # motor use; 65,535 signifies 100 percent motor use.
    ('wRightMotorSpeed', WORD)  # Speed of the right motor. Valid values are
                                # in the range 0 to 65,535. 
                                # Zero signifies no motor use; 65,535 
                                # signifies 100 percent motor use.                
            ]
# Remarks
# The left motor is the low-frequency rumble motor. 
# The right motor is the high-frequency rumble motor. 
# The two motors are not the same, and they create different vibration effects.                

   
#
# XINPUT_CAPABILITIES
#    
class XINPUT_CAPABILITIES(ctypes.Structure):
    _fields_ = [
    ('Type', c_ubyte),
    ('SubType', c_ubyte),
    ('Flags', WORD),
    ('Gamepad', XINPUT_GAMEPAD),
    ('Vibration', XINPUT_VIBRATION)
              ] 


if XINPUT_USE_9_1_0 is False:
    
    class XINPUT_BATTERY_INFORMATION(ctypes.Structure):
        _fields_ = [
        ('BatteryType',c_ubyte),
        ('BatteryLevel',c_ubyte),
                   ]


    #
    # XINPUT_KEYSTROKE
    #
    class XINPUT_KEYSTROKE(ctypes.Structure):
        _fields_ = [
            ('VirtualKey', WORD),
            ('Unicode', WCHAR),
            ('Flags', WORD),
            ('UserIndex', c_ubyte),
            ('HidCode', c_ubyte)
                  ]



class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1",DWORD),
        ("Data2",WORD),
        ("Data3",WORD),
        ("Data4",c_ubyte*8)
        ]

    #
    # VirtualKey
    #
    # Virtual-key code of the key, button, or stick movement. See XInput.h for a 
    # list of valid virtual-key (VK_xxx) codes. Also, see Remarks.
    #
    # Unicode
    # This member is unused and the value is zero.
    #
    #
    # Flags
    #
    #Flags that indicate the keyboard state at the time of the input event. This member can be any combination of the following flags:
    #Value	Description
    #
    #
    # UserIndex
    #
    # Index of the signed-in gamer associated with the device. Can be a value in
    # the range 0–3.
    #
    #
    # HidCode
    #
    # HID code corresponding to the input. If there is no corresponding HID code, 
    # this value is zero.
    #
    # Remarks
    #
    # Future devices may return HID codes and virtual key values that are not 
    # supported on current devices, and are currently undefined. Applications 
    # should ignore these unexpected values.
    # A virtual-key code is a byte value that represents a particular physical 
    # key on the keyboard, not the character or characters (possibly none) 
    # that the key can be mapped to based on keyboard state. The keyboard 
    # state at the time a virtual key is pressed modifies the character reported. 
    # For example, VK_4 might represent a "4" or a "$", depending on the state 
    # of the SHIFT key.
    #


#
## Functions
#

