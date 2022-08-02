import json

from psychopy.experiment import Param
from psychopy.experiment.components import BaseVisualComponent, getInitVals
from psychopy.localization import _translate
from pathlib import Path


class AnimationComponent(BaseVisualComponent):
    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'animation.png'
    tooltip = _translate('Animation: Display a set of images sequentially as an animation.')

    def __init__(self, exp, parentName, name='animation',
                 images='', frameRate=12, frameStart=0, loop=True, mask='',
                 interpolate='linear', units='from exp settings',
                 color='$[1,1,1]', colorSpace='rgb', pos=(0, 0),
                 size=(0.5, 0.5), anchor="center", ori=0, texRes='128', flipVert=False,
                 flipHoriz=False,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        BaseVisualComponent.__init__(
            self, exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'Animation'
        self.url = "https://www.psychopy.org/builder/components/animation.html"
        self.exp.requirePsychopyLibs(['visual'])

        msg = _translate("List of images to use as frames")
        self.params['images'] = Param(
            images, valType='list', inputType='fileList', categ='Basic',
            hint=msg,
            label=_translate("Images")
        )
        msg = _translate("How many times should the frame advance, per second?")
        self.params['frameRate'] = Param(
            frameRate, valType='code', inputType='single', categ='Basic',
            hint=msg,
            label=_translate("Frame Rate (FPS)")
        )
        msg = _translate("Start at frame...")
        self.params['frameStart'] = Param(
            frameStart, valType='code', inputType='single', categ='Basic',
            hint=msg,
            label=_translate("First Frame")
        )
        msg = _translate("When the animation finishes, should it loop?")
        self.params['loop'] = Param(
            loop, valType='bool', inputType='bool', categ='Basic',
            hint=msg,
            label=_translate("Loop?")
        )

        msg = _translate("Resolution of the mask if one is used.")
        self.params['texture resolution'] = Param(
            texRes, valType='num', inputType="choice", categ='Texture',
            allowedVals=['32', '64', '128', '256', '512'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Texture Resolution"))

        msg = _translate(
            "How should the image be interpolated if/when rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_translate("Interpolate"))

        msg = _translate(
            "Should the image be flipped vertically (top to bottom)?")
        self.params['flipVert'] = Param(
            flipVert, valType='bool', inputType="bool", categ='Layout',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Flip Vertical"))

        msg = _translate(
            "Should the image be flipped horizontally (left to right)?")
        self.params['flipHoriz'] = Param(
            flipHoriz, valType='bool', inputType="bool", categ='Layout',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Flip Horizontal"))
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

        del self.params['fillColor']
        del self.params['borderColor']

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, 'PsychoPy')

        # Alias interpolation modes
        if inits['interpolate'].val == 'linear':
            inits['interpolate'].val = True
        else:
            inits['interpolate'].val = False

        # Trim image list
        inits['images'].val = json.loads(inits['images'].val.replace("'", "\""))
        if "" in inits['images'].val:
            inits['images'].val.remove("")
        print(type(inits['images'].val), inits['images'].val)

        # Alias units
        if str(inits['units'].val).lower() in ("from experiment settings", "from exp settings", "none"):
            inits['units'].val = None
            inits['units'].valType = 'code'

        # Create object
        code = (
            "%(name)s = visual.FrameAnimation(\n"
            "    win, name='%(name)s', images=%(images)s,\n"
            "    frameRate=%(frameRate)s, frameStart=%(frameStart)s, loop=%(loop)s,\n"
            "    pos=%(pos)s, size=%(size)s, anchor=%(anchor)s, units=%(units)s,\n"
            "    ori=%(ori)s, flipHoriz=%(flipHoriz)s, flipVert=%(flipVert)s,\n"
            "    color=%(color)s, contrast=%(contrast)s, opacity=%(opacity)s, colorSpace=%(colorSpace)s,\n"
            "    texRes=%(texture resolution)s, interpolate=%(interpolate)s,\n"
            "    autoLog=True\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
