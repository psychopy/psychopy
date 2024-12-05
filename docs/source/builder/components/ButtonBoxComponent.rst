.. ButtonBoxComponent:

-------------------------------
Button Box Component
-------------------------------

Button Box: Get input from a button box

Categories:
    Responses
Works in:
    PsychoPy

Parameters
-------------------------------

Basic
===============================

Name
    Name of this Component (alphanumeric or _, no spaces)

Start type
    How do you want to define your start point?

Stop type
    How do you want to define your end point?

Start
    When does the Component start?

Stop
    When does the Component end? (blank is endless)

Expected start (s)
    (Optional) expected start (s), purely for representing in the timeline

Expected duration (s)
    (Optional) expected duration (s), purely for representing in the timeline

Force end of Routine
    Should a response force the end of the Routine (e.g end the trial)?


Device
===============================

Device label
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.

Device backend
    What kind of button box is it? What package/plugin should be used to talk to it?

Buttons
    Keys to treat as buttons (in order of what button index you want them to be). Must be the same length as the number of buttons.


Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Register button press on...
    When should the button press be registered? As soon as pressed, or when released?

Store
    Choose which (if any) responses to store at the end of a trial

Allowed buttons
    A comma-separated list of button indices (should be whole numbers), leave blank to listen for all buttons.

Store correct
    Do you want to save the response as correct/incorrect?

Correct answer
    What is the 'correct' key? Might be helpful to add a correctAns column and use $correctAns to compare to the key press. 


Testing
===============================

Disable Component
    Disable this Component




.. seealso::
	
	API reference for :class:`~psychopy.experiment.components.buttonBox`