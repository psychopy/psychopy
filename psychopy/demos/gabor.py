#!/usr/bin/env python
from psychopy import core, visual, event

#create a window to draw in
myWin = visual.Window([400,400.0], allowGUI=False)

#INITIALISE SOME STIMULI
gabor = visual.PatchStim(myWin,tex="sin",mask="gauss",texRes=256,
           size=[1.0,1.0], sf=[4,0],
           ori = 0)
message = visual.TextStim(myWin,pos=(0.0,-0.9),text='Hit Q to quit')
trialClock = core.Clock()

#repeat drawing for each frame
while trialClock.getTime()<20:
   gabor.setPhase(0.01,'+')
   gabor.draw()	
   message.draw()
   #handle key presses each frame
   for keys in event.getKeys(timeStamped=True):
      if keys[0][0] in ['escape','q']:
            print myWin.fps(), keys
            myWin.close()
            core.quit()
         
   myWin.flip()
