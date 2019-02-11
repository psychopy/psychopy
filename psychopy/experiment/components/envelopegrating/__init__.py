#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'envgrating.png')
tooltip = _translate('Envelope Grating: present cyclic textures including 2nd order envelope stimuli, prebuilt or from a '
                     'file')

# only use _localized values for label values, nothing functional:
_localized = {'carrier': _translate('Carrier texture'),
              'ori': _translate('Carrier Orientation'),
              'mask': _translate('Mask'),
              'sf': _translate('Carrier spatial frequency'),
              'phase': _translate('Carrier phase (in cycles)'),
              'contrast': _translate('Carrier contrast'),
              'texture resolution': _translate('Texture resolution'),
              'interpolate': _translate('Interpolate'),
              'envelope': _translate('Envelope texture'),
              'envsf':_translate('Envelope spatial frequency'),
              'envori':_translate('Envelope orientation'),
              'envphase':_translate('Envelope phase'),
              'moddepth':_translate('Envelope modulation depth'),
              'beat':_translate('Is modulation a beat'),
              'blendmode':_translate('OpenGL blend mode')
              }


class EnvGratingComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    def __init__(self, exp, parentName, name='env_grating', carrier='sin',
                 mask='None', sf=1.0, interpolate='linear',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 pos=(0, 0), size=(0.5, 0.5), ori=0, phase=0.0, texRes='128',
                 envelope='sin',envsf=1.0,envori=0.0,envphase=0.0, beat=False, contrast=0.5, moddepth=1.0, blendmode='avg',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        super().__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'EnvGrating'
        self.url = "http://www.psychopy.org/builder/components/EnvelopeGrating.html"
        self.order = ['carrier', 'mask']

        # params

        self.params['ori'] = Param(
            ori, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate("Orientation of this stimulus (in deg)"),
            label=_localized['ori'],categ="Carrier")

        msg = _translate("The (2D) texture of the background - can be sin, sqr,"
                         " sinXsin... or a filename (including path)")
        self.params['carrier'] = Param(
            carrier, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['carrier'], categ="Carrier")

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['mask'], categ="Carrier")

        msg = _translate("Contrast of background carrier")
        self.params['contrast'] = Param(
            contrast, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['contrast'], categ="Carrier")

        msg = _translate("Spatial frequency of background carrier repeats across the "
                         "grating in 1 or 2 dimensions, e.g. 4 or [2,3]")
        self.params['sf'] = Param(
            sf, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['sf'], categ="Carrier")

        msg = _translate("Spatial positioning of the background carrier "
                         "(wraps in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['phase'], categ="Carrier")

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes,
            valType='code', allowedVals=['32', '64', '128', '256', '512'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['texture resolution'], categ="Carrier")

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', allowedVals=['linear', 'nearest'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['interpolate'], categ="Carrier")


        msg = _translate("The (2D) texture of the envelope - can be sin, sqr,"
                         " sinXsin... or a filename (including path)")
        self.params['envelope'] = Param(
            envelope, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envelope'], categ="Envelope")

        msg = _translate("Spatial frequency of the modulation envelope repeats across the "
                         "grating in 1 or 2 dimensions, e.g. 4 or [2,3]")
        self.params['envsf'] = Param(
            envsf, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envsf'], categ="Envelope")

        msg = _translate("Spatial positioning of the modulation envelope"
                         "(wraps in range 0-1.0)")
        self.params['envphase'] = Param(
            envphase, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envphase'], categ="Envelope")

        msg = _translate("Orientation of the modulation envelope"
                         "(wraps in range 0-360)")
        self.params['envori'] = Param(
            envori, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envori'], categ="Envelope")

        msg = _translate("Modulation depth of modulation envelope")
        self.params['moddepth'] = Param(
            moddepth, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['moddepth'], categ="Envelope")

        msg = _translate("Do you want a 'beat'? [beat = carrier*envelope, "
                         "no beat = carrier*(1+envelope), True/False, Y/N]")
        self.params['beat'] = Param(
            beat, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['beat'], categ="Envelope")

        msg = _translate("OpenGL Blendmode. Avg is most common mode"
                         " in PsychoPy, add is useful if combining a beat with"
                         " the carrier image or numpy array at point of display")
        self.params['blendmode'] = Param(
            blendmode, valType='str', allowedVals=['avg', 'add'],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['blendmode'], categ="Basic")

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params
        #buff.writeIndented("from psychopy.visual.secondorder import EnvelopeGrating\n")

        # replaces variable params with defaults and sets sample updating flag
        inits = getInitVals(self.params)

        code = ("%s = visual.EnvelopeGrating(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                "    carrier=%(carrier)s, mask=%(mask)s,\n" % inits +
                "    ori=%(ori)s, pos=%(pos)s, size=%(size)s, " % inits +
                "sf=%(sf)s, phase=%(phase)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s, " % inits +
                "opacity=%(opacity)s, contrast=%(contrast)s,\n" % inits +
                # no newline - start optional parameters
                "    texRes=%(texture resolution)s,\n" % inits +
                "    envelope=%(envelope)s, envori=%(envori)s,\n" % inits +
                "    envsf=%(envsf)s, envphase=%(envphase)s, moddepth=%(moddepth)s, blendmode=%(blendmode)s" %inits )

        if self.params['beat'].val in ['Y','y','Yes', 'yes','True','true']:
            code += ", beat=True"
        elif self.params['beat'].val in ['N','n','No', 'no','False','false']:
            code += ", beat=False"
        else:
            code += ", beat=%(beat)s" %inits

        if self.params['interpolate'].val == 'linear':
            code += ", interpolate=True"
        else:
            code += ", interpolate=False"
        depth = -self.getPosInRoutine()
        code += ", depth=%.1f)\n" % depth
        buff.writeIndentedLines(code)

    def writeRoutineStartCode(self,buff):
        super().writeRoutineStartCode(buff)
        #if self.params['blendmode'].val!='default':
            #buff.writeIndented("__allEnvSaveBlendMode=win.blendMode #required to clean up after %(name)s\n" %self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % self.params['name'])
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.setAutoDraw(True)\n" % self.params)
        #if self.params['blendmode'].val!='default':
            #buff.writeIndented("%(name)s_SaveBlendMode=win.blendMode\n" %self.params)
            #buff.writeIndented("win.blendMode=%(blendmode)s\n" %self.params)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ('', None, -1, 'None'):
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" % self.params)
            #if self.params['blendmode'].val!='default':
                #buff.writeIndented("win.blendMode=%(name)s_SaveBlendMode\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            code = "if %(name)s.status == STARTED:  # only update if drawing\n"
            buff.writeIndented(code % self.params)
            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block

    def writeRoutineEndCode(self, buff):
        super().writeRoutineEndCode(buff)  # adds start/stop times to data
        #if self.params['blendmode'].val!='default':
            #buff.writeIndented("win.blendMode=__allEnvSaveBlendMode #clean up for %(name)s\n" %self.params)

