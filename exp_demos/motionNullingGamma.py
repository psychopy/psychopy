"""motion-nulling gamma correction"""

from psychopy import *
from psychopy import filters
import scipy

info={}
info['lumModNoise']=0.5
info['lumModLum']=0.1
info['contrastModNoise']=1.0
info['observer']='jwp'
nFrames=4
cyclesTime=2
cyclesSpace=3
gamVal=3
pixels=256

myWin = visual.Window((800,600), units='pix', allowGUI=False, bitsMode='fast')
visual.TextStim(myWin, text='building stimuli').draw()

myWin.update()

globalClock = core.Clock()

#for luminance modulated noise
noiseMatrix = scipy.random.randint(0,2,[pixels,pixels])#*noiseContrast
noiseMatrix = noiseMatrix*2.0-1 #into range -1:1
	
stimFrames=[]; lumGratings=[]
#grating and stimulus
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=0))
stimFrames.append(visual.AlphaStim(myWin, texRes=pixels, mask='circle',
								  size=pixels*2, sf=1.0/pixels, ori=90,
								  tex= (noiseMatrix*info['lumModNoise'] + lumGratings[0]*info['lumModLum'])
								  ))
#grating and stimulus
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=90)/2.0 + 0.5)

stimFrames.append(visual.AlphaStim(myWin, texRes=pixels, mask='circle',
								  size=pixels*2, sf=1.0/pixels, ori=90,
								  tex= (noiseMatrix*info['contrastModNoise']*lumGratings[1])
								  ))
#grating and stimulus
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=180))
stimFrames.append(visual.AlphaStim(myWin, texRes=pixels, mask='circle',
								  size=pixels*2, sf=1.0/pixels, ori=90,
								  tex= (noiseMatrix*info['lumModNoise'] + lumGratings[2]*info['lumModLum'])
								  ))
#grating and stimulus
lumGratings.append(filters.makeGrating(pixels, 0, cyclesSpace, phase=270)/2.0 + 0.5)
stimFrames.append(visual.AlphaStim(myWin, texRes=pixels, mask='circle',
								  size=pixels*2, sf=1.0/pixels, ori=90,
								  tex= (noiseMatrix*info['contrastModNoise']*lumGratings[3])
								  ))
				 

stairCase = data.StairHandler(startVal=gamVal, nTrials=50, 
								stepSizes=[0.5,0.5,0.1,0.1,0.1,0.1,0.05,0.05,0.01],stepType='lin',
								nUp=1, nDown=1)

def getResponse(direction):
	"""if subject said up when direction was up (+1) then increase gamma
	Otherwise, decrease gamma"""
	event.clearEvents()#clear the event buffer to start with
	resp=None#initially
	
	while 1:#forever until we return
		for key in event.getKeys():		
				#quit 
				if key in ['escape', 'q']:
						myWin.close()
						#myWin.bits.reset()
						core.quit()
						return None
				#valid response - check to see if correct
				elif key in ['down','up']:
						if (key in ['down'] and direction==-1) or \
							(key in ['up'] and direction==+1) :
								return 0
						else: 
								return 1
				else: 
						print "hit DOWN or UP (or Esc) (You hit %s)" %key

def presentStimulus(direction):
	"""Present stimulus drifting in a given direction (for low gamma)
	where:
		direction=+1(up) or -1(down)
	"""
	junk= myWin.fps()
	
	startPhase = scipy.rand()		
	if direction==1:
		frameIndices = num.arange(0,4)
	else: frameIndices = num.arange(3,-1,-1)
	
	for cycles in range(cyclesTime):
		#cycle through the 4 frames
		for ii in frameIndices:
			thisStim = stimFrames[ii]
			thisStim.setPhase(startPhase)
			for n in range(nFrames):
				#present for several constant frames (TF)
				thisStim.draw()
				myWin.update()
				
	#then blank the screen
	myWin.update()

#run the staircase
while stairCase.notFinished:
	thisGamma=stairCase.nextTrial()
	t = globalClock.getTime()
	myWin.setGamma([thisGamma,thisGamma,thisGamma])
	
	direction=scipy.random.randint(0,2)*2-1 # a random number -1 or 1 
	presentStimulus(direction)
	print direction, thisGamma
	
	ans=getResponse(direction)
	stairCase.addData(ans)
	
myWin.update()
core.wait(0.5)

myWin.close()

#save data
fileName=gui.fileSaveDlg()
stairCase.saveAsPickle(fileName)
stairCase.saveAsText(fileName)
	