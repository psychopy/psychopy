.. _codeLogging:

Logging data
-------------------

TrialHandler and StairHandler can both generate data outputs in which responses are stored, in relation to the stimulus conditions. In addition to those data outputs, PsychoPy can create detailed chronological log files of events during the experiment.

Log levels and targets
~~~~~~~~~~~~~~~~~~~~~~~~~
Log messages have various levels of severity:
    ERROR, WARNING, DATA, EXP, INFO and DEBUG

Multiple `targets` can also be created to receive log messages. Each target has a particular critical level and receives all logged messages greater than that. For example, you could set the console (visual output) to receive only warnings and errors, have a central log file that you use to store warning messages across studies (with file mode `append`), and another to create a detailed log of data and events within a single study with `level=INFO`::

    from psychopy import logging
    logging.console.setLevel(logging.WARNING)
    # overwrite (filemode='w') a detailed log of the last run in this dir
    lastLog = logging.LogFile("lastRun.log", level=logging.INFO, filemode='w')
    # also append warnings to a central log file
    centralLog = logging.LogFile("C:\\psychopyExps.log", level=logging.WARNING, filemode='a')

Updating the logs
~~~~~~~~~~~~~~~~~~~~~
For performance purposes log files are not actually written when the log commands are 'sent'. They are stored in a list and processed automatically when the script ends. You might also choose to force a `flush` of the logged messages manually during the experiment (e.g. during an inter-trial interval)::

    from psychopy import logging
    
    ...
    
    logging.flush()    # write messages out to all targets

This should only be necessary if you want to see the logged information as the experiment progresses.

AutoLogging
~~~~~~~~~~~~~~

**New in version 1.63.00**

Certain events will log themselves automatically by default. For instance, visual stimuli send log messages every time one of their parameters is changed, and when autoDraw is toggled they send a message that the stimulus has started/stopped. All such log messages are timestamped with the frame flip on which they take effect. To avoid this logging, for stimuli such as fixation points that might not be critical to your analyses, or for stimuli that change constantly and will flood the logging system with messages, the autoLogging can be turned on/off at initialisation of the stimulus and can be altered afterwards with `.setAutoLog(True/False)`

Manual methods
~~~~~~~~~~~~~~~~~~~~
In addition to a variety of automatic logging messages, you can create your own, of various levels. These can be timestamped immediately::

    from psychopy import logging
    logging.log(level=logging.WARN, msg='something important')
    logging.log(level=logging.EXP, msg='something about the conditions')
    logging.log(level=logging.DATA, msg='something about a response')
    logging.log(level=logging.INFO, msg='something less important')

There are additional convenience functions for the above: logging.warn('a warning') etc.

For stimulus changes you probably want the log message to be timestamped based on the frame flip (when the stimulus is next presented) rather than the time that the log message is sent::

    from psychopy import logging, visual
    win = visual.Window([400,400])
    win.flip()
    logging.log(level=logging.EXP, msg='sent immediately')
    win.logOnFlip(level=logging.EXP, msg='sent on actual flip')
    win.flip()
    
Using a custom clock for logs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**New in version 1.63.00**

By default times for log files are reported as seconds after the very beginning of the script (often it takes a few seconds to initialise and import all modules too). You can set the logging system to use any given :class:`core.Clock` object (actually, anything with a `getTime()` method)::

    from psychopy import core, logging
    globalClock = core.Clock()
    logging.setDefaultClock(globalClock)
