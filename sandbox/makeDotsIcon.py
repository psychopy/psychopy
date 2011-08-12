#!/usr/bin/env python
from psychopy import visual, event, core

#create a window to draw in
myWin =visual.Window((48,48), allowGUI=False,
    bitsMode=None, units='norm', winType='pyglet')

#INITIALISE SOME STIMULI
dotPatch =visual.DotStim(myWin, color=(1.0,1.0,1.0), dir=45,
    nDots=10, fieldShape='circle', fieldPos=(0.0,0.0),fieldSize=1.5,
    dotLife=500, #number of frames for each dot to be drawn
    signalDots='different', #are the signal and noise dots 'different' or 'same' popns (see Scase et al)
    noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
    speed=0.1, coherence=0.4)
scrPatch = visual.PatchStim(myWin, color=0, tex=None, size=2, opacity=0.3 )
trialClock =core.Clock()
cont = True
while cont:
    myWin.flip(clearBuffer=True)#redraw the buffer
    for frameN in range(3):#quits after 20 secs
        scrPatch.draw()
        dotPatch.draw()
        myWin.flip(clearBuffer=False)#redraw the buffer

    dotPatch.draw()
    myWin.flip(clearBuffer=False)#redraw the buffer
    keys = event.waitKeys()
    if 'q' in keys: cont=False
    if 's' in keys: myWin.getMovieFrame()
    
myWin.saveMovieFrames('last.png')
