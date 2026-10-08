#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import (
    BaseDeviceComponent, Param, getInitVals, _translate)
from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment import CodeGenerationException, valid_var_re
import re


class JoystickComponent(BaseDeviceComponent):
    """An event class for checking the joystick location and buttons
    at given timepoints
    """
    categories = ['Responses']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'joystick.png'
    iconSVG = Path(__file__).parent / 'JoystickComponent.svg'
    tooltip = _translate('Joystick: query joystick position and buttons')
    deviceClasses = ['psychopy.hardware.joystick.JoystickDevice']

    def __init__(self, exp, parentName, name='joystick',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 save='final', forceEndRoutineOnPress="any click",
                 timeRelativeTo='joystick onset', deviceLabel='',
                 deviceNumber='0', allowedButtons='', disabled=False):
        BaseDeviceComponent.__init__(
            self, exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            deviceLabel=deviceLabel, disabled=disabled)

        self.type = 'Joystick'
        self.url = "https://www.psychopy.org/builder/components/joystick.html"
        # `event` is kept available because Code Components in existing
        # experiments commonly assume this Component imported it
        self.exp.requirePsychopyLibs(['event'])
        self.exp.requireImport(
            importName='Joystick', importFrom='psychopy.hardware.joystick')
        self.categories = ['Inputs']

        self.order += ['forceEndRoutineOnPress',  # Basic tab
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
            label=_translate("Save joystick state"))

        msg = _translate("Should a button press force the end of the Routine"
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
            label=_translate("End Routine on press"))

        msg = _translate("What should the values of joystick.time be "
                         "relative to?")
        self.params['timeRelativeTo'] = Param(
            timeRelativeTo, valType='str', inputType="choice", categ='Data',
            allowedVals=['joystick onset', 'experiment', 'routine'],
            updates='constant', direct=False,
            hint=msg,
            label=_translate("Time relative to"))

        msg = _translate('A comma-separated list of your stimulus names that '
                         'can be "clicked" by the participant. '
                         'e.g. target, foil'
                         )
        self.params['clickable'] = Param(
            '', valType='list', inputType="single", categ='Data',
            updates='constant',
            hint=msg,
            label=_translate("Clickable stimuli"))

        msg = _translate('The params (e.g. name, text), for which you want '
                         'to store the current value, for the stimulus that was'
                         '"clicked" by the joystick. Make sure that all the '
                         'clickable objects have all these params.'
                         )
        self.params['saveParamsClickable'] = Param(
            'name,', valType='list', inputType="single", categ='Data',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Store params for clicked"))

        msg = _translate(
            "Deprecated: index of the joystick to use when no Device is named "
            "above. Prefer naming a device in the Device field, which lets the "
            "same joystick be shared between Components.")

        self.params['deviceNumber'] = Param(
            deviceNumber, valType='int', inputType="single", allowedTypes=[], categ="Device",
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Device number (deprecated)"))
        # only relevant while no named device is chosen. NB: this param is
        # deliberately NOT a legacyParam -- legacyParams drop the stored value
        # on load, and there's no way to migrate an index into another
        # machine's device config, so an experiment would silently change which
        # joystick it read from.
        self.depends.append({
            "dependsOn": "deviceLabel",
            "condition": "==''",
            "param": "deviceNumber",
            "true": "show",
            "false": "hide",
        })

        msg = _translate('Buttons to be read (blank for any) numbers separated by '
                         'commas')

        self.params['allowedButtons'] = Param(
            allowedButtons, valType='list', inputType="single", allowedTypes=[], categ='Data',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Allowed buttons"))

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

    @property
    def clockStr(self):
        """Name of the clock this Component times against.

        A property rather than something `writeFrameCode` assigns, so
        `writeRoutineEndCode` doesn't depend on the order the two are called in.
        """
        if self.params['timeRelativeTo'].val.lower() == 'experiment':
            return 'globalClock'
        return "%s.joystickClock" % self.params['name'].val

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        code = (
            "# set up joystick %(name)s\n"
            "%(name)s = Joystick(\n"
            "    device=%(deviceLabel)s,\n"
            "    index=%(deviceNumber)s,\n"
            "    win=win,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """

        code = ("{name}.clearData()\n"
                "{name}.oldButtonState = {name}.getAllButtons()[:]\n")
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
            code = ("elif not isinstance({0}, str):\n")
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

        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveJoystickState'].val not in
                ['every frame', 'on click'] and forceEnd == 'never'):
            return

        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            code = ("{name}.status = STARTED\n")
            if self.params['timeRelativeTo'].val.lower() == 'joystick onset':
                code += "{name}.joystickClock.reset()\n"
            buff.writeIndentedLines(code.format(**self.params))
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

        # if STARTED and not FINISHED!
        code = ("if %(name)s.status == STARTED:  "
                "# only update if started and not finished!\n") % self.params
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        code = ("%(name)s.poll()  # refresh the joystick state\n") % self.params
        buff.writeIndented(code)

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
                    "{name}.device_number, i, {name}.getX(), {name}.getY())) for i in {name}.pressedButtons]\n"
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
        if store == 'never':
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
            if self.params['clickable'].val:
                code = ("if len({name}.buttons) > 0:\n")
                buff.writeIndentedLines(code.format(**self.params))
                buff.setIndentLevel(+1, relative=True)
                self._writeClickableObjectsCode(buff)
                buff.setIndentLevel(-1, relative=True)

            code = ("{name}.poll()\n"
                    "x, y = {name}.getX(), {name}.getY()\n"
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


class JoystickDeviceBackend(DeviceBackend):
    """Joystick or gamepad, read through pyglet, GLFW, or keyboard emulation.

    There is one backend rather than one per input library because they all map
    onto the same device class -- which library to use is a property of the
    device being configured, so it is a parameter here rather than a separate
    backend. Registering several backends against one device class would also
    enumerate the same joysticks once per backend in Device Manager.
    """
    backendLabel = _translate("Joystick / Gamepad")
    deviceClass = "psychopy.hardware.joystick.JoystickDevice"
    icon = "light/joystick.png"

    def getParams(self):
        order = ['backend', 'deadzone']
        params = {
            # NB: DeviceBackend.__init__ stores the discovered profile before
            # calling this, so the backend a device was found under becomes its
            # default. `.get` covers the empty profile used for templates.
            'backend': Param(
                self.profile.get('backend', 'pyglet'),
                valType='str', inputType='choice', categ="Device",
                allowedVals=['pyglet', 'glfw', 'virtual'],
                allowedLabels=[
                    _translate("Pyglet"),
                    _translate("GLFW"),
                    _translate("Virtual (keyboard + mouse)"),
                ],
                label=_translate("Input library"),
                hint=_translate(
                    "Library used to read this device. Pyglet needs an open "
                    "pyglet Window which is being flipped; GLFW works with any "
                    "window backend, or none; Virtual emulates a joystick "
                    "using 'ctrl' + 'alt' + a number key and the mouse.")),
            'deadzone': Param(
                0, valType='num', inputType='single', categ="Device",
                label=_translate("Deadzone"),
                hint=_translate(
                    "Axis values whose magnitude falls below this are reported "
                    "as zero, which suppresses drift on an idle stick.")),
        }

        return params, order

    def writeDeviceCode(self, buff):
        self.writeBaseDeviceCode(buff, close=False)
        code = (
            "    backend=%(backend)s,\n"
            "    deadzone=%(deadzone)s,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % self.params)


JoystickComponent.registerBackend(JoystickDeviceBackend)
