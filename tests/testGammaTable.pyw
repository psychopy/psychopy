"""
Test that the graphics card responds to the 
pygame setgamma command"""

from psychopy import *

myWin = Window((800.0,800.0),fullscr=1)
myWin.setGamma(1.0)

gammaValDisplay = TextStim(myWin,pos=[-0.9,-0.9],rgb=(1.0,1.0,1.0))

trialClock = Clock()
t=0.0

while t<10:
    t = trialClock.getTime()
    
    gammaVal = t/3.0 +1
    gammaValDisplay.set('text',str(gammaVal))
    gammaValDisplay.draw()
    myWin.setGamma(gammaVal)
    myWin.update()
    
myWin.close()