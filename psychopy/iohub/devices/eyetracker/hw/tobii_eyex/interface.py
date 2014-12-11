#!/usr/bin/env python

#############################################################################
##
## Authors: Tom Vanasse, Nate Vack, and Dan Fitch
##
## This file provides the c_type python structures necessary to 
## run simple funtions with the Tobii Eyex Engine, as well as some basic
## functions of its own  This file works with the 'TobiiGazeCore64.dll'
## and 'TobiiGazeCore32.dll' (for psychopy, 32-bit only right now) found 
## here: http://developer.tobii.com/eyex-sdk/.
##
## TODO:
##   - Hide more of the innards
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################


from __future__ import print_function
import array 
import os
import sys 
import platform
from struct import *
from ctypes import *

DEBUG = False
    

def error_callback(error_code, user_data):
    print("ERROR: %s" % error_code.value)


class TobiiPythonInterface():
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
        #self.dll.tobiigaze_register_error_callback(self.eye_tracker, self.error_callback_type(error_callback), 0);

        if DEBUG:
            print("Connecting...")

        self.dll.tobiigaze_connect(self.eye_tracker, byref(self.error_code))  
        self.dll.tobiigaze_get_device_info(self.eye_tracker, byref(self.info), byref(self.error_code));

        if DEBUG:
            print("Init complete, status: %s" % self.error_code.value)

        self._isRecording = False


    def get_gaze_callback(self):
        def func(tobiigaze_gaze_data_ref, tobiigaze_gaze_data_extensions_ref, user_data):
            return tobiigaze_gaze_data_ref.contents

        return func
    

    def start_tracking(self, python_function):
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
        
    def stop_tracking(self):
        self.dll.tobiigaze_stop_tracking(self.eye_tracker, byref(self.error_code))

        self._isRecording = False

    def destroy(self):
        self.dll.tobiigaze_break_event_loop(self.eye_tracker)
        self.dll.tobiigaze_disconnect(self.eye_tracker)
        self.dll.tobiigaze_destroy(self.eye_tracker)
        
