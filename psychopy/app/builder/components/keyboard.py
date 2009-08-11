from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'keyboard.png')

class KeyboardComponent(BaseComponent):
    """An event class for checking the keyboard at given times"""
    def __init__(self, parentName, name='resp', allowedKeys='["q","left","right"]',store='last key',
            forceEndTrial=True,storeCorrect=False,correctIf="resp.keys==thisTrial.corrAns",storeResponseTime=True,times=[0,1]):
        self.type='Keyboard'
        self.psychopyLibs=['event']#needs this psychopy lib to operate
        self.parentName=parentName
        self.params={}
        self.order=['name','allowedKeys',
            'store','storeCorrect','correctIf',
            'forceEndTrial','times']
        self.params['name']=Param(name,  valType='code', hint="A name for this keyboard object (e.g. response)")  
        self.params['allowedKeys']=Param(allowedKeys, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="The keys the user may press, e.g. a,b,q,left,right")  
        self.params['times']=Param(times, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="A series of one or more periods to read the keyboard, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")
        self.params['store']=Param(store, valType='str', allowedTypes=[],allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant', allowedUpdates=[],
            hint="Choose which (if any) keys to store at end of trial")  
        self.params['forceEndTrial']=Param(forceEndTrial, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should the keypress force the end of the routine (e.g end the trial)?")
        self.params['storeCorrect']=Param(storeCorrect, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect?")
        self.params['correctIf']=Param(correctIf, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect? Might be helpful to add a corrAns column in the trialList")
        #todo: add response time clock to keyboard!!
        self.params['storeResponseTime']=Param(storeResponseTime, 
            valType='bool', 
            updates='constant', allowedUpdates=[],
            hint="Response time (saved as 'rt') is based from start of keyboard available period")
    def writeInitCode(self,buff):
        pass#no need to initialise keyboards?
    def writeRoutineStartCode(self, buff):
        if self.params['store'].val=='nothing' \
            and self.params['storeCorrect'].val==False \
            and self.params['storeResponseTime'].val==False:
            #the user doesn't want to store anything so don't bother
            return
        #create 
        buff.writeIndented("#store info from keyboard\n")
        buff.writeIndented("%s={'keys':None,'corr':None,'rt':None, 'clock'=None}\n" %self.params['name'])#start a dictionary
        
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        #some shortcuts
        store=self.params['store'].val
        storeCorr=self.params['storeCorrect'].val
        storeRT=self.params['storeResponseTime'].val
        forceEnd=self.params['forceEndTrial'].val
        
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        dedentAtEnd=1
        
        #check for keypresses
        buff.writeIndented("theseKeys = event.getKeys(keyList=%(allowedKeys)s)\n" %(self.params))
        buff.writeIndented("if len(theseKeys)>0:#at least one key was pressed")
        buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1
        
        if self.params['storeResponseTime'].val==True:
            buff.writeIndented("if %(name)s['clock']==None: %(name)s['clock']=core.Clock()" %self.params)
        #how do we store it?
        if store=='first key':#then see if a key has already been pressed
            buff.writeIndented("if %(name).keys==[]:#then this was the first keypress" %(self.params))
            buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1
            buff.writeIndented("%(name)s.keys=theseKeys[0]#just the first key pressed" %(self.params))
        elif store=='last key':
            buff.writeIndented("%(name)s.keys=theseKeys[-1]#just the last key pressed" %(self.params))
        elif store=='all keys':
            buff.writeIndented("%(name)s.keys.extend(theseKeys)#just the last key pressed" %(self.params))
        #get RT
        if storeRT:
            buff.writeIndented("%(name)s.rt = %(name)s['clock'].getTime()\n" %(self.params))
        #check if correct (if necess)
        if storeCorr:
            buff.writeIndented("if (%(correctIf)s): corr=1\n" %(self.params))
            buff.writeIndented("else: corr=0\n")
        #does the response end the trial?
        if forceEnd==True:
            buff.writeIndented("break #keypress ends routine\n")
            
        buff.setIndentLevel(-(dedentAtEnd), relative=True)          
    def writeRoutineEndCode(self, buff):
        #some shortcuts
        name = self.params['name']
        store=self.params['store'].val
        #work out which of multiple keys to store
        if store=='first key': index="[0]"
        elif store=='last key': index="[-1]"
        elif store=='all keys': index=""
        #write the actual text
        if store!='nothing':
            buff.writeIndented("if len(%s.keys)>0: %s.addData('%s.keys',%s.keys%s)" %(self.parentName,name,name,name,index))
        if self.params['storeCorrect'].val==True:
            buff.writeIndented("%s.addData('%s.corr',%s.corr)" %(self.parentName, name, name))
        if self.params['storeResponseTime'].val==True:
            buff.writeIndented("%s.addData('%s.rt',%s.rt)" %(self.parentName, name, name))
            