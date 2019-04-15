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
    
import copy
from collections import OrderedDict
import numpy as np
from .....devices import ioDeviceError, Computer
from .....errors import print2err, printExceptionDetailsToStdErr

getTime = Computer.getTime

try:
    import tobii_research
except Exception:
    # This only happens when it is Sphinx auto-doc loading the file
    printExceptionDetailsToStdErr()


# Tobii Eye Tracker and Time Synchronization Services

class TobiiTracker(object):
    LEFT = 0
    RIGHT = 1
    eye_data = OrderedDict(tracker_time_usec=np.NaN,
                           pupil_diameter_mm=np.NaN,
                           gaze_norm=[np.NaN, np.NaN],
                           gaze_mm=[np.NaN, np.NaN, np.NaN],
                           eye_location_norm=[np.NaN, np.NaN, np.NaN],
                           eye_location_mm=[np.NaN, np.NaN, np.NaN],
                           validity_code=np.NaN,
                           status='UNKNOWN',
                           trigger_signal=None)

    def __init__(self, serial_number=None,  model=None):
        
        self._eyetracker = None
        if serial_number or model:
            for et in tobii_research.find_all_eyetrackers():
                if serial_number == et.serial_number:
                    self._eyetracker = et
                    break
                if model == et.model:
                    self._eyetracker = et
                    break
        else:
            self._eyetracker = tobii_research.find_all_eyetrackers()[0]


        if self._eyetracker is None:
            raise RuntimeError('Could not connect to Tobii.')
            
        self._isRecording = False
        self._queue = None#Queue.Queue()


        #if create_sync_manager:
        #    self._eyetracker.events.OnError += self.on_eyetracker_error
        #    self._tobiiClock = TobiiPyClock()
        #    self._getTobiiClockResolution = self._tobiiClock.get_resolution
        #    self._getTobiiClockTime = self._tobiiClock.get_time
        #    self._syncTimeEventDeque = collections.deque(maxlen=32)
        #    self._sync_manager = TobiiPySyncManager(self._tobiiClock,
        #                                            self._eyetracker_info,
        #                                            self._mainloop,
        #                                            self.on_sync_error,
        #                                            self.on_sync_status)


    def on_eyetracker_data(self, *args, **kwargs):
        print2err('on_eyetracker_data:', args, kwargs)
