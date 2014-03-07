# -*- coding: utf-8 -*-
"""
Created on Wed Mar 05 16:47:13 2014

@author: Sol
"""

import time
from psychopy import core
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

io.clearEvents("all")   
tracker.enableEventReporting(True)
     
while not kb.getEvents():   
    core.wait(0.3)    
io.quit()
