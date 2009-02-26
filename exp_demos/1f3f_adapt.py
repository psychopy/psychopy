"""
Adapt a subject to 1f+3f compound stimuli and compare detection thresholds 
for 1f+3f at a variety of different phases

Method of constant stimuli for contrast detection
"""

from psycho import *
from pygame.locals import *
#import gui_thread
from numpy import *
import winsound

#create a window to draw in
MyWin = Window((800.0,800.0),fullscr=0,winType="pygame",scrWidthCM=25,scrDistCM=54)

#initialise stimuli
BaseFrequency=0.2
StimSize = 15.0
FixSpot = PatchStim(MyWin,tex="none", mask="circle",size=(0.05,0.05),rgb=[-1.0,-1.0,-1.0],sf=0)
f1 = PatchStim(MyWin,units="deg",
			tex="sin",mask="gauss",
			size=StimSize, sf=BaseFrequency)
f3 = PatchStim(MyWin,units="deg",
			tex="sin",mask="gauss",
			size=StimSize, sf=BaseFrequency*3.0,
			opacity=0.5)
Instructions = TextStim(MyWin,pos=(-0.9,0.9),
			text='Press left cursor if stimuli were oriented the same, right cursor if not')

#initialise other variables
BaseOri = 45
BackGroundOri = -45
TestPhaseDiffs = [0.0, 0.5] #corresponds to f1+f3 and f1-f3
TestConts = arange(0.00,0.07,0.01)
AdaptPhaseDiff = array([0.0])
NReps = 2
ThisCont=0.1
TrialClock = Clock();
ExpClock = Clock();#will use a single constant clock to link the phase to
quitNow=0

"""initialise trial info"""
Trials = { #a 'dictionary' of lists (see python tutorial)
		'TestPhaseDiff':[],#ones(NReps*len(OriDiffs)*2),
		'TestCont':[],
		'Resp':[]#ones(NReps*len(OriDiffs)*2)
		}
for n in range(NReps):
	for ThisTest in TestPhaseDiffs:
		for ThisCont in TestConts:
			Trials['TestPhaseDiff'].append(ThisTest)
			Trials['TestCont'].append(ThisTest)
			Trials['Resp'].append(-1)
#Trials['ori']=array(Trials['ori'])
#Trials['backg_on']=array(Trials['backg_on'])
#Trials['resp']=array(Trials['resp'])

#we only want to know about when keys get pressed - kill mice, joysticks etc...
pygame.event.set_allowed(None)
pygame.event.set_allowed(KEYDOWN)

"""Run the initial adaptation"""
t=0
while t<2:
	t=ExpClock.getTime()
	f1.set('phase',t)
	f3.set('phase',t*3+AdaptPhaseDiff)
	f1.draw(); f3.draw();
	MyWin.update()

"""Run the trials"""
for TrialN in misc.shuffleArray(arange(len(Trials['Resp']))):#a shuffled vector of integers for trialN
	if quitNow: break
	TrialClock.reset();
	
	#re-adapt
	f1.set('contrast',1.0); f3.set('contrast',1.0)#set contrast back to 1
	winsound.Beep(400,20)
	while TrialClock.getTime()<1.0:
		GlobalT = ExpClock.getTime()
		f1.set('phase',GlobalT);
		f3.set('phase',GlobalT*3+AdaptPhaseDiff); 
		f1.draw(); f3.draw()
		MyWin.update()
	TrialClock.reset();
	while TrialClock.getTime()<0.5:		#blank after stimuli
		MyWin.update()#to blank just refresh screen without drawing	
	#present the test
	f1.set('contrast',ThisCont)
	f3.set('contrast',ThisCont)
	winsound.Beep(800,20); print ThisCont
	TrialClock.reset();
	while TrialClock.getTime()<0.3:	#
		GlobalT = ExpClock.getTime()
		f1.set('phase',GlobalT); 
		f1.set('phase',GlobalT + Trials['TestPhaseDiff'][TrialN] ); 
		f1.draw(); f3.draw()
	TrialClock.reset();
	while TrialClock.getTime()<0.25:		#blank after stimuli
		MyWin.update()#to blank just refresh screen without drawing
		
	#wait for user response
	KeyboardEvent = pygame.event.wait()#wait for a key to be pressed
	KeyPressed = pygame.key.name(KeyboardEvent.key)#get the name of the key
	while KeyPressed not in ['right','left','q']:#keep looping until we get a proper response
		KeyboardEvent = pygame.event.wait()#wait for another keypress
		KeyPressed = pygame.key.name(KeyboardEvent.key)#get the name of this key
	
	# what did user guess?
	if KeyPressed == 'left':  Trials['Resp'][TrialN]=0; ThisCont+=0.01
	elif KeyPressed=='right': Trials['Resp'][TrialN]=1; ThisCont-=0.01
	elif KeyPressed=='q':		quitNow=1; break


"""analyze the data"""

