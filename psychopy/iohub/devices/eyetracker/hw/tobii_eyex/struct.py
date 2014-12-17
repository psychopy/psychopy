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

TOBIIGAZE_CALIBRATION_DATA_CAPACITY = 4 * 1024 * 1024

TOBIIGAZE_CALIBRATION_POINT_STATUS_FAILED_OR_INVALID = -1,
TOBIIGAZE_CALIBRATION_POINT_STATUS_VALID_BUT_NOT_USED_IN_CALIBRATION = 0,
TOBIIGAZE_CALIBRATION_POINT_STATUS_VALID_AND_USED_IN_CALIBRATION = 1

class TobiiDeviceInfo(Structure):
    
    _fields_ =[
        ("serial_number", c_char * 128),
        ("model", c_char * 64),
        ("generation", c_char * 64), 
        ("firmware_version", c_char * 128),
    ]

class UsbDeviceInfo(Structure):
    
    _fields_ =[
        ("serialNumber", c_char * 128),
        ("productName", c_char * 128),
        ("platformType", c_char * 128), 
        ("firmware_version", c_char * 128),
    ]
               

class TobiiGazePoint3d(Structure):
    
    _fields_ = [
        ("x", c_double),
        ("y", c_double),
        ("z", c_double),
    ]

class TobiiGazePoint2d(Structure):
    
    _fields_ = [
        ("x", c_double),
        ("y", c_double),
    ]

class TobiiGazePoint2df(Structure):
    
    _fields_ = [
        ("x", c_float),
        ("y", c_float),
    ]


class TobiiGazeRect(Structure):
    
    _fields_ = [
        ("left", c_int32),
        ("top", c_int32),
        ("right", c_int32),
        ("bottom", c_int32),
    ]

class TobiiGazeCalibrationPointData(Structure):

    _fields_ = [
        ("true_position", TobiiGazePoint2df),
        ("left_map_position", TobiiGazePoint2df),
        ("left_status", c_uint), # TOBIIGAZE_CALIBRATION_POINT_STATUS
        ("right_map_position", TobiiGazePoint2df),
        ("left_status", c_uint), # TOBIIGAZE_CALIBRATION_POINT_STATUS
    ]

class TobiiGazeCalibration(Structure):

    _fields_ = [
        # Tobii header says this data array holds null terminated strings
        ("data", c_uint8 * TOBIIGAZE_CALIBRATION_DATA_CAPACITY),
        ("actual_size", c_uint32),
    ]

class TobiiGazeDataEye(Structure):
    
    _fields_ = [
        ("eye_position_from_eye_tracker_mm", TobiiGazePoint3d),
        ("eye_position_in_track_box_normalized", TobiiGazePoint3d),
        ("gaze_point_from_eye_tracker_mm", TobiiGazePoint3d),
        ("gaze_point_on_display_normalized", TobiiGazePoint3d),
    ]
    
class TobiiGazeData(Structure):
    
    _fields_ = [
        ("timestamp", c_uint64),
        ("tracking_status", c_uint), # TOBIIGAZE_TRACKING_STATUS
        ("left", TobiiGazeDataEye), 
        ("right", TobiiGazeDataEye),
    ]

class TobiiGazeDataExtension(Structure):
    
    _fields_ = [
        ("column_id", c_uint32), 
        ("data", c_uint8 * 256), 
        ("actual_size", c_uint32),
    ]


class TobiiGazeDataExtensions(Structure):
    _fields_ = [
        ("extensions", 
        TobiiGazeDataExtension * TOBIIGAZE_MAX_GAZE_DATA_EXTENSIONS), 
        ("actual_size", c_uint32),
    ]


