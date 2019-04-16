"""ioHub Common Eye Tracker Interface for Tobii (C) Eye Tracking System."""
from __future__ import print_function
# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

try:
    unicode
except NameError:
    unicode = str

try:
    basestring
except NameError:
    basestring = str

import numpy as np
from .....devices import Computer
from .....errors import print2err, printExceptionDetailsToStdErr

getTime = Computer.getTime

try:
    import tobii_research
except Exception:
    # This only happens when it is Sphinx auto-doc loading the file
    printExceptionDetailsToStdErr()


# Tobii Eye Tracker

class TobiiTracker(object):
    def __init__(self, serial_number=None,  model=None):
        """
        """
        self._eyetracker = None
        retry_count = 10
        trackers = []
        while len(trackers)==0 or retry_count > 0:
            trackers = tobii_research.find_all_eyetrackers()
            retry_count = retry_count - 1

        if len(trackers)==0:
            raise RuntimeError('Could detect any Tobii devices.')
            
        if serial_number or model:
            for et in trackers:
                if serial_number == et.serial_number:
                    self._eyetracker = et
                    break
                if model == et.model:
                    self._eyetracker = et
                    break
        else:
            self._eyetracker = trackers[0]

        if self._eyetracker is None:
            raise RuntimeError('Could not connect to Tobii.')
        
        self._last_eye_data = None
        self._isRecording = False

    def on_eyetracker_data(self, *args, **kwargs):
        """
        {
         'system_time_stamp': 295431587453,
         'device_time_stamp': 1554911175642814,
         'right_gaze_point_on_display_area': (0.6514113545417786, 0.6740643382072449)
         'right_gaze_point_validity': 1,
         'right_pupil_diameter': 2.0828399658203125, 
         'right_pupil_validity': 1, 
         'left_gaze_point_on_display_area': (0.6300967931747437, 0.6632571816444397), 
         'left_gaze_point_validity': 1,
         'left_pupil_diameter': 2.2154541015625, 
         'left_pupil_validity': 1,

         'right_gaze_origin_in_user_coordinate_system': (26.230587005615234, 30.770994186401367, 584.1049194335938), 
         'right_gaze_origin_in_trackbox_coordinate_system': (0.4429018795490265, 0.339368999004364, 0.4470163881778717), 
         'left_gaze_origin_in_trackbox_coordinate_system': (0.6209999918937683, 0.35132133960723877, 0.4568300247192383),
         'right_gaze_origin_validity': 1,
         'right_gaze_point_in_user_coordinate_system': (51.17703628540039, 115.1743392944336, 27.5936222076416),
         'left_gaze_origin_validity': 1, 
         'left_gaze_origin_in_user_coordinate_system': (-33.106361389160156, 26.86952018737793, 587.0490112304688), 
         'left_gaze_point_in_user_coordinate_system': (43.972713470458984, 117.93881225585938, 28.65477752685547), 
         }
        """
        eye_data = args[0]
        print2err('on_eyetracker_data:')
        print2err(eye_data)
        print2err()
        self._last_eye_data = eye_data
        
    def getCurrentEyeTrackerTime(self):
        print2err("TODO: NOT IMPLEMENTED: getCurrentEyeTrackerTime. ")
        return 0.0#tobii_research.get_system_time_stamp()	

    def getCurrentLocalTobiiTime(self):
        return tobii_research.get_system_time_stamp()	


    def startTracking(self, et_data_rx_callback=None):
        if et_data_rx_callback:
            self.on_eyetracker_data = et_data_rx_callback        
        self._last_eye_data = None
        self._eyetracker.subscribe_to(tobii_research.EYETRACKER_GAZE_DATA, 
                                      self.on_eyetracker_data,
                                      as_dictionary=True)        
        self._isRecording = True
        return True

    def stopTracking(self):
        self._eyetracker.unsubscribe_from(tobii_research.EYETRACKER_GAZE_DATA,
                                          self.on_eyetracker_data)
        self._isRecording = False

    def getName(self):
        return self._eyetracker.name

    def setName(self, name):
        try:
            self._eyetracker.set_device_name(name)
        except tobii_research.EyeTrackerFeatureNotSupportedError:
            print2err("This eye tracker doesn't support changing the device name.")
        except tobii_research.EyeTrackerLicenseError:
            print2err("You need a higher level license to change the device name.")

    def setSamplingRate(self, rate):
        if rate in self.getAvailableSamplingRates():
            self._eyetracker.set_gaze_output_frequency(rate)
        return self.getSamplingRate()

    def getAvailableSamplingRates(self):
        return self._eyetracker.get_all_gaze_output_frequencies()

    def getSamplingRate(self):
        return self._eyetracker.get_gaze_output_frequency()

    def getMode(self):
        return self._eyetracker.get_eye_tracking_mode()

    def getAvailableModes(self):
        return self._eyetracker.get_all_eye_tracking_modes()

    def setMode(self, imode):
        cmode = self.getMode()
        try:
            self._eyetracker.set_eye_tracking_mode(imode)
        except:
            self._eyetracker.set_eye_tracking_mode(cmode)

    def getHeadBox(self):
        hb = self._eyetracker.get_track_box()
        if hb:
            bll = hb.back_lower_left
            blr = hb.back_lower_right
            bup = hb.back_upper_left
            bur = hb.back_upper_right
            fll = hb.front_lower_left
            flr = hb.front_lower_right
            ful = hb.front_upper_left
            fur = hb.front_upper_right 

            return np.asarray([
                bll,
                blr,
                bup,
                bur,
                fll,
                flr,
                ful,
                fur
            ])
        return None

    def disconnect(self):
        if self._isRecording:
            self.stopTracking()
        self._eyetracker = None

