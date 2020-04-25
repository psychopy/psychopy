#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo: show a very basic program: hello world
"""

from __future__ import absolute_import, division, print_function

# Import key parts of the PsychoPy library:
from psychopy import visual, core
import psychopy.tools.gltools as gltools
import pyglet.gl as GL

# Create a visual window:
win = visual.Window(useFBO=False, units='norm')
msg1 = visual.TextStim(win, text=u"Hello world!", pos=(0, 0))  # default position = centered
msg2 = visual.TextStim(win, text=u"Hello world2!")


win.createBuffer('newBuffer', (800, 600))
#print(win._frameBuffers)
win.setBuffer('newBuffer')
# GL.gluPerspective(90, 1.0 * width / height, 0.1, 100.0)
#win.resetEyeTransform(False)
win.color = (1, 0, 0)
win.clearBuffer()
# Draw the text to the hidden visual buffer:
msg1.draw()
#win.copyBuffer('back') #, (0, 0, 800, 600), (0, 0, 400, 600))
win.blitBuffer('back')
win.setBuffer('back', clear=False)

msg2.draw()


#win.color = (0, 0, 0)

# Create (but not yet display) some text:

#win.setBuffer('back', clear=False)
#print(win.viewPos)
#win.copyBuffer('back', (0, 0, 800, 600), (0, 0, 800, 600))
#win.setBuffer('back')
#win.color = (1, 0, 0)
#win.clearBuffer()
#
# Show the hidden buffer--everything that has been drawn since the last win.flip():
win.flip()

# Wait 3 seconds so people can see the message, then exit gracefully:
core.wait(3)

win.close()
core.quit()

# The contents of this file are in the public domain.
