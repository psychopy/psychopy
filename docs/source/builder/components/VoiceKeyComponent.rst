.. VoiceKeyComponent:

-------------------------------
Voice Key Component
-------------------------------

Voice Key: Get input from a microphone as simple true/false values

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
    What kind of voicekey is it? What package/plugin should be used to talk to it?

Microphone
    What microphone device to take volume readings from?

Threshold (0-255)
    Threshold volume (0 for min value in dB range, 255 for max value) above which to register a voicekey response

Decibel range
    What kind of values (dB) would you expect to receive from this device? In other words, how many dB does a threshold of 0 and of 255 correspond to?

Sampling window (s)
    How many seconds to average volume readings across? Bigger windows are less precise, but also less subject to random noise.


Data
===============================

Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).

Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)

Register button press on...
    When should the response be registered? When the sound starts, or when it stops?

Store
    Choose which (if any) responses to store at the end of a trial

Store correct
    Do you want to save the response as correct/incorrect?

Correct answer
    What is the 'correct' response (True/False)? Might be helpful to add a correctAns column and use $correctAns to compare to the response. 


Testing
===============================

Disable Component
    Disable this Component




.. seealso::
	
	API reference for :class:`~psychopy.experiment.components.voicekey`