#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from copy import deepcopy
from pathlib import Path
from xml.etree.ElementTree import Element
import re
from psychopy import logging, plugins
from psychopy.experiment.components import Param, _translate
from psychopy.experiment.routines.eyetracker_calibrate import EyetrackerCalibrationRoutine
import psychopy.tools.versionchooser as versions
from psychopy.experiment import utils as exputils
from psychopy.monitors import Monitor
from psychopy.iohub import util as ioUtil
from psychopy.alerts import alert
from psychopy.tools.filetools import genDelimiter

# for creating html output folders:
import shutil
import hashlib
from pkg_resources import parse_version
import ast  # for doing literal eval to convert '["a","b"]' to a list

try:
    import wx.__version__
    wx_version = wx.__version__
except ModuleNotFoundError:
    wx_version = "4.2"  # this won't matter if not in an app anyway!


def readTextFile(relPath):
    fullPath = os.path.join(Path(__file__).parent, relPath)
    with open(fullPath, "r") as f:
        txt = f.read()
    return txt


# used when writing scripts and in namespace:
_numpyImports = ['sin', 'cos', 'tan', 'log', 'log10', 'pi', 'average',
                 'sqrt', 'std', 'deg2rad', 'rad2deg', 'linspace', 'asarray']
_numpyRandomImports = ['random', 'randint', 'normal', 'shuffle', 'choice as randchoice']

# this is not a standard component - it will appear on toolbar not in
# components panel

# only use _localized values for label values, nothing functional:
_localized = {'expName': _translate("Experiment name"),
              'Show info dlg':  _translate("Show info dialog"),
              'Enable Escape':  _translate("Enable Escape key"),
              'Experiment info':  _translate("Experiment info"),
              'Data filename':  _translate("Data filename"),
              'Data file delimiter':  _translate("Data file delimiter"),
              'Full-screen window':  _translate("Full-screen window"),
              'Window size (pixels)':  _translate("Window size (pixels)"),
              'Screen': _translate('Screen'),
              'Monitor':  _translate("Monitor"),
              'color': _translate("Color"),
              'colorSpace':  _translate("Color space"),
              'Units':  _translate("Units"),
              'blendMode':   _translate("Blend mode"),
              'Show mouse':  _translate("Show mouse"),
              'Save log file':  _translate("Save log file"),
              'Save wide csv file':
                  _translate("Save csv file (trial-by-trial)"),
              'Save csv file': _translate("Save csv file (summaries)"),
              'Save excel file':  _translate("Save excel file"),
              'Save psydat file':  _translate("Save psydat file"),
              'logging level': _translate("Logging level"),
              'Use version': _translate("Use PsychoPy version"),
              'Completed URL': _translate("Completed URL"),
              'Incomplete URL': _translate("Incomplete URL"),
              'Output path': _translate("Output path"),
              'Additional Resources': _translate("Additional Resources"),
              'JS libs': _translate("JS libs"),
              'Force stereo': _translate("Force stereo"),
              'Export HTML': _translate("Export HTML")}
ioDeviceMap = dict(ioUtil.getDeviceNames())
ioDeviceMap['None'] = ""

# Keyboard backend options
keyboardBackendMap = {
    "ioHub": "iohub",
    "PsychToolbox": "ptb",
    "Pyglet": "event"
}


# # customize the Proj ID Param class to
# class ProjIDParam(Param):
#     @property
#     def allowedVals(self):
#         from psychopy.app.projects import catalog
#         allowed = list(catalog.keys())
#         # always allow the current val!
#         if self.val not in allowed:
#             allowed.append(self.val)
#         # always allow blank (None)
#         if '' not in allowed:
#             allowed.append('')
#         return allowed
#     @allowedVals.setter
#     def allowedVals(self, allowed):
#         pass


