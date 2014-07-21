#!/usr/bin/env python2

"""This demo requires a graphics card that supports OpenGL2 extensions. 

It shows how to manipulate an arbitrary set of elements using numpy arrays
and avoiding for loops in your code for optimised performance.

see also the elementArrayStim demo

"""

from psychopy import visual, event
from psychopy.tools.coordinatetools import pol2cart
import numpy

nDots = 500
maxSpeed = 0.02
dotSize = .0075

dotsTheta=numpy.random.rand(nDots)*360
dotsRadius=(numpy.random.rand(nDots)**0.5)*2
speed=numpy.random.rand(nDots)*maxSpeed

win = visual.Window([800,600],rgb=[-1,-1,-1])
dots = visual.ElementArrayStim(win, elementTex=None, elementMask='circle', 
    nElements=nDots, sizes=dotSize)

while True:
    #update radius
    dotsRadius = (dotsRadius+speed)
    #random radius where radius too large
    outFieldDots = (dotsRadius>=2.0)
    dotsRadius[outFieldDots] = numpy.random.rand(sum(outFieldDots))*2.0
    
    dotsX, dotsY = pol2cart(dotsTheta,dotsRadius)
    dotsX *= 0.75 #to account for wider aspect ratio
    dots.xys = numpy.array([dotsX, dotsY]).transpose()
    dots.draw()
    
    win.flip()
    
    # Exit on escape
    if event.getKeys(keyList=['escape', 'q']):
        break
