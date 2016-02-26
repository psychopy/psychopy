#!/usr/bin/env python2

"""Stimulus object for drawing arbitrary bitmap carriers with an arbitrary
second order envelope carrier and envelope can vary independently for
orienation, frequencyand phase. Also does beat stimuli. """

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# some code provided by Andrew Schofield
# Distributed under the terms of the GNU General Public License (GPL).

# Requires shaders if you don't have them it will just throw and error.
# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+

from __future__ import absolute_import

import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter
from .grating import GratingStim
import numpy

from . import shaders as _shaders

# we need a different shader program for this (3 textures)
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
        gl_FragColor.rgb = ((moddepth*envFrag.rgb+offset)*carrierFrag.rgb* (gl_Color.rgb*2.0-1.0)+add)/2.0;
    }
    '''


class EnvelopeGrating(GratingStim):
    """A stimulus with 3 textures; a carrier, an envelope and a mask

    **Examples**::

    env1 = EnvelopeGrating(win,ori=0, carrier='sin', envelope='sin',
            mask = 'gauss', sf=24, envsf=4, size=1, contrast=0.5,
            moddepth=1.0, envori=0, pos=[-.5,.5],interpolate=0)
            # gives a circular patch of high frequency carrier with a
            # low frequency envelope
    env2 = EnvelopeGrating(win,ori=0, carrier=noise, envelope='sin',
            mask = None, sf=1, envsf=4, size=1, contrast=0.5,
            moddepth=0.8, envori=0, pos=[-.5,-.5],interpolate=0)
            # If noise is some numpy array contaning random values gives a
            # circular patch of noise with a low freqeuncy sinewave envelope
    env4 = EnvelopeGrating(win,ori=90, carrier='sin', envelope='sin',
            mask = 'gauss', sf=24, envsf=4, size=1, contrast=0.5,
            moddepth=1.0, envori=0, pos=[.5,.5], beat=True, interpolate=0)
            # Setting beat will create a second order beat stimulus which
            # critically contains no net energy at the carrier frequency
            # even though it appears to be present in this case carrier
            # and envelope are at 90 degree to each other

    With an EnvelopeStim the carrier and envelope can have different spatial
    frequency phase and orientation. Its position can be shifted as a whole.
    contrast controls the contrast of the carrier and moddepth the modulation
    depth of the envelope.
    opacity controls the transparency of the whole stimulus.

    Because orientation is implemented very differently for the carrier and
    envelope using this function without a msk will produce unexpected results

    **Using EnvelopeStim with images from disk (jpg, tif, png, ...)**

    Ideally texture images to be rendered should be square with 'power-of-2'
    dimensions e.g. 16x16, 128x128. Any image that is not will be upscaled
    (with linear interpolation) to the nearest such texture by PsychoPy.
    The size of the stimulus should be specified in the normal way using
    the appropriate units (deg, pix, cm, ...). Be sure to get the aspect
    ratio the same as the image (if you don't want it stretched!).

    contrast and moddepth must work together, for moddepth=1 the max carrier
    contrast is 0.5. If moddepth < 1 higher contrasts can be accomodated.
    """

    def __init__(self,
                 win,
                 carrier="noise",
                 mask="none",
                 envelope="sin",
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
                 # not sure what this will do with an envelope stimulus.
                 opacity=1.0,
                 depth=0,
                 rgbPedestal=(0.0, 0.0, 0.0),
                 interpolate=False,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 maskParams=None):
        """ """  # Empty docstring. All doc is in attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        assert win._haveShaders is True, ("Currently EnvelopeGratings need "
                                          "your graphics card to have shaders"
                                          " and yours does not seem to.")
        self._initParams = dir()
        for unecess in ['self', 'rgb', 'dkl', 'lms']:
            self._initParams.remove(unecess)
        # initialise parent class
        GratingStim.__init__(self, win,
                             units=units, pos=pos, size=size, sf=sf,
                             ori=ori, phase=phase,
                             color=color, colorSpace=colorSpace,
                             contrast=contrast, opacity=opacity,
                             depth=depth, interpolate=interpolate,
                             name=name, autoLog=autoLog, autoDraw=autoDraw,
                             maskParams=None)
        # use shaders if available by default, this is a good thing
        self.__dict__['useShaders'] = win._haveShaders
        # UGLY HACK: Some parameters depend on each other for processing.
        # They are set "superficially" here.
        # TO DO: postpone calls to _createTexture, setColor and
        # _calcCyclesPerStim whin initiating stimulus
        self.__dict__['carrier'] = carrier
        self.__dict__['envelope'] = envelope
        self.__dict__['maskParams'] = maskParams

        # initialise textures and masks for stimulus
        self._carrierID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._carrierID))
        self._envelopeID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._envelopeID))
        self.interpolate = interpolate
        del self._texID  # created by GratingStim.__init__

        self.mask = mask
        self.envelope = envelope
        self.carrier = carrier
        self.envsf = val2array(envsf)
        self.envphase = val2array(envphase, False)
        self.envori = float(envori)
        self.moddepth = float(moddepth)
        self.beat = bool(beat)
        # print(self.CMphase)
        self._shaderProg = _shaders.compileProgram(
            _shaders.vertSimple, carrierEnvelopeMaskFrag)

        self.local = numpy.ones((texRes, texRes), dtype=numpy.ubyte)
        self.local_p = self.local.ctypes
        # self.local=GL.GL_UNSIGNED_BYTE(self.local)
        # fix scaling to window coords
        # self._calcCyclesPerStim()
        self._calcEnvCyclesPerStim()
        del self.__dict__['tex']

    @attributeSetter
    def envsf(self, value):
        # AJS
        """Spatial frequency of the envelope texture

        Should be a :ref:`x,y-pair <attrib-xy>` or
        :ref:`scalar <attrib-scalar>` or None.
        If `units` == 'deg' or 'cm' units are in cycles per deg or cm
        as appropriate.
        If `units` == 'norm' then sf units are in cycles per stimulus
        (and so SF scales with stimulus size).
        If texture is an image loaded from a file then sf=None defaults
        to 1/stimSize to give one cycle of the image.
        """

        # Recode phase to numpy array
        if value is None:
            # set the sf to default e.g. 1./size of the loaded image etc

            if (self.units in ['pix', 'pixels'] or
                    self._origSize is not None and
                    self.units in ['deg', 'cm']):
                value = 1.0 / self.size  # default to one cycle
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
        """Phase of the modulation in each dimension of the texture.

        Should be an :ref:`x,y-pair <attrib-xy>` or
        :ref:`scalar <attrib-scalar>`

        **NB** phase has modulus 1 (rather than 360 or 2*pi)
        This is a little unconventional but has the nice effect
        that setting phase=t*n drifts a stimulus at n Hz
        """
        # Recode phase to numpy array
        value = val2array(value)
        self.__dict__['envphase'] = value
        self._needUpdate = True

    @attributeSetter
    def moddepth(self, value):
        """modulation depth for envelope
        """
        self.__dict__['moddepth'] = value
        self._needUpdate = True

    @attributeSetter
    def envori(self, value):
        """Orientation for envelope
        """
        self.__dict__['envori'] = value
        self._needUpdate = True

    @attributeSetter
    def beat(self, value):
        """Orientation for envelope
        """
        self.__dict__['beat'] = value
        self._needUpdate = True

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
        if self.useShaders == True:
            self._createTexture(value, id=self._envelopeID,
                                pixFormat=GL.GL_RGB, stim=self,
                                res=self.texRes)
        else:
            self._createTexture(value, id=self._envelopeID,
                                pixFormat=GL.GL_ALPHA, stim=self,
                                res=self.texRes)

        # if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize is None:
            self.size = None  # Reset size do default
        self.__dict__['envelope'] = value
        self._needTextureUpdate = False

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """

        # make some corrections for the envelope:: The could be done whenever
        # the envelope variables are set using some internal variables,
        # putting it here is safer but sometimes slower
        # correct envelope orientation to adjust for link with carrier
        # orientation, to make it clockwise handed and convert to radians
        envrad = (self.ori - self.envori) * numpy.pi / 180.0
        # adjust envolope phases so that any envelope drift points
        # in the same direction as the envelope.
        rph1 = (numpy.cos(envrad) *
                self.envphase[0] + numpy.sin(envrad) * self.envphase[1])
        rph2 = (-numpy.cos(envrad) *
                self.envphase[1] + numpy.sin(envrad) * self.envphase[0])

        if 'avg' in self.win.blendMode:
            addvalue = 1.0
        else:
            addvalue = 0.0

        self._needUpdate = False
        GL.glNewList(self._listID, GL.GL_COMPILE)
        # setup the shaderprogram
        GL.glUseProgram(self._shaderProg)
        # set the carrier to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self._shaderProg, "carrier"),
                       0)
        # set the envelope to be texture unit 1
        GL.glUniform1i(GL.glGetUniformLocation(
            self._shaderProg, "envelope"), 1)
        GL.glUniform1i(GL.glGetUniformLocation(
            self._shaderProg, "mask"), 2)  # mask is texture unit 2
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, "moddepth"), self.moddepth)
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, "ori"), envrad)
        # CM envelopes use (modedepth*envelope+1.0)*carrier. If beat is True
        # this becomes (moddepth*envelope)*carrier thus maing a second order
        # 'beat' pattern.
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, "offset"), 1.0 - self.beat)
        # CM envelopes use (modedepth*envelope+1.0)*carrier. If beat is True
        # this becomes (moddepth*envelope)*carrier thus maing a second order
        # 'beat' pattern.
        GL.glUniform1f(GL.glGetUniformLocation(
            self._shaderProg, "add"), addvalue)

        # mask
        GL.glActiveTexture(GL.GL_TEXTURE2)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        # envelope
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._envelopeID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        # carrier
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._carrierID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        Lcar = -self._cycles[0] / 2 - self.phase[0] + 0.5
        Rcar = +self._cycles[0] / 2 - self.phase[0] + 0.5
        Tcar = +self._cycles[1] / 2 - self.phase[1] + 0.5
        Bcar = -self._cycles[1] / 2 - self.phase[1] + 0.5

        Lenv = -self._envcycles[0] / 2 - rph1 + 0.5
        Renv = +self._envcycles[0] / 2 - rph1 + 0.5
        Tenv = +self._envcycles[1] / 2 - rph2 + 0.5
        Benv = -self._envcycles[1] / 2 - rph2 + 0.5
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

    # for the sake of older graphics cards------------------------------------
    def _updateListNoShaders(self):
        """This currently combines the carrier and evelope as if they
        add, so is plain wrong. Therefore there is an assertion in the
        init function which will throw an error if the window object does
        not have shaders. Thus this function should never be
        reached. If someone without shaders wishes to do second-order
        gratings they need a new solution.

        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False

        # glColor can interfere with multitextures
        GL.glColor4f(1.0, 1.0, 1.0, 1.0)
        # mask
        GL.glActiveTextureARB(GL.GL_TEXTURE2_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        # envelope (eg a grating but can be anything)
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._envelopeID)
        # carrier (eg noise or textuture)
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._carrierID)

        # depth = self.depth

        Lcar = -self._cycles[0] / 2 - self.phase[0] + 0.5
        Rcar = +self._cycles[0] / 2 - self.phase[0] + 0.5
        Tcar = +self._cycles[1] / 2 - self.phase[1] + 0.5
        Bcar = -self._cycles[1] / 2 - self.phase[1] + 0.5

        Lenv = -self._envcycles[0] / 2 - self.envphase[0] + 0.5
        Renv = +self._envcycles[0] / 2 - self.envphase[0] + 0.5
        Tenv = +self._envcycles[1] / 2 - self.envphase[1] + 0.5
        Benv = -self._envcycles[1] / 2 - self.envphase[1] + 0.5

        Lmask = Bmask = 0.0
        Tmask = Rmask = 1.0  # mask

        # access just once because it's slower than basic property
        vertsPix = self.verticesPix
        # draw a 4 sided polygon
        GL.glBegin(GL.GL_QUADS)
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

        # disable mask
        GL.glActiveTextureARB(GL.GL_TEXTURE2_ARB)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # disable mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # we're done!
        GL.glEndList()

    def clearTextures(self):
        """This will be used by the __del__ method of GratingStim
        """
        GL.glDeleteTextures(1, self._carrierID)
        GL.glDeleteTextures(1, self._envelopeID)
        GL.glDeleteTextures(1, self._maskID)

    def _calcEnvCyclesPerStim(self):
        """
        """
        if self.units in ('norm', 'height'):
            # self._cycles = self.sf  # this is the only form of sf that is
            # not size dependent
            self._envcycles = self.envsf
        else:
            # self._cycles = self.sf * self.size
            self._envcycles = self.envsf * self.size
