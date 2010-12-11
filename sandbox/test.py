from psychopy import *

#create a window to draw in
myWin = visual.Window([400,400.0], allowGUI=False, winType="pygame")

#INITIALISE SOME STIMULI
#gabor = visual.PatchStim(myWin,tex="sin",mask="gauss",texRes=256,
           #rgb=[1.0,1.0,1.0],opacity=1.0,
           #size=[1.0,1.0], sf=[4,0],
           #ori = 45)
#message = visual.TextStim(myWin,pos=(0,-2),text='Hit Q to quit')
trialClock = core.Clock()

#repeat drawing for each frame
while trialClock.getTime()<20:
   #gabor.setPhase(0.01,'+')
   #gabor.draw()	
   #message.draw()
   #handle key presses each frame
   for keys in event.getKeys():
      if keys in ['escape','q']:
            print myWin.fps()
            myWin.close()
            core.quit()
         
   myWin.update()
