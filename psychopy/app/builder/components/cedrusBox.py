# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from .keyboard import KeyboardComponent, Param
from ..experiment import CodeGenerationException, _valid_var_re

__author__ = 'Jon Peirce'

# abs path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'cedrusBox.png')
tooltip = _translate('Cedrus Button Box: Cedrus response boxes, using the '
                     'pyxid library provided by Cedrus')

# only use _localized values for label values, nothing functional:
_localized = {'deviceNumber': _translate('Device number'),
              'useBoxTimer': _translate("Use box timer")}


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
                 getReleaseTime=False,  # not yet supported
                 forceEndRoutine=True, storeCorrect=False, correctAns="",
                 discardPrev=True,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',):
        super(cedrusButtonBoxComponent, self).__init__(
            exp, parentName, name=name,
            allowedKeys=allowedKeys, store=store, discardPrev=discardPrev,
            forceEndRoutine=forceEndRoutine, storeCorrect=storeCorrect,
            correctAns=correctAns, startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'cedrusButtonBox'
        self.url = "http://www.psychopy.org/builder/components/cedrusButtonBox.html"
        self.exp.requirePsychopyLibs(['hardware'])

        self.params['correctAns'].hint = _translate(
            "What is the 'correct' response? NB, buttons are labelled 0 to "
            "6 on a 7-button box. Enter 'None' (no quotes) if withholding "
            "a response is correct. Might be helpful to add a correctAns "
            "column and use $correctAns to compare to the key press.")

        self.params['correctAns'].valType = 'code'

        self.params['allowedKeys'].hint = _translate(
            'Keys to be read (blank for any) or key numbers separated by '
            'commas')

        msg = _translate('Device number, if you have multiple devices which'
                         ' one do you want (0, 1, 2...)')
        self.params['deviceNumber'] = Param(
            deviceNumber, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['deviceNumber'], categ='Advanced')

        # self.params['getReleaseTime'] = Param(getReleaseTime,
        #    valType='bool', allowedVals=[True, False],
        #    updates='constant', allowedUpdates=[],
        #    hint="Wait for the key to be released and store the time
        #       that it was held down",
        #    label="Get release time")

        msg = _translate('According to Cedrus the response box timer has '
                         'a drift - use with caution!')
        self.params['useBoxTimer'] = Param(
            getReleaseTime, valType='bool', allowedVals=[True, False],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['useBoxTimer'], categ='Advanced')

    def writeStartCode(self, buff):
        """code for start of the script (import statements)
        """
        buff.writeIndented("import pyxid  # to use the Cedrus response box\n")
        if self.params['useBoxTimer'].val:
            buff.writeIndented("pyxid.use_response_pad_timer = True\n")

    def writeInitCode(self, buff):
        code = ("for n in range(10):  # Cedrus connection doesn't always work first time!\n"
                "    try:\n"
                "        devices = pyxid.get_xid_devices()\n"
                "        core.wait(0.1)\n"
                "        %(name)s = devices[%(deviceNumber)s]\n"
                "        break  # once we found the device we can break the loop\n"
                "    except Exception:\n"
                "        pass\n"
                "%(name)s.status = NOT_STARTED\n"
                "%(name)s.clock = core.Clock()\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        if (self.params['store'].val != 'nothing' or
                self.params['storeCorrect'].val):
            code = ("%(name)s.keys = []  # to store response values\n"
                    "%(name)s.rt = []\n")
            buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame.
        """
        # some shortcuts
        store = self.params['store'].val
        storeCorr = self.params['storeCorrect'].val
        forceEnd = self.params['forceEndRoutine'].val
        useBoxTimer = self.params['useBoxTimer'].val

        # check whether we need to test for allowed keys (or just take all)
        allowedKeys = self.params['allowedKeys'].val.strip()
        allowedKeysIsVar = _valid_var_re.match(
            str(allowedKeys)) and not allowedKeys == 'None'
        if allowedKeysIsVar:  # only insert this code if we think allowed keys is a variable
            # if it looks like a variable, check that the variable is suitable
            # to eval at run-time
            code = ("# AllowedKeys looks like a variable named `%s`\n" % allowedKeys +
                    "if not '%s' in locals():\n" % allowedKeys +
                    "    logging.error('AllowedKeys variable `%s` is not defined.')\n" % allowedKeys +
                    "    core.quit()\n" +
                    "if not type(%s) in [list, tuple, np.ndarray]:\n" % allowedKeys +
                    "    if not isinstance(%s, basestring):\n" % allowedKeys +
                    "        logging.error('AllowedKeys variable `%s` is not string- or list-like.')\n" % allowedKeys +
                    "        core.quit()\n" +
                    "    elif not ',' in %s: %s = (%s,)\n" % (allowedKeys, allowedKeys, allowedKeys) +
                    "    else:  %s = eval(%s)\n" % (allowedKeys, allowedKeys))
            buff.writeIndentedLines(code)

            keyListStr = "keyList=list(%s)" % allowedKeys  # eval() at run time

        # now create the string that will loop-continue if
        if allowedKeys in [None, "none", "None", "", "[]", "()"]:
            keyCheckStr = ""
        elif not allowedKeysIsVar:
            try:
                keyList = eval(allowedKeys)
            except Exception:
                raise CodeGenerationException(
                    self.params["name"], "Allowed keys list is invalid.")
            # this means the user typed "left","right" not ["left","right"]
            if type(keyList) == tuple:
                keyList = list(keyList)
            elif isinstance(keyList, basestring):  # a single string/key
                keyList = [keyList]
            keyCheckStr = "%s" % (repr(keyList))

        # if just now starting on this frame:
        buff.writeIndented("# *%(name)s* updates\n" % self.params)
        # write start code
        # writes an if statement to determine whether to start
        self.writeStartTestCode(buff)
        code = ("%(name)s.status = STARTED\n"
                "%(name)s.clock.reset()  # now t=0\n")
        buff.writeIndentedLines(code % self.params)

        if self.params['discard previous'].val:
            code = ("# clear %(name)s responses (in a loop - the Cedrus own function doesn't work well)\n"
                    "%(name)s.poll_for_response()\n"
                    "while len(%(name)s.response_queue):\n"
                    "    %(name)s.clear_response_queue()\n"
                    "    %(name)s.poll_for_response() #often there are more resps waiting!\n")
            buff.writeIndentedLines(code % self.params)

        if useBoxTimer:
            code = "%(name)s.reset_rt_timer() #set the response time clock to 0\n"
            buff.writeIndented(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = STOPPED\n" % self.params)
            buff.setIndentLevel(-1, True)

        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of the if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        code = ("theseKeys=[]\n"
                "theseRTs=[]\n"
                "# check for key presses\n"
                "%(name)s.poll_for_response()\n"
                "while len(%(name)s.response_queue):\n"
                "    evt = %(name)s.get_next_response()\n")

        buff.writeIndentedLines(code % self.params)

        if len(keyCheckStr):
            code = ("    if evt['key'] not in %s:\n" % keyList +
                    "        continue  # we don't care about this key\n")
            buff.writeIndentedLines(code)

        code = ("    if evt['pressed']:  # could be extended to examine releases too?\n"
                "      theseKeys.append(evt['key'])\n")
        buff.writeIndentedLines(code)

        if useBoxTimer:
            code = "      theseRTs.append(evt['time']/1000.0) #NB psychopy times are in s not ms\n"
            buff.writeIndented(code)
        else:
            code = "      theseRTs.append(%(name)s.clock.getTime())\n"
            buff.writeIndented(code % self.params)

        code = ("    %(name)s.poll_for_response()\n"
                "%(name)s.clear_response_queue() # make sure we don't process these evts again\n")
        buff.writeIndentedLines(code % self.params)

        # how do we store it?
        if store != 'nothing' or forceEnd:
            # we are going to store something
            code = "if len(theseKeys) > 0:  # at least one key was pressed\n"
            buff.writeIndented(code)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

        if store == 'first key':  # then see if a key has already been pressed
            code = "if %(name)s.keys == []:  # then this was the first keypress\n"
            buff.writeIndented(code % self.params)

            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

            code = ("%(name)s.keys = theseKeys[0]  # just the first key pressed\n"
                    "%(name)s.rt = theseRTs[0]\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'last key':
            code = ("%(name)s.keys = theseKeys[-1]  # just the last key pressed\n"
                    "%(name)s.rt = theseRTs[-1]\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'all keys':
            code = ("%(name)s.keys.extend(theseKeys)  # storing all keys\n"
                    "%(name)s.rt.extend(theseRTs)\n")
            buff.writeIndentedLines(code % self.params)
        else:
            print(store, type(store), str(store))
        if storeCorr:
            code = ("# was this 'correct'?\n"
                    "if (%(name)s.keys == str(%(correctAns)s)) or (%(name)s.keys == %(correctAns)s):\n"
                    "    %(name)s.corr = 1\n"
                    "else:\n"
                    "    %(name)s.corr = 0\n")
            buff.writeIndentedLines(code % self.params)

        if forceEnd == True:
            code = ("# a response ends the routine\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code % self.params)

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
# buff.writeIndented("        %(name)s.corr = 0  # responded
# incorrectly\n"  % self.params)

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
