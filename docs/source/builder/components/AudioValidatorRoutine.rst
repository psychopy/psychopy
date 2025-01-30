.. _audiovalidatorroutine:

-------------------------------
Audio Validator Routine
-------------------------------

Use a voicekey or microphone to confirm that audio stimuli are presented when they should be.

Categories:
    Validation
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _audiovalidatorroutine-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _audiovalidatorroutine-variability:
Variability (s)
    How much variation from intended presentation times (in seconds) is acceptable?
    
.. _audiovalidatorroutine-report:
On fail...
    What to do when the validation fails. Just log, or stop the script and raise an error?
    
    Options:
    
    * Log warning
    
    * Raise error
    
.. _audiovalidatorroutine-findThreshold:
Find best threshold?
    Run a brief Routine to find the best threshold for the photodiode at experiment start?
    
.. _audiovalidatorroutine-threshold:
Threshold
    Light threshold at which the photodiode should register a positive, units go from 0 (least light) to 255 (most light).
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _audiovalidatorroutine-deviceLabel:
Device name
    A name to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same name here.
    
.. _audiovalidatorroutine-deviceBackend:
Photodiode type
    Type of photodiode to use.
    
.. _audiovalidatorroutine-channel:
Voicekey channel
    If relevant, a channel number attached to the photodiode, to distinguish it from other photodiodes on the same port. Leave blank to use the first photodiode which can detect the Window.
    
.. _audiovalidatorroutine-microphone:
Microphone
    What microphone device to use?
    
.. _audiovalidatorroutine-dbRange:
Decibel range
    Range of possible decibels to expect mic responses to be in, by default (0, 1)
    
.. _audiovalidatorroutine-samplingWindow:
Sampling window
    How long (s) to average samples from the microphone across? Larger sampling windows reduce the chance of random spikes, but also reduce sensitivity.
    
Data
===============================

What information about this Component should be saved?


.. _audiovalidatorroutine-saveValid:
Save validation results
    Save validation results after validating on/offset times for stimuli
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _audiovalidatorroutine-disabled:
Disable Routine
    Disable this Routine
    



.. seealso::
	
	API reference for :class:`~psychopy.experiment.routines.voicekeyValidator`