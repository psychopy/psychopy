#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
# This file by Andrew Schofield

from pathlib import Path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

# only use _localized values for label values, nothing functional:
_localized.update({'noiseImage': _translate('Image from which to derive noise spectrum'),
                   'mask': _translate('Mask'),
                   'sf': _translate('Final spatial frequency'),
                   'phase': _translate('Phase (in cycles)'),
                   'contrast': _translate('Contrast'),
                   'texture resolution': _translate('Texture resolution'),
                   'interpolate': _translate('Interpolate'),
                   'noiseType': _translate('Type of noise'),
                   'noiseElementSize': _translate('Noise element size'),
                   'noiseFractalPower': _translate("Skew in frequency spectrum"),
                   'noiseBaseSf': _translate('Base spatial frequency'),
                   'noiseBW': _translate('Spatial frequency bandwidth'),
                   'noiseBWO': _translate('Orientation bandwidth for Gabor noise'),
                   'noiseOri': _translate('Orientation for Gabor filter'),
                   'noiseFilterOrder': _translate('Order of filter'),
                   'noiseFilterUpper': _translate('Upper cut off frequency'),
                   'noiseFilterLower': _translate('Lower cut off frequency'),
                   'noiseClip': _translate('Number of standard deviations at which to clip noise'),
                   'filter': _translate('Apply filter to noise sample'),
                   'imageComponent': _translate('Radomize image component'),
                   'noiseNewSample': _translate('How to update noise sample'),
                   'noiseNewSampleWhen': _translate('When to update noise sample'),
                   'blendmode': _translate('OpenGL blend mode')})


class NoiseStimComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy']
    iconFile = Path(__file__).parent / 'noise.png'
    tooltip = _translate('Noise stimuli: generates a range of different types of random visual patterns')

    def __init__(self, exp, parentName, name='noise', noiseImage='None',
                 mask='None', sf='None', interpolate='nearest',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 pos=(0, 0), size=(0.5, 0.5), ori=0, phase=0.0, contrast=1.0, texRes='128',
                 noiseType='Binary',noiseElementSize=0.0625,noiseBaseSf=8.0,
                 noiseBW=1,noiseBWO=30, noiseOri=0.0,
                 noiseFractalPower=0.0,noiseFilterOrder=0.0,
                 noiseFilterUpper=8.0,noiseFilterLower=1.0,noiseClip=3.0,
                 imageComponent='Phase', filter='None', 
                 noiseNewSample='None', noiseNewSampleWhen='1',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,blendmode='avg',
                 startEstim='', durationEstim=''):
        super(NoiseStimComponent, self).__init__(
            exp, parentName, name=name, units=units,
            color=color, colorSpace=colorSpace,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        #self._noiseNewSample='None'
        self._forceUpdateRepeat = False
        self._forceUpdateFrames = False
        self._forceUpdateSeconds = False

        self.type = 'NoiseStim'
        self.url = "https://www.psychopy.org/builder/components/NoiseStim.html"
        self.order += [
            'blendmode',  # Appearance tab
            'noiseElementSize',  # Layout tab
            'noiseNewSample', 'noiseNewSampleWhen',  # Timing tab
            'noiseOri', 'mask']
        self.order.insert(self.order.index("size")+1, "noiseElementSize")
        # params

        msg = _translate("An image from which to derive the frequency spectrum for the noise. Give filename (including path)")
        self.params['noiseImage'] = Param(
            noiseImage, valType='file', inputType="file", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseImage'])

        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='str', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['mask'])

        msg = _translate("Michaelson contrast of the image")
        self.params['contrast'] = Param(
            contrast, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['contrast'])

        msg = _translate("Final spatial frequency of image in 1 or 2 dimensions, e.g. 4 or [2,3]. "
                         "Use None to set to 1 copy of noise per unit length of image "
                         "or 1 copy of noise per image if units=pix. "
                         "Set to 1/size (or [1/size,1/size]) where size is a number (or variable) "
                         "equal to the size of the stimulus to get one "
                         "copy of noise per image regardless of the units.")
        self.params['sf'] = Param(
            sf, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['sf'])

        msg = _translate("Spatial positioning of the noise within the stimulus "
                         "(wraps in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='code', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['phase'])

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes, categ='Texture',
            valType='int', inputType="single", allowedVals=['32', '64', '128', '256', '512','1024'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['texture resolution'])

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', inputType="choice", allowedVals=['linear', 'nearest'], categ='Texture',
            updates='constant', allowedUpdates=[], direct=False,
            hint=msg,
            label=_localized['interpolate'])

        msg = _translate("Type of noise (Binary, Normal, Gabor, Isotropic, White, Coloured, Filtered, Image)")
        self.params['noiseType'] = Param(
            noiseType, valType='str', inputType="choice", allowedTypes=[], categ='Basic',
            allowedVals=['Binary', 'Normal','Uniform','Gabor','Isotropic','White','Filtered','Image'],
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['noiseType'])

        msg = _translate("Apply filter to noise sample? "
                         "[Butterworth, Gabor, Isoptopic]. A filter with parameters taken from "
                         "the either the Filtered (Butterworth) or Gabor/Isotropic tab will be applied to OTHER "
                         "noise types. [NOTE: if noise of the same type as the filter is requested the filter "
                         "is applied, once only, to a white noise sample.]")
        self.params['filter'] = Param(
            filter, valType='str', inputType="choice", allowedTypes=[], categ='Texture',
            allowedVals=['None','Butterworth','Gabor','Isotropic'],
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['filter'])
            
        msg = _translate("Which image component should be randomised? "
                         "[Amplitude,Phase]. Randomizing amplitude will keep the phase spectrum of "
                         "the image but set the amplitude spectrum to random values [0...1]. This keeps spatial structure in tact. "
                         "Randoming the phase spectrum will keep the amplitude spectrum of the image  but set "
                         "the phase spectrum to random values [-pi...pi] in radians. This makes a noise sample with no obvious structure. ")
        self.params['imageComponent'] = Param(
            imageComponent, valType='str', inputType="choice", allowedTypes=[], categ='Basic',
            allowedVals=['Phase','Amplitude'],
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['imageComponent'])

        msg = _translate("(Binary, Normal and Uniform only) Size of noise elements in the stimulus units, for pixelated noise.")
        self.params['noiseElementSize'] = Param(
            noiseElementSize, valType='list', inputType="single", allowedTypes=[], categ='Layout',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseElementSize'])

        msg = _translate("Base spatial frequency in cycles per unit length "
                         "If units = pix this value should be < 0.5.")
        self.params['noiseBaseSf'] = Param(
            noiseBaseSf, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseBaseSf'])

        msg = _translate("Spatial frequency bandwidth in octaves - Full width half height")
        self.params['noiseBW'] = Param(
            noiseBW, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseBW'])

        msg = _translate("Orientation bandwidth in degrees (Gabor only) - Full width half height")
        self.params['noiseBWO'] = Param(
            noiseBWO, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseBWO'])
            
        msg = _translate("Orientation of Gabor filter in degrees. Used to set the orientation "
                           "of a Gabor filter to be applied to another noise sample with a "
                           "different overall orientation. "
                           "The best way to set the orientation of a Gabor noise sample "
                           "is to leave this as 0 degree and use the overall orientation "
                           "on the Advanced tab to vary the dominant orientation of the noise. "
                           "If using this setting for orientation it is strongly recommended to set "
                           "the interpolation method to 'linear' on the Advanced tab to avoid pixelization.")
        self.params['noiseOri'] = Param(
            noiseOri, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseOri'])

        msg = _translate("Exponent for the slope of the filter's amplitude spectrum (A=f^Exponent). 0 = flat, "
                         "-1 = slope of 1/f. When used on its own the 'filtered' noise type applies the filter to "
                         "white noise so the resulting noise samples have the spectral properties of the filter.  "
                         "When filtering a noise sample of another type "
                         "this term takes the original spectrum and multiplies it by a ramp in frequency space "
                         "with values set by the exponent. It does not force the spectrum to a specific slope. ")
        self.params['noiseFractalPower'] = Param(
            noiseFractalPower, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFractalPower'])

        msg = _translate("Order of filter - higher = steeper fall off, zero = no filter")
        self.params['noiseFilterOrder'] = Param(
            noiseFilterOrder, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFilterOrder'])

        msg = _translate("Upper cutoff frequency in cycles per unit length. "
                         "Set very high to avoid an upper cutoff and make a high pass filter.")
        self.params['noiseFilterUpper'] = Param(
            noiseFilterUpper, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFilterUpper'])

        msg = _translate("Lower cutoff frequency in cycles per unit length. "
                         "Set to zero to avoid a lower cuttoff and make a low pass filter.")
        self.params['noiseFilterLower'] = Param(
            noiseFilterLower, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFilterLower'])

        msg = _translate("Truncate high and low values beyond stated standard deviations from mean and rescale greyscale range. "
                         "This is not used at all for 'binary' or 'uniform' noise and scales rather than clips 'normal' noise). "
                         "The higher this is the lower the final RMS contrast. If very low noise may appear binarised. "
                         "NOTE: If a filter is used clipping and rescaling are applied after the filter, regardless of the noise type.")
        self.params['noiseClip'] = Param(
            noiseClip, valType='num', inputType="single", allowedTypes=[], categ='Texture',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseClip'])

        msg = _translate("How to update noise if not otherwise required by other changes (none, repeat, N-frames, Seconds)")
        self.params['noiseNewSample'] = Param(
            noiseNewSample, valType='str', inputType="choice", allowedVals=['None', 'Repeat', 'N-frames', 'Seconds'], categ='Timing',
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['noiseNewSample'])

        msg = _translate("How often to update noise (in frames or seconds) - can be a variable, ignored if any noise characteristic is updating on every frame")
        self.params['noiseNewSampleWhen'] = Param(
            noiseNewSampleWhen, valType='num', inputType="single", allowedVals=[], categ='Timing',
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['noiseNewSampleWhen'])

        msg = _translate("OpenGL Blendmode [avg, add (avg is most common mode in PsychoPy, add is used if you want to generate the sum of two components)]")
        self.params['blendmode'] = Param(
            blendmode, valType='str', inputType="choice", allowedVals=['avg', 'add'], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['blendmode'])

        del self.params['fillColor']
        del self.params['borderColor']

    def writeInitCode(self, buff):
        self._noiseNewSample=""
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params
        #buff.writeIndented("from psychopy.visual.noise import NoiseStim\n")

        # replaces variable params with defaults and sets sample updating flag
        inits = getInitVals(self.params)

        self._forceUpdateRepeat = False
        self._forceUpdateFrames = False
        self._forceUpdateSeconds = False
        if inits['noiseNewSample'].val in ['Repeat']:
            self._forceUpdateRepeat = True
        elif inits['noiseNewSample'].val in ['N-frames']:
            self._forceUpdateFrames = True
        elif inits['noiseNewSample'].val in ['Seconds']:
            self._forceUpdateSeconds = True

        code = ("%s = visual.NoiseStim(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                "    noiseImage=%(noiseImage)s, mask=%(mask)s,\n" % inits +
                "    ori=%(ori)s, pos=%(pos)s, size=%(size)s, sf=%(sf)s,\n" % inits +
                "    phase=%(phase)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s, " % inits +
                "    opacity=%(opacity)s, blendmode=%(blendmode)s, contrast=%(contrast)s,\n" % inits +
                # no newline - start optional parameters
                "    texRes=%(texture resolution)s, filter=%(filter)s,\n" % inits +
                "    noiseType=%(noiseType)s, noiseElementSize=%(noiseElementSize)s, \n" %inits +
                "    noiseBaseSf=%(noiseBaseSf)s, noiseBW=%(noiseBW)s,\n" %inits +
                "    noiseBWO=%(noiseBWO)s, noiseOri=%(noiseOri)s,\n" %inits +
                "    noiseFractalPower=%(noiseFractalPower)s,noiseFilterLower=%(noiseFilterLower)s,\n" %inits +
                "    noiseFilterUpper=%(noiseFilterUpper)s, noiseFilterOrder=%(noiseFilterOrder)s,\n" %inits + 
                "    noiseClip=%(noiseClip)s, imageComponent=%(imageComponent)s" %inits)

        if self.params['interpolate'].val == 'linear':
            code += ", interpolate=True"
        else:
            code += ", interpolate=False"
        depth = -self.getPosInRoutine()
        code += ", depth=%.1f)\n" % depth
        buff.writeIndentedLines(code)
        if not(self.params['noiseType'] in ['none', 'None']):
            buff.writeIndented("%(name)s.buildNoise()\n" %self.params)

    def writeRoutineStartCode(self,buff):
        super(NoiseStimComponent, self).writeRoutineStartCode(buff)

        if self._forceUpdateRepeat:
            buff.writeIndented("if not %(name)s._needBuild:\n" %self.params)
            buff.writeIndented("    %(name)s.updateNoise()\n" %self.params)
        if self._forceUpdateSeconds:
            buff.writeIndented("%(name)sSaveT=0.0\n" %self.params)

    def writeFrameCode(self,buff):

        super(NoiseStimComponent, self).writeFrameCode(buff)
        buff.writeIndented("if %(name)s.status == STARTED:\n" %self.params)
        buff.writeIndented("    if %(name)s._needBuild:\n" %self.params)
        buff.writeIndented("        %(name)s.buildNoise()\n" %self.params)

        try:
            _when=float(self.params['noiseNewSampleWhen'].val)
            if self._forceUpdateFrames:
                _when=int(_when)
                buff.writeIndented("    else:\n" %self.params)
                buff.writeIndented("        if (frameN-%(name)s.frameNStart) %% " %self.params)
                buff.writeIndented("%d==0:\n" % _when)
                buff.writeIndented("            %(name)s.updateNoise()\n" %self.params)
            elif self._forceUpdateSeconds:
                buff.writeIndented("    else:\n" %self.params)
                buff.writeIndented("        %(name)sT=t-(%(name)s.tStart+%(name)sSaveT)\n" %self.params)
                buff.writeIndented("        if %(name)sT>" %self.params)
                buff.writeIndented("%f:\n" % _when)
                buff.writeIndented("            %(name)sSaveT=t-%(name)s.tStart\n" %self.params)
                buff.writeIndented("            %(name)s.updateNoise()\n" %self.params)
        except:
            if self._forceUpdateFrames:
                buff.writeIndented("    else:\n" %self.params)
                buff.writeIndented("        if (frameN-%(name)s.frameNStart) %% " %self.params)
                buff.writeIndented("%(noiseNewSampleWhen)s==0:\n" %self.params)
                buff.writeIndented("            %(name)s.updateNoise()\n" %self.params)
            elif self._forceUpdateSeconds:
                buff.writeIndented("    else:\n" %self.params)
                buff.writeIndented("        %(name)sT=t-(%(name)s.tStart+%(name)sSaveT)\n" %self.params)
                buff.writeIndented("        if %(name)sT>" %self.params)
                buff.writeIndented("%(noiseNewSampleWhen)s:\n" %self.params)
                buff.writeIndented("            %(name)sSaveT=t-%(name)s.tStart\n" %self.params)
                buff.writeIndented("            %(name)s.updateNoise()\n" %self.params)
