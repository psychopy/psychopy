# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from .._base import BaseComponent, Param, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'eyeCalibrate.png')
tooltip = _translate('EyeTrackerCalibrate: Start eye tracker calibration procedure.')


class EyeCalibrateComponent(BaseComponent):
    """A class used to start the calibration process of an ioHub supported
    Eye Tracker."""
    categories = ['Stimuli']

    def __init__(self, exp, parentName, name='calibrates',
                 startEstim='', durationEstim=''):
        self.type = 'EyeCalibrate'
        self.url = "http://www.psychopy.org/builder/components/eyeCalibrate.html"
        self.parentName = parentName
        self.exp = exp  # so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['iohub'])
        # params
        self.params = {}
        self.order = []  # first param after the name

        # TODO: Determine proper params for EyeCalibrate component.
        # standard params (can ignore)
        msg = _translate(
            "Name of this component (alpha-numeric or _, no spaces)")
        self.params['name'] = Param(
            name, valType='code', allowedTypes=[],
            hint=msg,
            label="Name")

        msg = _translate("(Optional) expected start (s), purely for "
                         "representing in the timeline")
        self.params['startEstim'] = Param(
            startEstim, valType='code', allowedTypes=[],
            hint=msg)

        msg = _translate("(Optional) expected duration (s), purely for "
                         "representing in the timeline")
        self.params['durationEstim'] = Param(
            durationEstim, valType='code', allowedTypes=[],
            hint=msg)

    def writePreWindowCode(self, buff):
        pass

    def writeInitCode(self, buff):
        pass

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        pass

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        pass

    def writeRoutineEndCode(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        pass
