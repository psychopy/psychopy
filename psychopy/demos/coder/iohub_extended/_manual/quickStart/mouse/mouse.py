# -*- coding: utf-8 -*-
"""
Created on Mon Apr 29 13:38:36 2013

@author: Sol
"""

import sys

from psychopy import visual, core

from psychopy.iohub import quickStartHubServer, FullScreenWindow


# Create and start the ioHub Server Process, enabling the 
# the default ioHub devices: Keyboard, Mouse, Experiment, and Display.
#
# If you want to use the ioDataStore, an experiment_code and session_code
# must be provided. 
# If you do not want to use the ioDataStore, remove these two kwargs,
# or set them to None. 
# 
# When specifying the experiment code, it should never change within runs of the same
# experiment. 
# However the session code must be unique from experiment run to experiment run
# or an error will occur and the experiment will be aborted.
#
# If you would like to use a psychopy monitor config file, provide it's name 
# in the psychopy_monitor_name kwarg, otherwise remove the arg or set it to None.
# If psychopy_monitor_name is not specified or is None, a default psychopy monitor
# config is used.
#
# All args to quickStartHubServer **must be** kwargs
#
# The function returns an instance of the ioHubClientConnection class (see docs
# for full details), which is the experiment scripts interface to the ioHub
# device and event framework.
#
import random
io=quickStartHubServer(experiment_code="exp_code",session_code="s%d"%(random.randint(1,100000)))
   
# By default, keyboard, mouse, experiment, and display devices are created 
# by the quickStartHubServer function. 
#
# If you would like other devices added, specify each my adding a kwarg to the 
# quickStartHubServer function, where the kwarg is the ioHub Device class name,
# and the kwarg value is the device configuration dictionary for the device.
#
# Any device configuration properties not specified in the device configuration 
# use the device's default value for the configuration property.  See the 
# ioHub Device and DeviceEvent documentation for details. 
#
# The ioHub interface automatically creates a ioHubDeviceView class for each
# device created that is used to access device events or to call other device methods.
# All available devices are accessed via the io.devices attribute.
# 
# Lets create 'shortcuts' to the devices created when the ioHub Server was initialized
# to save a bit of typing later on.
#
myMouse=io.devices.mouse
display=io.devices.display
myKeyboard=io.devices.keyboard

# This is an example of calling an ioHub device method. It looks and functions
# just like it would if you were calling a normal method of a class created in the 
# experiment process. This is all that really matters.
# 
# However, for those interested,  remember that when using ioHub the Devices
# and all device event monitoring and processing is done in a separate
# system process (the ioHub Server Process). When this method is called,
# the ioHub Process is informed of the request, calls the method with any
# provided arguments using the actual MouseDevice instance that exists
# on the ioHub Server Process, and returns the result of the method call to your
# Experiment process script. This all happens without you needing to think about it,
# but it is nice to know what is actually happenning behind the scenes.
#
myMouse.setSystemCursorVisibility(False)

# Currently ioHub supports mapping operating system event positions to a single
# full screen psychopy window (that uses any of the supported psychopy window unit types,
# other than height). Therefore, it is most convenient to create this window using
# the FullScreenWindow utility function, which returns a psychopy window using
# the configuration settings provided when the ioHub Display device was created.
#
# If you provided a valid psychopy_monitor_name when creating the ioHub connection,
# and did not provide Display device configuration settings, then the psychopy monitor
# config specified by psychopy_monitor_name is read and the monitor size and eye to monitor
# distance are used in the ioHub Display device as well. Otherwise the settings provided 
# for the iohub Display device are used and the psychopy monitor config is updated with 
# these display size settings and eye to monitor distance. 
#
myWin = FullScreenWindow(display)

# We will read some of the ioHub Display device settings and store
# them in local variables for future use.
#
# Get the pixel width and height of the Display the full screen Window has been created on.
#
screen_resolution=display.getPixelResolution()
#
# Get the index of the Display. In a single Display configuration, this will always be 0.
# If there are two Displays connected and active on your computer, then possible
# values are 0 or 1, depending on which you told ioHub to create the Display Device for.
# The default is always to use the Display with index 0.
#
display_index=display.getIndex()
#
# Get the Display's full screen window coordinate type (unit type). This is also specified when
# the Display device is created . Coordinate systems match those specified by PsychoPy (excluding 'height').
# The default is 'pix'. 
#
coord_type=display.getCoordinateType()
#
# Get the calculated number of pixels per visual degree in the horizonal (x) dimension of the Display.
#
pixels_per_degree_x=display.getPixelsPerDegree()[0]

