from psychopy import *
from psychopy.visual import *

myWin = visual.Window([800,800])
radStim = RadialStim(myWin, tex='sinXsin', angularCycles=6, radialCycles=3)
for frameN in range(100):
    radStim.setRadialPhase(0.1, '+')
    radStim.setAngularPhase(0.1, '+')
    radStim.draw()
    myWin.update()

#event.waitKeys()