class SettingsComponent:
    """This component stores general info about how to run the experiment
    """
    categories = ['Custom']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'settings.png'
    tooltip = _translate("Edit settings for this experiment")

    def __init__(self, parentName, exp, expName='', fullScr=True,
                 winSize=(1024, 768), screen=1, monitor='testMonitor', winBackend='pyglet',
                 showMouse=False, saveLogFile=True, showExpInfo=True,
                 expInfo="{'participant':'f\"{randint(0, 999999):06.0f}\"', 'session':'001'}",
                 units='height', logging='exp',
                 color='$[0,0,0]', colorSpace='rgb', enableEscape=True,
                 backgroundImg="", backgroundFit="none",
                 blendMode='avg',
                 sortColumns="time", colPriority={'thisRow.t': "priority.CRITICAL", 'expName': "priority.LOW"},
                 saveXLSXFile=False, saveCSVFile=False, saveHDF5File=False,
                 saveWideCSVFile=True, savePsydatFile=True,
                 savedDataFolder='', savedDataDelim='auto',
                 useVersion='',
                 eyetracker="None",
                 mgMove='CONTINUOUS', mgBlink='MIDDLE_BUTTON', mgSaccade=0.5,
                 gpAddress='127.0.0.1', gpPort=4242,
                 elModel='EYELINK 1000 DESKTOP', elSimMode=False, elSampleRate=1000, elTrackEyes="RIGHT_EYE",
                 elLiveFiltering="FILTER_LEVEL_OFF", elDataFiltering="FILTER_LEVEL_2",
                 elTrackingMode='PUPIL_CR_TRACKING', elPupilMeasure='PUPIL_AREA', elPupilAlgorithm='ELLIPSE_FIT',
                 elAddress='100.1.1.1',
                 tbModel="", tbLicenseFile="", tbSerialNo="", tbSampleRate=60,
                 plPupillometryOnly=False,
                 plSurfaceName="psychopy_iohub_surface",
                 plConfidenceThreshold=0.6,
                 plPupilRemoteAddress="127.0.0.1",
                 plPupilRemotePort=50020,
                 plPupilRemoteTimeoutMs=1000,
                 plPupilCaptureRecordingEnabled=True,
                 plPupilCaptureRecordingLocation="",
                 keyboardBackend="ioHub",
                 filename=None, exportHTML='on Sync', endMessage=''):
        self.type = 'Settings'
        self.exp = exp  # so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual', 'gui'])
        self.parentName = parentName
        self.url = "https://www.psychopy.org/builder/settings.html"
        self._monitor = None

        # if filename is the default value fetch the builder pref for the
        # folder instead
        if filename is None:
            filename = ("u'xxxx/%s_%s_%s' % (expInfo['participant'], expName,"
                        " expInfo['date'])")
        if filename.startswith("u'xxxx"):
            folder = self.exp.prefsBuilder['savedDataFolder'].strip()
            filename = filename.replace("xxxx", folder)

        # params
        self.params = {}
        self.depends = []
        self.order = ['expName', 'Use version', 'Enable Escape',  'Show info dlg', 'Experiment info',  # Basic tab
                      'Audio lib', 'Audio latency priority', "Force stereo",  # Audio tab
                      'HTML path', 'exportHTML', 'Completed URL', 'Incomplete URL', 'End Message', 'Resources',  # Online tab
                      'Monitor', 'Screen', 'Full-screen window', 'Window size (pixels)', 'Show mouse', 'Units', 'color',
                      'colorSpace',  # Screen tab
                      ]
        self.depends = []
        # basic params
        self.params['expName'] = Param(
            expName, valType='str',  inputType="single", allowedTypes=[],
            hint=_translate("Name of the entire experiment (taken by default"
                            " from the filename on save)"),
            label=_translate("Experiment name"))
        self.depends.append(
            {"dependsOn": "Show info dlg",  # must be param name
             "condition": "==True",  # val to check for
             "param": "Experiment info",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        )
        self.params['Show info dlg'] = Param(
            showExpInfo, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Start the experiment with a dialog to set info"
                            " (e.g.participant or condition)"),
            label=_translate("Show info dialog"), categ='Basic')
        self.params['Enable Escape'] = Param(
            enableEscape, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Enable the <esc> key, to allow subjects to quit"
                            " / break out of the experiment"),
            label=_translate("Enable escape key"))
        self.params['Experiment info'] = Param(
            expInfo, valType='code', inputType="dict", categ='Basic',
            allowedLabels=(_translate("Field"), _translate("Default")),
            hint=_translate("The info to present in a dialog box. Right-click"
                            " to check syntax and preview the dialog box."),
            label=_translate("Experiment info"))
        self.params['Use version'] = Param(
            useVersion, valType='str', inputType="choice",
            # search for options locally only by default, otherwise sluggish
            allowedVals=versions._versionFilter(versions.versionOptions(), wx_version)
                        + ['']
                        + versions._versionFilter(versions.availableVersions(), wx_version),
            hint=_translate("The version of PsychoPy to use when running "
                            "the experiment."),
            label=_translate("Use PsychoPy version"), categ='Basic')

        # screen params
        self.params['Full-screen window'] = Param(
            fullScr, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Run the experiment full-screen (recommended)"),
            label=_translate("Full-screen window"), categ='Screen')
        self.params['winBackend'] = Param(
            winBackend, valType='str', inputType="choice", categ="Screen",
            allowedVals=plugins.getWindowBackends(),
            hint=_translate("What Python package should be used behind the scenes for drawing to the window?"),
            label=_translate("Window backend")
        )
        self.params['Window size (pixels)'] = Param(
            winSize, valType='list', inputType="single", allowedTypes=[],
            hint=_translate("Size of window (if not fullscreen)"),
            label=_translate("Window size (pixels)"), categ='Screen')
        self.params['Screen'] = Param(
            screen, valType='num', inputType="spin", allowedTypes=[],
            hint=_translate("Which physical screen to run on (1 or 2)"),
            label=_translate("Screen"), categ='Screen')
        self.params['Monitor'] = Param(
            monitor, valType='str', inputType="single", allowedTypes=[],
            hint=_translate("Name of the monitor (from Monitor Center). Right"
                            "-click to go there, then copy & paste a monitor "
                            "name here."),
            label=_translate("Monitor"), categ="Screen")
        self.params['color'] = Param(
            color, valType='color', inputType="color", allowedTypes=[],
            hint=_translate("Color of the screen (e.g. black, $[1.0,1.0,1.0],"
                            " $variable. Right-click to bring up a "
                            "color-picker.)"),
            label=_translate("Color"), categ='Screen')
        self.params['colorSpace'] = Param(
            colorSpace, valType='str', inputType="choice",
            hint=_translate("Needed if color is defined numerically (see "
                            "PsychoPy documentation on color spaces)"),
            allowedVals=['rgb', 'dkl', 'lms', 'hsv', 'hex'],
            label=_translate("Color space"), categ="Screen")
        self.params['backgroundImg'] = Param(
            backgroundImg, valType="str", inputType="file", categ="Screen",
            hint=_translate("Image file to use as a background (leave blank for no image)"),
            label=_translate("Background image")
        )
        self.params['backgroundFit'] = Param(
            backgroundFit, valType="str", inputType="choice", categ="Screen",
            allowedVals=("none", "cover", "contain", "fill", "scale-down"),
            hint=_translate("How should the background image scale to fit the window size?"),
            label=_translate("Background fit")
        )
        self.params['Units'] = Param(
            units, valType='str', inputType="choice", allowedTypes=[],
            allowedVals=['use prefs', 'deg', 'pix', 'cm', 'norm', 'height',
                         'degFlatPos', 'degFlat'],
            hint=_translate("Units to use for window/stimulus coordinates "
                            "(e.g. cm, pix, deg)"),
            label=_translate("Units"), categ='Screen')
        self.params['blendMode'] = Param(
            blendMode, valType='str', inputType="choice",
            allowedVals=['add', 'avg', 'nofbo'],
            allowedLabels=['add', 'average', 'average (no FBO)'],
            hint=_translate("Should new stimuli be added or averaged with "
                            "the stimuli that have been drawn already"),
            label=_translate("Blend mode"), categ='Screen')
        self.params['Show mouse'] = Param(
            showMouse, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Should the mouse be visible on screen? Only applicable for fullscreen experiments."),
            label=_translate("Show mouse"), categ='Screen')
        # self.depends.append(
        #     {"dependsOn": 'Full-screen window',  # must be param name
        #      "condition": "==True",  # val to check for
        #      "param": 'Show mouse',  # param property to alter
        #      "true": "show",  # what to do with param if condition is True
        #      "false": "hide",  # permitted: hide, show, enable, disable
        #      }
        # )

        # sound params
        self.params['Force stereo'] = Param(
            enableEscape, valType='bool', inputType="bool", allowedTypes=[], categ="Audio",
            hint=_translate("Force audio to stereo (2-channel) output"),
            label=_translate("Force stereo"))
        self.params['Audio lib'] = Param(
            'ptb', valType='str', inputType="choice",
            allowedVals=['ptb', 'pyo', 'sounddevice', 'pygame'],
            hint=_translate("Which Python sound engine do you want to play your sounds?"),
            label=_translate("Audio library"), categ='Audio')

        audioLatencyLabels = [
            '0: ' + _translate('Latency not important'),
            '1: ' + _translate('Share low-latency driver'),
            '2: ' + _translate('Exclusive low-latency'),
            '3: ' + _translate('Aggressive low-latency'),
            '4: ' + _translate('Latency critical'),
        ]
        self.params['Audio latency priority'] = Param(
            '3', valType='str', inputType="choice",
            allowedVals=['0', '1', '2', '3', '4'],
            allowedLabels=audioLatencyLabels,
            hint=_translate("How important is audio latency for you? If essential then you may need to get all your sounds in correct formats."),
            label=_translate("Audio latency priority"), categ='Audio')

        # --- Data params ---
        self.order += [
            "Data filename",
            "Data file delimiter",
            "sortColumns",
            "colPriority",
            "Save excel file",
            "Save log file",
            "Save csv file",
            "Save wide csv file",
            "Save psydat file",
            "Save hdf5 file",
            "logging level"
        ]
        self.params['Data filename'] = Param(
            filename, valType='code', inputType="single", allowedTypes=[],
            hint=_translate("Code to create your custom file name base. Don"
                            "'t give a file extension - this will be added."),
            label=_translate("Data filename"), categ='Data')
        self.params['Data file delimiter'] = Param(
            savedDataDelim, valType='str', inputType="choice",
            allowedVals=['auto', 'comma', 'semicolon', 'tab'],
            hint=_translate("What symbol should the data file use to separate columns? ""Auto"" will select a delimiter automatically from the filename."),
            label=_translate("Data file delimiter"), categ='Data'
        )
        self.params['sortColumns'] = Param(
            sortColumns, valType="str", inputType="choice", categ="Data",
            allowedLabels=[_translate("Alphabetical"), _translate("Priority"), _translate("First added")],
            allowedVals=["alphabetical", "priority", "time"],
            label=_translate("Sort columns by..."),
            hint=_translate(
                "How should data file columns be sorted? Alphabetically, by priority, or simply in the order they were "
                "added?"
            )
        )
        self.params['colPriority'] = Param(
            colPriority, valType="dict", inputType="dict", categ="Data",
            allowedLabels=(_translate("Column"), _translate("Priority")),
            label=_translate("Column priority"),
            hint=_translate(
                "Assign priority values to certain columns. To use predefined values, you can do $priority.HIGH, "
                "$priority.MEDIUM, etc."
            )
        )
        self.params['Save log file'] = Param(
            saveLogFile, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Save a detailed log (more detailed than the "
                            "Excel/csv files) of the entire experiment"),
            label=_translate("Save log file"), categ='Data')
        self.params['Save wide csv file'] = Param(
            saveWideCSVFile, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Save data from loops in comma-separated-value "
                            "(.csv) format for maximum portability"),
            label=_translate("Save csv file (trial-by-trial)"), categ='Data')
        self.params['Save csv file'] = Param(
            saveCSVFile, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Save data from loops in comma-separated-value "
                            "(.csv) format for maximum portability"),
            label=_translate("Save csv file (summaries)"), categ='Data')
        self.params['Save excel file'] = Param(
            saveXLSXFile, valType='bool', inputType="bool", allowedTypes=[],
            hint=_translate("Save data from loops in Excel (.xlsx) format"),
            label=_translate("Save Excel file"), categ='Data')
        self.params['Save psydat file'] = Param(
            savePsydatFile, valType='bool', inputType="bool", allowedVals=[True],
            hint=_translate("Save data from loops in psydat format. This is "
                            "useful for Python programmers to generate "
                            "analysis scripts."),
            label=_translate("Save psydat file"), categ='Data')
        self.params['Save hdf5 file'] = Param(
            saveHDF5File, valType='bool', inputType="bool",
            hint=_translate("Save data from eyetrackers in hdf5 format. This is "
                            "useful for viewing and analyzing complex data in structures."),
            label=_translate("Save hdf5 file"), categ='Data')
        self.params['logging level'] = Param(
            logging, valType='code', inputType="choice",
            allowedVals=['error', 'warning', 'data', 'exp', 'info', 'debug'],
            hint=_translate("How much output do you want in the log files? "
                            "('error' is fewest messages, 'debug' is most)"),
            label=_translate("Logging level"), categ='Data')

        # HTML output params
        # self.params['OSF Project ID'] = ProjIDParam(
        #     '', valType='str', # automatically updates to allow choices
        #     hint=_translate("The ID of this project (e.g. 5bqpc)"),
        #     label="OSF Project ID", categ='Online')
        self.params['HTML path'] = Param(
            '', valType='str', inputType="single", allowedTypes=[],
            hint=_translate("Place the HTML files will be saved locally "),
            label=_translate("Output path"), categ='Online')
        self.params['Resources'] = Param(
            [], valType='list', inputType="fileList", allowedTypes=[],
            hint=_translate("Any additional resources needed"),
            label=_translate("Additional resources"), categ='Online')
        self.params['End Message'] = Param(
            endMessage, valType='str', inputType='single',
            hint=_translate("Message to display to participants upon completing the experiment"),
            label=_translate("End message"), categ='Online')
        self.params['Completed URL'] = Param(
            '', valType='str', inputType="single",
            hint=_translate("Where should participants be redirected after the experiment on completion, e.g.\n"
                            "https://pavlovia.org/surveys/XXXXXX-XXXX-XXXXXXX?tab=0"),
            label=_translate("Completed URL"), categ='Online')
        self.params['Incomplete URL'] = Param(
            '', valType='str', inputType="single",
            hint=_translate("Where participants are redirected if they do not complete the task, e.g.\n"
                            "https://pavlovia.org/surveys/XXXXXX-XXXX-XXXXXXX?tab=0"),
            label=_translate("Incomplete URL"), categ='Online')
        self.params['exportHTML'] = Param(
            exportHTML, valType='str', inputType="choice",
            allowedVals=['on Save', 'on Sync', 'manually'],
            hint=_translate("When to export experiment to the HTML folder."),
            label=_translate("Export HTML"), categ='Online')

        # Eyetracking params
        self.order += ["eyetracker",
                       "gpAddress", "gpPort",
                       "elModel", "elAddress", "elSimMode"]

        # Hide params when not relevant to current eyetracker
        trackerParams = {
            "MouseGaze": ["mgMove", "mgBlink", "mgSaccade"],
            "GazePoint": ["gpAddress", "gpPort"],
            "SR Research Ltd": ["elModel", "elSimMode", "elSampleRate", "elTrackEyes", "elLiveFiltering",
                                "elDataFiltering", "elTrackingMode", "elPupilMeasure", "elPupilAlgorithm",
                                "elAddress"],
            "Tobii Technology": ["tbModel", "tbLicenseFile", "tbSerialNo", "tbSampleRate"],
            "Pupil Labs": ["plPupillometryOnly", "plSurfaceName", "plConfidenceThreshold",
                           "plPupilRemoteAddress", "plPupilRemotePort", "plPupilRemoteTimeoutMs",
                           "plPupilCaptureRecordingEnabled", "plPupilCaptureRecordingLocation"],
        }
        for tracker in trackerParams:
            for depParam in trackerParams[tracker]:
                self.depends.append(
                    {"dependsOn": "eyetracker",  # must be param name
                     "condition": "=='"+tracker+"'",  # val to check for
                     "param": depParam,  # param property to alter
                     "true": "show",  # what to do with param if condition is True
                     "false": "hide",  # permitted: hide, show, enable, disable
                     }
                )
        self.depends.append(
            {"dependsOn": "eyetracker",  # must be param name
             "condition": f" in {list(trackerParams)}",  # val to check for
             "param": "Save hdf5 file",  # param property to alter
             "true": "enable",  # what to do with param if condition is True
             "false": "disable",  # permitted: hide, show, enable, disable
             }
        )

        self.params['eyetracker'] = Param(
            eyetracker, valType='str', inputType="choice",
            allowedVals=list(ioDeviceMap),
            hint=_translate("What kind of eye tracker should PsychoPy use? Select 'MouseGaze' to use "
                            "the mouse to simulate eye movement (for debugging without a tracker connected)"),
            label=_translate("Eyetracker device"), categ="Eyetracking"
        )

        #mousegaze
        self.params['mgMove'] = Param(
            mgMove, valType='str', inputType="choice",
            allowedVals=['CONTINUOUS', 'LEFT_BUTTON', 'MIDDLE_BUTTON', 'RIGHT_BUTTON'],
            hint=_translate("Mouse button to press for eye movement."),
            label=_translate("Move button"), categ="Eyetracking"
        )

        self.params['mgBlink'] = Param(
            mgBlink, valType='list', inputType="multiChoice",
            allowedVals=['LEFT_BUTTON', 'MIDDLE_BUTTON', 'RIGHT_BUTTON'],
            hint=_translate("Mouse button to press for a blink."),
            label=_translate("Blink button"), categ="Eyetracking"
        )

        self.params['mgSaccade'] = Param(
            mgSaccade, valType='num', inputType="single",
            hint=_translate("Visual degree threshold for Saccade event creation."),
            label=_translate("Saccade threshold"), categ="Eyetracking"
        )

        # gazepoint
        self.params['gpAddress'] = Param(
            gpAddress, valType='str', inputType="single",
            hint=_translate("IP Address of the computer running GazePoint Control."),
            label=_translate("GazePoint IP address"), categ="Eyetracking"
        )

        self.params['gpPort'] = Param(
            gpPort, valType='num', inputType="single",
            hint=_translate("Port of the GazePoint Control server. Usually 4242."),
            label=_translate("GazePoint port"), categ="Eyetracking"
        )
        # eyelink
        self.params['elModel'] = Param(
            elModel, valType='str', inputType="choice",
            allowedVals=['EYELINK 1000 DESKTOP', 'EYELINK 1000 TOWER', 'EYELINK 1000 REMOTE',
                         'EYELINK 1000 LONG RANGE'],
            hint=_translate("Eye tracker model."),
            label=_translate("Model name"), categ="Eyetracking"
        )

        self.params['elSimMode'] = Param(
            elSimMode, valType='bool', inputType="bool",
            hint=_translate("Set the EyeLink to run in mouse simulation mode."),
            label=_translate("Mouse simulation mode"), categ="Eyetracking"
        )

        self.params['elSampleRate'] = Param(
            elSampleRate, valType='num', inputType="choice",
            allowedVals=['250', '500', '1000', '2000'],
            hint=_translate("Eye tracker sampling rate."),
            label=_translate("Sampling rate"), categ="Eyetracking"
        )

        self.params['elTrackEyes'] = Param(
            elTrackEyes, valType='str', inputType="choice",
            allowedVals=['LEFT_EYE', 'RIGHT_EYE', 'BOTH'],
            hint=_translate("Select with eye(s) to track."),
            label=_translate("Track eyes"), categ="Eyetracking"
        )

        self.params['elLiveFiltering'] = Param(
            elLiveFiltering, valType='str', inputType="choice",
            allowedVals=['FILTER_LEVEL_OFF', 'FILTER_LEVEL_1', 'FILTER_LEVEL_2'],
            hint=_translate("Filter eye sample data live, as it is streamed to the driving device. "
                            "This may reduce the sampling speed."),
            label=_translate("Live sample filtering"), categ="Eyetracking"
        )

        self.params['elDataFiltering'] = Param(
            elDataFiltering, valType='str', inputType="choice",
            allowedVals=['FILTER_LEVEL_OFF', 'FILTER_LEVEL_1', 'FILTER_LEVEL_2'],
            hint=_translate("Filter eye sample data when it is saved to the output file. This will "
                            "not affect the sampling speed."),
            label=_translate("Saved sample filtering"), categ="Eyetracking"
        )

        self.params['elTrackingMode'] = Param(
            elTrackingMode, valType='str', inputType="choice",
            allowedVals=['PUPIL_CR_TRACKING', 'PUPIL_ONLY_TRACKING'],
            hint=_translate("Track Pupil-CR or Pupil only."),
            label=_translate("Pupil tracking mode"), categ="Eyetracking"
        )

        self.params['elPupilAlgorithm'] = Param(
            elPupilAlgorithm, valType='str', inputType="choice",
            allowedVals=['ELLIPSE_FIT', 'CENTROID_FIT'],
            hint=_translate("Algorithm used to detect the pupil center."),
            label=_translate("Pupil center algorithm"), categ="Eyetracking"
        )

        self.params['elPupilMeasure'] = Param(
            elPupilMeasure, valType='str', inputType="choice",
            allowedVals=['PUPIL_AREA', 'PUPIL_DIAMETER', 'NEITHER'],
            hint=_translate("Type of pupil data to record."),
            label=_translate("Pupil data type"), categ="Eyetracking"
        )

        self.params['elAddress'] = Param(
            elAddress, valType='str', inputType="single",
            hint=_translate("IP Address of the EyeLink *Host* computer."),
            label=_translate("EyeLink IP address"), categ="Eyetracking"
        )

        # tobii
        self.params['tbModel'] = Param(
            tbModel, valType='str', inputType="single",
            hint=_translate("Eye tracker model."),
            label=_translate("Model name"), categ="Eyetracking"
        )

        self.params['tbLicenseFile'] = Param(
            tbLicenseFile, valType='str', inputType="file",
            hint=_translate("Eye tracker license file (optional)."),
            label=_translate("License file"), categ="Eyetracking"
        )

        self.params['tbSerialNo'] = Param(
            tbSerialNo, valType='str', inputType="single",
            hint=_translate("Eye tracker serial number (optional)."),
            label=_translate("Serial number"), categ="Eyetracking"
        )

        self.params['tbSampleRate'] = Param(
            tbSampleRate, valType='num', inputType="single",
            hint=_translate("Eye tracker sampling rate."),
            label=_translate("Sampling rate"), categ="Eyetracking"
        )

        # pupil labs
        self.params['plPupillometryOnly'] = Param(
            plPupillometryOnly, valType='bool', inputType="bool",
            hint=_translate("Subscribe to pupil data only, does not require calibration or surface setup"),
            label=_translate("Pupillometry only"),
            categ="Eyetracking"
        )
        self.params['plSurfaceName'] = Param(
            plSurfaceName, valType='str', inputType="single",
            hint=_translate("Name of the Pupil Capture surface"),
            label=_translate("Surface name"), categ="Eyetracking"
        )
        self.params['plConfidenceThreshold'] = Param(
            plConfidenceThreshold, valType='num', inputType="single",
            hint=_translate("Gaze confidence threshold"),
            label=_translate("Gaze confidence threshold"), categ="Eyetracking"
        )
        self.params['plPupilRemoteAddress'] = Param(
            plPupilRemoteAddress, valType='str', inputType="single",
            hint=_translate("Pupil remote address"),
            label=_translate("Pupil remote address"), categ="Eyetracking"
        )
        self.params['plPupilRemotePort'] = Param(
            plPupilRemotePort, valType='num', inputType="single",
            hint=_translate("Pupil remote port"),
            label=_translate("Pupil remote port"), categ="Eyetracking"
        )
        self.params['plPupilRemoteTimeoutMs'] = Param(
            plPupilRemoteTimeoutMs, valType='num', inputType="single",
            hint=_translate("Pupil remote timeout (ms)"),
            label=_translate("Pupil remote timeout (ms)"), categ="Eyetracking"
        )
        self.params['plPupilCaptureRecordingEnabled'] = Param(
            plPupilCaptureRecordingEnabled, valType='bool', inputType="bool",
            hint=_translate("Pupil capture recording enabled"),
            label=_translate("Pupil capture recording enabled"), categ="Eyetracking"
        )
        self.params['plPupilCaptureRecordingLocation'] = Param(
            plPupilCaptureRecordingLocation, valType='str', inputType="single",
            hint=_translate("Pupil capture recording location"),
            label=_translate("Pupil capture recording location"), categ="Eyetracking"
        )

        # Input
        self.params['keyboardBackend'] = Param(
            keyboardBackend, valType='str', inputType="choice",
            allowedVals=list(keyboardBackendMap),
            hint=_translate("What Python package should PsychoPy use to get keyboard input?"),
            label=_translate("Keyboard backend"), categ="Input"
        )

    @property
    def _xml(self):
        # Make root element
        element = Element("Settings")
        # Add an element for each parameter
        for key, param in sorted(self.params.items()):
            if key == 'name':
                continue
            # Create node
            paramNode = param._xml
            paramNode.set("name", key)
            # Add node
            element.append(paramNode)
        return element

    def getInfo(self):
        """Rather than converting the value of params['Experiment Info']
        into a dict from a string (which can lead to errors) use this function
        :return: expInfo as a dict
        """
        
        infoStr = str(self.params['Experiment info'].val).strip()
        if len(infoStr) == 0:
            return {}
        try:
            infoDict = ast.literal_eval(infoStr)
            # check for strings of lists: "['male','female']"
            for key in infoDict:
                val = infoDict[key]
                if exputils.list_like_re.search(str(val)):
                    # Try to call it with ast, if it produces a list/tuple, treat val type as list
                    try:
                        isList = ast.literal_eval(str(val))
                    except ValueError:
                        # If ast errors, treat as code
                        infoDict[key] = Param(val=val, valType='code')
                    else:
                        if isinstance(isList, (list, tuple)):
                            # If ast produces a list, treat as list
                            infoDict[key] = Param(val=val, valType='list')
                        else:
                            # If ast produces anything else, treat as code
                            infoDict[key] = Param(val=val, valType='code')
                elif val in ['True', 'False']:
                    infoDict[key] = Param(val=val, valType='bool')
                elif isinstance(val, str):
                    infoDict[key] = Param(val=val, valType='str')

        except (ValueError, SyntaxError):
            """under Python3 {'participant':'', 'session':02} raises an error because 
            ints can't have leading zeros. We will check for those and correct them
            tests = ["{'participant':'', 'session':02}",
                    "{'participant':'', 'session':02}",
                    "{'participant':'', 'session': 0043}",
                    "{'participant':'', 'session':02, 'id':009}",
                    ]
                    """

            def entryToString(match):
                entry = match.group(0)
                digits = re.split(r": *", entry)[1]
                return ':{}'.format(repr(digits))

            # 0 or more spaces, 1-5 zeros, 0 or more digits:
            pattern = re.compile(r": *0{1,5}\d*")
            try:
                infoDict = eval(re.sub(pattern, entryToString, infoStr))
            except SyntaxError:  # still a syntax error, possibly caused by user
                msg = ('Builder Expt: syntax error in '
                              '"Experiment info" settings (expected a dict)')
                logging.error(msg)
                raise AttributeError(msg)
        return infoDict

    def getType(self):
        return self.__class__.__name__

    def getShortType(self):
        return self.getType().replace('Component', '')

    def writeUseVersion(self, buff):
        if self.params['Use version'].val:
            code = ('\nimport psychopy\n'
                    'psychopy.useVersion({})\n\n')
            val = repr(self.params['Use version'].val)
            buff.writeIndentedLines(code.format(val))

    def writeInitCode(self, buff, version, localDateTime):

        buff.write(
            '#!/usr/bin/env python\n'
            '# -*- coding: utf-8 -*-\n'
            '"""\nThis experiment was created using PsychoPy3 Experiment '
            'Builder (v%s),\n'
            '    on %s\n' % (version, localDateTime) +
            'If you publish work using this script the most relevant '
            'publication is:\n\n'            
            u'    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, '
            u'Kastman E, Lindeløv JK. (2019) \n'
            '        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. \n'
            '        https://doi.org/10.3758/s13428-018-01193-y\n'
            '\n"""\n')

        self.writeUseVersion(buff)

        psychopyImports = []
        customImports = []
        for import_ in self.exp.requiredImports:
            if import_.importFrom == 'psychopy':
                psychopyImports.append(import_.importName)
            else:
                customImports.append(import_)

        buff.writelines(
            "\n"
            "# --- Import packages ---"
            "\n"
            "from psychopy import locale_setup\n"
            "from psychopy import prefs\n"
            "from psychopy import plugins\n"
            "plugins.activatePlugins()\n"  # activates plugins
        )
        # adjust the prefs for this study if needed
        if self.params['Audio lib'].val.lower() != 'use prefs':
            buff.writelines(
                "prefs.hardware['audioLib'] = {}\n".format(self.params['Audio lib'])
            )
        if self.params['Audio latency priority'].val.lower() != 'use prefs':
            buff.writelines(
                "prefs.hardware['audioLatencyMode'] = {}\n".format(self.params['Audio latency priority'])
            )
        buff.write(
            "from psychopy import %s\n" % ', '.join(psychopyImports) +
            "from psychopy.tools import environmenttools\n"
            "from psychopy.constants import (NOT_STARTED, STARTED, PLAYING,"
            " PAUSED,\n"
            "                                STOPPED, FINISHED, PRESSED, "
            "RELEASED, FOREVER, priority)\n\n"
            "import numpy as np  # whole numpy lib is available, "
            "prepend 'np.'\n"
            "from numpy import (%s,\n" % ', '.join(_numpyImports[:7]) +
            "                   %s)\n" % ', '.join(_numpyImports[7:]) +
            "from numpy.random import %s\n" % ', '.join(_numpyRandomImports) +
            "import os  # handy system and path functions\n" +
            "import sys  # to get file system encoding\n"
            "\n")

        if not self.params['eyetracker'] == "None" or self.params['keyboardBackend'] == "ioHub":
            code = (
                "import psychopy.iohub as io\n"
            )
            buff.writeIndentedLines(code)

        # Write custom import statements, line by line.
        for import_ in customImports:
            importName = import_.importName
            importFrom = import_.importFrom
            importAs = import_.importAs

            statement = ''
            if importFrom:
                statement += "from %s " % importFrom

            statement += "import %s" % importName

            if importAs:
                statement += " as %s" % importAs

            statement += "\n"
            buff.write(statement)

        buff.write("\n")

    def writeGlobals(self, buff, version):
        """
        Create some global variables which functions will need
        """
        # Substitute params
        params = self.params.copy()
        params['version'] = version
        if self.params['expName'].val in [None, '']:
            params['expName'].val = "untitled.py"

        code = (
            "# --- Setup global variables (available in all functions) ---\n"
            "# Ensure that relative paths start from the same directory as this script\n"
            "_thisDir = os.path.dirname(os.path.abspath(__file__))\n"
            "# Store info about the experiment session\n"
            "psychopyVersion = '%(version)s'\n"
            "expName = %(expName)s  # from the Builder filename that created this script\n"
        )
        buff.writeIndentedLines(code % params)
        # Construct exp info dict
        code = (
            "expInfo = {\n"
        )
        for key, value in self.getInfo().items():
            code += (
            f"    '{key}': {value},\n"
            )
        code += (
            "    'date': data.getDateStr(),  # add a simple timestamp\n"
            "    'expName': expName,\n"
            "    'psychopyVersion': psychopyVersion,\n"
            "}\n"
            "\n"
        )
        buff.writeIndented(code)

    def prepareResourcesJS(self):
        """Sets up the resources folder and writes the info.php file for PsychoJS
        """

        join = os.path.join

        def copyTreeWithMD5(src, dst):
            """Copies the tree but checks SHA for each file first
            """
            # despite time to check the md5 hashes this func gives speed-up
            # over about 20% over using shutil.rmtree() and copytree()
            for root, subDirs, files in os.walk(src):
                relPath = os.path.relpath(root, src)
                for thisDir in subDirs:
                    if not os.path.isdir(join(root, thisDir)):
                        os.makedirs(join(root, thisDir))
                for thisFile in files:
                    copyFileWithMD5(join(root, thisFile),
                                    join(dst, relPath, thisFile))

        def copyFileWithMD5(src, dst):
            """Copies a file but only if doesn't exist or SHA is diff
            """
            if os.path.isfile(dst):
                with open(dst, 'rb') as f:
                    dstMD5 = hashlib.md5(f.read()).hexdigest()
                with open(src, 'rb') as f:
                    srcMD5 = hashlib.md5(f.read()).hexdigest()
                if srcMD5 == dstMD5:
                    return  # already matches - do nothing
                # if we got here then the file exists but not the same
                # delete and replace. TODO: In future this should check date
                os.remove(dst)
            # either didn't exist or has been deleted
            folder = os.path.split(dst)[0]
            if not os.path.isdir(folder):
                os.makedirs(folder)
            shutil.copy2(src, dst)

        # write info.php file
        folder = os.path.dirname(self.exp.expPath)
        if not os.path.isdir(folder):
            os.mkdir(folder)

        # is email a defined parameter for this version
        if 'email' in self.params:
            email = repr(self.params['email'].val)
        else:
            email = "''"
        # populate resources folder
        resFolder = join(folder, 'resources')
        if not os.path.isdir(resFolder):
            os.mkdir(resFolder)
        resourceFiles = self.exp.getResourceFiles()

        for srcFile in resourceFiles:
            if "https://" in srcFile.get('abs', "") or srcFile.get('name', "") == "surveyId":
                # URLs and survey IDs don't need copying
                continue
            dstAbs = os.path.normpath(join(resFolder, srcFile['rel']))
            dstFolder = os.path.split(dstAbs)[0]
            if not os.path.isdir(dstFolder):
                os.makedirs(dstFolder)
            copyFileWithMD5(srcFile['abs'], dstAbs)

    def writeInitCodeJS(self, buff, version, localDateTime, modular=True):
        # create resources folder
        if self.exp.htmlFolder:
            self.prepareResourcesJS()
        jsFilename = os.path.basename(os.path.splitext(self.exp.filename)[0])

        # configure the PsychoJS version number from current/requested versions
        useVer = self.params['Use version'].val
        useVer = versions.getPsychoJSVersionStr(version, useVer)

        # html header
        if self.exp.expPath:
            template = readTextFile("JS_htmlHeader.tmpl")
            header = template.format(
                name=jsFilename,
                version=useVer,
                params=self.params)
            jsFile = self.exp.expPath
            folder = os.path.dirname(jsFile)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with open(os.path.join(folder, "index.html"), 'wb') as html:
                html.write(header.encode())
            html.close()

        # Write header comment
        starLen = "*"*(len(jsFilename) + 9)
        code = ("/%s \n"
               " * %s *\n" 
               " %s/\n\n")
        buff.writeIndentedLines(code % (starLen, jsFilename.title(), starLen))

        # Write imports if modular
        if modular:
            code = (
                    "import {{ core, data, sound, util, visual, hardware }} from './lib/psychojs-{version}.js';\n"
                    "const {{ PsychoJS }} = core;\n"
                    "const {{ TrialHandler, MultiStairHandler }} = data;\n"
                    "const {{ Scheduler }} = util;\n"
                    "//some handy aliases as in the psychopy scripts;\n"
                    "const {{ abs, sin, cos, PI: pi, sqrt }} = Math;\n"
                    "const {{ round }} = util;\n"
                    "\n").format(version=useVer)
            buff.writeIndentedLines(code)

        # Get expInfo as a dict
        expInfoDict = self.getInfo().items()
        # Convert each item to str
        expInfoStr = "{"
        if len(expInfoDict):
            # Only make the dict multiline if it actually has contents
            expInfoStr += "\n"
        for key, value in self.getInfo().items():
            expInfoStr += f"    '{key}': {value},\n"
        expInfoStr += "}"

        code = ("\n// store info about the experiment session:\n"
                "let expName = '%s';  // from the Builder filename that created this script\n"
                "let expInfo = %s;\n"
                "\n" % (jsFilename, expInfoStr))
        buff.writeIndentedLines(code)

    def writeExpSetupCodeJS(self, buff, version):

        
        # write the code to set up experiment
        buff.setIndentLevel(0, relative=False)
        template = readTextFile("JS_setupExp.tmpl")

        # Get file delimiter character
        delim_options = {
            'comma': ",",
            'semicolon': ";",
            'tab': r"\t"
            }
        delim = delim_options.get(
            self.params['Data file delimiter'].val,
            genDelimiter(self.params['Data filename'].val)
        )

        setRedirectURL = ''
        if len(self.params['Completed URL'].val) or len(self.params['Incomplete URL'].val):
            setRedirectURL = ("psychoJS.setRedirectUrls({completedURL}, {incompleteURL});\n"
                              .format(completedURL=self.params['Completed URL'],
                                      incompleteURL=self.params['Incomplete URL']))
        # check where to save data variables
        # if self.params['OSF Project ID'].val:
        #     saveType = "OSF_VIA_EXPERIMENT_SERVER"
        #     projID = "'{}'".format(self.params['OSF Project ID'].val)
        # else:
        #     saveType = "EXPERIMENT_SERVER"
        #     projID = 'undefined'

        code = template.format(
            params=self.params,
            filename=str(self.params['Data filename']),
            name=self.params['expName'].val,
            loggingLevel=self.params['logging level'].val.upper(),
            setRedirectURL=setRedirectURL,
            version=version, 
            field_separator=repr(delim)
        )
        buff.writeIndentedLines(code)

    def writeDataCode(self, buff):
        """
        Write code to handle data and saving (create ExperimentHandler, pick filename, etc.)
        """
        params = self.params.copy()

        # Enter function def
        code = (
            '\n'
            'def setupData(expInfo, dataDir=None):\n'
            '    """\n'
            '    Make an ExperimentHandler to handle trials and saving.\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    expInfo : dict\n'
            '        Information about this experiment, created by the `setupExpInfo` function.\n'
            '    dataDir : Path, str or None\n'
            '        Folder to save the data to, leave as None to create a folder in the current directory.'
            '    \n'
            '    Returns\n'
            '    ==========\n'
            '    psychopy.data.ExperimentHandler\n'
            '        Handler object for this experiment, contains the data to save and information about \n'
            '        where to save it to.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)

        # figure out participant id field (if any)
        participantVal = ''
        for field in ('participant', 'Participant', 'Subject', 'Observer'):
            if field in self.getInfo():
                participantVal = " + expInfo['%s']" % field
                break
        # make sure we have a filename
        if not params['Data filename'].val:  # i.e., the user deleted it
            params['Data filename'].val = (
                "'data' + os.sep%s + data.getDateStr()"
            ) % participantVal
        # get origin path
        params['originPath'] = repr(self.exp.expPath)
        # get fallback data dir value
        params['dataDir'] = "_thisDir"
        # deprecated code: before v1.80.00 we had 'Saved data folder' param
        if 'Saved data folder' in params:
            if params['Saved data folder'].val.strip():
                params['dataDir'] = params['Saved data folder']
            else:
                params['dataDir'] = repr(self.exp.prefsBuilder['savedDataFolder'].strip())

        code = (
            "\n"
            "# data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc\n"
            f"if dataDir is None:\n"
            f"    dataDir = %(dataDir)s\n"
            f"filename = %(Data filename)s\n"
            f"# make sure filename is relative to dataDir\n"
            f"if os.path.isabs(filename):\n"
            f"    dataDir = os.path.commonprefix([dataDir, filename])\n"
            f"    filename = os.path.relpath(filename, dataDir)\n"
        )
        buff.writeIndentedLines(code % params)

        # set up the ExperimentHandler
        code = ("\n# an ExperimentHandler isn't essential but helps with data saving\n"
                "thisExp = data.ExperimentHandler(\n"
                "    name=expName, version='',\n"
                "    extraInfo=expInfo, runtimeInfo=None,\n"
                "    originPath=%(originPath)s,\n"
                "    savePickle=%(Save psydat file)s, saveWideText=%(Save wide csv file)s,\n"
                "    dataFileName=dataDir + os.sep + filename, sortColumns=%(sortColumns)s\n"
                ")\n")
        buff.writeIndentedLines(code % params)

        # enforce dict on column priority param
        colPriority = params['colPriority'].val
        if isinstance(colPriority, str):
            try:
                colPriority = ast.literal_eval(colPriority)
            except:
                raise ValueError(_translate(
                    "Could not interpret value as dict: {}"
                ).format(colPriority))
        # setup column priority
        for key, val in colPriority.items():
            code = (
                f"thisExp.setPriority('{key}', {val})\n"
            )
            buff.writeIndentedLines(code)

        code = (
            "# return experiment handler\n"
            "return thisExp\n"
        )
        buff.writeIndentedLines(code)
        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeLoggingCode(self, buff):
        # Enter function def
        code = (
            '\n'
            'def setupLogging(filename):\n'
            '    """\n'
            '    Setup a log file and tell it what level to log at.\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    filename : str or pathlib.Path\n'
            '        Filename to save log file and data files as, doesn\'t need an extension.\n'
            '    \n'
            '    Returns\n'
            '    ==========\n'
            '    psychopy.logging.LogFile\n'
            '        Text stream to receive inputs from the logging system.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)

        level = self.params['logging level'].val.upper()

        if self.params['Save log file'].val:
            code = (
                "# save a log file for detail verbose info\n"
                "logFile = logging.LogFile(filename+'.log', level=logging.%s)\n"
            )
            buff.writeIndentedLines(code % level)
        buff.writeIndented("logging.console.setLevel(logging.WARNING)  "
                           "# this outputs to the screen, not a file\n")

        code = (
            "# return log file\n"
            "return logFile\n"
        )
        buff.writeIndentedLines(code)
        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeExpInfoDlgCode(self, buff):
        # Enter function def
        code = (
            '\n'
            'def showExpInfoDlg(expInfo):\n'
            '    """\n'
            '    Show participant info dialog.\n'
            '    Parameters\n'
            '    ==========\n'
            '    expInfo : dict\n'
            '        Information about this experiment, created by the `setupExpInfo` function.\n'
            '    \n'
            '    Returns\n'
            '    ==========\n'
            '    dict\n'
            '        Information about this experiment.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)

        sorting = "False"  # in Py3 dicts are chrono-sorted so default no sort
        code = (
            f"# temporarily remove keys which the dialog doesn't need to show\n"
            f"poppedKeys = {{\n"
            f"    'date': expInfo.pop('date', data.getDateStr()),\n"
            f"    'expName': expInfo.pop('expName', expName),\n"
            f"    'psychopyVersion': expInfo.pop('psychopyVersion', psychopyVersion),\n"
            f"}}\n"
            f"# show participant info dialog\n"
            f"dlg = gui.DlgFromDict(dictionary=expInfo, "
            f"sortKeys={sorting}, title=expName)\n"
            f"if dlg.OK == False:\n"
            f"    core.quit()  # user pressed cancel\n"
            f"# restore hidden keys\n"
            f"expInfo.update(poppedKeys)\n"
            f"# return expInfo\n"
            f"return expInfo\n"
        )
        buff.writeIndentedLines(code)

        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeIohubCode(self, buff):
        # Open function def
        code = (
            '\n'
            'def setupInputs(expInfo, thisExp, win):\n'
            '    """\n'
            '    Setup whatever inputs are available (mouse, keyboard, eyetracker, etc.)\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    expInfo : dict\n'
            '        Information about this experiment, created by the `setupExpInfo` function.\n'
            '    thisExp : psychopy.data.ExperimentHandler\n'
            '        Handler object for this experiment, contains the data to save and information about \n'
            '        where to save it to.\n'
            '    win : psychopy.visual.Window\n'
            '        Window in which to run this experiment.\n'
            '    Returns\n'
            '    ==========\n'
            '    dict\n'
            '        Dictionary of input devices by name.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)

        # Substitute inits
        inits = deepcopy(self.params)
        if inits['mgMove'].val == "CONTINUOUS":
            inits['mgMove'].val = "$"
        inits['keyboardBackend'].val = keyboardBackendMap[inits['keyboardBackend'].val]
        inits['eyetracker'].val = ioDeviceMap[inits['eyetracker'].val]

        # Make ioConfig dict
        code = (
            "# --- Setup input devices ---\n"
            "inputs = {}\n"
            "ioConfig = {}\n"
        )
        buff.writeIndentedLines(code % inits)
        # Add eyetracker config
        if self.params['eyetracker'] != "None":
            # Alert user if window is not fullscreen
            if not self.params['Full-screen window'].val:
                alert(code=4540)
            # Alert user if no monitor config
            if self.params['Monitor'].val in ["", None, "None"]:
                alert(code=4545)
            # Alert user if they need calibration and don't have it
            if self.params['eyetracker'].val != "MouseGaze":
                if not any(isinstance(rt, EyetrackerCalibrationRoutine)
                           for rt in self.exp.flow):
                    alert(code=4510, strFields={"eyetracker": self.params['eyetracker'].val})

            # Write code
            code = (
                "\n"
                "# Setup eyetracking\n"
                "ioConfig[%(eyetracker)s] = {\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(1, relative=True)
            code = (
                    "'name': 'tracker',\n"
            )
            buff.writeIndentedLines(code % inits)
            # Initialise for MouseGaze
            if self.params['eyetracker'] == "MouseGaze":
                code = (
                        "'controls': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)
                code = (
                            "'move': [%(mgMove)s],\n"
                            "'blink':%(mgBlink)s,\n"
                            "'saccade_threshold': %(mgSaccade)s,\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)

            elif self.params['eyetracker'] == "GazePoint":
                code = (
                        "'network_settings': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)
                code = (
                            "'ip_address': %(gpAddress)s,\n"
                            "'port': %(gpPort)s\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)

            elif self.params['eyetracker'] == "Tobii Technology":
                code = (
                        "'model_name': %(tbModel)s,\n"
                        "'serial_number': %(tbSerialNo)s,\n"
                        "'runtime_settings': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)
                code = (
                            "'sampling_rate': %(tbSampleRate)s,\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)

            elif self.params['eyetracker'] == "SR Research Ltd":
                code = (
                    "'model_name': %(elModel)s,\n"
                    "'simulation_mode': %(elSimMode)s,\n"
                    "'network_settings': %(elAddress)s,\n"
                    "'default_native_data_file_name': 'EXPFILE',\n"
                    "'runtime_settings': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)
                code = (
                        "'sampling_rate': %(elSampleRate)s,\n"
                        "'track_eyes': %(elTrackEyes)s,\n"
                        "'sample_filtering': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)
                code = (
                            "'sample_filtering': %(elDataFiltering)s,\n"
                            "'elLiveFiltering': %(elLiveFiltering)s,\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(-1, relative=True)
                code = (
                        "},\n"
                        "'vog_settings': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)
                code = (
                            "'pupil_measure_types': %(elPupilMeasure)s,\n"
                            "'tracking_mode': %(elTrackingMode)s,\n"
                            "'pupil_center_algorithm': %(elPupilAlgorithm)s,\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)

            elif self.params['eyetracker'] == "Pupil Labs":
                # Open runtime_settings dict
                code = (
                    "'runtime_settings': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)

                # Define runtime_settings dict
                code = (
                    "'pupillometry_only': %(plPupillometryOnly)s,\n"
                    "'surface_name': %(plSurfaceName)s,\n"
                    "'confidence_threshold': %(plConfidenceThreshold)s,\n"
                )
                buff.writeIndentedLines(code % inits)

                # Open runtime_settings > pupil_remote dict
                code = (
                    "'pupil_remote': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)

                # Define runtime_settings > pupil_remote dict
                code = (
                    "'ip_address': %(plPupilRemoteAddress)s,\n"
                    "'port': %(plPupilRemotePort)s,\n"
                    "'timeout_ms': %(plPupilRemoteTimeoutMs)s,\n"
                )
                buff.writeIndentedLines(code % inits)

                # Close runtime_settings > pupil_remote dict
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "},\n"
                )
                buff.writeIndentedLines(code % inits)

                # Open runtime_settings > pupil_capture_recording dict
                code = (
                    "'pupil_capture_recording': {\n"
                )
                buff.writeIndentedLines(code % inits)
                buff.setIndentLevel(1, relative=True)

                # Define runtime_settings > pupil_capture_recording dict
                code = (
                    "'enabled': %(plPupilCaptureRecordingEnabled)s,\n"
                    "'location': %(plPupilCaptureRecordingLocation)s,\n"
                )
                buff.writeIndentedLines(code % inits)

                # Close runtime_settings > pupil_capture_recording dict
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)

                # Close runtime_settings dict
                buff.setIndentLevel(-1, relative=True)
                code = (
                    "}\n"
                )
                buff.writeIndentedLines(code % inits)

            # Close ioDevice dict
            buff.setIndentLevel(-1, relative=True)
            code = (
                "}\n"
            )
            buff.writeIndentedLines(code % inits)

        # Add keyboard to ioConfig
        if self.params['keyboardBackend'] == 'ioHub':
            code = (
                "\n"
                "# Setup iohub keyboard\n"
                "ioConfig['Keyboard'] = dict(use_keymap='psychopy')\n\n"
            )
            buff.writeIndentedLines(code % inits)

        if self.needIoHub and self.params['keyboardBackend'] == 'PsychToolbox':
            alert(code=4550)

        # Start ioHub server
        if self.needIoHub:
            # Specify session
            code = (
                "ioSession = '1'\n"
                "if 'session' in expInfo:\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(1, relative=True)
            code = (
                    "ioSession = str(expInfo['session'])\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(-1, relative=True)
            # Start server
            if self.params['Save hdf5 file'].val:
                code = (
                    f"ioServer = io.launchHubServer(window=win, experiment_code=%(expName)s, session_code=ioSession, "
                    f"datastore_name=thisExp.dataFileName, **ioConfig)\n"
                )
            else:
                code = (
                    f"ioServer = io.launchHubServer(window=win, **ioConfig)\n"
                )
            buff.writeIndentedLines(code % inits)
            # Get eyetracker name
            if self.params['eyetracker'] != "None":
                code = (
                    "eyetracker = ioServer.getDevice('tracker')\n"
                )
                buff.writeIndentedLines(code % inits)
            else:
                code = (
                    "eyetracker = None\n"
                )
                buff.writeIndentedLines(code % inits)
        else:
            code = (
                "ioSession = ioServer = eyetracker = None"
            )
            buff.writeIndentedLines(code % inits)

        # Make default keyboard
        code = (
            "\n"
            "# create a default keyboard (e.g. to check for escape)\n"
            "defaultKeyboard = keyboard.Keyboard(backend=%(keyboardBackend)s)\n"
        )
        buff.writeIndentedLines(code % inits)

        code = (
            "# return inputs dict\n"
            "return {\n"
            "    'ioServer': ioServer,\n"
            "    'defaultKeyboard': defaultKeyboard,\n"
            "    'eyetracker': eyetracker,\n"
            "}\n"
        )
        buff.writeIndentedLines(code)
        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeWindowCode(self, buff):
        """Setup the window code.
        """
        # Open function def
        code = (
            '\n'
            'def setupWindow(expInfo=None, win=None):\n'
            '    """\n'
            '    Setup the Window\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    expInfo : dict\n'
            '        Information about this experiment, created by the `setupExpInfo` function.\n'
            '    win : psychopy.visual.Window\n'
            '        Window to setup - leave as None to create a new window.\n'
            '    \n'
            '    Returns\n'
            '    ==========\n'
            '    psychopy.visual.Window\n'
            '        Window in which to run this experiment.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)

        params = self.params.copy()

        # get parameters for the Window
        params['fullScr'] = self.params['Full-screen window'].val
        # if fullscreen then hide the mouse, unless its requested explicitly
        allowGUI = (not bool(params['fullScr'])) or bool(self.params['Show mouse'].val)
        allowStencil = False
        # NB routines is a dict:
        for thisRoutine in list(self.exp.routines.values()):
            # a single routine is a list of components:
            for thisComp in thisRoutine:
                if thisComp.type in ('Aperture', 'Textbox'):
                    allowStencil = True
                if thisComp.type == 'RatingScale':
                    allowGUI = True  # to have a mouse
        params['allowGUI'] = allowGUI
        params['allowStencil'] = allowStencil
        # use fbo?
        params['useFBO'] = "True"
        if params['blendMode'].val in ("nofbo",):
            params['blendMode'].val = 'avg'
            params['useFBO'] = "False"
        # Substitute units
        if self.params['Units'].val == 'use prefs':
            params['Units'] = "None"

        requestedScreenNumber = int(self.params['Screen'].val)
        nScreens = 10
        # try:
        #     nScreens = wx.Display.GetCount()  # NO, don't rely on wx being present
        # except Exception:
        #     # will fail if application hasn't been created (e.g. in test
        #     # environments)
        #     nScreens = 10
        if requestedScreenNumber > nScreens:
            logging.warn("Requested screen can't be found. Writing script "
                         "using first available screen.")
            params['screenNumber'] = 0
        else:
            # computer has 1 as first screen
            params['screenNumber'] = requestedScreenNumber - 1

        params['size'] = self.params['Window size (pixels)']
        params['winType'] = self.params['winBackend']

        # Do we need to make a new window?
        code = (
            "if win is None:\n"
            "    # if not given a window to setup, make one\n"
            "    win = visual.Window(\n"
            "        size=%(size)s, fullscr=%(fullScr)s, screen=%(screenNumber)s,\n"
            "        winType=%(winType)s, allowStencil=%(allowStencil)s,\n"
            "        monitor=%(Monitor)s, color=%(color)s, colorSpace=%(colorSpace)s,\n"
            "        backgroundImage=%(backgroundImg)s, backgroundFit=%(backgroundFit)s,\n"
            "        blendMode=%(blendMode)s, useFBO=%(useFBO)s,\n"
            "        units=%(Units)s\n"
            "    )\n"
            "    if expInfo is not None:\n"
            "        # store frame rate of monitor if we can measure it\n"
            "        expInfo['frameRate'] = win.getActualFrameRate()\n"
            "else:\n"
            "    # if we have a window, just set the attributes which are safe to set\n"
            "    win.color = %(color)s\n"
            "    win.colorSpace = %(colorSpace)s\n"
            "    win.backgroundImage = %(backgroundImg)s\n"
            "    win.backgroundFit = %(backgroundFit)s\n"
            "    win.units = %(Units)s\n"
        )
        buff.writeIndentedLines(code % params)

        # Show/hide mouse according to param
        code = (
            "win.mouseVisible = %s\n"
        )
        buff.writeIndentedLines(code % allowGUI)

        # Reset splash message
        code = (
            "win.hideMessage()\n"
        )
        buff.writeIndentedLines(code)

        # Import here to avoid circular dependency!
        from psychopy.experiment._experiment import RequiredImport
        microphoneImport = RequiredImport(importName='microphone',
                                          importFrom='psychopy',
                                          importAs='')
        if microphoneImport in self.exp.requiredImports:  # need a pyo Server
            buff.writeIndentedLines("\n# Enable sound input/output:\n"
                                    "microphone.switchOn()\n")
        # Exit function def
        code = (
            "return win\n"
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeSaveDataCode(self, buff):
        # Open function def
        code = (
            '\n'
            'def saveData(thisExp):\n'
            '    """\n'
            '    Save data from this experiment\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    thisExp : psychopy.data.ExperimentHandler\n'
            '        Handler object for this experiment, contains the data to save and information about \n'
            '        where to save it to.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)
        # Get filename from thisExp
        code = (
            "filename = thisExp.dataFileName\n"
            "# these shouldn't be strictly necessary (should auto-save)\n"
        )
        if self.params['Save wide csv file'].val:
            code += (
                "thisExp.saveAsWideText(filename + '.csv', delim=%(Data file delimiter)s)\n"
            )
        if self.params['Save psydat file'].val:
            code += (
                "thisExp.saveAsPickle(filename)\n"
            )
        buff.writeIndentedLines(code % self.params)

        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeWindowCodeJS(self, buff):
        """Setup the JS window code.
        """
        # Replace instances of 'use prefs'
        units = self.params['Units'].val
        if units == 'use prefs':
            units = 'height'

        code = ("// init psychoJS:\n"
                "const psychoJS = new PsychoJS({{\n"
                "  debug: true\n"
                "}});\n\n"
                "// open window:\n"
                "psychoJS.openWindow({{\n"
                "  fullscr: {fullScr},\n"
                "  color: new util.Color({params[color]}),\n"
                "  units: '{units}',\n"
                "  waitBlanking: true\n"
                "}});\n").format(fullScr=str(self.params['Full-screen window']).lower(),
                                 params=self.params,
                                 units=units)
        buff.writeIndentedLines(code)

    def writePauseCode(self, buff):
        # Open function def
        code = (
            'def pauseExperiment(thisExp, inputs=None, win=None, timers=[], playbackComponents=[]):\n'
            '    """\n'
            '    Pause this experiment, preventing the flow from advancing to the next routine until resumed.\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    thisExp : psychopy.data.ExperimentHandler\n'
            '        Handler object for this experiment, contains the data to save and information about \n'
            '        where to save it to.\n'
            '    inputs : dict\n'
            '        Dictionary of input devices by name.\n'
            '    win : psychopy.visual.Window\n'
            '        Window for this experiment.\n'
            '    timers : list, tuple\n'
            '        List of timers to reset once pausing is finished.\n'
            '    playbackComponents : list, tuple\n'
            '        List of any components with a `pause` method which need to be paused.\n'
            '    """'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)

        # handle pausing
        code = (
            "# if we are not paused, do nothing\n"
            "if thisExp.status != PAUSED:\n"
            "    return\n"
            "\n"
            "# pause any playback components\n"
            "for comp in playbackComponents:\n"
            "    comp.pause()\n"
            "# prevent components from auto-drawing\n"
            "win.stashAutoDraw()\n"
            "# run a while loop while we wait to unpause\n"
            "while thisExp.status == PAUSED:\n"
        )
        if self.params['Enable Escape'].val:
            code += (
            "    # make sure we have a keyboard\n"
            "    if inputs is None:\n"
            "        inputs = {\n"
            "            'defaultKeyboard': keyboard.Keyboard(backend=%(keyboardBackend)s)\n"
            "        }\n"
            "    # check for quit (typically the Esc key)\n"
            "    if inputs['defaultKeyboard'].getKeys(keyList=['escape']):\n"
            "        endExperiment(thisExp, win=win, inputs=inputs)\n"
            )
        code += (
            "    # flip the screen\n"
            "    win.flip()\n"
            "# if stop was requested while paused, quit\n"
            "if thisExp.status == FINISHED:\n"
            "    endExperiment(thisExp, inputs=inputs, win=win)\n"
            "# resume any playback components\n"
            "for comp in playbackComponents:\n"
            "    comp.play()\n"
            "# restore auto-drawn components\n"
            "win.retrieveAutoDraw()\n"
            "# reset any timers\n"
            "for timer in timers:\n"
            "    timer.reset()\n"
        )
        buff.writeIndentedLines(code % self.params)

        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeEndCode(self, buff):
        """Write code for end of experiment (e.g. close log file).
        """
        # Open function def
        code = (
            '\n'
            'def endExperiment(thisExp, inputs=None, win=None):\n'
            '    """\n'
            '    End this experiment, performing final shut down operations.\n'
            '    \n'
            '    This function does NOT close the window or end the Python process - use `quit` for this.\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    thisExp : psychopy.data.ExperimentHandler\n'
            '        Handler object for this experiment, contains the data to save and information about \n'
            '        where to save it to.\n'
            '    inputs : dict\n'
            '        Dictionary of input devices by name.\n'
            '    win : psychopy.visual.Window\n'
            '        Window for this experiment.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)
        # Write code to end experiment
        code = (
            "if win is not None:\n"
            "    # remove autodraw from all current components\n"
            "    win.clearAutoDraw()\n"
            "    # Flip one final time so any remaining win.callOnFlip() \n"
            "    # and win.timeOnFlip() tasks get executed\n"
            "    win.flip()\n"
            "# mark experiment handler as finished\n"
            "thisExp.status = FINISHED\n"
            "# shut down eyetracker, if there is one\n"
            "if inputs is not None:\n"
            "    if 'eyetracker' in inputs and inputs['eyetracker'] is not None:\n"
            "        inputs['eyetracker'].setConnectionState(False)\n"
        )
        if self.params['Save log file'].val:
            code += (
            "logging.flush()\n"
            )
        buff.writeIndentedLines(code)
        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

        # Open function def
        code = (
            '\n'
            'def quit(thisExp, win=None, inputs=None, thisSession=None):\n'
            '    """\n'
            '    Fully quit, closing the window and ending the Python process.\n'
            '    \n'
            '    Parameters\n'
            '    ==========\n'
            '    win : psychopy.visual.Window\n'
            '        Window to close.\n'
            '    inputs : dict\n'
            '        Dictionary of input devices by name.\n'
            '    thisSession : psychopy.session.Session or None\n'
            '        Handle of the Session object this experiment is being run from, if any.\n'
            '    """\n'
        )
        buff.writeIndentedLines(code)
        buff.setIndentLevel(+1, relative=True)
        # Write code to end session
        code = (
            "thisExp.abort()  # or data files will save again on exit\n"
            "# make sure everything is closed down\n"
            "if win is not None:\n"
            "    # Flip one final time so any remaining win.callOnFlip() \n"
            "    # and win.timeOnFlip() tasks get executed before quitting\n"
            "    win.flip()\n"
            "    win.close()\n"
            "if inputs is not None:\n"
            "    if 'eyetracker' in inputs and inputs['eyetracker'] is not None:\n"
            "        eyetracker.setConnectionState(False)\n"
        )
        if self.params['Save log file'].val:
            code += (
            "logging.flush()\n"
            )
        code += (
            "if thisSession is not None:\n"
            "    thisSession.stop()\n"
            "# terminate Python process\n"
            "core.quit()\n"
        )
        buff.writeIndentedLines(code)
        # Exit function def
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("\n")

    def writeEndCodeJS(self, buff):
        """Write some general functions that might be used by any Scheduler/object"""

        recordLoopIterationFunc = ("\nfunction importConditions(currentLoop) {\n"
                    "  return async function () {\n"
                    "    psychoJS.importAttributes(currentLoop.getCurrentTrial());\n"
                    "    return Scheduler.Event.NEXT;\n"
                    "    };\n"
                    "}\n")
        buff.writeIndentedLines(recordLoopIterationFunc)

        code = ("\nasync function quitPsychoJS(message, isCompleted) {\n")
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)
        code = ("// Check for and save orphaned data\n"
                "if (psychoJS.experiment.isEntryEmpty()) {\n"
                "  psychoJS.experiment.nextEntry();\n"
                "}\n")
        buff.writeIndentedLines(code)

        # Write End Experiment code component
        for thisRoutine in list(self.exp.routines.values()):
            # a single routine is a list of components:
            for thisComp in thisRoutine:
                if thisComp.type in ['Code', 'EmotivRecording']:
                    buff.writeIndented("\n")
                    thisComp.writeExperimentEndCodeJS(buff)
                    buff.writeIndented("\n")

        code = ("psychoJS.window.close();\n"
                "psychoJS.quit({message: message, isCompleted: isCompleted});\n\n"
                "return Scheduler.Event.QUIT;\n")
        buff.writeIndentedLines(code)

        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("}\n")
        buff.setIndentLevel(-1)

    @property
    def monitor(self):
        """Stores a monitor object for the  experiment so that it
        doesn't have to be fetched from disk repeatedly"""
        # remember to set _monitor to None periodically (start of script build?)
        # so that we do reload occasionally
        if not self._monitor:
            self._monitor = Monitor(self.params['Monitor'].val)
        return self._monitor

    @monitor.setter
    def monitor(self, monitor):
        self._monitor = monitor

    @property
    def needIoHub(self):
        # Needed for keyboard
        kb = self.params['keyboardBackend'] == 'ioHub'
        # Needed for eyetracking
        et = self.params['eyetracker'] != 'None'

        return any((kb, et))
