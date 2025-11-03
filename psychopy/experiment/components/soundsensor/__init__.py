from pathlib import Path
from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.components import BaseComponent, BaseDeviceComponent, Param, getInitVals
from psychopy.localization import _translate


class SoundSensorComponent(BaseDeviceComponent):
    """
    Component for getting button presses from a button box device.
    """
    categories = ['Responses']  # which section(s) in the components panel
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'soundsensor.png'
    iconSVG = Path(__file__).parent / 'SoundSensorComponent.svg'
    tooltip = _translate('Voice Key: Get input from a microphone as simple true/false values')
    beta = True
    legacyParams = [
        # old device setup params, no longer needed as this is handled by DeviceManager
        "deviceBackend",
        "meMicrophone",
        "meThreshold",
        "meRange",
        "meSamplingWindow",
    ]

    def __init__(
            self, exp, parentName,
            # basic
            name='soundSensor',
            startType='time (s)', startVal=0.0,
            stopType='duration (s)', stopVal=1.0,
            startEstim='', durationEstim='',
            forceEndRoutine=True,
            # device
            deviceLabel="",
            deviceBackend="microphone",
            # data
            registerOn=True,
            store='first',
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
        self.type = "SoundSensor"

        self.exp.requireImport(
            importName="SoundSensor",
            importFrom="psychopy.hardware.soundsensor"
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
                "When should the response be registered? When the sound starts, or when it stops?"
            ),
            label=_translate("Register button press on...")
        )
        self.params['store'] = Param(
            store, valType='str', inputType="choice", categ='Data',
            allowedVals=['last', 'first', 'all', 'nothing'],
            allowedLabels=[_translate("Last response"), _translate("First response"), _translate(
                "All responses"), _translate("Nothing")],
            updates='constant', direct=False,
            hint=_translate(
                "Choose which (if any) responses to store at the end of a trial"
            ),
            label=_translate("Store"))
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
            correctAns, valType='code', inputType="single", categ='Data',
            hint=_translate(
                "What is the 'correct' response (True/False)? Might be helpful to add a correctAns column and use "
                "$correctAns to compare to the response. "
            ),
            label=_translate("Correct answer"), direct=False)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # code to create object
        code = (
            "%(name)s = SoundSensor(\n"
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
                "    state=%(registerOn)s, clear=True\n"
                "):\n"
            )
            if self.params['store'] == "all":
                # if storing all, append
                code += (
                "    %(name)s.times.append(_thisResp.t)\n"
                )
                # include code to get correct
                if self.params['storeCorrect']:
                    code += (
                "    if bool(_thisResp.value) is bool(%(correctAns)s):\n"
                "        %(name)s.corr.append(1)\n"
                "    else:\n"
                "        %(name)s.corr.append(0)\n"
                    )
            elif self.params['store'] == "last":
                # if storing last, replace
                code += (
                "    %(name)s.times = _thisResp.t\n"
                )
                # include code to get correct
                if self.params['storeCorrect']:
                    code += (
                "    if bool(_thisResp.value) is bool(%(correctAns)s):\n"
                "        %(name)s.corr = 1\n"
                "    else:\n"
                "        %(name)s.corr = 0\n"
                    )
            elif self.params['store'] == "first":
                # if storing first, replace but only if empty
                code += (
                "    if not %(name)s.buttons:\n"
                "        %(name)s.times = _thisResp.t\n"
                )
                # include code to get correct
                if self.params['storeCorrect']:
                    code += (
                "        if bool(_thisResp.value) is bool(%(correctAns)s):\n"
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
                    "# end Routine if %(name)s got response\n"
                    "if %(name)s.times:\n"
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
            "thisExp.addData('%(name)s.times', %(name)s.times)\n"
            "thisExp.addData('%(name)s.corr', %(name)s.corr)\n"
        )
        buff.writeIndentedLines(code % params)
        

class MicrophoneSoundSensorBackend(DeviceBackend):
    backendLabel = "Microphone Sound Sensor"
    deviceClass = "psychopy.hardware.soundsensor.MicrophoneSoundSensor"
    icon = "light/soundsensor.png"

    def __init__(self, profile):
        # init parent class
        DeviceBackend.__init__(self, profile)
        # define order
        order = [
            "meMicrophone",
            "meThreshold",
            "meRange",
            "meSamplingWindow",
        ]
        # define params
        self.params['threshold'] = Param(
            0.5, valType="code", inputType="single",
            updates="constant", allowedUpdates=None,
            label=_translate("Threshold (0-1)"),
            hint=_translate(
                "Threshold volume (0 for min value in dB range, 1 for max value) above which to "
                "register a sound sensor response"
            )
        )
        self.params['dbRange'] = Param(
            (0, 1), valType="list", inputType="single",
            updates="constant", allowedUpdates=None,
            label=_translate("Decibel range"),
            hint=_translate(
                "What kind of values (dB) would you expect to receive from this device? In other "
                "words, how many dB does a threshold of 0 and 1 correspond to?"
            )
        )
        self.params['samplingWindow'] = Param(
            0.03, valType="code", inputType="single",
            updates="constant", allowedUpdates=None,
            label=_translate("Sampling window (s)"),
            hint=_translate(
                "How many seconds to average volume readings across? Bigger windows are less "
                "precise, but also less subject to random noise."
            )
        )
    
    def writeDeviceCode(self, buff):
        """
        Code to setup a device with this backend.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        # write basic code
        self.writeBaseDeviceCode(buff, close=False)
        # add exclusive param and close
        code = (
            "    threshold=%(threshold)s, \n"
            "    dbRange=%(dbRange)s, \n"
            "    samplingWindow=%(samplingWindow)s,\n"
            ")\n"
        )
        buff.writeIndentedLines(code % self.params)


# register backend with Component
SoundSensorComponent.registerBackend(MicrophoneSoundSensorBackend)
