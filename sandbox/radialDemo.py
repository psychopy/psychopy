from psychopy import *
from psychopy.visual import *
from numpy import pi

myWin = visual.Window([800,800])
radStim = RadialStim(myWin, size=1,pos=[-0.5, 0], 
    tex='sqrXsqr', rgb=-1, mask='circle', opacity=0.5,radialPhase=0.25,
    angularCycles=0, radialCycles=1, visibleWedge=[0, 270.0])
myWin.fps()

radStim.draw()
myWin.update()
event.waitKeys()