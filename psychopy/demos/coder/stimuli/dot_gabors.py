#!/usr/bin/env python2
from psychopy import visual, core, event

#create a window to draw in
myWin = visual.Window((600,600), allowGUI=False,
                      monitor='testMonitor', units='deg')

#INITIALISE SOME STIMULI
myDotShape = visual.GratingStim(myWin, mask='gauss',sf=3)
dotPatch = visual.DotStim(myWin, color=[1,1,1],
                        dotLife=5, #lifetime of a dot in frames (if this is long density artefacts can occur in the stimulus)
                        signalDots='different', #are the signal and noise dots 'different' or 'same' popns (see Scase et al)
                        noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
                        fieldPos=[0.0,0.0], nDots=40, fieldSize=3,
                        speed=0.05, fieldShape='circle', coherence=0.5,
                        element = myDotShape, name='dotPatch')
message = visual.TextStim(myWin,text='Hit Q to quit',
                                   pos=(0,-5), name='Instructions')
                                 
trialClock = core.Clock()
t = lastFPSupdate = 0
dotPatch.setAutoDraw(True)#always draw
message.setAutoDraw(True)#always draw

while t<60:#quits after 20 secs
    t=trialClock.getTime()
    myWin.flip()#redraw the buffer
    
    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            myWin.close()
            core.quit()
