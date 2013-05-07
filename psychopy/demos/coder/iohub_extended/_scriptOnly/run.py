"""
ioHub
.. file: ioHub/examples/simpleScriptOnly/run.py

-------------------------------------------------------------------------------

simpleScriptOnly
++++++++++++++++

Overview:
---------

This script is implemented using psychopy and the core ioHubConnection class 
only. It shows how to integrate the ioHub into a PsychoPy script in a minimal
way, without the need to use any of the ioHub's extra features such as automatic 
event storage.

To Run:
-------

1. Ensure you have followed the ioHub installation instructions 
   afound in the ioHub HTML documentation.
2. Open a command prompt to the directory containing this file.
3. Start the test program by running:
   python.exe run.py

"""
from psychopy import visual, core
from psychopy.iohub import Computer, quickStartHubServer,EventConstants,FullScreenWindow, OrderedDict

# PLEASE REMEMBER , THE SCREEN ORIGIN IS ALWAYS IN THE CENTER OF THE SCREEN,
# REGARDLESS OF THE COORDINATE SPACE YOU ARE RUNNING IN. THIS MEANS 0,0 IS SCREEN CENTER,
# -x_min, -y_min is the screen bottom left
# +x_max, +y_max is the screen top right
#

# create and start the ioHub Server Process, enabling the 
# the default ioHub devices: Keyboard, Mouse, and Display.
# The first arg is the experiment code to use for the ioDataStore Event storage,
# the second arg is the session code to give to the current session of the 
# experiment. Session codes must be unique for a given experiment code within an
# ioDataStore hdf5 event file.
import random
io=quickStartHubServer(experiment_code="exp_code",session_code="s%d"%(random.randint(1,1000000)))
        
# By default, keyboard, mouse, experiment, and display devices are created if you 
# do not pass any config info to the ioHubConnection class above.        
mouse=io.devices.mouse
display=io.devices.display
keyboard=io.devices.keyboard
experiment=io.devices.experiment

# Currently ioHub supports mapping event positions to a single full screen
# psychopy window. Therefore, it is most convient to create this window using
# the FullScreenWindow utility function, which returns a psychopy window using
# the configuration settings specified by the ioHub Display device that is the only
# parameter required by the fucntion. 
# If you provided a valid psychopy_monitor_name when creating the ioHub connection,
# and did not provide Display device config. settings, then the psychopy monitor
# config named psychopy_monitor_name is read and the monitor size and eye to monitor
# distance are used in the ioHub Display device.
#
# Otherwise the settings provided for the iohub Display device are used and the psychopy 
# monitor config is updated with these display settings and eye to monitor distance. 
psychoWindow =  FullScreenWindow(display)

# Hide the 'system mouse cursor' so we can display a cool gaussian mask for a mouse cursor.
mouse.setSystemCursorVisibility(False)

# Set the mouse position to 0,0, which means the 'center' of the screen.
mouse.setPosition((0.0,0.0))

# Create an ordered dictionary of psychopy stimuli. An ordered dictionary is 
# one that returns keys in the order they are added, you you can use it to 
# reference stim by a name or by 'zorder'

psychoStim=OrderedDict()

coord_type = display.getCoordinateType()

psychoStim['grating'] = visual.PatchStim(psychoWindow, mask="circle", 
                                        size=75,pos=[-100,0], sf=.075,
                                        units=coord_type)

psychoStim['fixation'] =visual.PatchStim(psychoWindow, size=25, 
                                        pos=[0,0], sf=0,  
                                        color=[-1,-1,-1],
                                        colorSpace='rgb',
                                        units=coord_type)
                                        
psychoStim['mouseDot'] =visual.GratingStim(psychoWindow,tex=None,
                                            mask="gauss", 
                                            pos=mouse.getPosition(),
                                            size=(50,50),color='purple',
                                            units=coord_type)


# Clear all events from the global event buffer, 
# and from the device level event buffers.
io.clearEvents('all')

# Draw the dtim and flip the screen to the updated display graphics
[psychoStim[stimName].draw() for stimName in psychoStim]
psychoWindow.flip()
first_flip_time=Computer.currentSec()

# Get the stimulus display inxed being used, so Mouse events can be filtered by
# the display index in multidisplay configurations. 
display_index=display.getIndex()

QUIT_EXP=False
# Loop until we get a keyboard event with the space, Enter (Return), 
# or Escape key is pressed.
while QUIT_EXP is False:

    # for each loop, update the grating phase
    # advance phase by 0.05 of a cycle
    psychoStim['grating'].setPhase(0.05, '+')

    # and update the mouse contingent gaussian based on the 
    # current mouse location
    mp,di=mouse.getPosition(return_display_index=True)
    if di == display_index:
        psychoStim['mouseDot'].setPos(mp)

    #draw all the stim
    [psychoStim[stimName].draw() for stimName in psychoStim]

    # flip the psychopy window buffers, so the 
    # stim changes you just made get displayed.
    flip_time=psychoWindow.flip()

    # for each new keyboard press event, check if it matches one
    # of the end example keys.
    for k in keyboard.getEvents(EventConstants.KEYBOARD_PRESS):
        if k.key in [' ','RETURN','ESCAPE']:
            print 'Quit key pressed: ',k.key
            QUIT_EXP=True

    io.clearEvents('all')
     
psychoWindow.close()
# be sure to shutdown your ioHub server!
io.quit()
core.quit()
### End of experiment logic

