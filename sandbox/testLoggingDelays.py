#!/usr/bin/env python
from psychopy import visual, event, core, log
logFile = log.LogFile('test.log', level=log.INFO, filemode='w')
logFile2 = log.LogFile('test2.log', level=log.INFO, filemode='w')
#create a window to draw in
myWin =visual.Window((600,600), allowGUI=False,
    bitsMode=None, units='norm', winType='pyglet')

#INITIALISE SOME STIMULI
dotPatch =visual.DotStim(myWin, rgb=(1.0,1.0,1.0), dir=270,
    nDots=100, fieldShape='circle', fieldPos=(0.0,0.0),fieldSize=1,
    dotLife=5, #number of frames for each dot to be drawn
    signalDots='same', #are the signal and noise dots 'different' or 'same' popns (see Scase et al)
    noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
    speed=0.01, coherence=0.9)
message =visual.TextStim(myWin,text='Hit Q to quit',
    pos=(0,-0.5))
trialClock =core.Clock()
myWin.setRecordFrameIntervals()
n=0
while True:#quits after 20 secs
    n+=1
    dotPatch.draw()
    message.draw()
    myWin.flip()#redraw the buffer
    for n in range(10):
        log.info('%i info' %n)
    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            log.data('final fps = %.3f' % myWin.fps())
            myWin.close()
            core.quit()
    event.clearEvents()#keep the event buffer from overflowing
