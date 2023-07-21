#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import Param, _translate, getInitVals, BaseVisualComponent


class ProgressComponent(BaseVisualComponent):
    """

    """
    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    version = "2023.2.0"
    iconFile = Path(__file__).parent / 'progress.png'
    tooltip = _translate('Progress: Present a progress bar, with values ranging from 0 to 1.')
    beta = True

    def __init__(self, exp, parentName, name='prog',
                 startType='time (s)', startVal=0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=True,
                 progress=0,
                 color="white", fillColor="None", borderColor="white", colorSpace="rgb",
                 opacity=1, lineWidth=4,
                 pos=(0, 0), size=(0.5, 0.5), anchor="center left", ori=0, units="height",
                 disabled=False):

        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        super(ProgressComponent, self).__init__(
            exp, parentName, name=name,
            units=units, color=color, fillColor=fillColor, borderColor=borderColor,
            pos=pos, size=size, ori=ori, colorSpace=colorSpace, opacity=opacity,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
            disabled=disabled
        )
        self.type = 'Progress'

        # Change labels for color params
        self.params['color'].label = _translate("Bar color")
        self.params['color'].hint = _translate(
            "Color of the filled part of the progress bar."
        )
        self.params['fillColor'].label = _translate("Back color")
        self.params['fillColor'].hint = _translate(
            "Color of the empty part of the progress bar."
        )
        self.params['borderColor'].label = _translate("Border color")
        self.params['borderColor'].hint = _translate(
            "Color of the line around the progress bar."
        )

        # --- Basic ---
        self.params['progress'] = Param(
            progress, valType='code', inputType="single", categ='Basic',
            updates='constant', allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate(
                "Value between 0 (not started) and 1 (complete) to set the progress bar to."
            ),
            label=_translate("Progress"))

        # --- Appearance ---
        msg = _translate("Width of the shape's line (always in pixels - this"
                         " does NOT use 'units')")
        self.params['lineWidth'] = Param(
            lineWidth, valType='num', inputType="single", allowedTypes=[], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate('Line width'))

        # --- Layout ---
        self.params['anchor'] = Param(
            anchor, valType='str', inputType="choice", categ='Layout',
            allowedVals=['center',
                         'top-center',
                         'bottom-center',
                         'center-left',
                         'center-right',
                         'top-left',
                         'top-right',
                         'bottom-left',
                         'bottom-right',
                         ],
            updates='constant',
            hint=_translate("Which point on the stimulus should be anchored to its exact position?"),
            label=_translate('Anchor'))

    def writeInitCode(self, buff):
        # Get inits
        inits = getInitVals(self.params, target="PsychoPy")
        inits['depth'] = -self.getPosInRoutine()
        # Create object
        code = (
            "%(name)s = visual.Progress(\n"
            "    win, name='%(name)s',\n"
            "    progress=%(progress)s,\n"
            "    pos=%(pos)s, size=%(size)s, anchor=%(anchor)s, units=%(units)s,\n"
            "    barColor=%(color)s, backColor=%(fillColor)s, borderColor=%(borderColor)s, "
            "colorSpace=%(colorSpace)s,\n"
            "    lineWidth=%(lineWidth)s, opacity=%(opacity)s, ori=%(ori)s,\n"
            "    depth=%(depth)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        # Get inits
        inits = getInitVals(self.params, target="PsychoJS")
        inits['depth'] = -self.getPosInRoutine()
        # Create object
        code = (
            "%(name)s = new visual.Progress({\n"
            "    win: psychoJS.window, name: '%(name)s',\n"
            "    progress: %(progress)s,\n"
            "    pos: %(pos)s, size: %(size)s, anchor: %(anchor)s, units: %(units)s,\n"
            "    barColor: %(color)s, backColor: %(fillColor)s, borderColor: %(borderColor)s, "
            "colorSpace: %(colorSpace)s,\n"
            "    lineWidth: %(lineWidth)s, opacity: %(opacity)s, ori: %(ori)s,\n"
            "    depth: %(depth)s\n"
            "})\n"
        )
        buff.writeIndentedLines(code % inits)
