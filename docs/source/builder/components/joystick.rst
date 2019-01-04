.. _joystickComponent:

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

Scenarios
~~~~~~~~~~~~~~~~~

This can be used in various ways. Here are some scenarios (email the list if you have other uses for your joystick):

Use the joystick to record the location of a button press

Use the joystick to control stimulus parameters
    Imagine you want to use your joystick to make your 'patch'_ bigger or smaller and save the final size.
    Call your `joystickComponent`_ 'joystick', set it to save its state at the end of the trial and set the button press to
    end the Routine. Then for the size setting of your Patch stimulus insert `$joystick.getX()` to use the
    x position of the joystick to control the size or `$joystick.getY()` to use the y position.

Tracking the entire path of the joystick during a period

Parameters Basic
~~~~~~~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the joystick should first be checked. See :ref:`startStop` for details.

stop :
    When the joystick is no longer checked. See :ref:`startStop` for details.

Force End Routine on Press
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the joystick buttons is pressed.

Save Joystick State
    How often do you need to save the state of the joystick? Every time the subject presses a joystick button, at the end of the trial, or every single frame?
    Note that the text output for cases where you store the joystick data repeatedly per trial
    (e.g. every press or every frame) is likely to be very hard to interpret, so you may then need to analyse your data using the psydat file (with python code) instead.
    Hopefully in future releases the output of the text file will be improved.

Time Relative To
    Whenever the joystick state is saved (e.g. on button press or at end of trial) a time is saved too.
    Do you want this time to be relative to start of the :ref:`Routine <Routines>`, or the start of the whole experiment?

Clickable Stimulus
    A comma-separated list of your stimulus names that 'can be "clicked" by the participant. e.g. target, foil.

Store params for clicked
    The params (e.g. name, text), for which you want to store the current value, for the stimulus that was "clicked" by the joystick.
    Make sure that all the clickable objects have all these params.

Parameters Advanced
~~~~~~~~~~~~~~~~~~~~~

Device Number
    If you have multiple joystick/gamepad devices which one do you want (0, 1, 2, ...).

Allowed Buttons
    Joystick buttons accepted for input (blank for any) numbers separated by 'commas'.

.. seealso::

    API reference for :mod:`~psychopy.hardware.Joystick`
