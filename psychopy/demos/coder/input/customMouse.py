#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of CustomMouse(), showing movement limits, click detected upon release,
and ability to change the pointer.

The contents of this file are in the public domain.
"""

from psychopy import core, visual, event
from psychopy.demos.coder import assetsFolder

# create window
win = visual.Window(
    units="height"
)
# hide the default mouse
win.mouseVisible = False
# setup an experiment clock
clock = core.Clock()
# create a mouse object
mouse = event.Mouse()
# put some instructions on screen
instr = visual.TextBox2(
    win,
    text=(
        "I, the wizard of PsychoPy, have transformed your mouse into a horse!\n"
        "\n"
        "Click to exit."
    ),
    alignment="center",
    autoDraw=True
)
# this is the object to use for your pointer, it can be anything with a pos/size 
# (so basically any visual stimulus)
pointer = visual.TextBox2(
    win,
    # let's use unicode and a custom font to draw a little horsey for our mouse marker...
    text="♞",
    font="Noto Sans Symbols 2",
    letterHeight=0.1,
    # use a center anchor and center alignment, so that the text is on the same point as .pos
    alignment="center",
    anchor="center",
    # the mouse will use the same units as the window, so make sure the pointer uses these units too
    units="height",
    autoDraw=True
)
pointer.fontMGR.addFontFile(
    assetsFolder / "NotoSansSymbols2.ttf"
)

# start the frame loop (run until user clicks)
while not any(mouse.getPressed()):
    # set the pointer object to have the same position as the mouse
    pointer.pos = mouse.getPos()
    # draw and flip
    win.flip()
