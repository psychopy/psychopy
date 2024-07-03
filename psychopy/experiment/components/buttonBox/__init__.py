from pathlib import Path
from psychopy.experiment.components import BaseComponent, BaseDeviceComponent, Param, getInitVals
from psychopy.experiment.plugins import PluginDevicesMixin, DeviceBackend
from psychopy.localization import _translate


class ButtonBoxComponent(BaseDeviceComponent, PluginDevicesMixin):
    """
    Component for getting button presses from a button box device.
    """
    categories = ['Responses']  # which section(s) in the components panel
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'buttonBox.png'
    tooltip = _translate('Button Box: Get input from a button box')
    beta = True

    def __init__(
            self, exp, parentName,
            # basic
            name='buttonBox',
            startType='time (s)', startVal=0.0,
            stopType='duration (s)', stopVal=1.0,
            startEstim='', durationEstim='',
            forceEndRoutine=True,
            # device
            deviceLabel="",
            deviceBackend="keyboard",
            # data
            registerOn=True,
            store='first',
            allowedButtons="",
            storeCorrect=False,
            correctAns="",
            # testing
            disabled=False,
    ):
        # initialise base class
        BaseDeviceComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            deviceLabel=deviceLabel,
            disabled=disabled
        )
        self.type = "ButtonBox"

        self.exp.requireImport(
            importName="ButtonBox",
            importFrom="psychopy.hardware.button"
        )

        # --- Basic params ---
        self.order += [
            "forceEndRoutine"
        ]
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', inputType="bool", categ='Basic',
            hint=_translate(
                "Should a response force the end of the Routine (e.g end the trial)?"
            ),
            label=_translate("Force end of Routine"))

        # --- Data params ---
        self.order += [
            "registerOn",
            "store",
            "allowedButtons",
            "storeCorrect",
            "correctAns",
        ]
        self.params['registerOn'] = Param(
            registerOn, valType='code', inputType='choice', categ='Data',
            allowedVals=[True, False],
            allowedLabels=[_translate("Press"), _translate("Release")],
            hint=_translate(
                "When should the button press be registered? As soon as pressed, or when released?"
            ),
            label=_translate("Register button press on...")
        )
        self.params['store'] = Param(
            store, valType='str', inputType="choice", categ='Data',
            allowedVals=['last', 'first', 'all', 'nothing'],
            allowedLabels=[_translate("Last button"), _translate("First button"), _translate(
                "All buttons"), _translate("Nothing")],
            updates='constant', direct=False,
            hint=_translate(
                "Choose which (if any) responses to store at the end of a trial"
            ),
            label=_translate("Store"))
        self.params['allowedButtons'] = Param(
            allowedButtons, valType='list', inputType="single", categ='Data',
            hint=_translate(
                "A comma-separated list of button indices (should be whole numbers), leave blank "
                "to listen for all buttons."
            ),
            label=_translate("Allowed buttons"))
        self.params['storeCorrect'] = Param(
            storeCorrect, valType='bool', inputType="bool", categ='Data',
            updates='constant',
            hint=_translate(
                "Do you want to save the response as correct/incorrect?"
            ),
            label=_translate("Store correct"))
        self.depends.append(
            {
                "dependsOn": "storeCorrect",  # if...
                "condition": f"== True",  # meets...
                "param": "correctAns",  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            }
        )
        self.params['correctAns'] = Param(
            correctAns, valType='list', inputType="single", categ='Data',
            hint=_translate(
                "What is the 'correct' key? Might be helpful to add a correctAns column and use "
                "$correctAns to compare to the key press. "
            ),
            label=_translate("Correct answer"), direct=False)

        # --- Device params ---
        self.order += [
            "deviceBackend",
        ]

        self.params['deviceBackend'] = Param(
            deviceBackend, valType="str", inputType="choice", categ="Device",
            allowedVals=self.getBackendKeys,
            allowedLabels=self.getBackendLabels,
            label=_translate("Device backend"),
            hint=_translate(
                "What kind of button box is it? What package/plugin should be used to talk to it?"
            ),
            direct=False
        )

        # add params for any backends
        self.loadBackends()

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # code to create object
        code = (
            "%(name)s = ButtonBox(\n"
            "    device=%(deviceLabel)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeRoutineStartCode(self, buff):
        # choose a clock to sync to according to component's params
        if "syncScreenRefresh" in self.params and self.params['syncScreenRefresh']:
            clockStr = ""
        else:
            clockStr = "clock=routineTimer"
        # sync component start/stop timers with validator clocks
        code = (
            f"# synchronise device clock for %(name)s with Routine timer\n"
            f"%(name)s.resetTimer({clockStr})\n"
        )
        buff.writeIndentedLines(code % self.params)
        # clear keys
        code = (
            "# clear %(name)s button presses\n"
            "%(name)s.buttons = []\n"
            "%(name)s.times = []\n"
            "%(name)s.corr = []\n"
            )
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        params = self.params
        code = (
            "\n"
            "# *%(name)s* updates\n"
        )
        buff.writeIndentedLines(code % params)
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            # dispatch and clear messages
            code = (
                "# clear any messages from before starting\n"
                "%(name)s.responses = []\n"
                "%(name)s.clearResponses()\n"
            )
            buff.writeIndentedLines(code % params)
            # to get out of the if statement
            buff.setIndentLevel(-indented, relative=True)

        # test for started (will update parameters each frame as needed)
        indented = self.writeActiveTestCode(buff)
        if indented:
            # write code to get messages
            code = (
                "# ask for messages from %(name)s device this frame\n"
                "for _thisResp in %(name)s.getResponses(\n"
                "    state=%(registerOn)s, channel=%(allowedButtons)s, clear=True\n"
                "):\n"
            )
            if self.params['store'] == "all":
                # if storing all, append
                code += (
                "    %(name)s.buttons.append(_thisResp.channel)\n"
                "    %(name)s.times.append(_thisResp.t)\n"
                )
                # include code to get correct
                if self.params['storeCorrect']:
                    code += (
                "    if _thisResp.channel in %(correctAns)s or _thisResp.channel == %(correctAns)s:\n"
                "        %(name)s.corr.append(1)\n"
                "    else:\n"
                "        %(name)s.corr.append(0)\n"
                    )
            elif self.params['store'] == "last":
                # if storing last, replace
                code += (
                "    %(name)s.buttons = _thisResp.channel\n"
                "    %(name)s.times = _thisResp.t\n"
                )
                # include code to get correct
                if self.params['storeCorrect']:
                    code += (
                "    if _thisResp.channel in %(correctAns)s or _thisResp.channel == %(correctAns)s:\n"
                "        %(name)s.corr = 1\n"
                "    else:\n"
                "        %(name)s.corr = 0\n"
                    )
            elif self.params['store'] == "first":
                # if storing first, replace but only if empty
                code += (
                "    if not %(name)s.buttons:\n"
                "        %(name)s.buttons = _thisResp.channel\n"
                "        %(name)s.times = _thisResp.t\n"
                )
                # include code to get correct
                if self.params['storeCorrect']:
                    code += (
                "        if _thisResp.channel in %(correctAns)s or _thisResp.channel == %(correctAns)s:\n"
                "            %(name)s.corr = 1\n"
                "        else:\n"
                "            %(name)s.corr = 0\n"
                    )
            else:
                code = "pass\n"

            buff.writeIndentedLines(code % params)
            # code to end Routine
            if self.params['forceEndRoutine']:
                code = (
                    "# end Routine if %(name)s got valid response\n"
                    "if %(name)s.buttons or %(name)s.buttons == 0:\n"
                    "    continueRoutine = False\n"
                )
                buff.writeIndentedLines(code % params)

            # to get out of the if statement
            buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        if indented:
            # to get out of the if statement
            buff.setIndentLevel(-indented, relative=True)

    def writeRoutineEndCode(self, buff):
        BaseComponent.writeRoutineEndCode(self, buff)
        params = self.params

        # write code to save responses
        code = (
            "# store data from %(name)s\n"
            "thisExp.addData('%(name)s.buttons', %(name)s.buttons)\n"
            "thisExp.addData('%(name)s.times', %(name)s.times)\n"
            "thisExp.addData('%(name)s.corr', %(name)s.corr)\n"
        )
        buff.writeIndentedLines(code % params)
        

class KeyboardButtonBoxBackend(DeviceBackend):
    """
    Adds a basic keyboard emulation backend for ButtonBoxComponent, as well as acting as an example
    for implementing other ButtonBoxBackends.
    """

    key = "keyboard"
    label = _translate("Keyboard")
    component = ButtonBoxComponent
    deviceClasses = ['psychopy.hardware.button.KeyboardButtonBox']

    def getParams(self: ButtonBoxComponent):
        # define order
        order = [
            "kbButtonAliases",
        ]
        # define params
        params = {}
        params['kbButtonAliases'] = Param(
            "'q', 'w', 'e'", valType="list", inputType="single", categ="Device",
            label=_translate("Buttons"),
            hint=_translate(
                "Keys to treat as buttons (in order of what button index you want them to be). "
                "Must be the same length as the number of buttons."
            )
        )

        return params, order

    def addRequirements(self):
        # no requirements needed - so just return
        return

    def writeDeviceCode(self: ButtonBoxComponent, buff):
        # get inits
        inits = getInitVals(self.params)
        # make ButtonGroup object
        code = (
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy.hardware.button.KeyboardButtonBox',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    buttons=%(kbButtonAliases)s,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)
