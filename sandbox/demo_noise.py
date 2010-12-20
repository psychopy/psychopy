#demo arbitrary numpy array

from psychopy import *
from psychopy import ext
import numpy

myWin = visual.Window([600,600], allowGUI=False)

noiseTexture = numpy.random.rand(128,128)*2.0-1
myPatch = visual.PatchStim(myWin, tex=noiseTexture, ori=45, size=(1,1), interpolate=False)

for frameN in xrange(240):
    myPatch.setPhase(0.005,'+')
    myPatch.draw()
    myWin.update()
