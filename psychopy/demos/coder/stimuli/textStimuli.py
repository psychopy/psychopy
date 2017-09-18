#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of text rendering in pyglet, including:
- how to specify fonts
- unicode
- rotating text
- mirror-image
"""

from __future__ import division

from psychopy import visual, core, event

# Create a window to draw in
win = visual.Window((800.0, 800.0), allowGUI=False, winType='pyglet',
            monitor='testMonitor', units ='deg', screen=0)
win.recordFrameIntervals = True

# Choose some fonts. If a list is provided, the first font found will be used.
fancy = ['Monotype Corsiva', 'Palace Script MT', 'Edwardian Script ITC']
sans = ['Gill Sans MT', 'Arial', 'Helvetica', 'Verdana']
serif = ['Times', 'Times New Roman']
comic = 'Comic Sans MS'  # the short name won't work

# Initialize some stimuli
fpsText = visual.TextStim(win,
    units='norm', height = 0.1,
    pos=(-0.98, -0.98), text='starting...',
    font=sans,
    alignHoriz = 'left', alignVert='bottom',
    color='BlanchedAlmond')
rotating = visual.TextStim(win, text="Fonts \nrotate!", pos=(0, 0),  # and can have line breaks
    color=[-1.0, -1, 1],
    units='deg',
    ori=0, height = 1.0,
    font=comic)
unicodeStuff = visual.TextStim(win,
    # you can find the unicode character value by searching online
    text = u"unicode (eg \u03A8 \u040A \u03A3)",
    color='black',
    font=serif, pos=(0, 3),
    height = 1)
psychopyTxt = visual.TextStim(win, color='#FFFFFF',
    text = u"PsychoPy \u00A9Jon Peirce",
    units='norm', height=0.1,
    pos=[0.95, 0.95], alignHoriz='right', alignVert='top',
    font=fancy)
longSentence = visual.TextStim(win,
    text = u"Very long sentences can wrap", wrapWidth=0.4,
    units='norm', height=0.05, color='DarkSlateBlue',
    pos=[0.95, -0.95], alignHoriz='right', alignVert='bottom')
mirror = visual.TextStim(win, text="mirror mirror",
    units='norm', height=0.12, color='Silver',
    pos=[0, -0.5], alignHoriz='center',
    flipHoriz=True)
trialClock = core.Clock()
t = lastFPSupdate = 0

# Continues the loop until any key is pressed
while not event.getKeys():
    t = trialClock.getTime()
    mirror.draw()
    rotating.ori += 1
    rotating.draw()
    unicodeStuff.draw()
    longSentence.draw()

    # update the fps text every second
    if t - lastFPSupdate > 1:
        fpsText.text = "%i fps" % win.fps()
        lastFPSupdate += 1
    fpsText.draw()
    psychopyTxt.draw()

    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
