#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Stimulus object for drawing arbitrary bitmap carriers with an arbitrary
second order envelope carrier and envelope can vary independently for
orientation, frequencyand phase. Also does beat stimuli. """

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# some code provided by Andrew Schofield
# Distributed under the terms of the GNU General Public License (GPL).

# Requires shaders if you don't have them it will just throw and error.
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+

from __future__ import absolute_import, print_function

import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl
try:
    from PIL import Image
except ImportError:
    import Image
import psychopy  # so we can get the __path__
from psychopy import logging
from psychopy.visual import filters
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter
from .grating import GratingStim
import numpy
from numpy import exp, sin, cos
from numpy.fft import fft2, ifft2, fftshift, ifftshift

from . import shaders as _shaders


class NoiseStim(GratingStim):
    """A stimulus with 2 textures: a radom noise sample and a mask

    **Example**::

    noise1 = noise = visual.NoiseStim(
                                    win=win, name='noise',units='pix', 
                                    noiseImage='testImg.jpg', mask='circle',
                                    ori=1.0, pos=(0, 0), size=(512, 512), sf=None, phase=0,
                                    color=[1,1,1], colorSpace='rgb', opacity=1, blendmode='add', contrast=1.0,
                                    texRes=512,
                                    noiseType='Gabor', noiseElementSize=4, noiseBaseSf=32.0/512,
                                    noiseBW=1.0, noiseBWO=30, noiseFractalPower=-1,noiseFilterLower=3/512, noiseFilterUpper=8.0/512.0, 
                                    noiseFilterOrder=3.0, noiseClip=3.0, interpolate=False, depth=-1.0)
                                    
            # gives a circular patch of noise made up of scattered Gabor elements with peak frequency = 32.0/512 cycles per pixel, 
            # orientation = 0 , frequency bandwidth = 1 octave and orientation bandwidth 30 degrees

    **Types of noise available**
    Binary, Normal, Uniform - pixel based noise samples drawn from a binary (blank and white), normal or uniform distribution respectively. Binary noise is always exactly zero mean, Normal and Uniform are approximately so.
            Parameters -    noiseElementSize - (can be a tuple) defines the size of the noise elements in the components units.
                            noiseClip the values in normally distributed noise are divided by noiseClip to limit excessively high or low values.
                                However, values can still go out of range -1 to 1 whih will throw a soft error message high values of noiseClip are recommended if using 'Normal'
    
    Gabor, Isotropic - Effectively a dense scattering of Gabor elements with random amplitude and fixed orientation for Gabor or random orientation for Isotropic noise.
            Parameters -    noiseBaseSf - centre spatial frequency in the component units. 
                            noiseBW - spatial frequency bandwidth full width half height in octaves.
                            ori - centre orientation for Gabor noise (works as for gratingStim so twists the final image at render time).
                            noiseBWO - orientation bandwidth for Gabor noise full width half height in degrees.

            In practice the desired amplitude spectrum for the noise is built in Fourier space with a random phase spectrum. DC term is set to zero - ie zero mean.
        
    Filtered - A noise sample that has been filtered with a low, high or bandpass Butterworth filter. The initial sample can have its spectrum skewed towards low or high frequencies
            The contrast of the noise falls by half its maximum (3dB) at the cutoff frequencies.
            Parameters -    noiseFilterUpper - upper cutoff frequency - if greater than texRes/2 cycles per image low pass filter used.
                            noiseFilterLower - Lower cutoff frequency - if zero low pass filter used.
                            noiseFilterOrder - The order of the filter controls the steepness of the falloff outside the passband is zero no filter is applied.
                            noiseFractalPower - spectrum = f^noiseFractalPower  - determines the spatial frequency bias of the initial noise sample. 0 = flat spectrum, negative = low frequency bias, positive = high frequency bias, -1 = fractal or brownian noise.
                            noiseClip - determines clipping values and rescaling factor such that final rms contrast is close to that requested by contrast parameter while keeping pixel values in range -1, 1.  

    White - A short cut to obtain noise with a flat, unfiltered spectrum
                            noiseClip - determines clipping values and rescaling factor such that final rms contrast is close to that requested by contrast parameter while keeping pixel values in range -1, 1.  

            In practice the desired amplitude spectrum is built in the Fourier Domain with a random phase spectrum. DC term is set to zero - ie zero mean
            Note despite name the noise contains all grey levels.

    Image - A noise sample whose spatial frequency spectrum is taken from the supplied image.
            Parameters -    noiseImage name of nparray or image file from which to take spectrum - should be same size as largest side requested for component if units is pix or texRes x texRes otherwise
                            noiseClip - determines clipping values and rescaling factor such that final rms contrast is close to that requested by contrast parameter while keeping pixel values in range -1, 1.  

            In practice the desired amplitude spectrum is taken from the image and paired with a random phase spectrum. DC term is set to zero - ie zero mean
            
    **Updating noise samples and timing**
    The noise is rebuilt at next call of the draw function whenever a parameter starting 'noise' is notionally changed even if the value does not actually change every time. eg. setting a parameter to update every frame will cause a new noise sample on every frame but see below.
    A rebuild can also be forced at any time using the buildNoise() function.
    The updateNoise() function can be used at any time to produce a new random saple of noise without doing a full build. ie it is quicker than a full build.
    Both buildNoise and updateNoise can be slow for large samples. 
    Samples of Binary, Normal or Uniform noise can usually be made at frame rate using noiseUpdate. 
    Updating or building other noise types at frame rate may result in dropped frames. 
    An alternative is to build a large sample of noise at the start of the routien and place it off the screen then cut a samples out of this at random locations and feed that as a numpy array into the texture of a visible gratingStim.

    **Notes on size**
    If units = pix and noiseType = Binary, Normal or Uniform will make noise sample of requested size.
    If units = pix and noiseType is Gabor, Isotropic, Filtered, White, Coloured or Image will make square noise sample with side length equal that of the largest dimetions requested.
    if units is not pix will make square noise sample with side length equal to texRes then rescale to present.
    
    **Notes on interpolation**
    For pixel based noise interpolation = nearest is usually best.
    For other noise types linear is better if the size of the noise sample does not match the final size of the image well.
    
    **Notes on frequency**
    Frequencies for cutoffs etc are converted between units for you but can be counter intuitive. 1/size is always 1 cycle per image.
    For the sf (final spatial frequency) parameter itself 1/size (or None for units pix) will faithfully represent the image without further scaling.
        
    Filter cuttoff and Gabor/Isotropic base frequencies should not be too high you should aim to keep them below 0.5 c/pixel on the screen.
    The function will produce an error when it can't draw the stimulus in the buffer but it may still be wrong when displayed.
    
    **Notes on orientation and phase**
    The ori parameter twists the final image so the samples in noiseType Binary, Normal or Uniform will no longer be alighned to the sides of the monitor if ori is not a multiple of 90.
    Most other noise types look broadly the same for all values of ori but the specific sample shown can be made to rotate by changing ori.
    The dominant orientation for Gabor noise is determined by ori at render time, not before.
    
    The phase parameter similarly shifts the sample around within the display window at render time and will not choose new random phases for the noise sample.
    """

    def __init__(self,
                 win,
                 mask="none",
                 units="",
                 pos=(0.0, 0.0),
                 size=None,
                 sf=None,
                 ori=0.0,
                 phase=(0.0, 0.0),
                 noiseType='none',
                 noiseElementSize='16',
                 noiseBaseSf='1',
                 noiseBW='1',
                 noiseBWO='30',
                 noiseFractalPower='0.0',
                 noiseFilterUpper='50',
                 noiseFilterLower='0',
                 noiseFilterOrder='0.0',
                 noiseClip='1',
                 noiseImage='None',
                 texRes=128,
                 rgb=None,
                 dkl=None,
                 lms=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=0.5,  # see doc
                 opacity=1.0,
                 depth=0,
                 rgbPedestal=(0.0, 0.0, 0.0),
                 interpolate=False,
                 blendmode='avg',
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 maskParams=None):
        """ """  # Empty docstring. All doc is in attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        #assert win._haveShaders is True, ("Currently EnvelopeGratings need "
        #                                  "your graphics card to have shaders"
        #                                  " and yours does not seem to.")
        self._initParams = dir()
        for unecess in ['self', 'rgb', 'dkl', 'lms']:
            self._initParams.remove(unecess)
        # initialise parent class
        GratingStim.__init__(self, win, tex='sin',
                             units=units, pos=pos, size=size, sf=sf,
                             ori=ori, phase=phase,
                             color=color, colorSpace=colorSpace,
                             contrast=contrast, opacity=opacity,
                             depth=depth, interpolate=interpolate,
                             name=name, autoLog=autoLog, autoDraw=autoDraw,
                             blendmode=blendmode,
                             maskParams=None)
        # use shaders if available by default, this is a good thing
        self.__dict__['useShaders'] = win._haveShaders
        # UGLY HACK: Some parameters depend on each other for processing.
        # They are set "superficially" here.
        # TO DO: postpone calls to _createTexture, setColor and
        # _calcCyclesPerStim whin initiating stimulus
        #self.__dict__['tex'] = tex
        self.__dict__['mask'] = mask
        self.__dict__['maskParams'] = maskParams

        # initialise textures and masks for stimulus
        #self._carrierID = GL.GLuint()
        #GL.glGenTextures(1, ctypes.byref(self._carrierID))
        #self._envelopeID = GL.GLuint()
        #GL.glGenTextures(1, ctypes.byref(self._envelopeID))
        #self.interpolate = interpolate
        #del self._texID  # created by GratingStim.__init__

        self.blendmode=blendmode
        self.mask = mask
        #self.tex = tex
        self.texRes=int(texRes)
        self.noiseType=noiseType
        self.noiseImage=noiseImage
        self.noiseElementSize=noiseElementSize
        #print self.noiseElementSize,noiseElementSize, self.__dict__['noiseElementSize']
        self.noiseBaseSf=float(noiseBaseSf)
        self.noiseBW=float(noiseBW)
        self.noiseBWO=float(noiseBWO)
        self.noiseFractalPower=float(noiseFractalPower)
        self.noiseFilterUpper=float(noiseFilterUpper)
        self.noiseFilterLower=float(noiseFilterLower)
        self.noiseFilterOrder=float(noiseFilterOrder)
        if noiseClip != 'none':
            self.noiseClip=float(noiseClip)
        else:
            self.noiseClip=noiseClip
        
        # print(self.CMphase)
        #self._shaderProg = _shaders.compileProgram(
         #   _shaders.vertSimple, carrierEnvelopeMaskFrag)

        self.local = numpy.ones((texRes, texRes), dtype=numpy.ubyte)
        self.local_p = self.local.ctypes
        # self.local=GL.GL_UNSIGNED_BYTE(self.local)
        # fix scaling to window coords
        # self._calcCyclesPerStim()
        #self._calcEnvCyclesPerStim()
        self._sideLength=1.0   
        self._size=512         # in unlikely case where it does not get set anywehre else before use.
        self.buildNoise()
        self._needBuild = False
        #self._needNoiseUpdate = False
        #print(self.noiseElementSize)

    @attributeSetter
    def noiseType(self, value):
        """Type of noise to generate
            'Binary, Normal and Uniform' produce pixel based random samples from the indicated distribitions. Binary has zero mean lumiannce, Normal and Uniform approximate this.
            'Gabor and Isotropic' produce dense, random scatterd Gabor elements with fixed (Gabor) or randomn (Isotropic) orientations. Zero mean lumiannce.
            'White' produces white noise with a flat amplitude spectrum. Zero mean lumiannce.
            'Filtered' Produces white noise filtered by a low-, high- or band-pass filter. Zero mean lumiannce.
            'Coloured' produces noise with a skewed applitude spectrum (note samples are grey scale not actually coloured). Zero mean lumiannce.
            'Image' prodcues noise with the same spectrum as the supplied image but with mean lumiance set to zero.
        
        """
        self.__dict__['noiseType'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseImage(self, value):
        """Image from which to derive the amplitude spectrum of noise type Image 
        """
       
        self.__dict__['noiseImage'] = value
        self._needUpdate = True
        self._needBuild = True

    @attributeSetter
    def noiseElementSize(self, value):
        """noise element size for Binary, Normal or Uniform noise
        """
        
        self.__dict__['noiseElementSize'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseBaseSf(self, value):
        """Spatial frequency for Gabor or Isotropic noise
        """
        
        self.__dict__['noiseBaseSf'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseBW(self, value):
        """Spatial frequency bandwidth for Gabor or Isotropic noise, full width at half height in octaves
        """
        
        self.__dict__['noiseBW'] = value
        self._needUpdate = True 
        self._needBuild = True
        
    @attributeSetter
    def noiseBWO(self, value):
        """Orientation bandwidth for Gabor noise, full width at half height in degrees
        """
        
        self.__dict__['noiseBWO'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseFractalPower(self, value):
        """Exponent for 'coloured' noise. Amplitide spectrum = f^noiseFractalPower
        """
        
        self.__dict__['noiseFractalPower'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseFilterUpper(self, value):
        """Upper cuttoff for filtered noise. > size/2 creates high pass filter
        """
        
        self.__dict__['noiseFilterUpper'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseFilterLower(self, value):
        """Lower cuttoff for filtered noise. Zero creates low pass filter
        """
        
        self.__dict__['noiseFilterLower'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseFilterOrder(self, value):
        """Order of Butterworth filter for filtered noise. High = fast fall off withfrequency outside pass band.
        """
        
        self.__dict__['noiseFilterOrder'] = value
        self._needUpdate = True
        self._needBuild = True
        
    @attributeSetter
    def noiseClip(self, value):
        """Ignored for types 'Binary and Uniform'.
            For 'Normal' noise pixel values are divided by noiseClip 
            to limit the standard deviation of the noise values.
            For all other noise types noiseClip determines the 
            level at which pixel values are cliped and subsequently 
            re-scaled so as to produce a final image appraching the 
            desired RMS contrast.
            High values will tend to reduce the ultimate RMS 
            contrast but increase fidelity of appearance.
            Low values prioritise accurate final contrast
            but result in a binarised or thresholded appearance.
        """
        
        self.__dict__['noiseClip'] = value
        self._needUpdate = True
        self._needBuild = True

    @attributeSetter
    def texRes(self, value):
        """Power-of-two int. Sets the resolution of the mask and texture.
        maybe used as the side length for generating the noise texture but is not used if units = pix.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['texRes'] = value

        # ... now rebuild textures (call attributeSetters without logging).
        
        self._needUpdate = True 
        self._needBuild = True
        
        if hasattr(self, 'tex'):
            self._set('tex', self.tex, log=False)
        if hasattr(self, 'mask'):
            self._set('mask', self.mask, log=False)

    def setTexRes(self, value, log=None):
        self._set('texRes', value, log=log)
        
    def setNoiseType(self, value, log=None):
        self._set('noiseType', value, log=log)
        
    def setNoiseImage(self, value, log=None):
        self._set('noiseImage', value, log=log)
        
    def setNoiseClip(self, value, log=None):
        self._set('noiseClip', value, log=log)
        
    def setNoiseElementSize(self, value, log=None):
        self._set('noiseElementSize', value, log=log)
        
    def setNoiseBaseSf(self, value, log=None):
        self._set('noiseBaseSf', value, log=log)
        
    def setNoiseBW(self, value, log=None):
        self._set('noiseBW', value, log=log)
        
    def setNoiseBWO(self, value, log=None):
        self._set('noiseBWO', value, log=log)
       
    def setNoiseFractalPower(self, value, log=None):
        self._set('noiseFractalPower', value, log=log)
       
    def setNoiseFilterUpper(self, value, log=None):
        self._set('noiseFilterUpper', value, log=log)
        
    def setNoiseFilterLower(self, value, log=None):
        self._set('noiseFilterLower', value, log=log)
        
    def setNoiseFilterOrder(self, value, log=None):
        self._set('noiseFilterOrder', value, log=log)

    def setblendMode(self, value, log=None):
        self._set('blendMode', value, log=log)

    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win is None:
            win = self.win
        saveBlendMode = win.blendMode
        win.setBlendMode(self.blendmode, log=False)
        self._selectWindow(win)

        #do scaling
        GL.glPushMatrix()  # push before the list, pop after
        win.setScale('pix')
        #the list just does the texture mapping

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace,
                                         self.contrast)
        GL.glColor4f(desiredRGB[0], desiredRGB[1], desiredRGB[2],
                     self.opacity)

        # re-build the noise if not done so since last parameter update
        if self._needBuild:
            self.buildNoise()
        # remake textures if necessary
        if self._needTextureUpdate:
            self.setTex(value=self.tex, log=False)
        if self._needUpdate:
            self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()
        win.setBlendMode(saveBlendMode, log=False)

            
    def updateNoise(self):
        """Updates the noise sample. Does not change any of the noise parameters 
            but choses a new random sample given the previously set parameters.
        """

        if not(self.noiseType in ['binary','Binary','normal','Normal','uniform','Uniform']):
            Ph = numpy.random.uniform(0,2*numpy.pi,int(self._size**2))
            Ph = numpy.reshape(Ph,(int(self._size),int(self._size)))
            In = self.noiseTex*exp(1j*Ph)
            Im = numpy.real(ifft2(In))
            Im = ifftshift(Im)
            gsd = filters.getRMScontrast(Im)
            factor = (gsd*self.noiseClip)
            numpy.clip(Im,-factor,factor,Im)
            self.tex = Im/factor
        elif self.noiseType in ['normal','Normal']:
            self.tex = numpy.random.randn(int(self._sideLength[1]),int(self._sideLength[0]))/self.noiseClip
        elif self.noiseType in ['uniform','Uniform']:
            self.tex = 2.0*numpy.random.rand(int(self._sideLength[1]),int(self._sideLength[0]))-1.0
        else:
            numpy.random.shuffle(self.noiseTex)  # pick random noise sample by shuffleing values
            self.tex = numpy.reshape(self.noiseTex,(int(self._sideLength[1]),int(self._sideLength[0])))
            
    def buildNoise(self):
        """build a new noise sample. Required to act on changes to any noise parameters or texRes.
        """

        if self.units == 'pix':
            if not (self.noiseType in ['Binary','binary','Normal','normal','uniform','Uniform']):
                mysize = numpy.max(self.size)
            else:
                mysize = self.size
            sampleSize = self.noiseElementSize
            mysf = self.__dict__['noiseBaseSf']*mysize
            lowsf = self.noiseFilterLower*mysize
            upsf = self.noiseFilterUpper*mysize
        else:
            mysize = self.texRes
            pixSize = self.size/self.texRes
            sampleSize = self.noiseElementSize/pixSize
            mysf = self.size[0]*self.noiseBaseSf
            lowsf = self.size[0]*self.noiseFilterLower
            upsf = self.size[0]*self.noiseFilterUpper
       
        self._size = mysize  # store for use by updateNoise()
        self._sf = mysf
        if self.noiseType in ['binary','Binary','normal','Normal','uniform','Uniform']:
            self._sideLength = numpy.round(mysize/sampleSize)  # dummy side length for use when unpacking noise samples in updateNoise()
            self._sideLength.astype(int)
            if ((self._sideLength[0] < 2) and (self._sideLength[1] < 2)):
                msg=('Noise sample size '
                     'must result in more than '
                     '1 sample per image dimension.')
                raise ValueError(msg)
            totalSamples = self._sideLength[0]*self._sideLength[1]
            if self.noiseType in ['binary','Binary']:
                self.noiseTex=numpy.append(numpy.ones(int(numpy.round(totalSamples/2.0))),-1*numpy.ones(int(numpy.round(totalSamples/2.0))))
        elif self.noiseType in ['White','white']:
            self.noiseTex = numpy.ones((int(mysize),int(mysize)))
            self.noiseTex[0][0] = 0
        #elif self.noiseType in ['Coloured','coloured']:
        #    pin=filters.makeRadialMatrix(matrixSize=mysize, center=(0,0), radius=1.0)
        #    self.noiseTex=numpy.multiply(numpy.ones((int(mysize),int(mysize))),(pin)**self.noiseFractalPower) 
        #    self.noiseTex=fftshift(self.noiseTex)
        #    self.noiseTex[0][0]=0
        elif self.noiseType in ['Isotropic','isotropic']:
            if mysf > mysize/2:
                msg = ('Base frequency for isotropic '
                      'noise is definitely too high.')
                raise Warning(msg)
            localf = mysf/mysize
            linbw = 2**self.noiseBW
            lowf = 2.0*localf/(linbw+1.0)
            highf = linbw*lowf
            FWF = highf-lowf
            sigmaF = FWF/(2*numpy.sqrt(2*numpy.log(2)))
            self.noiseTex = numpy.zeros(int(mysize**2))
            self.noiseTex = numpy.reshape(self.noiseTex,(int(mysize),int(mysize)))
            pin = filters.makeRadialMatrix(matrixSize=mysize, center=(0,0), radius=2)
            self.noiseTex = filters.makeGauss(pin, mean=localf, sd=sigmaF)
            self.noiseTex = fftshift(self.noiseTex)
            self.noiseTex[0][0] = 0
        elif self.noiseType in ['Gabor','gabor']:
            if mysf > mysize/2:
                msg = ('Base frequency for Gabor '
                      'noise is definitely too high.')
                raise Warning(msg)
            localf = mysf/mysize
            linbw = 2**self.noiseBW
            lowf = 2.0*localf/(linbw+1.0)
            highf = linbw*lowf
            FWF = highf-lowf
            sigmaF = FWF/(2*numpy.sqrt(2*numpy.log(2)))
            FWO = 2.0*localf*numpy.tan(numpy.pi*self.noiseBWO/360.0)
            sigmaO = FWO/(2*numpy.sqrt(2*numpy.log(2)))
            self.noiseTex=numpy.zeros(int(mysize**2))
            self.noiseTex=numpy.reshape(self.noiseTex,(int(mysize),int(mysize)))
            yy, xx = numpy.mgrid[0:mysize, 0:mysize]
            xx = (0.5 - 1.0 / mysize * xx) 
            yy = (0.5 - 1.0 / mysize * yy) 
            self.noiseTex=filters.make2DGauss(xx,yy,mean=(localf,0), sd=(sigmaF,sigmaO))
            self.noiseTex=self.noiseTex+filters.make2DGauss(xx,yy, mean=(-localf,0), sd=(sigmaF,sigmaO))
            self.noiseTex=fftshift(self.noiseTex)
            self.noiseTex[0][0]=0
        elif self.noiseType in ['Image','image']:
            if not(self.noiseImage in ['None','none']):  
                im = Image.open(self.noiseImage)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.convert("L")  # FORCE TO LUMINANCE
                intensity = numpy.array(im).astype(
                        numpy.float32) * 0.0078431372549019607 - 1.0
                self.noiseTex =  numpy.absolute(fft2(intensity))
            else:
                self.noiseTex = numpy.ones((int(mysize),int(mysize)))  # if image is 'None' will make white noise as tempary measure
            self.noiseTex[0][0]=0
        elif self.noiseType in ['filtered','Filtered']:
            pin=filters.makeRadialMatrix(matrixSize=mysize, center=(0,0), radius=1.0)
            self.noiseTex = numpy.multiply(numpy.ones((int(mysize),int(mysize))),(pin)**self.noiseFractalPower)
            if lowsf > mysize/2:
                msg = ('Lower cut off frequency for filtered '
                      'noise is definitely too high.')
                raise Warning(msg)
            if self.noiseFilterOrder > 0.01:
                if upsf<(mysize/2.0):
                    filter = filters.butter2d_lp_elliptic(size=[mysize,mysize], cutoff_x=upsf/mysize, cutoff_y=upsf/mysize, n=self.noiseFilterOrder, alpha=0, offset_x=2/(mysize-1),offset_y=2/(mysize-1))
                else:
                    filter = numpy.ones((int(mysize),int(mysize)))
                if lowsf>0:
                    filter = filter-filters.butter2d_lp_elliptic(size=[mysize,mysize], cutoff_x=lowsf/mysize, cutoff_y=lowsf/mysize, n=self.noiseFilterOrder, alpha=0, offset_x=2/(mysize-1),offset_y=2/(mysize-1))
                self.noiseTex = self.noiseTex*filter
            self.noiseTex = fftshift(self.noiseTex)
            self.noiseTex[0][0] = 0
        else:
            raise ValueError('Noise type not recognised.')
        self._needBuild = False # prevent noise from being re-built at next draw() unless a parameter is chnaged in the mean time.
        self.updateNoise()  # now choose the initial random sample.
        
 



 


