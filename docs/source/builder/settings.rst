Experiment settings
---------------------

The settings menu allows the user to set various aspects of the experiment, such as the size of the window to be used, additional information about the subject and determine what outputs (data files) should be generated.

Settings
==========

Screen:
    If multiple screens are available (and if the graphics card is `not` an intel integrated graphics chip) then the user can choose which screen they use (e.g. 1 or 2).

Full-screen window:
    If this box is checked then the experiment window will fill the screen (overriding the window size setting and using the size that the screen is currently set to in the operating system settings).

Window size:
    The size of the window in pixels, if this is not to be a full-screen window.

Experiment Info
    This is a python dictionary object that stores information about the current experiment. This will be saved with any data files so can be used for storing information about the current run of the study. The information stored here can also be used within the experiment. For example, if the `Experiment Info` was {'participant':'jwp', 'ori':10} then Builder :doc:`components` could access info['ori'] to retrieve the orientation set here. Obviously this is a useful way to run essentially the same experiment, but with different conditions set at run time.
    
Show info dlg
    If this box is checked then a dialog will appear at the beginning of the experiment allowing the `Experiment Info` to be changed.

Monitor
    The name of the monitor calibration. Must match one of the monitor names from :doc:`../general/monitors`.

Save log file
    A log file provides a record of what occurred during the experiment in chronological order, including information about any errors or warnings that may have occurred.

Units
    The default units of the window (see :doc:`../general/units`). These can be overridden by individual :doc:`components`.

Logging level
    How much detail do you want to be output to the log file, if it is being saved. The lowest level is `error`, which only outputs error messages; `warning` outputs warnings and errors; `info` outputs all info, warnings and errors; `debug` outputs all info that can be logged. This system enables the user to get a great deal of information whil generating their experiments, but then reducing this easily to just the critical information needed when actually running the study.
