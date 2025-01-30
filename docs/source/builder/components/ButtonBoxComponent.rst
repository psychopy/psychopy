.. _buttonboxcomponent:

-------------------------------
Button Box Component
-------------------------------

Button Box: Get input from a button box

Categories:
    Responses
Works in:
    PsychoPy

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _buttonboxcomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _buttonboxcomponent-startVal:
Start
    When the Button Box Component should start, see :ref:`startStop`.
    
.. _buttonboxcomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _buttonboxcomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _buttonboxcomponent-stopVal:
Stop
    When the Button Box Component should stop, see :ref:`startStop`.
    
.. _buttonboxcomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _buttonboxcomponent-stopType:
Stop type
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _buttonboxcomponent-forceEndRoutine:
Force end of Routine
    Should a response force the end of the Routine (e.g end the trial)?
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _buttonboxcomponent-deviceLabel:
Device label
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.
    
.. _buttonboxcomponent-deviceBackend:
Device backend
    What kind of button box is it? What package/plugin should be used to talk to it?
    
.. _buttonboxcomponent-kbButtonAliases:
Buttons
    Keys to treat as buttons (in order of what button index you want them to be). Must be the same length as the number of buttons.
    
Data
===============================

What information about this Component should be saved?


.. _buttonboxcomponent-registerOn:
Register button press on...
    When should the button press be registered? As soon as pressed, or when released?
    
    Options:
    
    * Press
    
    * Release
    
.. _buttonboxcomponent-store:
Store
    Choose which (if any) responses to store at the end of a trial
    
    Options:
    
    * Last button
    
    * First button
    
    * All buttons
    
    * Nothing
    
.. _buttonboxcomponent-allowedButtons:
Allowed buttons
    A comma-separated list of button indices (should be whole numbers), leave blank to listen for all buttons.
    
.. _buttonboxcomponent-storeCorrect:
Store correct
    Do you want to save the response as correct/incorrect?
    
.. _buttonboxcomponent-correctAns:
Correct answer
    What is the 'correct' key? Might be helpful to add a correctAns column and use $correctAns to compare to the key press. 
    
.. _buttonboxcomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _buttonboxcomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _buttonboxcomponent-disabled:
Disable Component
    Disable this Component
    