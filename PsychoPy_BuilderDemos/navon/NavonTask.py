#!/usr/bin/env python
"""This experiment was created using PsychoPy2 Experiment Builder If you publish work using this script please cite the relevant papers (e.g. Peirce, 2007;2009)"""

from numpy import * #many different maths functions
from numpy.random import * #maths randomisation functions
import os #handy system and path functions
from psychopy import core, data, event, visual, gui
import psychopy.log #import like this so it doesn't interfere with numpy.log

#store info about the experiment
expName='None'#from the Builder filename that created this script
expInfo={'participant':'001', 'session':1}
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
win = visual.Window(size=[2560, 1440], fullscr=True, screen=0,
    monitor='testMonitor', color='black', colorSpace='rgb')

#Initialise components for routine:instrPractice
instrPracticeClock=core.Clock()
instruct1=visual.TextStim(win=win, ori=0,
    text="In this experiment you will be presented with a large letter made up of smaller letters. Your task is to\n\nRespond by pressing;\n - 'S' if the SMALL letters are S\n - 'H' if the SMALL letters are H\n\nTry to respond as quickly and as accurately as possible.\n\nThere will be a number of practice trials in which you will be given feedback. \n\nPress any key when you are ready to proceed.",
    pos=[0, 0], height=0.075,
    color='white', colorSpace='rgb')
#create our own class to store info from keyboard
class KeyResponse:
    def __init__(self):
        self.keys=[]#the key(s) pressed
        self.corr=0#was the resp correct this trial? (0=no, 1=yes)
        self.rt=None#response time
        self.clock=None#we'll use this to measure the rt

#set up handler to look after randomisation of trials etc
practiceTrials=data.TrialHandler(nReps=1.0, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('trialTypes.xlsx'))
thisPracticetrial=practiceTrials.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisPracticetrial.rgb)
if thisPracticetrial!=None:
    for paramName in thisPracticetrial.keys():
        exec(paramName+'=thisPracticetrial.'+paramName)

#Initialise components for routine:trial
trialClock=core.Clock()
fixate=visual.TextStim(win=win, ori=0,
    text='+',
    units='cm', pos=[0, 0], height=2,
    color=[1, 1, 1], colorSpace='rgb')
stimulus=visual.PatchStim(win=win, tex=stimFile, mask='none',
    ori=0, pos=[xPos, yPos], size=[400,400], sf=None, phase=0.0,
    texRes=128, units='pix', interpolate=False)
mask=visual.PatchStim(win=win, tex='mask.png', mask='none',
    ori=0, pos=[xPos, yPos], size=[400,400], sf=None, phase=0.0,
    texRes=128, units='pix', interpolate=False)

#Initialise components for routine:feedback
feedbackClock=core.Clock()
#msg variable just needs some value at start
msg=''
feedback=visual.TextStim(win=win, ori=0,
    text=msg,
    pos=[0, 0], height=0.1,
    color=[1,1,1], colorSpace='rgb')

#Initialise components for routine:instrMain
instrMainClock=core.Clock()
instr2=visual.TextStim(win=win, ori=0,
    text="OK, ready to start the main experiment?\n\nRemember, press;\n - 'S' if the SMALL letters are S\n - 'H' if the SMALL letters are H\n\nTry to respond as quickly and as accurately as possible.\n\nWhen you are ready to proceed press any key.",
    pos=[0, 0], height=0.075,
    color='white', colorSpace='rgb')

#set up handler to look after randomisation of trials etc
trials=data.TrialHandler(nReps=2.0, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('trialTypes.xlsx'))
thisTrial=trials.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisTrial.rgb)
if thisTrial!=None:
    for paramName in thisTrial.keys():
        exec(paramName+'=thisTrial.'+paramName)

#Initialise components for routine:trial
trialClock=core.Clock()
fixate=visual.TextStim(win=win, ori=0,
    text='+',
    units='cm', pos=[0, 0], height=2,
    color=[1, 1, 1], colorSpace='rgb')
stimulus=visual.PatchStim(win=win, tex=stimFile, mask='none',
    ori=0, pos=[xPos, yPos], size=[400,400], sf=None, phase=0.0,
    texRes=128, units='pix', interpolate=False)
mask=visual.PatchStim(win=win, tex='mask.png', mask='none',
    ori=0, pos=[xPos, yPos], size=[400,400], sf=None, phase=0.0,
    texRes=128, units='pix', interpolate=False)

#Initialise components for routine:thanks
thanksClock=core.Clock()
thanksMsg=visual.TextStim(win=win, ori=0,
    text="You're done! Fun, wasn't it!? ;-)",
    pos=[0, 0], height=0.1,
    color=[1,1,1], colorSpace='rgb')

#update component parameters for each repeat
ok1 = KeyResponse()#create an object of type KeyResponse

