.. _keyboardcomponent:

-------------------------------
Keyboard Component
-------------------------------

The Keyboard component can be used to collect responses from a participant. 

By not storing the key press and checking the `forceEndTrial` box it can be used simply to end a :ref:`Routine <Routines>`

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _keyboardcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _keyboardcomponent-startVal:
Start
    When the Keyboard Component should start, see :ref:`startStop`.
    
.. _keyboardcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _keyboardcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _keyboardcomponent-stopVal:
Stop
    When the Keyboard Component should stop, see :ref:`startStop`.
    
.. _keyboardcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _keyboardcomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _keyboardcomponent-forceEndRoutine:
Force end of Routine
    Should a response force the end of the Routine (e.g end the trial)?
    
.. _keyboardcomponent-registerOn:
Register keypress on...
    When should the keypress be registered? As soon as pressed, or when released?
    
    Options:
    
    * press
    
    * release
    
.. _keyboardcomponent-allowedKeys:
Allowed keys
    A list of allowed keys can be specified here, e.g. ['m','z','1','2'], or the name of a variable holding such a list. If this box is left blank then any key that is pressed will be read. Only `allowed keys` count as having been pressed; any other key will not be stored and will not force the end of the Routine. Note that key names (even for number keys) should be given in single quotes, separated by commas. Cursor control keys can be accessed with 'up', 'down', and so on; the space bar is 'space'. To find other special keys, run the Coder Input demo, "what_key.py", press the key, and check the Coder output window. 
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _keyboardcomponent-deviceLabel:
Device label
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.
    
Data
===============================

What information about this Component should be saved?


.. _keyboardcomponent-store:
Store
    Which key press, if any, should be stored; the first to be pressed, the last to be pressed or all that have been pressed. If the key press is to force the end of the trial then this setting is unlikely to be necessary, unless two keys happen to be pressed in the same video frame. The response time will also be stored if a keypress is recorded. This time will be taken from the start of keyboard checking (e.g. if the keyboard was initiated 2 seconds into the trial and a key was pressed 3.2s into the trials the response time will be recorded as 1.2s).
    
    Options:
    
    * last key
    
    * first key
    
    * all keys
    
    * nothing
    
.. _keyboardcomponent-storeCorrect:
Store correct
    Check this box if you wish to store whether or not this key press was correct. If so then fill in the next box that defines what would constitute a correct answer e.g. left, 1 or `$corrAns` (note this should not be in inverted commas). This is given as Python code that should return True (1) or False (0). Often this correct answer will be defined in the settings of the :ref:`Loops`.
    
.. _keyboardcomponent-correctAns:
Correct answer
    What is the 'correct' key? Might be helpful to add a correctAns column and use $correctAns to compare to the key press.
    
.. _keyboardcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _keyboardcomponent-syncScreenRefresh:
Sync timing with screen
    A reaction time to a visual stimulus should be based on when the screen flipped
    
.. _keyboardcomponent-discard previous:
Discard previous
    Do you want to discard all responses occurring before the onset of this Component?
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _keyboardcomponent-disabled:
Disable Component
    Disable this Component
    

.. seealso::

    API reference for :doc:`psychopy.hardware.keyboard>`
