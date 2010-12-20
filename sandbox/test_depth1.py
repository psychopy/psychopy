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
myWin = psychopy.visual.Window((800,800.0), allowGUI=False, monitor='testMonitor', units='norm')

#INITIALISE SOME STIMULI
grating = psychopy.visual.PatchStim(myWin,tex=None, mask="circle",texRes=128,
						pos=(-1.0,-1.0),
						size=0.25,depth=-0.5)
message = psychopy.visual.TextStim(myWin,pos=(-0.95,-0.95),text='Hit Q to quit')

mouse = event.Mouse()

trialClock = psychopy.Clock()
t = lastFPSupdate = 0
while 1:#quits after 20 secs
	mouse_dX,mouse_dY = mouse.getPos()
	
	newDepth = mouse_dY/20.0-20
	grating.setDepth(newDepth)
	grating.draw()  #redraw it
	
	message.setText("depth=%.2f" %newDepth)
	message.draw()
	
	myWin.update()          #update the screen

	#handle key presses each frame
	for keys in event.getKeys():
			if keys in ['escape','q']:
					print grating.pos, grating.size[0], grating.depth
					psychopy.quit()
	event.clearEvents()
psychopy.quit()
