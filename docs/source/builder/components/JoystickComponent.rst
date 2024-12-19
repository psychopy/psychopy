.. _joystickcomponent:

-------------------------------
Joystick Component
-------------------------------

The Joystick component can be used to collect responses from a participant. The coordinates of the joystick location are
given in the same coordinates as the Window, with (0,0) in the centre. Coordinates are correctly scaled for 'norm' and 'height' units.
User defined scaling can be set by updating joystick.xFactor and joystick.yFactor to the desired values.
Joystick.device.getX() and joystick.device.getY() always return 'norm' units. Joystick.getX() and joystick.getY() are scaled by xFactor or yFactor

No cursor is drawn to represent the joystick current position,
but this is easily provided by updating the position of a partially transparent '.png' immage on each screen frame using the joystick coordinates:
joystick.getX() and joystick.getY(). To ensure that the cursor image is drawon on top of other images it should be the last image in the trial.

Joystick Emulation
    If no joystick device is found, the mouse and keyboard are used to emulate a joystick device.
    Joystick position corresponds to mouse position and mouse buttons correspond to joystick buttons (0,1,2).
    Other buttons can be simulated with key chords: 'ctrl' + 'alt' + digit(0..9).

Categories:
    Responses
Works in:
    PsychoPy

Scenarios
-------------------------------

This can be used in various ways. Here are some scenarios (email the list if you have other uses for your joystick):

Use the joystick to record the location of a button press

Use the joystick to control stimulus parameters
    Imagine you want to use your joystick to make your 'patch'_ bigger or smaller and save the final size.
    Call your `joystickComponent`_ 'joystick', set it to save its state at the end of the trial and set the button press to
    end the Routine. Then for the size setting of your Patch stimulus insert `$joystick.getX()` to use the
    x position of the joystick to control the size or `$joystick.getY()` to use the y position.

Tracking the entire path of the joystick during a period


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _joystickcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _joystickcomponent-startVal:
Start
    When the Joystick Component should start, see :ref:`startStop`.
    
.. _joystickcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _joystickcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _joystickcomponent-stopVal:
Stop
    When the Joystick Component should stop, see :ref:`startStop`.
    
.. _joystickcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _joystickcomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _joystickcomponent-forceEndRoutineOnPress:
End Routine on press
    Should a button press force the end of the Routine (e.g end the trial)?
    
    Options:
    
    * never
    
    * any click
    
    * valid click
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _joystickcomponent-deviceNumber:
Device number
    Device number, if you have multiple devices which one do you want (0, 1, 2...)
    
Data
===============================

What information about this Component should be saved?


.. _joystickcomponent-saveJoystickState:
Save joystick state
    How often should the joystick state (x,y,buttons) be stored? On every video frame, every click or just at the end of the Routine?
    
    Options:
    
    * final
    
    * on click
    
    * every frame
    
    * never
    
.. _joystickcomponent-timeRelativeTo:
Time relative to
    What should the values of joystick.time be relative to?
    
    Options:
    
    * joystick onset
    
    * experiment
    
    * routine
    
.. _joystickcomponent-clickable:
Clickable stimuli
    A comma-separated list of your stimulus names that can be "clicked" by the participant. e.g. target, foil
    
.. _joystickcomponent-saveParamsClickable:
Store params for clicked
    The params (e.g. name, text), for which you want to store the current value, for the stimulus that was"clicked" by the joystick. Make sure that all the clickable objects have all these params.
    
.. _joystickcomponent-allowedButtons:
Allowed buttons
    Buttons to be read (blank for any) numbers separated by commas
    
.. _joystickcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _joystickcomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _joystickcomponent-disabled:
Disable Component
    Disable this Component
    
.. seealso::

    API reference for :mod:`~psychopy.hardware.Joystick`
