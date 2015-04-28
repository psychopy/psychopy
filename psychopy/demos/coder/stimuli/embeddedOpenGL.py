#!/usr/bin/env python2
"""
This demo shows how you can make standard opengl calls within a
psychopy script, allowing you to draw anything that OpenGL can draw
(ie anything)
"""
from psychopy import visual, core, event
from pyglet import gl

myWin = visual.Window([600,600], units='norm',monitor='testMonitor')
a_blob = visual.GratingStim(myWin, pos = [0.5,0],mask='gauss', sf=3)

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

    myWin.flip()

drawStuff()
core.wait(2)
core.quit()
