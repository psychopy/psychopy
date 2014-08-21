# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/mouse/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors, please see credits section of documentation.
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""
from .. import Computer, Device
from ... import printExceptionDetailsToStdErr,print2err
from ...constants import EventConstants, DeviceConstants, MouseConstants,KeyboardConstants
import numpy as N
from collections import namedtuple

RectangleBorder=namedtuple('RectangleBorderClass', 'left top right bottom')


currentSec=Computer.currentSec

# OS ' independent' view of the Mouse Device


class MouseDevice(Device):
    """
    The Mouse class represents a standard USB or PS2 mouse device that has up to 
    three buttons and an optional scroll wheel (1D on Windows and Linux, 2D on OSX). 
    
    Mouse position data is mapped to the coordinate space defined in the ioHub 
    configuration file for the Display index specified. If the mouse is on a 
    display other than the PsychoPy full screen window Display, then positional
    data is returned using the OS desktop pixel bounds for the given display.
    
    ..note:: The Mouse device only supports multiple monitor computer setups
            on Windows at this time. Other OS's are supported if only a single
            monitor is attached to the computer, or if the primary monitor
            (monitor index 0) is used for the Full Screen PsychoPy Window.
            
            Essentially, the consideration of the monitor the mouse is currently 
            over is assumed to be index 0 on Linux and OSX and the
            logic for translating Mouse position information assumes that 
            only one monitor is present at this time.
            
    """
    EVENT_CLASS_NAMES=['MouseInputEvent','MouseButtonEvent','MouseScrollEvent',
                       'MouseMoveEvent', 'MouseDragEvent','MouseButtonPressEvent','MouseButtonReleaseEvent',
                       'MouseMultiClickEvent']
                       
    DEVICE_TYPE_ID=DeviceConstants.MOUSE
    DEVICE_TYPE_STRING='MOUSE'

    __slots__=['_lock_mouse_to_display_id','_scrollPositionY','_position','_clipRectsForDisplayID',
               '_lastPosition','_display_index','_last_display_index','_isVisible','activeButtons'
               ]
    def __init__(self,*args,**kwargs):     
        Device.__init__(self,*args,**kwargs)
        self._clipRectsForDisplayID={}
        self._lock_mouse_to_display_id=None
        self._scrollPositionY=0
        self._position=None
        self._lastPosition=0,0
        self._isVisible=0
        self._display_index=None
        self._last_display_index=None
        self.activeButtons={
            MouseConstants.MOUSE_BUTTON_LEFT:0,
            MouseConstants.MOUSE_BUTTON_RIGHT:0,
            MouseConstants.MOUSE_BUTTON_MIDDLE:0,
                            }
        
    def getSystemCursorVisibility(self):
        """
        Returns whether the system cursor is visible when within the physical 
        Display represented by the ioHub Display Device.
        
        Args: 
            None
            
        Returns: 
            bool: True if system cursor is visible when within the ioHub Display Device being used. False otherwise.
        """
        return self._nativeGetSystemCursorVisibility()
 
    def setSystemCursorVisibility(self,v):
        """
        Sets whether the system cursor is visible when within the physical 
        Display represented by the ioHub Display Device.
        
        Args:
            v (bool): True = Make system cursor visible. False = Hide system cursor
        
        Returns:
            (bool): True if system cursor is visible. False otherwise.

        """
        self._nativeSetSystemCursorVisibility(v)
        return self.getSystemCursorVisibility()

    def getCurrentButtonStates(self):
        """
        Returns a list of three booleans, representing the current state of the
        MOUSE_BUTTON_LEFT, MOUSE_BUTTON_MIDDLE, MOUSE_BUTTON_RIGHT ioHub Mouse Device.
        
        Args: 
            None

        Returns:
            (left_pressed, middle_pressed, right_pressed): Each element is True if the associated mouse button is pressed, False otherwise.
        """
        return (self.activeButtons[MouseConstants.MOUSE_BUTTON_LEFT]!=0,
                self.activeButtons[MouseConstants.MOUSE_BUTTON_MIDDLE]!=0,
                self.activeButtons[MouseConstants.MOUSE_BUTTON_RIGHT]!=0)
                

    def lockMouseToDisplayID(self,display_id):
        self._lock_mouse_to_display_id=display_id    
        if display_id is not None:
            if display_id not in self._clipRectsForDisplayID:
                screen=self._display_device.getConfiguration()['runtime_info']              
                if screen:
                    left,top,right,bottom=screen['bounds']
                    clip_rect=RectangleBorder(left,top,right,bottom)
                    native_clip_rect=self._nativeLimitCursorToBoundingRect(clip_rect)
                self._clipRectsForDisplayID[display_id]=native_clip_rect,clip_rect
        else:
            if None not in self._clipRectsForDisplayID:
                left,top,right,bottom=screen['bounds']
                clip_rect=RectangleBorder(left,top,right,bottom)
                native_clip_rect=self._nativeLimitCursorToBoundingRect(clip_rect)
                self._clipRectsForDisplayID[display_id]=native_clip_rect,clip_rect
        return self._clipRectsForDisplayID[display_id][1]

    def getlockedMouseDisplayID(self):
        return self._lock_mouse_to_display_id

    def _initialMousePos(self):
        """
        If getPosition is called prior to any mouse events being received, this
        method gets the current system cursor pos using ctypes.

        Windows only
        TODO: Add OS X and Linux support
        """
        if self._position is None:
            if Computer.system == 'win32':
                import ctypes
                _user32=ctypes.windll.user32
                POINT = ctypes.wintypes.POINT                  
                
                #class POINT(ctypes.Structure):
                #    _fields_ = [ ('x',ctypes.c_long),
                #                 ('y',ctypes.c_long)]
                mpos=POINT()
                ok = _user32.GetCursorPos(ctypes.byref(mpos))
                if ok:
                    self._position = [mpos.x,mpos.y]
                    self._lastPosition = self._position
            else:
                # TODO : Handle OS X and Linux in this case.
                self._position = 0.0,0.0
                self._lastPosition = 0.0,0.0

    def getPosition(self,return_display_index=False):
        """
        Returns the current position of the ioHub Mouse Device. Mouse Position is in display
        coordinate units, with 0,0 being the center of the screen.

        Args: 
            return_display_index: If True, the display index that is associated with the mouse position will also be returned.
            
        Returns:
            tuple: If return_display_index is false (default), return (x,y) position of mouse. If return_display_index is True return ( (x,y), display_index). 
        """
        self._initialMousePos()
        if return_display_index is True:
            return (tuple(self._position), self._display_index)       
        return tuple(self._position)

    def getDisplayIndex(self):
        """
        Returns the current display index of the ioHub Mouse Device. 
        If the display index == the index of the display being used for stimulus
        presentation, then mouse position is in the display's coordinate units.
        If the display index != the index of the display being used for stimulus
        presentation, then mouse position is in OS system mouse ccordinate space.

        Args:
            None
        Returns:
            (int): index of the Display the mouse is over. Display index's range from 0 to N-1, where N is the number of Display's active on the Computer.
        """
        return self._display_index
        
    def getPositionAndDelta(self,return_display_index=False):
        """
        Returns a tuple of tuples, being the current position of the ioHub Mouse Device as an (x,y) tuple,
        and the amount the mouse position changed the last time it was updated (dx,dy).
        Mouse Position and Delta are in display coordinate units.

        Args: 
            None
		
        Returns: 
            tuple: ( (x,y), (dx,dy) ) position of mouse, change in mouse position, both in Display coordinate space.
        """
        try:
            self._initialMousePos()
            cpos=self._position
            lpos=self._lastPosition
            change_x=cpos[0]-lpos[0]
            change_y=cpos[1]-lpos[1]
            if return_display_index is True:        
                return (cpos, (change_x,change_y), self._display_index)       
            return cpos, (change_x,change_y)

        except Exception, e:
            print2err(">>ERROR getPositionAndDelta: "+str(e))
            printExceptionDetailsToStdErr()
            if return_display_index is True:        
                return ((0.0,0.0),(0.0,0.0), self._display_index)       
            return (0.0,0.0),(0.0,0.0)

    def getScroll(self):
        """
        Returns the current vertical scroll value for the mouse. The vertical scroll value changes when the
        scroll wheel on a mouse is moved up or down. The vertical scroll value is in an arbitrary value space
        ranging for -32648 to +32648. Scroll position is initialize to 0 when the experiment starts.
        
        Args: 
            None

        Returns:
            int: current vertical scroll value.
        """
        return self._scrollPositionY


    def setScroll(self,s):
        """
        Sets the current vertical scroll value for the mouse. The vertical scroll value changes when the
        scroll wheel on a mouse is moved up or down. The vertical scroll value is in an
        arbitrary value space ranging for -32648 to +32648. Scroll position is initialize to 0 when
        the experiment starts. This method allows you to change the scroll value to anywhere in the
        valid value range.
        
        Args (int): 
            The scroll position you want to set the vertical scroll to. Should be a number between -32648 to +32648.
                    
        Returns:
            int: current vertical scroll value.
        """
        if isinstance(s, (int, long, float, complex)):
            self._scrollPositionY=s
        return self._scrollPositionY

    def setPosition(self,pos,display_index=None):
        """
        Sets the current position of the ioHub Mouse Device. Mouse position ( pos ) should be specified in
        Display coordinate units, with 0,0 being the center of the screen. If you would like the OS system
        mouse position to also be updated, set updateSystemMousePosition to True (the default). Otherwise,
        set it to False. When the system mouse position is updated, your position ( pos ) is converted
        to the associated screen pixel position expected by the OS.

        Args:
             pos ( (x,y) list or tuple ): The position, in Display coordinate space, to set the mouse position too.
             
             updateSystemMousePosition (bool): True = the OS mouse position will also be updated, False = it will not.
        
        Returns:
            tuple: new (x,y) position of mouse in Display coordinate space.

        """
        if isinstance(pos[0], (int, long, float, complex)) and isinstance(pos[1], (int, long, float, complex)):
            display=self._display_device
            current_display_index=display.getIndex()

            if display_index is None:
                display_index=current_display_index

            if display_index==-1:
                print2err(" !!! Display Index -1 received by mouse.setPosition. !!!")
                print2err(" mouse.setPos did not update mouse pos")
                return self._position
                
            px,py=display._displayCoord2Pixel(pos[0],pos[1],display_index)

            result=self._validateMousePosition((px,py),display_index)
            
            if result !=True:
                px,py=result
            
            mouse_display_index=self.getDisplayIndexForMousePosition((px,py))
            
            if mouse_display_index == -1:
                print2err(" !!! getDisplayIndexForMousePosition returned -1 in mouse.setPosition. !!!")
                print2err(" mouse.setPos did not update mouse pos")
            elif mouse_display_index!=display_index:
                print2err(" !!! requested display_index {0} != mouse_pos_index {1}".format(
                                display_index,mouse_display_index))
                print2err(" mouse.setPos did not update mouse pos")
            else:                    
                self._lastPosition=self._position
                self._position=px,py

                self._last_display_index=self._display_index
                self._display_index=mouse_display_index
            
                self._nativeSetMousePos(px,py)     
                
        return self._position
            
    def getDisplayIndexForMousePosition(self,system_mouse_pos):
        return self._display_device._getDisplayIndexForNativePixelPosition(system_mouse_pos)

    def _validateMousePosition(self, pixel_pos,display_index):
        left,top,right,bottom=self._display_device.getBounds()
        mx,my=pixel_pos
        mousePositionNeedsUpdate=False
        
        if mx < left:
            mx=left
            mousePositionNeedsUpdate=True
        elif mx >= right:
            mx=right-1
            mousePositionNeedsUpdate=True
            
        if my < top:
            my=top
            mousePositionNeedsUpdate=True
        elif my >= bottom:
            my=bottom-1
            mousePositionNeedsUpdate=True
        
        if mousePositionNeedsUpdate: 
            return mx,my
        
        return True

    def _nativeSetMousePos(self,px,py):
        print2err("ERROR: _nativeSetMousePos must be overwritten by OS dependent implementation")

    def _nativeGetSystemCursorVisibility(self):
        print2err("ERROR: _nativeGetSystemCursorVisibility must be overwritten by OS dependent implementation")
        return True
        
    def _nativeSetSystemCursorVisibility(self,v):
        print2err("ERROR: _nativeSetSystemCursorVisibility must be overwritten by OS dependent implementation")
        return True

    def _nativeLimitCursorToBoundingRect(self,clip_rect):
        print2err("ERROR: _nativeLimitCursorToBoundingRect must be overwritten by OS dependent implementation")
        native_clip_rect=None
        return native_clip_rect
        
