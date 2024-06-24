#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.alerts import alert


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
                 stopWithRoutine=False,
                 # legacy
                 save='final', configFile='myTracker.yaml'):
        BaseComponent.__init__(self, exp, parentName, name=name,
                               startType=startType, startVal=startVal,
                               stopType=stopType, stopVal=stopVal,
                               startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'EyetrackerRecord'
        self.url = "https://www.psychopy.org/builder/components/eyetracker.html"
        self.exp.requirePsychopyLibs(['iohub', 'hardware'])

        self.params['actionType'] = Param(
            actionType,
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

        self.params['stopWithRoutine'] = Param(
            stopWithRoutine,
            valType='bool', inputType="bool", updates='constant', categ='Basic',
            hint=_translate(
                "Should eyetracking stop when the Routine ends? Tick to force stopping "
                "after the Routine has finished."),
            label=_translate('Stop with Routine?'))

        self.depends.append(
            {
                "dependsOn": "actionType",  # must be param name
                "condition": "in ('Start and Stop', 'Stop Only')",  # val to check for
                "param": "stopWithRoutine",  # param property to alter
                "true": "show",  # what to do with param if condition is True
                "false": "hide",  # permitted: hide, show, enable, disable
            }
        )

        # TODO: Display actionType control after component name.
        #       Currently, adding params before start / stop time
        #       in .order has no effect
        self.order = self.order[:1]+['actionType']+self.order[1:]

    def getStartAndDuration(self):
        """ Due to the different action types hiding either the start or stop
        field parameters, we need to force the start and stop criteria to correct
        types and values, make sure the component is displayed accurately on the
        timeline reflecting the status of EyetrackerRecordComponent instead of
        the eyetracker device, and ensure proper nonSlip timing determination
        """
        # make a copy of params so we can change stuff harmlessly
        params = self.params.copy()
        # check if the actionType is 'Start Only' or 'Stop Only'
        if self.params['actionType'].val == 'Start Only':
            # if only starting, pretend stop is 0
            self.params['stopType'].val = 'duration (s)'
            self.params['stopVal'].val = 0.0
        elif self.params['actionType'].val == 'Stop Only':
            # if only stopping, pretend start was 0
            self.params['startType'].val = 'time (s)'
            self.params['startVal'].val = 0.0
        
        return super().getStartAndDuration(params)

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

        buff.writeIndented("\n")
        buff.writeIndentedLines("# *%s* updates\n" % self.params['name'])

        if "start" in self.params['actionType'].val.lower():
            # if this Component can start recording, write start test code
            indented = self.writeStartTestCode(buff)
            # write code to start
            code = (
                "%(name)s.start()\n"
            )
            buff.writeIndentedLines(code % self.params)
            # dedent
            buff.setIndentLevel(-indented, relative=True)
        else:
            # if this Component can't start recording, make sure it reads as already started
            code = (
                "if %(name)s.status == NOT_STARTED:\n"
                "    %(name)s.frameNStart = frameN  # exact frame index\n"
                "    %(name)s.tStart = t  # local t and not account for scr refresh\n"
                "    %(name)s.tStartRefresh = tThisFlipGlobal  # on global time\n"
                "    win.timeOnFlip(%(name)s, 'tStartRefresh')  # time at next scr refresh\n"
                "    %(name)s.status = STARTED\n"
            )
            buff.writeIndentedLines(code % self.params)

        if "stop" in self.params['actionType'].val.lower():
            # if this Component can stop recording, write stop test code
            indented = self.writeStopTestCode(buff)
            # write code to stop
            code = (
                "%(name)s.stop()\n"
            )
            buff.writeIndentedLines(code % self.params)
            # dedent
            buff.setIndentLevel(-indented, relative=True)
        else:
            # if this Component can't stop recording, mark as finished as soon as recording has started
            code = (
                "if %(name)s.status == STARTED:\n"
                "    %(name)s.tStop = t  # not accounting for scr refresh\n"
                "    %(name)s.tStopRefresh = tThisFlipGlobal  # on global time\n"
                "    %(name)s.frameNStop = frameN  # exact frame index\n"
                "    %(name)s.status = FINISHED\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCode(self, buff):
        if self.params['stopWithRoutine']:
            # stop at the end of the Routine, if requested
            code = (
                "%(name)s.stop()  # ensure eyetracking has stopped at end of Routine\n"
            )
            buff.writeIndentedLines(code % self.params)
