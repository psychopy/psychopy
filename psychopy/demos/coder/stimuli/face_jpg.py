#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo shows you different image presentation using visual.ImageStim and
visual.GratinGstim. It introduces some of the many attributes of these stimulus
types.
"""

# Import the modules that we need in this script
from psychopy import core, visual, event

# Create a window to draw in
win = visual.Window(size=(600, 600), color='black')

# An image using ImageStim.
image = visual.ImageStim(win, image='face.jpg')

# We can also use the image as a mask (mask="face.jpg") for other stimuli!
grating = visual.GratingStim(win,
    pos=(-0.5, 0),
    tex='sin',
    mask='face.jpg',
    color='green')
grating.size = (0.5, 0.5)  # attributes can be changed after initialization
grating.sf = 1.0

# Initiate clock to keep track of time
clock = core.Clock()
while clock.getTime() < 12 and not event.getKeys():
    # Set dynamic attributes. There's a lot of different possibilities.
    # so look at the documentation and try playing around here.
    grating.phase += 0.01  # Advance phase by 1/100th of a cycle
    grating.pos += (0.001, 0)  # Advance on x but not y
    image.ori *=  1.01  # Accelerating orientation (1% on every frame)
    image.size -= 0.001  # Decrease size uniformly on x and y
    if image.opacity >=  0:  # attributes can be referenced
        image.opacity -= 0.001  # Decrease opacity

    # Show the result of all the above
    image.draw()
    grating.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
