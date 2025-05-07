:orphan:

.. _audiovalidatorroutine:


-------------------------------
Audio Validator Routine
-------------------------------

Use a sound sensor to confirm that audio stimuli are presented when they should be.

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
    
.. _audiovalidatorroutine-findThreshold:

Find best threshold? 
    Run a brief Routine to find the best threshold for the sound sensor at experiment start?
    
.. _audiovalidatorroutine-threshold:

Threshold (*if :ref:`audiovalidatorroutine-findthreshold` isn't ==True*)
    Volume threshold at which the sound sensor should register a positive, units go from 0 (least volume) to 255 (most volume).
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _audiovalidatorroutine-deviceLabel:

Device name 
    A name to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same name here.
    
.. _audiovalidatorroutine-deviceBackend:

Sound sensor type 
    Type of sound sensor to use.
    
.. _audiovalidatorroutine-channel:

Sound sensor channel 
    If relevant, a channel number attached to the sound sensor, to distinguish it from other sound sensors on the same port. Leave blank to use the first sound sensor which can detect the Window.
    
.. _audiovalidatorroutine-microphone:

Microphone 
    What microphone device to use?
    
.. _audiovalidatorroutine-dbRange:

Decibel range (*if :ref:`audiovalidatorroutine-devicebackend` == 'microphone'*)
    Range of possible decibels to expect mic responses to be in, by default (0, 1)
    
.. _audiovalidatorroutine-samplingWindow:

Sampling window (*if :ref:`audiovalidatorroutine-devicebackend` == 'microphone'*)
    How long (s) to average samples from the microphone across? Larger sampling windows reduce the chance of random spikes, but also reduce sensitivity.
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _audiovalidatorroutine-disabled:

Disable Routine 
    Disable this Routine
    