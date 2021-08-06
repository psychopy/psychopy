#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This demo shows how you can make standard opengl calls within a psychopy
script, allowing you to draw anything that OpenGL can draw (i.e. anything).
"""

from psychopy import visual, core
from pyglet import gl

win = visual.Window([600, 600], units='norm', monitor='testMonitor')
a_blob = visual.GratingStim(win, pos = [0.5, 0], mask='gauss', sf=3)

def drawStuff(): 
    gl.glBegin(gl.GL_TRIANGLES)
    gl.glColor3f(1.0, 0.0, 1)
    gl.glVertex3f(0.0, 0.5, 1)
    gl.glColor3f(0.0, 1.0, 0.0)
    gl.glVertex3f(-0.5, -0.5, 1)
    gl.glColor3f(0.0, 0.0, 1.0)
    gl.glVertex3f(0.5, -0.5, -1)
    gl.glEnd()

    a_blob.draw()

    win.flip()

drawStuff()
core.wait(2)

win.close()
core.quit()

# The contents of this file are in the public domain.
