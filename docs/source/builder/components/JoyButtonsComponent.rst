.. _joybuttonscomponent:

-------------------------------
Joy Buttons Component
-------------------------------

The JoyButtons component can be used to collect gamepad/joystick button responses from a participant.

By not storing the button number pressed and checking the `forceEndTrial` box it can be used simply to end a :ref:`Routine <Routines>` If no gamepad/joystic is installed the keyboard can be used to simulate button presses by pressing 'ctrl' + 'alt' + digit(0-9).

Categories:
    Responses
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _joybuttonscomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _joybuttonscomponent-startVal:
Start
    When the Joy Buttons Component should start, see :ref:`startStop`.
    
.. _joybuttonscomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _joybuttonscomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _joybuttonscomponent-stopVal:
Stop
    When the Joy Buttons Component should stop, see :ref:`startStop`.
    
.. _joybuttonscomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _joybuttonscomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _joybuttonscomponent-forceEndRoutine:
Force end of Routine
    Should an `allowed` response force the end of the Routine (e.g end the trial)?
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _joybuttonscomponent-deviceNumber:
Device number
    Device number, if you have multiple devices which one do you want (0, 1, 2...)
    
Data
===============================

What information about this Component should be saved?


.. _joybuttonscomponent-allowedKeys:
Allowed buttons
    A list of allowed buttons can be specified here, e.g. [0,1,2,3], or the name of a variable holding such a list. If this box is left blank then any button that is pressed will be read. Only `allowed buttons` count as having been pressed; any other button will not be stored and will not force the end of the Routine. Note that button numbers (0, 1, 2, 3, ...), should be separated by commas.
    
.. _joybuttonscomponent-store:
Store
    Choose which (if any) responses to store at the end of a trial. If the button press is to force the end of the trial then this setting is unlikely to be necessary, unless two buttons happen to be pressed in the same video frame. The response time will also be stored if a button press is recorded. This time will be taken from the start of joyButtons checking (e.g. if the joyButtons was initiated 2 seconds into the trial and a button was pressed 3.2s into the trials the response time will be recorded as 1.2s).
    
    Options:
    
    * last key
    
    * first key
    
    * all keys
    
    * nothing
    
.. _joybuttonscomponent-storeCorrect:
Store correct
    Check this box if you wish to store whether or not this button press was correct. If so then fill in the next box that defines what would constitute a correct answer e.g. 1 or `$corrAns` (note this should not be in inverted commas). This is given as Python code that should return True (1) or False (0). Often this correct answer will be defined in the settings of the :ref:`Loops`.
    
.. _joybuttonscomponent-correctAns:
Correct answer
    What is the 'correct' key? Might be helpful to add a correctAns column and use $correctAns to compare to the key press.
    
.. _joybuttonscomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _joybuttonscomponent-syncScreenRefresh:
Sync RT with screen
    A reaction time to a visual stimulus should be based on when the screen flipped
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _joybuttonscomponent-disabled:
Disable Component
    Disable this Component
    