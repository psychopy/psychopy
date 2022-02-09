# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np
from .....devices import Computer
from .....errors import print2err, printExceptionDetailsToStdErr

getTime = Computer.getTime

try:
    import tobii_research
except Exception:
    # This can happen when it is Sphinx auto-doc loading the file
    printExceptionDetailsToStdErr()

# Tobii Eye Tracker
class TobiiTracker():
    try:
        CALIBRATION_STATUS_SUCCESS = tobii_research.CALIBRATION_STATUS_SUCCESS
    except:
        CALIBRATION_STATUS_SUCCESS = 1
        
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
        Default (standalone test use only) event handler.
        """
        eye_data = args[0]
        print2err('on_eyetracker_data:')
        print2err(eye_data)
        print2err()
        self._last_eye_data = eye_data
        
    def getCurrentEyeTrackerTime(self):
        '''
        Using tobii_research.get_system_time_stamp() as current tracker time.
        TODO: Find out how to accurately get current device time without
              having an event time.
        '''
        return tobii_research.get_system_time_stamp()	

    def getCurrentLocalTobiiTime(self):
        return tobii_research.get_system_time_stamp()	


    def newScreenCalibration(self):
        if self._eyetracker:
            return tobii_research.ScreenBasedCalibration(self._eyetracker)
        
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
