.. _expSettings:

Experiment settings
---------------------

The settings menu can be accessed by clicking the icon at the top of the window. It allows the user to set various aspects of the experiment, such as the size of the window to be used or what information is gathered about the subject and determine what outputs (data files) will be generated.

Settings
==========

Basic
~~~~~~~~~~~~~~~

Experiment name
    A name that will be stored in the metadata of the data file.

Use PsychoPy version
    Which version of |PsychoPy| was the task created in? if you are using a more recently installed version of |PsychoPy| this can compile using an archived, older version to run previously created tasks.

Show info dlg
    If this box is checked then a dialog will appear at the beginning of the experiment allowing the `Experiment Info` to be changed.

Enable escape
    If ticked then the `Esc` key can be used to exit the experiment at any time (even without a keyboard component)

Experiment Info
    This information will be presented in a dialog box at the start and will be saved with any data files and so can be used for storing information about the current run of the study. The information stored here can also be used within the experiment. For example, if the `Experiment Info` included a field called `ori` then Builder :doc:`components` could access expInfo['ori'] to retrieve the orientation set here. Obviously this is a useful way to run essentially the same experiment, but with different conditions set at run-time. If you are running a study online, we recommend keeping the field "participant" because this is used to name data output files.

Screen
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

Audio
~~~~~~~~~~~~~~~~

Audio library
    Choice of audio library to use to present sound, default uses preferences (see :doc:`../general/prefs`).

Audio latency priority
    Latency mode for PsychToolbox audio (see :doc:`../general/prefs`) (because this applies to the PTB sound backend, this only applies for local, not online studies)

Force stereo
    Force audio to stereo (2-channel) output

Online
~~~~~~~~~~~~~~~~
Output path
    Where to export the compiled javascript experiment and associated html files. (note that in earlier versions of |PsychoPy| this was `html` by default, this is not necissary as it will duplicate your resources, associated discourse threads with this suggestion might now be outdated)

Export html
    When to export a html file and compile a javascript version of the experiment. This is on sync by default, meaning these files will be generated when a project is pushed/synced to |Pavlovia|. Alternatively this can be "on save" or "manually" the latter might be used if you are making manual edits to the exported javascript file, though this is not recommended as changes will not be reflected back in your builder file.

Completed URL
    The URL to direct participants to upon completion (when they select "OK" in the green thank-you message online)

Incomplete URL
    The URL to direct participants to if they exit the task early (e.g. by pressing the escape key).

Additional resources
    Resources that your task will require (e.g. image files, excel sheets). Note that |PsychoPy| will attempt to populate this automatically, though if you encounter an "Unknown resource" error online, it is possible that you need to add resources to this list.

Eyetracking
~~~~~~~~~~~~~~~~

Eyetracker Device
    Specify what kind of eye tracker you are using. If you are creating your paradigm out-of-lab (i.e. with no eye tracker) we suggest using MouseGaze, which will use your mouse to simulate eye movements and blinks. Alternatively, you can select which device you are currently using and set-up those parameters (see :doc:`../api/iohub/device/eyetracker`)

Data
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

Data file delimiter
    What delimiter should your data file use to separate the columns

Save Excel file
	If this box is checked an Excel data file (.xlsx) will be stored.

Save csv file (summaries)
    If this box is checked a summary file will be created with one row corresponding to the entire loop. If a keyboard response is used the mean and dtandard deviations of responses across trials will also be stored.

Save csv file (trial-by-trial)
	If this box is checked a comma separated variable (.csv) will be stored. Each trial will be stored as a new row.

Save psydat file
	If this box is checked a :ref:`psydatFile` will be stored. This is a Python specific format (.pickle files) which contains more information that .xlsx or .csv files that can be used with data analysis and plotting scripts written in Python. Whilst you may not wish to use this format it is recommended that you always save a copy as it contains a complete record of the experiment at the time of data collection.

Save hdf5 file
    If this box is checked data will be stored to a hdf5 file, this is mainly applicable if a component is implemented that requires a complex data structure e.g. eyetracking.

Save log file
    A log file provides a record of what occurred during the experiment in chronological order, including information about any errors or warnings that may have occurred.

Logging level
    How much detail do you want to be output to the log file, if it is being saved. The lowest level is `error`, which only outputs error messages; `warning` outputs warnings and errors; `info` outputs all info, warnings and errors; `debug` outputs all info that can be logged. This system enables the user to get a great deal of information while generating their experiments, but then reducing this easily to just the critical information needed when actually running the study. If your experiment is not behaving as you expect it to, this is an excellent place to begin to work out what the problem is.
