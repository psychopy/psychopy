#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This experiment was created using PsychoPy2 Experiment Builder
If you publish work using this script please cite the relevant PsychoPy publications
  Peirce (2007) Journal of Neuroscience Methods 162:8-1
  Peirce (2009) Frontiers in Neuroinformatics, 2: 10"""

from numpy import * #many different maths functions
from numpy.random import * #maths randomisation functions
import os #handy system and path functions
from psychopy import core, data, event, visual, gui
import psychopy.log #import like this so it doesn't interfere with numpy.log

#store info about the experiment
expName='None'#from the Builder filename that created this script
expInfo={'participant':'ID01', 'session':001}
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
win = visual.Window(size=[1024, 768], fullscr=True, screen=0, allowGUI=False,
    monitor='testMonitor', color=[0,0,0], colorSpace='rgb')

#Initialise components for routine:instr
instrClock=core.Clock()
instrText=visual.TextStim(win=win, ori=0,
    text="If you press 'a' you'll get 3 trials of Routine A\n\nIf you press 'b' you'll get 3 trials of Routine B",
    pos=[0, 0], height=0.1,
    color='white', colorSpace='rgb')
#create our own class to store info from keyboard
class KeyResponse:
    def __init__(self):
        self.keys=[]#the key(s) pressed
        self.corr=0#was the resp correct this trial? (0=no, 1=yes)
        self.rt=None#response time
        self.clock=None#we'll use this to measure the rt


#set up handler to look after randomisation of trials etc
repsA=data.TrialHandler(nReps=1, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('trialTypes.xlsx'))
thisReps=repsA.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisReps.rgb)
if thisReps!=None:
    for paramName in thisReps.keys():
        exec(paramName+'=thisReps.'+paramName)

#Initialise components for routine:A
AClock=core.Clock()
msgA=visual.TextStim(win=win, ori=0,
    text='You chose A (the blue pill?)',
    pos=[0, 0], height=0.1,
    color=letterColor, colorSpace='rgb')

#set up handler to look after randomisation of trials etc
repsB=data.TrialHandler(nReps=1, method='random', extraInfo=expInfo, 
    trialList=data.importTrialList('trialTypes.xlsx'))
thisReps=repsB.trialList[0]#so we can initialise stimuli with some values
#abbrieviate parameter names if possible (e.g. rgb=thisReps.rgb)
if thisReps!=None:
    for paramName in thisReps.keys():
        exec(paramName+'=thisReps.'+paramName)

#Initialise components for routine:B
BClock=core.Clock()
msgB=visual.TextStim(win=win, ori=0,
    text='You chose B (the red pill?)',
    pos=[0, 0], height=0.1,
    color=letterColor, colorSpace='rgb')

#update component parameters for each repeat
resp = KeyResponse()#create an object of type KeyResponse


#run the trial
continueInstr=True
t=0; instrClock.reset()
while continueInstr and (t<1000000.0000):
    #get current time
    t=instrClock.getTime()
    
    #update/draw components on each frame
    if (0.0 <= t):
        instrText.draw()
    if (0.0 <= t):
        theseKeys = event.getKeys(keyList='ab')
        if len(theseKeys)>0:#at least one key was pressed
            resp.keys=theseKeys[-1]#just the last key pressed
            #abort routine on response
            continueInstr=False
    
    
    #check for quit (the [Esc] key)
    if event.getKeys(["escape"]): core.quit()
    event.clearEvents()#so that it doesn't get clogged with other events
    #refresh the screen
    win.flip()

#end of this routine (e.g. trial)
if resp.keys=='a':
    repsB.finished=True
else:
    repsA.finished=True


for thisReps in repsA:
    #abbrieviate parameter names if possible (e.g. rgb=thisReps.rgb)
    if thisReps!=None:
        for paramName in thisReps.keys():
            exec(paramName+'=thisReps.'+paramName)
    
    #update component parameters for each repeat
    msgA.setColor(letterColor, colorSpace='rgb')
    
    #run the trial
    continueA=True
    t=0; AClock.reset()
    while continueA and (t<1.0000):
        #get current time
        t=AClock.getTime()
        
        #update/draw components on each frame
        if (0.0<= t < (0.0+1.0)):
            msgA.draw()
        
        #check for quit (the [Esc] key)
        if event.getKeys(["escape"]): core.quit()
        event.clearEvents()#so that it doesn't get clogged with other events
        #refresh the screen
        win.flip()
    
    #end of this routine (e.g. trial)

#completed 1 repeats of 'repsA' repeats

repsA.saveAsPickle(filename+'repsA')
repsA.saveAsExcel(filename+'.xlsx', sheetName='repsA',
    stimOut=['letterColor', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')

for thisReps in repsB:
    #abbrieviate parameter names if possible (e.g. rgb=thisReps.rgb)
    if thisReps!=None:
        for paramName in thisReps.keys():
            exec(paramName+'=thisReps.'+paramName)
    
    #update component parameters for each repeat
    msgB.setColor(letterColor, colorSpace='rgb')
    
    #run the trial
    continueB=True
    t=0; BClock.reset()
    while continueB and (t<1.0000):
        #get current time
        t=BClock.getTime()
        
        #update/draw components on each frame
        if (0.0<= t < (0.0+1.0)):
            msgB.draw()
        
        #check for quit (the [Esc] key)
        if event.getKeys(["escape"]): core.quit()
        event.clearEvents()#so that it doesn't get clogged with other events
        #refresh the screen
        win.flip()
    
    #end of this routine (e.g. trial)

#completed 1 repeats of 'repsB' repeats

repsB.saveAsPickle(filename+'repsB')
repsB.saveAsExcel(filename+'.xlsx', sheetName='repsB',
    stimOut=['letterColor', ],
    dataOut=['n','all_mean','all_std', 'all_raw'])
psychopy.log.info('saved data to '+filename+'.dlm')

logFile.close()
win.close()
core.quit()
