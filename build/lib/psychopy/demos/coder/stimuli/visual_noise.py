#!/usr/bin/env python2
#demo arbitrary numpy array

from psychopy import visual, event, logging
import scipy

logging.console.setLevel(logging.DEBUG)

myWin = visual.Window([600,600], allowGUI=False)

noiseTexture = scipy.random.rand(128,128)*2.0-1
myPatch = visual.GratingStim(myWin, tex=noiseTexture, 
    size=(128,128), units='pix',
    interpolate=False,
    autoLog=False)#this stim changes too much for autologging to be useful

while not event.getKeys(keyList=['escape', 'q']):
    myPatch.phase += (1 / 128.0, 0.5 / 128.0)  # increment by (1, 0.5) pixels per frame
    
    myPatch.draw()
    myWin.flip()

myWin.close()
