#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo for psychopy.visual.ShapeStim.contains() and .overlaps()

Also inherited by various other stimulus types.
"""

from psychopy import visual, event, core

win = visual.Window(size=(500, 500), monitor='testMonitor', units='norm')
mouse = event.Mouse()
txt = 'click the shape to quit\nscroll to adjust circle'
instr = visual.TextStim(win, text=txt, pos=(0, -.7), opacity=0.5)
msg = visual.TextStim(win, text=' ', pos=(0, -.4))

# a target polygon (strange shape):
shape = visual.ShapeStim(win, fillColor='darkblue', lineColor=None,
    vertices=[(-0.02, -0.0), (-.8, .2), (0, .6), (.1, 0.06), (.8, .3), (.6, -.4)])

# define a buffer zone around the mouse for proximity detection:
# use pix units just to show that it works to mix (shape and mouse use norm units)
bufzone = visual.Circle(win, radius=30, edges=13, units='pix')

# loop until detect a click inside the shape:
while not mouse.isPressedIn(shape):
    instr.draw()
    # dynamic buffer zone around mouse pointer:
    bufzone.pos = mouse.getPos() * win.size / 2  # follow the mouse
    bufzone.size += mouse.getWheelRel()[1] / 20.0  # vert scroll adjusts radius
    # is the mouse inside the shape (hovering over it)?
    if shape.contains(mouse):
        msg.text = 'inside'
        shape.opacity = bufzone.opacity = 1
    elif shape.overlaps(bufzone):
        msg.text = 'near'
        shape.opacity = bufzone.opacity = 0.6
    else:
        msg.text = 'far away'
        shape.opacity = bufzone.opacity = 0.2
    bufzone.draw()  # drawing helps visualize the mechanics
    msg.draw()
    shape.draw()
    win.flip()

win.close()
core.quit()

# The contents of this file are in the public domain.
