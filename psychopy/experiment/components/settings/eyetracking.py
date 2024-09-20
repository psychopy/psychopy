from psychopy.localization import _translate
from psychopy.experiment import Param


knownEyetrackerBackends = {}


class EyetrackerBackend:
    # label to display in Builder
    label = None
    # key to index this backend by
    key = None

    # information about this backend's needs (for raising alerts and etc.)
    needsFullscreen = True
    needsCalibration = True
    
    def __init_subclass__(cls):
        # skip any classes with no key
        if cls.key is None:
            return
        # append to global variable
        global knownEyetrackerBackends
        knownEyetrackerBackends[cls.key] = cls
    
    @classmethod
    def getParams(cls):
        """
        Method to get the params to be added to SettingsComponent by this backend.
        
        Returns
        -------
        dict[str: Param]
            Dict of params to add, by name
        list[str]
            List determining order of params (by name)
        """
        params = {}
        order = []

        return params, order
    
    @classmethod
    def writeDeviceCode(cls, inits, buff):
        """
        Overload this method in a subclass to control the code that's written in the `setupDevices` 
        function of Builder experiments when using this backend.

        Parameters
        ----------
        comp : dict[str: psychopy.experiment.Param]
            Dict of params from the Settings Component
        buff : io.StringIO
            String buffer to write to (i.e. the experiment-in-progress)
        """
        raise NotImplementedError()


class MouseGazeEyetrackerBackend(EyetrackerBackend):
    label = "MouseGaze"
    key = "eyetracker.hw.mouse.EyeTracker"

    needsFullscreen = False
    needsCalibration = False

    @classmethod
    def getParams(cls):
        # define order
        order = [
            "mgMove",
            "mgBlink",
            "mgSaccade",
        ]
        # define params
        params = {}
        params['mgMove'] = Param(
            "CONTINUOUS", valType='str', inputType="choice",
            allowedVals=['CONTINUOUS', 'LEFT_BUTTON', 'MIDDLE_BUTTON', 'RIGHT_BUTTON'],
            hint=_translate("Mouse button to press for eye movement."),
            label=_translate("Move button"), categ="Eyetracking"
        )
        params['mgBlink'] = Param(
            "MIDDLE_BUTTON", valType='list', inputType="multiChoice",
            allowedVals=['LEFT_BUTTON', 'MIDDLE_BUTTON', 'RIGHT_BUTTON'],
            hint=_translate("Mouse button to press for a blink."),
            label=_translate("Blink button"), categ="Eyetracking"
        )
        params['mgSaccade'] = Param(
            0.5, valType='num', inputType="single",
            hint=_translate("Visual degree threshold for Saccade event creation."),
            label=_translate("Saccade threshold"), categ="Eyetracking"
        )

        return params, order

    @classmethod
    def writeDeviceCode(cls, inits, buff):
        code = (
            "ioConfig[%(eyetracker)s] = {\n"
            "    'name': 'tracker',\n"
            "    'controls': {\n"
            "        'move': [%(mgMove)s],\n"
            "        'blink':%(mgBlink)s,\n"
            "        'saccade_threshold': %(mgSaccade)s,\n"
            "    },\n"
            "}\n"
        )
        buff.writeIndentedLines(code % inits)
