#!/usr/bin/env python
"""This experiment was created using PsychoPy2 Experiment Builder If you publish work using this script please cite the relevant papers (e.g. Peirce, 2007;2009)"""

from numpy import * #many different maths functions
from numpy.random import * #maths randomisation functions
import os #handy system and path functions
from psychopy import core, data, event, visual, gui
import psychopy.log #import like this so it doesn't interfere with numpy.log

#store info about the experiment
expName='None'#from the Builder filename that created this script
expInfo={'participant':'ID', 'session':002}
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
    monitor='testMonitor', color=[0, 0, 0], colorSpace='rgb')

#Initialise components for routine:practInstruct
practInstructClock=core.Clock()
instr1=visual.TextStim(win=win, ori=0,
    text='In this experiment you will be presented with a sequence of between 1 and 6 randomly ordered numbers.\n\nFollowing a short delay you will then be presented with a single number and you will have to decide whether this new number was a member of the sequence.\n\nRespond with the top row number keys:\n - LEFT CURSOR if the number was NOT in the sequence\n - RIGHT CURSOR if the number WAS in the sequence\n\nThere will be a number of practice trials in which you will be given feedback.  Try to respond as quickly and as accurately as possible.\n\nWhen you are ready to proceed press any key.',
    pos=[0, 0], height=0.05,
    color=[1,1,1], colorSpace='rgb')
#create our own class to store info from keyboard
class KeyResponse:
    def __init__(self):
        self.keys=[]#the key(s) pressed
        self.corr=0#was the resp correct this trial? (0=no, 1=yes)
        self.rt=None#response time
        self.clock=None#we'll use this to measure the rt

#set up handler to look after randomisation of trials etc
pracTrials=data.TrialHandler(nReps=1.0, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('pracTrials.xlsx'))
thisPractrial=pracTrials.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisPractrial.rgb)
if thisPractrial!=None:
    for paramName in thisPractrial.keys():
        exec(paramName+'=thisPractrial.'+paramName)

#Initialise components for routine:trial
trialClock=core.Clock()
fixation=visual.TextStim(win=win, ori=0,
    text='+',
    pos=[0, 0], height=0.05,
    color='white', colorSpace='rgb')
presentSet=visual.TextStim(win=win, ori=0,
    text=numberSet,
    pos=[0, 0], height=0.1,
    color='white', colorSpace='rgb')
presentTarget=visual.TextStim(win=win, ori=0,
    text=target,
    pos=[0, 0], height=0.1,
    color='white', colorSpace='rgb')

#Initialise components for routine:feedback
feedbackClock=core.Clock()
#msg variable just needs some value at start
msg=''
feedback=visual.TextStim(win=win, ori=0,
    text=msg,
    pos=[0, 0], height=0.1,
    color=[1,1,1], colorSpace='rgb')

#Initialise components for routine:mainInstruct
mainInstructClock=core.Clock()
instr2=visual.TextStim(win=win, ori=0,
    text="OK, ready to start the main experiment?\n\nRemember:\n - '1' for 'not in the set'\n - '9' for 'in the set'\n\nTry to respond as quickly and as accurately as possible.\n\nWhen you are ready to proceed press any key.",
    pos=[0, 0], height=0.05,
    color=[1, 1, 1], colorSpace='rgb')

#set up handler to look after randomisation of trials etc
trials=data.TrialHandler(nReps=1.0, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('mainTrials.xlsx'))
thisTrial=trials.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisTrial.rgb)
if thisTrial!=None:
    for paramName in thisTrial.keys():
        exec(paramName+'=thisTrial.'+paramName)

#Initialise components for routine:trial
trialClock=core.Clock()
fixation=visual.TextStim(win=win, ori=0,
    text='+',
    pos=[0, 0], height=0.05,
    color='white', colorSpace='rgb')
presentSet=visual.TextStim(win=win, ori=0,
    text=numberSet,
    pos=[0, 0], height=0.1,
    color='white', colorSpace='rgb')
presentTarget=visual.TextStim(win=win, ori=0,
    text=target,
    pos=[0, 0], height=0.1,
    color='white', colorSpace='rgb')

#update component parameters for each repeat
OK1 = KeyResponse()#create an object of type KeyResponse

#run the trial
continuePractinstruct=True
t=0; practInstructClock.reset()
while continuePractinstruct and (t<1000000.0000):
    #get current time
    t=practInstructClock.getTime()
    
    #update/draw components on each frame
    if (0.0 <= t):
        instr1.draw()
    if (0.0 <= t):
        theseKeys = event.getKeys()
        if len(theseKeys)>0:#at least one key was pressed
            OK1.keys=theseKeys[-1]#just the last key pressed
            #abort routine on response
            continuePractinstruct=False
    
    #check for quit (the [Esc] key)
    if event.getKeys(["escape"]): core.quit()
    event.clearEvents()#so that it doesn't get clogged with other events
    #refresh the screen
    win.flip()

#end of this routine (e.g. trial)

