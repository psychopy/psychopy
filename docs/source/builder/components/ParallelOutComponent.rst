.. _paralleloutcomponent:

-------------------------------
Parallel Out Component
-------------------------------

This component allows you to send triggers to a parallel port, USB2TTL8, or LabJack U3 device.

An example usage would be in EEG experiments to set the port to 0 when no stimuli are present and then set it to an identifier value for each stimulus synchronised to the start/stop of that stimulus. In that case you might set the `Start data` to be `$ID` (with ID being a column in your conditions file) and set the `Stop Data` to be 0

Categories:
    I/O, EEG
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _paralleloutcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _paralleloutcomponent-startVal:
Start 
    When the Parallel Out Component should start, see :ref:`startStop`.
    
.. _paralleloutcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _paralleloutcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _paralleloutcomponent-stopVal:
Stop 
    When the Parallel Out Component should stop, see :ref:`startStop`.
    
.. _paralleloutcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _paralleloutcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _paralleloutcomponent-address:
Port address 
    You need to know the address of the parallel port you wish to write to. The options that appear in this drop-down list are determined by the application preferences. You can add your particular port there if you prefer.
    
    Options:
    
    * 0x0378
    
    * 0x03BC
    
    * LabJack U3
    
    * USB2TTL8
    
.. _paralleloutcomponent-register:
U3 register (*if :ref:`paralleloutcomponent-address` =='LabJack U3'*)
    When using a LabJack U3, you can select which register is used to write a data byte to. Register EIO is the default.
    
    Options:
    
    * EIO
    
    * FIO
    
Data
===============================

What information about this Component should be saved?


.. _paralleloutcomponent-startData:
Start data 
    Data to be sent at 'start'. The value is given as a byte (a value from 0-255) controlling the 8 data pins of the parallel port.
    
.. _paralleloutcomponent-stopData:
Stop data 
    Data to be sent at 'end'. The value is given as a byte (a value from 0-255) controlling the 8 data pins of the parallel port.
    
.. _paralleloutcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _paralleloutcomponent-syncScreenRefresh:
Sync timing with screen refresh 
    If true then the parallel port will be sent synchronised to the next screen refresh, which is ideal if it should indicate the onset of a visual stimulus. If set to False then the data will be set on the parallel port immediately.
    
.. _paralleloutcomponent-syncScreen:
Sync to screen 
    If the parallel port data relates to visual stimuli then sync its pulse to the screen refresh
    
    Options:
    
    * True
    
    * False
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _paralleloutcomponent-disabled:
Disable Component 
    Disable this Component
    