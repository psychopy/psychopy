import psychopy
from math import sin, pi

#create a window to draw in
myWin = psychopy.visual.Window((800,600),fullscr=0, winType="pygame",
                                        bitsMode='fast', rgb=-0, gamma=1.0)

grating1 = psychopy.visual.PatchStim(myWin,tex="sin",mask="circle",texRes=128,
			rgb=[1.0,1.0,1.0],opacity=1.0,
			size=(1.0,1.0), sf=(4.0,2.0),
			ori = 45, contrast=0.99)

fpsDisplay = psychopy.visual.TextStim(myWin,pos=(-0.95,-0.95),text='fps...')

trialClock = psychopy.Clock()
timer = psychopy.Clock()
t = lastFPSupdate = 0
while t<20:#quits after 20 secs
	t=trialClock.getTime()
	#grating1.draw()  #redraw it
	myWin.update()   #update the screen
	
	for keys in psychopy.event.getKeys():
		if keys in ['escape','q']:
			psychopy.core.quit()
	
psychopy.core.quit()
