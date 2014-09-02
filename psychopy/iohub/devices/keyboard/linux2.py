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
                
                #print2err('--')
                ## Check if key event window id is in list of psychopy
                #  windows and what report_system_wide_events value is                 
                win_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('window_id')
                report_system_wide_events = self.getConfiguration().get(
                'report_system_wide_events', True)
                pyglet_window_hnds = self._iohub_server._pyglet_window_hnds
                
                # win id seems to be OK on win and linux. OSX untested.
                #print2err('winID, id_list: ',pyglet_window_hnds," , ",event_array[win_id_index])
                
                if event_array[win_id_index] in pyglet_window_hnds:
                    pass
                elif len(pyglet_window_hnds) > 0 and report_system_wide_events is False:
                    return True

                auto_repeated_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('auto_repeated')
                key_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key')
                key_id_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
                event_type_index = KeyboardInputEvent.EVENT_TYPE_ID_INDEX
                event_modifiers_index = KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('modifiers')

                is_pressed = event_array[event_type_index] == EventConstants.KEYBOARD_PRESS

                # AUto repeat value provided by pyXHook code
                auto_repeat_count = event_array[auto_repeated_index] 
                # Check if the event is an auto repeat event or not, and
                # what the state of _report_auto_repeats is.

                #print2err('auto_repeat_count: ',auto_repeat_count," , ",
                #         is_pressed, " : ", self._report_auto_repeats)
                
                if auto_repeat_count > 0 and is_pressed:
                    if self._report_auto_repeats is False:
                        return True

                # set event id for event since it has passed all filters
                event_id_index = KeyboardInputEvent.EVENT_ID_INDEX
                event_array[event_id_index]=Computer._getNextEventID()
   
                ioHubKeyboardDevice._modifier_value = event_array[event_modifiers_index]  
                #print2err('Issueing KB Event:', event_array[event_id_index])
                                
                self._updateKeyboardEventState(event_array, is_pressed)          


                self._addNativeEventToBuffer(event_array)
        except:
            printExceptionDetailsToStdErr()
        
        # Must return original event or no mouse events will get to OSX!
        return 1
            
    def _getIOHubEventObject(self,native_event_data):
        #ioHub.print2err('Event: ',native_event_data)
        return native_event_data


        
