#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2021.1.0),
    on February 15, 2021, at 12:48
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019) 
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. 
        https://doi.org/10.3758/s13428-018-01193-y

"""

from __future__ import absolute_import, division

from psychopy import locale_setup
from psychopy import prefs
prefs.hardware['audioLib'] = 'pygame'
prefs.hardware['audioLatencyMode'] = '4'
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard



# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)

# Store info about the experiment session
psychopyVersion = '2021.1.0'
expName = 'visualsearch_eyetracker'  # from the Builder filename that created this script
expInfo = {'session': '1', 'participant': '001', 'Eye Tracker Config': 'eyelink_config.yaml'}
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
    originPath='D:\\DEV\\my-code\\psychopy\\psychopy\\demos\\builder\\Feature Demos\\iohub\\visualsearch_eyetracker\\visualsearch_eyetracker.py',
    savePickle=True, saveWideText=True,
    dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file
frameTolerance = 0.001  # how close to onset before 'same' frame

# Start Code - component code to be run after the window creation

# Setup the Window
win = visual.Window(
    size=[1920, 1080], fullscr=True, screen=0, 
    winType='pyglet', allowGUI=True, allowStencil=False,
    monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True, 
    units='pix')
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# create a default keyboard (e.g. to check for escape)
defaultKeyboard = keyboard.Keyboard()

# Initialize components for Routine "tracker_setup"
tracker_setupClock = core.Clock()
eye_tracker = None
gaze_x = gaze_y = 0.0
io = None
# get the name of the eye tracker
# config file from the expInfo dialog:
config_file = expInfo['Eye Tracker Config']

# only proceed if the filename points to a valid file:
if os.path.isfile(config_file):
    # import some needed libraries from ioHub:
    from psychopy.iohub import util, launchHubServer

    et_config = util.readConfig(config_file)
    io = launchHubServer(**et_config)
    eye_tracker = io.getDevice('tracker')
else:
    print("Quit because eye tracker config {} could not be loaded.".format(config_file))
    core.quit()

if not eye_tracker:
    print("Quit because couldn't connect to eye tracker.")
    io.quit()
    core.quit()
tracker_message = visual.TextStim(win=win, name='tracker_message',
    text='Press any key to start\nEye Tracker setup / calibration.',
    font='Arial',
    units='norm', pos=(0, 0), height=0.1, wrapWidth=None, ori=0, 
    color='white', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-1.0);
proceed = keyboard.Keyboard()

# Initialize components for Routine "instruct"
instructClock = core.Clock()
instructs = visual.TextStim(win=win, name='instructs',
    text='Fixate on the blue circle.\n\nThen fixation the hexagon as \nquickly as possible.\n\nPress ESCAPE at any time to exit experiment.\nPress any key to start.\n',
    font='Arial',
    pos=(0, 0), height=20, wrapWidth=None, ori=0, 
    color='blue', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=0.0);
proceed_key = keyboard.Keyboard()
block_info = visual.TextStim(win=win, name='block_info',
    text='default text',
    font='Arial',
    units='norm', pos=(0, -0.5), height=0.1, wrapWidth=None, ori=0, 
    color='blue', colorSpace='rgb', opacity=1, 
    languageStyle='LTR',
    depth=-3.0);

# Initialize components for Routine "fixation"
fixationClock = core.Clock()
fixation_target = visual.Polygon(
    win=win, name='fixation_target',units='pix', 
    edges=99, size=(40,40),
    ori=0, pos=(0, 0),
    lineWidth=1,     colorSpace='rgb',  lineColor=[-1,-1,1], fillColor=[-1,-1,1],
    opacity=1, depth=0.0, interpolate=True)
gaze_position = visual.Polygon(
    win=win, name='gaze_position',units='pix', 
    edges=99, size=(30, 30),
    ori=0, pos=[0,0],
    lineWidth=1,     colorSpace='rgb',  lineColor=[-1,-1,1], fillColor=None,
    opacity=1, depth=-2.0, interpolate=True)

# Initialize components for Routine "trial"
trialClock = core.Clock()
x_pos = [-400, -300, -200, -100, 0, 100, 200, 300, 400]
y_pos = [-200, -150, -100, -50, 0, 50, 100, 150, 200]

#x_pos = [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4]
#y_pos = [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4]

#correct_sound = sound.Sound(u'A', secs = 0.4)
#correct_sound.setVolume(1)
#wrong_sound = sound.Sound(u'D', secs = 0.4)
target = visual.Polygon(
    win=win, name='target',units='pix', 
    edges=6, size=(40,40),
    ori=30, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor='white',
    opacity=1, depth=-1.0, interpolate=True)
distract_1 = visual.Polygon(
    win=win, name='distract_1',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-2.0, interpolate=False)
distract_2 = visual.Polygon(
    win=win, name='distract_2',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-3.0, interpolate=False)
distract_3 = visual.Polygon(
    win=win, name='distract_3',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-4.0, interpolate=False)
distract_4 = visual.Polygon(
    win=win, name='distract_4',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-5.0, interpolate=False)
distract_5 = visual.Polygon(
    win=win, name='distract_5',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-6.0, interpolate=False)
distract_6 = visual.Polygon(
    win=win, name='distract_6',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-7.0, interpolate=False)
distract_7 = visual.Polygon(
    win=win, name='distract_7',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-8.0, interpolate=False)
distract_8 = visual.Polygon(
    win=win, name='distract_8',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-9.0, interpolate=False)
gaze_position_1 = visual.Polygon(
    win=win, name='gaze_position_1',units='pix', 
    edges=99, size=(30, 30),
    ori=0, pos=[0,0],
    lineWidth=1,     colorSpace='rgb',  lineColor=[-1,-1,1], fillColor=None,
    opacity=1, depth=-10.0, interpolate=True)

# Initialize components for Routine "feedback"
feedbackClock = core.Clock()
target_2 = visual.Polygon(
    win=win, name='target_2',units='pix', 
    edges=6, size=(40,40),
    ori=30, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor='green',
    opacity=1, depth=0.0, interpolate=True)
distract = visual.Polygon(
    win=win, name='distract',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-1.0, interpolate=False)
distract_9 = visual.Polygon(
    win=win, name='distract_9',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-2.0, interpolate=False)
distract_10 = visual.Polygon(
    win=win, name='distract_10',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-3.0, interpolate=False)
distract_11 = visual.Polygon(
    win=win, name='distract_11',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-4.0, interpolate=False)
distract_12 = visual.Polygon(
    win=win, name='distract_12',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-5.0, interpolate=False)
distract_13 = visual.Polygon(
    win=win, name='distract_13',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-6.0, interpolate=False)
distract_14 = visual.Polygon(
    win=win, name='distract_14',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-7.0, interpolate=False)
distract_15 = visual.Polygon(
    win=win, name='distract_15',units='pix', 
    edges=5, size=(40,40),
    ori=0, pos=[0,0],
    lineWidth=0,     colorSpace='rgb',  lineColor=[1,1,1], fillColor=[-1,-1,-1],
    opacity=1.0, depth=-8.0, interpolate=False)
gaze_position_2 = visual.Polygon(
    win=win, name='gaze_position_2',units='pix', 
    edges=99, size=(30, 30),
    ori=0, pos=[0,0],
    lineWidth=1,     colorSpace='rgb',  lineColor=[-1,-1,1], fillColor=None,
    opacity=1, depth=-9.0, interpolate=True)

# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

# ------Prepare to start Routine "tracker_setup"-------
continueRoutine = True
# update component parameters for each repeat
proceed.keys = []
proceed.rt = []
_proceed_allKeys = []
# keep track of which components have finished
tracker_setupComponents = [tracker_message, proceed]
for thisComponent in tracker_setupComponents:
    thisComponent.tStart = None
    thisComponent.tStop = None
    thisComponent.tStartRefresh = None
    thisComponent.tStopRefresh = None
    if hasattr(thisComponent, 'status'):
        thisComponent.status = NOT_STARTED
# reset timers
t = 0
_timeToFirstFrame = win.getFutureFlipTime(clock="now")
tracker_setupClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
frameN = -1

# -------Run Routine "tracker_setup"-------
while continueRoutine:
    # get current time
    t = tracker_setupClock.getTime()
    tThisFlip = win.getFutureFlipTime(clock=tracker_setupClock)
    tThisFlipGlobal = win.getFutureFlipTime(clock=None)
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    
    # *tracker_message* updates
    if tracker_message.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
        # keep track of start time/frame for later
        tracker_message.frameNStart = frameN  # exact frame index
        tracker_message.tStart = t  # local t and not account for scr refresh
        tracker_message.tStartRefresh = tThisFlipGlobal  # on global time
        win.timeOnFlip(tracker_message, 'tStartRefresh')  # time at next scr refresh
        tracker_message.setAutoDraw(True)
    
    # *proceed* updates
    waitOnFlip = False
    if proceed.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
        # keep track of start time/frame for later
        proceed.frameNStart = frameN  # exact frame index
        proceed.tStart = t  # local t and not account for scr refresh
        proceed.tStartRefresh = tThisFlipGlobal  # on global time
        win.timeOnFlip(proceed, 'tStartRefresh')  # time at next scr refresh
        proceed.status = STARTED
        # keyboard checking is just starting
        waitOnFlip = True
        win.callOnFlip(proceed.clock.reset)  # t=0 on next screen flip
        win.callOnFlip(proceed.clearEvents, eventType='keyboard')  # clear events on next screen flip
    if proceed.status == STARTED and not waitOnFlip:
        theseKeys = proceed.getKeys(keyList=None, waitRelease=False)
        _proceed_allKeys.extend(theseKeys)
        if len(_proceed_allKeys):
            proceed.keys = _proceed_allKeys[-1].name  # just the last key pressed
            proceed.rt = _proceed_allKeys[-1].rt
            # a response ends the routine
            continueRoutine = False
    
    # check if all components have finished
    if not continueRoutine:  # a component has requested a forced-end of Routine
        break
    continueRoutine = False  # will revert to True if at least one component still running
    for thisComponent in tracker_setupComponents:
        if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
            continueRoutine = True
            break  # at least one component has not yet finished
    
    # refresh the screen
    if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
        win.flip()

# -------Ending Routine "tracker_setup"-------
for thisComponent in tracker_setupComponents:
    if hasattr(thisComponent, "setAutoDraw"):
        thisComponent.setAutoDraw(False)
# Minimize experiment window 
win.winHandle.minimize()

# Run eye tracker setup / calibration
# which opens a seperate full screen 
# window.
eye_tracker.runSetupProcedure()

# Eye tracker setup complete.
# Maximize experiment window.
win.winHandle.activate()
win.winHandle.maximize()
thisExp.addData('tracker_message.started', tracker_message.tStartRefresh)
thisExp.addData('tracker_message.stopped', tracker_message.tStopRefresh)
# the Routine "tracker_setup" was not non-slip safe, so reset the non-slip timer
routineTimer.reset()

# set up handler to look after randomisation of conditions etc
trials = data.TrialHandler(nReps=20, method='random', 
    extraInfo=expInfo, originPath=-1,
    trialList=data.importConditions('search_conditions.xlsx'),
    seed=None, name='trials')
thisExp.addLoop(trials)  # add the loop to the experiment
thisTrial = trials.trialList[0]  # so we can initialise stimuli with some values
# abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
if thisTrial != None:
    for paramName in thisTrial:
        exec('{} = thisTrial[paramName]'.format(paramName))

for thisTrial in trials:
    currentLoop = trials
    # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
    if thisTrial != None:
        for paramName in thisTrial:
            exec('{} = thisTrial[paramName]'.format(paramName))
    
    # ------Prepare to start Routine "instruct"-------
    continueRoutine = True
    # update component parameters for each repeat
    proceed_key.keys = []
    proceed_key.rt = []
    _proceed_key_allKeys = []
    if trials.thisN % 18 != 0:
        continueRoutine = False
    block_info.setText('Block: ' + str(trials.thisRepN))
    # keep track of which components have finished
    instructComponents = [instructs, proceed_key, block_info]
    for thisComponent in instructComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    instructClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "instruct"-------
    while continueRoutine:
        # get current time
        t = instructClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=instructClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *instructs* updates
        if instructs.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            instructs.frameNStart = frameN  # exact frame index
            instructs.tStart = t  # local t and not account for scr refresh
            instructs.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(instructs, 'tStartRefresh')  # time at next scr refresh
            instructs.setAutoDraw(True)
        
        # *proceed_key* updates
        waitOnFlip = False
        if proceed_key.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            proceed_key.frameNStart = frameN  # exact frame index
            proceed_key.tStart = t  # local t and not account for scr refresh
            proceed_key.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(proceed_key, 'tStartRefresh')  # time at next scr refresh
            proceed_key.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(proceed_key.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(proceed_key.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if proceed_key.status == STARTED and not waitOnFlip:
            theseKeys = proceed_key.getKeys(keyList=None, waitRelease=False)
            _proceed_key_allKeys.extend(theseKeys)
            if len(_proceed_key_allKeys):
                proceed_key.keys = _proceed_key_allKeys[-1].name  # just the last key pressed
                proceed_key.rt = _proceed_key_allKeys[-1].rt
                # a response ends the routine
                continueRoutine = False
        
        # *block_info* updates
        if block_info.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            block_info.frameNStart = frameN  # exact frame index
            block_info.tStart = t  # local t and not account for scr refresh
            block_info.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(block_info, 'tStartRefresh')  # time at next scr refresh
            block_info.setAutoDraw(True)
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in instructComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "instruct"-------
    for thisComponent in instructComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    trials.addData('instructs.started', instructs.tStartRefresh)
    trials.addData('instructs.stopped', instructs.tStopRefresh)
    trials.addData('block_info.started', block_info.tStartRefresh)
    trials.addData('block_info.stopped', block_info.tStopRefresh)
    # the Routine "instruct" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # ------Prepare to start Routine "fixation"-------
    continueRoutine = True
    # update component parameters for each repeat
    # Clear any keyboard events
    # received before start of trial.
    event.clearEvents()
    
    #Start collecting eye tracker data
    eye_tracker.setRecordingState(True)
    
    missed_samples = 0
    fixation_started = False
    
    # keep track of which components have finished
    fixationComponents = [fixation_target, gaze_position]
    for thisComponent in fixationComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    fixationClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "fixation"-------
    while continueRoutine:
        # get current time
        t = fixationClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=fixationClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *fixation_target* updates
        if fixation_target.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            fixation_target.frameNStart = frameN  # exact frame index
            fixation_target.tStart = t  # local t and not account for scr refresh
            fixation_target.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(fixation_target, 'tStartRefresh')  # time at next scr refresh
            fixation_target.setAutoDraw(True)
        gaze_pos = eye_tracker.getPosition()
        
        if type(gaze_pos) not in [list, tuple]:
            missed_samples = missed_samples + 1
        else:
            gaze_x, gaze_y = gaze_pos
            distance_from_centre = sqrt(gaze_x ** 2 + gaze_y ** 2)
            if distance_from_centre <= 60:
                if not fixation_started:
                    fixation_started = True
                    fixation_start_time = t
                elif t - fixation_start_time > 0.3:
                    continueRoutine = False
            else:
                fixation_started = False
        
        
        
        
        
        
        
        # *gaze_position* updates
        if gaze_position.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            gaze_position.frameNStart = frameN  # exact frame index
            gaze_position.tStart = t  # local t and not account for scr refresh
            gaze_position.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(gaze_position, 'tStartRefresh')  # time at next scr refresh
            gaze_position.setAutoDraw(True)
        if gaze_position.status == STARTED:  # only update if drawing
            gaze_position.setPos((gaze_x, gaze_y))
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in fixationComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "fixation"-------
    for thisComponent in fixationComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    trials.addData('fixation_target.started', fixation_target.tStartRefresh)
    trials.addData('fixation_target.stopped', fixation_target.tStopRefresh)
    #print('Could not read eye position on ' + str(missed_samples) + ' frames during fixation period of experiment.')
    
    trials.addData('gaze_position.started', gaze_position.tStartRefresh)
    trials.addData('gaze_position.stopped', gaze_position.tStopRefresh)
    # the Routine "fixation" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # ------Prepare to start Routine "trial"-------
    continueRoutine = True
    # update component parameters for each repeat
    shuffle(x_pos)
    shuffle(y_pos)
    
    missed_samples = 0
    
    
    
    target.setFillColor(target_color)
    target.setPos((x_pos[0], y_pos[0]))
    distract_1.setOpacity(opacity_1)
    distract_1.setPos((x_pos[1], y_pos[1]))
    distract_2.setOpacity(opacity_2)
    distract_2.setPos((x_pos[2], y_pos[2]))
    distract_3.setOpacity(opacity_3)
    distract_3.setPos((x_pos[3], y_pos[3]))
    distract_4.setOpacity(opacity_4)
    distract_4.setPos((x_pos[4], y_pos[4]))
    distract_5.setOpacity(opacity_5)
    distract_5.setPos((x_pos[5], y_pos[5]))
    distract_6.setOpacity(opacity_6)
    distract_6.setPos((x_pos[6], y_pos[6]))
    distract_7.setOpacity(opacity_7)
    distract_7.setPos((x_pos[7], y_pos[7]))
    distract_8.setOpacity(opacity_8)
    distract_8.setPos((x_pos[8], y_pos[8]))
    # keep track of which components have finished
    trialComponents = [target, distract_1, distract_2, distract_3, distract_4, distract_5, distract_6, distract_7, distract_8, gaze_position_1]
    for thisComponent in trialComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    trialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "trial"-------
    while continueRoutine:
        # get current time
        t = trialClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        gaze_pos = eye_tracker.getPosition()
        
        try:
            gaze_x, gaze_y = gaze_pos
        except:
            gaze_pos = None
            missed_samples = missed_samples + 1
        
        keys = event.getKeys()
        if keys:
            if 'escape' in keys:
                eye_tracker.setRecordingState(False)
                eye_tracker.setConnectionState(False)
                print("Exiting experiment, ESCAPE was presssed.")
                io.quit()
                core.quit()
        
        if gaze_pos:
            if target.contains(gaze_x, gaze_y):
                thisExp.addData('RT', t)
                continueRoutine = False
            else:
                for distractor in [distract_1, distract_2, distract_3, distract_4, distract_5, distract_6, distract_7, distract_8]:
                    if distractor.contains(gaze_x, gaze_y) and distractor.opacity > 0.99:
                        pass#wrong_sound.play()
        
        
        
        # *target* updates
        if target.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            target.frameNStart = frameN  # exact frame index
            target.tStart = t  # local t and not account for scr refresh
            target.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(target, 'tStartRefresh')  # time at next scr refresh
            target.setAutoDraw(True)
        
        # *distract_1* updates
        if distract_1.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_1.frameNStart = frameN  # exact frame index
            distract_1.tStart = t  # local t and not account for scr refresh
            distract_1.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_1, 'tStartRefresh')  # time at next scr refresh
            distract_1.setAutoDraw(True)
        
        # *distract_2* updates
        if distract_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_2.frameNStart = frameN  # exact frame index
            distract_2.tStart = t  # local t and not account for scr refresh
            distract_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_2, 'tStartRefresh')  # time at next scr refresh
            distract_2.setAutoDraw(True)
        
        # *distract_3* updates
        if distract_3.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_3.frameNStart = frameN  # exact frame index
            distract_3.tStart = t  # local t and not account for scr refresh
            distract_3.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_3, 'tStartRefresh')  # time at next scr refresh
            distract_3.setAutoDraw(True)
        
        # *distract_4* updates
        if distract_4.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_4.frameNStart = frameN  # exact frame index
            distract_4.tStart = t  # local t and not account for scr refresh
            distract_4.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_4, 'tStartRefresh')  # time at next scr refresh
            distract_4.setAutoDraw(True)
        
        # *distract_5* updates
        if distract_5.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_5.frameNStart = frameN  # exact frame index
            distract_5.tStart = t  # local t and not account for scr refresh
            distract_5.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_5, 'tStartRefresh')  # time at next scr refresh
            distract_5.setAutoDraw(True)
        
        # *distract_6* updates
        if distract_6.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_6.frameNStart = frameN  # exact frame index
            distract_6.tStart = t  # local t and not account for scr refresh
            distract_6.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_6, 'tStartRefresh')  # time at next scr refresh
            distract_6.setAutoDraw(True)
        
        # *distract_7* updates
        if distract_7.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_7.frameNStart = frameN  # exact frame index
            distract_7.tStart = t  # local t and not account for scr refresh
            distract_7.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_7, 'tStartRefresh')  # time at next scr refresh
            distract_7.setAutoDraw(True)
        
        # *distract_8* updates
        if distract_8.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_8.frameNStart = frameN  # exact frame index
            distract_8.tStart = t  # local t and not account for scr refresh
            distract_8.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_8, 'tStartRefresh')  # time at next scr refresh
            distract_8.setAutoDraw(True)
        
        # *gaze_position_1* updates
        if gaze_position_1.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            gaze_position_1.frameNStart = frameN  # exact frame index
            gaze_position_1.tStart = t  # local t and not account for scr refresh
            gaze_position_1.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(gaze_position_1, 'tStartRefresh')  # time at next scr refresh
            gaze_position_1.setAutoDraw(True)
        if gaze_position_1.status == STARTED:  # only update if drawing
            gaze_position_1.setPos((gaze_x, gaze_y))
        
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
    eye_tracker.setRecordingState(False)
    #win.getMovieFrame()
    #win.saveMovieFrames('data/pngs/search_{}.png'.format(trials.thisN), codec='png')
    #print('Eye position could not be read on ' + str(missed_samples) + ' frames during the trial.')
    
    trials.addData('target.started', target.tStartRefresh)
    trials.addData('target.stopped', target.tStopRefresh)
    trials.addData('distract_1.started', distract_1.tStartRefresh)
    trials.addData('distract_1.stopped', distract_1.tStopRefresh)
    trials.addData('distract_2.started', distract_2.tStartRefresh)
    trials.addData('distract_2.stopped', distract_2.tStopRefresh)
    trials.addData('distract_3.started', distract_3.tStartRefresh)
    trials.addData('distract_3.stopped', distract_3.tStopRefresh)
    trials.addData('distract_4.started', distract_4.tStartRefresh)
    trials.addData('distract_4.stopped', distract_4.tStopRefresh)
    trials.addData('distract_5.started', distract_5.tStartRefresh)
    trials.addData('distract_5.stopped', distract_5.tStopRefresh)
    trials.addData('distract_6.started', distract_6.tStartRefresh)
    trials.addData('distract_6.stopped', distract_6.tStopRefresh)
    trials.addData('distract_7.started', distract_7.tStartRefresh)
    trials.addData('distract_7.stopped', distract_7.tStopRefresh)
    trials.addData('distract_8.started', distract_8.tStartRefresh)
    trials.addData('distract_8.stopped', distract_8.tStopRefresh)
    trials.addData('gaze_position_1.started', gaze_position_1.tStartRefresh)
    trials.addData('gaze_position_1.stopped', gaze_position_1.tStopRefresh)
    # the Routine "trial" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # ------Prepare to start Routine "feedback"-------
    continueRoutine = True
    routineTimer.add(0.500000)
    # update component parameters for each repeat
    target_2.setPos((x_pos[0], y_pos[0]))
    distract.setOpacity(opacity_1)
    distract.setPos((x_pos[1], y_pos[1]))
    distract_9.setOpacity(opacity_2)
    distract_9.setPos((x_pos[2], y_pos[2]))
    distract_10.setOpacity(opacity_3)
    distract_10.setPos((x_pos[3], y_pos[3]))
    distract_11.setOpacity(opacity_4)
    distract_11.setPos((x_pos[4], y_pos[4]))
    distract_12.setOpacity(opacity_5)
    distract_12.setPos((x_pos[5], y_pos[5]))
    distract_13.setOpacity(opacity_6)
    distract_13.setPos((x_pos[6], y_pos[6]))
    distract_14.setOpacity(opacity_7)
    distract_14.setPos((x_pos[7], y_pos[7]))
    distract_15.setOpacity(opacity_8)
    distract_15.setPos((x_pos[8], y_pos[8]))
    # keep track of which components have finished
    feedbackComponents = [target_2, distract, distract_9, distract_10, distract_11, distract_12, distract_13, distract_14, distract_15, gaze_position_2]
    for thisComponent in feedbackComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    feedbackClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "feedback"-------
    while continueRoutine and routineTimer.getTime() > 0:
        # get current time
        t = feedbackClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=feedbackClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *target_2* updates
        if target_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            target_2.frameNStart = frameN  # exact frame index
            target_2.tStart = t  # local t and not account for scr refresh
            target_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(target_2, 'tStartRefresh')  # time at next scr refresh
            target_2.setAutoDraw(True)
        if target_2.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > target_2.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                target_2.tStop = t  # not accounting for scr refresh
                target_2.frameNStop = frameN  # exact frame index
                win.timeOnFlip(target_2, 'tStopRefresh')  # time at next scr refresh
                target_2.setAutoDraw(False)
        
        # *distract* updates
        if distract.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract.frameNStart = frameN  # exact frame index
            distract.tStart = t  # local t and not account for scr refresh
            distract.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract, 'tStartRefresh')  # time at next scr refresh
            distract.setAutoDraw(True)
        if distract.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract.tStop = t  # not accounting for scr refresh
                distract.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract, 'tStopRefresh')  # time at next scr refresh
                distract.setAutoDraw(False)
        
        # *distract_9* updates
        if distract_9.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_9.frameNStart = frameN  # exact frame index
            distract_9.tStart = t  # local t and not account for scr refresh
            distract_9.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_9, 'tStartRefresh')  # time at next scr refresh
            distract_9.setAutoDraw(True)
        if distract_9.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_9.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_9.tStop = t  # not accounting for scr refresh
                distract_9.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_9, 'tStopRefresh')  # time at next scr refresh
                distract_9.setAutoDraw(False)
        
        # *distract_10* updates
        if distract_10.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_10.frameNStart = frameN  # exact frame index
            distract_10.tStart = t  # local t and not account for scr refresh
            distract_10.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_10, 'tStartRefresh')  # time at next scr refresh
            distract_10.setAutoDraw(True)
        if distract_10.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_10.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_10.tStop = t  # not accounting for scr refresh
                distract_10.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_10, 'tStopRefresh')  # time at next scr refresh
                distract_10.setAutoDraw(False)
        
        # *distract_11* updates
        if distract_11.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_11.frameNStart = frameN  # exact frame index
            distract_11.tStart = t  # local t and not account for scr refresh
            distract_11.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_11, 'tStartRefresh')  # time at next scr refresh
            distract_11.setAutoDraw(True)
        if distract_11.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_11.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_11.tStop = t  # not accounting for scr refresh
                distract_11.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_11, 'tStopRefresh')  # time at next scr refresh
                distract_11.setAutoDraw(False)
        
        # *distract_12* updates
        if distract_12.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_12.frameNStart = frameN  # exact frame index
            distract_12.tStart = t  # local t and not account for scr refresh
            distract_12.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_12, 'tStartRefresh')  # time at next scr refresh
            distract_12.setAutoDraw(True)
        if distract_12.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_12.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_12.tStop = t  # not accounting for scr refresh
                distract_12.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_12, 'tStopRefresh')  # time at next scr refresh
                distract_12.setAutoDraw(False)
        
        # *distract_13* updates
        if distract_13.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_13.frameNStart = frameN  # exact frame index
            distract_13.tStart = t  # local t and not account for scr refresh
            distract_13.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_13, 'tStartRefresh')  # time at next scr refresh
            distract_13.setAutoDraw(True)
        if distract_13.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_13.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_13.tStop = t  # not accounting for scr refresh
                distract_13.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_13, 'tStopRefresh')  # time at next scr refresh
                distract_13.setAutoDraw(False)
        
        # *distract_14* updates
        if distract_14.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_14.frameNStart = frameN  # exact frame index
            distract_14.tStart = t  # local t and not account for scr refresh
            distract_14.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_14, 'tStartRefresh')  # time at next scr refresh
            distract_14.setAutoDraw(True)
        if distract_14.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_14.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_14.tStop = t  # not accounting for scr refresh
                distract_14.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_14, 'tStopRefresh')  # time at next scr refresh
                distract_14.setAutoDraw(False)
        
        # *distract_15* updates
        if distract_15.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            distract_15.frameNStart = frameN  # exact frame index
            distract_15.tStart = t  # local t and not account for scr refresh
            distract_15.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(distract_15, 'tStartRefresh')  # time at next scr refresh
            distract_15.setAutoDraw(True)
        if distract_15.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > distract_15.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                distract_15.tStop = t  # not accounting for scr refresh
                distract_15.frameNStop = frameN  # exact frame index
                win.timeOnFlip(distract_15, 'tStopRefresh')  # time at next scr refresh
                distract_15.setAutoDraw(False)
        
        # *gaze_position_2* updates
        if gaze_position_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            gaze_position_2.frameNStart = frameN  # exact frame index
            gaze_position_2.tStart = t  # local t and not account for scr refresh
            gaze_position_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(gaze_position_2, 'tStartRefresh')  # time at next scr refresh
            gaze_position_2.setAutoDraw(True)
        if gaze_position_2.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > gaze_position_2.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                gaze_position_2.tStop = t  # not accounting for scr refresh
                gaze_position_2.frameNStop = frameN  # exact frame index
                win.timeOnFlip(gaze_position_2, 'tStopRefresh')  # time at next scr refresh
                gaze_position_2.setAutoDraw(False)
        if gaze_position_2.status == STARTED:  # only update if drawing
            gaze_position_2.setPos((gaze_x, gaze_y))
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in feedbackComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "feedback"-------
    for thisComponent in feedbackComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    trials.addData('target_2.started', target_2.tStartRefresh)
    trials.addData('target_2.stopped', target_2.tStopRefresh)
    trials.addData('distract.started', distract.tStartRefresh)
    trials.addData('distract.stopped', distract.tStopRefresh)
    trials.addData('distract_9.started', distract_9.tStartRefresh)
    trials.addData('distract_9.stopped', distract_9.tStopRefresh)
    trials.addData('distract_10.started', distract_10.tStartRefresh)
    trials.addData('distract_10.stopped', distract_10.tStopRefresh)
    trials.addData('distract_11.started', distract_11.tStartRefresh)
    trials.addData('distract_11.stopped', distract_11.tStopRefresh)
    trials.addData('distract_12.started', distract_12.tStartRefresh)
    trials.addData('distract_12.stopped', distract_12.tStopRefresh)
    trials.addData('distract_13.started', distract_13.tStartRefresh)
    trials.addData('distract_13.stopped', distract_13.tStopRefresh)
    trials.addData('distract_14.started', distract_14.tStartRefresh)
    trials.addData('distract_14.stopped', distract_14.tStopRefresh)
    trials.addData('distract_15.started', distract_15.tStartRefresh)
    trials.addData('distract_15.stopped', distract_15.tStopRefresh)
    trials.addData('gaze_position_2.started', gaze_position_2.tStartRefresh)
    trials.addData('gaze_position_2.stopped', gaze_position_2.tStopRefresh)
    thisExp.nextEntry()
    
# completed 20 repeats of 'trials'

io.quit()
eye_tracker.setConnectionStae(False)

# Flip one final time so any remaining win.callOnFlip() 
# and win.timeOnFlip() tasks get executed before quitting
win.flip()

# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename+'.csv', delim='auto')
thisExp.saveAsPickle(filename)
logging.flush()
# make sure everything is closed down
thisExp.abort()  # or data files will save again on exit
win.close()
core.quit()
