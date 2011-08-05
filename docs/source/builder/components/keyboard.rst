.. _keyboard:

Keyboard Component
-------------------------------

The Keyboard component can be used to collect responses from a participant. 

By not storing the key press and checking the `forceEndTrial` box it can be used simply to end a :ref:`Routine <Routines>`

Parameters
~~~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no puncuation marks or spaces).

Start : float or integer
    The time that the keyboard should first get checked. See :ref:`startStop` for details.

Stop : 
    When the keyboard is no longer checked. See :ref:`startStop` for details.

Force end routine
    If this box is checked then the :ref:`Routine <Routines>` will end as soon as one of the `allowed` keys is pressed.
	
Allowed keys
    A list of allowed keys can be inserted e.g. ["m","z","1","2"]. If this box is left blank then any keys will be read. Only allowed keys count as having been pressed; any other key will not be stored and will not force the end of the Routine. Note that key names (even for number keys) should be given in inverted commas, as with text parameters. Cursor keys can be accessed with "up", "down", etc. If you leave this empty any key will be allowed.

Store
    Which key press, if any, should be stored; the first to be pressed, the last to be pressed or all that have been pressed. If the key press is to force the end of the trial then this setting is unlikely to be necessary, unless two keys happen to be pressed in the same video frame.

Store response time
    If checked then the response time will also be stored. This time will be taken from the start of keyboard checking.
	
Store correct
    Check this box if you wish to store whether or not this key press was correct. If so then fill in the next box that defines what would consitute a correct answer e.g. left, 1 or `$corrAns` (note this should not be in inverted commas). This is given as Python code that should return True (1) or False (0). Often this correct answer will be defined in the settings of the :ref:`Loops`.
	
Discard previous
	Check this box to ensure that only key presses that occur during this keyboard checking period are used. If this box is not checked a keyboard press that has occured before the start of the checking period will be interpreted as the first keyboard press. For most experiments this box should be checked.
        
.. seealso::
	
	API reference for :mod:`~psychopy.event`
     