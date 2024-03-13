#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
import re


class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons
    at given timepoints
    """
    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'mouse.png'
    tooltip = _translate('Mouse: query mouse position and buttons')

    def __init__(self, exp, parentName, name='mouse',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 save='on click', forceEndRoutineOnPress="any click",
                 storeCorrect=False, correctAns="",
                 timeRelativeTo='mouse onset'):
        super(MouseComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Mouse'
        self.url = "https://www.psychopy.org/builder/components/mouse.html"
        self.exp.requirePsychopyLibs(['event'])

        self.order += [
            'forceEndRoutineOnPress',  # Basic tab
            'saveMouseState', 'timeRelativeTo', 'newClicksOnly', 'clickable', 'saveParamsClickable',  # Data tab
            ]

        # params
        msg = _translate(
            "How often should the mouse state (x,y,buttons) be stored? "
            "On every video frame, every click or just at the end of the "
            "Routine?")
        self.params['saveMouseState'] = Param(
            save, valType='str', inputType="choice", categ='Data',
            allowedVals=['final', 'on click', 'on valid click', 'every frame', 'never'],
            hint=msg, direct=False,
            label=_translate("Save mouse state"))

        msg = _translate("Should a button press force the end of the Routine"
                         " (e.g end the trial)?")
        if forceEndRoutineOnPress is True:
            forceEndRoutineOnPress = 'any click'
        elif forceEndRoutineOnPress is False:
            forceEndRoutineOnPress = 'never'
        self.params['forceEndRoutineOnPress'] = Param(
            forceEndRoutineOnPress, valType='str', inputType="choice", categ='Basic',
            allowedVals=['never', 'any click', 'valid click', 'correct click'],
            updates='constant', direct=False,
            hint=msg,
            label=_translate("End Routine on press"))

        msg = _translate("What should the values of mouse.time should be "
                         "relative to?")
        self.params['timeRelativeTo'] = Param(
            timeRelativeTo, valType='str', inputType="choice", categ='Data',
            allowedVals=['mouse onset', 'experiment', 'routine'],
            updates='constant',
            hint=msg, direct=False,
            label=_translate("Time relative to"))

        msg = _translate('If the mouse button is already down when we start '
                         'checking then wait for it to be released before '
                         'recording as a new click.'
                         )
        self.params['newClicksOnly'] = Param(
            True, valType='bool', inputType="bool", categ='Basic',
            updates='constant',
            hint=msg,
            label=_translate("New clicks only"))

        msg = _translate('A comma-separated list of your stimulus names that '
                         'can be "clicked" by the participant. '
                         'e.g. target, foil'
                         )
        self.params['clickable'] = Param(
            '', valType='list', inputType="single", categ='Basic',
            updates='constant',
            hint=msg,
            label=_translate("Clickable stimuli"))

        msg = _translate('The params (e.g. name, text), for which you want '
                         'to store the current value, for the stimulus that was'
                         '"clicked" by the mouse. Make sure that all the '
                         'clickable objects have all these params.'
                         )
        self.params['saveParamsClickable'] = Param(
            'name,', valType='list', inputType="single", categ='Data',
            updates='constant', allowedUpdates=[], direct=False,
            hint=msg,
            label=_translate("Store params for clicked"))

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
            "What is the 'correct' object? To specify an area, remember that you can create a shape Component with 0 "
            "opacity.")
        self.params['correctAns'] = Param(
            correctAns, valType='list', inputType="single", allowedTypes=[], categ='Data',
            updates='constant',
            hint=msg, direct=False,
            label=_translate("Correct answer"))

    @property
    def _clickableParamsList(self):
        # convert clickableParams (str) to a list
        params = self.params['saveParamsClickable'].val
        paramsList = re.findall(r"[\w']+", params)
        return paramsList or ['name']

    def _writeClickableObjectsCode(self, buff):
        # code to check if clickable objects were clicked
        code = (
            "# check if the mouse was inside our 'clickable' objects\n"
            "gotValidClick = False\n"
            "clickableList = environmenttools.getFromNames(%(clickable)s, namespace=locals())\n"
            "for obj in clickableList:\n"
            "    # is this object clicked on?\n"
            "    if obj.contains(%(name)s):\n"
            "        gotValidClick = True\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+2, relative=True)
        code = ''
        for paramName in self._clickableParamsList:
            code += "%s.clicked_%s.append(obj.%s)\n" %(self.params['name'],
                                                     paramName, paramName)
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-2, relative=True)

    def _writeCorrectAnsCode(self, buff):
        code = (
            "# check whether click was in correct object\n"
            "if gotValidClick:\n"
            "    _corr = 0\n"
            "    _corrAns = environmenttools.getFromNames(%(correctAns)s, namespace=locals())\n"
            "    for obj in _corrAns:\n"
            "        # is this object clicked on?\n"
            "        if obj.contains(%(name)s):\n"
            "            _corr = 1\n"
            "    %(name)s.corr.append(_corr)\n"
        )
        # Write force end code
        if self.params['forceEndRoutineOnPress'] == 'correct click':
            code += (
            "    if corr:\n"
            "        continueRoutine = False  # end routine on correct answer\n"
            )
        buff.writeIndentedLines(code % self.params)

    def _writeCorrectAnsCodeJS(self, buff):
        code = (
            "// check whether click was in correct object\n"
            "if (gotValidClick) {\n"
            "    corr = 0;\n"
            "    corrAns = %(correctAns)s;\n"
            "    for (let obj of [corrAns]) {\n"
            "        if (obj.contains(%(name)s)) {\n"
            "            corr = 1;\n"
            "        };\n"
            "    };\n"
            "    %(name)s.corr.push(corr);\n"
        )
        # Write force end code
        if self.params['forceEndRoutineOnPress'] == 'correct click':
            code += (
            "    if (corr) {\n"
            "        // end routine on correct answer\n"
            "        continueRoutine = false;\n"
            "    };\n"
            )
        buff.writeIndentedLines(code % self.params)
        # Close if statement
        code = (
            "};\n"
        )
        buff.writeIndentedLines(code % self.params)

    def _writeClickableObjectsCodeJS(self, buff):
        # code to check if clickable objects were clicked
        code = (
            "// check if the mouse was inside our 'clickable' objects\n"
            "gotValidClick = false;\n"
            "for (const obj of [{clickable}]) {{\n"
            "  if (obj.contains({name})) {{\n"
            "    gotValidClick = true;\n")
        buff.writeIndentedLines(code.format(name=self.params['name'],
                                            clickable=self.params['clickable'].val))
        buff.setIndentLevel(+2, relative=True)
        dedent = 2
        code = ''
        for paramName in self._clickableParamsList:
            code += "%s.clicked_%s.push(obj.%s)\n" % (self.params['name'],
                                                        paramName, paramName)

        buff.writeIndentedLines(code % self.params)
        for dents in range(dedent):
            buff.setIndentLevel(-1, relative=True)
            buff.writeIndented('}\n')

    def writeInitCode(self, buff):
        code = ("%(name)s = event.Mouse(win=win)\n"
                "x, y = [None, None]\n"
                "%(name)s.mouseClock = core.Clock()\n")
        buff.writeIndentedLines(code % self.params)

    def writeInitCodeJS(self, buff):
        code = ("%(name)s = new core.Mouse({\n"
                "  win: psychoJS.window,\n"
                "});\n"
                "%(name)s.mouseClock = new util.Clock();\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        # create some lists to store recorded values positions and events if
        # we need more than one
        code = ("# setup some python lists for storing info about the "
                "%(name)s\n")
        if self.params['saveMouseState'].val in ['every frame', 'on click', 'on valid click']:
            code += ("%(name)s.x = []\n"
                     "%(name)s.y = []\n"
                     "%(name)s.leftButton = []\n"
                     "%(name)s.midButton = []\n"
                     "%(name)s.rightButton = []\n"
                     "%(name)s.time = []\n")
        if self.params['storeCorrect']:
            code += (
                "%(name)s.corr = []\n"
            )
        if self.params['clickable'].val:
            for clickableObjParam in self._clickableParamsList:
                code += "%(name)s.clicked_{} = []\n".format(clickableObjParam)

        code += "gotValidClick = False  # until a click is received\n"

        if self.params['timeRelativeTo'].val.lower() == 'routine':
            code += "%(name)s.mouseClock.reset()\n"

        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCodeJS(self, buff):
        """Write the code that will be called at the start of the routine"""

        code = ("// setup some python lists for storing info about the %(name)s\n")
        if self.params['saveMouseState'].val in ['every frame', 'on click', 'on valid click']:
            code += ("// current position of the mouse:\n"
                     "%(name)s.x = [];\n"
                     "%(name)s.y = [];\n"
                     "%(name)s.leftButton = [];\n"
                     "%(name)s.midButton = [];\n"
                     "%(name)s.rightButton = [];\n"
                     "%(name)s.time = [];\n")

        if self.params['storeCorrect']:
            code += (
                "%(name)s.corr = [];\n"
            )

        if self.params['clickable'].val:
            for clickableObjParam in self._clickableParamsList:
                code += "%s.clicked_%s = [];\n" % (self.params['name'], clickableObjParam)
        code += "gotValidClick = false; // until a click is received\n"

        if self.params['timeRelativeTo'].val.lower() == 'routine':
            code += "%(name)s.mouseClock.reset();\n"

        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""

        forceEnd = self.params['forceEndRoutineOnPress'].val

        # get a clock for timing
        timeRelative = self.params['timeRelativeTo'].val.lower()
        if timeRelative == 'experiment':
            self.clockStr = 'globalClock'
        elif timeRelative in ['routine', 'mouse onset']:
            self.clockStr = '%s.mouseClock' % self.params['name'].val

        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            code = ""
            if self.params['timeRelativeTo'].val.lower() == 'mouse onset':
                code += "%(name)s.mouseClock.reset()\n"

            if self.params['newClicksOnly']:
                code += (
                    "prevButtonState = %(name)s.getPressed()"
                    "  # if button is down already this ISN'T a new click\n")
            else:
                code += (
                    "prevButtonState = [0, 0, 0]"
                    "  # if now button is down we will treat as 'new' click\n")
            buff.writeIndentedLines(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveMouseState'].val not in
                ['every frame', 'on click', 'on valid click'] and forceEnd == 'never'):
            return

        # if STARTED and not FINISHED!
        code = ("if %(name)s.status == STARTED:  "
                "# only update if started and not finished!\n") % self.params
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        def _buttonPressCode(buff, dedent):
            """Code compiler for mouse button events"""
            code = ("buttons = %(name)s.getPressed()\n"
                    "if buttons != prevButtonState:  # button state changed?")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedent += 1
            buff.writeIndented("prevButtonState = buttons\n")
            code = ("if sum(buttons) > 0:  # state changed to a new click\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedent += 1
            if self.params['clickable'].val:
                self._writeClickableObjectsCode(buff)
            if self.params['storeCorrect']:
                self._writeCorrectAnsCode(buff)
            return buff, dedent

        # No mouse tracking, end routine on any or valid click
        if self.params['saveMouseState'].val in ['never', 'final'] and forceEnd != "never":
            buff, dedentAtEnd = _buttonPressCode(buff, dedentAtEnd)

            if forceEnd == 'valid click':
                    # does valid response end the trial?
                    code = ("if gotValidClick:  \n"
                            "    continueRoutine = False  # end routine on response\n")
                    buff.writeIndentedLines(code)
                    buff.setIndentLevel(-dedentAtEnd, relative=True)
            else:
                buff.writeIndented('continueRoutine = False  # end routine on response')
                buff.setIndentLevel(-dedentAtEnd, relative=True)

        elif self.params['saveMouseState'].val != 'never':
            mouseCode = ("x, y = {name}.getPos()\n"
                    "{name}.x.append(x)\n"
                    "{name}.y.append(y)\n"
                    "buttons = {name}.getPressed()\n"
                    "{name}.leftButton.append(buttons[0])\n"
                    "{name}.midButton.append(buttons[1])\n"
                    "{name}.rightButton.append(buttons[2])\n"
                    "{name}.time.append({clockStr}.getTime())\n".format(name=self.params['name'],
                                                                        clockStr=self.clockStr))

            # Continuous mouse tracking
            if self.params['saveMouseState'].val in ['every frame']:
                buff.writeIndentedLines(mouseCode)

            # Continuous mouse tracking for all button press
            if forceEnd == 'never' and self.params['saveMouseState'].val in ['on click', 'on valid click']:
                buff, dedentAtEnd = _buttonPressCode(buff, dedentAtEnd)
                if self.params['saveMouseState'].val in ['on click']:
                    buff.writeIndentedLines(mouseCode)
                elif self.params['clickable'].val and self.params['saveMouseState'].val in ['on valid click']:
                    code = (
                        "if gotValidClick:\n"
                    )
                    buff.writeIndentedLines(code)
                    buff.setIndentLevel(+1, relative=True)
                    buff.writeIndentedLines(mouseCode)
                    buff.setIndentLevel(-1, relative=True)

            # Mouse tracking for events that end routine
            elif forceEnd != "never":
                buff, dedentAtEnd = _buttonPressCode(buff, dedentAtEnd)
                # Save all mouse events on button press
                if self.params['saveMouseState'].val in ['on click']:
                    buff.writeIndentedLines(mouseCode)
                elif self.params['clickable'].val and self.params['saveMouseState'].val in ['on valid click']:
                    code = (
                        "if gotValidClick:\n"
                    )
                    buff.writeIndentedLines(code)
                    buff.setIndentLevel(+1, relative=True)
                    buff.writeIndentedLines(mouseCode)
                    buff.setIndentLevel(-1, relative=True)
                # also write code about clicked objects if needed.
                if self.params['clickable'].val:
                    # does valid response end the trial?
                    if forceEnd == 'valid click':
                        code = ("if gotValidClick:\n"
                                "    continueRoutine = False  # end routine on response\n")
                        buff.writeIndentedLines(code)
                # does any response end the trial?
                if forceEnd == 'any click':
                    code = ("\n"
                            "continueRoutine = False  # end routine on response\n")
                    buff.writeIndentedLines(code)
                elif forceEnd == 'correct click':
                    code = (
                        "if %(name)s.corr and %(name)s.corr[-1]:\n"
                        "    continueRoutine = False  # end routine on response\n"
                    )
                else:
                    pass # forceEnd == 'never'
                # 'if' statement of the time test and button check
            buff.setIndentLevel(-dedentAtEnd, relative=True)

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame"""
        forceEnd = self.params['forceEndRoutineOnPress'].val

        # get a clock for timing
        timeRelative = self.params['timeRelativeTo'].val.lower()
        if timeRelative == 'experiment':
            self.clockStr = 'globalClock'
        elif timeRelative in ['routine', 'mouse onset']:
            self.clockStr = '%s.mouseClock' % self.params['name'].val
        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveMouseState'].val not in
                ['every frame', 'on click', 'on valid click'] and forceEnd == 'never'):
            return
        buff.writeIndented("// *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        self.writeStartTestCodeJS(buff)
        code = "%(name)s.status = PsychoJS.Status.STARTED;\n"
        if self.params['timeRelativeTo'].val.lower() == 'mouse onset':
            code += "%(name)s.mouseClock.reset();\n" % self.params

        if self.params['newClicksOnly']:
            code += (
                "prevButtonState = %(name)s.getPressed();"
                "  // if button is down already this ISN'T a new click\n")
        else:
            code += (
                "prevButtonState = [0, 0, 0];"
                "  // if now button is down we will treat as 'new' click\n")
        code+=("}\n")
        buff.writeIndentedLines(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCodeJS(buff)
            buff.writeIndented("%(name)s.status = PsychoJS.Status.FINISHED;\n"
                               "  }\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # if STARTED and not FINISHED!
        code = ("if (%(name)s.status === PsychoJS.Status.STARTED) {  "
                "// only update if started and not finished!\n")
        buff.writeIndented(code % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        # write param checking code
        if (self.params['saveMouseState'].val in ['on click', 'on valid click'] or forceEnd in ['any click', 'correct click', 'valid click']):
            code = ("_mouseButtons = %(name)s.getPressed();\n")
            buff.writeIndentedLines(code % self.params)
            # buff.setIndentLevel(1, relative=True)
            # dedentAtEnd += 1
            code = "if (!_mouseButtons.every( (e,i,) => (e == prevButtonState[i]) )) { // button state changed?\n"
            buff.writeIndented(code)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1
            buff.writeIndented("prevButtonState = _mouseButtons;\n")
            code = ("if (_mouseButtons.reduce( (e, acc) => (e+acc) ) > 0) { // state changed to a new click\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1

        elif self.params['saveMouseState'].val == 'every frame':
            code = "_mouseButtons = %(name)s.getPressed();\n" % self.params
            buff.writeIndented(code)

        # also write code about clicked objects if needed.
        if self.params['clickable'].val:
            self._writeClickableObjectsCodeJS(buff)

        # also write code about correct objects if needed
        if self.params['storeCorrect']:
            self._writeCorrectAnsCodeJS(buff)

        if self.params['saveMouseState'].val in ['on click', 'on valid click', 'every frame']:
            storeCode = (
                    "_mouseXYs = %(name)s.getPos();\n"
                    "%(name)s.x.push(_mouseXYs[0]);\n"
                    "%(name)s.y.push(_mouseXYs[1]);\n"
                    "%(name)s.leftButton.push(_mouseButtons[0]);\n"
                    "%(name)s.midButton.push(_mouseButtons[1]);\n"
                    "%(name)s.rightButton.push(_mouseButtons[2]);\n"
                    % self.params
            )
            storeCode += ("%s.time.push(%s.getTime());\n" % (self.params['name'], self.clockStr))
            if self.params['clickable'].val and self.params['saveMouseState'].val in ['on valid click']:
                code = (
                    "if (gotValidClick === true) { \n"
                )
                buff.writeIndentedLines(code)
                buff.setIndentLevel(+1, relative=True)
                buff.writeIndentedLines(storeCode)
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code)
            else:
                buff.writeIndentedLines(storeCode)

            # does the response end the trial?
        if forceEnd == 'any click':
            code = ("// end routine on response\n"
                    "continueRoutine = false;\n")
            buff.writeIndentedLines(code)

        elif forceEnd == 'valid click':
            code = ("if (gotValidClick === true) { // end routine on response\n"
                    "  continueRoutine = false;\n"
                    "}\n")
            buff.writeIndentedLines(code)
        else:
            pass  # forceEnd == 'never'
        for thisDedent in range(dedentAtEnd):
            buff.setIndentLevel(-1, relative=True)
            buff.writeIndentedLines('}')

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        # do this because the param itself is not a string!
        store = self.params['saveMouseState'].val
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type == 'StairHandler':
            code = ("# NB PsychoPy doesn't handle a 'correct answer' for "
                    "mouse events so doesn't know how to handle mouse with "
                    "StairHandler\n")
        else:
            code = ("# store data for %s (%s)\n" %
                    (currLoop.params['name'], currLoop.type))

        buff.writeIndentedLines(code)

        if store == 'final':  # for the o
            # buff.writeIndented("# get info about the %(name)s\n"
            # %(self.params))
            code = ("x, y = {name}.getPos()\n"
                    "buttons = {name}.getPressed()\n").format(name=self.params['name'])
            # also write code about clicked objects if needed.
            buff.writeIndentedLines(code)
            if self.params['clickable'].val:
                buff.writeIndented("if sum(buttons):\n")
                buff.setIndentLevel(+1, relative=True)
                self._writeClickableObjectsCode(buff)
                buff.setIndentLevel(-1, relative=True)

            if currLoop.type != 'StairHandler':
                code = (
                    "{loopName}.addData('{name}.x', x)\n" 
                    "{loopName}.addData('{name}.y', y)\n" 
                    "{loopName}.addData('{name}.leftButton', buttons[0])\n" 
                    "{loopName}.addData('{name}.midButton', buttons[1])\n" 
                    "{loopName}.addData('{name}.rightButton', buttons[2])\n"
                )
                if self.params['storeCorrect']:
                    code += (
                        "{loopName}.addData('{name}.corr', {name}.corr)\n"
                    )
                buff.writeIndentedLines(
                    code.format(loopName=currLoop.params['name'],
                                name=name))
                # then add `trials.addData('mouse.clicked_name',.....)`
                if self.params['clickable'].val:
                    for paramName in self._clickableParamsList:
                        code = (
                            "if len({name}.clicked_{param}):\n"
                            "    {loopName}.addData('{name}.clicked_{param}', " 
                            "{name}.clicked_{param}[0])\n"
                        )
                        buff.writeIndentedLines(
                            code.format(loopName=currLoop.params['name'],
                                        name=name,
                                        param=paramName))

        elif store != 'never':
            # buff.writeIndented("# save %(name)s data\n" %(self.params))
            mouseDataProps = ['x', 'y', 'leftButton', 'midButton',
                             'rightButton', 'time']
            if self.params['storeCorrect']:
                mouseDataProps += ['corr']
            # possibly add clicked params if we have clickable objects
            if self.params['clickable'].val:
                for paramName in self._clickableParamsList:
                    mouseDataProps.append("clicked_{}".format(paramName))
            # use that set of properties to create set of addData commands
            for property in mouseDataProps:
                if store == 'every frame' or forceEnd == "never":
                    code = ("%s.addData('%s.%s', %s.%s)\n" %
                            (currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)
                else:
                    # we only had one click so don't return a list
                    code = ("%s.addData('%s.%s', %s.%s)\n" %
                            (currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)


        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

    def writeRoutineEndCodeJS(self, buff):
        """Write code at end of routine"""
        # some shortcuts
        name = self.params['name']
        # do this because the param itself is not a string!
        store = self.params['saveMouseState'].val
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type == 'StairHandler':
            code = ("/*NB PsychoPy doesn't handle a 'correct answer' for "
                    "mouse events so doesn't know how to handle mouse with "
                    "StairHandler*/\n")
        else:
            code = ("// store data for %s (%s)\n" %
                    (currLoop.params['name'], currLoop.type))

        buff.writeIndentedLines(code)

        if store == 'final':

            code = ("_mouseXYs = {name}.getPos();\n"
                    "_mouseButtons = {name}.getPressed();\n")

            if currLoop.type != 'StairHandler':
                code += (
                    "psychoJS.experiment.addData('{name}.x', _mouseXYs[0]);\n"
                    "psychoJS.experiment.addData('{name}.y', _mouseXYs[1]);\n"
                    "psychoJS.experiment.addData('{name}.leftButton', _mouseButtons[0]);\n"
                    "psychoJS.experiment.addData('{name}.midButton', _mouseButtons[1]);\n"
                    "psychoJS.experiment.addData('{name}.rightButton', _mouseButtons[2]);\n"
                )
                if self.params['storeCorrect']:
                    code += (
                        "psychoJS.experiment.addData('{name}.corr', {name}.corr);\n"
                    )
                buff.writeIndentedLines(code.format(name=name))

                # For clicked objects...
                if self.params['clickable'].val:
                    for paramName in self._clickableParamsList:
                        code = (
                            "if ({name}.clicked_{param}.length > 0) {{\n"
                            "  psychoJS.experiment.addData('{name}.clicked_{param}', "
                            "{name}.clicked_{param}[0]);}}\n".format(name=name,
                                                                     param=paramName))
                        buff.writeIndentedLines(code)

        elif store != 'never':
            # buff.writeIndented("# save %(name)s data\n" %(self.params))
            mouseDataProps = ['x', 'y', 'leftButton', 'midButton',
                              'rightButton', 'time']
            if self.params['storeCorrect']:
                mouseDataProps += ['corr']
            # possibly add clicked params if we have clickable objects
            if self.params['clickable'].val:
                for paramName in self._clickableParamsList:
                    mouseDataProps.append("clicked_{}".format(paramName))
            # use that set of properties to create set of addData commands
            for property in mouseDataProps:
                if store == 'every frame' or forceEnd in ["never", "correct click"]:
                    code = ("psychoJS.experiment.addData('%s.%s', %s.%s);\n" %
                            (name, property, name, property))
                    buff.writeIndented(code)
                else:
                    # we only had one click so don't return a list
                    code = ("if (%s.%s) {"
                            "  psychoJS.experiment.addData('%s.%s', %s.%s[0])};\n"
                            % (name, property, name, property, name, property))
                    buff.writeIndented(code)
            buff.writeIndentedLines("\n")
