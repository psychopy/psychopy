.. _expSettings:

Experiment settings
---------------------

The settings menu can be accessed by clicking the icon at the top of the window. It allows the user to set various aspects of the experiment, such as the size of the window to be used or what information is gathered about the subject and determine what outputs (data files) will be generated.

Settings
==========

Basic settings
~~~~~~~~~~~~~~~

Experiment name:
    A name that will be stored in the metadata of the data file.

Show info dlg:
    If this box is checked then a dialog will appear at the beginning of the experiment allowing the `Experiment Info` to be changed.
	
Experiment Info:
    This information will be presented in a dialog box at the start and will be saved with any data files and so can be used for storing information about the current run of the study. The information stored here can also be used within the experiment. For example, if the `Experiment Info` included a field called `ori` then Builder :doc:`components` could access expInfo['ori'] to retrieve the orientation set here. Obviously this is a useful way to run essentially the same experiment, but with different conditions set at run-time.

Enable escape:
    If ticked then the `Esc` key can be used to exit the experiment at any time (even without a keyboard component)
    
Data settings
~~~~~~~~~~~~~~~~

.. _dataFileName:

Data filename:
    A :ref:`formatted string <formattedStrings>` to control the base filename and path, often based on variables such as the date and/or the participant. This base filename will be given the various extensions for the different file types as needed. Examples::
        
        # all in data folder relative to experiment file: data/JWP_memoryTask_2014_Feb_15_1648
        'data/%s_%s_%s' %(expInfo['participant'], expName, expInfo['date'])
        
        # group by participant folder: data/JWP/memoryTask-2014_Feb_15_1648
        'data/%s/%s-%s' %(expInfo['participant'], expName, expInfo['date'])
        
        # put into dropbox: ~/dropbox/data/memoryTask/JWP-2014_Feb_15_1648
        # os.path.expanduser replaces '~' with the path to your home directory,
        # os.path.join joins the path components together correctly, regardless of OS
        # os.path.relpath creates a relative path between the specified path and the current directory
        '$os.path.relpath(os.path.join(os.path.expanduser('~'), 'dropbox', 'data', expName, expInfo['participant'] + '-' + expInfo['date']))

Save Excel file:
	If this box is checked an Excel data file (.xlsx) will be stored.
	
Save csv file:
	If this box is checked a comma separated variable (.csv) will be stored.

Save psydat file:
	If this box is checked a :ref:`psydatFile` will be stored. This is a Python specific format (.pickle files) which contains more information that .xlsx or .csv files that can be used with data analysis and plotting scripts written in Python. Whilst you may not wish to use this format it is recommended that you always save a copy as it contains a complete record of the experiment at the time of data collection.

Save log file
    A log file provides a record of what occurred during the experiment in chronological order, including information about any errors or warnings that may have occurred.

Logging level
    How much detail do you want to be output to the log file, if it is being saved. The lowest level is `error`, which only outputs error messages; `warning` outputs warnings and errors; `info` outputs all info, warnings and errors; `debug` outputs all info that can be logged. This system enables the user to get a great deal of information while generating their experiments, but then reducing this easily to just the critical information needed when actually running the study. If your experiment is not behaving as you expect it to, this is an excellent place to begin to work out what the problem is.

Screen settings
~~~~~~~~~~~~~~~~

Monitor
    The name of the monitor calibration. Must match one of the monitor names from :doc:`../general/monitors`.

Screen:
    If multiple screens are available (and if the graphics card is `not` an intel integrated graphics chip) then the user can choose which screen they use (e.g. 1 or 2).

Full-screen window:
    If this box is checked then the experiment window will fill the screen (overriding the window size setting and using the size that the screen is currently set to in the operating system settings).

Window size:
    The size of the window in pixels, if this is not to be a full-screen window.

Units
    The default units of the window (see :doc:`../general/units`). These can be overridden by individual :doc:`components`.
