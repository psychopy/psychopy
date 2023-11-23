from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, getInitVals
from psychopy.localization import _translate


class ButtonBoxBackend:
    def __init_subclass__(cls, key, label=None):
        """
        Initialise a new backend for ButtonBoxComponent.

        Parameters
        ----------
        key : str
            Name of this backend - will be used in allowedVals for the deviceBackend parameter of ButtonBoxComponent.
            This will be used for indexing, so shouldn't be localized (translated)!
        label : str
            Label for this backend - will be used in allowedLabels for the deviceBackend parameter of
            ButtonBoxComponent.
        """
        # if not given a label, use key
        if label is None:
            label = key
        # store key and label in class
        cls.key = key
        cls.label = label
        # add class to list of backends for ButtonBoxComponent
        ButtonBoxComponent.backends.append(cls)

    def getParams(self):
        """
        Get parameters from this backend to add to each new instance of ButtonBoxComponent

        Returns
        -------
        dict[str:Param]
            Dict of Param objects, which will be added to any Button Box Component's params, along
            with a dependency to only show them when this backend is selected
        list[str]
            List of param names, defining the order in which params should appear
        list[dict[str:str]]
            List of dependency dicts, defining any additional dependencies required by this backend
        """
        raise NotImplementedError()

    def addRequirements(self):
        """
        Add any required module/package imports for this backend
        """
        raise NotImplementedError()

    def writeDeviceCode(self, buff):
        raise NotImplementedError()


class ButtonBoxComponent(BaseComponent):
    """

    """
    categories = ['Responses']  # which section(s) in the components panel
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'buttonBox.png'
    tooltip = _translate('Button Box: Get input from a button box')
    # list of backends - starts with generic serial, plugins (lke psychopy-bbtk or psychopy-cedrus) will add to this
    backends = []

    def __init__(
            self, exp, parentName,
            # basic
            name='buttonBox', nButtons=1,
            startType='time (s)', startVal=0.0,
            stopType='duration (s)', stopVal=1.0,
            startEstim='', durationEstim='',
            forceEndRoutine=True,
            # device
            deviceName="",
            deviceBackend="serial",
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
        BaseComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            disabled=disabled
        )

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
            "deviceName",
            "deviceBackend",
        ]
        self.params['deviceName'] = Param(
            deviceName, valType="str", inputType="single", categ="Device",
            label=_translate("Device name"),
            hint=_translate(
                "A name to refer to this Component's associated hardware device by. If using the "
                "same device for multiple components, be sure to use the same name here."
            )
        )
        def getBackendVals():
            return [getattr(cls, 'key', cls.__name__) for cls in self.backends]
        def getBackendLabels():
            return [getattr(cls, 'label', cls.__name__) for cls in self.backends]
        self.params['deviceBackend'] = Param(
            deviceBackend, valType="str", inputType="choice", categ="Device",
            allowedVals=getBackendVals,
            allowedLabels=getBackendLabels,
            label=_translate("Device backend"),
            hint=_translate(
                "What kind of button box is it? What package/plugin should be used to talk to it?"
            ),
            direct=False
        )

    def loadBackends(self):
        from psychopy.plugins import activatePlugins
        activatePlugins()
        # add params from backends
        for backend in self.backends:
            # get params using backend's method
            params, order = backend.getParams(self)
            # add order
            self.order.extend(order)
            # add any params
            for key, param in params.items():
                if key in self.params:
                    # if this param already exists (i.e. from saved data), get the saved val
                    param.val = self.params[key].val
                    param.updates = self.params[key].updates
                # add param
                self.params[key] = param

            # add dependencies so that backend params are only shown for this backend
            for name in params:
                self.depends.append(
                    {
                        "dependsOn": "deviceBackend",  # if...
                        "condition": f"== '{backend.key}'",  # meets...
                        "param": name,  # then...
                        "true": "show",  # should...
                        "false": "hide",  # otherwise...
                    }
                )
            # add requirements
            backend.addRequirements(self)

    def writeDeviceCode(self, buff):
        # write init code from backend
        for backend in self.backends:
            if backend.key == self.params['deviceBackend']:
                backend.writeDeviceCode(self, buff)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # code to create object
        code = (
            "%(name)s = ButtonBox(\n"
            "    device=%(deviceName)s\n"
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
                "for resp in %(name)s.getResponses(\n"
                "    state=%(registerOn)s, channel=%(allowedButtons)s, clear=True\n"
                "):\n"
                "    %(name)s.buttons.append(resp.channel)\n"
                "    %(name)s.times.append(resp.t)\n"
            )
            # include code to get correct
            if self.params['storeCorrect']:
                code += (
                    "    %(name)s.corr.append(resp.channel in %(correctAns)s)\n"
                )
            buff.writeIndentedLines(code % params)
            # code to end Routine
            if self.params['forceEndRoutine']:
                code = (
                    "# end Routine if %(name)s got valid response\n"
                    "if len(%(name)s.buttons):\n"
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
        )
        if self.params['store'] == "all":
            code += (
                "thisExp.addData('%(name)s.buttons', %(name)s.buttons)\n"
                "thisExp.addData('%(name)s.times', %(name)s.times)\n"
                "thisExp.addData('%(name)s.corr', %(name)s.corr)\n"
            )
        elif self.params['store'] == "last":
            code += (
                "if len(%(name)s.buttons):\n"
                "    thisExp.addData('%(name)s.buttons', %(name)s.buttons[-1])\n"
                "if len(%(name)s.times):\n"
                "    thisExp.addData('%(name)s.times', %(name)s.times[-1])\n"
                "if len(%(name)s.corr):\n"
                "    thisExp.addData('%(name)s.corr', %(name)s.corr[-1])\n"
            )
        elif self.params['store'] == "first":
            code += (
                "if len(%(name)s.buttons):\n"
                "    thisExp.addData('%(name)s.buttons', %(name)s.buttons[0])\n"
                "if len(%(name)s.times):\n"
                "    thisExp.addData('%(name)s.times', %(name)s.times[0])\n"
                "if len(%(name)s.corr):\n"
                "    thisExp.addData('%(name)s.corr', %(name)s.corr[0])\n"
            )
        buff.writeIndentedLines(code % params)


class KeyboardButtonBoxBackend(ButtonBoxBackend, key="keyboard", label=_translate("Keyboard")):
    """
    Adds a basic serial connection backend for ButtonBoxComponent, as well as acting as an example for implementing
    other ButtonBoxBackends.
    """
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
            "    deviceName=%(deviceName)s,\n"
            "    buttons=%(kbButtonAliases)s,\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)
