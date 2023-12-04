#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path

from psychopy.experiment.components import BaseDeviceComponent, Param, _translate, getInitVals
from psychopy.experiment import CodeGenerationException, valid_var_re
from pkgutil import find_loader

# Check for psychtoolbox
havePTB = find_loader('psychtoolbox') is not None


class KeyboardComponent(BaseDeviceComponent):
    """An event class for checking the keyboard at given timepoints"""
    # an attribute of the class, determines the section in components panel
    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'keyboard.png'
    tooltip = _translate('Keyboard: check and record keypresses')

    def __init__(self, exp, parentName, name='key_resp', deviceLabel="",
                 allowedKeys="'y','n','left','right','space'", registerOn="press",
                 store='last key', forceEndRoutine=True, storeCorrect=False,
                 correctAns="", discardPrev=True,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 syncScreenRefresh=True,
                 disabled=False):
        BaseDeviceComponent.__init__(
            self, exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            deviceLabel=deviceLabel,
            disabled=disabled
        )

        self.type = 'Keyboard'
        self.url = "https://www.psychopy.org/builder/components/keyboard.html"
        self.exp.requirePsychopyLibs(['gui'])

        # params

        # NB name and timing params always come 1st
        self.order += ['forceEndRoutine', 'registerOn', 'allowedKeys',  # Basic tab
                       'store', 'storeCorrect', 'correctAns'  # Data tab
                       ]

        # --- Basic ---
        self.order += [
            "registerOn",
            "allowedKeys",
            "forceEndRoutine"
        ]

        msg = _translate(
            "When should the keypress be registered? As soon as pressed, or when released?")
        self.params['registerOn'] = Param(
            registerOn, valType='str', inputType='choice',
            categ='Basic', updates='constant',
            allowedVals=["press", "release"],
            hint=msg,
            label=_translate("Register keypress on...")
        )

        msg = _translate(
            "A comma-separated list of keys (with quotes), such as "
            "'q','right','space','left'")
        self.params['allowedKeys'] = Param(
            allowedKeys, valType='list', inputType="single", categ='Basic',
            updates='constant', allowedUpdates=['constant', 'set every repeat'],
            hint=(msg),
            label=_translate("Allowed keys"))

        msg = _translate("Should a response force the end of the Routine "
                         "(e.g end the trial)?")
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            updates='constant',
            hint=msg,
            label=_translate("Force end of Routine"))

        # hints say 'responses' not 'key presses' because the same hint is
        # also used with button boxes
        msg = _translate("Do you want to discard all responses occurring "
                         "before the onset of this Component?")
        self.params['discard previous'] = Param(
            discardPrev, valType='bool', inputType="bool", allowedTypes=[], categ='Data',
            updates='constant',
            hint=msg,
            label=_translate("Discard previous"))

        msg = _translate("Choose which (if any) responses to store at the "
                         "end of a trial")
        self.params['store'] = Param(
            store, valType='str', inputType="choice", allowedTypes=[], categ='Data',
            allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant', direct=False,
            hint=msg,
            label=_translate("Store"))

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
            correctAns, valType='str', inputType="single", allowedTypes=[], categ='Data',
            updates='constant',
            hint=msg, direct=False,
            label=_translate("Correct answer"))

        msg = _translate(
            "A reaction time to a visual stimulus should be based on when "
            "the screen flipped")
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType='bool', inputType="bool", categ='Data',
            updates='constant',
            hint=msg,
            label=_translate("Sync timing with screen"))

    def writeDeviceCode(self, buff):
        # get inits
        inits = getInitVals(self.params)
        # write device creation code
        code = (
            "if deviceManager.getDevice(%(deviceLabel)s) is None:\n"
            "    # initialise %(deviceLabelCode)s\n"
            "    %(deviceLabelCode)s = deviceManager.addDevice(\n"
            "        deviceClass='keyboard',\n"
            "        deviceName=%(deviceLabel)s,\n"
            "    )\n"
        )
        buff.writeOnceIndentedLines(code % inits)

    def writeInitCode(self, buff):
        # get inits
        inits = getInitVals(self.params)
        # make Keyboard object
        code = (
            "%(name)s = keyboard.Keyboard(deviceName=%(deviceLabel)s)\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        code = "%(name)s = new core.Keyboard({psychoJS: psychoJS, clock: new util.Clock(), waitForStart: true});\n\n"
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        code = ("%(name)s.keys = []\n"
                "%(name)s.rt = []\n"
                "_%(name)s_allKeys = []\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCodeJS(self, buff):
        code = ("%(name)s.keys = undefined;\n"
                "%(name)s.rt = undefined;\n"
                "_%(name)s_allKeys = [];\n")
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # some shortcuts
        store = self.params['store'].val
        storeCorr = self.params['storeCorrect'].val
        forceEnd = self.params['forceEndRoutine'].val
        allowedKeys = str(self.params['allowedKeys'])
        visualSync = self.params['syncScreenRefresh'].val

        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % self.params['name'])
        if visualSync:
            buff.writeIndented("waitOnFlip = False\n")
        allowedKeysIsVar = (valid_var_re.match(str(allowedKeys)) and not allowedKeys == 'None')
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            if allowedKeysIsVar:
                # if it looks like a variable, check that the variable is suitable
                # to eval at run-time
                stringType = 'str'
                code = ("# AllowedKeys looks like a variable named `{0}`\n"
                        "if not type({0}) in [list, tuple, np.ndarray]:\n"
                        "    if not isinstance({0}, {1}):\n"
                        "        logging.error('AllowedKeys variable `{0}` is "
                        "not string- or list-like.')\n"
                        "        core.quit()\n"
                        .format(allowedKeys, stringType))

                code += (
                    "    elif not ',' in {0}:\n"
                    "        {0} = ({0},)\n"
                    "    else:\n"
                    "        {0} = eval({0})\n"
                    .format(allowedKeys))
                buff.writeIndentedLines(code)

                keyListStr = "list(%s)" % allowedKeys  # eval at run time

            buff.writeIndented("# keyboard checking is just starting\n")

            if visualSync:
                code = ("waitOnFlip = True\n"
                        "win.callOnFlip(%(name)s.clock.reset)  "
                        "# t=0 on next screen flip\n") % self.params
            else:
                code = "%(name)s.clock.reset()  # now t=0\n" % self.params
            buff.writeIndentedLines(code)

            if self.params['discard previous'].val:
                if visualSync:
                    code = ("win.callOnFlip(%(name)s.clearEvents, eventType='keyboard')  "
                            "# clear events on next screen flip\n") % self.params
                else:
                    code = "%(name)s.clearEvents(eventType='keyboard')\n" % self.params
                buff.writeIndented(code)

        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        if indented:
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        buff.writeIndented("if %s.status == STARTED%s:\n"
                           % (self.params['name'], ['', ' and not waitOnFlip'][visualSync]))
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later
        # do we need a list of keys? (variable case is already handled)
        if allowedKeys in [None, "none", "None", "", "[]", "()"]:
            keyListStr = ""
        elif not allowedKeysIsVar:
            keyListStr = self.params['allowedKeys']

        # check for keypresses
        expEscape = "None"
        if self.exp.settings.params['Enable Escape']:
            expEscape = '["escape"]'
        code = ("theseKeys = {name}.getKeys(keyList={keyStr}, ignoreKeys={expEscape}, waitRelease={waitRelease})\n"
                "_{name}_allKeys.extend(theseKeys)\n"
                "if len(_{name}_allKeys):\n")
        buff.writeIndentedLines(
            code.format(
                name=self.params['name'],
                waitRelease=self.params['registerOn'] == "release",
                keyStr=(keyListStr or None),
                expEscape=expEscape
            )
        )

        buff.setIndentLevel(1, True)
        dedentAtEnd += 1
        if store == 'first key':  # then see if a key has already been pressed
            code = ("{name}.keys = _{name}_allKeys[0].name  # just the first key pressed\n"
                    "{name}.rt = _{name}_allKeys[0].rt\n"
                    "{name}.duration = _{name}_allKeys[0].duration\n")
            buff.writeIndentedLines(code.format(name=self.params['name']))
        elif store == 'last key' or store == "nothing":  # If store nothing, save last key for correct answer test
            code = ("{name}.keys = _{name}_allKeys[-1].name  # just the last key pressed\n"
                    "{name}.rt = _{name}_allKeys[-1].rt\n"
                    "{name}.duration = _{name}_allKeys[-1].duration\n")
            buff.writeIndentedLines(code.format(name=self.params['name']))
        elif store == 'all keys':
            code = ("{name}.keys = [key.name for key in _{name}_allKeys]  # storing all keys\n"
                    "{name}.rt = [key.rt for key in _{name}_allKeys]\n"
                    "{name}.duration = [key.duration for key in _{name}_allKeys]\n")
            buff.writeIndentedLines(code.format(name=self.params['name']))

        if storeCorr:
            code = ("# was this correct?\n"
                    "if ({name}.keys == str({correctAns})) or ({name}.keys == {correctAns}):\n"
                    "    {name}.corr = 1\n"
                    "else:\n"
                    "    {name}.corr = 0\n")
            buff.writeIndentedLines(
                code.format(
                    name=self.params['name'],
                    correctAns=self.params['correctAns']
                )
            )

        if forceEnd == True:
            code = ("# a response ends the routine\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code)

        buff.setIndentLevel(-(dedentAtEnd), relative=True)

    def writeFrameCodeJS(self, buff):
        # some shortcuts
        store = self.params['store'].val
        storeCorr = self.params['storeCorrect'].val
        forceEnd = self.params['forceEndRoutine'].val
        allowedKeys = self.params['allowedKeys'].val.strip()

        buff.writeIndented("\n")
        buff.writeIndented("// *%s* updates\n" % self.params['name'])
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCodeJS(buff)

        allowedKeysIsVar = (valid_var_re.match(str(allowedKeys)) and not
                            allowedKeys == 'None')

        if allowedKeysIsVar:
            # if it looks like a variable, check that the variable is suitable
            # to eval at run-time
            raise CodeGenerationException(
                "Variables for allowKeys aren't supported for JS yet")
            #code = ("# AllowedKeys looks like a variable named `%s`\n"
            #        "if not '%s' in locals():\n"
            #        "    logging.error('AllowedKeys variable `%s` is not defined.')\n"
            #        "    core.quit()\n"
            #        "if not type(%s) in [list, tuple, np.ndarray]:\n"
            #        "    if not isinstance(%s, str):\n"
            #        "        logging.error('AllowedKeys variable `%s` is "
            #        "not string- or list-like.')\n"
            #        "        core.quit()\n" %
            #        allowedKeys)
            #
            #vals = (allowedKeys, allowedKeys, allowedKeys)
            #code += (
            #    "    elif not ',' in %s: %s = (%s,)\n" % vals +
            #    "    else:  %s = eval(%s)\n" % (allowedKeys, allowedKeys))
            #buff.writeIndentedLines(code)
            #
            #keyListStr = "keyList=list(%s)" % allowedKeys  # eval at run time

        buff.writeIndented("// keyboard checking is just starting\n")

        if self.params['syncScreenRefresh'].val:
            code = ("psychoJS.window.callOnFlip(function() { %(name)s.clock.reset(); });  "
                    "// t=0 on next screen flip\n"
                    "psychoJS.window.callOnFlip(function() { %(name)s.start(); }); "
                    "// start on screen flip\n") % self.params
        else:
            code = ("%(name)s.clock.reset();\n"
                    "%(name)s.start();\n") % self.params

        buff.writeIndentedLines(code)

        if self.params['discard previous'].val:
            if self.params['syncScreenRefresh'].val:
                 buff.writeIndented("psychoJS.window.callOnFlip(function() { %(name)s.clearEvents(); });\n"
                                    % self.params)
            else:
                buff.writeIndented("%(name)s.clearEvents();\n" % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("}\n\n")

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCodeJS(buff)
            buff.writeIndented("%(name)s.status = PsychoJS.Status.FINISHED;\n"
                               "  }\n"
                               "\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        buff.writeIndented("if (%(name)s.status === PsychoJS.Status.STARTED) {\n" % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later
        # do we need a list of keys? (variable case is already handled)
        if allowedKeys in [None, "none", "None", "", "[]", "()"]:
            keyListStr = "[]"
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
            keyListStr = "%s" % repr(keyList)

        # check for keypresses
        waitRelease = "false"
        if self.params['registerOn'] == "release":
            waitRelease = "true"
        code = ("let theseKeys = {name}.getKeys({{keyList: {keyStr}, waitRelease: {waitRelease}}});\n"
                "_{name}_allKeys = _{name}_allKeys.concat(theseKeys);\n"
                "if (_{name}_allKeys.length > 0) {{\n")
        buff.writeIndentedLines(
            code.format(
                name=self.params['name'],
                waitRelease=waitRelease,
                keyStr=keyListStr
            )
        )
        buff.setIndentLevel(1, True)
        dedentAtEnd += 1
        # how do we store it?
        if store == 'first key':  # then see if a key has already been pressed
            code = ("{name}.keys = _{name}_allKeys[0].name;  // just the first key pressed\n"
                    "{name}.rt = _{name}_allKeys[0].rt;\n"
                    "{name}.duration = _{name}_allKeys[0].duration;\n")
            buff.writeIndentedLines(code.format(name=self.params['name']))
        elif store == 'last key' or store =='nothing':
            code = ("{name}.keys = _{name}_allKeys[_{name}_allKeys.length - 1].name;  // just the last key pressed\n"
                    "{name}.rt = _{name}_allKeys[_{name}_allKeys.length - 1].rt;\n"
                    "{name}.duration = _{name}_allKeys[_{name}_allKeys.length - 1].duration;\n")
            buff.writeIndentedLines(code.format(name=self.params['name']))
        elif store == 'all keys':
            code = ("{name}.keys = _{name}_allKeys.map((key) => key.name);  // storing all keys\n"
                    "{name}.rt = _{name}_allKeys.map((key) => key.rt);\n" \
                    "{name}.duration = _{name}_allKeys.map((key) => key.duration);\n")
            buff.writeIndentedLines(code.format(name=self.params['name']))

        if storeCorr:
            code = ("// was this correct?\n"
                    "if ({name}.keys == {correctAns}) {{\n"
                    "    {name}.corr = 1;\n"
                    "}} else {{\n"
                    "    {name}.corr = 0;\n"
                    "}}\n")
            buff.writeIndentedLines(
                code.format(
                    name=self.params['name'],
                    correctAns=self.params['correctAns']
                )
            )

        if forceEnd == True:
            code = ("// a response ends the routine\n"
                    "continueRoutine = false;\n")
            buff.writeIndentedLines(code)

        for dedents in range(dedentAtEnd):
            buff.setIndentLevel(-1, relative=True)
            buff.writeIndented("}\n")
        buff.writeIndented("\n")

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
                "if %(name)s.keys in ['', [], None]:  # No response was made\n"
                "    %(name)s.keys = None\n")
        buff.writeIndentedLines(code % self.params)

        if self.params['storeCorrect'].val:  # check for correct NON-response
            code = ("    # was no response the correct answer?!\n"
                    "    if str(%(correctAns)s).lower() == 'none':\n"
                    "       %(name)s.corr = 1;  # correct non-response\n"
                    "    else:\n"
                    "       %(name)s.corr = 0;  # failed to respond (incorrectly)\n"
                    % self.params)

            code += ("# store data for %s (%s)\n" %
                     (currLoop.params['name'], currLoop.type))

            buff.writeIndentedLines(code % self.params)

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
            code = (
                    "if %(name)s.keys != None:  # we had a response\n" % self.params +
                    "    %s.addData('%s.rt', %s.rt)\n" % (currLoop.params['name'], name, name) +
                    "    %s.addData('%s.duration', %s.duration)\n" % (currLoop.params['name'], name, name)
            )
            buff.writeIndentedLines(code)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)

    def writeRoutineEndCodeJS(self, buff):
        # some shortcuts
        name = self.params['name']
        store = self.params['store'].val
        forceEnd = self.params['forceEndRoutine'].val
        if store == 'nothing':
            # Still stop keyboard to prevent textbox from not working on single keypresses due to buffer
            buff.writeIndentedLines("%(name)s.stop();\n" % self.params)
            return
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if self.params['storeCorrect'].val:  # check for correct NON-repsonse
            code = ("// was no response the correct answer?!\n"
                    "if (%(name)s.keys === undefined) {\n"
                    "  if (['None','none',undefined].includes(%(correctAns)s)) {\n"
                    "     %(name)s.corr = 1;  // correct non-response\n"
                    "  } else {\n"
                    "     %(name)s.corr = 0;  // failed to respond (incorrectly)\n"
                    "  }\n"
                    "}\n"
                    % self.params)

            code += "// store data for current loop\n"

            buff.writeIndentedLines(code % self.params)

        code = (
            "// update the trial handler\n"
            "if (currentLoop instanceof MultiStairHandler) {\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        code = (
                "currentLoop.addResponse(%(name)s.corr, level);\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = (
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)

        # always add keys
        buff.writeIndented("psychoJS.experiment.addData('%(name)s.keys', %(name)s.keys);\n" % self.params)

        if self.params['storeCorrect'].val == True:
            buff.writeIndented("psychoJS.experiment.addData('%(name)s.corr', %(name)s.corr);\n" % self.params)

        # only add an RT if we had a response
        code = ("if (typeof {name}.keys !== 'undefined') {{  // we had a response\n"
                "    psychoJS.experiment.addData('{name}.rt', {name}.rt);\n"
                "    psychoJS.experiment.addData('{name}.duration', {name}.duration);\n")
        if forceEnd:
            code += ("    routineTimer.reset();\n"
                     "    }}\n\n")
        else:
            code += "    }}\n\n"
        buff.writeIndentedLines(code.format(name=name))
        # Stop keyboard
        buff.writeIndentedLines("%(name)s.stop();\n" % self.params)
