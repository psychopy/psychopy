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

    def __init__(self, exp, parentName, name='eye_calibrate'):#,
        #         startEstim='0', durationEstim='30'):
        self.type = 'EyeCalibrate'
        self.url = "http://www.psychopy.org/builder/components/eyeCalibrate.html"
        self.parentName = parentName
        self.exp = exp  # so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['iohub'])
        # params
        self.params = {}
        self.order = []  # first param after the name

        # standard params (can ignore)
        msg = _translate(
            "Name of this component (alpha-numeric or _, no spaces)")
        self.params['name'] = Param(
            name, valType='code', allowedTypes=[],
            hint=msg,
            label="Name")

        # SS: I am getting following error when tryuing to add component
        # to a routine when I have the following component param code
        # so for now, just not having any params for this component.
        #
        #msg = _translate("(Optional) expected start (s), purely for "
        #                 "representing in the timeline")
        #self.params['startEstim'] = Param(
        #    startEstim, valType='code', allowedTypes=[],
        #    hint=msg)
        #msg = _translate("(Optional) expected duration (s), purely for "
        #                 "representing in the timeline")
        #self.params['durationEstim'] = Param(
        #    durationEstim, valType='code', allowedTypes=[],
        #    hint=msg)

    def writePreWindowCode(self, buff):
        # SS: If I try an write the code in writeInitCode() here instead,
        # it is not output to script. Really should be in here, prior to win
        # being created.
        pass

    def writeInitCode(self, buff):
        code = ("if 'iohub_eyetracker' not in locals():\n"
                "    try:\n"
                "        iohub_eyetracker = iohub_server.devices.tracker\n"
                "    except Exception:\n"
                "        # No eye tracker config found in iohub_config.yaml\n"
                "        from psychopy.gui.qtgui import criticalDlg, hideWindow\n"
                "        hideWindow(win)\n"
                "        dlg_ = criticalDlg('ioHub Eye Tracker Not Configured',\n"
                "                    'No Eye Tracker config found in the the '\n"
                "                    'ioHub settings file:\\n'\n"
                "                    %(ioHubConfigFile)s\n"
                "                    '\\n\\n'\n"
                "                    'Update the ioHub settings file with an '\n"
                "                    'eye tracker configuration\\nor remove '\n"
                "                    'all Eye Tracker Components from your project.'\n"
                "                    '\\n\\nPress OK to exit demo.')\n"
                "        iohub_server.quit()\n"
                "        core.quit()\n"%self.exp.settings.params)
        buff.writeIndentedLines(code)


    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        # Start the eye tracker setup / calibration procedure.
        buff.writeIndentedLines("if iohub_eyetracker:\n"
                                "    import psychopy.gui.qtgui as qtgui\n"
                                "    qtgui.hideWindow(win)\n"
                                "    iohub_eyetracker.runSetupProcedure()\n"
                                "    qtgui.showWindow(win)\n\n")

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        pass

    def writeRoutineEndCode(self, buff):
        pass

    def writeExperimentEndCode(self, buff):
        pass
