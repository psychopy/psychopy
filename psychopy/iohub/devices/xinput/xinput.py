# -*- coding: utf-8 -*-
"""
ioHub Python Module
.. file: ioHub/devices/xinput/xinput.py

fileauthor: Sol Simpson <sol@isolver-software.com>

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + 
contributors, please see credits section of documentation.
"""

from xinput_h import *
from math import sqrt
import ctypes,ctypes.wintypes
from ctypes.wintypes import DWORD, pointer
from .. import Computer

#
## XInput Functions
#

global _xinput_dll    

def loadDLL():
    global _xinput_dll
    _xinput_dll=getattr(ctypes.windll,XINPUT_DLL)

def createXInputGamePadState(user_id):
        global _xinput_dll
        gamepadState=XINPUT_STATE(DWORD(0),XINPUT_GAMEPAD(0,0,0,0,0,0,0))
        t1=Computer.getTime()
        dwResult=_xinput_dll.XInputGetState(user_id, pointer(gamepadState))
        t2=Computer.getTime()
        ci=t2-t1
        return dwResult, gamepadState, t2, ci

def normalizeThumbStickValues(X,Y,INPUT_DEADZONE):
    #determine how far the controller is pushed
    magnitude = sqrt(X*X + Y*Y)

    normalizedX=0
    normalizedY=0

    if magnitude != 0:
        #determine the direction the controller is pushed
        normalizedX = X / magnitude;
        normalizedY = Y / magnitude;

    normalizedMagnitude = 0;

    #check if the controller is outside a circular dead zone
    if (magnitude > INPUT_DEADZONE):

        #clip the magnitude at its expected maximum value
        if (magnitude > 32767.0):
            magnitude = 32767.0;
  
        #adjust magnitude relative to the end of the dead zone
        magnitude -= INPUT_DEADZONE;

        # normalize the magnitude with respect to its expected range
        # giving a magnitude value of 0.0 to 1.0
        normalizedMagnitude = magnitude / (32767.0 - INPUT_DEADZONE)
        
        return normalizedX,normalizedY,normalizedMagnitude

    else: #if the controller is in the deadzone zero out the magnitude
        magnitude = 0.0
        normalizedMagnitude = 0.0
        return 0,0,0

##############################################################################
#
# Not yet Implemented......
#
## return DWORD 
#def XInputGetDSoundAudioDeviceGuids(
#    dwUserIndex,          # (DWORD)Index of the gamer associated with the device
#    pDSoundRenderGuid,    # (GUID*) DSound device ID for render
#    pDSoundCaptureGuid    # (GUID*) DSound device ID for capture
#    ):
#        pass
#
#if XINPUT_USE_9_1_0 is False:
#    
#
#
#    # returns DWORD
#    def XInputGetKeystroke(
#        dwUserIndex,    # (DWORD) Index of the gamer associated with the device
#        dwReserved,     # (DWORD) Reserved for future use
#        pKeystroke    # (PXINPUT_KEYSTROKE )Pointer to an XINPUT_KEYSTROKE structure that receives an input event.
#    ):
#        pass