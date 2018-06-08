#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy2 Experiment Builder (v1.85.3),
    on October 26, 2017, at 10:36
If you publish work using this script please cite the PsychoPy publications:
    Peirce, JW (2007) PsychoPy - Psychophysics software in Python.
        Journal of Neuroscience Methods, 162(1-2), 8-13.
    Peirce, JW (2009) Generating stimuli for neuroscience using PsychoPy.
        Frontiers in Neuroinformatics, 2:10. doi: 10.3389/neuro.11.010.2008
"""

from __future__ import absolute_import, division
from psychopy import locale_setup, sound, gui, visual, core, data, event, logging

from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle
from time import sleep, clock
import os  # handy system and path functions
import sys  # to get file system encoding

# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))#.decode(sys.getfilesystemencoding())
os.chdir(_thisDir)

# Store info about the experiment session
expName = u'crsTest'  # from the Builder filename that created this script
expInfo = {u'Device': u'Display++', 
           u'Analog': u'No',
           u'Touch screen': u'Yes',
           u'Button box': u'CB6',
           u'Monitor': u'Display++160'}
dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
#filename = _thisDir + os.sep + u'data' + os.sep + '%s_%s_%s' %(expInfo['Device'], expInfo['Analog'], expInfo['Touch Screen'], expInfo['Button box'], expInfo['date'])

# An ExperimentHandler isn't essential but helps with data saving
#thisExp = data.ExperimentHandler(name=expName, version='',
#    extraInfo=expInfo, runtimeInfo=None,
#    originPath=None,
#    savePickle=True, saveWideText=True,
#    dataFileName=filename)
# save a log file for detail verbose info
#logFile = logging.LogFile(filename+'.log', level=logging.EXP)
#logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

# Start Code - component code to be run before the window creation

# Setup the Window
print("Open window")
win = visual.Window(
    size=(800, 600), fullscr=True, screen=1,
    allowGUI=False, allowStencil=False,
    monitor=expInfo['Monitor'], color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True,
    units='deg')
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess

# Initialize components for Routine "preflight"
preflightClock = core.Clock()
import sys
from psychopy import monitors, filters, gamma, visual 
from psychopy.visual import gamma
from psychopy.hardware import crs
from scipy import misc


mon=monitors.Monitor(expInfo['Monitor'],distance=56)
print("open CRS")
if expInfo['Device']=='Bits++':
    bits = crs.BitsPlusPlus(win, mode='bits++',rampType=1, frameRate=120) 
if expInfo['Device']=='Bits#':
    bits = crs.BitsSharp(win, mode='bits++',checkConfigLevel=1) 
if expInfo['Device']=='Display++':
    if expInfo['Touch screen']=="Yes":
        bits = crs.DisplayPlusPlusTouch(win, mode='bits++',checkConfigLevel=1) 
    else:
        bits = crs.DisplayPlusPlus(win, mode='bits++',checkConfigLevel=1) 

if  expInfo['Device'] != 'Bits++':
    #bits = crs.BitsSharp(win, mode='bits++') 
    #gamma.setGamma(win.winHandle._dc, 1.0, 1)
    bits.sendMessage('$TemporalDithering=[ON]\r')
    bits.read(timeout=0.1)
    bits.sendMessage('$VideoFrameRate\r')
    bits.read(timeout=0.1)
    bits.sendMessage('$enableGammaCorrection=[invGammaPF225fA.txt]\r')
    bits.read(timeout=0.1)
    bits.sendMessage('$EnableTouchScreen=[OFF]\e')
    bits.read(timeout=0.1)
    bits.sendMessage('$Stop\r')
    msg='a'
    while len(msg)>0:
        msg=bits.read(timeout=0.1)
    print("OK I seem to have cleared the buffer now")

    print("Connect DOUT1 (pin 2) to DIN7 (pin 21)")
    print("Connect DOUT5 (pin 6) to DIN8 (pin 24)")
    print("Connect DOUT6 (pin 7) to DIN9 (pin 25)")
    if expInfo['Device'] == 'Bits#' or expInfo['Analog'] == 'Yes':
        print("Connect Analog OUT 1 TO Analog IN 1")
else:
    print("Connect DOUT1 (pin2) to Oscilloscope A")
    print("Connect DOUT5 (pin6) to Oscilloscope B")

sleep(10)

grating = visual.GratingStim(
    win=win, name='grating',units='norm', 
    tex='sin', mask=None,
    ori=0, pos=(0,0), size=(1, 1), sf=5, phase=1.0,
    color=[1,1,1], colorSpace='rgb', opacity=1,blendmode='avg',
    texRes=128, interpolate=True, depth=-2.0)

#LUT test
print("1: testing look up tables")
print("Should see pulsating grating")
frameN=-1
while frameN < bits.frameRate*5:
    # get current time
    frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
    # update/draw components on each frame
    #bits.setAnalog(AOUT1 = 5*sin(t*50), AOUT2 = 5*cos(t*50))
    # *thanksMsg* updates
    if frameN == 0:
        grating.setAutoDraw(True)
    bits.setContrast((sin(np.pi*frameN/bits.frameRate)))
    win.flip()
grating.setAutoDraw(False)
bits.setContrast(1.0)
win.flip()

#Trigger and goggle tests
print("2a: Testing triggers")
bits.setTrigger(0b0000001111,0.002,0.002)
bits.startTrigger()
bits.win.flip()
T=clock()
if expInfo['Device'] != 'Bits++':
    bits.startStatusLog()
    sleep(5)
    bits.stopStatusLog()
    while clock()-T<5:
        bits.win.flip()
    vals = bits.getAllStatusValues()
    print("All status values")
    for i in range(20):
        print(vals[i])
    print("DIN7 should change lots")
    vals = bits.getAllStatusEvents()
    print("All status events")
    for i in range(20):
        print(vals[i])
    print("Input 7 should change lots")
else:
    print("Should observe 2ms pulses on Ch A")
    while clock()-T<5:
        bits.win.flip()


bits.stopTrigger()
bits.win.flip()
sleep(10)
if expInfo['Device'] != 'Bits++':
    bits.flush()




print("2b: test goggles")
bits.setTrigger(0b1111111101,0.0,0.004)
#bits.startTrigger()
bits.startGoggles(left=0,right=1)
bits.win.flip()
T=clock()
if expInfo['Device'] != 'Bits++':
    bits.startStatusLog()
    while clock()-T<5:
        bits.win.flip()
    bits.stopStatusLog()
    bits.flush()
    vals = bits.getAllStatusValues()
    print("All status values")
    for i in range(20):
        print(vals[i])
    print("DIN8 should change lots")
    vals = bits.getAllStatusEvents()
    print("All status events")
    for i in range(20):
        print(vals[i])
    print("Input 8 should change lots")
else:
    print("Should observe pulses on Ch B")
    while clock()-T<5:
        sleep(0.004)
        bits.win.flip()

#sleep(1)
bits.stopGoggles()
#bits.stopTrigger()
bits.win.flip()
sleep(10)
if expInfo['Device'] != 'Bits++':
    bits.flush()

print("2c:Goggles with  triggers")
bits.startGoggles()
bits.setTrigger(0b0000001111,0.0,0.004)
bits.startTrigger()
bits.win.flip()
T=clock()
if expInfo['Device'] != 'Bits++':
    bits.startStatusLog()
    while clock()-T<5:
        bits.win.flip()
    bits.stopStatusLog()
    bits.flush()
    vals = bits.getAllStatusValues()
    print("All status values")
    for i in range(20):
        print(vals[i])
    print("DIN7 and DIN8 should change lots")
    vals = bits.getAllStatusEvents()
    print("All status events")
    for i in range(20):
        print(vals[i])
    print("Input 7 and Input 8 should change lots")
else:
    print("Should observe 4ms pulses on Ch A")
    print("Should observe pulses on Ch B")
    while clock()-T<5:
        sleep(0.004)
        bits.win.flip()

bits.stopGoggles()
bits.stopTrigger()
bits.win.flip()
sleep(10)
if expInfo['Device'] != 'Bits++':
    bits.flush()

if expInfo['Device'] == 'Bits++':
    print("All tests done")
else:
    bits.flush()
    print("2d: Single shot trigger and RTBox Input via DIN")
    bits.pollStatus()
    valD = bits.getDigitalWord()
    print(bin(valD['DWORD']))
    bits.RTBoxEnable(mode=['down'], map=[('btn1','Din9')])#[('btn0','Din0'),('btn1','Din1')])
    bits.setTrigger(0b1111111,0,0.004)
    bits.startTrigger()
    bits.win.flip()
    bits.stopTrigger()
    bits.win.flip()
    btn=bits.RTBoxWait()
    print(btn)
    bits.RTBoxDisable()
    sleep(5)
    print("3a: Beep test")
    bits.beep(400,0.5)
    sleep(0.5)
    # bitsSharp tests
    print("3b: Clock Reset test")
    bits.resetClock()
    bits.win.flip()
    sleep(1)
    T=clock()
    bits.pollStatus()
    print("Time taken to poll status = ",clock()-T)
    val = bits.getStatus()
    print("Time recorded by devise should be about 1s. Actually = ", val.time)
    sleep(5)
    bits.flush()
    bits.sendMessage('$Stop\r')

    print("4a: RTBox test")
    bits.flush()
    if expInfo['Button box'] == 'CB6':
        bits.RTBoxEnable(mode=['CB6','Down'])
        print("Press a button on the Box")
        button = bits.RTBoxWait()
        print(button)
    elif expInfo['Button box'] == 'IO6':
        bits.RTBoxEnable(mode=['IO','Down'])
        print("Press one of first 3 buttons on the Box")
        button = bits.RTBoxWait()
        print(button)
    elif expInfo['Button box'] == 'IO':
        bits.RTBoxEnable(mode=['IO','Down'])
        print("Press of first 3 buttons on the Box")
        button = bits.RTBoxWait()
        print(button)
        
    print("4a: Clock and RTBox calibration test")
    bits.RTBoxCalibrate()
    bits.RTBoxDisable()
    bits.flush()
    
    if expInfo['Device'] == 'Bits#' or expInfo['Analog'] == 'Yes':
        print("5: Analog tests")
        print("5a: Analog only")
        #bits.setAnalog(2,2)
        #bits.startAnalog()
        bits.sendAnalog(2,2)
        sleep(1)
        bits.pollStatus()
        val = bits.getAnalog()
        bits.win.flip()
        #bits.stopAnalog
        print("Analog 1 should be = 2v")
        print(val['ADC'])
        sleep(5)
        bits.flush()
        print("5b: Analog and triggers")
        bits.setAnalog(3,3)
        bits.setTrigger(0b1111111101,0.0,0.0084)
        bits.startTrigger()
        bits.startAnalog()
        bits.win.flip()
        sleep(1)
        bits.pollStatus()
        valA = bits.getAnalog()
        valD = bits.getDigitalWord()
        bits.stopAnalog
        bits.stopTrigger()
        print("Analog 1 should be = 3v")
        print(valA['ADC'])
        print("Digital word should have bit 8 low")
        print(bin(valD['DWORD']))
        sleep(5)
        bits.flush()
        
    if expInfo['Device'] == 'Display++' and expInfo['Touch screen'] == 'Yes':
        print("6: Touch Screen test")
        print("6a: Touch the screen")
        bits.touchEnable()
        val=bits.touchWait()
        bits.touchDisable()
        print(val)
        
        sleep(5)
        print("6b: Touch the screen again")
        bits.touchEnable()
        while not bits.touchPressed():
            continue
        vals=bits.getAllTouchResponses()
        bits.touchDisable()
        for i in range(len(vals)):
            print(vals[i])
            
        sleep(5)
        bits.startTouchLog()
        print("6c: Touch the screen lots")
        sleep(10)
        bits.stopTouchLog()
        bits.getTouchLog()
        vals=bits.getTouchEvents()
        for i in range(len(vals)):
            print(vals[i])
    print("All tests done")
del bits
win.close()
core.quit()
