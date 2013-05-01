# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/keyboard/_linux2.py

Copyright (C) 2012-2013 iSolver Software Solutions
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
                
                if event_array[4] == EventConstants.KEYBOARD_PRESS:
                    repeat_pressed_count=event_array[-7]
                    if self._report_auto_repeats is False and repeat_pressed_count > 0:
                        return True
                
                event_array[3]=Computer._getNextEventID()
                
                mod_key=event_array[-3]
                if mod_key in self._modifier_states.keys():
                    current_state=self._modifier_states[mod_key]
                    if event_array[4]==EventConstants.KEYBOARD_PRESS and current_state is False:
                        self._modifier_states[mod_key]=True
                        self._modifier_value+=KeyboardConstants._modifierCodes.getID(mod_key)
                    elif event_array[4]==EventConstants.KEYBOARD_RELEASE and current_state is True:
                        self._modifier_states[mod_key]=False
                        self._modifier_value-=KeyboardConstants._modifierCodes.getID(mod_key)
        
                event_array[-2]=self._modifier_value

                self._addNativeEventToBuffer(event_array)
                
                self._last_callback_time=logged_time
        except:
            printExceptionDetailsToStdErr()
        
        # Must return original event or no mouse events will get to OSX!
        return 1
            
    def _getIOHubEventObject(self,native_event_data):
        #ioHub.print2err('Event: ',native_event_data)
        return native_event_data


        
