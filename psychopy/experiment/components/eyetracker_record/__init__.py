#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.localization import _localized as __localized
from psychopy.alerts import alert
_localized = __localized.copy()


class EyetrackerRecordComponent(BaseComponent):
    """A class for using one of several eyetrackers to follow gaze"""
    categories = ['Eyetracking']
    targets = ['PsychoPy']
    version = "2021.2.0"
    iconFile = Path(__file__).parent / 'eyetracker_record.png'
    tooltip = _translate('Start and / or Stop recording data from the eye tracker')
    beta = True

    def __init__(self, exp, parentName, name='etRecord',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 actionType="Start and Stop",
                 #legacy
                 save='final', configFile='myTracker.yaml'):
        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'EyetrackerRecord'
        self.url = "https://www.psychopy.org/builder/components/eyetracker.html"
        self.exp.requirePsychopyLibs(['iohub', 'hardware'])

        self.params['actionType'] = Param(actionType,
            valType='str', inputType='choice', categ='Basic',
            allowedVals=["Start and Stop", "Start Only", "Stop Only"],
            hint=_translate("Should this Component start and / or stop eye tracker recording?"),
            label=_translate("Record actions")
        )

        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Start Only'",  # val to check for
              "param": "stop",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
         )

        self.depends.append(
             {"dependsOn": "actionType",  # must be param name
              "condition": "=='Stop Only'",  # val to check for
              "param": "start",  # param property to alter
              "true": "hide",  # what to do with param if condition is True
              "false": "show",  # permitted: hide, show, enable, disable
              }
         )

        # TODO: Display actionType control after component name.
        #       Currently, adding params before start / stop time
        #       in .order has no effect
        self.order = self.order[:1]+['actionType']+self.order[1:]

    def writeInitCode(self, buff):
        inits = self.params
        # Make a controller object
        code = (
            "%(name)s = hardware.eyetracker.EyetrackerControl(\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "tracker=eyetracker,\n"
                "actionType=%(actionType)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # Alert user if eyetracking isn't setup
        if self.exp.eyetracking == "None":
            alert(code=4505)

        inits = self.params
        buff.writeIndentedLines("# *%s* updates\n" % self.params['name'])

        # test for whether we're just starting to record
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        org_val = self.params['stopVal'].val
        if self.params['actionType'].val.find('Start Only') >= 0:
            self.params['stopVal'].val = 0

        indented = self.writeStopTestCode(buff)
        buff.setIndentLevel(-indented, relative=True)

        self.params['stopVal'].val = org_val

    def writeRoutineEndCode(self, buff):
        inits = self.params

        code = (
            "# make sure the eyetracker recording stops\n"
            "if %(name)s.status != FINISHED:\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(1, relative=True)
        code = (
                "%(name)s.status = FINISHED\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
