#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v3.1.1),
    on Thu May  9 17:56:54 2019
If you publish work using this script please cite the PsychoPy publications:
    Peirce, JW (2007) PsychoPy - Psychophysics software in Python.
        Journal of Neuroscience Methods, 162(1-2), 8-13.
    Peirce, JW (2009) Generating stimuli for neuroscience using PsychoPy.
        Frontiers in Neuroinformatics, 2:10. doi: 10.3389/neuro.11.010.2008
"""

from psychopy import locale_setup, sound, gui, visual, core, data, event, logging, clock, hardware
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Store info about the experiment session
psychopyVersion = '3.1.1'
expName = 'untitled.py'
expInfo = {'participant': '', 'session': '001'}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName
expInfo['psychopyVersion'] = psychopyVersion

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename = _thisDir + os.sep + u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])

# An ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, version='',
    extraInfo=expInfo, runtimeInfo=None,
    originPath='newcedrusButtonBoxComponent.py',
    savePickle=True, saveWideText=True,
    dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp

# Start Code - component code to be run before the window creation
import pyxid2 as pyxid  # to use the Cedrus response box

# Setup the Window
win = visual.Window(
    size=(1024, 768), fullscr=True, screen=0, 
    winType='pyglet', allowGUI=False, allowStencil=False,
    monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True, 
    units='height')
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# Initialize components for Routine "trial"
trialClock = core.Clock()
buttonBox = None
for n in range(10):  # doesn't always work first time!
    try:
        devices = pyxid.get_xid_devices()
        core.wait(0.1)
        buttonBox = devices[0]
        break  # found a device so can break the loop
    except Exception:
        pass
if not buttonBox:
    logging.error('could not find a Cedrus device.')
    core.quit()
buttonBox.clock = core.Clock()

# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

# ------Prepare to start Routine "trial"-------
t = 0
trialClock.reset()  # clock
frameN = -1
continueRoutine = True
routineTimer.add(1.000000)
# update component parameters for each repeat
buttonBox.keys = []  # to store response values
buttonBox.rt = []
buttonBox.status = None
# keep track of which components have finished
trialComponents = [buttonBox]
for thisComponent in trialComponents:
    thisComponent.tStart = None
    thisComponent.tStop = None
    thisComponent.tStartRefresh = None
    thisComponent.tStopRefresh = None
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED

# -------Start Routine "trial"-------
while continueRoutine and routineTimer.getTime() > 0:
    # get current time
    t = trialClock.getTime()
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    # *buttonBox* updates
    if t >= 0.0 and buttonBox.status == NOT_STARTED:
        # keep track of start time/frame for later
        buttonBox.tStart = t  # not accounting for scr refresh
        buttonBox.frameNStart = frameN  # exact frame index
        win.timeOnFlip(buttonBox, 'tStartRefresh')  # time at next scr refresh
        buttonBox.status = STARTED
        buttonBox.clock.reset()  # now t=0
        # clear buttonBox responses (in a loop - the Cedrus own function doesn't work well)
        buttonBox.poll_for_response()
        while len(buttonBox.response_queue):
            buttonBox.clear_response_queue()
            buttonBox.poll_for_response() #often there are more resps waiting!
    frameRemains = 0.0 + 1.0- win.monitorFramePeriod * 0.75  # most of one frame period left
    if buttonBox.status == STARTED and t >= frameRemains:
        # keep track of stop time/frame for later
        buttonBox.tStop = t  # not accounting for scr refresh
        buttonBox.frameNStop = frameN  # exact frame index
        win.timeOnFlip(buttonBox, 'tStopRefresh')  # time at next scr refresh
        buttonBox.status = FINISHED
    if buttonBox.status == STARTED:
        theseKeys=[]
        theseRTs=[]
        # check for key presses
        buttonBox.poll_for_response()
        while len(buttonBox.response_queue):
            evt = buttonBox.get_next_response()
            if evt['pressed']:
              theseKeys.append(evt['key'])
              theseRTs.append(buttonBox.clock.getTime())
            buttonBox.poll_for_response()
        buttonBox.clear_response_queue()  # don't process again
        if len(theseKeys) > 0:  # at least one key was pressed
            if buttonBox.keys == []:  # then this is first keypress
                buttonBox.keys = theseKeys[0]  # the first key pressed
                buttonBox.rt = theseRTs[0]
                # a response ends the routine
                continueRoutine = False
    
    # check for quit (typically the Esc key)
    if endExpNow or keyboard.Keyboard().getKeys(keyList=["escape"]):
        core.quit()
    
    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in trialComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished
    
    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

# -------Ending Routine "trial"-------
for thisComponent in trialComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)
# check responses
if buttonBox.keys in ['', [], None]:  # No response was made
    buttonBox.keys = None
thisExp.addData('buttonBox.keys',buttonBox.keys)
if buttonBox.keys != None:  # we had a response
    thisExp.addData('buttonBox.rt', buttonBox.rt)
thisExp.addData('buttonBox.started', buttonBox.tStartRefresh)
thisExp.addData('buttonBox.stopped', buttonBox.tStopRefresh)
thisExp.nextEntry()

# Flip one final time so any remaining win.callOnFlip() 
# and win.timeOnFlip() tasks get executed before quitting
win.flip()

# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename+'.csv')
thisExp.saveAsPickle(filename)
logging.flush()
# make sure everything is closed down
thisExp.abort()  # or data files will save again on exit
win.close()
core.quit()
