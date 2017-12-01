"""ioHub Common Eye Tracker Interface for Tobii (C) Eye Tracking System"""
# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

if __name__ == '__main__':
    import time
    from .tobiiclasses import TobiiTrackerBrowser, TobiiTracker
    from psychopy.iohub.devices import Computer

    getTime = Computer.getTime
    # init global clock manually for test
    from psychopy.clock import MonotonicClock
    Computer.global_clock = MonotonicClock()

    TobiiTrackerBrowser.start()

    print '>> Return first device detected and print details dict: '
    tracker_info = TobiiTrackerBrowser.findDevice()
    if tracker_info:
        print 'Success: ', tracker_info
        print '\tDetails:'
        for k, v in TobiiTrackerBrowser.getTrackerDetails(
                tracker_info.product_id).items():
            print '\t', k, ':', v
    else:
        print 'ERROR: No Tracker Found.'
    print ''

    print '>> Return first Tobii T120 detected: '
    tracker_info = TobiiTrackerBrowser.findDevice(model='Tobii T120')
    if tracker_info:
        print '\tSuccess: ', tracker_info
    else:
        print '\tERROR: No Tracker Found.'
    print ''

    print '>> Return first Tobii T120 with id TT120-206-95100697 detected: '
    tracker_info = TobiiTrackerBrowser.findDevice(
        model='Tobii T120', product_id='TT120-206-95100697')
    if tracker_info:
        print '\tSuccess: ', tracker_info
    else:
        print '\tERROR: No Tracker Found.'
    print ''

    print '>> Return Tobii with product id 12345678 detected (should always fail): '
    tracker_info = TobiiTrackerBrowser.findDevice(product_id='1234567')
    if tracker_info:
        print '\tSuccess: ', tracker_info
    else:
        print 'ERROR: No Tracker Found.'

    TobiiTrackerBrowser.stop()

    print '###################################'
    print ''

    print 'Test Creating a connected TobiiTracker class, using first available Tobii:'

    tobii_tracker = TobiiTracker()
    print '\tCreated a Connected Tobii Tracker OK.'
    print '\tDetails:'
    for k, v in tobii_tracker.getTrackerDetails().items():
        print '\t\t{0}  {1}'.format(k, v)

    print ''
    print 'Tracker Name: ', tobii_tracker.getName()
    print 'Set Tracker Name (to "tracker [time]") ...'
    tobii_tracker.setName('tracker %.6f' % getTime())
    print 'Tracker Name now: ', tobii_tracker.getName()

    print ''
    print 'Tracker Low Blink Mode: ', tobii_tracker.getLowBlinkMode()

    print ''
    print 'Tracker Low Blink Mode: ', tobii_tracker.getAvailableIlluminationModes()

    print ''
    imodes = tobii_tracker.getAvailableIlluminationModes()
    print 'Valid Tracker Illumination Modes: ', imodes
    if imodes:
        cimode = tobii_tracker.getIlluminationMode()
        print 'Current Illumination Mode: ', cimode
        print 'Setting Illumination Mode to ', imodes[0]
        tobii_tracker.setIlluminationMode(imodes[0])
        print 'Current Illumination Mode Now: ', tobii_tracker.getIlluminationMode()
        print 'Setting Illumination Mode back to ', cimode
        tobii_tracker.setIlluminationMode(cimode)
        print 'Current Illumination Mode Now: ', tobii_tracker.getIlluminationMode()
    else:
        print 'NOTE: Illumination Mode API features are not supported.'

    print ''
    print 'Tracker Head Movement Box: ', tobii_tracker.getHeadBox()

    print ''
    print 'Tracker Physical Placement: ', tobii_tracker.getEyeTrackerPhysicalPlacement()

    print ''
    print 'Tracker Enabled Extensions: ', tobii_tracker.getEnabledExtensions()

    print ''
    print 'Tracker Available Extensions: ', tobii_tracker.getAvailableExtensions()

    print ''
    srates = tobii_tracker.getAvailableSamplingRates()
    print 'Valid Tracker Sampling Rates: ', srates
    crate = tobii_tracker.getSamplingRate()
    print 'Current Sampling Rate: ', crate
    print 'Setting Sampling Rate to ', srates[0]
    tobii_tracker.setSamplingRate(srates[0])
    print 'Current Sampling Rate Now: ', tobii_tracker.getSamplingRate()
    print 'Setting Sampling Rate back to ', crate
    tobii_tracker.setSamplingRate(crate)
    print 'Current Sampling Rate Now: ', tobii_tracker.getSamplingRate()

    print ''
    print 'Tobii Time Info (20 sec):'
    # give some time for events

    last_times = None
    first_call_times = None
    stime = getTime()
    while getTime() - stime < 20.0:
        print '\tgetTobiiTimeResolution: ', tobii_tracker.getTobiiTimeResolution()
        iohub_t = int(getTime() * 1000000.0)
        tobii_local_t = tobii_tracker.getCurrentLocalTobiiTime()
        tobii_remote_t = tobii_tracker.getCurrentEyeTrackerTime()
        tlocal_iohub_dt = tobii_local_t - iohub_t
        tremote_iohub_dt = tobii_remote_t - iohub_t
        tlocal_tremote_dt = tobii_remote_t - tobii_local_t

        if last_times:
            print '\tioHub Time in usec (dt): ', iohub_t, iohub_t - last_times[0]
            print '\tgetCurrentLocalTobiiTime (dt): ', tobii_local_t, tobii_local_t - last_times[1]
            print '\tgetCurrentEyeTrackerTime (dt): ', tobii_remote_t, tobii_remote_t - last_times[2]
            print '\tioHub, tobii local, tobii remote Elapsed times:', iohub_t - first_call_times[0], tobii_local_t - first_call_times[1], tobii_remote_t - first_call_times[2]
            print '\t---'
        else:
            first_call_times = (iohub_t, tobii_local_t, tobii_remote_t)
        last_times = (iohub_t, tobii_local_t, tobii_remote_t)
        time.sleep(0.2)

    print ''
    print 'Tobii Recording Data (20 sec):'

    tobii_tracker.startTracking()

    stime = getTime()
    while getTime() - stime < 20.0:
        time.sleep(0.01)

    tobii_tracker.stopTracking()

    tobii_tracker.disconnect()

    print ''
    print 'TESTS COMPLETE.'
