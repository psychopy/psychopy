.. AudioValidatorRoutine:

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

Name
    Name of this Routine (alphanumeric or _, no spaces)

Variability (s)
    How much variation from intended presentation times (in seconds) is acceptable?

On fail...
    What to do when the validation fails. Just log, or stop the script and raise an error?

Find best threshold?
    Run a brief Routine to find the best threshold for the photodiode at experiment start?

Threshold
    Light threshold at which the photodiode should register a positive, units go from 0 (least light) to 255 (most light).


Device
===============================

Device name
    A name to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same name here.

Photodiode type
    Type of photodiode to use.

Voicekey channel
    If relevant, a channel number attached to the photodiode, to distinguish it from other photodiodes on the same port. Leave blank to use the first photodiode which can detect the Window.

Microphone
    What microphone device to use?

Decibel range
    Range of possible decibels to expect mic responses to be in, by default (0, 1)

Sampling window
    How long (s) to average samples from the microphone across? Larger sampling windows reduce the chance of random spikes, but also reduce sensitivity.


Data
===============================

Save validation results
    Save validation results after validating on/offset times for stimuli


Testing
===============================

Disable Routine
    Disable this Routine




.. seealso::
	
	API reference for :class:`~psychopy.experiment.routines.voicekeyValidator`