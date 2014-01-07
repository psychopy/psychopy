# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from keyboard import *
from os import path
from psychopy.app.builder.experiment import CodeGenerationException, _valid_var_re

__author__ = 'Jon Peirce'

thisFolder = path.abspath(path.dirname(__file__))  # abs path to the folder containing this path
iconFile = path.join(thisFolder, 'cedrusBox.png')
tooltip = 'Cedrus Button Box: Cedrus response boxes, using the pyxid library provided by Cedrus'

class cedrusButtonBoxComponent(KeyboardComponent):
    """An event class for checking an Cedrus RBxxx button boxes using XID library

    This is based on keyboard component, several important differences:
    - no special response class analogous to event.BuilderKeyResponse()
    - enabled responses (active keys) are handled by the hardware device

    More than one component in a routine will produce conflicts between
    components over which active keys (for responses and lights).
    """
    categories = ['Responses']  # which section(s) in the components panel
    def __init__(self, exp, parentName, name='buttonBox',
                store='first key',
                useTimer=True, deviceNumber=0, allowedKeys="",
                getReleaseTime=False,  #not yet supported
                forceEndRoutine=True, storeCorrect=False, correctAns="",
                discardPrev=True,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim='',):
        self.type = 'cedrusButtonBox'
        self.url = "http://www.psychopy.org/builder/components/cedrusButtonBox.html"
        self.exp = exp  # so we can access the experiment
        self.exp.requirePsychopyLibs(['hardware'])
        self.parentName = parentName

        self.params = {}
        self.order = ['forceEndRoutine', 'allowedKeys', #NB name and timing params always come 1st
            'store', 'storeCorrect', 'correctAns']
        self.params['name'] = Param(name, valType='code', hint="A name for this ButtonBox object (e.g. bbox)",
            label="Name")
        self.params['allowedKeys'] = Param(allowedKeys, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="Keys to be read (blank for any) or key numbers separated by commas",
            label="Allowed keys")
        self.params['startType'] = Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?",
            label="")
        self.params['stopType'] = Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal'] = Param(startVal, valType='code', allowedTypes=[],
            hint="When to start checking keys")
        self.params['stopVal'] = Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When to stop checking keys")
        self.params['startEstim'] = Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim'] = Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        self.params['discard previous'] = Param(discardPrev, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to discard all key presses occuring before the onset of this component?",
            label="Discard previous")
        self.params['store'] = Param(store, valType='str', allowedTypes=[],
            allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant', allowedUpdates=[],
            hint="Choose which (if any) responses to store at end of a trial",
            label="Store")
        self.params['forceEndRoutine'] = Param(forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should a key press force the end of the routine (e.g end the trial)?",
            label="Force end of Routine")
        self.params['storeCorrect'] = Param(storeCorrect, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect?",
            label="Store correct")
        self.params['correctAns'] = Param(correctAns, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="What is the 'correct' response? NB, keys are labelled 0 to 6 on a 7-button box",
            label="Correct answer")
        self.params['deviceNumber'] = Param(deviceNumber, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Device number, if you have multiple devices which one do you want (0, 1, 2...)",
            label="Device number", categ='Advanced')
        #self.params['getReleaseTime'] = Param(getReleaseTime, valType='bool', allowedVals=[True, False],
        #    updates='constant', allowedUpdates=[],
        #    hint="Wait for the key to be released and store the time that it was held down",
        #    label="Get release time")
        self.params['useBoxTimer'] = Param(getReleaseTime, valType='bool', allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint="According to Cedrus the response box timer has a drift - use with caution!",
            label="Use box timer", categ='Advanced')

    def writeStartCode(self, buff):
        """code for start of the script (import statements)
        """
        buff.writeIndented("import pyxid #to use the Cedrus response box\n")
        if self.params['useBoxTimer'].val:
            buff.writeIndented("pyxid.use_response_pad_timer = True\n")

    def writeInitCode(self, buff):
        buff.writeIndented("for n in range(10): #Cedrus connection doesn't always work first time!\n")
        buff.writeIndented("    try:\n")
        buff.writeIndented("        devices = pyxid.get_xid_devices()\n")
        buff.writeIndented("        core.wait(0.1)\n")
        buff.writeIndented("        %(name)s = devices[%(deviceNumber)s]\n" %self.params)
        buff.writeIndented("        break #once we found the device we can break the loop\n")
        buff.writeIndented("    except:\n")
        buff.writeIndented("        pass\n")
        buff.writeIndented("%(name)s.status = NOT_STARTED\n" %self.params)
        buff.writeIndented("%(name)s.clock = core.Clock()\n" %self.params)

    def writeRoutineStartCode(self,buff):
        if self.params['store'].val != 'nothing' or self.params['storeCorrect'].val:
            buff.writeIndentedLines("%(name)s.keys = []  # to store response values\n" %self.params +
                  "%(name)s.rt = []\n" % self.params)

    def writeFrameCode(self,buff):
        """Write the code that will be called every frame.
        """
        #some shortcuts
        store = self.params['store'].val
        storeCorr = self.params['storeCorrect'].val
        forceEnd = self.params['forceEndRoutine'].val
        useBoxTimer = self.params['useBoxTimer'].val

        #check whether we need to test for allowed keys (or just take all)
        allowedKeys = self.params['allowedKeys'].val.strip()
        allowedKeysIsVar = _valid_var_re.match(str(allowedKeys)) and not allowedKeys == 'None'
        if allowedKeysIsVar: #only insert this code if we think allowed keys is a variable
            # if it looks like a variable, check that the variable is suitable to eval at run-time
            buff.writeIndented("# AllowedKeys looks like a variable named `%s`\n" % allowedKeys)
            buff.writeIndented("if not '%s' in locals():\n" % allowedKeys)
            buff.writeIndented("    logging.error('AllowedKeys variable `%s` is not defined.')\n" % allowedKeys)
            buff.writeIndented("    core.quit()\n")
            buff.writeIndented("if not type(%s) in [list, tuple, np.ndarray]:\n" % allowedKeys)
            buff.writeIndented("    if not isinstance(%s, basestring):\n" % allowedKeys)
            buff.writeIndented("        logging.error('AllowedKeys variable `%s` is not string- or list-like.')\n" % allowedKeys)
            buff.writeIndented("        core.quit()\n")
            buff.writeIndented("    elif not ',' in %s: %s = (%s,)\n" % (allowedKeys, allowedKeys, allowedKeys))
            buff.writeIndented("    else:  %s = eval(%s)\n" % (allowedKeys, allowedKeys))
            keyListStr = "keyList=list(%s)" % allowedKeys  # eval() at run time
        #now create the string that will loop-continue if
        if allowedKeys in [None, "none", "None", "", "[]", "()"]:
            keyCheckStr=""
        elif not allowedKeysIsVar:
            try:
                keyList = eval(allowedKeys)
            except:
                raise CodeGenerationException(self.params["name"], "Allowed keys list is invalid.")
            if type(keyList)==tuple: #this means the user typed "left","right" not ["left","right"]
                keyList=list(keyList)
            elif isinstance(keyList, basestring): #a single string/key
                keyList=[keyList]
            keyCheckStr= "%s" %(repr(keyList))

        # if just now starting on this frame:
        buff.writeIndented("# *%(name)s* updates\n" % self.params)
        #write start code
        self.writeStartTestCode(buff)  #writes an if statement to determine whether to start
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)
        buff.writeIndented("%(name)s.clock.reset()  # now t=0\n" % self.params)
        if self.params['discard previous'].val:
            buff.writeIndented("# clear %(name)s responses (in a loop - the Cedrus own function doesn't work well)\n" % self.params)
            buff.writeIndented("%(name)s.poll_for_response()\n" % self.params)
            buff.writeIndented("while len(%(name)s.response_queue):\n" % self.params)
            buff.writeIndented("    %(name)s.clear_response_queue()\n" % self.params)
            buff.writeIndented("    %(name)s.poll_for_response() #often there are more resps waiting!\n" % self.params)
        if useBoxTimer:
            buff.writeIndented("%(name)s.reset_rt_timer() #set the response time clock to 0\n" % self.params)

        buff.setIndentLevel(-1, relative=True)  # to get out of the if statement
        #test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)  # writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.status = STOPPED\n" % self.params)
            buff.setIndentLevel(-1, True)

        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)  #to get out of the if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        buff.writeIndented("theseKeys=[]\n" % self.params)
        buff.writeIndented("theseRTs=[]\n" % self.params)
        buff.writeIndented("# check for key presses\n" % self.params)
        buff.writeIndented("%(name)s.poll_for_response()\n" %self.params)
        buff.writeIndented("while len(%(name)s.response_queue):\n" %self.params)
        buff.writeIndented("    evt = %(name)s.get_next_response()\n" %self.params)
        if len(keyCheckStr):
            buff.writeIndented("    if evt['key'] not in %s:\n" %keyList)
            buff.writeIndented("        continue #we don't care about this key\n")
        buff.writeIndented("    if evt['pressed']: #could be extended to examine releases too?\n")
        buff.writeIndented("      theseKeys.append(evt['key'])\n")
        if useBoxTimer:
            buff.writeIndented("      theseRTs.append(evt['time']/1000.0) #NB psychopy times are in s not ms\n")
        else:
            buff.writeIndented("      theseRTs.append(%(name)s.clock.getTime())\n" %self.params)
        buff.writeIndented("    %(name)s.poll_for_response()\n" %self.params)
        buff.writeIndented("%(name)s.clear_response_queue() # make sure we don't process these evts again\n" % self.params)


        #how do we store it?
        if store!='nothing' or forceEnd:
            #we are going to store something
            buff.writeIndented("if len(theseKeys) > 0:  # at least one key was pressed\n")
            buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1

        if store=='first key':#then see if a key has already been pressed
            buff.writeIndented("if %(name)s.keys == []:  # then this was the first keypress\n" %(self.params))
            buff.setIndentLevel(1,True); dedentAtEnd+=1 #indent by 1
            buff.writeIndented("%(name)s.keys = theseKeys[0]  # just the first key pressed\n" %(self.params))
            buff.writeIndented("%(name)s.rt = theseRTs[0]\n" %(self.params))
        elif store=='last key':
            buff.writeIndented("%(name)s.keys = theseKeys[-1]  # just the last key pressed\n" %(self.params))
            buff.writeIndented("%(name)s.rt = theseRTs[-1]\n" %(self.params))
        elif store=='all keys':
            buff.writeIndented("%(name)s.keys.extend(theseKeys)  # storing all keys\n" %(self.params))
            buff.writeIndented("%(name)s.rt.extend(theseRTs)\n" %(self.params))
        else:
            print store, type(store), str(store)
        if storeCorr:
            buff.writeIndented("# was this 'correct'?\n" %self.params)
            buff.writeIndented("if (%(name)s.keys == str(%(correctAns)s)) or (%(name)s.keys == %(correctAns)s):\n" %(self.params))
            buff.writeIndented("    %(name)s.corr = 1\n" %(self.params))
            buff.writeIndented("else:\n")
            buff.writeIndented("    %(name)s.corr = 0\n" %(self.params))

        if forceEnd==True:
            buff.writeIndented("# a response ends the routine\n" %self.params)
            buff.writeIndented("continueRoutine = False\n")

        buff.setIndentLevel(-(dedentAtEnd), relative=True)

