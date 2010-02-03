# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'keyboard.png')

class KeyboardComponent(BaseComponent):
    """An event class for checking the keyboard at given timepoints"""
    def __init__(self, exp, parentName, name='resp', allowedKeys='["left","right"]',store='last key',
            forceEndTrial=True,storeCorrect=False,correctAns="",storeResponseTime=True,
            startTime=0.0, duration=1.0):
        self.type='Keyboard'
        self.url="http://www.psychopy.org/builder/components/keyboard.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['gui'])
        self.parentName=parentName
        #params
        self.params={}
        self.order=['name','allowedKeys',
            'store','storeCorrect','correctAns',
            'forceEndTrial','startTime']
        self.params['name']=Param(name,  valType='code', hint="A name for this keyboard object (e.g. response)")  
        self.params['allowedKeys']=Param(allowedKeys, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="The keys the user may press, e.g. a,b,q,left,right")
        self.params['startTime']=Param(startTime, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The time that the keyboard starts being checked")
        self.params['duration']=Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The length of time that the keyboard should be checked")
        self.params['store']=Param(store, valType='str', allowedTypes=[],allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant', allowedUpdates=[],
            hint="Choose which (if any) keys to store at end of trial")  
        self.params['forceEndTrial']=Param(forceEndTrial, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should the keypress force the end of the routine (e.g end the trial)?")
        self.params['storeCorrect']=Param(storeCorrect, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect?")
        self.params['correctAns']=Param(correctAns, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="What is the 'correct' key? Might be helpful to add a correctAns column to your definition of trials in the loop")
        #todo: add response time clock to keyboard!!
        self.params['storeResponseTime']=Param(storeResponseTime, 
            valType='bool', 
            updates='constant', allowedUpdates=[],
            hint="Response time (saved as 'rt') is based from start of keyboard available period")
    def writeInitCode(self,buff):
        #create a key response object - easier to store data (including a clock to start 
        #at beginning of keyboard testing
        if self.exp.noKeyResponse and self.params['store'].val!='nothing':
            buff.writeIndented("#create our own class to store info from keyboard\n")
            buff.writeIndented("class KeyResponse:\n")
            buff.writeIndented("    def __init__(self):\n")
            buff.writeIndented("        self.keys=[]#the key(s) pressed\n")
            buff.writeIndented("        self.corr=None#was the subj correct this trial?\n")
            buff.writeIndented("        self.rt=None#response time\n")
            buff.writeIndented("        self.clock=None#we'll use this to measure the rt\n")
            self.exp.noKeyResponse=False#don't write this again
    def writeRoutineStartCode(self,buff):
        if self.params['store'].val=='nothing' \
            and self.params['storeCorrect'].val==False \
            and self.params['storeResponseTime'].val==False:
            #the user doesn't want to store anything so don't bother
            return
        buff.writeIndented("%(name)s = KeyResponse()#create an object of type KeyResponse\n" %self.params)
        
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        #some shortcuts
        store=self.params['store'].val
        storeCorr=self.params['storeCorrect'].val
        storeRT=self.params['storeResponseTime'].val
        forceEnd=self.params['forceEndTrial'].val
        continueName = self.exp.flow._currentRoutine._continueName
        
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the time test
        dedentAtEnd=1
        #create a clo
        if self.params['storeResponseTime'].val==True:
            buff.writeIndented("if %(name)s.clock==None: #if we don't have one we've just started\n" %self.params)
            buff.writeIndented("    %(name)s.clock=core.Clock()#create one (now t=0)\n" %self.params)
            
        #do we need a list of keys?
        if self.params['allowedKeys'].val in [None, "", "[]"]: keyListStr=""
        else: keyListStr= "keyList=%(allowedKeys)s" %(self.params)
        #check for keypresses
        buff.writeIndented("theseKeys = event.getKeys(%s)\n" %(keyListStr))
        
        #how do we store it?
        if store!='nothing' or storeRT or storeCorr:
            #we are going to store something
            buff.writeIndented("if len(theseKeys)>0:#at least one key was pressed\n")
            buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1
            if store=='first key':#then see if a key has already been pressed
                buff.writeIndented("if %(name).keys==[]:#then this was the first keypress\n" %(self.params))
                buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1
                buff.writeIndented("%(name)s.keys=theseKeys[0]#just the first key pressed\n" %(self.params))
            elif store=='last key':
                buff.writeIndented("%(name)s.keys=theseKeys[-1]#just the last key pressed\n" %(self.params))
            elif store=='all keys':
                buff.writeIndented("%(name)s.keys.extend(theseKeys)#just the last key pressed\n" %(self.params))
            #get RT
            if storeRT:
                buff.writeIndented("%(name)s.rt = %(name)s.clock.getTime()\n" %(self.params))
            #check if correct (if necess)
            if storeCorr:
                buff.writeIndented("#was this 'correct'?\n" %self.params)
                buff.writeIndented("if (%(name)s.keys==str(%(correctAns)s)): %(name)s.corr=1\n" %(self.params))
                buff.writeIndented("else: %(name)s.corr=0\n" %self.params)
        #does the response end the trial?
        if forceEnd==True:
            buff.writeIndented("#abort routine on response\n" %self.params)
            buff.writeIndented("%s=False\n" %continueName)
            
        buff.setIndentLevel(-(dedentAtEnd), relative=True)          
    def writeRoutineEndCode(self,buff):
        #some shortcuts
        name = self.params['name']
        store=self.params['store'].val
        if len(self.exp.flow._loopList):
            currLoop=self.exp.flow._loopList[-1]#last (outer-most) loop
        else: currLoop=None
        
        #work out which of multiple keys to store
        if store=='first key': index="[0]"
        elif store=='last key': index="[-1]"
        elif store=='all keys': index=""
        
        #write the actual code
        if store!='nothing' and currLoop and currLoop.type=='StairHandler':
            #data belongs to a StairHandler
            buff.writeIndented("if len(%s.keys)>0:#we had a response\n" %name)
            if self.params['storeCorrect'].val==True:
                buff.writeIndented("    %s.addData(%s.corr)\n" \
                                   %(currLoop.params['name'], name))
        elif store!='nothing' and currLoop:
            #data belongs to a TrialHandler
            buff.writeIndented("if len(%s.keys)>0:#we had a response\n" %name)
            buff.writeIndented("    %s.addData('%s.keys',%s.keys%s)\n" \
                               %(currLoop.params['name'],name,name,index))
            if self.params['storeCorrect'].val==True:
                buff.writeIndented("    %s.addData('%s.corr',%s.corr)\n" \
                                   %(currLoop.params['name'], name, name))
            if self.params['storeResponseTime'].val==True:
                buff.writeIndented("    %s.addData('%s.rt',%s.rt)\n" \
                                   %(currLoop.params['name'], name, name))
            