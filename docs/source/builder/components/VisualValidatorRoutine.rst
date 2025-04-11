:orphan:

.. _visualvalidatorroutine:


-------------------------------
Visual Validator Routine
-------------------------------

Use a light sensor to confirm that visual stimuli are presented when they should be.

Categories:
    Validation
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _visualvalidatorroutine-name:

Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _visualvalidatorroutine-findThreshold:

Find best threshold? 
    Run a brief Routine to find the best threshold for the light sensor at experiment start?
    
.. _visualvalidatorroutine-threshold:

Threshold (*if :ref:`visualvalidatorroutine-findthreshold` isn't ==True*)
    Light threshold at which the light sensor should register a positive, units go from 0 (least light) to 255 (most light).
    
.. _visualvalidatorroutine-findSensor:

Find diode? 
    Run a brief Routine to find the size and position of the light sensor at experiment start?
    
.. _visualvalidatorroutine-sensorPos:

Position [x,y] (*if :ref:`visualvalidatorroutine-finddiode` isn't ==True*)
    Position of the light sensor on the window.
    
.. _visualvalidatorroutine-sensorSize:

Size [x,y] (*if :ref:`visualvalidatorroutine-finddiode` isn't ==True*)
    Size of the area covered by the light sensor on the window.
    
.. _visualvalidatorroutine-sensorUnits:

Spatial units (*if :ref:`visualvalidatorroutine-finddiode` isn't ==True*)
    Spatial units in which the light sensor size and position are specified.
    
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


.. _visualvalidatorroutine-deviceLabel:

Device name 
    A name to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same name here.
    
.. _visualvalidatorroutine-deviceBackend:

Light sensor type 
    Type of light sensor to use.
    
.. _visualvalidatorroutine-channel:

Light sensor channel 
    If relevant, a channel number attached to the light sensor, to distinguish it from other light sensors on the same port. Leave blank to use the first light sensor which can detect the Window.
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _visualvalidatorroutine-disabled:

Disable Routine 
    Disable this Routine
    