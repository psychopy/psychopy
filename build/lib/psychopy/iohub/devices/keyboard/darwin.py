# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/keyboard/darwin.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

        
from copy import copy
import Quartz as Qz
from AppKit import NSEvent #NSKeyUp, NSSystemDefined, NSEvent

from . import ioHubKeyboardDevice
from ... import print2err,printExceptionDetailsToStdErr
from ...constants import KeyboardConstants, DeviceConstants, EventConstants
from .. import Computer

from unicodedata import category as ucategory

getTime = Computer.getTime

eventHasModifiers = lambda v: Qz.kCGEventFlagMaskNonCoalesced - v != 0     
keyFromNumpad = lambda v: Qz.kCGEventFlagMaskNumericPad & v > 0   
caplocksEnabled = lambda v : Qz.kCGEventFlagMaskAlphaShift & v > 0 
shiftModifierActive = lambda v : Qz.kCGEventFlagMaskShift & v > 0
altModifierActive = lambda v : Qz.kCGEventFlagMaskAlternate & v > 0
controlModifierActive = lambda v : Qz.kCGEventFlagMaskControl & v > 0
commandModifierActive = lambda v : Qz.kCGEventFlagMaskCommand & v > 0

class Keyboard(ioHubKeyboardDevice):       
    _OS_MODIFIERS=([(0x00001,'CONTROL_LEFT'),(0x02000,'CONTROL_RIGHT'),
                    (0x00002,'SHIFT_LEFT'),(0x00004,'SHIFT_RIGHT'),
                    (0x00020,'ALT_LEFT'),(0x00040,'ALT_RIGHT'),
                    (0x000008, 'COMMAND_LEFT'),(0x000010,'COMMAND_RIGHT'),
                    (Qz.kCGEventFlagMaskAlphaShift, 'CAPS_LOCK'),
                    (Qz.kCGEventFlagMaskSecondaryFn, "MOD_FUNCTION"),
                    (Qz.kCGEventFlagMaskHelp , "MOD_HELP")])        # 0x400000   
   
    DEVICE_TIME_TO_SECONDS=0.000000001
    
    _EVENT_TEMPLATE_LIST=[0, # experiment id
                        0,  # session id
                        0, #device id (not currently used)
                        0,  # Computer._getNextEventID(),
                        0,  # ioHub Event type
                        0.0,# event device time,
                        0.0,# event logged_time,
                        0.0,# event iohub Time,
                        0.0,# confidence_interval, 
                        0.0,# delay,
                        0,  # filtered by ID (always 0 right now)  
                        0, # auto repeat count
                        0,  # ScanCode
                        0,  # KeyID 
                        0,  # ucode
                        u'',# Unicode key utf-8 encoded / Key Name Constant ( i.e. SPACE, ESCAPE, ENTER, etc )
                        None,# mods
                        0 ] # event.Window]
    
    __slots__=['_loop_source','_tap','_device_loop','_CGEventTapEnable','_loop_mode','_last_general_mod_states','_ring_buffer']

    def __init__(self,*args,**kwargs):
        ioHubKeyboardDevice.__init__(self,*args,**kwargs['dconfig'])
        
        # TODO: This dict should be reset whenever monitoring is turned off for the device OR
        # whenever events are cleared fpr the device.
        # Same to do for the _active_modifiers bool lookup array
        self._last_general_mod_states=dict(shift_on=False,alt_on=False,cmd_on=False,ctrl_on=False)
        
        self._loop_source=None
        self._tap=None
        self._device_loop=None
        self._loop_mode=None        

        self._tap = Qz.CGEventTapCreate(
            Qz.kCGSessionEventTap,
            Qz.kCGHeadInsertEventTap,
            Qz.kCGEventTapOptionDefault,
            Qz.CGEventMaskBit(Qz.kCGEventKeyDown) |
            Qz.CGEventMaskBit(Qz.kCGEventKeyUp)|
            Qz.CGEventMaskBit(Qz.kCGEventFlagsChanged),
            self._nativeEventCallback,
            None)            
        
        self._CGEventTapEnable=Qz.CGEventTapEnable
        self._loop_source = Qz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        
        self._device_loop = Qz.CFRunLoopGetCurrent()
        
        self._loop_mode=Qz.kCFRunLoopDefaultMode
        
        from ...util import NumPyRingBuffer
        self._ring_buffer=NumPyRingBuffer(100)
        Qz.CFRunLoopAddSource(self._device_loop, self._loop_source, self._loop_mode)
        
    def _handleModifierChangeEvent(self,event):
        flags=Qz.CGEventGetFlags(event)
        key_name=None
        ioe_type=None
        ioHubKeyboardDevice._modifier_value,mod_str_list=Keyboard._checkForLeftRightModifiers(flags)
        mod_presses=[]
        mod_releases=[]
        for mod_name, mod_state in self._modifier_states.iteritems():
            if mod_name in mod_str_list and not mod_state:
                self._modifier_states[mod_name]=True
                mod_presses.append(mod_name)
            elif mod_name not in mod_str_list and mod_state:   
                self._modifier_states[mod_name]=False
                mod_releases.append(mod_name)                                

        if (len(mod_presses) + len(mod_releases)) > 1:
            print2err("\nWARNING: Multiple modifiers reported a state change in one event. BUG??:", mod_presses, mod_releases)
            print2err("Using ONLY first change detected for event.\n")
        
        # OK, so if there is an element in mod presses or releases, then
        # we know the mod key that changed the state transition is a left_*,
        # or right_* or the cap locks key and we have the key we need.
        if len(mod_presses) > 0:
            ioe_type=EventConstants.KEYBOARD_PRESS
            key_name=mod_presses[0]
        elif len(mod_releases) > 0:
            key_name=mod_releases[0]
            ioe_type=EventConstants.KEYBOARD_RELEASE
        
        #TODO: What keyCode should we use for each modifier events?
        # key_code = ???
        
        if key_name is None:
            # So no modifiers matching the left_, right_ mod codes were found,
            # so lets check the generic non position based mode codes that are 'officially'
            # defined by OS X
            shift_on=shiftModifierActive(flags)
            alt_on=altModifierActive(flags)
            ctrl_on=controlModifierActive(flags)
            cmd_on=commandModifierActive(flags)    

            if shift_on != self._last_general_mod_states['shift_on']:
                if shift_on is True:
                    ioe_type=EventConstants.KEYBOARD_PRESS
                else:
                    ioe_type=EventConstants.KEYBOARD_RELEASE
                self._last_general_mod_states['shift_on']=shift_on
                key_name=u'MOD_SHIFT'
            elif alt_on != self._last_general_mod_states['alt_on']:
                if alt_on is True:
                    ioe_type=EventConstants.KEYBOARD_PRESS
                else:
                    ioe_type=EventConstants.KEYBOARD_RELEASE
                self._last_general_mod_states['alt_on']=alt_on
                key_name=u'MOD_ALT'
            elif ctrl_on != self._last_general_mod_states['ctrl_on']:
                if ctrl_on is True:
                    ioe_type=EventConstants.KEYBOARD_PRESS
                else:
                    ioe_type=EventConstants.KEYBOARD_RELEASE
                self._last_general_mod_states['ctrl_on']=ctrl_on
                key_name=u'MOD_CTRL'
            elif cmd_on != self._last_general_mod_states['cmd_on']:
                if cmd_on is True:
                    ioe_type=EventConstants.KEYBOARD_PRESS
                else:
                    ioe_type=EventConstants.KEYBOARD_RELEASE
                key_name=u'MOD_CMD'
                self._last_general_mod_states['cmd_on']=cmd_on
        return ioe_type,key_name
            
    def _getKeyNameForEvent(self,ns_event):
        key_code=ns_event.keyCode()  
        ucode=0

        key_name=ns_event.characters()
        if key_name and len(key_name)>0:
            ucode=ord(key_name)
            #print2err('characters hit: [',key_name, '] ', ucode, ' ', len(key_name))                 
            #print2err("characters ucategory: ",ucategory(unichr(ucode)))
        
        if ucode == 0 or ucategory(unichr(ucode))[0] == 'C':
            key_name=ns_event.charactersIgnoringModifiers()
            if key_name and len(key_name)>0:
                ucode=ord(key_name)   
                #print2err(" charactersIgnoringModifiers ucategory: ",ucategory(unichr(ucode)))
                #print2err('charactersIgnoringModifiers hit: [',key_name, '] ', ord(key_name[-1]), ' ', len(key_name))                 
        
        if ucode != 0:                     
            umac_key_name=KeyboardConstants._unicodeChars.getName(ucode)
            if umac_key_name and len(umac_key_name)>0:
                if umac_key_name.startswith('VK_'):
                    umac_key_name=umac_key_name[3:]
                key_name=u''+umac_key_name 
                #ucode=ord(key_name[-1]) 
