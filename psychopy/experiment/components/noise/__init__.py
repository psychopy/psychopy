#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
# This file by Andrew Schofield

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'NoiseStim.png')
tooltip = _translate('Noise stimuli: generates a range of different types of random visual patterns')

# only use _localized values for label values, nothing functional:
_localized = {'noiseImage': _translate('Image from which to derive noise spectrum'),
              'ori': _translate('Orientation'),
              'mask': _translate('Mask'),
              'sf': _translate('Final spatial frequency'),
              'phase': _translate('Phase (in cycles)'),
              'contrast': _translate('Contrast'),
              'texture resolution': _translate('Texture resolution'),
              'interpolate': _translate('Interpolate'),
              'noiseType':_translate('Type of noise'),
              'noiseElementSize':_translate('Noise element size for pixelated noise'),
              'noiseFractalPower':_translate("Skew in frequency spectrum"),
              'noiseBaseSf':_translate('Base spatial frequency'),
              'noiseBW':_translate('Spatial frequency bandwidth'),
              'noiseBWO':_translate('Orientation bandwidth for Gabor noise'),
              'noiseFilterOrder':_translate('Order of filter'),
              'noiseFilterUpper':_translate('Upper cut off frequency'),
              'noiseFilterLower':_translate('Lower cut off frequency'),
              'noiseClip' :_translate('Number of standard deviations at which to clip noise'),
              'noiseNewSample':_translate('How to update noise sample'),
              'noiseNewSampleWhen':_translate('When to update noise sample'),
              'blendmode':_translate('OpenGL blend mode')
              }