if Computer.system == 'win32':
    from win32 import Mouse
            
elif Computer.system == 'linux2':
    from linux2 import Mouse

elif Computer.system == 'darwin':
    from darwin import Mouse
   
############# OS Independent Mouse Event Classes ####################

from .. import DeviceEvent

class MouseInputEvent(DeviceEvent):
    """
    The MouseInputEvent is an abstract class that is the parent of all MouseInputEvent types
    that are supported in the ioHub. Mouse position is mapped to the coordinate space
    defined in the ioHub configuration file for the Display.
    """
    PARENT_DEVICE=Mouse
    EVENT_TYPE_STRING='MOUSE_INPUT'
    EVENT_TYPE_ID=EventConstants.MOUSE_INPUT
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    _newDataTypes = [
                     ('display_id',N.uint8),     # gives the display index that the mouse was over for the event.
                     ('button_state',N.uint8),    # 1 if button is pressed, 0 if button is released
                     ('button_id',N.uint8),       # 1, 2,or 4, representing left, right, and middle buttons
                     ('pressed_buttons',N.uint8), # sum of currently active button int values

                     ('x_position',N.int16),    # x position of the position when the event occurred
                     ('y_position',N.int16),    # y position of the position when the event occurred

                     ('scroll_dx', N.int8),  # horizontal scroll wheel position change when the event occurred (OS X only)
                     ('scroll_x', N.int16),  # horizontal scroll wheel abs. position when the event occurred (OS X only)
                     ('scroll_dy', N.int8),  # vertical scroll wheel position change when the event occurred
                     ('scroll_y', N.int16),  # vertical scroll wheel abs. position when the event occurred

                     ('modifiers',N.uint32),  # indicates what modifier keys were active when the mouse event occurred.

                     ('window_id',N.uint64)      # window ID that the mouse was over when the event occurred
                                                # (window does not need to have focus)
                    ]

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        
        #: The id of the display that the mouse was over when the event occurred.
        #: Only supported on Windows at this time. Always 0 on other OS's.
        self.display_id=None        
        
        #: 1 if button is pressed, 0 if button is released
        self.button_state=None

        #: MouseConstants.MOUSE_BUTTON_LEFT, MouseConstants.MOUSE_BUTTON_RIGHT
        #: and MouseConstants.MOUSE_BUTTON_MIDDLE are int constants 
        #: representing left, right, and middle buttons of the mouse.
        self.button_id=None

        #: 'All' currently pressed button id's logically OR'ed together.
        self.pressed_buttons=None

        #: x position of the Mouse when the event occurred; in display coordinate space.
        self.x_position=None

        #: y position of the Mouse when the event occurred; in display coordinate space.
        self.y_position=None
        
        #: Horizontal scroll wheel position change when the event occurred.
        #: OS X Only. Always 0 on other OS's.
        self.scroll_dx=None

        #: Horizontal scroll wheel absolute position when the event occurred.
        #: OS X Only. Always 0 on other OS's.
        self.scroll_x=None

        #: Vertical scroll wheel position change when the event occurred.
        self.scroll_dy=None

        #: Vertical scroll wheel absolute position when the event occurred.
        self.scroll_y=None
        
        #: List of the modifiers that were active when the mouse event occurred,
        #: provided in online events as a list of the modifier constant labels  
        #: specified in iohub.ModifierConstants
        #: list: Empty if no modifiers are pressed, otherwise each elemnt is the string name of a modifier constant.
        self.modifiers=0

        #: Window handle reference that the mouse was over when the event occurred
        #: (window does not need to have focus)
        self.window_id=None

        DeviceEvent.__init__(self, *args, **kwargs)

    @classmethod
    def _convertFields(cls,event_value_list):
        modifier_value_index=cls.CLASS_ATTRIBUTE_NAMES.index('modifiers')
        event_value_list[modifier_value_index]=KeyboardConstants._modifierCodes2Labels(event_value_list[modifier_value_index])
        
    @classmethod
    def createEventAsDict(cls,values):
        cls._convertFields(values)
        return dict(zip(cls.CLASS_ATTRIBUTE_NAMES,values))

    #noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls,valueList):
        cls._convertFields(valueList)
        return cls.namedTupleClass(*valueList)

