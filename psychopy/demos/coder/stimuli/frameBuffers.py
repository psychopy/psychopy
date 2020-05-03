#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo: show a very basic program: hello world
"""

from __future__ import absolute_import, division, print_function

# Import key parts of the PsychoPy library:
from psychopy import visual, core

# Create a visual window:
win = visual.Window(useFBO=False, units='norm')
msg1 = visual.TextStim(win, text=u"Hello world!", pos=(0, 0))  # default position = centered
msg2 = visual.TextStim(win, text=u"Hello world2!")
win.createBuffer('test')
win.createBufferFromRect('left', 'back', (0, 0, 400, 600))
win.createBufferFromRect('right', 'back', (400, 0, 400, 600))
win.color = (1, 0, 0)
win.setBuffer('left')
msg1.draw()
win.color = (0, 0, 1)
win.setBuffer('right')
msg2.draw()
win.color = (0, 0, 0)

# Show the hidden buffer--everything that has been drawn since the last win.flip():

win.flip()
print(win.buffer)
win.deleteBuffer('right')

# Wait 3 seconds so people can see the message, then exit gracefully:
core.wait(3)

win.close()
core.quit()

# The contents of this file are in the public domain.
