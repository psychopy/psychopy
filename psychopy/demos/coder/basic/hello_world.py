#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo: show a very basic program: hello world
"""

# Import key parts of the PsychoPy library:
from psychopy import visual, core

# Create a visual window:
win = visual.Window(units="height")

# Create (but not yet display) some text:
msg1 = visual.TextBox2(win, 
    text=u"Hello world!", 
    font="Open Sans", letterHeight=0.1,
    pos=(0, 0.2)) 
msg2 = visual.TextBox2(win, 
    text=u"\u00A1Hola mundo!", 
    font="Open Sans", letterHeight=0.1, 
    pos=(0, -0.2))

# Draw the text to the hidden visual buffer:
msg1.draw()
msg2.draw()

# Show the hidden buffer--everything that has been drawn since the last win.flip():
win.flip()

# Wait 3 seconds so people can see the message, then exit gracefully:
core.wait(3)

win.close()
core.quit()

# The contents of this file are in the public domain.
