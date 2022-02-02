#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# only use _localized values for label values, nothing functional:
_localized.update({'carrier': _translate('Carrier texture'),
                   'ori': _translate('Carrier Orientation'),
                   'mask': _translate('Mask'),
                   'sf': _translate('Carrier spatial frequency'),
                   'phase': _translate('Carrier phase (in cycles)'),
                   'contrast': _translate('Carrier contrast'),
                   'texture resolution': _translate('Texture resolution'),
                   'interpolate': _translate('Interpolate'),
                   'envelope': _translate('Envelope texture'),
                   'envsf': _translate('Envelope spatial frequency'),
                   'envori': _translate('Envelope orientation'),
                   'envphase': _translate('Envelope phase'),
                   'moddepth': _translate('Envelope modulation depth'),
                   'power': _translate('Power to which envelope is raised'),
                   'beat': _translate('Is modulation a beat'),
                   'blendmode': _translate('OpenGL blend mode')})


class EnvGratingComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'envelopegrating.png'
    tooltip = _translate('Envelope Grating: present cyclic textures including 2nd order envelope stimuli, '
                         'prebuilt or from a file')

    def __init__(self, exp, parentName, name='env_grating', carrier='sin',
                 mask='None', sf=1.0, interpolate='linear',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 pos=(0, 0), size=(0.5, 0.5), anchor="center", ori=0, phase=0.0, texRes='128',
                 envelope='sin',envsf=1.0,envori=0.0,envphase=0.0, 
                 beat=False, power=1.0,
                 contrast=0.5, moddepth=1.0, blendmode='avg',
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
        self.url = "https://www.psychopy.org/builder/components/EnvelopeGrating.html"
        self.order = ['carrier', 'mask']

        # params

        self.params['ori'].categ = "Carrier"

        msg = _translate("The (2D) texture of the background - can be sin, sqr,"
                         " sinXsin... or a filename (including path)")
        self.params['carrier'] = Param(
            carrier, valType='file', inputType="file", allowedTypes=[], allowedVals=["sin", "sqr", "sinXsin"], categ="Carrier",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['carrier'])

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='file', inputType="file", allowedVals=["gauss", "circle"], allowedTypes=[], categ="Carrier",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['mask'])

        msg = _translate("Contrast of background carrier")
        self.params['contrast'] = Param(
            contrast, valType='num', inputType="single", allowedTypes=[], categ="Carrier",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['contrast'])

        msg = _translate("Spatial frequency of background carrier repeats across the "
                         "grating in 1 or 2 dimensions, e.g. 4 or [2,3]")
        self.params['sf'] = Param(
            sf, valType='num', inputType="single", allowedTypes=[], categ="Carrier",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['sf'])

        msg = _translate("Spatial positioning of the background carrier "
                         "(wraps in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='num', inputType="single", allowedTypes=[], categ="Carrier",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['phase'])

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes,
            valType='code', inputType="choice", allowedVals=['32', '64', '128', '256', '512'], categ="Carrier",
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['texture resolution'])

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ="Carrier",
            updates='constant', allowedUpdates=[],
            hint=msg, direct=False,
            label=_localized['interpolate'])

        msg = _translate("The (2D) texture of the envelope - can be sin, sqr,"
                         " sinXsin... or a filename (including path)")
        self.params['envelope'] = Param(
            envelope, valType='file', inputType="file", allowedVals=["sin", "sqr", "sinXsin"], allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envelope'])

        msg = _translate("Spatial frequency of the modulation envelope repeats across the "
                         "grating in 1 or 2 dimensions, e.g. 4 or [2,3]")
        self.params['envsf'] = Param(
            envsf, valType='num', inputType="single", allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envsf'])

        msg = _translate("Spatial positioning of the modulation envelope"
                         "(wraps in range 0-1.0)")
        self.params['envphase'] = Param(
            envphase, valType='num', inputType="single", allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envphase'])

        msg = _translate("Orientation of the modulation envelope"
                         "(wraps in range 0-360)")
        self.params['envori'] = Param(
            envori, valType='num', inputType="single", allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['envori'])

        msg = _translate("Modulation depth of modulation envelope")
        self.params['moddepth'] = Param(
            moddepth, valType='num', inputType="single", allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['moddepth'])
            
        msg = _translate("Power of modulation envelope. "
                          "The modulator will be raised to this power "
                          "according to the equation S=cC*(1+mM)^power, "
                          "where C is the carrier and M is the modulator. "
                          "and c and m are there respective contrast and modulation depth. "
                          "Only works with AM envelopes (hence +1) in "
                          "equation. Power is ignored if a beat is requested. "
                          "This is used to obtain the square root of the modulator (power = 0.5) "
                          "which is useful if combining two envelope gratings "
                          "with different carriers and a 180 degree phase shift "
                          "as the resulting combined signal will not "
                          "have any reduction in local contrast at any point in the image. "
                          "This is similar - but not identical to - the method used by "
                          "Landy and Oruc, Vis Res 2002. "
                          "Note overall contrast (apparent carrier contrast) will be altered.")
        self.params['power'] = Param(
            moddepth, valType='num', inputType="single", allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['power'])

        msg = _translate("Do you want a 'beat'? [beat = carrier*envelope, "
                         "no beat = carrier*(1+envelope), True/False, Y/N]")
        self.params['beat'] = Param(
            beat, valType='str', inputType="single", allowedTypes=[], categ="Envelope",
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['beat'])

        msg = _translate("OpenGL Blendmode. Avg is most common mode"
                         " in PsychoPy, add is useful if combining a beat with"
                         " the carrier image or numpy array at point of display")
        self.params['blendmode'] = Param(
            blendmode, valType='str', inputType="choice", allowedVals=['avg', 'add'],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['blendmode'], categ="Appearance")

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
                "    ori=%(ori)s, pos=%(pos)s, size=%(size)s,\n" % inits +
                "    sf=%(sf)s, phase=%(phase)s, anchor=%(anchor)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s,\n " % inits +
                "    opacity=%(opacity)s, contrast=%(contrast)s,\n" % inits +
                "    texRes=%(texture resolution)s, envelope=%(envelope)s,\n" % inits +
                "    envori=%(envori)s, envsf=%(envsf)s,\n" % inits +
                "    envphase=%(envphase)s, power=%(power)s,\n" % inits +
                "    moddepth=%(moddepth)s, blendmode=%(blendmode)s" %inits )

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
        code += "if sys.version[0]=='3' and np.min(win.gamma) == None:\n"
        code += "    logging.warning('Envelope grating in use with no gamma set. Unless you have hardware gamma correction the image will be distorted.')\n"           
        code += "elif np.min(win.gamma) < 1.01:\n"
        code += "    logging.warning('Envelope grating in use with window gamma <= 1.0 or no gamma set at all. Unless you have hardware gamma correction the image will be distorted.')\n"        
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
            buff.setIndentLevel(-2, relative=True)

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
