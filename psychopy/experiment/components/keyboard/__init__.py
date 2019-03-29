#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from builtins import str
from builtins import range
from builtins import super  # provides Py3-style super() using python-future
from past.builtins import basestring

from os import path

from psychopy.constants import PY3
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.experiment import CodeGenerationException, valid_var_re
from pkgutil import find_loader

# Check for psychtoolbox
havePTB = find_loader('psychtoolbox') is not None

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'keyboard.png')
tooltip = _translate('Keyboard: check and record keypresses')

# only use _localized values for label values, nothing functional:
_localized = {'allowedKeys': _translate('Allowed keys'),
              'discard previous': _translate('Discard previous'),
              'store': _translate('Store'),
              'forceEndRoutine': _translate('Force end of Routine'),
              'storeCorrect': _translate('Store correct'),
              'correctAns': _translate('Correct answer'),
              'syncScreenRefresh': _translate('Sync timing with screen')}


class KeyboardComponent(BaseComponent):
    """An event class for checking the keyboard at given timepoints"""
    # an attribute of the class, determines the section in components panel
    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']

    def __init__(self, exp, parentName, name='key_resp',
                 allowedKeys="'y','n','left','right','space'",
                 store='last key', forceEndRoutine=True, storeCorrect=False,
                 correctAns="", discardPrev=True,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 syncScreenRefresh=True):
        super(KeyboardComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Keyboard'
        self.url = "http://www.psychopy.org/builder/components/keyboard.html"
        self.exp.requirePsychopyLibs(['gui'])

        # params

        # NB name and timing params always come 1st
        self.order = ['forceEndRoutine', 'allowedKeys', 'store',
                      'storeCorrect', 'correctAns']

        msg = _translate(
            "A comma-separated list of keys (with quotes), such as "
            "'q','right','space','left'")
        self.params['allowedKeys'] = Param(
            allowedKeys, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat'],
            hint=(msg),
            label=_localized['allowedKeys'])

        # hints say 'responses' not 'key presses' because the same hint is
        # also used with button boxes
        msg = _translate("Do you want to discard all responses occuring "
                         "before the onset of this component?")
        self.params['discard previous'] = Param(
            discardPrev, valType='bool', allowedTypes=[],
            updates='constant',
            hint=msg,
            label=_localized['discard previous'])

        msg = _translate("Choose which (if any) responses to store at the "
                         "end of a trial")
        self.params['store'] = Param(
            store, valType='str', allowedTypes=[],
            allowedVals=['last key', 'first key', 'all keys', 'nothing'],
            updates='constant',
            hint=msg,
            label=_localized['store'])

        msg = _translate("Should a response force the end of the Routine "
                         "(e.g end the trial)?")
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant',
            hint=msg,
            label=_localized['forceEndRoutine'])

        msg = _translate("Do you want to save the response as "
                         "correct/incorrect?")
        self.params['storeCorrect'] = Param(
            storeCorrect, valType='bool', allowedTypes=[],
            updates='constant',
            hint=msg,
            label=_localized['storeCorrect'])

        msg = _translate(
            "What is the 'correct' key? Might be helpful to add a "
            "correctAns column and use $correctAns to compare to the key "
            "press.")
        self.params['correctAns'] = Param(
            correctAns, valType='str', allowedTypes=[],
            updates='constant',
            hint=msg,
            label=_localized['correctAns'])

        msg = _translate(
            "A reaction time to a visual stimulus should be based on when "
            "the screen flipped")
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType='bool',
            updates='constant',
            hint=msg,
            label=_localized['syncScreenRefresh'])

    def writeRoutineStartCode(self, buff):
        code = "%(name)s = keyboard.Keyboard()\n"
        buff.writeIndentedLines(code % self.params)

        if (self.params['store'].val == 'nothing' and
                self.params['storeCorrect'].val == False):
            # the user doesn't want to store anything so don't bother
            return

    def writeRoutineStartCodeJS(self, buff):
        code = "%(name)s = new core.BuilderKeyResponse(psychoJS);\n\n"
        buff.writeIndentedLines(code % self.params)

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
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)

        allowedKeysIsVar = (valid_var_re.match(str(allowedKeys)) and not
                            allowedKeys == 'None')

        if allowedKeysIsVar:
            # if it looks like a variable, check that the variable is suitable
            # to eval at run-time
            stringType = '{}'.format(['basestring', 'str'][PY3])
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

        if store != 'nothing':
            if self.params['syncScreenRefresh'].val:
                code = ("win.callOnFlip(%(name)s.clock.reset)  # t=0 on next"
                        " screen flip\n") % self.params
            else:
                code = "%(name)s.clock.reset()  # now t=0\n" % self.params

            buff.writeIndented(code)

        if self.params['discard previous'].val:
            code = "%(name)s.clearEvents(eventType='keyboard')\n" % self.params
            buff.writeIndented(code)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later
        # do we need a list of keys? (variable case is already handled)
        if allowedKeys in [None, "none", "None", "", "[]", "()"]:
            keyListStr = ""
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
            keyListStr = "%s" % repr(keyList)

        # check for keypresses
        code = "theseKeys = %s.getKeys(keyList=%s, waitRelease=False)\n" % (self.params['name'], (keyListStr or None))
        buff.writeIndented(code)

        # Check for response
        buff.writeIndented("if len(theseKeys):\n")
        buff.setIndentLevel(1, True)
        dedentAtEnd += 1  # indent by 1
        buff.writeIndented("theseKeys = theseKeys[0]  # at least one key was pressed\n")

        if self.exp.settings.params['Enable Escape'].val:
            code = ('\n# check for quit:\n'
                    'if "escape" == theseKeys:\n'
                    '    endExpNow = True\n')
            buff.writeIndentedLines(code)

        if store != 'nothing' or forceEnd:
            if store == 'first key':  # then see if a key has already been pressed
                code = ("if %(name)s.keys == []:  # then this was the first keypress\n") % self.params
                buff.writeIndented(code)
                buff.setIndentLevel(1, True)
                dedentAtEnd += 1  # indent by 1
                code = ("%(name)s.keys = theseKeys.name  # just the first key pressed\n"
                        "%(name)s.rt = theseKeys.rt\n")
                buff.writeIndentedLines(code % self.params)
            elif store == 'last key':
                code = ("%(name)s.keys = theseKeys.name  # just the last key pressed\n"
                        "%(name)s.rt = theseKeys.rt\n")
                buff.writeIndentedLines(code % self.params)
            elif store == 'all keys':
                code = ("%(name)s.keys.append(theseKeys.name)  # storing all keys\n"
                        "%(name)s.rt.append(theseKeys.rt)\n")
                buff.writeIndentedLines(code % self.params)

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
        buff.writeIndented("%(name)s.status = PsychoJS.Status.STARTED;\n" % self.params)

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
            #        "    if not isinstance(%s, basestring):\n"
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

        if store != 'nothing':
            if self.params['syncScreenRefresh'].val:
                code = ("psychoJS.window.callOnFlip(function() { %(name)s.clock.reset(); });"
                        " // t = 0 on screen flip\n") % self.params
            else:
                code = "%(name)s.clock.reset();  // now t=0\n" % self.params

            buff.writeIndented(code)

        if self.params['discard previous'].val:
            buff.writeIndented("psychoJS.eventManager.clearEvents({eventType:'keyboard'});\n")
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
            keyListStr = ""
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
            keyListStr = "{keyList:%s}" % repr(keyList)

        # check for keypresses
        buff.writeIndented("let theseKeys = psychoJS.eventManager.getKeys(%s);\n" % keyListStr)

        if self.exp.settings.params['Enable Escape'].val:
            code = ("\n// check for quit:\n"
                    "if (theseKeys.indexOf('escape') > -1) {\n"
                    "  psychoJS.experiment.experimentEnded = true;\n"
                    "}\n\n")
            buff.writeIndentedLines(code)

        # how do we store it?
        if store != 'nothing' or forceEnd:
            # we are going to store something
            code = ("if (theseKeys.length > 0) {"
                    "  // at least one key was pressed\n")
            buff.writeIndented(code)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # indent by 1

        if store == 'first key':  # then see if a key has already been pressed
            code = ("if (%(name)s.keys.length === 0) {"
                    "  // then this was the first keypress\n") % self.params
            buff.writeIndented(code)

            buff.setIndentLevel(1, True)
            dedentAtEnd += 1  # to undo this level of "if"

            code = ("%(name)s.keys = theseKeys[0];"
                    "  // just the first key pressed\n"
                    "%(name)s.rt = %(name)s.clock.getTime();\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'last key':
            code = ("%(name)s.keys = theseKeys[theseKeys.length-1];"
                    "  // just the last key pressed\n"
                    "%(name)s.rt = %(name)s.clock.getTime();\n")
            buff.writeIndentedLines(code % self.params)
        elif store == 'all keys':
            code = ("%(name)s.keys = %(name)s.keys.concat(theseKeys);  // storing all keys\n"
                    "%(name)s.rt = %(name)s.rt.concat(%(name)s.clock.getTime());\n")
            buff.writeIndentedLines(code % self.params)

        if storeCorr:
            code = ("// was this 'correct'?\n"
                    "if (%(name)s.keys == %(correctAns)s) {\n"
                    "    %(name)s.corr = 1;\n"
                    "} else {\n"
                    "    %(name)s.corr = 0;\n"
                    "}\n")
            buff.writeIndentedLines(code % self.params)

        if forceEnd == True:
            code = ("// a response ends the routine\n"
                    "continueRoutine = false;\n")
            buff.writeIndentedLines(code % self.params)

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
                code = ("%s.addResponse(%s.corr)\n" %
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
            return
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        # write the actual code
        code = ("\n// check responses\n"
                "if (%(name)s.keys === undefined || %(name)s.keys.length === 0) {"
                "    // No response was made\n"
                "    %(name)s.keys = undefined;\n"
                "}\n\n")
        buff.writeIndentedLines(code % self.params)

        if self.params['storeCorrect'].val:  # check for correct NON-repsonse
            code = ("// was no response the correct answer?!\n"
                    "if (%(name)s.keys === undefined) {\n"
                    "  if (['None','none',undefined].includes(%(correctAns)s)) {\n"
                    "     %(name)s.corr = 1  // correct non-response\n"
                    "  } else {\n"
                    "     %(name)s.corr = 0  // failed to respond (incorrectly)\n"
                    "  }\n"
                    "}\n"
                    % self.params)

            code += ("// store data for %s (%s)\n" %
                     (currLoop.params['name'], currLoop.type))

            buff.writeIndentedLines(code % self.params)

        if currLoop.type in ['StairHandler', 'MultiStairHandler']:
            raise CodeGenerationException(
                "StairHandlers not currently supported by PsychoJS")
        else:
            # always add keys
            buff.writeIndented("psychoJS.experiment.addData('%(name)s.keys', %(name)s.keys);\n" % self.params)

            if self.params['storeCorrect'].val == True:
                buff.writeIndented("psychoJS.experiment.addData('%(name)s.corr', %(name)s.corr);\n" % self.params)

            # only add an RT if we had a response
            code = ("if (typeof {name}.keys !== 'undefined') {{  // we had a response\n"
                    "    psychoJS.experiment.addData('{name}.rt', {name}.rt);\n")
            if forceEnd:
                code += ("    routineTimer.reset();\n"
                         "    }}\n\n")
            else:
                code += "    }}\n\n"
            buff.writeIndentedLines(code.format(loopName=currLoop.params['name'], name=name))
