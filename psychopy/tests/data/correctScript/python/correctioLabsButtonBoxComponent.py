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
    originPath='newioLabsButtonBoxComponent.py',
    savePickle=True, saveWideText=True,
    dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp

# Start Code - component code to be run before the window creation
# connect to ioLabs bbox, turn lights off
from psychopy.hardware import iolab
iolab.ButtonBox().standby()

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
bbox = iolab.ButtonBox()

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
bbox.clearEvents()
bbox.active = (0,1,2,3,4,5,6,7)  # tuple or list of int 0..7
bbox.setEnabled(bbox.active)
bbox.setLights(bbox.active)
bbox.btns = []  # responses stored in .btns and .rt
bbox.rt = []
# keep track of which components have finished
trialComponents = [bbox]
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
    # *bbox* updates
    if t >= 0.0 and bbox.status == NOT_STARTED:
        # keep track of start time/frame for later
        bbox.tStart = t  # not accounting for scr refresh
        bbox.frameNStart = frameN  # exact frame index
        win.timeOnFlip(bbox, 'tStartRefresh')  # time at next scr refresh
        bbox.status = STARTED
        bbox.clearEvents()
        # buttonbox checking is just starting
        bbox.resetClock()  # set bbox hardware internal clock to 0.000; ms accuracy
    frameRemains = 0.0 + 1.0- win.monitorFramePeriod * 0.75  # most of one frame period left
    if bbox.status == STARTED and t >= frameRemains:
        # keep track of stop time/frame for later
        bbox.tStop = t  # not accounting for scr refresh
        bbox.frameNStop = frameN  # exact frame index
        win.timeOnFlip(bbox, 'tStopRefresh')  # time at next scr refresh
        bbox.status = FINISHED
    if bbox.status == STARTED:
        theseButtons = bbox.getEvents()
        if theseButtons:  # at least one button was pressed this frame
            if bbox.btns == []:  # True if the first
                bbox.btns = theseButtons[0].key  # just the first button
                bbox.rt = theseButtons[0].rt
                # a response forces the end of the routine
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
# store ioLabs bbox data for bbox (ExperimentHandler)
if len(bbox.btns) == 0:  # no ioLabs responses
    bbox.btns = None
thisExp.addData('bbox.btns', bbox.btns)
if bbox.btns != None:  # add RTs if there are responses
    thisExp.addData('bbox.rt', bbox.rt)
# check responses
if bbox.keys in ['', [], None]:  # No response was made
    bbox.keys = None
thisExp.addData('bbox.keys',bbox.keys)
if bbox.keys != None:  # we had a response
    thisExp.addData('bbox.rt', bbox.rt)
thisExp.addData('bbox.started', bbox.tStartRefresh)
thisExp.addData('bbox.stopped', bbox.tStopRefresh)
thisExp.nextEntry()
thisExp.nextEntry()
bbox.standby()  # lights out etc

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