#    def writeRoutineEndCode(self, buff):
#        # some shortcuts
#        name = self.params['name']
#        store = self.params['store'].val
#        storeCorrect = self.params['storeCorrect'].val
#        if len(self.exp.flow._loopList):
#            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
#        else:
#            currLoop = None
#        if store == 'nothing' or not currLoop:  # need a loop to store any data!
#            return
#        loopname = currLoop.params['name']

#        # write the actual code
#        buff.writeIndented( "# store cedrus response box data for %s (%s)\n" % (name, currLoop.type))
#        buff.writeIndented("if len(%(name)s.btns) == 0:  # no responses\n" % self.params)
#        buff.writeIndented("    %(name)s.btns = None\n" % self.params)
#            buff.writeIndented("    if str(%(correctAns)s).lower()=='none':\n" % self.params)
#            buff.writeIndented("        %(name)s.corr = 1 # correctly witheld response\n" % self.params)
#            buff.writeIndented("    else:\n" % self.params)
#            buff.writeIndented("        %(name)s.corr = 0  # failed to withold a response\n"  % self.params)
#        if store == 'first key': #'last key', 'last key', 'first key', 'all keys'
#            buff.writeIndented("else:\n" % self.params)
#            buff.writeIndented("    %(name)s.btns = %(name)s.btns[0] #just keep first key\n" % self.params)
#            buff.writeIndented("    %(name)s.rt = %(name)s.rt[0] #just keep first key\n" % self.params)
#        elif store == 'last key': #'last key', 'last key', 'first key', 'all keys'
#            buff.writeIndented("else:\n" % self.params)
#            buff.writeIndented("    %(name)s.btns = %(name)s.btns[-1] #just keep last key\n" % self.params)
#            buff.writeIndented("    %(name)s.rt = %(name)s.rt[-1] #just keep first key\n" % self.params)
#        if self.params['storeCorrect'].val:  #check for correct NON-repsonse
#            buff.writeIndented("    # was this 'correct'?\n")
#            buff.writeIndented("    if %(name)s.btns==%(correctAns)s:\n" % self.params)
#            buff.writeIndented("        %(name)s.corr = 1\n" % self.params)
#            buff.writeIndented("    else:\n" % self.params)
#            buff.writeIndented("        %(name)s.corr = 0  # responded incorrectly\n"  % self.params)

#        if currLoop.type == 'StairHandler':
#            # StairHandler only needs correct-ness
#            if self.params['storeCorrect'].val:
#                buff.writeIndented("%s.addData(%s.corr)\n" % (loopname, name))
#                buff.writeIndented("%s.addOtherData('%s.rt', %s.rt)\n" %(loopname, name, name))
#        else:
#            # TrialHandler gets key and RT info:
#            buff.writeIndented("%s.addData('%s.btns', %s.btns)\n" % (loopname, name, name))
#            if self.params['storeCorrect'].val:
#                buff.writeIndented("%s.addData('%s.corr', %s.corr)\n" % (loopname, name, name))
#            buff.writeIndented("if %(name)s.btns != None:  # add RTs if there are responses\n" % self.params)
#            buff.writeIndented("    %s.addData('%s.rt', %s.rt)\n" % (loopname, name, name))
