# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 18:52:59 2013

@author: isolver
"""

from ctypes import cdll
from . import MouseDevice
from ... import print2err,MouseConstants,printExceptionDetailsToStdErr
from .. import Computer,Keyboard

currentSec=Computer.getTime

class Mouse(MouseDevice):
    """
    The Mouse class and related events represent a standard computer mouse device
    and the events a standard mouse can produce. Mouse position data is mapped to
    the coordinate space defined in the ioHub configuration file for the Display.
    """
    
    _xdll=None
    _xfixsdll=None
    _xdisplay=None
    _xscreen_count=None

    __slots__=['_cursorVisible']
    def __init__(self,*args,**kwargs):          
        MouseDevice.__init__(self,*args,**kwargs['dconfig'])      

        self._cursorVisible=True
        
        if Mouse._xdll is None:
            try:
                Mouse._xdll = cdll.LoadLibrary('libX11.so') 
                Mouse._xdisplay = self._xdll.XOpenDisplay(None) 
                Mouse._xscreen_count = self._xdll.XScreenCount(self._xdisplay)  
                try:
                    # should use linux cmd:
                    # find /usr/lib -name libXfixes.so\*
                    # to find full path to the lib (if it exists)
                    #
                    Mouse._xfixsdll=cdll.LoadLibrary('libXfixes.so')
                except Exception:
                    try:
                        Mouse._xfixsdll=cdll.LoadLibrary('libXfixes.so.3.1.0')
                    except Exception:
                        print2err('ERROR: Mouse._xfixsdll is None. libXfixes.so cound not be found')
            except Exception:
                print2err('ERROR: Mouse._xdll is None. libX11.so cound not be found')
               
        if Mouse._xfixsdll and self._xdll and self._display_device and self._display_device._xwindow is None:
            self._display_device._xwindow= self._xdll.XRootWindow(Mouse._xdisplay, self._display_device.getIndex())

    def _nativeSetMousePos(self,px,py):
        Mouse._xdll.XWarpPointer(Mouse._xdisplay,None,self._display_device._xwindow,0,0,0,0,int(px),int(py)) 
        Mouse._xdll.XFlush(Mouse._xdisplay);   
         
    def _nativeGetSystemCursorVisibility(self):
        return self._cursorVisible
        
    def _nativeSetSystemCursorVisibility(self,v):
        if Mouse._xfixsdll is None:
            print2err("Xfixes DLL could not be loaded. Cursor visiblity support is unavailable.")
            return True
            
        if v is True and self._nativeGetSystemCursorVisibility() is False:
            Mouse._xfixsdll.XFixesShowCursor(Mouse._xdisplay,self._display_device._xwindow)
            Mouse._xfixsdll.XFlush(Mouse._xdisplay)   
            self._cursorVisible=True
        elif v is False and self._nativeGetSystemCursorVisibility() is True:
            Mouse._xfixsdll.XFixesHideCursor(Mouse._xdisplay,self._display_device._xwindow)
            Mouse._xfixsdll.XFlush(Mouse._xdisplay)   
            self._cursorVisible=False
            
        return self._nativeGetSystemCursorVisibility()
          
    def _nativeLimitCursorToBoundingRect(self,clip_rect):
        print2err('WARNING: Mouse._nativeLimitCursorToBoundingRect not implemented on Linux yet.')
        native_clip_rect=None
        return native_clip_rect

                     
    def _nativeEventCallback(self,event):
        try:
            if self.isReportingEvents():
                logged_time=currentSec()                
                event_array=event[0]

                psychowins=self._iohub_server._pyglet_window_hnds
                report_all=self.getConfiguration().get('report_system_wide_events',True)
                if report_all is False and psychowins and event_array[-1] not in psychowins:
                    return True

                event_array[3]=Computer._getNextEventID()
                
                display_index=self._display_device.getIndex()                
                x,y=self._display_device._pixel2DisplayCoord(event_array[15],event_array[16],display_index)  
                event_array[15]=x
                event_array[16]=y
                event_array[-2]=Keyboard._modifier_value
                self._lastPosition=self._position
                self._position=x,y

                self._last_display_index=self._display_index
                self._display_index=display_index

                bstate=event_array[-11]
                bnum=event_array[-10]

                if bnum is not MouseConstants.MOUSE_BUTTON_NONE:
                    self.activeButtons[bnum]= int(bstate==True)
           
                self._scrollPositionY= event_array[-3]

                self._addNativeEventToBuffer(event_array)

                self._last_callback_time=logged_time
        except Exception:
                printExceptionDetailsToStdErr()
        return True
            
    def _getIOHubEventObject(self,native_event_data):
        return native_event_data

    def _close(self):
        if Mouse._xdll:
            if Mouse._xfixsdll and self._nativeGetSystemCursorVisibility() is False:
                Mouse._xfixsdll.XFixesShowCursor(Mouse._xdisplay,self._display_device._xwindow)   
            Mouse._xdll.XCloseDisplay(Mouse._xdisplay)
            Mouse._xdll=None
            Mouse._xfixsdll=None
            Mouse._xdisplay=None
            Mouse._xscreen_count=None
            
            try:
                self._display_device._xwindow=None
            except Exception:
                pass
