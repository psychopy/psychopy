#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
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
    iconFile = Path(__file__).parent / 'eyetracker_record.png'
    tooltip = _translate('Eyetracker: use one of several eyetrackers to follow '
                         'gaze')
    beta = True

    def __init__(self, exp, parentName, name='etRecord',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 #legacy
                 save='final', configFile='myTracker.yaml'):
        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'EyetrackerRecord'
        self.url = "https://www.psychopy.org/builder/components/eyetracker.html"
        self.exp.requirePsychopyLibs(['iohub', 'hardware'])

    def writeInitCode(self, buff):
        inits = self.params
        # Make a controller object
        code = (
            "%(name)s = hardware.eyetracker.EyetrackerControl(\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "server=ioServer,\n"
                "tracker=eyetracker\n"
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
        self.writeStartTestCode(buff)
        code = (
                "%(name)s.status = STARTED\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            code = (
                "%(name)s.status = FINISHED\n"
            )
            buff.writeIndentedLines(code % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-2, relative=True)

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
