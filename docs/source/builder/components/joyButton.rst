.. _joyButtons:

JoyButtons Component
-------------------------------

The JoyButtons component can be used to collect gamepad/joystick button responses from a participant.

By not storing the button number pressed and checking the `forceEndTrial` box it can be used simply to end a :ref:`Routine <Routines>` If no gamepad/joystic is installed the keyboard can be used to simulate button presses by pressing 'ctrl' + 'alt' + digit(0-9).

Parameters
~~~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start : float or integer
    The time that joyButtons should first get checked. See :ref:`startStop` for details.

Stop : float or integer
    When joyButtons should no longer get checked. See :ref:`startStop` for details.

Force end routine :
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the `allowed` buttons is pressed.

Allowed buttons :
    A list of allowed buttons can be specified here, e.g. [0,1,2,3], or the name of a variable holding such a list. If this box is left blank then any button that is pressed will be read. Only `allowed buttons` count as having been pressed; any other button will not be stored and will not force the end of the Routine. Note that button numbers (0, 1, 2, 3, ...), should be separated by commas.

Store :
    Which button press, if any, should be stored; the first to be pressed, the last to be pressed or all that have been pressed. If the button press is to force the end of the trial then this setting is unlikely to be necessary, unless two buttons happen to be pressed in the same video frame. The response time will also be stored if a button press is recorded. This time will be taken from the start of joyButtons checking (e.g. if the joyButtons was initiated 2 seconds into the trial and a button was pressed 3.2s into the trials the response time will be recorded as 1.2s).

Store correct :
    Check this box if you wish to store whether or not this button press was correct. If so then fill in the next box that defines what would constitute a correct answer e.g. 1 or `$corrAns` (note this should not be in inverted commas). This is given as Python code that should return True (1) or False (0). Often this correct answer will be defined in the settings of the :ref:`Loops`.

Advanced Settings
+++++++++++++++++++

Device number : integer
    Which gamepad/joystick device number to use. The first device found is numbered 0.
