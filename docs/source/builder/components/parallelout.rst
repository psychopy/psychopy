.. _parallelout:

Parallel Port Out Component
---------------------------------

This component allows you to send triggers to a parallel port or to a LabJack device.

An example usage would be in EEG experiments to set the port to 0 when no stimuli are present and then set it to an identifier value for each stimulus synchronised to the start/stop of that stimulus. In that case you might set the `Start data` to be `$ID` (with ID being a column in your conditions file) and set the `Stop Data` to be 0.

Properties
~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

Stop :
    Governs the duration for which the stimulus is presented. See :ref:`startStop` for details.

Port address : select the appropriate option
    You need to know the address of the parallel port you wish to write to. The options that appear in this drop-down list are determined by the application preferences. You can add your particular port there if you prefer.

Start data : 0-255
    When the start time/condition occurs this value will be sent to the parallel port. The value is given as a byte (a value from 0-255) controlling the 8 data pins of the parallel port.

Stop data : 0-255
    As with start data but sent at the end of the period.

Sync to screen : boolean
    If true then the parallel port will be sent synchronised to the next screen refresh, which is ideal if it should indicate the onset of a visual stimulus. If set to False then the data will be set on the parallel port immediately.

.. seealso::

	API reference for :class:`~psychopy.hardware.iolab`
