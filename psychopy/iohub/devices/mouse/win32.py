# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 18:48:58 2013

@author: isolver
"""

import ctypes
from . import MouseDevice
from ...constants import EventConstants,MouseConstants
from ... import print2err
from .. import Computer,Keyboard

currentSec=Computer.getTime

POINT = ctypes.wintypes.POINT
RECT = ctypes.wintypes.RECT

class Mouse(MouseDevice):
    """
    The Mouse class and related events represent a standard computer mouse device
    and the events a standard mouse can produce. Mouse position data is mapped to
    the coordinate space defined in the ioHub configuration file for the Display.
    """
    WM_MOUSEFIRST = 0x0200
    WM_MOUSEMOVE = 0x0200
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    WM_LBUTTONDBLCLK = 0x0203
    WM_RBUTTONDOWN =0x0204
    WM_RBUTTONUP = 0x0205
    WM_RBUTTONDBLCLK = 0x0206
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_MBUTTONDBLCLK = 0x0209
    WM_MOUSEWHEEL = 0x020A
    WM_MOUSELAST = 0x020A

    WH_MOUSE = 7
    WH_MOUSE_LL = 14
    WH_MAX = 15
   
    _mouse_event_mapper={
        WM_MOUSEMOVE : [0, EventConstants.MOUSE_MOVE, MouseConstants.MOUSE_BUTTON_NONE],
        WM_RBUTTONDOWN : [MouseConstants.MOUSE_BUTTON_STATE_PRESSED, EventConstants.MOUSE_BUTTON_PRESS, MouseConstants.MOUSE_BUTTON_RIGHT],
        WM_MBUTTONDOWN : [MouseConstants.MOUSE_BUTTON_STATE_PRESSED, EventConstants.MOUSE_BUTTON_PRESS, MouseConstants.MOUSE_BUTTON_MIDDLE],
        WM_LBUTTONDOWN : [MouseConstants.MOUSE_BUTTON_STATE_PRESSED, EventConstants.MOUSE_BUTTON_PRESS, MouseConstants.MOUSE_BUTTON_LEFT],
        WM_RBUTTONUP : [MouseConstants.MOUSE_BUTTON_STATE_RELEASED, EventConstants.MOUSE_BUTTON_RELEASE, MouseConstants.MOUSE_BUTTON_RIGHT],
        WM_MBUTTONUP : [MouseConstants.MOUSE_BUTTON_STATE_RELEASED, EventConstants.MOUSE_BUTTON_RELEASE, MouseConstants.MOUSE_BUTTON_MIDDLE],
        WM_LBUTTONUP : [MouseConstants.MOUSE_BUTTON_STATE_RELEASED, EventConstants.MOUSE_BUTTON_RELEASE, MouseConstants.MOUSE_BUTTON_LEFT],
        WM_RBUTTONDBLCLK : [MouseConstants.MOUSE_BUTTON_STATE_MULTI_CLICK, EventConstants.MOUSE_MULTI_CLICK, MouseConstants.MOUSE_BUTTON_RIGHT],
        WM_MBUTTONDBLCLK : [MouseConstants.MOUSE_BUTTON_STATE_MULTI_CLICK, EventConstants.MOUSE_MULTI_CLICK, MouseConstants.MOUSE_BUTTON_MIDDLE],
        WM_LBUTTONDBLCLK : [MouseConstants.MOUSE_BUTTON_STATE_MULTI_CLICK, EventConstants.MOUSE_MULTI_CLICK, MouseConstants.MOUSE_BUTTON_LEFT],
        WM_MOUSEWHEEL : [0, EventConstants.MOUSE_SCROLL, MouseConstants.MOUSE_BUTTON_NONE]
    }

    slots=['_user32','_original_system_cursor_clipping_rect']
    def __init__(self,*args,**kwargs):          
        MouseDevice.__init__(self,*args,**kwargs['dconfig'])

        self._user32=ctypes.windll.user32

        self.getSystemCursorVisibility()
        self._original_system_cursor_clipping_rect=RECT()
        self._user32.GetClipCursor(ctypes.byref(self._original_system_cursor_clipping_rect))
#        cr=self._original_system_cursor_clipping_rect
#        print2err("MOUSE CLIP CURSOR BOUNDS: {0} {1} {2} {3}".format(cr.left,cr.top,cr.right,cr.bottom))
        
#    def _nativeLimitCursorToBoundingRect(self,clip_rect):
#        native_clip_rect=RECT()            
#        if clip_rect:
#            native_clip_rect.right=ctypes.c_long(clip_rect.right)
#            native_clip_rect.bottom=ctypes.c_long(clip_rect.bottom)
#            native_clip_rect.left=ctypes.c_long(clip_rect.left)
#            native_clip_rect.top=ctypes.c_long(clip_rect.top)
#            self._user32.ClipCursor(ctypes.byref(native_clip_rect))
#        else:
#            self._user32.ClipCursor(None)
#            self._user32.GetClipCursor(ctypes.byref(native_clip_rect))
#        return native_clip_rect
        
    def _nativeSetMousePos(self,px,py):
        self._user32.SetCursorPos(int(px),int(py))
        #ioHub.print2err(" mouse.setPos updated to {0}".format((px,py)))
        
    def _nativeGetSystemCursorVisibility(self):
        self._user32.ShowCursor(False)    
        self._isVisible = self._user32.ShowCursor(True)
        return self._isVisible >= 0
 
    def _nativeSetSystemCursorVisibility(self,v):
        self._isVisible=self._user32.ShowCursor(v)
        return self._isVisible >= 0
        
    def _nativeEventCallback(self,event):
        if self.isReportingEvents():
            logged_time=currentSec()
            report_system_wide_events=self.getConfiguration().get('report_system_wide_events',True)
            pyglet_window_hnds=self._iohub_server._pyglet_window_hnds
            #print2err ("pyglet_window_hnds: ",pyglet_window_hnds, " : ",event.Window)
            if event.Window in pyglet_window_hnds:
                pass
            elif len(pyglet_window_hnds)>0 and report_system_wide_events is False:
                # For the Mouse, always pass along events, but do not log
                # events that occurred targeted for a non Psychopy win.
                #
                #print2err ("Skipping mouse event...",pyglet_window_hnds, " : ",event.Window)
                return True
            self._scrollPositionY+= event.Wheel
            event.WheelAbsolute=self._scrollPositionY

            display_index=self.getDisplayIndexForMousePosition(event.Position)

            if display_index == -1:
                if self._last_display_index is not None:
                    display_index=self._last_display_index
                else:    
                    #print2err("!!! _nativeEventCallback error: mouse event pos {0} not in any display bounds!!!".format(event.Position))
                    #print2err("!!!  -> SKIPPING EVENT")
                    #print2err("===============")
                    return True
            
#            result=self._validateMousePosition(event.Position,display_index)
            #print2err("_validateMousePosition result: ", result)
            
#            if result != True:
                #ioHub.print2err("!!! _validateMousePosition made ajustment: {0} to {1}".format(
                #                                   event.Position,result))
#                self._nativeSetMousePos(*result) 
#                event.Position=result
#                display_index=self.getDisplayIndexForMousePosition(event.Position)
                
            mx,my=event.Position                
            event.DisplayIndex=display_index                
            p=self._display_device._pixel2DisplayCoord(mx,my,event.DisplayIndex)  
        
            #print2err("Going to Update mousePosition: {0} => {1} on D {2}".format(
            #                    event.Position,p,event.DisplayIndex))

            event.Position=p
            
            self._lastPosition=self._position
            self._position=event.Position

            self._last_display_index=self._display_index
            self._display_index=display_index
 
            #print2err("===============")
            
            # <<<<<<<<<
            
            bstate,etype,bnum=self._mouse_event_mapper[event.Message]
            if bnum is not MouseConstants.MOUSE_BUTTON_NONE:
                self.activeButtons[bnum]= int(bstate==MouseConstants.MOUSE_BUTTON_STATE_PRESSED)

            abuttonSum=0
            for k,v in self.activeButtons.iteritems():
                abuttonSum+=k*v

            event.ActiveButtons=abuttonSum

            self._addNativeEventToBuffer((logged_time,event))

            self._last_callback_time=logged_time
            
        # pyHook require the callback to return True to inform the windows 
        # low level hook functionality to pass the event on.
        return True

    def _getIOHubEventObject(self,native_event_data):
        logged_time, event=native_event_data
        p = event.Position
        px=p[0]
        py=p[1]

        bstate,etype,bnum=self._mouse_event_mapper[event.Message]

        if event.Message == self.WM_MOUSEMOVE and event.ActiveButtons>0:
            etype=EventConstants.MOUSE_DRAG

        confidence_interval=0.0
        delay=0.0

        # From MSDN: http://msdn.microsoft.com/en-us/library/windows/desktop/ms644939(v=vs.85).aspx
        # The time is a long integer that specifies the elapsed time, in milliseconds, from the time the system was started to the time the message was 
        # created (that is, placed in the thread's message queue).REMARKS: The return value from the GetMessageTime function does not necessarily increase
        # between subsequent messages, because the value wraps to zero if the timer count exceeds the maximum value for a long integer. To calculate time
        # delays between messages, verify that the time of the second message is greater than the time of the first message; then, subtract the time of the
        # first message from the time of the second message.
        device_time = event.Time/1000.0 # convert to sec
        
        hubTime = logged_time

        r= [0,
            0,
            0, #device id
            Computer._getNextEventID(),
            etype,
            device_time,
            logged_time,
            hubTime,
            confidence_interval, 
            delay,
            0, 
            event.DisplayIndex, 
            bstate, 
            bnum,
            event.ActiveButtons,
            px, 
            py,
            0, #scroll_dx not supported
            0, #scroll_x not supported   
            event.Wheel,
            event.WheelAbsolute,  
            Keyboard._modifier_value,                   
            event.Window]    
        return r

    def __del__(self):
        self._user32.ClipCursor(ctypes.byref(self._original_system_cursor_clipping_rect))
        MouseDevice.__del__(self)
