#!/usr/bin/env python2
from psychopy import visual, event, core

#create a window to draw in
myWin =visual.Window((600,600), allowGUI=False,
    bitsMode=None, units='norm', winType='pyglet')

#INITIALISE SOME STIMULI
dotPatch =visual.DotStim(myWin, color=(1.0,1.0,1.0), dir=270,
    nDots=500, fieldShape='circle', fieldPos=(0.0,0.0),fieldSize=1,
    dotLife=5, #number of frames for each dot to be drawn
    signalDots='same', #are the signal dots the 'same' on each frame? (see Scase et al)
    noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
    speed=0.01, coherence=0.9)
message =visual.TextStim(myWin,text='Hit Q to quit',
    pos=(0,-0.5))
trialClock =core.Clock()
while True:#forever
    dotPatch.draw()
    message.draw()
    myWin.flip()#redraw the buffer

    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            print myWin.fps()
            myWin.close()
            core.quit()
    event.clearEvents('mouse')#only really needed for pygame windows

