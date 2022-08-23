#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import Param, _translate, getInitVals, BaseVisualComponent
from psychopy import prefs

# only use _localized values for label values, nothing functional:
_localized = {'name': _translate('Name')}


class PanoramaComponent(BaseVisualComponent):
    """This is used by Builder to represent a component that was not known
    by the current installed version of PsychoPy (most likely from the future).
    We want this to be loaded, represented and saved but not used in any
    script-outputs. It should have nothing but a name - other params will be
    added by the loader
    """
    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'panorama.png'
    tooltip = _translate('Panorama: Present a panoramic image (such as from a phone camera in Panorama mode) on '
                         'screen.')

    def __init__(self, exp, parentName, name='pan',
                 startType='time (s)', startVal=0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=True,
                 image="", controlStyle="mouse", smooth=True, sensitivity=1,
                 altitude="", azimuth=""):
        self.type = 'Panorama'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        super(PanoramaComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
        )
        self.order += [
            "image",
            "controlStyle",
            "latitude",
            "longitude",
            "sensitivity",
            "smooth",
        ]

        msg = _translate(
            "The image to be displayed - a filename, including path"
        )
        self.params['image'] = Param(
            image, valType='file', inputType="file", allowedTypes=[], categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Image"))
        msg = _translate(
            "How to control looking around the panorama scene"
        )
        self.params['controlStyle'] = Param(
            controlStyle, valType='str', inputType="choice", categ="Basic",
            allowedVals=["mouse", "drag", "arrows", "wasd", "custom"],
            allowedLabels=["Mouse", "Drag", "Keyboard (Arrow Keys)", "Keyboard (WASD)", "Custom"],
            updates="constant",
            hint=msg,
            label=_translate("Control Style")
        )
        self.depends.append(
            {
                "dependsOn": "controlStyle",  # if...
                "condition": "=='custom'",  # meets...
                "param": "azimuth",  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            }
        )
        msg = _translate(
            "Horizontal look position, ranging from -1 (fully left) to 1 (fully right)"
        )
        self.params['azimuth'] = Param(
            azimuth, valType='code', inputType='single', categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Azimuth")
        )
        self.depends.append(
            {
                "dependsOn": "controlStyle",  # if...
                "condition": "=='custom'",  # meets...
                "param": "altitude",  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            }
        )
        msg = _translate(
            "Vertical look position, ranging from -1 (fully left) to 1 (fully right)"
        )
        self.params['altitude'] = Param(
            altitude, valType='code', inputType='single', categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Altitude")
        )
        self.depends.append(
            {
                "dependsOn": "controlStyle",  # if...
                "condition": "in ('custom', 'mouse')",  # meets...
                "param": "smooth",  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            }
        )
        msg = _translate(
            "Should movement be smoothed, so the view keeps moving a little after a change?"
        )
        self.params['smooth'] = Param(
            smooth, valType='bool', inputType="bool", categ="Basic",
            updates="constant",
            hint=msg,
            label=_translate("Smooth?")
        )
        self.depends.append(
            {
                "dependsOn": "controlStyle",  # if...
                "condition": "=='custom'",  # meets...
                "param": "sensitivity",  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            }
        )
        msg = _translate(
            "Multiplier to apply to view changes. 1 means that moving the mouse from the center of the screen to the "
            "edge or holding down a key for 2s will rotate 180°."
        )
        self.params['sensitivity'] = Param(
            sensitivity, valType='code', inputType="single", categ="Basic",
            updates="sensitivity",
            hint=msg,
            label=_translate("Sensitivity")
        )
        # Most params don't apply to 3d stim, so delete them
        for key in ["color", "fillColor", "borderColor", "colorSpace", "opacity", "contrast", "size", "pos", "units", "ori"]:
            del self.params[key]

    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        pass

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, target="PsychoPy")
        code = (
            "\n"
            "# create panorama stimulus for %(name)s\n"
            "%(name)s = visual.PanoramicImageStim(\n"
            "    win,\n"
            "    image=%(image)s,\n"
            "    altitude=%(altitude)s, azimuth=%(azimuth)s\n"
            ")\n"
            "# add attribute to keep track of last movement\n"
            "%(name)s.momentum = np.asarray([0.0, 0.0])\n"
        )
        buff.writeIndentedLines(code % inits)
        # Add control handler if needed
        if self.params['controlStyle'].val in ("mouse", "drag"):
            code = (
                "# add control handler for %(name)s\n"
                "%(name)s.ctrl = event.Mouse()\n"
            )
            buff.writeIndentedLines(code % inits)
        elif self.params['controlStyle'].val in ("arrows", "wasd"):
            # If keyboard, add mapping of keys to deltas
            code = (
                "# add control handler for %(name)s\n"
                "%(name)s.ctrl = keyboard.Keyboard()\n"
                "# store a dictionary to map keys to the amount to change by per frame\n"
                "%(name)s.ctrl.deltas = {{\n"
                "    '{u}': np.array([0, -win.monitorFramePeriod]),\n"
                "    '{l}': np.array([-win.monitorFramePeriod, 0]),\n"
                "    '{d}': np.array([0, +win.monitorFramePeriod]),\n"
                "    '{r}': np.array([+win.monitorFramePeriod, 0]),\n"
                "    'space': np.array([0, 0]),\n"
                "}}\n"
            )
            if self.params['controlStyle'].val == "wasd":
                # If WASD, sub in w, a, s and d
                code = code.format(u="w", l="a", d="s", r="d")
            else:
                # If arrows, sub in left, right, up and down
                code = code.format(l="left", r="right", u="up", d="down")
            buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        # If control style isn't custom, make sure altitude and azimuth aren't updated each frame
        if self.params['controlStyle'].val != "custom":
            self.params['azimuth'].updates = "constant"
            self.params['altitude'].updates = "constant"

        # Start code
        if self.writeStartTestCode(buff):
            code = (
                "# start drawing %(name)s\n"
                "%(name)s.setAutoDraw(True)\n"
            )
            buff.writeIndentedLines(code % self.params)
            self.exitStartTest(buff)

        # Active code
        self.writeActiveTestCode(buff)

        if self.params['controlStyle'].val == "mouse":
            # If control style is mouse, set azimuth and elevation according to mouse pos
            code = (
                "# update panorama view from mouse pos\n"
                "pos = layout.Position(%(name)s.ctrl.getPos(), win.units, win)\n"
                "%(name)s.azimuth = pos.norm[0] * %(sensitivity)s\n"
                "%(name)s.altitude = -pos.norm[1] * %(sensitivity)s\n"
            )
            buff.writeIndentedLines(code % self.params)

        elif self.params['controlStyle'].val == "drag":
            # If control style is drag, set azimuth and elevation according to change in mouse pos
            code = (
                "# update panorama view from mouse change if clicked\n"
                "rel = layout.Position(%(name)s.ctrl.getRel(), win.units, win)\n"
                "if %(name)s.ctrl.getPressed()[0]:\n"
                "    %(name)s.momentum = rel.norm * %(sensitivity)s\n"
                "    %(name)s.azimuth -= %(name)s.momentum[0]\n"
                "    %(name)s.altitude += %(name)s.momentum[1]\n"
            )
            buff.writeIndentedLines(code % self.params)
            if self.params['smooth']:
                # If smoothing requested, let momentum decay sinusoidally
                code = (
                "else:\n"
                "    # after click, keep moving a little\n"
                "    %(name)s.azimuth -= %(name)s.momentum[0]\n"
                "    %(name)s.altitude += %(name)s.momentum[1]\n"
                "    # decrease momentum every frame so that it approaches 0\n"
                "    %(name)s.momentum = %(name)s.momentum * (1 - win.monitorFramePeriod * 2)\n"
                )
                buff.writeIndentedLines(code % self.params)

        elif self.params['controlStyle'].val in ("arrows", "wasd"):
            # If control is keyboard, set azimuth and elevation according to keypresses
            code = (
                "# update panorama view from key presses\n"
                "keys = %(name)s.ctrl.getKeys(list(%(name)s.ctrl.deltas), waitRelease=False, clear=False)\n"
                "if len(keys):\n"
                "    # work out momentum of movement from keys pressed\n"
                "    %(name)s.momentum = np.asarray([0.0, 0.0])\n"
                "    for key in keys:\n"
                "        %(name)s.momentum += %(name)s.ctrl.deltas[key.name] * %(sensitivity)s\n"
                "    # apply momentum to panorama view\n"
                "    %(name)s.azimuth += %(name)s.momentum[0]\n"
                "    %(name)s.altitude += %(name)s.momentum[1]\n"
                "    # get keys which have been released and clear them from the buffer before next frame\n"
                "    %(name)s.ctrl.getKeys(list(%(name)s.ctrl.deltas), waitRelease=True, clear=True)\n"
            )
            buff.writeIndentedLines(code % self.params)
            if self.params['smooth']:
                # If smoothing requested, let momentum decay sinusoidally
                code = (
                "else:\n"
                "    # after pressing, keep moving a little\n"
                "    %(name)s.azimuth += %(name)s.momentum[0]\n"
                "    %(name)s.altitude += %(name)s.momentum[1]\n"
                "    # decrease momentum every frame so that it approaches 0\n"
                "    %(name)s.momentum = %(name)s.momentum * (1 - win.monitorFramePeriod * 2)\n"
                )
                buff.writeIndentedLines(code % self.params)

        self.exitActiveTest(buff)

        # Stop code
        if self.writeStopTestCode(buff):
            code = (
                "# Stop drawing %(name)s\n"
                "%(name)s.setAutoDraw(False)\n"
            )
            buff.writeIndentedLines(code % self.params)
            self.exitStopTest(buff)
