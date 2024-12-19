.. _voicekeycomponent:

-------------------------------
Voice Key Component
-------------------------------

Voice Key: Get input from a microphone as simple true/false values

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


.. _voicekeycomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _voicekeycomponent-startVal:
Start 
    When the Voice Key Component should start, see :ref:`startStop`.
    
.. _voicekeycomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _voicekeycomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _voicekeycomponent-stopVal:
Stop 
    When the Voice Key Component should stop, see :ref:`startStop`.
    
.. _voicekeycomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _voicekeycomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _voicekeycomponent-forceEndRoutine:
Force end of Routine 
    Should a response force the end of the Routine (e.g end the trial)?
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _voicekeycomponent-deviceLabel:
Device label 
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.
    
.. _voicekeycomponent-deviceBackend:
Device backend 
    What kind of voicekey is it? What package/plugin should be used to talk to it?
    
.. _voicekeycomponent-meMicrophone:
Microphone (*if :ref:`voicekeycomponent-devicebackend` is "Microphone"*)
    What microphone device to take volume readings from?
    
.. _voicekeycomponent-meThreshold:
Threshold (0-255) (*if :ref:`voicekeycomponent-devicebackend` is "Microphone"*)
    Threshold volume (0 for min value in dB range, 255 for max value) above which to register a voicekey response
    
.. _voicekeycomponent-meRange:
Decibel range (*if :ref:`voicekeycomponent-devicebackend` is "Microphone"*)
    What kind of values (dB) would you expect to receive from this device? In other words, how many dB does a threshold of 0 and of 255 correspond to?
    
.. _voicekeycomponent-meSamplingWindow:
Sampling window (s) (*if :ref:`voicekeycomponent-devicebackend` is "Microphone"*)
    How many seconds to average volume readings across? Bigger windows are less precise, but also less subject to random noise.
    
Data
===============================

What information about this Component should be saved?


.. _voicekeycomponent-registerOn:
Register button press on... 
    When should the response be registered? When the sound starts, or when it stops?
    
    Options:
    
    * Press
    
    * Release
    
.. _voicekeycomponent-store:
Store 
    Choose which (if any) responses to store at the end of a trial
    
    Options:
    
    * Last response
    
    * First response
    
    * All responses
    
    * Nothing
    
.. _voicekeycomponent-storeCorrect:
Store correct 
    Do you want to save the response as correct/incorrect?
    
.. _voicekeycomponent-correctAns:
Correct answer (*if :ref:`voicekeycomponent-storecorrect` is checked*)
    What is the 'correct' response (True/False)? Might be helpful to add a correctAns column and use $correctAns to compare to the response. 
    
.. _voicekeycomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _voicekeycomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _voicekeycomponent-disabled:
Disable Component 
    Disable this Component
    