for thisPractrial in pracTrials:
    #abbrieviate parameter names if possible (e.g. rgb=thisPractrial.rgb)
    if thisPractrial!=None:
        for paramName in thisPractrial.keys():
            exec(paramName+'=thisPractrial.'+paramName)
    
    #update component parameters for each repeat
    presentSet.setText(numberSet)
    presentTarget.setText(target)
    resp = KeyResponse()#create an object of type KeyResponse
    
    #run the trial
    continueTrial=True
    t=0; trialClock.reset()
    while continueTrial and (t<1000000.0000):
        #get current time
        t=trialClock.getTime()
        
        #update/draw components on each frame
        if (0.0<= t < (0.0+1.0)):
            fixation.draw()
        if (1.2<= t < (1.2+1.5)):
            presentSet.draw()
        if (4.7<= t < (4.7+2)):
            presentTarget.draw()
        if (4.7 <= t):
            if resp.clock==None: #if we don't have one we've just started
                resp.clock=core.Clock()#create one (now t=0)
            theseKeys = event.getKeys(keyList="['left','right']")
            if len(theseKeys)>0:#at least one key was pressed
                resp.keys=theseKeys[-1]#just the last key pressed
                resp.rt = resp.clock.getTime()
                #was this 'correct'?
                if (resp.keys==str(corrAns)): resp.corr=1
                else: resp.corr=0
                #abort routine on response
                continueTrial=False
        
        #check for quit (the [Esc] key)
        if event.getKeys(["escape"]): core.quit()
        event.clearEvents()#so that it doesn't get clogged with other events
        #refresh the screen
        win.flip()
    
    #end of this routine (e.g. trial)
    if len(resp.keys)>0:#we had a response
        pracTrials.addData('resp.keys',resp.keys)
        pracTrials.addData('resp.corr',resp.corr)
        pracTrials.addData('resp.rt',resp.rt)
    
    #update component parameters for each repeat
    if resp.corr:#stored on last run routine
      msg="Correct! RT=%.3f" %(resp.rt)
    else:
      msg="Oops! That was wrong"
    feedback.setText(msg)
    
    #run the trial
    continueFeedback=True
    t=0; feedbackClock.reset()
    while continueFeedback and (t<1.0000):
        #get current time
        t=feedbackClock.getTime()
        
        #update/draw components on each frame
        
        if (0.0<= t < (0.0+1.0)):
            feedback.draw()
        
        #check for quit (the [Esc] key)
        if event.getKeys(["escape"]): core.quit()
        event.clearEvents()#so that it doesn't get clogged with other events
        #refresh the screen
        win.flip()
    
    #end of this routine (e.g. trial)
    

#completed 1.0 repeats of 'pracTrials' repeats

pracTrials.saveAsPickle(filename+'pracTrials')
pracTrials.saveAsExcel(filename+'.xlsx', sheetName='pracTrials',
    stimOut=['numberSet', 'target', 'corrAns', 'posInSet', 'setSize', 'present', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')

#update component parameters for each repeat
OK2 = KeyResponse()#create an object of type KeyResponse

#run the trial
continueMaininstruct=True
t=0; mainInstructClock.reset()
while continueMaininstruct and (t<1000000.0000):
    #get current time
    t=mainInstructClock.getTime()
    
    #update/draw components on each frame
    if (0.0 <= t):
        instr2.draw()
    if (0.0 <= t):
        theseKeys = event.getKeys()
        if len(theseKeys)>0:#at least one key was pressed
            OK2.keys=theseKeys[-1]#just the last key pressed
            #abort routine on response
            continueMaininstruct=False
    
    #check for quit (the [Esc] key)
    if event.getKeys(["escape"]): core.quit()
    event.clearEvents()#so that it doesn't get clogged with other events
    #refresh the screen
    win.flip()

#end of this routine (e.g. trial)

for thisTrial in trials:
    #abbrieviate parameter names if possible (e.g. rgb=thisTrial.rgb)
    if thisTrial!=None:
        for paramName in thisTrial.keys():
            exec(paramName+'=thisTrial.'+paramName)
    
    #update component parameters for each repeat
    presentSet.setText(numberSet)
    presentTarget.setText(target)
    resp = KeyResponse()#create an object of type KeyResponse
    
    #run the trial
    continueTrial=True
    t=0; trialClock.reset()
    while continueTrial and (t<1000000.0000):
        #get current time
        t=trialClock.getTime()
        
        #update/draw components on each frame
        if (0.0<= t < (0.0+1.0)):
            fixation.draw()
        if (1.2<= t < (1.2+1.5)):
            presentSet.draw()
        if (4.7<= t < (4.7+2)):
            presentTarget.draw()
        if (4.7 <= t):
            if resp.clock==None: #if we don't have one we've just started
                resp.clock=core.Clock()#create one (now t=0)
            theseKeys = event.getKeys(keyList="['left','right']")
            if len(theseKeys)>0:#at least one key was pressed
                resp.keys=theseKeys[-1]#just the last key pressed
                resp.rt = resp.clock.getTime()
                #was this 'correct'?
                if (resp.keys==str(corrAns)): resp.corr=1
                else: resp.corr=0
                #abort routine on response
                continueTrial=False
        
        #check for quit (the [Esc] key)
        if event.getKeys(["escape"]): core.quit()
        event.clearEvents()#so that it doesn't get clogged with other events
        #refresh the screen
        win.flip()
    
    #end of this routine (e.g. trial)
    if len(resp.keys)>0:#we had a response
        trials.addData('resp.keys',resp.keys)
        trials.addData('resp.corr',resp.corr)
        trials.addData('resp.rt',resp.rt)

#completed 1.0 repeats of 'trials' repeats

trials.saveAsPickle(filename+'trials')
trials.saveAsExcel(filename+'.xlsx', sheetName='trials',
    stimOut=['numberSet', 'target', 'corrAns', 'posInSet', 'setSize', 'present', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')

logFile.close()
win.close()
core.quit()
