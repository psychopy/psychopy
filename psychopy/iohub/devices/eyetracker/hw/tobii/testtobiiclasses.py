# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

"""ioHub Common Eye Tracker Interface for Tobii (C) Eye Tracking System"""

from __future__ import print_function

def printEyeTrackerInfo(tobii_tracker):
    eyetracker = tobii_tracker._eyetracker
    print('\tCreated a Connected Tobii Tracker OK.')
    print('\tDetails:')
    print('\t\tAddress: '+eyetracker.address)
    print('\t\tName: '+eyetracker.device_name)
    print('\t\tModel: '+eyetracker.model)
    print('\t\tSerial Number: '+eyetracker.serial_number)

    et_can = []
    et_cannot = []
    
    if tr.CAPABILITY_CAN_SET_DISPLAY_AREA in eyetracker.device_capabilities:
        et_can.append('Set display area on eye tracker.')
    else:
        et_cannot.append('Set display area on eye tracker.')
    
    if tr.CAPABILITY_HAS_EXTERNAL_SIGNAL in eyetracker.device_capabilities:
        et_can.append("Deliver an external signal stream.")
    else:
        et_cannot.append("Deliver an external signal stream.")
    
    if tr.CAPABILITY_HAS_EYE_IMAGES in eyetracker.device_capabilities:
        et_can.append("Deliver an eye image stream.")
    else:
        et_cannot.append("Deliver an eye image stream.")
     
    if tr.CAPABILITY_HAS_GAZE_DATA in eyetracker.device_capabilities:
        et_can.append("Deliver a gaze data stream.")
    else:
        et_cannot.append("Deliver a gaze data stream.")
    
    if tr.CAPABILITY_HAS_HMD_GAZE_DATA in eyetracker.device_capabilities:
        et_can.append("Deliver a HMD gaze data stream.")
    else:
        et_cannot.append("Deliver a HMD gaze data stream.")
    
    if tr.CAPABILITY_CAN_DO_SCREEN_BASED_CALIBRATION in eyetracker.device_capabilities:
        et_can.append("Screen based calibration.")
    else:
        et_cannot.append("Screen based calibration.")
    
    if tr.CAPABILITY_CAN_DO_MONOCULAR_CALIBRATION in eyetracker.device_capabilities:
        et_can.append("Monocular calibration.")
    else:
        et_cannot.append("Monocular calibration.")
    
    if tr.CAPABILITY_CAN_DO_HMD_BASED_CALIBRATION in eyetracker.device_capabilities:
        et_can.append("HMD screen based calibration.")
    else:
        et_cannot.append("HMD screen based calibration.")

    if tr.CAPABILITY_HAS_HMD_LENS_CONFIG in eyetracker.device_capabilities:
        et_can.append("get/set the HMD lens configuration.")
    else:
        et_cannot.append("get/set the HMD lens configuration.")
   
    print("Supported Capabilities:")
    for c in et_can:
        print("\t\t"+c)
    print("NOT Supported Capabilities:")
    for c in et_cannot:
        print("\t\t"+c)

    
if __name__ == '__main__':
    from psychopy.iohub.devices.eyetracker.hw.tobii.tobiiclasses import TobiiTracker
    from psychopy.iohub.devices import Computer
    import tobii_research as tr

    getTime = Computer.getTime
    # init global clock manually for test
    from psychopy.clock import MonotonicClock
    Computer.global_clock = MonotonicClock()

    
    print('Test Creating a connected TobiiTracker class, using first available Tobii:')

    tobii_tracker = TobiiTracker()
    
    printEyeTrackerInfo(tobii_tracker)    
    
    # TODO: Add tests for .setMode, .getMode
    
    # TODO: Add tests for .getAvailableSamplingRates, .getSamplingRate, setSamplingRate
    
    # TODO: Add tests for .getName, .setName
    
    # STart Recording Test
    
    tobii_tracker.startTracking()
    
    ctime = getTime()
    while getTime() - ctime < 0.5:
        pass
    
    tobii_tracker.stopTracking()
    
    track_box = tobii_tracker.getHeadBox()#_eyetracker.get_track_box()
    print("track_box", track_box)
 

    #print('')
    #print('Tracker Physical Placement: ', tobii_tracker.getEyeTrackerPhysicalPlacement())

    #print('')
    #print('Tracker Enabled Extensions: ', tobii_tracker.getEnabledExtensions())

    #print('')
    #print('Tracker Available Extensions: ', tobii_tracker.getAvailableExtensions())

    #print('')
    #srates = tobii_tracker.getAvailableSamplingRates()
    #print('Valid Tracker Sampling Rates: ', srates)
    #crate = tobii_tracker.getSamplingRate()
    #print('Current Sampling Rate: ', crate)
    #print('Setting Sampling Rate to ', srates[0])
    #tobii_tracker.setSamplingRate(srates[0])
    #print('Current Sampling Rate Now: ', tobii_tracker.getSamplingRate())
    #print('Setting Sampling Rate back to ', crate)
    #tobii_tracker.setSamplingRate(crate)
    #print('Current Sampling Rate Now: ', tobii_tracker.getSamplingRate())

    #print('')
    #print('Tobii Time Info (20 sec):')
    # give some time for events

    #last_times = None
    #first_call_times = None
    #stime = getTime()
    #while getTime() - stime < 20.0:
    #    print('\tgetTobiiTimeResolution: ', tobii_tracker.getTobiiTimeResolution())
    #    iohub_t = int(getTime() * 1000000.0)
    #    tobii_local_t = tobii_tracker.getCurrentLocalTobiiTime()
    #    tobii_remote_t = tobii_tracker.getCurrentEyeTrackerTime()
    #    tlocal_iohub_dt = tobii_local_t - iohub_t
    #    tremote_iohub_dt = tobii_remote_t - iohub_t
    #    tlocal_tremote_dt = tobii_remote_t - tobii_local_t

    #    if last_times:
    #        print('\tioHub Time in usec (dt): ', iohub_t, iohub_t - last_times[0])
    #        print('\tgetCurrentLocalTobiiTime (dt): ', tobii_local_t, tobii_local_t - last_times[1])
    #        print('\tgetCurrentEyeTrackerTime (dt): ', tobii_remote_t, tobii_remote_t - last_times[2])
    #        print('\tioHub, tobii local, tobii remote Elapsed times:', iohub_t - first_call_times[0], tobii_local_t - first_call_times[1], tobii_remote_t - first_call_times[2])
    #        print('\t---')
    #    else:
    #        first_call_times = (iohub_t, tobii_local_t, tobii_remote_t)
    #    last_times = (iohub_t, tobii_local_t, tobii_remote_t)
    #    time.sleep(0.2)

    #print('')
    #print('Tobii Recording Data (20 sec):')

    #tobii_tracker.startTracking()

    #stime = getTime()
    #while getTime() - stime < 20.0:
    #    time.sleep(0.01)

    #tobii_tracker.stopTracking()

    #tobii_tracker.disconnect()

    print('')
    print('TESTS COMPLETE.')
