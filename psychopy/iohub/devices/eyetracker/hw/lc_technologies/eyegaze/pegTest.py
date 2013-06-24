# -*- coding: utf-8 -*-
import pEyeGaze
from ctypes import byref

def initEyeGaze():
    """
    Function to create the _stEgControl object and init the 
    EyeGaze system. Exits the program if the init fails.
    """
    import sys
    
    eyegaze_control=pEyeGaze._stEgControl()
                            
    eyegaze_control.iNDataSetsInRingBuffer = 32
    eyegaze_control.bTrackingActive = False
    # hardcoding display resolution here; for this example only. ;)
    eyegaze_control.iScreenWidthPix = 1280
    eyegaze_control.iScreenHeightPix = 1024
    eyegaze_control.bEgCameraDisplayActive = False
    eyegaze_control.iEyeImagesScreenPos=1    
    eyegaze_control.iVisionSelect=0; # Set this reserved variable to 0
    eyegaze_control.iCommType = pEyeGaze.EG_COMM_TYPE_LOCAL 

    result=pEyeGaze.EgInit(byref(eyegaze_control))
    if result!=0:
        print "Could not connect to EyeGaze. Error: ",result
        sys.exit(0)
        
    return eyegaze_control
    
def runCalibration(eyegaze_control):
    """
    Function to run the external calibrate.exe program.
    Returns a new instance of _stEgControl (probably not 'necessary').
    """
    import subprocess,time

    result=pEyeGaze.EgExit(byref(eyegaze_control))
    eyegaze_control=None
    
    p = subprocess.Popen(('calibrate.exe', ''))
    while p.poll() is None:
        time.sleep(0.05)

    return initEyeGaze()
    
if __name__ == '__main__':
    import timeit, time
    
    'pEyeGaze Test Started...'
    # initialize the system and get the control object back
    eyegaze_control=initEyeGaze()
    
    # run calibration, getting a new control object back
    # since the calibrate.exe requires us to close and reopen the connection
    eyegaze_control=runCalibration(eyegaze_control)
    
    # start recording
    eyegaze_control.bTrackingActive=True

    
    # For the example, collect 1000+ samples of data
    samples_rx=0
    rec_start=timeit.default_timer()
    MAX_SAMPLES=100
    while samples_rx < MAX_SAMPLES:
        # This is the 'doing something else' part in the example.
        time.sleep(0.005)
        
        # we'll use async. mode, getting avail samples 
        # and then 'do something else'.
        while eyegaze_control.iNPointsAvailable:
             pEyeGaze.EgGetData(byref(eyegaze_control))
             # assume monocular for this example only. ;)
             sample_data0=eyegaze_control.pstEgData[0]
             stime=sample_data0.dGazeTimeSec
             current_time=(pEyeGaze.lct_TimerRead(None)/1000000.0) - pEyeGaze.EgGetApplicationStartTimeSec()
             delay=current_time-stime
             gaze_x=sample_data0.iIGaze
             gaze_y=sample_data0.iJGaze
             print 'Sample Time: {0}\t{1}\t{2}\tX: {3}\tY: {4}\ti: {5}'.format(stime,current_time,delay,gaze_x,gaze_y,samples_rx)
             samples_rx+=1
             if samples_rx > MAX_SAMPLES:
                 break
             
    rec_end=timeit.default_timer()
    
    # stop recording
    eyegaze_control.bTrackingActive=False
       
    # Exit the lcteg system
    result=pEyeGaze.EgInit(byref(eyegaze_control))

    dur=rec_end-rec_start
    print 'Collected {0} samples in {1} seconds. {2} SPS'.format(samples_rx,dur,samples_rx/dur)