#!/usr/bin/env python

from psychopy import log

"""PsychoPy's log module is mostly a simple wrapper of the python logging module. 
It allows messages to be sent from any location (any library or your script) and 
written to files according to the importance level of the message and the minimum level
that the log file (or console) is set to receive. You can have multiple log files each receiving 
different levels of input.

The importance levels are;
    40:ERROR
    35:DATA
    30:WARNING
    20:INFO
    10:DBEUG
So setting to DEBUG level will include all possible messages, setting to ERROR will include only the absolutely essential messages.

"""

log.console.setLevel(log.DEBUG)#set the console to receive all messges
logDat = log.LogFile('lastRun.log', 
    filemode='w',#if you set this to 'a' it will append instead of overwriting
    level=log.WARNING)#errors, data and warnings will be sent to this logfile

#the following will go to any files with the appropriate minimum level set
log.info('Something fairly unimportant')
log.data('something about our data. Data is likely very important!')
log.warning('Should certainly be turned on while working on your experiment - highlights possible flaws in code/design')
log.error("You might have done something that PsychoPy can't handle! But hopefully this gives you some idea what.")

#LogFiles can also simply receive direct input from the write() method.
logDat.write("Test ended")