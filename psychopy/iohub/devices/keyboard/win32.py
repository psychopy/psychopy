# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/keyboard/_win32.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import pyHook
import ctypes
from unicodedata import category as ucategory

        
from . import ioHubKeyboardDevice
from ... import print2err,printExceptionDetailsToStdErr
from ...constants import KeyboardConstants, EventConstants
from .. import Computer

import win32_vk

getTime = Computer.getTime
class Keyboard(ioHubKeyboardDevice):
    _win32_modifier_mapping={
                 win32_vk.VK_LCONTROL  : 'CONTROL_LEFT', 
                 win32_vk.VK_RCONTROL  : 'CONTROL_RIGHT', 
                 win32_vk.VK_LSHIFT  : 'SHIFT_LEFT', 
                 win32_vk.VK_RSHIFT  : 'SHIFT_RIGHT', 
                 win32_vk.VK_LMENU  : 'ALT_LEFT', 
                 win32_vk.VK_RMENU  : 'ALT_RIGHT', 
                 win32_vk.VK_LWIN : 'COMMAND_LEFT', 
                 win32_vk.VK_RWIN : 'COMMAND_RIGHT', 
                 win32_vk.VK_CAPITAL : 'CAPS_LOCK', 
                 win32_vk.VK_SHIFT : 'MOD_SHIFT', 
                 win32_vk.VK_MENU : 'MOD_ALT', 
                 win32_vk.VK_CONTROL : 'MOD_CTRL', 
                 #win32_vk. : 'MOD_CMD', 
                 win32_vk.VK_NUMLOCK : 'NUMLOCK' 
                 }           
    
    __slots__=['_user32','_keyboard_state','_unichar']
    
    def __init__(self,*args,**kwargs):                        
        ioHubKeyboardDevice.__init__(self,*args,**kwargs['dconfig'])
        self._user32=ctypes.windll.user32
        self._keyboard_state=(ctypes.c_byte*256)()
        for i in range(256):
            self._keyboard_state[i] = 0

        self._unichar=(ctypes.c_wchar*8)()
        
    def _nativeEventCallback(self,event):
        if self.isReportingEvents():
            notifiedTime=getTime()
            
            report_system_wide_events=self.getConfiguration().get('report_system_wide_events',True)

            pyglet_window_hnds=self._iohub_server._pyglet_window_hnds
            if event.Window in pyglet_window_hnds:
                pass
            elif len(pyglet_window_hnds)>0 and report_system_wide_events is False:
                # For keyboard, when report_system_wide_events is false
                # do not record kb events that are not targeted for
                # a PsychoPy window, still allow them to pass to the desktop 
                # apps.
                return True
                
            event.Type = EventConstants.KEYBOARD_RELEASE
            if event.Message in [pyHook.HookConstants.WM_KEYDOWN,pyHook.HookConstants.WM_SYSKEYDOWN]:
                event.Type = EventConstants.KEYBOARD_PRESS

            self._last_callback_time=notifiedTime
            
            event.RepeatCount=0
            key_already_pressed=self._key_states.get(event.KeyID,None)
            if key_already_pressed and event.Type == EventConstants.KEYBOARD_PRESS:
                event.RepeatCount=key_already_pressed[1]+1
                if self._report_auto_repeats is False and event.RepeatCount>0:
                    return True
            elif key_already_pressed and event.Type == EventConstants.KEYBOARD_RELEASE:
                if 'KeyboardReleaseEvent' not in self.getConfiguration().get('monitor_event_types'):
                    event.RepeatCount=0
                    self._key_states.pop(event.KeyID)
                    
            self._addNativeEventToBuffer((notifiedTime,event))
            
        #endtime=getTime()
        #print2err("callback dur: %.3f msec"%((endtime-notifiedTime)*1000.0))
        # pyHook require the callback to return True to inform the windows 
        # low level hook functionality to pass the event on.
        return True

    def _getIOHubEventObject(self,native_event_data):
        try:
            if  len(native_event_data) >2:
                # it is a KeyboardCharEvent
                return native_event_data
    
    #        stime=getTime()
            notifiedTime, event=native_event_data
            etype = event.Type
                            
            #
            # Start Tracking Modifiers that are pressed
            #
            keyID=event.KeyID
            
            modKeyName=Keyboard._win32_modifier_mapping.get(keyID,None)
            if modKeyName:
                mod_value=KeyboardConstants._modifierCodes.getID(modKeyName)
                if  keyID == win32_vk.VK_CAPITAL and etype==EventConstants.KEYBOARD_PRESS:
                    if self._keyboard_state[keyID] > 0:
                        self._keyboard_state[keyID]=0
                        ioHubKeyboardDevice._modifier_value-=mod_value
                    else:
                        self._keyboard_state[keyID] = 0x01
                        ioHubKeyboardDevice._modifier_value+=mod_value
                        
                elif etype==EventConstants.KEYBOARD_PRESS and self._keyboard_state[keyID]==0:
                    self._keyboard_state[keyID] = 0x80
                    ioHubKeyboardDevice._modifier_value+=mod_value
    
                    #print2err("SETTING MOD KEY ELEMENT: ",keyID,' state: ',pyHook.GetKeyState(keyID))
                    
                    if keyID in [win32_vk.VK_LSHIFT,win32_vk.VK_RSHIFT] and self._keyboard_state[win32_vk.VK_SHIFT]==0:                    
                        self._keyboard_state[win32_vk.VK_SHIFT] = 0x80
                        #print2err("SETTING shift ",keyID)
                    elif keyID in [win32_vk.VK_LCONTROL,win32_vk.VK_RCONTROL] and self._keyboard_state[win32_vk.VK_CONTROL] ==0:                    
                        self._keyboard_state[win32_vk.VK_CONTROL] = 0x80
                        #print2err("SETTING CTRL: ",keyID)
                    elif keyID in [win32_vk.VK_LMENU,win32_vk.VK_RMENU] and self._keyboard_state[win32_vk.VK_MENU]==0:                    
                        self._keyboard_state[win32_vk.VK_MENU] = 0x80
                        #print2err("SETTING  VK_MENU: ",keyID)
                        
                elif etype==EventConstants.KEYBOARD_RELEASE and keyID != win32_vk.VK_CAPITAL:
                    if self._keyboard_state[keyID]!=0 and keyID != win32_vk.VK_CAPITAL:
                        ioHubKeyboardDevice._modifier_value-=mod_value
                        self._keyboard_state[keyID] = 0
                        #print2err("clearing MOD KEY ELEMENT: ",keyID,' state: ',pyHook.GetKeyState(keyID))
    
                        if modKeyName.find('SHIFT')>=0 and self._keyboard_state[win32_vk.VK_LSHIFT]==0 and self._keyboard_state[win32_vk.VK_RSHIFT]==0:
                            self._keyboard_state[win32_vk.VK_SHIFT] = 0
                           # print2err("CLEAR  VK_SHIFT: ",keyID)
                        elif modKeyName.find('CONTROL')>=0 and self._keyboard_state[win32_vk.VK_LCONTROL]==0 and self._keyboard_state[win32_vk.VK_RCONTROL]==0:
                            self._keyboard_state[win32_vk.VK_CONTROL] = 0
                            #print2err("CLEAR  VK_CONTROL: ",keyID)
                        elif modKeyName.find('ALT')>=0 and self._keyboard_state[win32_vk.VK_LMENU]==0 and self._keyboard_state[win32_vk.VK_RMENU]==0:
                            self._keyboard_state[win32_vk.VK_MENU] = 0
                            #print2err("CLEAR  VK_MENU: ",keyID)
            #
            # End Tracking Modifiers that are pressed
            #
            if ioHubKeyboardDevice._modifier_value is None:
                ioHubKeyboardDevice._modifier_value=0
            event.Modifiers=ioHubKeyboardDevice._modifier_value
    
            # From MSDN: http://msdn.microsoft.com/en-us/library/windows/desktop/ms644939(v=vs.85).aspx
            # The time is a long integer that specifies the elapsed time, in milliseconds, from the time the system was started to the time the message was 
            # created (that is, placed in the thread's message queue).REMARKS: The return value from the GetMessageTime function does not necessarily increase
            # between subsequent messages, because the value wraps to zero if the timer count exceeds the maximum value for a long integer. To calculate time
            # delays between messages, verify that the time of the second message is greater than the time of the first message; then, subtract the time of the
            # first message from the time of the second message.
            device_time = event.Time/1000.0 # convert to sec
            time = notifiedTime #TODO correct kb times to factor in delay if possible.
     
            confidence_interval=0.0 # since this is a keyboard device using a callback method, confidence_interval is not applicable
            delay=0.0 # since this is a keyboard, we 'know' there is a delay, but until we support setting a delay in the device properties based on external testing for a given keyboard, we will leave at 0.
    
            #
            ## check for unicode char        
            #
            
            # uchar holds the unicode ord() number for the unicode char. unichr(uchar) == u'x' unicode str
            uchar=0
            
            # key holds the unicode char, in 8 bit string format encoded in UTF-8. 
            # Safe to transmit and to store in pytables. Use key.decode('utf-8') to get the unicode sybol decoded into a unicode string. 
            key=None 
            
            # ucat holds the unicode character category. This can be used  to tell what king of code point it is.
            # For a list of categories see http://www.unicode.org/reports/tr44/#General_Category_Values
            # examples:
            #   u'v' -> category: Ll 
            #   u'<-' (ESCAPE) -> category: Cc 
            #   u' ' -> category: Zs
    
            ucat=None
            
            result=self._user32.ToUnicode(event.KeyID, event.ScanCode,ctypes.byref(self._keyboard_state),ctypes.byref(self._unichar),8,0)
            if result > 0:
                if result == 1:
    #               print2err("self._unichar[0]: ",self._unichar[0], " ", type(self._unichar[0]))
    #              print2err(u"á: ",u"á", " upper: ",u"á".upper())
    #               print2err(u"': ",u"'", " upper: ",u"'".upper())
                   key=self._unichar[0].encode('utf-8') 
                   uchar=ord(self._unichar[0])
                   ucat=ucategory(self._unichar[0])
                else:                    
                    key=u''
                    for c in range(result):
                        uchar=ord(self._unichar[c])
                        ucat=ucategory(self._unichar[c])
                    key=self._unichar[0:result]
                    key=key.encode('utf-8')
            elif result == -1:
                # The specified virtual key is a dead-key character (accent or diacritic). 
                # This value is returned regardless of the keyboard layout, even if several
                # characters have been typed and are stored in the keyboard state. If possible,
                # even with Unicode keyboard layouts, the function has written a spacing version
                # of the dead-key character to the buffer specified by pwszBuff. For example,
                # the function writes the character SPACING ACUTE (0x00B4), 
                # rather than the character NON_SPACING ACUTE (0x0301).                
                key=self._unichar[0].encode('utf-8') 
                uchar=ord(self._unichar[0])
                ucat=ucategory(self._unichar[0])
            
            
            if result==0 or ucat and ucat[0]=='C':
                #
                ## TODO , TO FIX: We should only bother looking in the hardcoded character label lookup tables if the key did not result in
                ## a unicode char being returned, or if the unicode char is in a Control char category, etc.
                ## However it seems that the ToUnice fucntion is not factoring in whether shift is pressed or not, so it always returns a lower case letter.
                ## So for now, look up all keys and if a result is found, replace the 'key' field with it; but leave the ucode field as is.
                ## I 'think' we should be getting upper case unicode chars if shift is pressed, so this needs to be looked into. 
                #
                # also look in built in key mappings; if a key label is returned, use it instead of the unicode char (it could be a non visible key)
                lookupkey,_=KeyboardConstants._getKeyNameAndModsForEvent(event)
                if lookupkey and len(lookupkey)>0:
                    key=lookupkey
            
            #import ctypes
            #_dll=ctypes.windll.user32   
            #kstatus=ctypes.c_short(_dll.GetAsyncKeyState(ctypes.c_int(k.key_id)))
            #print k.key, ' status is %x pressed=%d was_pressed=%d'%(kstatus.value,(kstatus.value&0x80)>0,(kstatus.value&0x01)>0)
        
                        
            return [0,
                    0,
                    0, #device id (not currently used)
                    Computer._getNextEventID(),
                    etype,
                    device_time,
                    notifiedTime,
                    time,
                    confidence_interval,
                    delay,
                    0,
                    event.RepeatCount,
                    event.ScanCode,
                    event.KeyID,
                    uchar,
                    key,
                    event.Modifiers,
                    event.Window
                    ]
        except:
            printExceptionDetailsToStdErr()