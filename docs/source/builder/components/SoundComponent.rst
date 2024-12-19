.. _soundcomponent:

-------------------------------
Sound Component
-------------------------------

Play recorded files or generated sounds

Categories:
    Stimuli
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _soundcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _soundcomponent-startVal:
Start 
    When the Sound Component should start, see :ref:`startStop`.
    
.. _soundcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _soundcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _soundcomponent-stopVal:
Stop 
    When the Sound Component should stop, see :ref:`startStop`.
    
.. _soundcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _soundcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _soundcomponent-sound:
Sound 
    A sound can be a note name (e.g. A or Bf), a number to specify Hz (e.g. 440) or a filename.
    
.. _soundcomponent-syncScreenRefresh:
Sync start with screen 
    A reaction time to a sound stimulus should be based on when the screen flipped
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _soundcomponent-deviceLabel:
Device label 
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.
    
.. _soundcomponent-speakerIndex:
Speaker 
    What speaker to play this sound on
    
.. _soundcomponent-resample:
Resample 
    If the sample rate of a clip doesn't match the sample rate of the speaker, should we resample it to match?
    
.. _soundcomponent-latencyClass:
Latency/exclusivity mode 
    How should PsychoPy handle latency? Some options will result in other apps being denied access to the speaker while your experiment is running.
    
    Options:
    
    - Shared: Don't take exclusive control over the speaker, so other apps can still use it. Send sounds via the system mixer so that sample rates are all handled, even though this introduces latency.
    - Shared low-latency: Don't take exclusive control over the speaker, so other apps can still use it. Send sounds directly to reduce latency, so sounds will need to match the sample rate of the speaker. **Recommended in most cases - if :ref:`soundcomponent-resample` is checked then sample rates are already handled on load!**
    - Exclusive low-latency: Take exclusive control over the speaker, so other apps can't use it. Send sounds directly to reduce latency, so sounds will need to be the same sample rate as one another, but this can be any sample rate supported by the speaker.
    - Exclusive aggressive low-latency (with fallback): Take exclusive control over the speaker, so other apps can't use it. Send sounds directly to reduce latency, so sounds will need to be the same sample rate as one another, but this can be any sample rate supported by the speaker. Force the system to prioritise resources towards playing sounds on this speaker for absolute minimum latency, but fallback to mode 2 if the system rejects this.
    - Exclusive aggressive low-latency (no fallback): Take exclusive control over the speaker, so other apps can't use it. Send sounds directly to reduce latency, so sounds will need to be the same sample rate as one another, but this can be any sample rate supported by the speaker. Force the system to prioritise resources towards playing sounds on this speaker for absolute minimum latency, and raise an error if the system rejects this.
    
Playback
===============================




.. _soundcomponent-volume:
Volume 
    The volume with which the sound should be played. It's a normalized value between 0 (minimum) 
    and 1 (maximum).
    
.. _soundcomponent-hamming:
Hamming window 
    For tones we can apply a hamming window to prevent 'clicks' that are caused by a sudden onset. This delays onset by roughly 1ms.
    
.. _soundcomponent-stopWithRoutine:
Stop with Routine? 
    Should playback cease when the Routine ends? Untick to continue playing after the Routine has finished.
    
.. _soundcomponent-forceEndRoutine:
Force end of Routine 
    Should the end of the sound cause the end of the Routine (e.g. trial)?
    
Data
===============================

What information about this Component should be saved?


.. _soundcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _soundcomponent-disabled:
Disable Component 
    Disable this Component
    
.. _soundcomponent-validator:
Validate with... 
    Name of the Validator Routine to use to check the timing of this stimulus. Options are generated live, so will vary according to your setup.
    