# Create some psychopy visual stim. This is identical to how you would do so normally.
# The only consideration is that you currently need to pass the unit type used by the Display
# device to each stim reasource created, as is done here.
#
fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",
pos=(0,0), size=(30,30),color='black', autoLog=False, units=coord_type)

grating = visual.PatchStim(myWin,pos=(300,0),
                               tex="sin",mask="gauss",
                               color=[1.0,0.5,-1.0],
                               size=(150.0,150.0), sf=(0.01,0.0),
                               autoLog=False, units=coord_type)
                   
message = visual.TextStim(myWin,pos=(0.0,-250),alignHoriz='center',
                              alignVert='center',height=40,
                              text='move=mv-spot, left-drag=SF, right-drag=mv-grating, scroll=ori',
                              autoLog=False,wrapWidth=screen_resolution[0]*.9,
                              units=coord_type)

last_wheelPosY=0

# Run the example until the 'q' or 'ESCAPE' key is pressed
#
while True: 
    # Get the current mouse position.
    #
    # Note that this is 'not' the same as getting mouse motion events, 
    # since you are getting the latest position information, and not information about how
    # the mouse has moved since the last time mouse events were accessed.
    # 
    position, posDelta = myMouse.getPositionAndDelta()
    mouse_dX,mouse_dY=posDelta
    
    # Get the current state of each of the Mouse Buttons. True means the button is
    # pressed, False means it is released.
    #
    left_button, middle_button, right_button = myMouse.getCurrentButtonStates()
    
    # If the left button is pressed, change the visual gratings spatial frequency 
    # by the number of pixels the mouse moved in the x dimenstion divided by the 
    # calculated number of pixels per visual degree for x.
    #
    if left_button:
        grating.setSF(mouse_dX/pixels_per_degree_x/20.0, '+')
    #
    # If the right mouse button is pressed, move the grating to the position of the mouse.
    #
    elif right_button:
        grating.setPos(position)
    
    # If no buttons are pressed on the Mouse, move the position of the mouse cursor.
    #
    if True not in (left_button, middle_button, right_button):
        fixSpot.setPos(position)
            
    if sys.platform == 'darwin':
        # On OS X, both x and y mouse wheel events can be detected, assuming the mouse being used
        # supported 2D mouse wheel motion.
        #
        wheelPosX,wheelPosY = myMouse.getScroll()        
    else:
        # On Windows and Linux, only vertical (Y) wheel position is supported.
        #
        wheelPosY = myMouse.getScroll()
    
    # keep track of the wheel position 'delta' since the last frame.
    #
    wheel_dY=wheelPosY-last_wheelPosY
    last_wheelPosY=wheelPosY
    
    # Change the orientation of the visual grating based on any vertical mouse wheel movement.
    #
    grating.setOri(wheel_dY*5, '+')
    
    #
    # Advance 0.05 cycles per frame.
    grating.setPhase(0.05, '+')
    
    # Redraw the stim for this frame.
    #
    fixSpot.draw()
    grating.draw()
    message.draw()
    flip_time=myWin.flip()#redraw the buffer
    
    # For the example, we will print the flip times out to devide events that are printed for each flip.
    print '########### WINDOW REDRAW AT %.6f secs'%(flip_time)
    
    # Handle key presses each frame. Since no event type is being given
    # to the getEvents() method, all KeyboardEvent types will be 
    # returned (KeyboardPressEvent, KeyboardReleaseEvent, KeyboardCharEvent), 
    # and used in this evaluation.
    #
    for event in myKeyboard.getEvents():
        #
        # If the keyboard event reports that the 'q' or 'ESCAPE' key was pressed
        # then exit the example. 
        # Note that specifying the lower case 'q' will only cause the experiment
        # to exit if a lower case q is what was actually pressed (i.e. a 'SHIFT'
        # key modifier was not being pressed and the 'CAPLOCKS' modifier was not 'on').
        # If you want the experiment to exit regardless of whether an upper or lower
        # case letter was pressed, either include both in the list of keys to match
        # , i.e. ['ESCAPE', 'q', 'Q'], or use the string.upper() method, i.e.
        # if event.key.upper() in ['ESCAPE','Q']
        #
        if event.key in ['ESCAPE','q']:
            io.quit()
            core.quit()
        else:
            # For the example, lets print out the keyboard event object, 
            # which will print all the attributes of the KeyBoard event.
            print event
                
    for event in myMouse.getEvents(): 
        # For the example, lets print out the keyboard event object, 
        # which will print all the attributes of the KeyBoard event.
        print event
        
    # Since we are getting events from the two main event generating devices
    # in our experiment, no need to clear anything.
    #
    #io.clearEvents('all')

#
## End of Example
#
