.. _keyboard:

Keyboard
-------------------------------

The Keyboard component can be used to collect responses from a participant. 

By not storing the key press and setting `force end of trial` to be true it can be used simply to end a :ref:`Routine <Routines>`

Parameters
~~~~~~~~~~~~~~

Name
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).

StartTime : float or integer
    The time (relative to the beginning of this Routine) that the keyboard should first be checked.

Duration : float or integer
    The duration for which the keyboard is checked.

Allowed keys
    A list of allowed keys can be inserted e.g. ["m","z","1","2"]. If this box is left blank then any keys will be read. Only allowed keys count as having been pressed; any other key will not be stored and will not force the end of the Routine. Note that key names (even for number keys) should be given in inverted commas, as with text parameters. Cursor keys can be accessed with "up", "down", etc. 

Store
    Which key press, if any, should be stored; the first to be pressed, the last to be pressed or all that have been pressed. If the key press is to force the end of the trial then this setting is unlikely to be necessary, unless two keys happen to be pressed in the same video frame.

Store correct
    Check this box if you wish to store whether or not this key press was correct. If so then fill in the next box that defines what would consitute a correct answer. This is given as Python code that should return True (1) or False (0). Often this correct answer will be defined in the settings of the :ref:`Loops`.

Force end trial
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the `allowed` keys is pressed.

Store response time
    If checked then the response time will also be stored. This time will be taken from the start of keyboard checking.
        
.. seealso::
	
	API reference for :mod:`~psychopy.event`
     