
"""
ioHub
Eye tracker interface code for Tobii EyeX devices

.. file: ioHub/devices/eyetracker/hw/tobii/eyex_classes.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Dan Fitch <dfitch@wisc.edu>
"""


from __future__ import print_function
import array 
import os
import sys 
import platform
from ctypes import *
from .....constants import EventConstants, EyeTrackerConstants
from .... import Computer
from ..... import print2err

DEBUG = False


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
        ("gaze_point_on_display_normalized", TobiiGazePoint2d),
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



class TobiiEyeXTracker():
    def __init__(self):

        machine = platform.machine()
        WINDOWS_64BIT = sys.maxsize > 2**32

        if WINDOWS_64BIT:
            print2err("Although the Tobii 64-bit driver should work in theory, it is untested inside psychopy")
            self.dll = WinDLL(os.path.dirname(__file__) + '\\TobiiGazeCore64.dll');
            callback_generator = WINFUNCTYPE
        else:
            def tobii_path(key):
                return os.path.join(os.environ[key], "Tobii", "Tobii EyeX", "TobiiGazeCore32.dll")
            p1 = tobii_path("ProgramFiles")
            p2 = tobii_path("ProgramFiles(x86)")
            if os.path.exists(p1):
                self.dll = CDLL(p1);
            elif os.path.exists(p2):
                self.dll = CDLL(p2);
            else:
                raise Exception("TobiiGazeCore32.dll not found")
            callback_generator = CFUNCTYPE


        # NOTE: First arg is return type, was c_int but the C example returns void
        self.gaze_callback_type = callback_generator(None, POINTER(TobiiGazeData), 
                                    POINTER(TobiiGazeDataExtensions),
                                    c_void_p)

        self.async_callback_type = callback_generator(None, c_uint32, c_void_p)

        self.error_callback_type = callback_generator(None, c_uint32, c_void_p)


        url_size = 256
        c_url_size = c_uint32(url_size)

        self.url = create_string_buffer(url_size)
        self.error_code = c_uint32(0)

        self.dll.tobiigaze_get_connected_eye_tracker.argtypes = [c_char_p,c_uint32,POINTER(c_uint32)]
        self.dll.tobiigaze_get_connected_eye_tracker(self.url, c_url_size, None)

        self.eye_tracker = c_void_p(self.dll.tobiigaze_create(self.url, None))
        self.info = TobiiDeviceInfo()
        self.dll.tobiigaze_run_event_loop_on_internal_thread(self.eye_tracker, None, None)

        # TODO: Attempt to register an error callback
        #def self.error_callback(error_code, user_data):
        #    print("ERROR: %s" % error_code.value)

        #self.dll.tobiigaze_register_error_callback(self.eye_tracker, self.error_callback_type(self.error_callback), 0);

        if DEBUG:
            print("Connecting...")

        self.dll.tobiigaze_connect(self.eye_tracker, byref(self.error_code))  
        self.dll.tobiigaze_get_device_info(self.eye_tracker, byref(self.info), byref(self.error_code));

        self._calibrationPoints = []
        self._callbackReferences = []
        self._isConnected = True
        self._start_timestamp = None
        self._mainloop = True
        self._last_usec = Computer.getTime() * 0.000001 

        if DEBUG:
            print("Init complete, status: %s" % self.error_code.value)

        self._isRecording = False

    def isConnected(self):
        return self._isConnected

    def isRecordingEnabled(self):
        return self._isRecording

    def get_gaze_callback(self):
        def func(tobiigaze_gaze_data_ref, tobiigaze_gaze_data_extensions_ref, user_data):
            return tobiigaze_gaze_data_ref.contents

        return func
    

    def startTracking(self, python_function):
        if DEBUG:
            print("Start tracking, status: %s" % self.error_code.value)

        def gaze_callback(tobiigaze_gaze_data_ref, tobiigaze_gaze_data_extensions_ref, user_data):
            python_function(tobiigaze_gaze_data_ref.contents)

        self.gaze_callback = gaze_callback
        self.gaze = self.gaze_callback_type(self.gaze_callback)

        self.dll.tobiigaze_start_tracking(self.eye_tracker, self.gaze, byref(self.error_code), None)

        self._isRecording = True
        
        if DEBUG:
            print("Start tracking finished, status: %s" % self.error_code.value)
        
    def stopTracking(self):
        self.dll.tobiigaze_stop_tracking(self.eye_tracker, byref(self.error_code))
        if self.error_code > 0:
            print("Stop tracking failure: ", self.error_code)

        self._isRecording = False

    def getAvailableSamplingRates(self):
        return [60]

    def setSamplingRate(self, *args):
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def setAvailableSamplingRates(self):
        return EyeTrackerConstants.EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED

    def getCurrentEyeTrackerTime(self):
        # Use hacky last time from event handler
        return self._last_usec

    def getDelayInMicroseconds(self, timestamp, convert_to_sec):
        """
        The Tobii EyeX timestamp starts at a random number of
        microseconds, so we need to track when we started.
        Nothing we can really do about clock drift at this time.
        """
        if self._start_timestamp is None:
            self._start_timestamp = timestamp
            self._start_usec = timestamp * convert_to_sec

        value = self._start_usec + (timestamp - self._start_timestamp)

        self._last_usec = value

        return value

    def disconnect(self):
        self.dll.tobiigaze_break_event_loop(self.eye_tracker)
        self.dll.tobiigaze_disconnect(self.eye_tracker)
        self.dll.tobiigaze_destroy(self.eye_tracker)
        self._isConnected = False
        

    """
    ###############################################################################
    Calibration code to imitate the older API
    Weird because we have to wrap callbacks
    """

    def WrapAsyncCallback(self, callback, name):
        def callback_wrapper(error, data):
            if DEBUG:
                print2err("Got callback for {0}".format(name))
            if error > 0:
                print2err("Got calibration {0} callback error: {1} with data {2}".format(name, error, data))

            if callback == None:
                return 0
            else:
                callback(error, data)

        c = self.async_callback_type(callback_wrapper)
        # Keep a reference to the callback so it doesn't get garbage collected
        self._callbackReferences.append(c)
        return c

    def StartCalibration(self, callback):
        nativeCallback = self.WrapAsyncCallback(callback, "start")
        self.dll.tobiigaze_calibration_start_async(self.eye_tracker, nativeCallback, None)

    def StopCalibration(self, callback):
        nativeCallback = self.WrapAsyncCallback(callback, "stop")
        self.dll.tobiigaze_calibration_stop_async(self.eye_tracker, nativeCallback, None)

    def ClearCalibration(self):
        for p in self._calibrationPoints:
            RemoveCalibrationPoint(p, None)

    def AddCalibrationPoint(self, p, callback):
        # This has to take a calibration point from the other Tobii API and put it into this one
        point = TobiiGazePoint2d()
        point.x = c_double(p.x)
        point.y = c_double(p.y)

        nativeCallback = self.WrapAsyncCallback(callback, "add")
        self._calibrationPoints.append(point)
        self.dll.tobiigaze_calibration_add_point_async(self.eye_tracker, addressof(point), nativeCallback, None)

    def RemoveCalibrationPoint(self, p, callback):
        # This has to take a calibration point from the other Tobii API and put it into this one
        point = TobiiGazePoint2d()
        point.x = c_double(p.x)
        point.y = c_double(p.y)

        # Remove the point from our internal tracking list
        remove_index = -1
        for index, c in enumerate(self._calibrationPoints):
            if c.x == p.x and p.y == c.y:
                remove_index = index
        if remove_index >= 0:
            self._calibrationPoints.pop(remove_index)

        nativeCallback = self.WrapAsyncCallback(callback, "remove")
        self.dll.tobiigaze_calibration_remove_point_async(self.eye_tracker, addressof(point), nativeCallback, None)
        
    def ComputeCalibration(self, callback):
        if DEBUG:
            print2err("Computing calibration")
        nativeCallback = self.WrapAsyncCallback(callback, "compute")
        self.dll.tobiigaze_calibration_compute_and_set_async(self.eye_tracker, nativeCallback, None)

    def GetCalibration(self, callback):
        if DEBUG:
            print2err("Trying to get calibration")

        callback(0, None)

        """
        TODO: Returns error and no data in testing, and there are no examples
        of usage in the API docs and samples, so we can't use this yet,
        but it's not crucial for calibration to complete

        calibration = TobiiGazeCalibration()
        nativeCallback = self.WrapAsyncCallback(callback, "get")
        self.dll.tobiigaze_get_calibration_async(self.eye_tracker, nativeCallback, None)
        """

