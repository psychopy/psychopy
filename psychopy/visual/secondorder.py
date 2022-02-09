#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Stimulus object for drawing arbitrary bitmap carriers with an arbitrary
second order envelope carrier and envelope can vary independently for
orientation, frequencyand phase. Also does beat stimuli. """

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd..
# Additional code provided by Andrew Schofield
# Distributed under the terms of the GNU General Public License (GPL).

# Requires shaders if you don't have them it will just throw and error.
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter
from psychopy.visual.grating import GratingStim
import numpy

from . import shaders as _shaders

# we need a different shader program for this stimuli (3 textures)
carrierEnvelopeMaskFrag = '''
    uniform sampler2D carrier, envelope, mask;
    uniform float moddepth, offset, ori, add;

    void main() {
        float mid=0.5;
        vec4 carrierFrag = texture2D(carrier,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[2].st);
        vec2 tex = gl_TexCoord[1].st;

        vec2 rotated = vec2(cos(ori) * (tex.x - mid ) + sin(ori) * (tex.y - mid) + mid , cos(ori) * (tex.y - mid) - sin(ori) * (tex.x - mid) + mid );
        vec4 envFrag = texture2D( envelope,  rotated);
        gl_FragColor.a = gl_Color.a*maskFrag.a;
        gl_FragColor.rgb = ((moddepth*envFrag.rgb + offset)*carrierFrag.rgb*(gl_Color.rgb*2.0 - 1.0) + add)/2.0;
    }
    '''

# we need a different shader program for this (4 textures including the power term)
carrierEnvelopeMaskFragPow = '''
    uniform sampler2D carrier, envelope, mask, power;
    uniform float moddepth, offset, ori, add;

    void main() {
        float mid=0.5;
        vec4 carrierFrag = texture2D(carrier,gl_TexCoord[0].st);
        vec4 maskFrag = texture2D(mask,gl_TexCoord[2].st);
        vec4 powerFrag = texture2D(power,gl_TexCoord[2].st);
        vec2 tex = gl_TexCoord[1].st;

        vec2 rotated = vec2(cos(ori) * (tex.x - mid ) + sin(ori) * (tex.y - mid) + mid , cos(ori) * (tex.y - mid) - sin(ori) * (tex.x - mid) + mid );
        vec4 envFrag = texture2D( envelope,  rotated);
        gl_FragColor.a = gl_Color.a*maskFrag.a;
        gl_FragColor.rgb = (pow((moddepth*envFrag.rgb + offset), powerFrag.rgb)*carrierFrag.rgb*(gl_Color.rgb*2.0 - 1.0) + add)/2.0;
    }
    '''

class EnvelopeGrating(GratingStim):
    """Second-order envelope stimuli with 3 textures; a carrier, an envelope and a mask

    **Examples**::

    env1 = EnvelopeGrating(win,ori=0, carrier='sin', envelope='sin',
            mask = 'gauss', sf=24, envsf=4, size=1, contrast=0.5,
            moddepth=1.0, envori=0, pos=[-.5,.5],interpolate=0)
            # gives a circular patch of high frequency carrier with a
            # low frequency envelope
    env2 = EnvelopeGrating(win,ori=0, carrier=noise, envelope='sin',
            mask = None, sf=1, envsf=4, size=1, contrast=0.5,
            moddepth=0.8, envori=0, pos=[-.5,-.5],interpolate=0)
            # If noise is some numpy array containing random values gives a
            # patch of noise with a low frequency sinewave envelope
    env4 = EnvelopeGrating(win,ori=90, carrier='sin', envelope='sin',
            mask = 'gauss', sf=24, envsf=4, size=1, contrast=0.5,
            moddepth=1.0, envori=0, pos=[.5,.5], beat=True, interpolate=0)
            # Setting beat will create a second order beat stimulus which
            # critically contains no net energy at the carrier frequency
            # even though it appears to be present. In this case carrier
            # and envelope are at 90 degree to each other

    With an EnvelopeStim the carrier and envelope can have different spatial
    frequencies, phases and orientations. Its position can be shifted as a whole.

    contrast controls the contrast of the carrier and moddepth the modulation
    depth of the envelope. contrast and moddepth must work together, for moddepth=1 the max carrier
    contrast is 0.5 otherwise the displayable range will be exceeded. If moddepth < 1 higher contrasts can be accommodated.

    Opacity controls the transparency of the whole stimulus.

    Because orientation is implemented very differently for the carrier and
    envelope using this function without a broadly circular mask may produce unexpected results

    **Using EnvelopeStim with images from disk (jpg, tif, png, ...)**

    Ideally texture images to be rendered should be square with 'power-of-2'
    dimensions e.g. 16x16, 128x128. Any image that is not will be upscaled
    (with linear interpolation) to the nearest such texture by PsychoPy.
    The size of the stimulus should be specified in the normal way using
    the appropriate units (deg, pix, cm, ...). Be sure to get the aspect
    ratio the same as the image (if you don't want it stretched!).
    """

    def __init__(self,
                 win,
                 carrier="noise",
                 mask="none",
                 envelope="sin",
                 anchor="center",
                 units="",
                 pos=(0.0, 0.0),
                 size=None,
                 sf=None,
                 envsf=None,
                 ori=0.0,
                 envori=0.0,
                 phase=(0.0, 0.0),
                 envphase=(0.0, 0.0),
                 beat=False,
                 texRes=128,
                 rgb=None,
                 dkl=None,
                 lms=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=0.5,  # see doc
                 moddepth=1.0,  # modulation depth for envelope
                 power=1.0, # power to raise modulator to.
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
        assert win._haveShaders is True, ("Currently EnvelopeGratings needs "
                                         "your graphics card to have shaders"
                                         " and yours does not seem to.")
        self._initParams = dir()
        for unecess in ['self', 'rgb', 'dkl', 'lms']:
            self._initParams.remove(unecess)
        # initialise parent class
        GratingStim.__init__(self, win,
                             units=units, pos=pos, size=size, sf=sf,
                             ori=ori, phase=phase, anchor=anchor,
                             color=color, colorSpace=colorSpace,
                             contrast=contrast, opacity=opacity,
                             depth=depth, interpolate=interpolate,
                             name=name, autoLog=autoLog, autoDraw=autoDraw,
                             maskParams=None)

        # UGLY HACK: Some parameters depend on each other for processing.
        # They are set "superficially" here.
        # TO DO: postpone calls to _createTexture, setColor and
        # _calcCyclesPerStim whin initiating stimulus

        #AJS
        self.__dict__['carrier'] = carrier
        self.__dict__['envelope'] = envelope
        self.__dict__['maskParams'] = maskParams

        # initialise textures and masks for stimulus
        self._carrierID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._carrierID))
        self._envelopeID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._envelopeID))
        self._powerID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._powerID))
        self.interpolate = interpolate
        del self._texID  # created by GratingStim.__init__
        self.texRes = int(texRes)
        self.mask = mask

        self.envelope = envelope
        self.carrier = carrier
        self.envsf = val2array(envsf)
        self.envphase = val2array(envphase, False)
        self.envori = float(envori)
        self.moddepth = float(moddepth)
        self.power = float(power)
        if beat in ['True','true','Yes','yes','Y','y']:
            self.beat = True
        elif beat in ['False','false','No','no','N','n']:
            self.beat = False
        else:
            self.beat = bool(beat)
        self._needUpdate = True
        self.blendmode=blendmode
        self._shaderProgBeat = _shaders.compileProgram(
            _shaders.vertSimple, carrierEnvelopeMaskFrag)
        self._shaderProgPow = _shaders.compileProgram(
            _shaders.vertSimple, carrierEnvelopeMaskFragPow)

        self.local = numpy.ones((texRes, texRes), dtype=numpy.ubyte)
        self.local_p = self.local.ctypes
        # fix scaling to window coords
        self._calcEnvCyclesPerStim()
        
        del self.__dict__['tex']

    @attributeSetter
    def envsf(self, value):
        """Spatial frequency of the envelope texture

        Should be a :ref:`x,y-pair <attrib-xy>` or
        :ref:`scalar <attrib-scalar>` or None.
        If `units` == 'deg' or 'cm' units are in cycles per deg or cm
        as appropriate.
        If `units` == 'norm' then sf units are in cycles per stimulus
        (and so envsf scales with stimulus size).
        If texture is an image loaded from a file then envsf=None defaults
        to 1/stimSize to give one cycle of the image.
        Note sf is inhertited from GratingStim and controls the spatial frequency of the carrier
        """

        # Recode phase to numpy array
        if value is None:
            # set the sf to default e.g. 1./size of the loaded image etc

            if (self.units in ['pix', 'pixels'] or
                    self._origSize is not None and
                    self.units in ['deg', 'cm']):
                value = 1.0/self.size  # default to one cycle
            else:
                value = numpy.array([1.0, 1.0])
        else:
            value = val2array(value)

        # Set value and update stuff
        self.__dict__['envsf'] = value
        self._calcEnvCyclesPerStim()
        self._needUpdate = True

    @attributeSetter
    def envphase(self, value):
        """Phase of the modulation in each dimension of the envelope texture.

        Should be an :ref:`x,y-pair <attrib-xy>` or
        :ref:`scalar <attrib-scalar>`

        **NB** phase has modulus 1 (rather than 360 or 2*pi)
        This is a little unconventional but has the nice effect
        that setting phase=t*n drifts a stimulus at n Hz
        Note phase in inherited from GratingStim and controls the phase of the carrier
        """
        # Recode phase to numpy array
        value = val2array(value)
        self.__dict__['envphase'] = value
        self._needUpdate = True

    @attributeSetter
    def moddepth(self, value):
        """Modulation depth or 'contrast' for the envelope component (0.0 - 1.0)

        Sets the range of variation in carrier contrast.
        MD=(Cmax-Cmin)/(Cma+Cmin)
        """
        self.__dict__['moddepth'] = value
        self._needUpdate = True

    @attributeSetter
    def envori(self, value):
        """The orientation for the envelope texture (in degrees).

        Should be a single value (scalar). Operations are supported.
        Orientation convention is like a clock: 0 is vertical, and positive values rotate clockwise. Beyond 360 and below zero values wrap appropriately.
        Note ori is inhertied from gratingStim and controls only the orientation of the carrier
        """
        self.__dict__['envori'] = value
        self._needUpdate = True

    @attributeSetter
    def beat(self, value):
        """Beat (True) stimulus or full moduaiton (False)

        'The differences is that the spatial frequency components of the carrier are absent in a beat
        (although the carrier will still be a visible component of the overall image)
        whereas they are present in a full modulation. Beats will always appear to have a 100% modulation
        depth and if sinusoidal the modulation will appear to be twice the requested spatial frequency.
        The modulation depth of fully modulated stimuli can be varied and they appear at their true frequency.
        Both beats and full modulations appear in the literature and have specific uses.
        """
        if value in ['True','true','Yes','yes','Y','y']:
            self.__dict__['beat'] =True
        elif value in ['False','false','No','no','N','n']:
            self.__dict__['beat'] =False
        else:
            self.__dict__['beat'] =bool(value)
        self._needUpdate = True


    #@attributeSetter
    #def blendmode(self, value):
    #    """The OpenGL mode in which the stimulus is draw
    #
    #    Can the 'avg' or 'add'. Average (avg) places the new stimulus over the old one
    #    with a transparency given by its opacity. Opaque stimuli will hide other stimuli
    #    transparent stimuli won't. Add performs the arithmetic sum of the new stimulus and the ones
    #    already present.
    #
    #    """
    #    self.__dict__['blendmode'] = value
    #   self._needUpdate = True

    @attributeSetter
    def carrier(self, value):
        """Texture to use in the stimulus as a carrier, typically noise array.

        This can be one of various options:
            + the name of an image file (most formats supported)
            + a numpy array (1xN or NxN) ranging -1:1

        If specifying your own texture using an image or numpy array
        you should ensure that the image has square power-of-two
        dimesnions (e.g. 256 x 256). If not then PsychoPy will upsample
        your stimulus to the next larger power of two.
        """
        self._createTexture(value, id=self._carrierID, pixFormat=GL.GL_RGB,
                            stim=self, res=self.texRes)
        # if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize is None:
            self.size = None  # Reset size do default
        self.__dict__['carrier'] = value
        self._needTextureUpdate = False

    @attributeSetter
    def envelope(self, value):
        """Texture to use on the stimulus as a envelope, typically a grating.

        This can be one of various options:
            + **'sin'**,'sqr', 'saw', 'tri', None (resets to default)
            + the name of an image file (most formats supported)
            + a numpy array (1xN or NxN) ranging -1:1

        If specifying your own texture using an image or numpy array
        you should ensure that the image has square power-of-two dimesnions
        (e.g. 256 x 256). If not then PsychoPy will upsample your stimulus
        to the next larger power of two.
        """
        self._createTexture(value, id=self._envelopeID,
                            pixFormat=GL.GL_RGB, stim=self,
                            res=self.texRes)

        # if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize is None:
            self.size = None  # Reset size do default
        self.__dict__['envelope'] = value
        self._needTextureUpdate = False

    @attributeSetter
    def power(self, value):
        """Will raise the modulator to the given power 
           using the equation S=C*(1+M)^power where C is the carrier and M
           is the modulator. Only works with AM envelopes (hence +1) in 
           equation. Power is ignored if a beat is requested.
           This is used to obtain the square root of the modulator (power = 0.5)
           which is useful if combining two envelope gratings with different carriers
           and a 180 degree phase shift as the resulting combined signal will not 
           have any reduction in local contrast at any point in the image.
           This is similar - but not identical to the method used by 
           Landy and Oruc, Vis Res 2002.
           Note overall contrast (apparent carrier contrast) will be altered.
        """
        self._createTexture(
            numpy.ones((self.texRes,self.texRes)) * value,
            id=self._powerID,
            pixFormat=GL.GL_RGB,
            stim=self,
            res=self.texRes)

        # if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize is None:
            self.size = None  # Reset size do default
        self.__dict__['power'] = value
        self._needTextureUpdate = False

    @attributeSetter
    def texRes(self, value):
        """Power-of-two int. Sets the resolution of the mask and texture.
        texRes is overridden if an array or image is provided as mask.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['texRes'] = value

        # ... now rebuild textures (call attributeSetters without logging).
        if hasattr(self, 'carrier'):
            self._set('carrier', self.carrier, log=False)
        if hasattr(self, 'envelope'):
            self._set('envelope', self.envelope, log=False)
        #if hasattr(self, 'power'):
        #    self._set('power', self.power, log=False)
        if hasattr(self, 'mask'):
            self._set('mask', self.mask, log=False)

    def setTexRes(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('texRes', value, log=log)

    def setEnvori(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('envori', value, log=log)

    def setEnvsf(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('envsf', value, log=log)

    def setEnvphase(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('envphase', value, log=log)

    def setModdepth(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('moddepth', value, log=log)
        
    def setPower(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self.power = numpy.ones(self.texRes,self.texRes)*value 

    def setBeat(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('beat', value, log=log)

    def setCarrier(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self.carrier = value

    def setEnvelope(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self.envelope = value

    #def setBlendmode(self, value, log=None):
    #    """DEPRECATED. Use 'stim.parameter = value' syntax instead
    #    """
    #    self._set('blendmode', value, log=log)

    #def draw(self, win=None):
    #    """Draw the stimulus in its relevant window. You must call
    #    this method after every MyWin.flip() if you want the
    #    stimulus to appear on that frame and then update the screen
    #    again.
    #    """
    #    if win is None:
    #        win = self.win

    #    saveBlendMode=win.blendMode
    #    win.blendMode=self.blendmode
     #   self._selectWindow(win)
    #
    #    super(EnvelopeGrating, self).draw(win)

    #    win.blendMode=saveBlendMode

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """

        # make some corrections for the envelope:: This could be done whenever
        # the envelope variables are set using some internal variables,
        # putting it here is safer but sometimes slower

        # correct envelope orientation to adjust for link with carrier
        # orientation, to make it clockwise handed and convert to radians
        envrad = (self.ori - self.envori) * numpy.pi / 180.0

        # adjust envelope phases so that any envelope drift points
        # in the same direction as the envelope.
        rph1 = (numpy.cos(envrad) *
                self.envphase[0] + numpy.sin(envrad) * self.envphase[1])
        rph2 = (-numpy.cos(envrad) *
                self.envphase[1] + numpy.sin(envrad) * self.envphase[0])

        # we need a corrective offset when the blendmode is set to average
        if self.blendmode=='avg':
            addvalue = 1.0
        else:
            addvalue = 0.0
            
        # setup the shaderprogram
        if self.beat:
            self._shaderProg = self._shaderProgBeat
        else:
            self._shaderProg = self._shaderProgPow
        self._needUpdate = False
        GL.glNewList(self._listID, GL.GL_COMPILE)
        GL.glUseProgram(self._shaderProg)

        # set the carrier to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self._shaderProg, b"carrier"),
                       0)
        # set the envelope to be texture unit 1
        GL.glUniform1i(GL.glGetUniformLocation(
            self._shaderProg, b"envelope"), 1)
        GL.glUniform1i(GL.glGetUniformLocation(
            self._shaderProg, b"mask"), 2)  # mask is texture unit 2
        GL.glUniform1i(GL.glGetUniformLocation(
            self._shaderProg, b"power"), 3)  # power is texture unit 3
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, b"moddepth"), self.moddepth)
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, b"ori"), envrad)
        # CM envelopes use (modedepth*envelope+1.0)*carrier. If beat is True
        # this becomes (moddepth*envelope)*carrier thus maing a second order
        # 'beat' pattern.
        if self.beat:
            GL.glUniform1f(GL.glGetUniformLocation(
                self._shaderProg, b"offset"),0.0)
        else:
            GL.glUniform1f(GL.glGetUniformLocation(
                self._shaderProg, b"offset"), 1.0)
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, b"add"), addvalue)

        # mask
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        # envelope
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._envelopeID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        #power
        GL.glActiveTexture(GL.GL_TEXTURE3)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._powerID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        # carrier
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._carrierID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        Lcar = (-self._cycles[0]/2) - self.phase[0] + 0.5
        Rcar = (+self._cycles[0]/2) - self.phase[0] + 0.5
        Tcar = (+self._cycles[1]/2) - self.phase[1] + 0.5
        Bcar = (-self._cycles[1]/2) - self.phase[1] + 0.5

        Lenv = (-self._envcycles[0]/2) - rph1 + 0.5
        Renv = (+self._envcycles[0]/2) - rph1 + 0.5
        Tenv = (+self._envcycles[1]/2) - rph2 + 0.5
        Benv = (-self._envcycles[1]/2) - rph2 + 0.5
        Lmask = Bmask = 0.0
        Tmask = Rmask = 1.0  # mask

        # access just once because it's slower than basic property
        vertsPix = self.verticesPix
        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rcar, Bcar)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Renv, Benv)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE2, Rmask, Bmask)
        GL.glVertex2f(vertsPix[0, 0], vertsPix[0, 1])
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Lcar, Bcar)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lenv, Benv)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE2, Lmask, Bmask)
        GL.glVertex2f(vertsPix[1, 0], vertsPix[1, 1])
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Lcar, Tcar)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lenv, Tenv)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE2, Lmask, Tmask)
        GL.glVertex2f(vertsPix[2, 0], vertsPix[2, 1])
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rcar, Tcar)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Renv, Tenv)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE2, Rmask, Tmask)
        GL.glVertex2f(vertsPix[3, 0], vertsPix[3, 1])
        GL.glEnd()

        # unbind the textures
        #power
        GL.glActiveTexture(GL.GL_TEXTURE3)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # mask
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # envelope
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        # main carrier
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)

        GL.glEndList()

    def clearTextures(self):
        """This will be used by the __del__ method of EnvelopeGrating
        """
        GL.glDeleteTextures(1, self._carrierID)
        GL.glDeleteTextures(1, self._envelopeID)
        GL.glDeleteTextures(1, self._maskID)

    def _calcEnvCyclesPerStim(self):
        """The user should never need to call this function directly as it is
        called whenever there is a need to recalcuate the spatial
        frequency of the envelope.
        """
        if self.units in ('norm', 'height'):
            # self._cycles = self.sf  # this is the only form of sf that is
            # not size dependent
            self._envcycles = self.envsf
        else:
            # self._cycles = self.sf * self.size
            self._envcycles = self.envsf * self.size
