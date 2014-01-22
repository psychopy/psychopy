#!/usr/bin/env python2
#demo arbitrary numpy array

from psychopy import visual, core, event, logging
import scipy

logging.console.setLevel(logging.DEBUG)

myWin = visual.Window([600,600], allowGUI=False)

noiseTexture = scipy.random.rand(128,128)*2.0-1
myPatch = visual.GratingStim(myWin, tex=noiseTexture, 
    size=(128,128), units='pix',
    interpolate=False,
    autoLog=False)#this stim changes too much for autologging to be useful

for n in range(200): #for 200 frames
    myPatch.setPhase(1/128.0,'+')# increment by one pixel
    #draw for two framess
    myPatch.draw()
    myWin.flip()
    myPatch.draw()
    myWin.flip()
    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            core.quit()

myWin.close()
