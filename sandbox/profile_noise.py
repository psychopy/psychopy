#profile noise
import profile
from psychopy import *
from psychopy import ext
import numpy

def main():
    #demo arbitrary numpy array
    
    ext.rush(3)
    myWin = visual.Window([600,600], allowGUI=False)
    
    noiseTexture = numpy.random.rand(128,128)*2.0-1
    myPatch = visual.PatchStim(myWin, tex=noiseTexture, ori=45, size=(1,1), interpolate=False)
    
    for frameN in xrange(2400):
        myPatch.setPhase(0.005,'+')
        myPatch.draw()
        myWin.update()
        
profile.run('main()', 'profNoise.prof')