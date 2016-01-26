# -*- coding: utf-8 -*-
"""
ioHub
.. file: ioHub/devices/touch/hw/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""
import hw
from ... import printExceptionDetailsToStdErr,print2err
from ...constants import EventConstants, DeviceConstants
from .. import Device
import numpy as N

class TouchDevice(Device):
    """
    The Touch class represents a touch screen input device. 
    
    Touch position data is mapped to the coordinate space defined in the ioHub 
    configuration file for the Display index specified. If the touch device is 
    on a display other than the PsychoPy full screen window Display, then 
    positional data is returned using the OS desktop pixel bounds for the given 
    display.

    Touch Events are generated independantly of other device events, including 
    a mouse device. Therefore touch data can be used in parallel to mouse data.
    """
    EVENT_CLASS_NAMES=['TouchEvent','TouchMoveEvent','TouchPressEvent','TouchReleaseEvent']                       
    DEVICE_TYPE_ID=DeviceConstants.TOUCH
    DEVICE_TYPE_STRING='TOUCH'
    __slots__=['_position','_lastPosition','_display_index']
    def __init__(self,*args,**kwargs):   
        Device.__init__(self,*args,**kwargs['dconfig'])
        self._position=0,0
        self._lastPosition=0,0
        self._display_index=None
        
    def queryDevice(self,query_type, *args):
        """
        Send the underlying touch screen device a query request and return the response.
        """
        pass

    def commandDevice(self,cmd_type, *args):
        """
        Send the underlying touch screen device a command and return the response.
        """
        pass

    def saveConfiguration(self):
        """
        Save current touch device settings and calibration data to the touch device
        hardware.
        """
        pass
   
        
    def restoreConfiguration(self):
        """
        Load touch device settings and calibration data from the touch device
        hardware.
        """
        pass
    
    def initCalibration(self):
        """
        Initialize the calibration mode on the touch device.
        """     
        pass
        
            
    def applyCalibrationData(self,xmin,xmax,ymin,ymax,x1,y1,x2,y2,sx,sy,leftx,uppery,rightx,lowery):
        """
        Apply The data mapping collected for raw touch coordinates to 
        pixel coordinate space.
        """     
        pass
           
    def _pixelToDisplayCoords(self,px,py):
        """
        Converts 0,0,pix_width,pix_height coord space to display device coord space.  
        """
        try:
            dw,dh=self._display_device.getPixelResolution()
            rx=px/float(dw)
            ry=py/float(dh)
            left,top,right,bottom=self._display_device.getCoordBounds()
            w,h=right-left,top-bottom            
            x,y=left+w*rx,bottom+h*(1.0-ry) 
            return x,y
        except Exception:
            print2err("Error During EloDevice._pixelToDisplayCoords:") 
            printExceptionDetailsToStdErr()
            return px,py
                
    def getPosition(self):
        """
        Returns the current position of the ioHub Touch Device. 
        Touch Position is in display coordinate units, with 0,0 being the center
        of the screen.

        Args: 
            None
            
        Returns:
            tuple: If return_display_index is false (default), return (x,y) position of the touch event.
        """      
        return tuple(self._position)
        
    def getPositionAndDelta(self):
        """
        Returns a tuple of tuples, being the current position of the 
        ioHub Touch Device as an (x,y) tuple, and the amount the touch position 
        changed the last time it was updated (dx,dy).
        Touch Position and Delta are in display coordinate units.

        Args: 
            None
		
        Returns: 
            tuple: ( (x,y), (dx,dy) ) position of the touch event, change in touch position, both in Display coordinate space.
        """
        try:
            cpos=self._position
            lpos=self._lastPosition
            change_x=cpos[0]-lpos[0]
            change_y=cpos[1]-lpos[1]
            return cpos, (change_x,change_y)

        except Exception, e:
            print2err(">>ERROR getPositionAndDelta: "+str(e))
            printExceptionDetailsToStdErr()
            return (0.0,0.0),(0.0,0.0)

        
############# OS Independent Mouse Event Classes ####################

from .. import DeviceEvent

class TouchEvent(DeviceEvent):
    """
    The TouchEvent is an abstract class that is the parent of all Touch Event types
    supported by the ioHub. Touch position is mapped to the coordinate space
    defined in the ioHub configuration file for the Display.
    """
    PARENT_DEVICE=TouchDevice
    EVENT_TYPE_STRING='TOUCH'
    EVENT_TYPE_ID=EventConstants.TOUCH
    IOHUB_DATA_TABLE=EVENT_TYPE_STRING

    _newDataTypes = [
                     ('display_id',N.uint8),     # gives the display index that the mouse was over for the event.
                     ('x_position',N.float32),     # x position of the position when the event occurred
                     ('y_position',N.float32),     # y position of the position when the event occurred
                     ('pressure',N.uint8)         # (not supported on all Elo Models)                                                  # level of touch pressure being applied when the event occurred
                    ]

    __slots__=[e[0] for e in _newDataTypes]
    def __init__(self,*args,**kwargs):
        
        #: The id of the display where the touch event occurred.
        self.display_id=None        
        
        #: x position of the Touch Device when the event occurred; in display coordinate space.
        self.x_position=None

        #: y position of the Touch Device when the event occurred; in display coordinate space.
        self.y_position=None
        
        #: Pressure being applied to the Touch Device when the event occurred.
        self.pressure=None

        DeviceEvent.__init__(self,*args,**kwargs)
        
    @classmethod
    def createEventAsDict(cls,values):
        cls._convertFields(values)
        return dict(zip(cls.CLASS_ATTRIBUTE_NAMES,values))

    #noinspection PyUnresolvedReferences
    @classmethod
    def createEventAsNamedTuple(cls,valueList):
        return cls.namedTupleClass(*valueList)

class TouchMoveEvent(TouchEvent):
    """
    TouchMoveEvent's occur when the touch position changes and the finger was
    already applying pressure to the Touch Device in atleast 1 previous event.
    Touch position is mapped to the coordinate space defined in the ioHub 
    configuration file for the Display the Touch Device is associated with.
    
    Event Type ID: EventConstants.TOUCH_MOVE
    
    Event Type String: 'TOUCH_MOVE'
    """
    EVENT_TYPE_STRING='TOUCH_MOVE'
    EVENT_TYPE_ID=EventConstants.TOUCH_MOVE
    IOHUB_DATA_TABLE=TouchEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        TouchEvent.__init__(self, *args, **kwargs)


class TouchPressEvent(TouchEvent):
    """
    TouchPressEvent's are created when the touch device is initially pressed. 

    Event Type ID: EventConstants.TOUCH_PRESS
    
    Event Type String: 'TOUCH_PRESS'    
    """
    EVENT_TYPE_STRING='TOUCH_PRESS'
    EVENT_TYPE_ID=EventConstants.TOUCH_PRESS
    IOHUB_DATA_TABLE=TouchEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        TouchEvent.__init__(self, *args, **kwargs)

class TouchReleaseEvent(TouchEvent):
    """
    TouchReleaseEvent's are created when the finger pressing the Touch Device is
    removed (lifted) from the touch device. 
    
    Event Type ID: EventConstants.TOUCH_RELEASE
    
    Event Type String: 'TOUCH_RELEASE'    
    """
    EVENT_TYPE_STRING='TOUCH_RELEASE'
    EVENT_TYPE_ID=EventConstants.TOUCH_RELEASE
    IOHUB_DATA_TABLE=TouchEvent.IOHUB_DATA_TABLE
    __slots__=[]
    def __init__(self, *args, **kwargs):
        TouchEvent.__init__(self, *args, **kwargs)