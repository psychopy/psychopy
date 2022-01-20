#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Determine screen gamma using motion-nulling method
of Ledgeway and Smith, 1994, Vision Research, 34, 2727-2740
A similar system had been used early for chromatic isoluminance:
Anstis SM, Cavanagh P. A minimum motion technique for judging equiluminance.
In: Sharpe MJD & LT Colour vision: Psychophysics and physiology. London: Academic Press; 1983. pp. 66-77.

Instructions: on each trial press the up/down cursor keys depending on
the apparent direction of motion of the bars.
"""

from psychopy import visual, core, event, gui, data
from psychopy.tools.filetools import fromFile, toFile
from psychopy.visual import filters
import numpy as num
import time

try:
    # try to load previous info
    info = fromFile('info_gamma.pickle')
    print(info)
except Exception:
    # if no file use some defaults
    info = {}
    info['lumModNoise'] = 0.5
    info['lumModLum'] = 0.1
    info['contrastModNoise'] = 1.0
    info['observer'] = ''
    info['highGamma'] = 3.0
    info['lowGamma'] = 0.8
    info['nTrials'] = 50
dlg = gui.DlgFromDict(info)
# save to a file for future use (ie storing as defaults)
if dlg.OK:
    toFile('info_gamma.pickle', info)
else:
    core.quit()  # user cancelled. quit
print(info)

info['timeStr']=time.strftime("%b_%d_%H%M", time.localtime())
nFrames = 3
cyclesTime = 2
cyclesSpace = 2
pixels = 128

win = visual.Window((1024, 768), units='pix', allowGUI=True, bitsMode=None)
visual.TextStim(win, text='building stimuli').draw()

win.flip()

globalClock = core.Clock()

# for luminance modulated noise
noiseMatrix = num.random.randint(0, 2, [pixels, pixels])  # * noiseContrast
noiseMatrix = noiseMatrix * 2.0-1  # into range -1: 1

stimFrames = []; lumGratings=[]
# create the 4 frames of the sequence (luminance and contrast modulated noise in quadrature)
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=0))
stimFrames.append(visual.GratingStim(win, texRes=pixels, mask='circle',
        size=pixels * 2, sf=1.0 / pixels, ori=90,
        tex= (noiseMatrix * info['lumModNoise'] + lumGratings[0] * info['lumModLum'])
        ))
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=90) / 2.0 + 0.5)
stimFrames.append(visual.GratingStim(win, texRes=pixels, mask='circle',
        size=pixels * 2, sf=1.0/pixels, ori=90,
        tex= (noiseMatrix * info['contrastModNoise'] * lumGratings[1])
        ))
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=180))
stimFrames.append(visual.GratingStim(win, texRes=pixels, mask='circle',
        size=pixels * 2, sf=1.0/pixels, ori=90,
        tex= (noiseMatrix * info['lumModNoise'] + lumGratings[2] * info['lumModLum'])
        ))
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=270) / 2.0 + 0.5)
stimFrames.append(visual.GratingStim(win, texRes=pixels, mask='circle',
        size=pixels * 2, sf=1.0/pixels, ori=90,
        tex= (noiseMatrix * info['contrastModNoise'] * lumGratings[3])
        ))

stairCases = []
# two staircases - one from the top, one from below - to average
stairCases.append(data.StairHandler(startVal=info['highGamma'], nTrials=info['nTrials'],
        stepSizes=[0.5, 0.5, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05], stepType='lin',
        nUp=1, nDown=1))
stairCases.append(data.StairHandler(startVal=info['lowGamma'], nTrials=info['nTrials'],
        stepSizes=[0.5, 0.5, 0.1, 0.1, 0.1, 0.1, 0.05, 0.05], stepType='lin',
        nUp=1, nDown=1))

def getResponse(direction):
    """if subject said up when direction was up ( + 1) then increase gamma
    Otherwise, decrease gamma"""
    event.clearEvents()  # clear the event buffer to start with

    while 1:  # forever until we return
        for key in event.getKeys():
            # quit
            if key in ['escape', 'q']:
                win.close()
                # win.bits.reset()
                core.quit()
            # valid response - check to see if correct
            elif key in ['down', 'up']:
                if ((key in ['down'] and direction == -1) or
                        (key in ['up'] and direction == +1)):
                    return 0
                else:
                    return 1
            else:
                print("hit DOWN or UP (or Esc) (You hit %s)" %key)

def presentStimulus(direction):
    """Present stimulus drifting in a given direction (for low gamma)
    where:
        direction = + 1(up) or -1(down)
    """
    win.fps()

    startPhase = num.random.random()
    if direction == 1:
        frameIndices = num.arange(0, 4)
    else:
        frameIndices = num.arange(3, -1, -1)

    for cycles in range(cyclesTime):
        # cycle through the 4 frames
        for ii in frameIndices:
            thisStim = stimFrames[ii]
            thisStim.setPhase(startPhase)
            for n in range(nFrames):
                # present for several constant frames (TF)
                thisStim.draw()
                win.flip()

    # then blank the screen
    win.flip()

# run the staircase
for trialN in range(info['nTrials']):
    for stairCase in stairCases:
        thisGamma = next(stairCase)
        t = globalClock.getTime()
        win.gamma = [thisGamma, thisGamma, thisGamma]

        direction = num.random.randint(0, 2) * 2-1  # a random number -1 or 1
        presentStimulus(direction)

        ans = getResponse(direction)
        stairCase.addData(ans)

win.flip()
core.wait(0.5)

win.close()

# save data
fileName = gui.fileSaveDlg('.', '%s_%s' %(info['observer'], info['timeStr']))
stairCases[1].saveAsPickle(fileName + 'hi')
stairCases[1].saveAsText(fileName + 'hi')
stairCases[0].saveAsPickle(fileName + 'lo')
stairCases[0].saveAsText(fileName + 'lo')

print('That took %.1fmins' % (globalClock.getTime() / 60.0))

core.quit()

# The contents of this file are in the public domain.
