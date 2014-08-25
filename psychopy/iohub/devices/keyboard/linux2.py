# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/keyboard/_linux2.py

Copyright (C) 2012-2014 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

from . import ioHubKeyboardDevice
from ... import print2err,printExceptionDetailsToStdErr
from .. import Computer
from ...constants import EventConstants,KeyboardConstants

getTime = Computer.getTime

class Keyboard(ioHubKeyboardDevice):
    def __init__(self,*args,**kwargs):
        ioHubKeyboardDevice.__init__(self,*args,**kwargs['dconfig'])

    def _nativeEventCallback(self,event):
        try:
            if self.isReportingEvents():             
                logged_time=getTime()
                event_array=event[0]
	        from . import KeyboardInputEvent        
    	        report_system_wide_events = self.getConfiguration().get(
	        'report_system_wide_events', True)

	        pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
	        if event_array[KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('window_id')] in pyglet_window_hnds:
	            pass
	        elif len(pyglet_window_hnds) > 0 and report_system_wide_events is False:
	            # For keyboard, when report_system_wide_events is false
	            # do not record kb events that are not targeted for
	            # a PsychoPy window, still allow them to pass to the desktop 
	            # apps.
	            return True
                
                if event_array[KeyboardInputEvent.EVENT_TYPE_ID_INDEX] == EventConstants.KEYBOARD_PRESS:
                    repeat_pressed_count=event_array[KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('auto_repeated')]
                    if self._report_auto_repeats is False and repeat_pressed_count > 0:
                        return True
                
                event_array[KeyboardInputEvent.EVENT_ID_INDEX]=Computer._getNextEventID()
                
                mod_key=event_array[KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')]
                if mod_key in self._modifier_states.keys():
                    current_state=self._modifier_states[mod_key]
                    if event_array[KeyboardInputEvent.EVENT_TYPE_ID_INDEX]==EventConstants.KEYBOARD_PRESS and current_state is False:
                        self._modifier_states[mod_key]=True
                        ioHubKeyboardDevice._modifier_value+=KeyboardConstants._modifierCodes.getID(mod_key)
                    elif event_array[KeyboardInputEvent.EVENT_TYPE_ID_INDEX]==EventConstants.KEYBOARD_RELEASE and current_state is True:
                        self._modifier_states[mod_key]=False
                        ioHubKeyboardDevice._modifier_value-=KeyboardConstants._modifierCodes.getID(mod_key)
        
                event_array[KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('modifiers')]=ioHubKeyboardDevice._modifier_value
                self._addNativeEventToBuffer(event_array)
                
                self._last_callback_time=logged_time
        except:
            printExceptionDetailsToStdErr()
        
        # Must return original event or no mouse events will get to OSX!
        return 1
            
    def _getIOHubEventObject(self,native_event_data):
        #ioHub.print2err('Event: ',native_event_data)
        return native_event_data


        
