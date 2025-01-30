.. _photodiodevalidatorroutine:

-------------------------------
Photodiode Validator Routine
-------------------------------

Use a photodiode to confirm that visual stimuli are presented when they should be.

Categories:
    Validation
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _photodiodevalidatorroutine-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _photodiodevalidatorroutine-variability:
Variability (s) 
    How much variation from intended presentation times (in seconds) is acceptable?
    
.. _photodiodevalidatorroutine-report:
On fail... 
    What to do when the validation fails. Just log, or stop the script and raise an error?
    
    Options:
    
    * Log warning
    
    * Raise error
    
.. _photodiodevalidatorroutine-findThreshold:
Find best threshold? 
    Run a brief Routine to find the best threshold for the photodiode at experiment start
    
.. _photodiodevalidatorroutine-threshold:
Threshold (*if :ref:`photodiodevalidatorroutine-findthreshold` isn't checked*)
    Light threshold at which the photodiode should register a positive, units go from 0 (least light) to 255 (most light).
    
.. _photodiodevalidatorroutine-findDiode:
Find diode? 
    Run a brief Routine to find the size and position of the photodiode at experiment start
    
.. _photodiodevalidatorroutine-diodePos:
Position [x,y] (*if :ref:`photodiodevalidatorroutine-finddiode` isn't checked*)
    Position of the photodiode on the window.
    
.. _photodiodevalidatorroutine-diodeSize:
Size [x,y] (*if :ref:`photodiodevalidatorroutine-finddiode` isn't checked*)
    Size of the area covered by the photodiode on the window.
    
.. _photodiodevalidatorroutine-diodeUnits:
Spatial units (*if :ref:`photodiodevalidatorroutine-finddiode` isn't checked*)
    Spatial units in which the photodiode size and position are specified.
    
    Options:
    
    * from exp settings
    
    * deg
    
    * cm
    
    * pix
    
    * norm
    
    * height
    
    * degFlatPos
    
    * degFlat
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _photodiodevalidatorroutine-deviceLabel:
Device name 
    A name to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same name here.
    
.. _photodiodevalidatorroutine-deviceBackend:
Photodiode type 
    Type of photodiode to use.
    
.. _photodiodevalidatorroutine-channel:
Photodiode channel 
    If relevant, a channel number attached to the photodiode, to distinguish it from other photodiodes on the same port. Leave blank to use the first photodiode which can detect the Window.
    
Data
===============================

What information about this Component should be saved?


.. _photodiodevalidatorroutine-saveValid:
Save validation results 
    Save validation results after validating on/offset times for stimuli
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _photodiodevalidatorroutine-disabled:
Disable Routine 
    Disable this Routine
    