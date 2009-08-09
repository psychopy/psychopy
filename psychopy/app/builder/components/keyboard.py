from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'keyboard.png')

class KeyboardComponent(BaseComponent):
    """An event class for checking the keyboard at given times"""
    def __init__(self, parentName, name='', allowedKeys='["q","left","right"]',storeWhat='first key',
            forceEndTrial=True,storeCorrect=False,correctIf="==thisTrial.corrAns",times=[0,1]):
        self.type='Keyboard'
        self.psychopyLibs=['event']#needs this psychopy lib to operate
        self.parentName=parentName
        self.params={}
        self.order=['name','allowedKeys',
            'storeWhat','storeCorrect','correctIf',
            'forceEndTrial','times']
        self.params['name']=Param(name,  valType='code', hint="A name for this keyboard object (e.g. response)")  
        self.params['allowedKeys']=Param(allowedKeys, valType='str', allowedTypes=['str','code'],
            updates="never", allowedUpdates=["never","routine"],
            hint="The keys the user may press, e.g. a,b,q,left,right")  
        self.params['times']=Param(times, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="A series of one or more periods to read the keyboard, e.g. [2.0,2.5] or [[2.0,2.5],[3.0,3.8]]")
        self.params['storeWhat']=Param(storeWhat, valType='str', allowedTypes=['str'],allowedVals=['first key', 'all keys', 'nothing'],
            updates="never", allowedUpdates=["never"],
            hint="Store a single key, or append to a list of all keys pressed during the routine")  
        self.params['forceEndTrial']=Param(forceEndTrial, valType='bool', allowedTypes=['bool'],
            updates="never", allowedUpdates=["never"],
            hint="Should the keypress force the end of the routine (e.g end the trial)?")
        self.params['storeCorrect']=Param(storeCorrect, valType='bool', allowedTypes=['bool'],
            updates="never", allowedUpdates=["never"],
            hint="Do you want to save the response as correct/incorrect?")
        self.params['correctIf']=Param(correctIf, valType='code', allowedTypes=['code'],
            updates="never", allowedUpdates=["never"],
            hint="Do you want to save the response as correct/incorrect? Might be helpful to add a corrAns column in the trialList")
        #todo: add response time clock to keyboard!!
#        self.params['storeResponseTimeFrom']=Param(storeCorrect, 
#            valType='str', allowedTypes=['str'],allowedVals=['']
#            updates="never", allowedUpdates=["never"],
#            hint="Save the response time, and as what?")
    def writeInitCode(self,buff):
        pass#no need to initialise keyboards?
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the times test
        #check for keypress
        buff.writeIndented("%(name)s = event.getKeys(keyList=%(allowedKeys)s)\n" %(self.params))
        #check if correct (if necess)
        if self.params['storeCorrect'].val:
            buff.writeIndented("if (%(name)s%(correctIf)s): corr=1\n" %(self.params))
            buff.writeIndented("else: corr=0\n")
        #does the response end the trial?
        if self.params['forceEndTrial'].val:
            buff.writeIndented("#if key was pressed end routine\n" %(self.params))
            buff.writeIndented("if len(%(name)s)>0: break\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)        
    def writeRoutineEndCode(self, buff):
        if self.params['storeWhat'].val=='first key':
            buff.writeIndented("%s.addData('%s',%s)" %(self.parentName, self.params['name'], self.params['name']))
        if self.params['storeCorrect'].val=='True':
            buff.writeIndented("%s.addData('corr',%s)" %(self.parentName, self.params['name']))