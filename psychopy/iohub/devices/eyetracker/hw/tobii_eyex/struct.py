#!/usr/bin/env python

#############################################################################
##
## Authors: Tom Vanasse and Nate Vack
##
## This file provides the c_type python structures necessary to 
## run simple funtions with the Tobii Eyex Engine, as well as some basic
## functions of its own  This file works with the 'TobiiGazeCore64.dll' found 
## here: http://developer.tobii.com/eyex-sdk/.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

from __future__ import print_function
import array 
import os
from ctypes import *
import sys 

TOBIIGAZE_TRACKING_STATUS_NO_EYES_TRACKED = 0
TOBIIGAZE_TRACKING_STATUS_BOTH_EYES_TRACKED = 1
TOBIIGAZE_TRACKING_STATUS_ONLY_LEFT_EYE_TRACKED = 2
TOBIIGAZE_TRACKING_STATUS_ONE_EYE_TRACKED_PROBABLY_LEFT = 3
TOBIIGAZE_TRACKING_STATUS_ONE_EYE_TRACKED_UNKNOWN_WHICH = 4
TOBIIGAZE_TRACKING_STATUS_ONE_EYE_TRACKED_PROBABLY_RIGHT = 5
TOBIIGAZE_TRACKING_STATUS_ONLY_RIGHT_EYE_TRACKED = 6

TOBIIGAZE_MAX_GAZE_DATA_EXTENSIONS = 32


class TobiiDeviceInfo(Structure):
    
    _fields_ =[
        ("serial_number", c_char * 128),
        ("model", c_char * 64),
        ("generation", c_char * 64), ("firmware_version", c_char * 128)
    ]

class UsbDeviceInfo(Structure):
    
    _fields_ =[
        ("serialNumber", c_char * 128),
        ("productName", c_char * 128),
        ("platformType", c_char * 128), 
        ("firmware_version", c_char * 128)
    ]
               
class TobiigazePoint3d(Structure):
    
    _fields_ = [("x", c_double), ("y", c_double), ("z", c_double)]

class TobiigazePoint2d(Structure):
    
    _fields_ = [("x", c_double), ("y", c_double)]

class TobiiGazeDataEye(Structure):
    
    _fields_ = [("eye_position_from_eye_tracker_mm", TobiigazePoint3d),
                ("eye_position_in_track_box_normalized", TobiigazePoint3d),
                ("gaze_point_from_eye_tracker_mm", TobiigazePoint3d),
                ("gaze_point_on_display_normalized", TobiigazePoint3d)
                ]
    
class TobiiGazeData(Structure):
    
    _fields_ = [("timestamp", c_uint64), ("tracking_status", c_uint),
                ("left", TobiiGazeDataEye), 
                ("right", TobiiGazeDataEye)
                ]

class TobiiGazeDataExtension(Structure):
    
    _fields_ = [("column_id", c_uint32), ("data", c_uint8 * 256), 
                ("actual_size", c_uint32)
                ]


class TobiiGazeDataExtensions(Structure):
    _fields_ = [("extensions", 
                 TobiiGazeDataExtension * TOBIIGAZE_MAX_GAZE_DATA_EXTENSIONS), 
                 ("actual_size", c_uint32)
                 ]


