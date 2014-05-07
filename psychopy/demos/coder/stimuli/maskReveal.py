#!/usr/bin/env python2
"""When you want to reveal an image gradually from behind a mask, 
the tempting thing to do is to alter a stimulus mask using .setMask()

That will actually be very slow because of the overhead in sending 
textures to the graphics card on each change. Instead, the more
efficient way of doing this is to create an element array and alter the
opacity of each element of the array to reveal what's behind it.

"""
from psychopy import core, visual, event
from psychopy.tools.arraytools import createXYs
import numpy

#create a window to draw in
myWin = visual.Window((600,600), allowGUI=False, color=0, 
        monitor='testMonitor',winType='pyglet', units='norm')

#INITIALISE SOME STIMULI
gabor = visual.GratingStim(myWin,tex='sin',
    mask='gauss',
    pos=(0.0,0.0),
    size=(1.0,1.0),
    sf=5)

#create a grid of xy vals
xys = createXYs( numpy.linspace(-0.5,0.5,11) )#11 entries from -0.5 to 0.5
#create opacity for each square in mask
opacs = numpy.ones(len(xys))#all opaque to start
#create mask
elSize = xys[1,0]-xys[0,0]
mask = visual.ElementArrayStim(myWin, elementTex=None, elementMask=None,
    nElements=len(xys),
    rgbs=0, #set to same as background
    xys=xys, opacities=opacs,
    sizes=elSize)

trialClock = core.Clock()
t=lastFPSupdate=0
maskIndices=numpy.arange(len(xys))
numpy.random.shuffle(maskIndices)
frameN=0
while True:
    t=trialClock.getTime()
    gabor.ori += 1  #advance ori by 1 degree
    gabor.draw()

    #update mask b ymaking one element transparent
    if frameN<len(maskIndices):
        ii = maskIndices[frameN]#select the next index to make transparent
        opacs[ii]=0
        mask.opacities = opacs
    mask.draw()
    
    myWin.flip()
    frameN+=1
    #handle key presses each frame
    if event.getKeys(keyList=['escape','q']):
        myWin.close()
        core.quit()
