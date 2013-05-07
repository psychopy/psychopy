# -*- coding: utf-8 -*-
"""
Converted PsychoPy mouse.py demo script to use ioHub package for keyboard and
mouse input.

Inital Version: May 6th, 2013, Sol Simpson
"""
import sys

from psychopy import visual,core
from iohub import launchHubServer 


# launchHubServer is a fucntion that can be used to create an instance of the 
#   ioHub Process within a procedural PsychoPy Script and without the need for
#   external configuration files. It is useful when devices like the Keyboard,
#   Mouse, Display, and Experiment are all that is needed. By default the
#   Display device will use pixel units and display index 0 of a multimonitor setup.
#   The returned 'io' variable gives access to the ioHub Process.
#
io=launchHubServer(experiment_code='mos_evts',psychopy_monitor_name='default')

# Devices that have been created on the ioHub Process and will be monitored
# for events during the experiment can be accessed via the io.devices.* attribute.
#
# save some 'dots' during the trial loop
#
display = io.devices.display
keyboard = io.devices.keyboard
mouse=io.devices.mouse

# Hide the 'system mouse cursor'.
mouse.setSystemCursorVisibility(False)

# Get settings needed to create the PsychoPy full screen window.
#   - display_resolution: the current resolution of diplsay specified by the screen_index.
#       Using this to create your full screen window stops the warniong about the
#       resolution entered does not match the full screen size that PsychoPy will generate.
#   - unit_type: same as PsychoPy units.
#   - screen_index: specifies what Display to use in a multi monitor setup. Default is 0. 
#
display_resolution=display.getPixelResolution()
unit_type=display.getCoordinateType()
screen_index=display.getIndex()

# ioHub currently supports the use of 'one', 'full screen' PsychoPy Window
# for stimulus presentation. Let's create one....
#
window=visual.Window(display_resolution, 
                        units=unit_type,
                        color=[128,128,128], colorSpace='rgb255',
                        fullscr=True, allowGUI=False,
                        screen=screen_index
                        )                 

# Create some psychopy visual stim. This is identical to how you would do so normally.
# The only consideration is that you currently need to pass the unit type used by the Display
# device to each stim reasource created, as is done here.
#
fixSpot = visual.PatchStim(window,tex="none", mask="gauss",
		pos=(0,0), size=(30,30),color='black', autoLog=False, units=unit_type)	
grating = visual.PatchStim(window,pos=(300,0),
						   tex="sin",mask="gauss",
						   color=[1.0,0.5,-1.0],
						   size=(150.0,150.0), sf=(0.01,0.0),
						   autoLog=False, units=unit_type)					   
message = visual.TextStim(window,pos=(0.0,-(display_resolution[1]/2-140)),alignHoriz='center',
						  alignVert='center',height=40,
						  text='move=mv-spot, left-drag=SF, right-drag=mv-grating, scroll=ori',
						  autoLog=False,wrapWidth=display_resolution[0]*.9,
						  units=unit_type)

#
# Get the calculated number of pixels per visual degree 
# in the horizonal (x) dimension of the Display. Used in setSF
#
pixels_per_degree_x=display.getPixelsPerDegree()[0]

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
	position, posDelta = mouse.getPositionAndDelta()		
	mouse_dX,mouse_dY=posDelta

	# Get the current state of each of the Mouse Buttons. True means the button is
	# pressed, False means it is released.
	#
	left_button, middle_button, right_button = mouse.getCurrentButtonStates()
	
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
		wheelPosX,wheelPosY = mouse.getScroll()		
	else:
		# On Windows and Linux, only vertical (Y) wheel position is supported.
		#
		wheelPosY = mouse.getScroll()
	
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
	window.flip()#redraw the buffer

	# Handle key presses each frame. Since no event type is being given
	# to the getEvents() method, all KeyboardEvent types will be 
	# returned (KeyboardPressEvent, KeyboardReleaseEvent, KeyboardCharEvent), 
	# and used in this evaluation.
	#
	for event in keyboard.getEvents():
		#
		# If the keyboard event reports that the 'q' or 'ESCAPE' key was pressed
		# then exit the example. 
           #
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
			
	# Clear out events that were not accessed this frame.
	#
	io.clearEvents()

#
## End of Example
#