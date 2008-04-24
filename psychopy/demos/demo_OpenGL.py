#! /usr/local/bin/python2.5
from psychopy import *
from OpenGL.GL import *

myWin = visual.Window([600,600], units='norm',monitor='testMonitor')
a_blob = visual.PatchStim(myWin, pos = [0.5,0],mask='gauss', sf=3)
xx = visual.PatchStim(myWin, texRes=4)

def drawStuff():    
    
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 0.0, 1)
    glVertex3f(0.0, 0.5, 1)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(-0.5, -0.5, 1)
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.5, -0.5, -1)
    glEnd()
    
    a_blob.draw()
    
    myWin.update()
 
drawStuff()
core.wait(2)
core.quit()