#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PsychoPy's log module is mostly a simple wrapper of the python logging module.
It allows messages to be sent from any location (any library or your script) and
written to files according to the importance level of the message and the minimum level
that the log file (or console) is set to receive. You can have multiple log files each receiving
different levels of input.

The importance levels are
    40: ERROR
    35: DATA
    30: WARNING
    25: DATA
    22: EXP
    20: INFO
    10: DEBUG
So setting to DEBUG level will include all possible messages, setting to ERROR will include only the absolutely essential messages.
"""

from psychopy import logging, core, visual

globalClock = core.Clock()  # if this isn't provided the log times will reflect secs since python started
logging.setDefaultClock(globalClock)

logging.console.setLevel(logging.DEBUG)  # receive nearly all messages
logDat = logging.LogFile('logLastRun.log',
    filemode='w',  # if you set this to 'a' it will append instead of overwriting
    level=logging.WARNING)  # errors, data and warnings will be sent to this logfile

# the following will go to any files with the appropriate minimum level set
logging.info('Something fairly unimportant')
logging.data('Something about our data. Data is likely very important!')
logging.warning('Handy while building your experiment - highlights possible flaws in code/design')
logging.error("You might have done something that PsychoPy can't handle! But hopefully this gives you some idea what.")

# some things should be logged timestamped on the next video frame
# For instance the time of a stimulus appearing is related to the flip:
win = visual.Window([400, 400])
for n in range(5):
    win.logOnFlip('frame %i occured' %n, level=logging.EXP)
    if n in [2, 4]:
        win.logOnFlip('an even frame occured', level=logging.EXP)
    win.flip()

# LogFiles can also simply receive direct input from the write() method
# messages using write() will be sent immediately, and are often not
# in correct chronological order with logged messages
logDat.write("Testing\n\n")

win.close()
core.quit()

# The contents of this file are in the public domain.
