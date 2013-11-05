# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import CodeGenerationException, _valid_var_re

__author__ = 'Jon Peirce'

thisFolder = path.abspath(path.dirname(__file__))  # abs path to the folder containing this path
iconFile = path.join(thisFolder, 'cedrusBox.png')
tooltip = 'Cedrus Button Box: '

class cedrusButtonBoxComponent(BaseComponent):
    """An event class for checking an Cedrus RBxxx button boxes using XID library

    This is based on keyboard component, several important differences:
    - no special response class analogous to event.BuilderKeyResponse()
    - enabled responses (active buttons) are handled by the hardware device

    More than one component in a routine will produce conflicts between
    components over which active buttons (for responses and lights).
    """
    categories = ['Responses']  # which section(s) in the components panel
    def __init__(self, exp, parentName, name='buttonBox',
                store='first button',
                useTimer=False, deviceNumber=0, allowedKeys="",
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
        self.params['advancedParams']=['useBoxTimer', 'deviceNumber']
        self.order = ['forceEndRoutine', 'allowedKeys', #NB name and timing params always come 1st
            'store', 'storeCorrect', 'correctAns']
        self.params['name'] = Param(name, valType='code', hint="A name for this ButtonBox object (e.g. bbox)",
            label="Name")
        self.params['allowedKeys'] = Param(allowedKeys, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="Buttons to be read (blank for any) or button numbers separated by commas",
            label="Allowed buttons")
        self.params['startType'] = Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?",
            label="")
        self.params['stopType'] = Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal'] = Param(startVal, valType='code', allowedTypes=[],
            hint="When to start checking buttons")
        self.params['stopVal'] = Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When to stop checking buttons")
        self.params['startEstim'] = Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim'] = Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        self.params['discard previous'] = Param(discardPrev, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to discard all button presses occuring before the onset of this component?",
            label="Discard previous")
        self.params['store'] = Param(store, valType='str', allowedTypes=[],
            allowedVals=['last button', 'first button', 'all buttons', 'nothing'],
            updates='constant', allowedUpdates=[],
            hint="Choose which (if any) responses to store at end of a trial",
            label="Store")
        self.params['forceEndRoutine'] = Param(forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should a button press force the end of the routine (e.g end the trial)?",
            label="Force end of Routine")
        self.params['storeCorrect'] = Param(storeCorrect, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect?",
            label="Store correct")
        self.params['correctAns'] = Param(correctAns, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="What is the 'correct' response? This should be an integer for the button (or a variable containing an integer)",
            label="Correct answer")
        self.params['deviceNumber'] = Param(deviceNumber, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Device number, if you have multiple devices which one do you want (0, 1, 2...)",
            label="Device number")
        #self.params['getReleaseTime'] = Param(getReleaseTime, valType='bool', allowedVals=[True, False],
        #    updates='constant', allowedUpdates=[],
        #    hint="Wait for the button to be released and store the time that it was held down",
        #    label="Get release time")
        self.params['useBoxTimer'] = Param(getReleaseTime, valType='bool', allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint="According to Cedrus the response box timer has a drift - use with caution!",
            label="Use box timer")

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
        if not self.params['useBoxTimer'].val:
            #create a clock to store our responses
            buff.writeIndented("%(name)sClock = core.Clock()\n" %self.params)


    def writeRoutineStartCode(self,buff):
        if self.params['store'].val != 'nothing' or self.params['storeCorrect'].val:
            buff.writeIndentedLines("%(name)s.btns = []  # to store response values\n" %self.params +
                  "%(name)s.rts = []\n" % self.params)

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
        if self.params['discard previous'].val:
            buff.writeIndented("%(name)s.poll_for_response()\n" % self.params)
            buff.writeIndented("%(name)s.clear_response_queue()\n" % self.params)
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

        buff.writeIndented("theseButtonsPressed=[]\n" % self.params)
        buff.writeIndented("theseButtonsRTs=[]\n" % self.params)
        buff.writeIndented("# check for button presses\n" % self.params)
        buff.writeIndented("%(name)s.poll_for_response()\n" %self.params)
        buff.writeIndented("for evt in %(name)s.response_queue:\n" %self.params)
        if len(keyCheckStr):
            buff.writeIndented("    if evt['key'] not in %s:\n" %keyList)
            buff.writeIndented("        continue #we don't care about this key\n" %keyList)
        buff.writeIndented("    if evt['pressed']: #could be extended to examine releases too?\n")
        buff.writeIndented("      theseButtonsPressed.append(evt['key'])\n")
        if useBoxTimer:
            buff.writeIndented("      theseButtonsRTs.append(evt['time'])\n")
        else:
            buff.writeIndented("      theseButtonsRTs.append(%(name)sClock.getTime())\n" %self.params)
        buff.writeIndented("%(name)s.clear_response_queue() #and clear those responses so we don't process them again\n" % self.params)

        # store something?
        if store != 'nothing' or forceEnd:
            buff.writeIndented("if len(theseButtonsPressed):  # at least one button was pressed this frame\n" % self.params)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1

        if store == 'first button':
            buff.writeIndented("if %(name)s.btns == []:  # True if the first\n" % self.params)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1
            buff.writeIndented("%(name)s.btns = [theseButtonsPressed[0]]  # just the first button\n" % self.params)
            buff.writeIndented("%(name)s.rts = [theseButtonsRTs[0]]\n" %(self.params))
        elif store == 'last button':
            buff.writeIndented("%(name)s.btns = [theseButtonsPressed[-1]] # just the last button\n" % self.params)
            buff.writeIndented("%(name)s.rts = [theseButtonsRTs[-1]]\n" % self.params)
        elif store == 'all buttons':
            buff.writeIndented("%(name)s.btns.extend(theseButtonsPressed)  # all buttons\n" % self.params)
            buff.writeIndented("%(name)s.rts.extend(theseButtonsRTs)\n" % self.params)

        if storeCorr:
            buff.writeIndented("# was this 'correct'?\n")
            buff.writeIndented("if %(name)s.btns == [int(%(correctAns)s)]:\n" % self.params)
            buff.writeIndented("    %(name)s.corr = 1\n" % self.params)
            buff.writeIndentedLines("else:\n    %(name)s.corr=0\n" % self.params)
        if forceEnd:
            buff.writeIndented("# a response forces the end of the routine\n" % self.params)
            buff.writeIndented("continueRoutine = False\n" % self.params)
        buff.setIndentLevel(-(dedentAtEnd), relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        store = self.params['store'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = None
        if store == 'nothing' or not currLoop:  # need a loop to store any data!
            return
        loopname = currLoop.params['name']

        # write the actual code
        lines = ''
        lines += "# store cedrus response box data for %s (%s)\n" % (name, currLoop.type)
        lines += ("if len(%(name)s.btns) == 0:  # no responses\n" +
                  "    %(name)s.btns = None\n")
        if self.params['storeCorrect'].val:  #check for correct NON-repsonse
            lines += "    # was no response the correct answer?\n"
            lines += "    if str(%(correctAns)s).lower() == 'none':\n"
            lines += "        %(name)sCorr = 1  # correct non-response\n"
            lines += "    else:\n"
            lines += "        %(name)sCorr = 0  # failed to withold a response\n"
        buff.writeIndentedLines(lines % self.params)
        if currLoop.type == 'StairHandler':
            # StairHandler only needs correct-ness
            if self.params['storeCorrect'].val:
                buff.writeIndented("%s.addData(%sCorr)\n" % (loopname, name))
                buff.writeIndented("%s.addOtherData('%s.rt', %s.rt)\n" %(loopname, name, name))
        else:
            # TrialHandler gets button and RT info:
            buff.writeIndented("%s.addData('%s.btns', %s.btns)\n" % (loopname, name, name))
            if self.params['storeCorrect'].val:
                buff.writeIndented("%s.addData('%s.corr', %sCorr)\n" % (loopname, name, name))
            buff.writeIndented("if %(name)s.btns != None:  # add RTs if there are responses\n" % self.params)
            buff.writeIndented("    %s.addData('%s.rt', %s.rts)\n" % (loopname, name, name))
