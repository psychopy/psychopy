#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of text rendering in pyglet, including:
- how to specify fonts
- unicode
- rotating text
- mirror-image
- bidirectional and reshaped Arabic/Farsi text
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

# Initialize some stimuli.
# Note that in Python 3 we no longer need to create special unicode strings
# with a u'' prefix, as all strings are unicode. For the time being, we 
# retain the prefix in this demo, for backwards compatibility for people 
# running PsychoPy under Python 2.7
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

# By default, right-to-left languages like Hebrew are often shown in
# reversed order. Additionally, Arabic-based text by default is shown
# with characters in their isolated form, rather than flowing correctly
# into their neighbours. We can use the invisible \u200E left-to-right
# control character to resolve ambiguous transitions between text 
# directions (for example, to determine in which directional run a 
# punctuation character belongs).
raw_Farsi = visual.TextStim(win,
    text = u'Raw Farsi text: \n \u200E خوش آمدید 1999',
    units = 'norm', height = 0.06, color = 'DarkRed',
    pos = (-0.9, 0.8), font = 'Arial',
    wrapWidth = 1.0, alignHoriz = 'left',
    languageStyle = 'LTR') # left-to-right
# We correct these issues by setting setting the languageStyle to be
# 'bidirectional' (sufficient for Hebrew, for example) or 'Arabic'
# (which additionally does the reshaping of individual characters
# needed for languages based on the Arabic alphabet):
corrected_Farsi = visual.TextStim(win,
    text = u'Reshaped & bidirectional: \n \u200E خوش آمدید 1999',
    units = 'norm', height = 0.06, color = 'DarkRed',
    pos = (-0.9, 0.6), font = 'Arial',
    wrapWidth = 1.0, alignHoriz = 'left',
    languageStyle = 'Arabic') # RTL + reshaped
# Please give the developers feedback if there are display issues in
# other languages that you are familiar with.

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
    raw_Farsi.draw()
    corrected_Farsi.draw()

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