#                print2err('mac ucode hit: [',key_name, '] ', ucode, ' ', len(key_name))
                
        if key_name is None or len(key_name)==0:# or ucategory(unichr(ucode))[0] == 'C':
                            
            key_name=KeyboardConstants._virtualKeyCodes.getName(key_code)
            if key_name:
                if key_name.startswith('VK_'):
                    key_name=key_name[3:]
                key_name=(u''+key_name)            
        
            if not key_name:
                amac_key_name=KeyboardConstants._ansiKeyCodes.getName(key_code)
                if amac_key_name and len(amac_key_name)>0:
                    key_name=amac_key_name 
                    if key_name.startswith('ANSI_'):
                        key_name=key_name[5:]
                    key_name=u''+key_name
                    
        return key_name,ucode,key_code

    
    def _poll(self):
        self._last_poll_time=getTime()            
        while Qz.CFRunLoopRunInMode(self._loop_mode, 0.0, True) == Qz.kCFRunLoopRunHandledSource:
            pass
                        
    def _nativeEventCallback(self,*args):
        try:
            proxy, etype, event, refcon = args
            
            if self.isReportingEvents():
                logged_time=getTime()

                  
                if etype == Qz.kCGEventTapDisabledByTimeout:
                    print2err("** WARNING: Keyboard Tap Disabled due to timeout. Re-enabling....: ", etype)
                    Qz.CGEventTapEnable(self._tap, True)
                    return event
               
                confidence_interval=logged_time-self._last_poll_time
                delay=0.0 # No point trying to guess for the keyboard or mouse.
                            # May add a 'default_delay' prefernce to the device config settings,
                            # so if a person knows the average delay for something like the kb or mouse
                            # they are using, then they could specify it in the config file and it could be used here.
                iohub_time = logged_time-delay
                device_time=Qz.CGEventGetTimestamp(event)*self.DEVICE_TIME_TO_SECONDS                        
                key_code = Qz.CGEventGetIntegerValueField(event, Qz.kCGKeyboardEventKeycode)                    
                key_name=None
                window_number=0       
                ioe_type=None
                ucode=0 # the int version of the unicode utf-8 ichar
                is_auto_repeat= Qz.CGEventGetIntegerValueField(event, Qz.kCGKeyboardEventAutorepeat)
                #np_key=keyFromNumpad(flags)     
                                        
                # This is a modifier state change event, so we need to manually determine
                # which mod key was either pressed or released that resulted in the state change....
                if etype == Qz.kCGEventFlagsChanged:
                    try:
                        ioe_type, key_name=self._handleModifierChangeEvent(event)
