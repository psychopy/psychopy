#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy2 Experiment Builder (v1.83.04), Fri 30 Sep 2016 07:23:01 AM EDT
If you publish work using this script please cite the relevant PsychoPy publications
  Peirce, JW (2007) PsychoPy - Psychophysics software in Python. Journal of Neuroscience Methods, 162(1-2), 8-13.
  Peirce, JW (2009) Generating stimuli for neuroscience using PsychoPy. Frontiers in Neuroinformatics, 2:10. doi: 10.3389/neuro.11.010.2008
"""

from __future__ import division  # so that 1/3=0.333 instead of 1/3=0
from psychopy import locale_setup, visual, core, data, event, logging, sound, gui
from psychopy.constants import *  # things like STARTED, FINISHED
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import sin, cos, tan, log, log10, pi, average, sqrt, std, deg2rad, rad2deg, linspace, asarray
from numpy.random import random, randint, normal, shuffle
import os  # handy system and path functions
import sys # to get file system encoding

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__)).decode(sys.getfilesystemencoding())
os.chdir(_thisDir)

# Store info about the experiment session
expName = u'keyNameFinder'  # from the Builder filename that created this script
expInfo = {u'session': u'001', u'participant': u''}
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename = _thisDir + os.sep + u'data/%s_%s_%s' %(expInfo['participant'], expName, expInfo['date'])

# An ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, version='',
    extraInfo=expInfo, runtimeInfo=None,
    originPath=u'/home/daniel/Documents/PsychoPyTests/keyNameFinder/keyNameFinder.psyexp',
    savePickle=True, saveWideText=True,
    dataFileName=filename)
#save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp

# Start Code - component code to be run before the window creation

# Setup the Window
win = visual.Window(size=[800, 600], fullscr=False, screen=0, allowGUI=True, allowStencil=False,
    monitor=u'testMonitor', color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True,
    )
# store frame rate of monitor if we can measure it successfully
expInfo['frameRate']=win.getActualFrameRate()
if expInfo['frameRate']!=None:
    frameDur = 1.0/round(expInfo['frameRate'])
else:
    frameDur = 1.0/60.0 # couldn't get a reliable measure so guess

# Initialize components for Routine "trial"
trialClock = core.Clock()
ISI = core.StaticPeriod(win=win, screenHz=expInfo['frameRate'], name='ISI')
description = visual.TextStim(win=win, ori=0, name='description',
    text=u'This tool helps you find the names of your allowed/correct keys for your experiment.\n\n(Press space to move on, escape to quit)',    font=u'Arial',
    pos=[0, 0], height=0.1, wrapWidth=None,
    color=u'white', colorSpace='rgb', opacity=1,
    depth=-1.0)

# Initialize components for Routine "keyNameFinderRoutine"
keyNameFinderRoutineClock = core.Clock()
keyNameText = visual.TextStim(win=win, ori=0, name='keyNameText',
    text='Press any key',    font='Arial',
    pos=[0, 0], height=0.1, wrapWidth=None,
    color='white', colorSpace='rgb', opacity=1,
    depth=0.0)


# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

#------Prepare to start Routine "trial"-------
t = 0
trialClock.reset()  # clock 
frameN = -1
# update component parameters for each repeat
descriptionKeyboard = event.BuilderKeyResponse()  # create an object of type KeyResponse
descriptionKeyboard.status = NOT_STARTED
# keep track of which components have finished
trialComponents = []
trialComponents.append(ISI)
trialComponents.append(description)
trialComponents.append(descriptionKeyboard)
for thisComponent in trialComponents:
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED

#-------Start Routine "trial"-------
continueRoutine = True
while continueRoutine:
    # get current time
    t = trialClock.getTime()
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    
    # *description* updates
    if t >= 0.0 and description.status == NOT_STARTED:
        # keep track of start time/frame for later
        description.tStart = t  # underestimates by a little under one frame
        description.frameNStart = frameN  # exact frame index
        description.setAutoDraw(True)
    
    # *descriptionKeyboard* updates
    if t >= 0.0 and descriptionKeyboard.status == NOT_STARTED:
        # keep track of start time/frame for later
        descriptionKeyboard.tStart = t  # underestimates by a little under one frame
        descriptionKeyboard.frameNStart = frameN  # exact frame index
        descriptionKeyboard.status = STARTED
        # keyboard checking is just starting
        win.callOnFlip(descriptionKeyboard.clock.reset)  # t=0 on next screen flip
        event.clearEvents(eventType='keyboard')
    if descriptionKeyboard.status == STARTED:
        theseKeys = event.getKeys(keyList=['space'])
        
        # check for quit:
        if "escape" in theseKeys:
            endExpNow = True
        if len(theseKeys) > 0:  # at least one key was pressed
            descriptionKeyboard.keys = theseKeys[-1]  # just the last key pressed
            descriptionKeyboard.rt = descriptionKeyboard.clock.getTime()
            # a response ends the routine
            continueRoutine = False
    # *ISI* period
    if t >= 0.0 and ISI.status == NOT_STARTED:
        # keep track of start time/frame for later
        ISI.tStart = t  # underestimates by a little under one frame
        ISI.frameNStart = frameN  # exact frame index
        ISI.start(0.5)
    elif ISI.status == STARTED: #one frame should pass before updating params and completing
        ISI.complete() #finish the static period
    
    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in trialComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished
    
    # check for quit (the Esc key)
    if endExpNow or event.getKeys(keyList=["escape"]):
        core.quit()
    
    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

#-------Ending Routine "trial"-------
for thisComponent in trialComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)
# check responses
if descriptionKeyboard.keys in ['', [], None]:  # No response was made
   descriptionKeyboard.keys=None
# store data for thisExp (ExperimentHandler)
thisExp.addData('descriptionKeyboard.keys',descriptionKeyboard.keys)
if descriptionKeyboard.keys != None:  # we had a response
    thisExp.addData('descriptionKeyboard.rt', descriptionKeyboard.rt)
thisExp.nextEntry()
# the Routine "trial" was not non-slip safe, so reset the non-slip timer
routineTimer.reset()

#------Prepare to start Routine "keyNameFinderRoutine"-------
t = 0
keyNameFinderRoutineClock.reset()  # clock 
frameN = -1
# update component parameters for each repeat

# keep track of which components have finished
keyNameFinderRoutineComponents = []
keyNameFinderRoutineComponents.append(keyNameText)
for thisComponent in keyNameFinderRoutineComponents:
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED

#-------Start Routine "keyNameFinderRoutine"-------
continueRoutine = True
while continueRoutine:
    # get current time
    t = keyNameFinderRoutineClock.getTime()
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    
    # *keyNameText* updates
    if t >= 0.0 and keyNameText.status == NOT_STARTED:
        # keep track of start time/frame for later
        keyNameText.tStart = t  # underestimates by a little under one frame
        keyNameText.frameNStart = frameN  # exact frame index
        keyNameText.setAutoDraw(True)
    keys = event.getKeys()
    if keys:
    
        if 'escape' in keys:
            continueRoutine = False
    
        lastKey = keys.pop()
    
        messFormat = "That key was:\n\n\'{0}\'\n\nPress another key".format(lastKey)
    
        keyNameText.text = messFormat
    
    
    
    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in keyNameFinderRoutineComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished
    
    # check for quit (the Esc key)
    if endExpNow or event.getKeys(keyList=["escape"]):
        core.quit()
    
    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

#-------Ending Routine "keyNameFinderRoutine"-------
for thisComponent in keyNameFinderRoutineComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)

# the Routine "keyNameFinderRoutine" was not non-slip safe, so reset the non-slip timer
routineTimer.reset()

# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename+'.csv')
thisExp.saveAsPickle(filename)
logging.flush()
# make sure everything is closed down
thisExp.abort() # or data files will save again on exit
win.close()
core.quit()
