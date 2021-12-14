#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of several visual stimuli depending on the mouse position.
"""

from psychopy import visual, event, core
import numpy

win = visual.Window([600, 600], color='black')

gabor = visual.GratingStim(win, mask='gauss', pos=[-0.5, -0.5], color=[0, 0, 1], sf=5, ori=30)
movie = visual.MovieStim3(win, 'jwpIntro.mp4', units='pix', pos=[100, 100], size=[160, 120])
txt = u"unicode (eg \u03A8 \u040A \u03A3)"
text = visual.TextStim(win, pos=[0.5, -0.5], text=txt, font=['Times New Roman'])
faceRGB = visual.ImageStim(win, image='face.jpg', pos=[-0.5, 0.5])

mouse = event.Mouse()
instr = visual.TextStim(win, text='move the mouse around')

t = 0.0
while not event.getKeys() and not mouse.getPressed()[0]:
    # get mouse events
    mouse_dX, mouse_dY = mouse.getRel()

    gabor.ori -= mouse_dY * 10
    text.ori += mouse_dY * 10
    faceRGB.ori += mouse_dY * 10
    movie.ori -= mouse_dY * 10

    t += 1/60.0
    gabor.phase = t * 2.0
    gabor.draw()
    text.color = [numpy.sin(t * 2), 0, 1]
    text.draw()
    faceRGB.draw()
    movie.draw()

    instr.draw()

    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
