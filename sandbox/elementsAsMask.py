#!/usr/bin/env python
from psychopy import core, visual, event
import numpy

#create a window to draw in
myWin = visual.Window((600,600), allowGUI=False, color=0, 
        monitor='testMonitor',winType='pyglet', units='norm')

#INITIALISE SOME STIMULI
faceRGB = visual.PatchStim(myWin,tex='sin',
    mask='gauss',
    pos=(0.0,0.0),
    size=(1.0,1.0),
    sf=5)

#create a grid of xy vals
x=y=numpy.linspace(-0.5,0.5,11)#11 entries from -0.5 to 0.5 
xs,ys = numpy.meshgrid(x,y)
#get that grid to be 121x2 in shape (expected by element array)
xys = numpy.zeros([len(xs.flat), 2])
xys[:,0]=xs.flat
xys[:,1]=ys.flat
#create opacity for each square in mask
opacs = numpy.ones(len(xys))#all opaque to start
print opacs.shape
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
    faceRGB.setOri(1,'+')#advance ori by 1 degree
    faceRGB.draw()

    #update mask b ymaking one element transparent
    if frameN<len(maskIndices):
        ii = maskIndices[frameN]#select the next index to make transparent
        opacs[ii]=0
        mask.setOpacities(opacs)
    mask.draw()
    
    myWin.flip()
    frameN+=1
    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            print myWin.fps()
            myWin.close()
            core.quit()
