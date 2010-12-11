import psychopy
from math import sin, pi


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
myWin = psychopy.visual.Window((600,600.0),fullscr=0, winType="pygame",
							   bitsMode='slow')

#INITIALISE SOME STIMULI
grating1 = psychopy.visual.PatchStim(myWin,tex="sin",mask="circle",texRes=128,
			rgb=[1.0,1.0,1.0],opacity=1.0,
			size=(1.0,1.0), sf=(4.0,2.0),
			ori = 45, contrast=0.99)

fpsDisplay = psychopy.visual.TextStim(myWin,pos=(-0.95,-0.95),text='fps...')

trialClock = psychopy.Clock()
timer = psychopy.Clock()
t = lastFPSupdate = 0
while t<1:#quits after 20 secs
	t=trialClock.getTime()
	grating1.draw()  #redraw it
	if t-lastFPSupdate>0.5:#update the fps each 1 second
		fpsDisplay.set('text',str(t)[0:4]+' fps')
		lastFPSupdate+=0.5
	fpsDisplay.draw()
	myWin.update()          #update the screen
	
timer.reset()
myWin.bits.setContrast(0.2)
print timer.getTime()

timer.reset()
myWin.bits.setContrast(-0.2)
print timer.getTime()
timer.reset()
myWin.bits.setContrast(0.2)
print timer.getTime()
timer.reset()
myWin.bits.setContrast(-0.2)
print timer.getTime()

psychopy.quit()
