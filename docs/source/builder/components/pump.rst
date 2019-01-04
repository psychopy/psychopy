.. _pump:

Pump Component
--------------

This component allows you to deliver liquid stimuli using a Cetoni neMESYS syringe pump.

Please specify the name of the pump configuration to use in the PsychoPy
preferences under ``Hardware / Qmix pump configuration``. See the `readme file`_ of
the ``pyqmix`` project for details on how to set up your computer and create
the configuration file.


Properties
~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the stimulus should first appear.

Stop :
    Governs the duration for which the stimulus is presented.

Pump index : int
    The index of the pump: The first pump's index is 0, the second pump's index is 1, etc.
    You may insert the name of a variable here to adjust this value dynamically.

Syringe type : select the appropriate option
    Currently, 25 mL and 50 mL glass syringes are supported. This setting ensures that
    the pump will operate at the correct flow rate.

Pump action : ``aspirate`` or ``dispense``
    Whether to fill (``aspirate``) or to empty (``dispense``) the syringe.

Flow rate : float
    The flow rate in the selected flow rate units.

Flow rate unit : ``mL/s`` or ``mL/min``
    The unit in which the flow rate values are supplied.

Switch valve after dosing : bool
    Whether to switch the valve osition after the pump operation has
    finished. This can be used to ensure a sharp(er) stimulus offset.

Sync to screen : bool
    Whether to synchronize the pump operations (starting, stopping) to the
    screen refresh. This ensures better synchronization with visual stimuli.


.. _readme file: https://github.com/psyfood/pyqmix/blob/master/README.md