class MouseMoveEvent(MouseInputEvent):
    """
    MouseMoveEvent's occur when the mouse position changes. Mouse position is
    mapped to the coordinate space defined in the ioHub configuration file 
    for the Display.
    
    Event Type ID: EventConstants.MOUSE_MOVE
    
    Event Type String: 'MOUSE_MOVE'
    """
    EVENT_TYPE_STRING='MOUSE_MOVE'
    EVENT_TYPE_ID=EventConstants.MOUSE_MOVE
    IOHUB_DATA_TABLE=MouseInputEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        MouseInputEvent.__init__(self, *args, **kwargs)

class MouseDragEvent(MouseMoveEvent):
    """
    MouseDragEvents occur when the mouse position changes and at least one mouse
    button is pressed. Mouse position is mapped to the coordinate space defined
    in the ioHub configuration file for the Display.
    
    Event Type ID: EventConstants.MOUSE_DRAG
    
    Event Type String: 'MOUSE_DRAG'
    """
    EVENT_TYPE_STRING='MOUSE_DRAG'
    EVENT_TYPE_ID=EventConstants.MOUSE_DRAG
    IOHUB_DATA_TABLE=MouseMoveEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        MouseMoveEvent.__init__(self, *args, **kwargs)

class MouseScrollEvent(MouseInputEvent):
    """
    MouseScrollEvent's are generated when the scroll wheel on the 
    Mouse Device (if it has one) is moved. Vertical scrolling is supported
    on all operating systems, horizontal scrolling is only supported on OS X.
    
    Each MouseScrollEvent provides the number of units the wheel was turned 
    in each supported dimension, as well as the absolute scroll value for 
    of each supported dimension.

    Event Type ID: EventConstants.MOUSE_SCROLL
    
    Event Type String: 'MOUSE_SCROLL'
    """
    EVENT_TYPE_STRING='MOUSE_SCROLL'
    EVENT_TYPE_ID=EventConstants.MOUSE_SCROLL
    IOHUB_DATA_TABLE=MouseInputEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        """

        :rtype : MouseScrollEvent
        :param args:
        :param kwargs:
        """
        MouseInputEvent.__init__(self, *args, **kwargs)

