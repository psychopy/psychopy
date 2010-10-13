#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This experiment was created using PsychoPy2 Experiment Builder
If you publish work using this script please cite the relevant PsychoPy publications
  Peirce (2007) Journal of Neuroscience Methods 162:8-1
  Peirce (2009) Frontiers in Neuroinformatics, 2: 10)"""

from numpy import * #many different maths functions
from numpy.random import * #maths randomisation functions
import os #handy system and path functions
from psychopy import core, data, event, visual, gui
import psychopy.log #import like this so it doesn't interfere with numpy.log

#store info about the experiment
expName='None'#from the Builder filename that created this script
expInfo={'participant':'001', 'session':001}
dlg=gui.DlgFromDict(dictionary=expInfo,title=expName)
if dlg.OK==False: core.quit() #user pressed cancel
expInfo['date']=data.getDateStr()#add a simple timestamp
expInfo['expName']=expName
#setup files for saving
if not os.path.isdir('data'):
    os.makedirs('data')#if this fails (e.g. permissions) we will get error
filename= 'data/%s_%s' %(expInfo['participant'], expInfo['date'])
logFile=open(filename+'.log', 'w')
psychopy.log.console.setLevel(psychopy.log.WARNING)#this outputs to the screen, not a file

#setup the Window
win = visual.Window(size=[2560, 1440], fullscr=True, screen=0, allowGUI=False,
    monitor='testMonitor', color=[0,0,0], colorSpace='rgb')

#set up handler to look after randomisation of trials etc
trials=data.TrialHandler(nReps=1.0, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('balloons.xlsx'))
thisTrial=trials.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisTrial.rgb)
if thisTrial!=None:
    for paramName in thisTrial.keys():
        exec(paramName+'=thisTrial.'+paramName)

#Initialise components for routine:trial
trialClock=core.Clock()
bankedEarnings=0.0
lastBalloonEarnings=0.0
thisBalloonEarnings=0.0
balloonSize=0.08
balloonMsgHeight=0.01
print 'nPumps', 'balloonSize', 'popped'
balloonBody=visual.PatchStim(win=win, tex='redBalloon3.png', mask='None',
    ori=0, pos=[-1+balloonSize/2, 0], size=balloonSize, sf=1, phase=0.0,
    color='white', colorSpace='rgb',
    texRes=512, units='norm', interpolate=False)
pumpMsg=visual.TextStim(win=win, ori=0,
    text='Press SPACE to pump the balloon\nPress RETURN to bank this sum',
    pos=[0, -0.8], height=0.05,
    color='white', colorSpace='rgb')
balloonValMsg=visual.TextStim(win=win, ori=0,
    text=u"£%.2f" %thisBalloonEarnings,
    pos=[0,0.05], height=0.1,
    color='white', colorSpace='rgb')

#create our own class to store info from keyboard
class KeyResponse:
    def __init__(self):
        self.keys=[]#the key(s) pressed
        self.corr=0#was the resp correct this trial? (0=no, 1=yes)
        self.rt=None#response time
        self.clock=None#we'll use this to measure the rt
bankMsg=visual.TextStim(win=win, ori=0,
    text="You have banked:\n%£.2f" %bankedEarnings,
    pos=[0, 0], height=0.1,
    color='white', colorSpace='rgb')

for thisTrial in trials:
    #abbrieviate parameter names if possible (e.g. rgb=thisTrial.rgb)
    if thisTrial!=None:
        for paramName in thisTrial.keys():
            exec(paramName+'=thisTrial.'+paramName)
    
    #update component parameters for each repeat
    
    balloonSize=0.08
    popped=False
    nPumps=0
    
    bankButton = KeyResponse()#create an object of type KeyResponse
    
    #run the trial
    continueTrial=True
    t=0; trialClock.reset()
    while continueTrial and (t<1000000.0000):
        #get current time
        t=trialClock.getTime()
        
        #update/draw components on each frame
        thisBalloonEarnings=nPumps*0.05
        balloonSize=0.1+nPumps*0.015
        if (0.0 <= t):
            balloonBody.setPos([-1+balloonSize/2, 0])
            balloonBody.setSize(balloonSize)
            balloonBody.draw()
        if (0.0 <= t):
            pumpMsg.draw()
        if (0.0 <= t):
            balloonValMsg.setText(u"£%.2f" %thisBalloonEarnings)
            balloonValMsg.draw()
        if event.getKeys(['space']):
          nPumps=nPumps+1
          if balloonSize>breakPoint:
            popped=True
            continueTrial=False
        if (0.0 <= t):
            if bankButton.clock==None: #if we don't have one we've just started
                bankButton.clock=core.Clock()#create one (now t=0)
            theseKeys = event.getKeys(keyList='["return"]')
            if len(theseKeys)>0:#at least one key was pressed
                bankButton.keys=theseKeys[-1]#just the last key pressed
                bankButton.rt = bankButton.clock.getTime()
                #abort routine on response
                continueTrial=False
        if (0.0 <= t):
            bankMsg.setText("You have banked:\n%£.2f" %bankedEarnings)
            bankMsg.draw()
        
        #check for quit (the [Esc] key)
        if event.getKeys(["escape"]): core.quit()
        event.clearEvents()#so that it doesn't get clogged with other events
        #refresh the screen
        win.flip()
    
    #end of this routine (e.g. trial)
    #calculate cash 'earned'
    if popped:
      lastBalloonEarnings=0.0
    else:   lastBalloonEarnings=thisBalloonEarnings
    bankedEarnings = bankedEarnings+lastBalloonEarnings
    #save data
    trials.addData('nPumps', nPumps)
    trials.addData('size', balloonSize)
    trials.addData('popped', popped)
    #print data for info
    print nPumps, balloonSize, popped
    
    
    if len(bankButton.keys)>0:#we had a response
        trials.addData('bankButton.keys',bankButton.keys)
        trials.addData('bankButton.rt',bankButton.rt)

#completed 1.0 repeats of 'trials' repeats

trials.saveAsPickle(filename+'trials')
trials.saveAsExcel(filename+'.xlsx', sheetName='trials',
    stimOut=['balloonColour', 'breakPoint', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')



logFile.close()
win.close()
core.quit()
