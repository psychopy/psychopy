#!/usr/bin/env python2
from psychopy import visual, core, event
import numpy
import time
from pycrsltd import bits
from pyglet import gl

from psychopy import logging
#logging.console.setLevel(logging.DEBUG) #if we need more info messages

bitsBox = bits.BitsSharp()
if not bitsBox.OK:
    print "could not connect to Bits#"
print bitsBox.getInfo() #ensures we have the expected connection to bitsSharp
#bitsBox.startBitsPlusPlusMode() #if we need to see the pixels then show it this way
#time.sleep(2)

def drawPixels(intensities):
    #create row of rgb vals from intensities
    pixels = numpy.ones([len(intensities),1,3]).astype(numpy.ubyte)
    pixels[:,0,0] = intensities
    pixels[:,0,1] = intensities
    pixels[:,0,2] = intensities
    #scale window
    gl.glOrtho( 0, win.size[0], 0, win.size[1], 0, 1 )
    #move to top left
    gl.glRasterPos2f(0, win.size[1]-1 )
    gl.glDrawPixels(pixels.shape[0], pixels.shape[1],
        gl.GL_RGB, gl.GL_UNSIGNED_BYTE,
        pixels.tostring())

intensities = [1,2,3,4]

#create a window with bitsMode='fast' (why would you ever use 'slow'!?)
win = visual.Window([800,800], screen=1, fullscr=True, gamma=1.0)
drawPixels(intensities)
win.flip()

bitsBox.showStatusScreen()
time.sleep(2)
print bitsBox.getVideoLine(lineN=1, nPixels=10)[:,0]
bitsBox.startBitsPlusPlusMode()
time.sleep(0.1)