#run the trial
continueInstrpractice=True
t=0; instrPracticeClock.reset()
while continueInstrpractice and (t<1000000.0000):
    #get current time
    t=instrPracticeClock.getTime()
    
    #update/draw components on each frame
    if (0.0 <= t):
        instruct1.draw()
    if (0.0 <= t):
        theseKeys = event.getKeys()
        if len(theseKeys)>0:#at least one key was pressed
            ok1.keys=theseKeys[-1]#just the last key pressed
            #abort routine on response
            continueInstrpractice=False
    
    #check for quit (the [Esc] key)
    if event.getKeys(["escape"]): core.quit()
    event.clearEvents()#so that it doesn't get clogged with other events
    #refresh the screen
    win.flip()

#end of this routine (e.g. trial)

for thisPracticetrial in practiceTrials:
    #abbrieviate parameter names if possible (e.g. rgb=thisPracticetrial.rgb)
    if thisPracticetrial!=None:
        for paramName in thisPracticetrial.keys():
            exec(paramName+'=thisPracticetrial.'+paramName)
    
    #update component parameters for each repeat
    stimulus.setTex(stimFile)
    stimulus.setPos([xPos, yPos])
    mask.setPos([xPos, yPos])
    resp = KeyResponse()#create an object of type KeyResponse
    
    #run the trial
    continueTrial=True
    t=0; trialClock.reset()
    while continueTrial and (t<9.0000):
        #get current time
        t=trialClock.getTime()
        
        #update/draw components on each frame
        if (1.0<= t < (1.0+1.0)):
            fixate.draw()
        if (2.0<= t < (2.0+0.3)):
            stimulus.draw()
        if (2.3<= t < (2.3+5.0)):
            mask.draw()
        if (2.0<= t < (2.0+7.0)):
            if resp.clock==None: #if we don't have one we've just started
                resp.clock=core.Clock()#create one (now t=0)
            theseKeys = event.getKeys(keyList="['s','h']")
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
        practiceTrials.addData('resp.keys',resp.keys[-1])
        practiceTrials.addData('resp.corr',resp.corr)
        practiceTrials.addData('resp.rt',resp.rt)
    
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
    

#completed 1.0 repeats of 'practiceTrials' repeats

practiceTrials.saveAsPickle(filename+'practiceTrials')
practiceTrials.saveAsExcel(filename+'.xlsx', sheetName='practiceTrials',
    stimOut=['xPos', 'congruence', 'yPos', 'location', 'stimFile', 'corrAns', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')

#update component parameters for each repeat

#run the trial
continueInstrmain=True
t=0; instrMainClock.reset()
while continueInstrmain and (t<1000000.0000):
    #get current time
    t=instrMainClock.getTime()
    
    #update/draw components on each frame
    if (0.0 <= t):
        instr2.draw()
    if (0.0 <= t):
        theseKeys = event.getKeys()
        if len(theseKeys)>0:#at least one key was pressed
            #abort routine on response
            continueInstrmain=False
    
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
    stimulus.setTex(stimFile)
    stimulus.setPos([xPos, yPos])
    mask.setPos([xPos, yPos])
    resp = KeyResponse()#create an object of type KeyResponse
    
    #run the trial
    continueTrial=True
    t=0; trialClock.reset()
    while continueTrial and (t<9.0000):
        #get current time
        t=trialClock.getTime()
        
        #update/draw components on each frame
        if (1.0<= t < (1.0+1.0)):
            fixate.draw()
        if (2.0<= t < (2.0+0.3)):
            stimulus.draw()
        if (2.3<= t < (2.3+5.0)):
            mask.draw()
        if (2.0<= t < (2.0+7.0)):
            if resp.clock==None: #if we don't have one we've just started
                resp.clock=core.Clock()#create one (now t=0)
            theseKeys = event.getKeys(keyList="['s','h']")
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
        trials.addData('resp.keys',resp.keys[-1])
        trials.addData('resp.corr',resp.corr)
        trials.addData('resp.rt',resp.rt)

#completed 2.0 repeats of 'trials' repeats

trials.saveAsPickle(filename+'trials')
trials.saveAsExcel(filename+'.xlsx', sheetName='trials',
    stimOut=['xPos', 'congruence', 'yPos', 'location', 'stimFile', 'corrAns', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')

#update component parameters for each repeat

#run the trial
continueThanks=True
t=0; thanksClock.reset()
while continueThanks and (t<2.0000):
    #get current time
    t=thanksClock.getTime()
    
    #update/draw components on each frame
    if (0.0<= t < (0.0+2.0)):
        thanksMsg.draw()
    
    #check for quit (the [Esc] key)
    if event.getKeys(["escape"]): core.quit()
    event.clearEvents()#so that it doesn't get clogged with other events
    #refresh the screen
    win.flip()

#end of this routine (e.g. trial)

logFile.close()