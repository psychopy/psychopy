#!/usr/bin/env python
from psychopy import visual, core, event

#create a window to draw in
myWin = visual.Window((600,600), allowGUI=False,
                      monitor='testMonitor', units='deg')

#INITIALISE SOME STIMULI
myDotShape = visual.PatchStim(myWin, mask='gauss',sf=3)
dotPatch = visual.DotStim(myWin, color=[1,1,1],
                        dotLife=5, #lifetime of a dot in frames (if this is long density artefacts can occur in the stimulus)
                        signalDots='different', #are the signal and noise dots 'different' or 'same' popns (see Scase et al)
                        noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
                        fieldPos=[0.0,0.0], nDots=40, fieldSize=3,
                        speed=0.05, fieldShape='circle', coherence=0.5,
                        element = myDotShape)
message = visual.TextStim(myWin,text='Hit Q to quit',
                                   pos=(0,-5))
                                   
trialClock = core.Clock()
t = lastFPSupdate = 0
while t<60:#quits after 20 secs
    t=trialClock.getTime()
    dotPatch.draw()	
    message.draw()
    myWin.flip()#redraw the buffer
    
    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            print myWin.fps()
            myWin.close()
            core.quit()
            