#                        print2err('_handleModifierChangeEvent: ',ioe_type, ' ',key_name)
                    except Exception, e:
                        print2err("kCGEventFlagsChanged failed: ",e)
                        printExceptionDetailsToStdErr()                            
                else:
                    # This is an actual button press / release event, so handle it....
                    try:
                        keyEvent = NSEvent.eventWithCGEvent_(event)
                        key_name,ucode,key_code=self._getKeyNameForEvent(keyEvent)
                        window_number=keyEvent.windowNumber()

                        #report_system_wide_events=self.getConfiguration().get('report_system_wide_events',True)
            
                        #pyglet_window_hnds=self._iohub_server._pyglet_window_hnds
                        #print2err("pyglet_window_hnds: ",pyglet_window_hnds)
                        #if event.Window in pyglet_window_hnds:
                        #    pass
                        #elif len(pyglet_window_hnds)>0 and report_system_wide_events is False:
                            # For keyboard, when report_system_wide_events is false
                            # do not record kb events that are not targeted for
                            # a PsychoPy window, still allow them to pass to the desktop 
                            # apps.
                        #    return event



                        if etype == Qz.kCGEventKeyUp:
                            ioe_type=EventConstants.KEYBOARD_RELEASE
                        elif etype == Qz.kCGEventKeyDown:
                            ioe_type=EventConstants.KEYBOARD_PRESS
                    except Exception,e:
                        print2err("Create NSEvent failed: ",e)
                        printExceptionDetailsToStdErr()
                if ioe_type: 
                    # The above logic resulted in finding a key press or release event
                    # from the expected events OR from modifier state changes. So,
                    # send the iohub event version to ioHub.
                    #
                    # FILL IN AND CREATE EVENT
                    # index 0 and 1 are session and exp. ID's
                    # index 3 is device id (not yet supported)
                    #key_name='£'
                    if ioe_type == EventConstants.KEYBOARD_PRESS:                       
                        if is_auto_repeat > 0 and self._report_auto_repeats is False:
                            return event

                    if key_name is None or len(key_name)==0:
                        # TO DO: dead char we need to deal with??
                        key_name=u'DEAD_KEY?'
                        print2err("DEAD KEY HIT?")
                    else:    
                        ioe=self._EVENT_TEMPLATE_LIST
                        ioe[3]=Computer._getNextEventID()
                        ioe[4]=ioe_type #event type code
                        ioe[5]=device_time
                        ioe[6]=logged_time
                        ioe[7]=iohub_time
                        ioe[8]=confidence_interval
                        ioe[9]=delay
                        # index 10 is filter id, not used at this time                        
                        ioe[11]=is_auto_repeat

                        ioe[12]=key_code # Quartz does not give the scancode, so fill this with keycode
                        ioe[13]=key_code #key_code
                        ioe[14]=ucode
                        ioe[15]=key_name.encode('utf-8') 
                        ioe[16]=ioHubKeyboardDevice._modifier_value
                        ioe[17]=window_number
                        #print2err('OSX event handler: ',ucode,' ',iohub_time,' ',window_number)
                        self._addNativeEventToBuffer(copy(ioe))
                        #print2err("**Final values:key_name [",key_name,"] ucode: ",ucode, ' key_code: ',key_code)
                else:
                    print2err("\nWARNING: KEYBOARD RECEIVED A [ {0} ] KB EVENT, BUT COULD NOT GENERATE AN IOHUB EVENT FROM IT !!".format(etype)," [",key_name,"] ucode: ",ucode, ' key_code: ',key_code)
                    
                self._last_callback_time=logged_time                
            
                #cdur=getTime()-logged_time
                #print2err('callback dur: ',cdur)        
                # Must return original event or no keyboard events will get to OSX!
            return event
        except:
            printExceptionDetailsToStdErr()
            Qz.CGEventTapEnable(self._tap, False)
        
        return event
    
    @classmethod
    def _checkForLeftRightModifiers(cls,mod_state):
        mod_value=0
        mod_strs=[]
        for k,v in cls._OS_MODIFIERS:
            if mod_state & k > 0:
                mod_value+=KeyboardConstants._modifierCodes.getID(v)
                mod_strs.append(v)
        return mod_value,mod_strs            
        
    def _getIOHubEventObject(self,native_event_data):
        return native_event_data
    
    def _close(self):            
        try:
            Qz.CGEventTapEnable(self._tap, False)
        except:
            pass
        try:
            if Qz.CFRunLoopContainsSource(self._device_loop,self._loop_source,self._loop_mode) is True:    
                Qz.CFRunLoopRemoveSource(self._device_loop,self._loop_source,self._loop_mode)
        finally:
            self._loop_source=None
            self._tap=None
            self._device_loop=None
            self._loop_mode=None            
        ioHubKeyboardDevice._close(self)
