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

    def __init__(self, exp, parentName, name='', image="", latitude="", longitude=""):
        self.type = 'Unknown'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed
        self.params = {}
        self.depends = []
        super(PanoramaComponent, self).__init__(exp, parentName, name=name)
        self.order += [
            "image",
            "latitude",
            "longitude",
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
            "Horizontal look position, ranging from -1 (fully left) to 1 (fully right)"
        )
        self.params['longitude'] = Param(
            longitude, valType='code', inputType='single', categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Longitude")
        )
        msg = _translate(
            "Vertical look position, ranging from -1 (fully left) to 1 (fully right)"
        )
        self.params['latitude'] = Param(
            longitude, valType='code', inputType='single', categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Latitude")
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
            "# Create panorama stimulus for %(name)s\n"
            "%(name)s = visual.PanoramicImageStim(\n"
            "    win,\n"
            "    image=%(image)s,\n"
            "    latitude=%(latitude)s, longitude=%(longitude)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