class NoiseStimComponent(BaseVisualComponent):
    """A class for presenting grating stimuli"""

    def __init__(self, exp, parentName, name='noise', noiseImage='None',
                 mask='None', sf='None', interpolate='nearest',
                 units='from exp settings', color='$[1,1,1]', colorSpace='rgb',
                 pos=(0, 0), size=(0.5, 0.5), ori=0, phase=0.0, contrast=1.0, texRes='128',
                 noiseType='Binary',noiseElementSize=0.0625,noiseBaseSf=8.0,noiseBW=1,noise_BWO=30,noiseFractalPower=0.0,noiseFilterOrder=0.0,noiseFilterUpper=8.0,noiseFilterLower=1.0,noiseClip=3.0, noiseNewSample='None', noiseNewSampleWhen='1',
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
        self.url = "http://www.psychopy.org/builder/components/NoiseStim.html"
        self.order = ['tex', 'mask']

        # params

        msg = _translate("An image from which to derive the frequency spectrum for the noise. Give filename (including path)")
        self.params['noiseImage'] = Param(
            noiseImage, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseImage'], categ="Image noise")

        self.params['ori'] = Param(
            ori, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate("Orientation of this stimulus (in deg)"),
            label=_localized['ori'],categ="Advanced")



        msg = _translate("An image to define the alpha mask (ie shape)- "
                         "gauss, circle... or a filename (including path)")
        self.params['mask'] = Param(
            mask, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['mask'], categ="Advanced")

        msg = _translate("Michaelson contrast of the image")
        self.params['contrast'] = Param(
            contrast, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['contrast'], categ="Advanced")

        msg = _translate("Final spatial frequency of image in 1 or 2 dimensions, e.g. 4 or [2,3] use None to set to 1 cycle per unit length or 1 cycle per image if units=pix")
        self.params['sf'] = Param(
            sf, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['sf'], categ="Advanced")

        msg = _translate("Spatial positioning of the image  "
                         "(wraps in range 0-1.0)")
        self.params['phase'] = Param(
            phase, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['phase'], categ="Advanced")

        msg = _translate(
            "Resolution of the texture for standard ones such as sin, sqr "
            "etc. For most cases a value of 256 pixels will suffice")
        self.params['texture resolution'] = Param(
            texRes,
            valType='code', allowedVals=['32', '64', '128', '256', '512'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['texture resolution'], categ="Advanced")

        msg = _translate("How should the image be interpolated if/when "
                         "rescaled")
        self.params['interpolate'] = Param(
            interpolate, valType='str', allowedVals=['linear', 'nearest'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['interpolate'], categ="Advanced")

        msg = _translate("Type of noise (Binary, Normal, Gabor, Isotropic, White, Coloured, Filtered, Image)")
        self.params['noiseType'] = Param(
            noiseType, valType='str', allowedTypes=[], allowedVals=['Binary', 'Normal','Uniform','Gabor','Isotropic','White','Filtered','Image'],
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['noiseType'], categ=" Noise")

        msg = _translate("(Binary, Normal an Uniform only) Size of noise elements")
        self.params['noiseElementSize'] = Param(
            noiseElementSize, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseElementSize'], categ="Binary/Normal/Uniform")

        msg = _translate("Base spatial frequency")
        self.params['noiseBaseSf'] = Param(
            noiseBaseSf, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseBaseSf'], categ="Gabor/Isotropic")

        msg = _translate("Spatial frequency bandwidth in octaves - Full width half height")
        self.params['noiseBW'] = Param(
            noiseBW, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseBW'], categ="Gabor/Isotropic")

        msg = _translate("Orientation bandwidth in degrees (Gabor only) - Full width half height")
        self.params['noiseBWO'] = Param(
            noiseBW, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseBWO'], categ="Gabor/Isotropic")

        msg = _translate("Exponent for spectral slope (A=f^Exponent) of noise negative exponents look nice. -1='pink noise', 0='white noise' (changes the spatial frequency spectrum - does not make the noise colourful)")
        self.params['noiseFractalPower'] = Param(
            noiseFractalPower, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFractalPower'], categ="Filtered")

        msg = _translate("Order of filter - higher = steeper fall off, zero = no filter")
        self.params['noiseFilterOrder'] = Param(
            noiseFilterOrder, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFilterOrder'], categ="Filtered")

        msg = _translate("Upper cutoff frequency")
        self.params['noiseFilterUpper'] = Param(
            noiseFilterUpper, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFilterUpper'], categ="Filtered")

        msg = _translate("Lower cutoff frequency")
        self.params['noiseFilterLower'] = Param(
            noiseFilterLower, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseFilterLower'], categ="Filtered")

        msg = _translate("Truncate high and low values beyond stated standard deviations from mean (not used for binary or uniform noise; scales rather than clips normal noise). The higher this is the lower the final RMS contrast. If low noise may appear binary")
        self.params['noiseClip'] = Param(
            noiseClip, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['noiseClip'], categ=" Noise")

        msg = _translate("How to update noise if not otherwise required by other changes (none, repeat, N-frames, Seconds)")
        self.params['noiseNewSample'] = Param(
            noiseNewSample, valType='str', allowedVals=['None', 'Repeat', 'N-frames', 'Seconds'],
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['noiseNewSample'], categ=" Noise")

        msg = _translate("How often to update noise (in frames or seconds) - can be a variable, ignored if any noise characteristic is updating on every frame")
        self.params['noiseNewSampleWhen'] = Param(
            noiseNewSampleWhen, valType='str', allowedVals=[],
            updates='constant',
            allowedUpdates=[],
            hint=msg,
            label=_localized['noiseNewSampleWhen'], categ=" Noise")

        msg = _translate("OpenGL Blendmode [avg, add (avg is most common mode in PsychoPy, add is used if you want to generate the sum of two components)]")
        self.params['blendmode'] = Param(
            blendmode, valType='str', allowedVals=['avg', 'add'],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['blendmode'], categ="Basic")

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

        #for myparam in inits:
        #    if ('noise' in myparam):
        #        if (inits[myparam].updates in ['set every frame']):
        #            self._forceRebuild=True
            #if not (inits[myparam].updates in ['constant', None, 'None']):
            #    inits[myparam]='1'
        #if not (self.params['A_noiseType'].updates in ['constant', None, 'None']):
        #    inits['A_noiseType']='Binary'
        #if ('rebuild_frame' in self._noiseNewSample):
        #    print 'Warning: Rebuilding the noise sample every frame may be slow and could corrupt frame timing'
        # noise sample updating set to every repeat or frame will override result of parameter settings
        self._forceUpdateRepeat = False
        self._forceUpdateFrames = False
        self._forceUpdateSeconds = False
        if inits['noiseNewSample'].val in ['Repeat']:
            self._forceUpdateRepeat = True
        elif inits['noiseNewSample'].val in ['N-frames']:
            self._forceUpdateFrames = True
        elif inits['noiseNewSample'].val in ['Seconds']:
            self._forceUpdateSeconds = True
        #self._when=float(inits['Z_when'].val)
        #print self._when

        #else whenIsVariale=false
        #if (inits['carrier'].val in ['noise','Noise']):
        #    inits['carrier']="%(name)s.noiseTex" %inits
        code = ("%s = visual.NoiseStim(\n" % inits['name'] +
                "    win=win, name='%s',%s\n" % (inits['name'], unitsStr) +
                "    noiseImage=%(noiseImage)s, mask=%(mask)s,\n" % inits +
                "    ori=%(ori)s, pos=%(pos)s, size=%(size)s, " % inits +
                "sf=%(sf)s, phase=%(phase)s,\n" % inits +
                "    color=%(color)s, colorSpace=%(colorSpace)s, " % inits +
                "opacity=%(opacity)s, blendmode=%(blendmode)s, contrast=%(contrast)s,\n" % inits +
                # no newline - start optional parameters
                "    texRes=%(texture resolution)s,\n" % inits +
                "    noiseType=%(noiseType)s, noiseElementSize=%(noiseElementSize)s, noiseBaseSf=%(noiseBaseSf)s,\n" %inits+
                "    noiseBW=%(noiseBW)s, noiseBWO=%(noiseBWO)s, noiseFractalPower=%(noiseFractalPower)s,noiseFilterLower=%(noiseFilterLower)s, noiseFilterUpper=%(noiseFilterUpper)s, noiseFilterOrder=%(noiseFilterOrder)s, noiseClip=%(noiseClip)s" %inits)


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
