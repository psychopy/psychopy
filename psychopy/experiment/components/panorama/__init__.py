#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import Param, _translate, getInitVals, BaseVisualComponent
from psychopy import prefs

# only use _localized values for label values, nothing functional:
_localized = {'name': _translate("Name")}


class PanoramaComponent(BaseVisualComponent):
    """This is used by Builder to represent a component that was not known
    by the current installed version of PsychoPy (most likely from the future).
    We want this to be loaded, represented and saved but not used in any
    script-outputs. It should have nothing but a name - other params will be
    added by the loader
    """
    categories = ['Stimuli']
    targets = ['PsychoPy']
    version = "2023.1.0"
    iconFile = Path(__file__).parent / 'panorama.png'
    tooltip = _translate('Panorama: Present a panoramic image (such as from a phone camera in Panorama mode) on '
                         'screen.')
    beta = True

    def __init__(self, exp, parentName, name='pan',
                 startType='time (s)', startVal=0,
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=True,
                 image="",
                 interpolate='linear',
                 posCtrl="mouse", smooth=True, posSensitivity=1,
                 elevation="", azimuth="",
                 zoomCtrl="wheel",
                 zoom=1, zoomSensitivity=1,
                 inKey="up", outKey="down",
                 upKey="w", leftKey="a", downKey="s", rightKey="d", stopKey="space"):

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
        self.type = 'Panorama'

        self.order += [
            "image",
            "posCtrl",
            "azimuth", "elevation",
            "upKey", "leftKey", "downKey", "rightKey", "stopKey",
            "posSensitivity",
            "smooth",
            "zoomCtrl",
            "zoom",
            "inKey", "outKey",
            "zoomSensitivity"
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
            "How should the image be interpolated if/when rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice",
            allowedVals=['linear', 'nearest'], categ='Basic',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Interpolate"))

        # Position controls
        
        msg = _translate(
            "How to control looking around the panorama scene"
        )
        self.params['posCtrl'] = Param(
            posCtrl, valType='str', inputType="choice", categ="Basic",
            allowedVals=[
                "mouse", "drag", "arrows", "wasd", "keymap", "custom"],
            allowedLabels=[
                "Mouse", "Drag", "Keyboard (Arrow Keys)", "Keyboard (WASD)", "Keyboard (Custom keys)", "Custom"],
            updates="constant",
            hint=msg,
            label=_translate("Position control")
        )
        
        self.depends.append(
            {
                "dependsOn": "posCtrl",  # if...
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
                "dependsOn": "posCtrl",  # if...
                "condition": "=='custom'",  # meets...
                "param": "elevation",  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            }
        )
        msg = _translate(
            "Vertical look position, ranging from -1 (fully down) to 1 (fully up)"
        )
        self.params['elevation'] = Param(
            elevation, valType='code', inputType='single', categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Elevation")
        )
        keys = {'upKey': upKey, 'leftKey': leftKey, 'downKey': downKey, 'rightKey': rightKey, 'stopKey': stopKey}
        labels = {'upKey': _translate("Up"), 'leftKey': _translate("Left"), 'downKey': _translate("Down"),
                  'rightKey': _translate("Right"), 'stopKey': _translate("Stop")}
        for key, val in keys.items():
            # Only show key controls if control type is custom keys
            self.depends.append(
                {
                    "dependsOn": "posCtrl",  # if...
                    "condition": "=='keymap'",  # meets...
                    "param": key,  # then...
                    "true": "show",  # should...
                    "false": "hide",  # otherwise...
                }
            )
            # Add a ctrl for each key
            msg = _translate("What key corresponds to the view action '{}'?")
            self.params[key] = Param(
                val, valType='str', inputType='single', categ='Basic',
                updates='constant',
                hint=msg.format(labels[key]),
                label=labels[key]
            )

        self.depends.append(
            {
                "dependsOn": "posCtrl",  # if...
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
                "dependsOn": "posCtrl",  # if...
                "condition": "=='custom'",  # meets...
                "param": "posSensitivity",  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            }
        )
        msg = _translate(
            "Multiplier to apply to view changes. 1 means that moving the mouse from the center of the screen to the "
            "edge or holding down a key for 2s will rotate 180°."
        )
        self.params['posSensitivity'] = Param(
            posSensitivity, valType='code', inputType="single", categ="Basic",
            hint=msg,
            label=_translate("Movement sensitivity")
        )

        # Zoom controls

        msg = _translate(
            "How to control zooming in and out of the panorama scene"
        )
        self.params['zoomCtrl'] = Param(
            zoomCtrl, valType='str', inputType="choice", categ="Basic",
            allowedVals=[
                "wheel", "invwheel", "arrows", "plusmin", "keymap", "custom"],
            allowedLabels=[
                "Mouse Wheel", "Mouse Wheel (Inverted)", "Keyboard (Arrow Keys)", "Keyboard (+-)", "Keyboard (Custom keys)", "Custom"],
            updates="constant",
            hint=msg,
            label=_translate("Zoom control")
        )

        keys = {'inKey': inKey, 'outKey': outKey}
        labels = {'inKey': _translate("Zoom in"), 'outKey': _translate("Zoom out")}
        for key, val in keys.items():
            # Only show key controls if zoom type is custom keys
            self.depends.append(
                {
                    "dependsOn": "zoomCtrl",  # if...
                    "condition": "=='keymap'",  # meets...
                    "param": key,  # then...
                    "true": "show",  # should...
                    "false": "hide",  # otherwise...
                },
            )
            # Add a ctrl for each key
            msg = _translate("What key corresponds to the view action '{}'?")
            self.params[key] = Param(
                val, valType='str', inputType='single', categ='Basic',
                updates='constant',
                hint=msg.format(labels[key]),
                label=labels[key]
            )

        self.depends.append(
            {
                "dependsOn": "zoomCtrl",  # if...
                "condition": "=='custom'",  # meets...
                "param": "zoom",  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            }
        )
        msg = _translate(
            "How zoomed in the scene is, with 1 being no adjustment."
        )
        self.params['zoom'] = Param(
            zoom, valType='code', inputType='single', categ='Basic',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Zoom")
        )

        self.depends.append(
            {
                "dependsOn": "zoomCtrl",  # if...
                "condition": "=='custom'",  # meets...
                "param": "zoomSensitivity",  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            }
        )
        msg = _translate(
            "Multiplier to apply to zoom changes. 1 means that pressing the zoom in key for 1s or scrolling the mouse "
            "wheel 100% zooms in 100%."
        )
        self.params['zoomSensitivity'] = Param(
            zoomSensitivity, valType='code', inputType="single", categ="Basic",
            hint=msg,
            label=_translate("Zoom sensitivity")
        )


        # Most params don't apply to 3d stim, so delete them
        for key in ["color", "fillColor", "borderColor", "colorSpace", "opacity", "contrast", "size", "pos", "units", "ori"]:
            del self.params[key]

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
            "    elevation=%(elevation)s, azimuth=%(azimuth)s,\n"
            "    interpolate=%(interpolate)s\n"
            ")\n"
            "# add attribute to keep track of last movement\n"
            "%(name)s.momentum = np.asarray([0.0, 0.0])\n"
        )
        buff.writeIndentedLines(code % inits)
        # Add control handlers
        code = (
            "# add control handlers for %(name)s\n"
            "%(name)s.mouse = event.Mouse()\n"
            "%(name)s.kb = keyboard.Keyboard()\n"
        )
        buff.writeIndentedLines(code % inits)
        if self.params['posCtrl'].val in ("arrows", "wasd", "keymap"):
            # If keyboard, add mapping of keys to deltas
            code = (
                "# store a dictionary to map keys to the amount to change by per frame\n"
                "%(name)s.kb.deltas = {{\n"
                "    {u}: np.array([0, +win.monitorFramePeriod]),\n"
                "    {l}: np.array([-win.monitorFramePeriod, 0]),\n"
                "    {d}: np.array([0, -win.monitorFramePeriod]),\n"
                "    {r}: np.array([+win.monitorFramePeriod, 0]),\n"
                "    {x}: np.array([0, 0]),\n"
                "}}\n"
            )
            if self.params['posCtrl'].val == "wasd":
                # If WASD, sub in w, a, s and d
                code = code.format(u="'w'", l="'a'", d="'s'", r="'d'", x="'space'")
            elif self.params['posCtrl'].val == "arrows":
                # If arrows, sub in left, right, up and down
                code = code.format(l="'left'", r="'right'", u="'up'", d="'down'", x="'space'")
            else:
                # Otherwise, use custom keys
                code = code.format(
                    l=self.params['leftKey'], r=self.params['rightKey'], u=self.params['upKey'],
                    d=self.params['downKey'], x=self.params['stopKey'])
            buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        # If control style isn't custom, make sure elevation, azimuth and zoom aren't updated each frame
        if self.params['posCtrl'].val != "custom":
            self.params['azimuth'].updates = "constant"
            self.params['elevation'].updates = "constant"
        if self.params['zoomCtrl'].val != "custom":
            self.params['zoom'].updates = "constant"

        # Start code
        indented = self.writeStartTestCode(buff)
        if indented:
            code = (
                "# start drawing %(name)s\n"
                "%(name)s.setAutoDraw(True)\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # Active code
        indented = self.writeActiveTestCode(buff)
        if indented:
            # Pos control code
            if self.params['posCtrl'].val == "mouse":
                # If control style is mouse, set azimuth and elevation according to mouse pos
                code = (
                    "# update panorama view from mouse pos\n"
                    "pos = layout.Position(%(name)s.mouse.getPos(), win.units, win)\n"
                    "%(name)s.azimuth = -pos.norm[0] * %(posSensitivity)s\n"
                    "%(name)s.elevation = -pos.norm[1] * %(posSensitivity)s\n"
                )
                buff.writeIndentedLines(code % self.params)

            elif self.params['posCtrl'].val == "drag":
                # If control style is drag, set azimuth and elevation according to change in mouse pos
                code = (
                    "# update panorama view from mouse change if clicked\n"
                    "rel = layout.Position(%(name)s.mouse.getRel(), win.units, win)\n"
                    "if %(name)s.mouse.getPressed()[0]:\n"
                    "    %(name)s.momentum = rel.norm * %(posSensitivity)s\n"
                    "    %(name)s.azimuth -= %(name)s.momentum[0]\n"
                    "    %(name)s.elevation -= %(name)s.momentum[1]\n"
                )
                buff.writeIndentedLines(code % self.params)
                if self.params['smooth']:
                    # If smoothing requested, let momentum decay sinusoidally
                    code = (
                    "else:\n"
                    "    # after click, keep moving a little\n"
                    "    %(name)s.azimuth -= %(name)s.momentum[0]\n"
                    "    %(name)s.elevation -= %(name)s.momentum[1]\n"
                    "    # decrease momentum every frame so that it approaches 0\n"
                    "    %(name)s.momentum = %(name)s.momentum * (1 - win.monitorFramePeriod * 2)\n"
                    )
                    buff.writeIndentedLines(code % self.params)

            elif self.params['posCtrl'].val in ("arrows", "wasd", "keymap"):
                # If control is keyboard, set azimuth and elevation according to keypresses
                code = (
                    "# update panorama view from key presses\n"
                    "keys = %(name)s.kb.getKeys(list(%(name)s.kb.deltas), waitRelease=False, clear=False)\n"
                    "if len(keys):\n"
                    "    # work out momentum of movement from keys pressed\n"
                    "    %(name)s.momentum = np.asarray([0.0, 0.0])\n"
                    "    for key in keys:\n"
                    "        %(name)s.momentum += %(name)s.kb.deltas[key.name] * %(posSensitivity)s\n"
                    "    # apply momentum to panorama view\n"
                    "    %(name)s.azimuth += %(name)s.momentum[0]\n"
                    "    %(name)s.elevation += %(name)s.momentum[1]\n"
                    "    # get keys which have been released and clear them from the buffer before next frame\n"
                    "    %(name)s.kb.getKeys(list(%(name)s.kb.deltas), waitRelease=True, clear=True)\n"
                )
                buff.writeIndentedLines(code % self.params)
                if self.params['smooth']:
                    # If smoothing requested, let momentum decay sinusoidally
                    code = (
                    "else:\n"
                    "    # after pressing, keep moving a little\n"
                    "    %(name)s.azimuth += %(name)s.momentum[0]\n"
                    "    %(name)s.elevation += %(name)s.momentum[1]\n"
                    "    # decrease momentum every frame so that it approaches 0\n"
                    "    %(name)s.momentum = %(name)s.momentum * (1 - win.monitorFramePeriod * 4)\n"
                    )
                    buff.writeIndentedLines(code % self.params)

            # Zoom control code
            if self.params['zoomCtrl'].val in ("wheel", "invwheel"):
                # If control style is wheel, set zoom from mouse wheel
                if self.params['zoomCtrl'].val == "invwheel":
                    _op = "-="
                else:
                    _op = "+="
                code = (
                    f"# update panorama zoom from mouse wheel\n"
                    f"%(name)s.zoom {_op} %(name)s.mouse.getWheelRel()[1] * %(zoomSensitivity)s * win.monitorFramePeriod * 4\n"
                )
                buff.writeIndentedLines(code % self.params)
            elif self.params['zoomCtrl'].val in ("arrows", "plusmin", "keymap"):
                # If control style is key based, get keys from params/presets and set from pressed
                if self.params['zoomCtrl'].val == "arrows":
                    inKey, outKey = ("'up'", "'down'")
                elif self.params['zoomCtrl'].val == "plusmin":
                    inKey, outKey = ("'equal'", "'minus'")
                else:
                    inKey, outKey = (self.params['inKey'], self.params['outKey'])
                code = (
                    f"# update panorama zoom from key presses\n"
                    f"keys = %(name)s.kb.getKeys([{inKey}, {outKey}], waitRelease=False, clear=False)\n"
                    f"# work out zoom change from keys pressed\n"
                    f"for key in keys:\n"
                    f"    if key.name == {inKey}:\n"
                    f"        %(name)s.zoom += %(zoomSensitivity)s * win.monitorFramePeriod * 4\n"
                    f"    if key.name == {outKey}:\n"
                    f"        %(name)s.zoom -= %(zoomSensitivity)s * win.monitorFramePeriod * 4\n"
                    f"# get keys which have been released and clear them from the buffer before next frame\n"
                    f"%(name)s.kb.getKeys([{inKey}, {outKey}], waitRelease=True, clear=True)\n"
                )
                buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # Stop code
        indented = self.writeStopTestCode(buff)
        if indented:
            code = (
                "# Stop drawing %(name)s\n"
                "%(name)s.setAutoDraw(False)\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)
