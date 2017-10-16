======================================
QuickStart Guide for PsychoPy Coders
======================================

.. note::

    This QuickStart Guide gives an easy introduction to using the
    ioHub Event Monitoring Framework with PsychoPy by 'porting'
    an existing PsychoPy demo to use ioHub for device event reporting. 
    
    The full functionality of using the ioHub with PsychoPy in a research setting,
    including a description of all supported devices, is outside the scope of this
    brief introduction. For a more complete review of the ioHub package features and how to use them,
    see the ioHub User Manual section.
    
    Obviously the PsychoPy package API is used heavily, so it is important
    that you have an understanding of how to use PsychoPy at a *coder* level.
    Please refer to the very good `documentation for PsychoPy <http://www.psychopy.org/>`_ 
    if / when needed.
        
Overview
==========

In this section we will introduce ioHub by converting the PsychoPy demo 'mouse.py'
to use the ioHub Event Monitoring Framework using a *script only* approach to
working with ioHub. 

..	note:: The source for the iohub version of the mouse demo can be found in the psychopy demos/coder/iohub_basic folder.

Converting PsychoPy's mouse.py Demo to use ioHub
================================================

First, let's take an example from one of the PsychoPy demo scripts and show how
to easily use the ioHub keyboard and mouse devices with it using psychopy.iohub.launchHubServer.

The original PsychoPy Example (mouse.py taken from a recent version of the 
PsychoPy software installation)::

    from psychopy import visual, core, event

    #create a window to draw in
    myWin = visual.Window((600.0,600.0), allowGUI=True)

    #INITIALISE SOME STIMULI
    fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",
            pos=(0,0), size=(0.05,0.05),color='black', autoLog=False)
    grating = visual.PatchStim(myWin,pos=(0.5,0),
                               tex="sin",mask="gauss",
                               color=[1.0,0.5,-1.0],
                               size=(1.0,1.0), sf=(3,0),
                               autoLog=False)#this stim changes too much for autologging to be useful
    myMouse = event.Mouse(win=myWin)
    message = visual.TextStim(myWin,pos=(-0.95,-0.9),alignHoriz='left',height=0.08,
        text='left-drag=SF, right-drag=pos, scroll=ori',
        autoLog=False)

    while True: #continue until keypress
        #handle key presses each frame
        for key in event.getKeys():
            if key in ['escape','q']:
                core.quit()
                
        #get mouse events
        mouse_dX,mouse_dY = myMouse.getRel()
        mouse1, mouse2, mouse3 = myMouse.getPressed()
        if (mouse1):
            grating.setSF(mouse_dX, '+')
        elif (mouse3):
            grating.setPos([mouse_dX, mouse_dY], '+')
            
        #Handle the wheel(s):
        # Y is the normal mouse wheel, but some (e.g. mighty mouse) have an x as well
        wheel_dX, wheel_dY = myMouse.getWheelRel()
        grating.setOri(wheel_dY*5, '+')
        
        event.clearEvents()#get rid of other, unprocessed events
        
        #do the drawing
        fixSpot.draw()
        grating.setPhase(0.05, '+')#advance 0.05cycles per frame
        grating.draw()
        message.draw()
        myWin.flip()#redraw the buffer
        
Now we take the mouse.py demo above and convert it as literally as possible in order to monitor
the keyboard and mouse device inputs with the ioHub Event Model. Please review the
comments added below the source code, as they explain differences to note when using
ioHub instead of the built in PsychoPy event functionality::

    # -*- coding: utf-8 -*-
    """
    Demo of basic mouse handling from the ioHub (a separate asynchronous process for
    fetching and processing events from hardware; mice, keyboards, eyetrackers).
    """
    import sys

    from psychopy import visual,core
    from psychopy.iohub import launchHubServer

    # create the process that will run in the background polling devices
    io=launchHubServer()

    # some default devices have been created that can now be used
    display = io.devices.display
    keyboard = io.devices.keyboard
    mouse=io.devices.mouse

    # Hide the 'system mouse cursor'.
    mouse.setSystemCursorVisibility(False)

    # We can use display to find info for the Window creation, like the resolution
    # (which means PsychoPy won't warn you that the fullscreen does not match your requested size)
    display_resolution=display.getPixelResolution()

    # ioHub currently supports the use of a single full-screen PsychoPy Window
    window=visual.Window(display_resolution,
                            units='pix',
                            fullscr=True, allowGUI=False,
                            screen=0
                            )

    # Create some psychopy visual stim. This is identical to how you would do so normally.
    fixSpot = visual.PatchStim(window,tex="none", mask="gauss",
                        pos=(0,0), size=(30,30),color='black', autoLog=False)
    grating = visual.PatchStim(window,pos=(300,0),
                        tex="sin",mask="gauss",
                        color=[1.0,0.5,-1.0],
                        size=(150.0,150.0), sf=(0.01,0.0),
                        autoLog=False)
    message = visual.TextStim(window,pos=(0.0,-(display_resolution[1]/2-140)),alignHoriz='center',
                        alignVert='center',height=40,
                        text='move=mv-spot, left-drag=SF, right-drag=mv-grating, scroll=ori',
                        autoLog=False,wrapWidth=display_resolution[0]*.9)

    last_wheelPosY=0

    # Run the example until the 'q' or 'ESCAPE' key is pressed
    #
    while True:
        # Get the current mouse position
        # posDelta is the change in position *since the last call*
        position, posDelta = mouse.getPositionAndDelta()
        mouse_dX,mouse_dY=posDelta

        # Get the current state of each of the Mouse Buttons
        left_button, middle_button, right_button = mouse.getCurrentButtonStates()

        # If the left button is pressed, change the grating's spatial frequency
        if left_button:
            grating.setSF(mouse_dX/5000.0, '+')
        elif right_button:
            grating.setPos(position)

        # If no buttons are pressed on the Mouse, move the position of the mouse cursor.
        if True not in (left_button, middle_button, right_button):
            fixSpot.setPos(position)

        if sys.platform == 'darwin':
            # On macOS, both x and y mouse wheel events can be detected, assuming the mouse being used
            # supported 2D mouse wheel motion.
            wheelPosX,wheelPosY = mouse.getScroll()
        else:
            # On Windows and Linux, only vertical (Y) wheel position is supported.
            wheelPosY = mouse.getScroll()

        # keep track of the wheel position 'delta' since the last frame.
        wheel_dY=wheelPosY-last_wheelPosY
        last_wheelPosY=wheelPosY

        # Change the orientation of the visual grating based on any vertical mouse wheel movement.
        grating.setOri(wheel_dY*5, '+')

        # Advance 0.05 cycles per frame.
        grating.setPhase(0.05, '+')

        # Redraw the stim for this frame.
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
            # Check if we should quit
            # Note that the keyboard events in iohub are case-sensitive (shift-q means "Q")
            if event.key in ['ESCAPE','q']:
                io.quit()
                core.quit()

        # Clear out events that were not accessed this frame.
        io.clearEvents()

    #
    ## End of Example
    #
	
With your experiment file saved, you can run this example by running the python
file script just as you would the original PsychoPy mouse.py demo.