#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of gabor dots, using autodraw.
"""

from psychopy import visual, core, event

# Create a window to draw in
win = visual.Window((600, 600), allowGUI=False,
                      monitor='testMonitor', units='deg')

# Initialize
gabor_shape = visual.GratingStim(win, mask='gauss', sf=3)
dotPatch = visual.DotStim(win, color='black',
    dotLife=5,  # lifetime of a dot in frames (if this is long density artifacts can occur in the stimulus)
    signalDots='different',  # are the signal and noise dots 'different' or 'same' popns (see Scase et al)
    noiseDots='direction',  # do the noise dots follow random- 'walk', 'direction', or 'position'
    fieldPos=[0.0, 0.0], nDots=40, fieldSize=3,
    speed=0.05, fieldShape='circle', coherence=0.5,
    element=gabor_shape, name='dotPatch')
message = visual.TextStim(win, text='Any key to quit', pos=(0, -5))

# always draw
dotPatch.autoDraw = True
message.autoDraw = True

while not event.getKeys():
    win.flip()  # redraw the buffer, autodraw does the rest

win.close()
core.quit()

# The contents of this file are in the public domain.
