.. _serialout:

Serial Port Out Component
---------------------------------

This component allows you to send triggers to a serial port. For a full tutorial please see :ref: `this page <serial>`. 

An example usage would be in EEG experiments to set the port to 0 when no stimuli are present and then set it to an identifier value for each stimulus synchronised to the start/stop of that stimulus. In that case you might set the `Start data` to be `$ID` (with ID being a column in your conditions file) and set the `Stop Data` to be "0".

Properties
~~~~~~~~~~~

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

Port address : type the appropriate option
    You need to know the address of the serial port you wish to write to. For more information on how to find out this address please see :ref: `this page <serial>`. 

Start data : string
    When the start time/condition occurs this value will be sent to the serial port. For more information please see :ref: `this page <serial>`. 

Stop data : string
    As with start data but sent at the end of the period.

Data
====

Sync timing with screen refresh : boolean
    If true then the serial port will be sent synchronised to the next screen refresh, which is ideal if it should indicate the onset of a visual stimulus. If set to False then the data will be set on the serial port immediately.

Get response? : boolean
    If true then PsychoPy reads and records a response from the port after the data has been sent.

Hardware
========
Parameters for controlling hardware.

Baud rate : 
    The baud rate, or speed, of the connection.

Data bits : 
    The size of the bits to be sent.

Stop bits : 
    The size of the bits ti be sent on stop.

Parity :
    The parity mode.

Timeout : 
    Time at which to give up listening for a repsonse from the serial port.



