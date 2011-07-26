# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'keyboard.png')

class KeyboardComponent(BaseComponent):
    """An event class for checking the keyboard at given timepoints"""
    def __init__(self, exp, parentName, name='key_resp', allowedKeys='["left","right"]',store='last key',
                forceEndTrial=True,storeCorrect=False,correctAns="", discardPrev=True,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        self.type='Keyboard'
        self.url="http://www.psychopy.org/builder/components/keyboard.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['gui'])
        self.parentName=parentName
        #params
        self.params={}
        self.order=['forceEndTrial','allowedKeys',#NB name and timing params always come 1st
            'store','storeCorrect','correctAns',
            ]
        self.params['name']=Param(name,  valType='code', hint="A name for this keyboard object (e.g. response)")
        self.params['allowedKeys']=Param(allowedKeys, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="ynq allows those 3 keys to be used. For keys with complex names use $['left','right']")
        self.params['startType']=Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?")
        self.params['stopType']=Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal']=Param(startVal, valType='code', allowedTypes=[],
            hint="When does the keyboard checking start?")
        self.params['stopVal']=Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When does the keyboard checking end?")
        self.params['startEstim']=Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim']=Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        self.params['discard previous']=Param(discardPrev, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to discard any keypresses occuring before the onset of this component?")
        self.params['store']=Param(store, valType='str', allowedTypes=[],allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant', allowedUpdates=[],
            hint="Choose which (if any) keys to store at end of trial")
        self.params['forceEndTrial']=Param(forceEndTrial, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should the keypress force the end of the routine (e.g end the trial)?")
        self.params['storeCorrect']=Param(storeCorrect, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect?")
        self.params['correctAns']=Param(correctAns, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="What is the 'correct' key? Might be helpful to add a correctAns column and use $thisTrial.correctAns")
    def writeRoutineStartCode(self,buff):
        buff.writeIndented("%(name)s.status=NOT_STARTED\n" %self.params)
        if self.params['store'].val=='nothing' \
            and self.params['storeCorrect'].val==False:
            #the user doesn't want to store anything so don't bother
            return
        buff.writeIndented("%(name)s = event.BuilderKeyResponse() #create an object of type KeyResponse\n" %self.params)

    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("#*%s* updates\n" %(self.params['name']))
        #some shortcuts
        store=self.params['store'].val
        storeCorr=self.params['storeCorrect'].val
        forceEnd=self.params['forceEndTrial'].val

        buff.writeIndented("\n")
        buff.writeIndented("#*%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.status=STARTED\n" %(self.params))
        buff.writeIndented("#keyboard checking is just starting\n")
        if store != 'nothing':
            buff.writeIndented("    %(name)s.clock.reset() # now t=0\n" % self.params)
        if self.params['discard previous'].val:
            buff.writeIndented("event.clearEvents()\n")
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.status=STOPPED\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement

        #if we've only just started then do a clearEvents()
        buff.writeIndented("if %(name)s.status==NOT_STARTED:\n" %self.params)
        buff.setIndentLevel(1, relative=True)#indent
        buff.writeIndented("%(name)s.status=STARTED\n" %self.params)
        buff.setIndentLevel(-1, relative=True)#dedent

        #do we need a list of keys?
        if self.params['allowedKeys'].val in [None,"none","None", "", "[]"]: keyListStr=""
        else: keyListStr= "keyList=%(allowedKeys)s" %(self.params)
        #check for keypresses
        buff.writeIndented("theseKeys = event.getKeys(%s)\n" %(keyListStr))

        #how do we store it?
        if store!='nothing' or storeRT or storeCorr or forceEnd:
            #we are going to store something
            buff.writeIndented("if len(theseKeys)>0:#at least one key was pressed\n")
            buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1

        if store=='first key':#then see if a key has already been pressed
            buff.writeIndented("if %(name)s.keys==[]:#then this was the first keypress\n" %(self.params))
            buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1
            buff.writeIndented("%(name)s.keys=theseKeys[0]#just the first key pressed\n" %(self.params))
            if storeRT: buff.writeIndented("%(name)s.rt = %(name)s.clock.getTime()\n" %(self.params))
        elif store=='last key':
            buff.writeIndented("%(name)s.keys=theseKeys[-1]#just the last key pressed\n" %(self.params))
            if storeRT: buff.writeIndented("%(name)s.rt = %(name)s.clock.getTime()\n" %(self.params))
        elif store=='all keys':
            buff.writeIndented("%(name)s.keys.extend(theseKeys)#storing all keys\n" %(self.params))
            buff.writeIndented("%(name)s.rt.append(%(name)s.clock.getTime())\n" %(self.params))

        if storeCorr:
            buff.writeIndented("#was this 'correct'?\n" %self.params)
            buff.writeIndented("if (%(name)s.keys==str(%(correctAns)s)): %(name)s.corr=1\n" %(self.params))
            buff.writeIndented("else: %(name)s.corr=0\n" %self.params)

        if forceEnd==True:
            buff.writeIndented("#abort routine on response\n" %self.params)
            buff.writeIndented("continueRoutine=False\n")

        buff.setIndentLevel(-(dedentAtEnd), relative=True)
    def writeRoutineEndCode(self,buff):
        #some shortcuts
        name = self.params['name']
        store=self.params['store'].val
        if len(self.exp.flow._loopList):
            currLoop=self.exp.flow._loopList[-1]#last (outer-most) loop
        else: currLoop=None

        #write the actual code
        if (store!='nothing') and currLoop:#need a loop to do the storing of data!
            buff.writeIndented("#check responses\n" %self.params)
            buff.writeIndented("if len(%(name)s.keys)==0: #No response was made\n"%self.params)
            buff.writeIndented("   %(name)s.keys=None\n" %(self.params))
            if self.params['storeCorrect'].val:#check for correct NON-repsonse
                buff.writeIndented("   #was no response the correct answer?!\n" %(self.params))
                buff.writeIndented("   if str(%(correctAns)s).lower()=='none':%(name)s.corr=1 #correct non-response\n" %(self.params))
                buff.writeIndented("   else: %(name)s.corr=0 #failed to respond (incorrectly)\n" %(self.params))
            buff.writeIndented("#store data for %s (%s)\n" %(currLoop.params['name'], currLoop.type))
            if currLoop.type=='StairHandler':
                #data belongs to a StairHandler
                if self.params['storeCorrect'].val==True:
                    buff.writeIndented("%s.addData(%s.corr)\n" %(currLoop.params['name'], name))
            else:
                #always add keys
                buff.writeIndented("%s.addData('%s.keys',%s.keys)\n" \
                   %(currLoop.params['name'],name,name))
                if self.params['storeCorrect'].val==True:
                    buff.writeIndented("%s.addData('%s.corr',%s.corr)\n" \
                                       %(currLoop.params['name'], name, name))
                #only add an RT if we had a response
                buff.writeIndented("if %(name)s.keys != None:#we had a response\n" %(self.params))
                buff.writeIndented("    %s.addData('%s.rt',%s.rt)\n" \
                                   %(currLoop.params['name'], name, name))

