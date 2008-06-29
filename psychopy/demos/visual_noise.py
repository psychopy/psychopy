#! /usr/local/bin/python2.5
#demo arbitrary numpy array

from psychopy import *
from psychopy import ext
import scipy

myWin = visual.Window([600,600], allowGUI=False)

noiseTexture = scipy.random.rand(128,128)*2.0-1
myPatch = visual.PatchStim(myWin, tex=noiseTexture, 
    size=(128,128), units='pix',
    interpolate=False)

for n in range(200): #for 200 frames
    myPatch.setPhase(1/128.0,'+')# increment by one pixel
    #draw for two frames
    myPatch.draw()
    myWin.update()
    myPatch.draw()
    myWin.update()

myWin.close()