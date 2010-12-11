import psychopy
from math import sin, pi
from psychopy import event

"""
There are many ways to generate counter-phase e.g. 
vary the contrast of a grating sinusoidally between 1 and -1, 
take 2 gratings in opposite phase overlaid and vary the 
opacity of the upper one between 1:0, or take 2 gratings
overlaid with the upper one of 0.5 opacity and drift them
in opposite directions.
This script takes the first approach as a test of how fast 
contrast textures are being rewritten to the graphics card
"""

#create a window to draw in
myWin = psychopy.visual.Window((1280,1024), allowGUI=True, units='norm')

#INITIALISE SOME STIMULI
grating = psychopy.visual.PatchStim(myWin,tex=None,mask="circle",texRes=128,
						rgb=[1.0,1.0,1.0],opacity=1.0,
						size=0.1,pos=[-0.6,-0.6],
						ori = 45, depth=0.5)
mouse = event.Mouse()

trialClock = psychopy.Clock()
t = lastFPSupdate = 0

mouse_dX,mouse_dY = mouse.getRel()
b1, b2, b3 = mouse.getPressed()

grating.draw()  #redraw it

myWin.update()          #update the screen

event.waitKeys()
#handle key presses each frame
#for keys in event.getKeys():
		#if keys in ['escape','q']:
			#print grating.pos, grating.size[0]
			#psychopy.quit()
#event.clearEvents()
psychopy.quit()
