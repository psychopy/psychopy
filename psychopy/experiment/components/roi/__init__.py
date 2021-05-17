#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from pathlib import Path
from psychopy.experiment.components import Param, getInitVals, _translate, BaseVisualComponent
from psychopy.experiment.components.polygon import PolygonComponent
from psychopy.localization import _localized as __localized
_localized = __localized.copy()


class RegionOfInterestComponent(PolygonComponent):
    """A class for using one of several eyetrackers to follow gaze"""
    categories = ['Eyetracking']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'eyetracker_roi.png'
    tooltip = _translate('Region Of Interest: Define a region of interest for use with eyetrackers')

    def __init__(self, exp, parentName, name='roi',
                 units='from exp settings',
                 endRoutineOn="none",
                 shape='triangle', nVertices=4,
                 pos=(0, 0), size=(0.5, 0.5), ori=0,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 timeRelativeTo='roi onset',
                 lookDur=100, debug=False,
                 save='every look'):

        PolygonComponent.__init__(self, exp, parentName, name=name,
                 units=units,
                 shape=shape, nVertices=nVertices,
                 pos=pos, size=size, ori=ori,
                 startType=startType, startVal=startVal,
                 stopType=stopType, stopVal=stopVal,
                 startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'RegionOfInterest'
        self.url = "https://www.psychopy.org/builder/components/roi.html"
        self.exp.requirePsychopyLibs(['iohub', 'hardware'])
        # params
        self.order += ['config']  # first param after the name

        # Delete all appearance parameters
        for param in list(self.params).copy():
            if self.params[param].categ in ["Appearance", "Texture"]:
                del self.params[param]

        self.params['endRoutineOn'] = Param(endRoutineOn,
            valType='str', inputType='choice', categ='Basic',
            allowedVals=["look at", "look away", "none"],
            hint=_translate("Under what condition should this ROI end the routine?"),
            label=_translate("End Routine On...")
        )

        self.params['lookDur'] = Param(lookDur,
            valType='num', inputType='single', categ='Basic',
            hint=_translate("How long (ms) does the participant need to look at the ROI to count as a look?"),
            label=_translate("Min. Look Time")
        )

        self.params['debug'] = Param(
            debug, valType='bool', inputType='bool', categ='Testing',
            hint=_translate("In debug mode, the ROI is drawn in red. Use this to see what area of the "
                            "screen is in the ROI."),
            label=_translate("Debug Mode")
        )

        self.params['save'] = Param(
            save, valType='str', inputType="choice", categ='Data',
            allowedVals=['first look', 'last look', 'every look', 'none'],
            hint=_translate(
                "What looks on this ROI should be saved to the data output?"),
            label=_translate('Save...'))

        self.params['timeRelativeTo'] = Param(
            timeRelativeTo, valType='str', inputType="choice", categ='Data',
            allowedVals=['roi onset', 'experiment', 'routine'],
            updates='constant',
            hint=_translate(
                "What should the values of mouse.time should be "
                "relative to?"),
            label=_translate('Time Relative To...'))

    def writePreWindowCode(self, buff):
        pass

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params
        # do writing of init
        inits = getInitVals(self.params, 'PsychoPy')
        code = (
            "%(name)s = visual.ROI(win, name='%(name)s', tracker=eyetracker,\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "debug=%(debug)s,\n"
                "shape=%(shape)s,\n"
                + unitsStr + "pos=%(pos)s, size=%(size)s, ori=0.0)\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # do writing of init
        inits = getInitVals(self.params, 'PsychoPy')
        # Write basics
        BaseVisualComponent.writeFrameCode(self, buff)
        buff.setIndentLevel(1, relative=True)
        code = (
            "%(name)s.status = STARTED\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        # String to get time
        if inits['timeRelativeTo'] == 'roi onset':
            timing = "%(name)s.clock.getTime()"
        elif inits['timeRelativeTo'] == 'experiment':
            timing = "globalClock.getTime()"
        elif inits['timeRelativeTo'] == 'routine':
            timing = "routineTimer.getTime()"
        else:
            timing = "globalClock.getTime()"
        # Assemble code
        code = (
            f"if %(name)s.status == STARTED:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            f"# check whether %(name)s has been looked in\n"
            f"if %(name)s.isLookedIn:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            f"if not %(name)s.wasLookedIn:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            f"%(name)s.timesOn.append({timing}) # store time of first look\n"
            f"%(name)s.timesOff.append({timing}) # store time looked until\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            f"else:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            f"%(name)s.timesOff[-1] = {timing} # update time looked until\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            f"%(name)s.wasLookedIn = True  # if %(name)s is still looked at next frame, it is not a new look\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            f"else:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            f"%(name)s.wasLookedIn = False  # if %(name)s is looked at next frame, it is a new look\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-2, relative=True)
        code = (
            f"else:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            f"%(name)s.clock.reset() # keep clock at 0 if roi hasn't started / has finished\n"
            f"%(name)s.wasLookedIn = False  # if %(name)s is looked at next frame, it is a new look\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)

    def writeRoutineEndCode(self, buff):
        BaseVisualComponent.writeRoutineEndCode(self, buff)
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler
        name = self.params['name']
        if self.params['save'] == 'first look':
            index = "[0]"
        elif self.params['save'] == 'last look':
            index = "[-1]"
        else:
            index = ""
        if self.params['save'] != 'none':
            code = (
                f"{currLoop.params['name']}.addData('{name}.numLooks', {name}.numLooks)\n"
                f"if {name}.numLooks:\n"
                f"   {currLoop.params['name']}.addData('{name}.timesOn', {name}.timesOn{index})\n"
                f"   {currLoop.params['name']}.addData('{name}.timesOff', {name}.timesOff{index})\n"
                f"else:\n"
                f"   {currLoop.params['name']}.addData('{name}.timesOn', \"\")\n"
                f"   {currLoop.params['name']}.addData('{name}.timesOff', \"\")\n"
            )
            buff.writeIndentedLines(code)

    def writeExperimentEndCode(self, buff):
        pass
