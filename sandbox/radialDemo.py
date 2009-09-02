from psychopy import *
from psychopy.visual import *
from numpy import pi


myWin = visual.Window([800,800])
radStim = RadialStim(myWin, size=1,pos=[-0.5, 0], 
    tex='sinXsin', rgb=-1, mask='circle', opacity=0.5,
    angularCycles=0, radialCycles=3, visibleWedge=[1, 271.0])
radStim3 = RadialStim(myWin, size=1,pos=[-0.5, 0], 
    tex='sinXsin', rgb=-1, mask='circle', opacity=0.5,
    angularCycles=0, radialCycles=3, visibleWedge=[271, 361.0])
radStim2 = RadialStim(myWin, size=0.5,pos=[0.5, 0], mask='gauss',tex='sinXsin', angularCycles=0, radialCycles=3)
myWin.fps()
for frameN in range(1000):
    radStim.setRadialPhase(0.02, '+')
    radStim2.setRadialPhase(0.02, '-')
    #radStim.setAngularPhase(0.1, '+')
    radStim.draw()
    radStim2.draw()
    radStim3.draw()
    myWin.update()
print myWin.fps()
#event.waitKeys()