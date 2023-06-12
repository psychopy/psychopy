#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path

from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.experiment import CodeGenerationException, valid_var_re
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# only use _localized values for label values, nothing functional:
_localized.update({'allowedKeys': _translate('Allowed buttons'),
                   'store': _translate('Store'),
                   'forceEndRoutine': _translate('Force end of Routine'),
                   'storeCorrect': _translate('Store correct'),
                   'correctAns': _translate('Correct answer'),
                   'deviceNumber': _translate('Device number'),
                   'syncScreenRefresh': _translate('sync RT with screen')})


class JoyButtonsComponent(BaseComponent):
    """An event class for checking the joyButtons at given timepoints"""
    # an attribute of the class, determines the section in components panel
    categories = ['Responses']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'joyButtons.png'
    tooltip = _translate('JoyButtons: check and record joystick/gamepad button presses')

    def __init__(self, exp, parentName, name='button_resp',
                 allowedKeys="0,1,2,3,4",
                 store='last key', forceEndRoutine=True, storeCorrect=False,
                 correctAns="",
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 deviceNumber='0',
                 syncScreenRefresh=True):
        super(JoyButtonsComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'JoyButtons'
        self.url = "https://www.psychopy.org/builder/components/joyButtons.html"
        self.exp.requirePsychopyLibs(['gui'])

        self.order += ['forceEndRoutine',  # Basic tab
                       'allowedKeys', 'store', 'storeCorrect', 'correctAns',  # Data tab
                       'deviceNumber',  # Hardware tab
                       ]

        msg = _translate(
            "A comma-separated list of button numbers, such as "
            "0,1,2,3,4")
        self.params['allowedKeys'] = Param(
            allowedKeys, valType='list', inputType="single", allowedTypes=[], categ='Data',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=(msg),
            label=_translate("Allowed buttons"))

        msg = _translate("Choose which (if any) responses to store at the "
                         "end of a trial")
        self.params['store'] = Param(
            store, valType='str', inputType="choice", allowedTypes=[], categ='Data',
            allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant', direct=False,
            hint=msg,
            label=_translate("Store"))

        msg = _translate("Should a response force the end of the Routine "
                         "(e.g end the trial)?")
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=msg,
            label=_translate("Force end of Routine"))

        msg = _translate("Do you want to save the response as "
                         "correct/incorrect?")
        self.params['storeCorrect'] = Param(
            storeCorrect, valType='bool', inputType="bool", allowedTypes=[], categ='Data',
            updates='constant',
            hint=msg,
            label=_translate("Store correct"))

        self.depends += [  # allows params to turn each other off/on
            {"dependsOn": "storeCorrect",  # must be param name
             "condition": "== True",  # val to check for
             "param": "correctAns",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        ]

        msg = _translate(
            "What is the 'correct' key? Might be helpful to add a "
            "correctAns column and use $correctAns to compare to the key "
            "press.")
        self.params['correctAns'] = Param(
            correctAns, valType='list', inputType="single", allowedTypes=[], categ='Data',
            updates='constant',
            hint=msg,
            label=_translate("Correct answer"))

        msg = _translate(
            "A reaction time to a visual stimulus should be based on when "
            "the screen flipped")
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType='bool', inputType="bool", categ='Data',
            updates='constant',
            hint=msg,
            label=_translate("Sync RT with screen"))

        msg = _translate(
            "Device number, if you have multiple devices which"
            " one do you want (0, 1, 2...)")
        self.params['deviceNumber'] = Param(
            deviceNumber, valType='int', inputType="int", allowedTypes=[], categ='Hardware',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Device number"))

    def writeStartCode(self, buff):
        code = ("from psychopy.hardware import joystick as joysticklib  "
                "# joystick/gamepad accsss\n"
                "from psychopy.experiment.components.joyButtons import "
                "virtualJoyButtons as virtualjoybuttonslib\n")
        buff.writeIndentedLines(code % self.params)

    def writeInitCode(self, buff):
        code = ("%(name)s = type('', (), {})() "
                "# Create an object to use as a name space\n"
                "%(name)s.device = None\n"
                "%(name)s.device_number = %(deviceNumber)s\n"
                "\n"
                "try:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("numJoysticks = joysticklib.getNumJoysticks()\n"
                "if numJoysticks > 0:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("%(name)s.device = joysticklib.Joystick(%(deviceNumber)s)\n")
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        buff.setIndentLevel(+1, relative=True)
        code = ("try:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("joystickCache\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = ("except NameError:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("joystickCache={}\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = ("if not %(deviceNumber)s in joystickCache:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("joystickCache[%(deviceNumber)s] = joysticklib.Joystick(%(deviceNumber)s)\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = ("%(name)s.device = joystickCache[%(deviceNumber)s]\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = ("else:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("%(name)s.device = virtualjoybuttonslib.VirtualJoyButtons(%(deviceNumber)s)\n"
                "logging.warning(\"joystick_{}: "
                "Using keyboard emulation 'ctrl' + 'Alt' + digit.\".format(%(name)s.device_number))\n")
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        buff.setIndentLevel(-1, relative=True)

        code = ("except Exception:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("pass\n\n")
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        code = ("if not %(name)s.device:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("logging.error('No joystick/gamepad device found.')\n"
                "core.quit()\n")
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        code = ("\n"
                "%(name)s.status = None\n"
                "%(name)s.clock = core.Clock()\n"
                "%(name)s.numButtons = %(name)s.device.getNumButtons()\n")
        buff.writeIndentedLines(code % self.params)
        buff.writeIndented("\n")

    def writeRoutineStartCode(self, buff):
        code = ("{name}.oldButtonState = {name}.device.getAllButtons()[:]\n"
                "{name}.keys = []\n"
                "{name}.rt = []\n"
        )
        buff.writeIndentedLines(code.format(**self.params))

        if (self.params['store'].val == 'nothing' and
                self.params['storeCorrect'].val == False):
            # the user doesn't want to store anything so don't bother
            return

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # some shortcuts
        store = self.params['store'].val
        storeCorr = self.params['storeCorrect'].val
        forceEnd = self.params['forceEndRoutine'].val
        allowedKeys = self.params['allowedKeys'].val.strip()

        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % self.params['name'])
        # writes an if statement to determine whether to draw etc
        allowedKeysIsVar = (valid_var_re.match(str(allowedKeys)) and not allowedKeys == 'None')
        indented = self.writeStartTestCode(buff)
        if indented:
            if allowedKeysIsVar:
                # if it looks like a variable, check that the variable is suitable
                # to eval at run-time
                code = ("# AllowedKeys looks like a variable named `{0}`\n"
                        "if not type({0}) in [list, tuple, np.ndarray]:\n")

                buff.writeIndentedLines(code.format(allowedKeys))

                buff.setIndentLevel(1, relative=True)
                code = ("if type({0}) == int:\n")
                buff.writeIndentedLines(code.format(allowedKeys))

                buff.setIndentLevel(1, relative=True)
                code = ("{0} = [{0}]\n")
                buff.writeIndentedLines(code.format(allowedKeys))
                buff.setIndentLevel(-1, relative=True)

                code = ("elif not (isinstance({0}, str) "
                        "or isinstance({0}, unicode)):\n")
                buff.writeIndentedLines(code.format(allowedKeys))

                buff.setIndentLevel(1, relative=True)
                code = ("logging.error('AllowedKeys variable `{0}` is "
                        "not string- or list-like.')\n"
                        "core.quit()\n")
                buff.writeIndentedLines(code.format(allowedKeys))
                buff.setIndentLevel(-1, relative=True)

                code = (
                    "elif not ',' in {0}: {0} = eval(({0},))\n"
                    "else: {0} = eval({0})\n")
                buff.writeIndentedLines(code.format(allowedKeys))
                buff.setIndentLevel(-1, relative=True)

            buff.writeIndented("# joyButtons checking is just starting\n")

            if store != 'nothing':
                if self.params['syncScreenRefresh'].val:
                    code = ("win.callOnFlip(%(name)s.clock.reset)  # t=0 on next"
                            " screen flip\n") % self.params
                else:
                    code = "%(name)s.clock.reset()  # now t=0\n" % self.params

                buff.writeIndented(code)

        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later
        # do we need a list of keys? (variable case is already handled)
        if allowedKeys in [None, "none", "None", "", "[]", "()"]:
            keyList=[]
        elif not allowedKeysIsVar:
            keyList = self.params['allowedKeys']

        code1 = ("{name}.newButtonState = {name}.device.getAllButtons()[:]\n"
                 "{name}.pressedButtons = []\n"
                 "{name}.releasedButtons = []\n"
                 "{name}.newPressedButtons = []\n"
                 "if {name}.newButtonState != {name}.oldButtonState:\n")

        code2 = ("{name}.pressedButtons = [i for i in range({name}.numButtons) "
                 "if {name}.newButtonState[i] and not {name}.oldButtonState[i]]\n"
                 "{name}.releasedButtons = [i for i in range({name}.numButtons) "
                 "if not {name}.newButtonState[i] and {name}.oldButtonState[i]]\n"
                 "{name}.oldButtonState = {name}.newButtonState\n"
                 "{name}.newPressedButtons = "
                 "[i for i in {0} if i in {name}.pressedButtons]\n"
                 "[logging.data(\"joystick_{{}}_button: {{}}\".format("
                 "{name}.device_number,i)) for i in {name}.pressedButtons]\n"
        )
        if allowedKeysIsVar:
            buff.writeIndentedLines(code1.format(allowedKeys, **self.params))
            buff.setIndentLevel(+1, relative=True)
            buff.writeIndentedLines(code2.format(allowedKeys, **self.params))
            buff.setIndentLevel(-1, relative=True)
        else:
            if keyList == []:
                buff.writeIndentedLines(code1.format(allowedKeys, **self.params))
                buff.setIndentLevel(+1, relative=True)
                buff.writeIndentedLines(code2.format(
                    "range({name}.numButtons)".format(**self.params), **self.params))
                buff.setIndentLevel(-1, relative=True)
            else:
                buff.writeIndentedLines(code1.format(allowedKeys, **self.params))
                buff.setIndentLevel(+1, relative=True)
                buff.writeIndentedLines(
                    code2.format("{}".format(keyList), **self.params))
                buff.setIndentLevel(-1, relative=True)

        code = (
            "theseKeys = %(name)s.newPressedButtons\n"
        )
        buff.writeIndented(code % self.params)

        if self.exp.settings.params['Enable Escape'].val:
            code = ('\n# check for quit:\n'
                    'if "escape" in theseKeys:\n'
                    '    endExpNow = True\n')

        # how do we store it?
        if store != 'nothing' or forceEnd:
            # we are going to store something
            code = "if len(theseKeys) > 0:  # at least one key was pressed\n"
            buff.writeIndented(code)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

        if store == 'first key':  # then see if a key has already been pressed
            code = ("if %(name)s.keys == []:  # then this was the first "
                    "keypress\n") % self.params
            buff.writeIndented(code)

            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

            code = ("%(name)s.keys = theseKeys[0]  # just the first key pressed\n"
                    "%(name)s.rt = %(name)s.clock.getTime()\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'last key':
            code = ("%(name)s.keys = theseKeys[-1]  # just the last key pressed\n"
                    "%(name)s.rt = %(name)s.clock.getTime()\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'all keys':
            code = ("%(name)s.keys.extend(theseKeys)  # storing all keys\n"
                    "%(name)s.rt.append(%(name)s.clock.getTime())\n")
            buff.writeIndentedLines(code % self.params)

        if storeCorr:
            code = ("# was this 'correct'?\n"
                    "if (str(%(name)s.keys) == str(%(correctAns)s)):\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(+1, relative=True)
            code = ("%(name)s.corr = 1\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-1, relative=True)
            code = ("else:\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(+1, relative=True)
            code =  ("%(name)s.corr = 0\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-1, relative=True)

        if forceEnd == True:
            code = ("# a response ends the routine\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-(dedentAtEnd), relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        store = self.params['store'].val
        if store == 'nothing':
            return
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        # write the actual code
        code = ("# check responses\n"
                "if %(name)s.keys in ['', [], None]:  # No response was made\n")
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(+1, relative=True)
        code = ("%(name)s.keys=None\n")
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        if self.params['storeCorrect'].val:  # check for correct NON-repsonse
            buff.setIndentLevel(1, relative=True)
            code = ("# was no response the correct answer?!\n"
                    "if str(%(correctAns)s).lower() == 'none':\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            code = ("%(name)s.corr = 1;  # correct non-response\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-1, relative=True)
            code = ("else:\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            code = ("%(name)s.corr = 0;  # failed to respond (incorrectly)\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-2, relative=True)
            code = ("# store data for %s (%s)\n")
            buff.writeIndentedLines(code %
                                    (currLoop.params['name'], currLoop.type))

        if currLoop.type in ['StairHandler', 'MultiStairHandler']:
            # data belongs to a Staircase-type of object
            if self.params['storeCorrect'].val is True:
                code = ("%s.addResponse(%s.corr, level)\n" %
                        (currLoop.params['name'], name) +
                        "%s.addOtherData('%s.rt', %s.rt)\n"
                        % (currLoop.params['name'], name, name))
                buff.writeIndentedLines(code)
        else:
            # always add keys
            buff.writeIndented("%s.addData('%s.keys',%s.keys)\n" %
                               (currLoop.params['name'], name, name))

            if self.params['storeCorrect'].val == True:
                buff.writeIndented("%s.addData('%s.corr', %s.corr)\n" %
                                   (currLoop.params['name'], name, name))

            # only add an RT if we had a response
            code = ("if %(name)s.keys != None:  # we had a response\n" %
                    self.params +
                    "    %s.addData('%s.rt', %s.rt)\n" %
                    (currLoop.params['name'], name, name))
            buff.writeIndentedLines(code)

        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)
