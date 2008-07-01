#! /usr/local/bin/python2.5
from psychopy import visual, event, core

#create a window to draw in
myWin =visual.Window((600,600), allowGUI=False,
    bitsMode=None, units='norm', winType='pyglet')

#INITIALISE SOME STIMULI
dotPatch =visual.DotStim(myWin, rgb=(1.0,1.0,1.0),
    fieldPos=(0.0,0.0), nDots=500, fieldSize=(0.5,0.5),
    speed=0.01, coherence=0.2)
message =visual.TextStim(myWin,text='Hit Q to quit',
    pos=(0,-0.5))

trialClock =core.Clock()
while True:#quits after 20 secs
    dotPatch.draw()
    message.draw()
    myWin.flip()#redraw the buffer

    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            print myWin.fps()
            myWin.close()
            core.quit()
    event.clearEvents()#keep the event buffer from overflowing