class MouseButtonEvent(MouseInputEvent):
    EVENT_TYPE_STRING='MOUSE_BUTTON'
    EVENT_TYPE_ID=EventConstants.MOUSE_BUTTON
    IOHUB_DATA_TABLE=MouseInputEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        """

        :rtype : MouseButtonEvent
        :param args:
        :param kwargs:
        """
        MouseInputEvent.__init__(self, *args, **kwargs)

class MouseButtonPressEvent(MouseButtonEvent):
    """
    MouseButtonPressEvent's are created when a button on the mouse is pressed. 
    The button_state of the event will equal MouseConstants.MOUSE_BUTTON_STATE_PRESSED,
    and the button that was pressed (button_id) will be MouseConstants.MOUSE_BUTTON_LEFT,
    MouseConstants.MOUSE_BUTTON_RIGHT, or MouseConstants.MOUSE_BUTTON_MIDDLE, 
    assuming you have a 3 button mouse.

    To get the current state of all three buttons on the Mouse Device, 
    the pressed_buttons attribute can be read, which tracks the state of all three
    mouse buttons as an int that is equal to the sum of any pressed button id's 
    ( MouseConstants.MOUSE_BUTTON_LEFT,  MouseConstants.MOUSE_BUTTON_RIGHT, or
    MouseConstants.MOUSE_BUTTON_MIDDLE ).

    To tell if a given mouse button was depressed when the event occurred, regardless of which
    button triggered the event, you can use the following::

        isButtonPressed = event.pressed_buttons & MouseConstants.MOUSE_BUTTON_xxx == MouseConstants.MOUSE_BUTTON_xxx

    where xxx is LEFT, RIGHT, or MIDDLE.

    For example, if at the time of the event both the left and right mouse buttons
    were in a pressed state::

        buttonToCheck=MouseConstants.MOUSE_BUTTON_RIGHT
        isButtonPressed = event.pressed_buttons & buttonToCheck == buttonToCheck

        print isButtonPressed

        >> True

        buttonToCheck=MouseConstants.MOUSE_BUTTON_LEFT
        isButtonPressed = event.pressed_buttons & buttonToCheck == buttonToCheck

        print isButtonPressed

        >> True

        buttonToCheck=MouseConstants.MOUSE_BUTTON_MIDDLE
        isButtonPressed = event.pressed_buttons & buttonToCheck == buttonToCheck

        print isButtonPressed

        >> False

    Event Type ID: EventConstants.MOUSE_BUTTON_PRESS
    
    Event Type String: 'MOUSE_BUTTON_PRESS'    
    """
    EVENT_TYPE_STRING='MOUSE_BUTTON_PRESS'
    EVENT_TYPE_ID=EventConstants.MOUSE_BUTTON_PRESS
    IOHUB_DATA_TABLE=MouseInputEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        MouseButtonEvent.__init__(self, *args, **kwargs)

