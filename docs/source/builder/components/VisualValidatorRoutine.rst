:orphan:

.. _visualvalidatorroutine:


-------------------------------
Visual Validator Routine
-------------------------------

Use a light sensor to confirm that visual stimuli are presented when they should be. Before using a validator component in your experiment it is important to ensure that you have a photodiode device available for the routine to use. If you do not have a photodiode to hand you can use an "emulator" temporarily until you have access to a real device.

To configure your photodiode with an emulator go to Device Manager > Add device > Screen Buffer Sampler (Debug) > Light Sensor Emulator. Alternatively if you have a photodiode connected you can search for the name of your actual device in the list of available devices.

Once you have selected the Visual Validator component, it is important to add it to your experiment flow. Select Insert Routine > [name of your visual validator component] > add to your flow (usually best at the start of the experiment).

In the "Device" section of the component you can select the name of your photodiode device from the dropdown list. If you have multiple photodiodes connected to your system you may also need to specify a channel number to distinguish between them.

By default "Find best threshold?" and "Find sensor?" " are both set to True. This means that when you run your experiment the visual validator routine will first run a brief routine to find the best threshold for the light sensor, followed by another brief routine to find the size and position of the light sensor on the screen. Once these two brief routines have been run the main visual validator routine will run for the remainder of your experiment. 

Recommended debugging steps for using the visual validator routine in your experiment:

* Use an external piece of software to check that your computer can detect the external hardware. For example, if using Cedrus you can install `Xidon <https://cedrus.com/support/xid/xidon.htm>`_ to check that your computer can detect the device.
* Set the threshold manually to a value that you know will work with your setup. You can do this by setting "Find best threshold?" to False and then entering a value for "Threshold". Lowering the threshold will make it more sensitive.


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
    Light threshold at which the light sensor should register a positive, units go from 0 (least light) to 1 (most light).
    
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

Information about the device associated with this Component (the photodiode or light sensor emulator)


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
    