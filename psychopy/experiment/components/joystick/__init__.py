#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.experiment import valid_var_re
from psychopy.experiment import CodeGenerationException, valid_var_re
from psychopy.localization import _localized as __localized
_localized = __localized.copy()
import re

# only use _localized values for label values, nothing functional:
_localized.update({'saveJoystickState': _translate('Save joystick state'),
                   'forceEndRoutineOnPress': _translate('End Routine on press'),
                   'timeRelativeTo': _translate('Time relative to'),
                   'Clickable stimuli': _translate('Clickable stimuli'),
                   'Store params for clicked': _translate('Store params for clicked'),
                   'deviceNumber': _translate('Device number'),
                   'allowedButtons': _translate('Allowed Buttons')})


class JoystickComponent(BaseComponent):
    """An event class for checking the joystick location and buttons
    at given timepoints
    """
    categories = ['Responses']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'joystick.png'
    tooltip = _translate('Joystick: query joystick position and buttons')

    def __init__(self, exp, parentName, name='joystick',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 save='final', forceEndRoutineOnPress="any click",
                 timeRelativeTo='joystick onset', deviceNumber='0', allowedButtons=''):
        super(JoystickComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Joystick'
        self.url = "https://www.psychopy.org/builder/components/joystick.html"
        self.exp.requirePsychopyLibs(['event'])
        self.categories = ['Inputs']

        self.order += ['forceEndRoutine',  # Basic tab
                       'saveJoystickState', 'timeRelativeTo', 'clickable', 'saveParamsClickable', 'allowedButtons',  # Data tab
                       'deviceNumber',  # Hardware tab
                       ]
        # params
        msg = _translate(
            "How often should the joystick state (x,y,buttons) be stored? "
            "On every video frame, every click or just at the end of the "
            "Routine?")
        self.params['saveJoystickState'] = Param(
            save, valType='str', inputType="choice", categ='Data',
            allowedVals=['final', 'on click', 'every frame', 'never'],
            hint=msg, direct=False,
            label=_localized['saveJoystickState'])

        msg = _translate("Should a button press force the end of the routine"
                         " (e.g end the trial)?")
        if forceEndRoutineOnPress is True:
            forceEndRoutineOnPress = 'any click'
        elif forceEndRoutineOnPress is False:
            forceEndRoutineOnPress = 'never'
        self.params['forceEndRoutineOnPress'] = Param(
            forceEndRoutineOnPress, valType='str', inputType="choice", categ='Basic',
            allowedVals=['never', 'any click', 'valid click'],
            updates='constant',
            hint=msg, direct=False,
            label=_localized['forceEndRoutineOnPress'])

        msg = _translate("What should the values of joystick.time should be "
                         "relative to?")
        self.params['timeRelativeTo'] = Param(
            timeRelativeTo, valType='str', inputType="choice", categ='Data',
            allowedVals=['joystick onset', 'experiment', 'routine'],
            updates='constant', direct=False,
            hint=msg,
            label=_localized['timeRelativeTo'])

        msg = _translate('A comma-separated list of your stimulus names that '
                         'can be "clicked" by the participant. '
                         'e.g. target, foil'
                         )
        self.params['clickable'] = Param(
            '', valType='list', inputType="single", categ='Data',
            updates='constant',
            hint=msg,
            label=_localized['Clickable stimuli'])

        msg = _translate('The params (e.g. name, text), for which you want '
                         'to store the current value, for the stimulus that was'
                         '"clicked" by the joystick. Make sure that all the '
                         'clickable objects have all these params.'
                         )
        self.params['saveParamsClickable'] = Param(
            'name,', valType='list', inputType="single", categ='Data',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_localized['Store params for clicked'])

        msg = _translate('Device number, if you have multiple devices which'
                         ' one do you want (0, 1, 2...)')

        self.params['deviceNumber'] = Param(
            deviceNumber, valType='int', inputType="single", allowedTypes=[], categ='Hardware',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['deviceNumber'])

        msg = _translate('Buttons to be read (blank for any) numbers separated by '
                         'commas')

        self.params['allowedButtons'] = Param(
            allowedButtons, valType='list', inputType="single", allowedTypes=[], categ='Data',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['allowedButtons'])

    @property
    def _clickableParamsList(self):
        # convert clickableParams (str) to a list
        params = self.params['saveParamsClickable'].val
        paramsList = re.findall(r"[\w']+", params)
        return paramsList or ['name']

    def _writeClickableObjectsCode(self, buff):
        # code to check if clickable objects were clicked
        code = (
            "# check if the joystick was inside our 'clickable' objects\n"
            "gotValidClick = False;\n"
            "for obj in [%(clickable)s]:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("if obj.contains(%(name)s.getX(), %(name)s.getY()):\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("gotValidClick = True\n")
        buff.writeIndentedLines(code % self.params)

        code = ''
        for paramName in self._clickableParamsList:
            code += "%s.clicked_%s.append(obj.%s)\n" %(self.params['name'],
                                                     paramName, paramName)
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-2, relative=True)

    def writeStartCode(self, buff):
        code = ("from psychopy.hardware import joystick as joysticklib  "
                "# joystick/gamepad accsss\n"
                "from psychopy.experiment.components.joystick import "
                "virtualJoystick as virtualjoysticklib\n")
        buff.writeIndentedLines(code % self.params)

    def writeInitCode(self, buff):
        code = ("x, y = [None, None]\n"
                "%(name)s = type('', (), {})() "
                "# Create an object to use as a name space\n"
                "%(name)s.device = None\n"
                "%(name)s.device_number = %(deviceNumber)s\n"
                "%(name)s.joystickClock = core.Clock()\n"
                "%(name)s.xFactor = 1\n"
                "%(name)s.yFactor = 1\n"
                "\n"
                "try:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("numJoysticks = joysticklib.getNumJoysticks()\n"
                "if numJoysticks > 0:\n")
        buff.writeIndentedLines(code % self.params)

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

        code = ("if win.units == 'height':\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        code = ("%(name)s.xFactor = 0.5 * win.size[0]/win.size[1]\n"
                "%(name)s.yFactor = 0.5\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        buff.setIndentLevel(-1, relative=True)

        code = ("else:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("%(name)s.device = virtualjoysticklib.VirtualJoystick(%(deviceNumber)s)\n"
                "logging.warning(\"joystick_{}: "
                "Using keyboard+mouse emulation 'ctrl' "
                "+ 'Alt' + digit.\".format(%(name)s.device_number))\n")
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
                "%(name)s.numButtons = %(name)s.device.getNumButtons()\n"
                "%(name)s.getNumButtons = %(name)s.device.getNumButtons\n"
                "%(name)s.getAllButtons = %(name)s.device.getAllButtons\n"
                "%(name)s.getX = lambda: %(name)s.xFactor * %(name)s.device.getX()\n"
                "%(name)s.getY = lambda: %(name)s.yFactor * %(name)s.device.getY()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.writeIndented("\n")


    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """

        code = ("{name}.oldButtonState = {name}.device.getAllButtons()[:]\n")
        buff.writeIndentedLines(code.format(**self.params))

        allowedButtons = self.params['allowedButtons'].val.strip()
        allowedButtonsIsVar = (valid_var_re.match(str(allowedButtons)) and not
                               allowedButtons == 'None')

        if allowedButtonsIsVar:
            # if it looks like a variable, check that the variable is suitable
            # to eval at run-time
            code = ("# AllowedKeys looks like a variable named `{0}`\n"
                    #"print(\"{0}<{{}}> type:{{}}\".format({0}, type({0})))\n"
                    "if not type({0}) in [list, tuple, np.ndarray]:\n")
            buff.writeIndentedLines(code.format(allowedButtons))

            buff.setIndentLevel(1, relative=True)
            code = ("if type({0}) == int:\n")
            buff.writeIndentedLines(code.format(allowedButtons))

            buff.setIndentLevel(1, relative=True)
            code = ("{0} = [{0}]\n")
            buff.writeIndentedLines(code.format(allowedButtons))

            buff.setIndentLevel(-1, relative=True)
            code = ("elif not (isinstance({0}, str) "
                    "or isinstance({0}, unicode)):\n")
            buff.writeIndentedLines(code.format(allowedButtons))

            buff.setIndentLevel(1, relative=True)
            code = ("logging.error('AllowedKeys variable `{0}` is "
                    "not string- or list-like.')\n"
                    "core.quit()\n")
            buff.writeIndentedLines(code.format(allowedButtons))

            buff.setIndentLevel(-1, relative=True)
            code = ("elif not ',' in {0}: {0} = eval(({0},))\n"
                    "else:  {0} = eval({0})\n")
            buff.writeIndentedLines(code.format(allowedButtons))
            buff.setIndentLevel(-1, relative=True)

        # do we need a list of buttons? (variable case is already handled)
        if allowedButtons in [None, "none", "None", "", "[]", "()"]:
            buttonList=[]
        elif not allowedButtonsIsVar:
            try:
                buttonList = eval(allowedButtons)
            except Exception:
                raise CodeGenerationException(
                    self.params["name"], "Allowed buttons list is invalid.")
            if type(buttonList) == tuple:
                buttonList = list(buttonList)
            elif isinstance(buttonList, int):  # a single string/key
                buttonList = [buttonList]
            #print("buttonList={}".format(buttonList))

        if allowedButtonsIsVar:
            code = ("{name}.activeButtons={0}\n")
            buff.writeIndentedLines(code.format(allowedButtons, **self.params))
        else:
            if buttonList == []:
                code = ("{name}.activeButtons=[i for i in range({name}.numButtons)]")
                buff.writeIndentedLines(code.format(allowedButtons, **self.params))
            else:
                code = ("{name}.activeButtons={0}")
                buff.writeIndentedLines(code.format(buttonList, **self.params))

        # create some lists to store recorded values positions and events if
        # we need more than one
        code = ("# setup some python lists for storing info about the "
                "%(name)s\n")

        if self.params['saveJoystickState'].val in ['every frame', 'on click']:
            code += ("%(name)s.x = []\n"
                     "%(name)s.y = []\n"
                     "%(name)s.buttonLogs = [[] for i in range(%(name)s.numButtons)]\n"
                     "%(name)s.time = []\n")
        if self.params['clickable'].val:
            for clickableObjParam in self._clickableParamsList:
                code += "%(name)s.clicked_{} = []\n".format(clickableObjParam)

        code += "gotValidClick = False  # until a click is received\n"

        if self.params['timeRelativeTo'].val.lower() == 'routine':
            code += "%(name)s.joystickClock.reset()\n"

        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        # some shortcuts
        forceEnd = self.params['forceEndRoutineOnPress'].val
        #routineClockName = self.exp.flow._currentRoutine._clockName

        # get a clock for timing
        timeRelative = self.params['timeRelativeTo'].val.lower()
        if timeRelative == 'experiment':
            self.clockStr = 'globalClock'
        elif timeRelative in ['routine', 'joystick onset']:
            self.clockStr = '%s.joystickClock' % self.params['name'].val

        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveJoystickState'].val not in
                ['every frame', 'on click'] and forceEnd == 'never'):
            return

        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        code = ("{name}.status = STARTED\n")
        if self.params['timeRelativeTo'].val.lower() == 'joystick onset':
            code += "{name}.joystickClock.reset()\n"
        buff.writeIndentedLines(code.format(**self.params))
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-2, relative=True)

        # if STARTED and not FINISHED!
        code = ("if %(name)s.status == STARTED:  "
                "# only update if started and not finished!\n") % self.params
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        # write param checking code
        if (self.params['saveJoystickState'].val == 'on click'
            or forceEnd in ['any click', 'valid click']):
            code = ("{name}.newButtonState = {name}.getAllButtons()[:]\n"
                    "if {name}.newButtonState != {name}.oldButtonState: "
                    "# New button press\n")
            buff.writeIndentedLines(code.format(**self.params))
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1

            code = ("{name}.pressedButtons = [i for i in range({name}.numButtons) "
                    "if {name}.newButtonState[i] and not {name}.oldButtonState[i]]\n"
                    "{name}.releasedButtons = [i for i in range({name}.numButtons) "
                    "if not {name}.newButtonState[i] and {name}.oldButtonState[i]]\n"
                    "{name}.newPressedButtons = [i for i in {name}.activeButtons "
                    "if i in {name}.pressedButtons]\n"
                    "{name}.oldButtonState = {name}.newButtonState\n"
                    "{name}.buttons = {name}.newPressedButtons\n"
                    #"print({name}.pressedButtons)\n"
                    #"print({name}.newPressedButtons)\n"
                    "[logging.data(\"joystick_{{}}_button: {{}}, pos=({{:1.4f}},{{:1.4f}})\".format("
                    "{name}.device_number, i, {name}.getX(), {name}.getY())) for i in {name}.pressedButtons]\n"
            )
            buff.writeIndentedLines(code.format(**self.params))

            code = ("if len({name}.buttons) > 0:  # state changed to a new click\n")
            buff.writeIndentedLines(code.format(**self.params))
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1

        elif self.params['saveJoystickState'].val == 'every frame':
            code = ("{name}.newButtonState = {name}.getAllButtons()[:]\n"
                    "{name}.pressedButtons = [i for i in range({name}.numButtons) "
                    "if {name}.newButtonState[i] and not {name}.oldButtonState[i]]\n"
                    "{name}.releasedButtons = [i for i in range({name}.numButtons) "
                    "if not {name}.newButtonState[i] and {name}.oldButtonState[i]]\n"
                    "{name}.newPressedButtons = [i for i in {name}.activeButtons "
                    "if i in {name}.pressedButtons]\n"
                    "{name}.buttons = {name}.newPressedButtons\n"
                    #"print({name}.pressedButtons)\n"
                    #"print({name}.newPressedButtons)\n"
                    "[logging.data(\"joystick_{{}}_button: {{}}, pos=({{:1.4f}},{{:1.4f}})\".format("
                    "{name}.device_number, i, {name}.getX(), {name}.getY()) for i in {name}.pressedButtons]\n"
            )
            buff.writeIndentedLines(code.format(**self.params))

        # only do this if buttons were pressed
        if self.params['saveJoystickState'].val in ['on click', 'every frame']:
            code = ("x, y = %(name)s.getX(), %(name)s.getY()\n"
                    #"print(\"x:{} y:{}\".format(x,y))\n"
                    "%(name)s.x.append(x)\n"
                    "%(name)s.y.append(y)\n"
                    "[%(name)s.buttonLogs[i].append(int(%(name)s.newButtonState[i])) "
                    "for i in %(name)s.activeButtons]\n")
            buff.writeIndentedLines(code % self.params)

            code = ("{name}.time.append({clockStr}.getTime())\n")
            buff.writeIndentedLines(
                code.format(name=self.params['name'],clockStr=self.clockStr))

        # also write code about clicked objects if needed.
        if self.params['clickable'].val:
            self._writeClickableObjectsCode(buff)

        # does the response end the trial?
        if forceEnd == 'any click':
            code = ("# abort routine on response\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code)

        elif forceEnd == 'valid click':
            code = ("if gotValidClick:  # abort routine on response\n")
            buff.writeIndentedLines(code)
            buff.setIndentLevel(1, relative=True)
            code = ("continueRoutine = False\n")
            buff.writeIndentedLines(code)
            buff.setIndentLevel(-1, relative=True)
        else:
            pass # forceEnd == 'never'
        # 'if' statement of the time test and button check
        buff.setIndentLevel(-dedentAtEnd, relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        # do this because the param itself is not a string!
        store = self.params['saveJoystickState'].val
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type == 'StairHandler':
            code = ("# NB PsychoPy doesn't handle a 'correct answer' for "
                    "joystick events so doesn't know how to handle joystick with "
                    "StairHandler\n")
        else:
            code = ("# store data for %s (%s)\n" %
                    (currLoop.params['name'], currLoop.type))

        buff.writeIndentedLines(code)

        if store == 'final':
            # write code about clicked objects if needed.
            buff.writeIndentedLines(code)
            if self.params['clickable'].val:
                code = ("if len({name}.buttons) > 0:\n")
                buff.writeIndentedLines(code.format(**self.params))
                buff.setIndentLevel(+1, relative=True)
                self._writeClickableObjectsCode(buff)
                buff.setIndentLevel(-1, relative=True)

            code = ("x, y = {name}.getX(), {name}.getY()\n"
                    "{name}.newButtonState = {name}.getAllButtons()[:]\n"
                    "{name}.pressedState = [{name}.newButtonState[i] "
                    "for i in range({name}.numButtons)]\n"
                    "{name}.time = {clock}.getTime()\n")

            buff.writeIndentedLines(
                code.format(name=self.params['name'], clock=self.clockStr))

            if currLoop.type != 'StairHandler':
                code = (
                    "{loopName}.addData('{joystickName}.x', x)\n"
                    "{loopName}.addData('{joystickName}.y', y)\n"
                    "[{loopName}.addData('{joystickName}.button_{{0}}'.format(i), "
                    "int({joystickName}.pressedState[i])) "
                    "for i in {joystickName}.activeButtons]\n"
                    "{loopName}.addData('{joystickName}.time', {joystickName}.time)\n"
                )
                buff.writeIndentedLines(
                    code.format(loopName=currLoop.params['name'],
                                joystickName=name))
                # then add `trials.addData('joystick.clicked_name',.....)`
                if self.params['clickable'].val:
                    for paramName in self._clickableParamsList:
                        code = (
                            "if len({joystickName}.clicked_{param}):\n"
                            "    {loopName}.addData('{joystickName}.clicked_{param}', "
                            "{joystickName}.clicked_{param}[0])\n"
                        )
                        buff.writeIndentedLines(
                            code.format(loopName=currLoop.params['name'],
                                        joystickName=name,
                                        param=paramName))

        elif store != 'never':
            joystickDataProps = ['x', 'y', 'time']

            # possibly add clicked params if we have clickable objects
            if self.params['clickable'].val:
                for paramName in self._clickableParamsList:
                    joystickDataProps.append("clicked_{}".format(paramName))
            # use that set of properties to create set of addData commands
            for property in joystickDataProps:
                if store == 'every frame' or forceEnd == "never":
                    code = ("%s.addData('%s.%s', %s.%s)\n" %
                            (currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)
                else:
                    # we only had one click so don't return a list
                    code = ("if len(%s.%s): %s.addData('%s.%s', %s.%s[0])\n" %
                            (name, property,
                             currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)

            if store == 'every frame' or forceEnd == "never":
                code = ("[{0}.addData('{name}.button_{{0}}'.format(i), "
                        "{name}.buttonLogs[i]) for i in {name}.activeButtons "
                        "if len({name}.buttonLogs[i])]\n")
            else:
                code = ("[{0}.addData('{name}.button_{{0}}'.format(i), "
                        "{name}.buttonLogs[i][0]) for i in {name}.activeButtons "
                        "if len({name}.buttonLogs[i])]\n")
            buff.writeIndented(code.format(currLoop.params['name'], **self.params))

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)
