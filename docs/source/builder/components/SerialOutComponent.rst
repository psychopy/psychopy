.. _serialoutcomponent:

-------------------------------
Serial Out Component
-------------------------------

This component allows you to send triggers to a serial port. For a full tutorial please see :ref: `this page <serial>`. 

An example usage would be in EEG experiments to set the port to 0 when no stimuli are present and then set it to an identifier value for each stimulus synchronised to the start/stop of that stimulus. In that case you might set the `Start data` to be `$ID` (with ID being a column in your conditions file) and set the `Stop Data` to be "0".

Categories:
    I/O, EEG
Works in:
    PsychoPy

**Note: Since this is still in beta, keep an eye out for bug fixes.**

Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _serialoutcomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _serialoutcomponent-startVal:
Start 
    When the Serial Out Component should start, see :ref:`startStop`.
    
.. _serialoutcomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _serialoutcomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _serialoutcomponent-stopVal:
Stop 
    When the Serial Out Component should stop, see :ref:`startStop`.
    
.. _serialoutcomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _serialoutcomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _serialoutcomponent-port:
Port 
    You need to know the address of the serial port you wish to write to. For more information on how to find out this address please see :ref: `this page <serial>`. 
    
.. _serialoutcomponent-startdata:
Start data 
    Data to be sent at start of pulse. Data will be converted to bytes, so to specify anumeric value directly use $chr(...).
    
.. _serialoutcomponent-stopdata:
Stop data 
    String data to be sent at end of pulse. Data will be converted to bytes, so to specify anumeric value directly use $chr(...).
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _serialoutcomponent-baudrate:
Baud rate 
    The baud rate, or speed, of the connection.
    
.. _serialoutcomponent-bytesize:
Data bits 
    Size of bits to be sent.
    
.. _serialoutcomponent-stopbits:
Stop bits 
    Size of bits to be sent on stop.
    
.. _serialoutcomponent-parity:
Parity 
    Parity mode.
    
    Options:
    
    * None
    
    * Even
    
    * Off
    
    * Mark
    
    * Space
    
.. _serialoutcomponent-timeout:
Timeout 
    Time at which to give up listening for a response (leave blank for no limit)
    
Data
===============================

What information about this Component should be saved?


.. _serialoutcomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _serialoutcomponent-syncScreenRefresh:
Sync timing with screen refresh 
    If true then the serial port will be sent synchronised to the next screen refresh, which is ideal if it should indicate the onset of a visual stimulus. If set to False then the data will be set on the serial port immediately.
    
.. _serialoutcomponent-getResponse:
Get response? 
    After sending a signal, should PsychoPy read and record a response from the port?
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _serialoutcomponent-disabled:
Disable Component 
    Disable this Component
    