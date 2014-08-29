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
            self._last_callback_time = getTime()

            if self.isReportingEvents():             
                event_array=event[0]
                from . import KeyboardInputEvent        
                report_system_wide_events = self.getConfiguration().get(
                'report_system_wide_events', True)

                win_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('window_id')

                pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
                if event_array[win_id_index] in pyglet_window_hnds:
                    pass
                elif len(
                        pyglet_window_hnds) > 0 and report_system_wide_events is False:
                    # For keyboard, when report_system_wide_events is false
                    # do not record kb events that are not targeted for
                    # a PsychoPy window, still allow them to pass to the desktop 
                    # apps.
                    return True


                auto_repeated_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('auto_repeated')
                #key_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')
                key_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
                event_type_index = KeyboardInputEvent.EVENT_TYPE_ID_INDEX
                event_id_index = KeyboardInputEvent.EVENT_ID_INDEX
                event_modifiers_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('modifiers')
                
                key_already_pressed = self._key_states.get(event_array[key_id_index], None)
                if key_already_pressed and  event_array[event_type_index] == EventConstants.KEYBOARD_PRESS:
                    event_array[auto_repeated_index] = key_already_pressed[1] + 1
                    if self._report_auto_repeats is False and event_array[auto_repeated_index] > 0:
                        return True
    
          
                duration = 0.0
                press_event_id = 0
                # TODO: Set duration of key down event
                # and the associated press event id for the release event.
                if event_array[event_type_index]==EventConstants.KEYBOARD_RELEASE:
                    duration = 1.0   
                    press_event_id = 0
                    # update necessary 2 fields in array....
            
                
                event_array[event_id_index]=Computer._getNextEventID()
                
                mod_key=event_array[key_id_index]
                if mod_key in self._modifier_states.keys():
                    current_state=self._modifier_states[mod_key]
                    if event_array[event_type_index]==EventConstants.KEYBOARD_PRESS and current_state is False:
                        self._modifier_states[mod_key]=True
                        ioHubKeyboardDevice._modifier_value+=KeyboardConstants._modifierCodes.getID(mod_key)
                    elif event_array[event_type_index]==EventConstants.KEYBOARD_RELEASE and current_state is True:
                        self._modifier_states[mod_key]=False
                        ioHubKeyboardDevice._modifier_value-=KeyboardConstants._modifierCodes.getID(mod_key)
        
                event_array[event_modifiers_index]=ioHubKeyboardDevice._modifier_value
                self._addNativeEventToBuffer(event_array)
        except:
            printExceptionDetailsToStdErr()
        
        # Must return original event or no mouse events will get to OSX!
        return 1
            
    def _getIOHubEventObject(self,native_event_data):
        #ioHub.print2err('Event: ',native_event_data)
        return native_event_data


        
