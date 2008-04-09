from psychopy import *

#create a window to draw in
myWin = visual.Window((800.0,800.0),fullscr=0)

#INITIALISE SOME STIMULI
fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",pos=(0,0), size=(0.05,0.05),rgb=[-1.0,-1.0,-1.0])
gabor = visual.PatchStim(myWin,pos=(0.5,0),
					tex="sin",mask="gauss",
					rgb=[0.5,0.5,0.5],
					size=(1.0,1.0), sf=(2,0), rgbPedestal=0.5)

message = visual.TextStim(myWin,pos=(-0.95,-0.95),text='Hit Q to quit')
trialClock = core.Clock()
t = 0
while t<20:#quits after 20 secs
    t=trialClock.getTime()
    
    fixSpot.draw()
    
    gabor.set('phase',t)
    gabor.draw()    
    
    message.draw()
    myWin.update()#redraw the buffer
    
    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            core.quit()
    event.clearEvents()
    
    
