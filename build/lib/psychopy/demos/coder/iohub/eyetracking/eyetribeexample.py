# -*- coding: utf-8 -*-
"""
Created on Wed Mar 05 16:47:13 2014

@author: Sol
"""

import time
from psychopy import core, visual
from psychopy.iohub import launchHubServer
    
psychopy_mon_name='testMonitor'
exp_code='gap_endo_que'
sess_code='S_{0}'.format(long(time.mktime(time.localtime())))
#print 'Current Session Code will be: ', sess_code    

iohub_config={
"psychopy_monitor_name":psychopy_mon_name,
"eyetracker.hw.theeyetribe.EyeTracker":{},
"experiment_code":exp_code, 
"session_code":sess_code
}

io=launchHubServer(**iohub_config)

display=io.devices.display
tracker=io.devices.eyetracker
kb=io.devices.keyboard

#print tracker.getConfiguration()
#print 'Display Psychopy Monitor Name: ', display.getPsychopyMonitorName()        
#print 'Display Default Eye Distance: ', display.getDefaultEyeDistance()        
#print 'Display Physical Dimensions: ', display.getPhysicalDimensions()        
#print 'Display Resolution: ', display.getPixelResolution()

res=display.getPixelResolution() # Current pixel resolution of the Display to be used
coord_type=display.getCoordinateType()
window=visual.Window(res,monitor=display.getPsychopyMonitorName(), # name of the PsychoPy Monitor Config file if used.
                            units=coord_type, # coordinate space to use.
                            fullscr=True, # We need full screen mode.
                            allowGUI=False, # We want it to be borderless
                            screen= display.getIndex() # The display index to use, assuming a multi display setup.
                            )

# Create a circle to use for the Gaze Cursor. Current units assume pix.
#
gaze_dot =visual.GratingStim(window,tex=None, mask="gauss",
                             pos=(0,0 ),size=(66,66),color='green',
                                                units=coord_type)


io.clearEvents("all")   
tracker.enableEventReporting(True)
     
while not kb.getEvents():   
    # Get the latest gaze position in display coord space..
    #
    gpos=tracker.getPosition()
    if type(gpos) in [tuple,list]:
        # If we have a gaze position from the tracker,
        # redraw the background image and then the
        # gaze_cursor at the current eye position.
        #
        gaze_dot.setPos([gpos[0],gpos[1]])
        gaze_dot.draw()
    else:
        # Otherwise just draw the background image.
        # This will remove the gaze cursor from the screen
        # when the eye tracker is not successfully
        # tracking eye position.
        #
        window.clearBuffer()

    # Flip video buffers, displaying the stim we just
    # updated.
    #
    flip_time=window.flip()  
    
io.quit()