class MouseButtonReleaseEvent(MouseButtonEvent):
    """
    MouseButtonUpEvent's are created when a button on the mouse is released. 
    
    The button_state of the event will equal MouseConstants.MOUSE_BUTTON_STATE_RELEASED,
    and the button that was pressed (button_id) will be MouseConstants.MOUSE_BUTTON_LEFT,
    MouseConstants.MOUSE_BUTTON_RIGHT, or MouseConstants.MOUSE_BUTTON_MIDDLE, 
    assuming you have a 3 button mouse.

    Event Type ID: EventConstants.MOUSE_BUTTON_RELEASE
    
    Event Type String: 'MOUSE_BUTTON_RELEASE'    
    """
    EVENT_TYPE_STRING='MOUSE_BUTTON_RELEASE'
    EVENT_TYPE_ID=EventConstants.MOUSE_BUTTON_RELEASE
    IOHUB_DATA_TABLE=MouseInputEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        MouseButtonEvent.__init__(self, *args, **kwargs)

class MouseMultiClickEvent(MouseButtonEvent):
    """
    MouseMultiClickEvent's are created when you rapidly press and release a 
    mouse button two or more times. This event may never get triggered if your 
    OS does not support it. The button that was multi clicked (button_id) 
    will be MouseConstants.MOUSE_BUTTON_LEFT, MouseConstants.MOUSE_BUTTON_RIGHT, 
    or MouseConstants.MOUSE_BUTTON_MIDDLE, assuming you have a 3 button mouse.

    Event Type ID: EventConstants.MOUSE_MULTI_CLICK
    
    Event Type String: 'MOUSE_MULTI_CLICK'    
    """
    EVENT_TYPE_STRING='MOUSE_MULTI_CLICK'
    EVENT_TYPE_ID=EventConstants.MOUSE_MULTI_CLICK
    IOHUB_DATA_TABLE=MouseInputEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        MouseButtonEvent.__init__(self, *args, **kwargs)
