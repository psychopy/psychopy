#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path

from psychopy.experiment.components import Param, _translate
from psychopy.experiment.components.keyboard import KeyboardComponent
from psychopy.experiment import CodeGenerationException, valid_var_re
from psychopy.localization import _localized as __localized
_localized = __localized.copy()
__author__ = 'Jon Peirce'

# only use _localized values for label values, nothing functional:
_localized.update({'deviceNumber': _translate('Device number'),
                   'useBoxTimer': _translate("Use box timer")})


class cedrusButtonBoxComponent(KeyboardComponent):
    """An event class for checking an Cedrus RBxxx button boxes
    using XID library

    This is based on keyboard component, several important differences:
    - no special response class analogous to event.BuilderKeyResponse()
    - enabled responses (active keys) are handled by the hardware device

    More than one component in a routine will produce conflicts between
    components over which active keys (for responses and lights).
    """
    categories = ['Responses']  # which section(s) in the components panel
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'cedrusBox.png'
    tooltip = _translate('Cedrus Button Box: Cedrus response boxes, using the '
                         'pyxid2 library provided by Cedrus')

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
        self.url = "https://www.psychopy.org/builder/components/cedrusButtonBox.html"
        self.order += ['forceEndRoutine',  # Basic tab
                       'allowedKeys', 'store', 'storeCorrect', 'correctAns'  # Data tab
                       ]

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
            deviceNumber, valType='int', inputType="spin", allowedTypes=[], categ='Hardware',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['deviceNumber'])

        # self.params['getReleaseTime'] = Param(getReleaseTime,
        #    valType='bool', allowedVals=[True, False],
        #    updates='constant', allowedUpdates=[],
        #    hint="Wait for the key to be released and store the time
        #       that it was held down",
        #    label="Get release time")

        msg = _translate('According to Cedrus the response box timer has '
                         'a drift - use with caution!')
        self.params['useBoxTimer'] = Param(
            getReleaseTime, valType='bool', inputType="bool", allowedVals=[True, False], categ='Hardware',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['useBoxTimer'])

    def writeRunOnceInitCode(self, buff):
        code = ("try:  # to use the Cedrus response box\n"
                "   import pyxid2 as pyxid\n"
                "except ImportError:\n"
                "   import pyxid\n"
                "cedrusBox_%(deviceNumber)s = None\n"
                "for n in range(10):  # doesn't always work first time!\n"
                "    try:\n"
                "        devices = pyxid.get_xid_devices()\n"
                "        core.wait(0.1)\n"
                "        cedrusBox_%(deviceNumber)s = devices[%(deviceNumber)s]\n"
                "        cedrusBox_%(deviceNumber)s.clock = core.Clock()\n"
                "        break  # found the device so can break the loop\n"
                "    except Exception:\n"
                "        pass\n"
                "if not cedrusBox_%(deviceNumber)s:\n"
                "    logging.error('could not find a Cedrus device.')\n"
                "    core.quit()\n")
        buff.writeOnceIndentedLines(code % self.params)

    def writeInitCode(self, buff):
        code = ("%(name)s = cedrusBox_%(deviceNumber)s\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        if (self.params['store'].val != 'nothing' or
                self.params['storeCorrect'].val):
            code = ("%(name)s.keys = []  # to store response values\n"
                    "%(name)s.rt = []\n"
                    "%(name)s.status = None\n")
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
        allowedKeysIsVar = valid_var_re.match(
            str(allowedKeys)) and not allowedKeys == 'None'
        if allowedKeysIsVar:
            # only insert this code if we think allowed keys is a variable.
            # check at run-time that the var is suitable to eval
            stringType = 'str'
            code = ("# AllowedKeys looks like a variable named `{0}`\n"
                    "if not '{0}' in locals():\n"
                    "    logging.error('AllowedKeys variable `{0}` "
                    "is not defined.')\n"
                    "    core.quit()\n" +
                    "if not type({0}) in [list, tuple, np.ndarray]:\n"
                    "    if not isinstance({0}, str):\n"
                    "        logging.error('AllowedKeys variable `{0}`"
                    " is not string- or list-like.')\n"
                    "        core.quit()\n" +
                    "    elif not ',' in {0}: {0} = ({0},)\n"
                    "    else:  {0} = eval({0})\n").format(allowedKeys, stringType)
            buff.writeIndentedLines(code)

            keyCheckStr = "keyList=list(%s)" % allowedKeys  # eval() @ run time
            keyList = allowedKeys

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
            elif isinstance(keyList, str):  # a single string/key
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
            code = ("# clear %(name)s responses (in a loop - the Cedrus "
                    "own function doesn't work well)\n"
                    "%(name)s.poll_for_response()\n"
                    "while len(%(name)s.response_queue):\n"
                    "    %(name)s.clear_response_queue()\n"
                    "    %(name)s.poll_for_response() #often there are "
                    "more resps waiting!\n")
            buff.writeIndentedLines(code % self.params)

        if useBoxTimer:
            code = "%(name)s.reset_rt_timer()\n"
            buff.writeIndented(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)
            buff.setIndentLevel(-2, True)

        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
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

        code = ("    if evt['pressed']:\n"
                "      theseKeys.append(evt['key'])\n")
        buff.writeIndentedLines(code)

        if useBoxTimer:
            code = "      theseRTs.append(evt['time']/1000.0)\n"
            buff.writeIndented(code)
        else:
            code = "      theseRTs.append(%(name)s.clock.getTime())\n"
            buff.writeIndented(code % self.params)

        code = ("    %(name)s.poll_for_response()\n"
                "%(name)s.clear_response_queue()  # don't process again\n")
        buff.writeIndentedLines(code % self.params)

        # how do we store it?
        if store != 'nothing' or forceEnd:
            # we are going to store something
            code = "if len(theseKeys) > 0:  # at least one key was pressed\n"
            buff.writeIndented(code)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

        if store == 'first key':  # then see if a key has already been pressed
            code = "if %(name)s.keys == []:  # then this is first keypress\n"
            buff.writeIndented(code % self.params)

            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

            code = ("%(name)s.keys = theseKeys[0]  # the first key pressed\n"
                    "%(name)s.rt = theseRTs[0]\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'last key':
            code = ("%(name)s.keys = theseKeys[-1]  # the last key pressed\n"
                    "%(name)s.rt = theseRTs[-1]\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'all keys':
            code = ("%(name)s.keys.extend(theseKeys)  # storing all keys\n"
                    "%(name)s.rt.extend(theseRTs)\n")
            buff.writeIndentedLines(code % self.params)
        else:
            print((store, type(store), str(store)))
        if storeCorr:
            code = ("# was this 'correct'?\n"
                    "if (%(name)s.keys == str(%(correctAns)s)) or "
                    "(%(name)s.keys == %(correctAns)s):\n"
                    "    %(name)s.corr = 1\n"
                    "else:\n"
                    "    %(name)s.corr = 0\n")
            buff.writeIndentedLines(code % self.params)

        if forceEnd is True:
            code = ("# a response ends the routine\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code)
        buff.setIndentLevel(-(dedentAtEnd), relative=True)

    # this was commented-out (removed Feb 2016, available in history):
    # def writeRoutineEndCode(self, buff):