# =============================================================================
#         eye_data_event = args[1]
#         LEFT = self.LEFT
#         RIGHT = self.RIGHT
# 
#         eyes = (copy.deepcopy(self.eye_data), copy.deepcopy(self.eye_data))
# 
#         eyes[LEFT]['validity_code'] = eye_data_event.LeftValidity
#         eyes[RIGHT]['validity_code'] = eye_data_event.RightValidity
#         eyes[LEFT]['tracker_time_usec'] = eye_data_event.Timestamp
#         eyes[RIGHT]['tracker_time_usec'] = eye_data_event.Timestamp
#         if hasattr(eye_data_event, 'TrigSignal'):
#             eyes[LEFT]['trigger_signal'] = eye_data_event.TrigSignal
#             eyes[RIGHT]['trigger_signal'] = eye_data_event.TrigSignal
# 
#         # print "*** lastEyeData.RightGazePoint2D:
#         # ",lastEyeData.RightGazePoint2D.__dict__
#         if eye_data_event.LeftValidity >= 2 and eye_data_event.RightValidity >= 2:
#             # no eye signal
#             eyes[LEFT]['status'] = 'Missing'
#             eyes[RIGHT]['status'] = 'Missing'
# 
#         elif eye_data_event.LeftValidity < 2 and eye_data_event.RightValidity >= 2:
#             # left eye only available
#             eyes[LEFT]['status'] = 'Available'
#             eyes[RIGHT]['status'] = 'Missing'
# 
#             eyes[LEFT]['pupil_diameter_mm'] = eye_data_event.LeftPupil
#             eyes[LEFT]['gaze_norm'][0] = eye_data_event.LeftGazePoint2D.x
#             eyes[LEFT]['gaze_norm'][1] = eye_data_event.LeftGazePoint2D.y
#             eyes[LEFT]['gaze_mm'][0] = eye_data_event.LeftGazePoint3D.x
#             eyes[LEFT]['gaze_mm'][1] = eye_data_event.LeftGazePoint3D.y
#             eyes[LEFT]['gaze_mm'][2] = eye_data_event.LeftGazePoint3D.z
#             eyes[LEFT]['eye_location_norm'][
#                 0] = eye_data_event.LeftEyePosition3DRelative.x
#             eyes[LEFT]['eye_location_norm'][
#                 1] = eye_data_event.LeftEyePosition3DRelative.y
#             eyes[LEFT]['eye_location_norm'][
#                 2] = eye_data_event.LeftEyePosition3DRelative.z
#             eyes[LEFT]['eye_location_mm'][
#                 0] = eye_data_event.LeftEyePosition3D.x
#             eyes[LEFT]['eye_location_mm'][
#                 1] = eye_data_event.LeftEyePosition3D.y
#             eyes[LEFT]['eye_location_mm'][
#                 2] = eye_data_event.LeftEyePosition3D.z
# 
#         elif eye_data_event.LeftValidity >= 2 and eye_data_event.RightValidity < 2:
#             # right eye only available
#             eyes[RIGHT]['status'] = 'Available'
#             eyes[LEFT]['status'] = 'Missing'
# 
#             eyes[RIGHT]['pupil_diameter_mm'] = eye_data_event.RightPupil
#             eyes[RIGHT]['gaze_norm'][0] = eye_data_event.RightGazePoint2D.x
#             eyes[RIGHT]['gaze_norm'][1] = eye_data_event.RightGazePoint2D.y
#             eyes[RIGHT]['gaze_mm'][0] = eye_data_event.RightGazePoint3D.x
#             eyes[RIGHT]['gaze_mm'][1] = eye_data_event.RightGazePoint3D.y
#             eyes[RIGHT]['gaze_mm'][2] = eye_data_event.RightGazePoint3D.z
#             eyes[RIGHT]['eye_location_norm'][
#                 0] = eye_data_event.RightEyePosition3DRelative.x
#             eyes[RIGHT]['eye_location_norm'][
#                 1] = eye_data_event.RightEyePosition3DRelative.y
#             eyes[RIGHT]['eye_location_norm'][
#                 2] = eye_data_event.RightEyePosition3DRelative.z
#             eyes[RIGHT]['eye_location_mm'][
#                 0] = eye_data_event.RightEyePosition3D.x
#             eyes[RIGHT]['eye_location_mm'][
#                 1] = eye_data_event.RightEyePosition3D.y
#             eyes[RIGHT]['eye_location_mm'][
#                 2] = eye_data_event.RightEyePosition3D.z
#         else:
#             # binocular available
#             eyes[RIGHT]['status'] = 'Available'
#             eyes[LEFT]['status'] = 'Available'
# 
#             eyes[LEFT]['pupil_diameter_mm'] = eye_data_event.LeftPupil
#             eyes[LEFT]['gaze_norm'][0] = eye_data_event.LeftGazePoint2D.x
#             eyes[LEFT]['gaze_norm'][1] = eye_data_event.LeftGazePoint2D.y
#             eyes[LEFT]['gaze_mm'][0] = eye_data_event.LeftGazePoint3D.x
#             eyes[LEFT]['gaze_mm'][1] = eye_data_event.LeftGazePoint3D.y
#             eyes[LEFT]['gaze_mm'][2] = eye_data_event.LeftGazePoint3D.z
#             eyes[LEFT]['eye_location_norm'][
#                 0] = eye_data_event.LeftEyePosition3DRelative.x
#             eyes[LEFT]['eye_location_norm'][
#                 1] = eye_data_event.LeftEyePosition3DRelative.y
#             eyes[LEFT]['eye_location_norm'][
#                 2] = eye_data_event.LeftEyePosition3DRelative.z
#             eyes[LEFT]['eye_location_mm'][
#                 0] = eye_data_event.LeftEyePosition3D.x
#             eyes[LEFT]['eye_location_mm'][
#                 1] = eye_data_event.LeftEyePosition3D.y
#             eyes[LEFT]['eye_location_mm'][
#                 2] = eye_data_event.LeftEyePosition3D.z
# 
#             eyes[RIGHT]['pupil_diameter_mm'] = eye_data_event.RightPupil
#             eyes[RIGHT]['gaze_norm'][0] = eye_data_event.RightGazePoint2D.x
#             eyes[RIGHT]['gaze_norm'][1] = eye_data_event.RightGazePoint2D.y
#             eyes[RIGHT]['gaze_mm'][0] = eye_data_event.RightGazePoint3D.x
#             eyes[RIGHT]['gaze_mm'][1] = eye_data_event.RightGazePoint3D.y
#             eyes[RIGHT]['gaze_mm'][2] = eye_data_event.RightGazePoint3D.z
#             eyes[RIGHT]['eye_location_norm'][
#                 0] = eye_data_event.RightEyePosition3DRelative.x
#             eyes[RIGHT]['eye_location_norm'][
#                 1] = eye_data_event.RightEyePosition3DRelative.y
#             eyes[RIGHT]['eye_location_norm'][
#                 2] = eye_data_event.RightEyePosition3DRelative.z
#             eyes[RIGHT]['eye_location_mm'][
#                 0] = eye_data_event.RightEyePosition3D.x
#             eyes[RIGHT]['eye_location_mm'][
#                 1] = eye_data_event.RightEyePosition3D.y
#             eyes[RIGHT]['eye_location_mm'][
#                 2] = eye_data_event.RightEyePosition3D.z
# 
# =============================================================================


    def on_external_framerate_change(self, *args, **kwargs):
        print2err('NOTE: Tobii System Sampling Rate Changed.')
        return False

    def on_head_box_change(self, *args, **kwargs):
        print2err('NOTE: Tobii Head Movement Box Changed.')
        return False

    def getTimeSyncManager(self):
        return self._sync_manager

    def getTimeSyncState(self):
        return self._sync_manager.sync_state()

    def getCurrentEyeTrackerTime(self):
        return self._sync_manager.convert_from_local_to_remote(
            self._getTobiiClockTime())

    def getCurrentLocalTobiiTime(self):
        return self._getTobiiClockTime()

    def getTobiiTimeResolution(self):
        return self._getTobiiClockResolution()

    def getTrackerDetails(self):
        tobiiInfoProperties = [
            'product_id',
            'given_name',
            'model',
            'generation',
            'firmware_version',
            'status']
        tprops = OrderedDict()
        eyetracker_info = self._eyetracker_info
        for tp in tobiiInfoProperties:
            ta = getattr(eyetracker_info, tp)
            if callable(ta):
                ta = ta()
            tprops[tp] = ta
        tprops['factory_info_string'] = str(eyetracker_info.factory_info)
        return tprops

    def getTrackerInfo(self):
        if hasattr(self._eyetracker, 'GetUnitInfo'):
            return self._eyetracker.GetUnitInfo()
        return None

    def startTracking(self, et_data_rx_callback=None):
        if et_data_rx_callback:
            self.on_eyetracker_data = et_data_rx_callback
        
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
        return self._eyetracker.getSamplingRate()

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
        """
        tobii_research format:
            Back Lower Left: (-200.0, -130.0, 750.0)
            Back Lower Right: (200.0, -130.0, 750.0)
            Back Upper Left: (-200.0, 130.0, 750.0)
            Back Upper Right: (200.0, 130.0, 750.0)
            Front Lower Left: (-140.0, -80.0, 450.0)
            Front Lower Right: (140.0, -80.0, 450.0)
            Front Upper Left: (-140.0, 80.0, 450.0)
            Front Upper Right: (140.0, 80.0, 450.0)
        """
        
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

    def setXSeriesPhysicalPlacement(self, upperLeft, upperRight, lowerLeft):
        if self.getTrackerDetails()['generation'] == 'X':
            self._eyetracker.SetXConfiguration(upperLeft,
                                               upperRight,
                                               lowerLeft)
            return True
        return False

    def getEyeTrackerPhysicalPlacement(self):
        etpc = self._eyetracker.GetXConfiguration()
        ll = etpc.LowerLeft
        ul = etpc.UpperLeft
        ur = etpc.UpperRight
        return dict(lowerLeft=(ll.x, ll.y, ll.z),
                    upperLeft=(ul.x, ul.y, ul.z),
                    upperRight=(ur.x, ur.y, ur.z))

    def getAvailableExtensions(self):
        return [
            OrderedDict(
                name=e.Name,
                extensionId=e.ExtensionId,
                protocolVersion=e.ProtocolVersion,
                realm=e.Realm) for e in self._eyetracker.GetAvailableExtensions()]

    def getEnabledExtensions(self):
        return [
            OrderedDict(
                name=e.Name,
                extensionId=e.ExtensionId,
                protocolVersion=e.ProtocolVersion,
                realm=e.Realm) for e in self._eyetracker.GetEnabledExtensions()]

    def enableExtension(self, extension):
        extension_id = extension
        if isinstance(extension, OrderedDict):
            extension_id = extension['extensionId']
        self._eyetracker.EnableExtension(extension_id)

    def disconnect(self):
        if self._isRecording:
            self.stopTracking()
        self._eyetracker = None

