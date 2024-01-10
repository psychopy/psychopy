#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Stimulus object for drawing arbitrary bitmaps that can repeat (cycle)
in either dimension. One of the main stimuli for PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet

from psychopy.colors import Color

pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter
from psychopy.visual.basevisual import (
    BaseVisualStim, DraggingMixin, ColorMixin, ContainerMixin, TextureMixin
)
import numpy


class GratingStim(BaseVisualStim, DraggingMixin, TextureMixin, ColorMixin,
                  ContainerMixin):
    """Stimulus object for drawing arbitrary bitmaps that can repeat (cycle) in
    either dimension. This is a lazy-imported class, therefore import using 
    full path `from psychopy.visual.grating import GratingStim` when inheriting
    from it.

    One of the main stimuli for PsychoPy.

    Formally `GratingStim` is just a texture behind an optional transparency
    mask  (an 'alpha mask'). Both the texture and mask can be arbitrary bitmaps
    and their combination allows an enormous variety of stimuli to be drawn in
    realtime.

    A `GratingStim` can be rotated scaled and shifted in position, its texture
    can be drifted in X and/or Y and it can have a spatial frequency in X
    and/or Y (for an image file that simply draws multiple copies in the patch).

    Also since transparency can be controlled, two `GratingStim` objects can be
    combined (e.g. to form a plaid.)

    **Using GratingStim with images from disk (jpg, tif, png, ...)**

    Ideally texture images to be rendered should be square with 'power-of-2'
    dimensions e.g. 16 x 16, 128 x 128. Any image that is not will be up-scaled
    (with linear interpolation) to the nearest such texture by PsychoPy. The
    size of the stimulus should be specified in the normal way using the
    appropriate units (deg, pix, cm, ...). Be sure to get the aspect ratio the
    same as the image (if you don't want it stretched!).

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window this shape is being drawn to. The stimulus instance will allocate
        its required resources using that Windows context. In many cases, a
        stimulus instance cannot be drawn on different windows unless those
        windows share the same OpenGL context, which permits resources to be
        shared between them.
    tex : str or None
        Texture to use for the primary carrier. Values may be one of `'sin'`,
        `'sin'`, `'sqr'`, `'saw'`, `'tri'`, or `None`.
    mask : str or None
        Optional mask to control the shape of the grating. Values may be one of
        `'circle'`, `'sin'`, `'sqr'`, `'saw'`, `'tri'`, or `None`.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    anchor : str
        Anchor string to specify the origin of the stimulus.
    pos : array_like
        Initial position (`x`, `y`) of the shape on-screen relative to the
        origin located at the center of the window or buffer in `units`. This
        can be updated after initialization by setting the `pos` property. The
        default value is `(0.0, 0.0)` which results in no translation.
    size : array_like, float, int or None
        Width and height of the shape as `(w, h)` or `[w, h]`. If a single value
        is provided, the width and height will be set to the same specified
        value. If `None` is specified, the `size` will be set with values passed
        to `width` and `height`.
    sf : float
        Spatial frequency for the grating. Values are dependent on the units in
        use to draw the stimuli.
    ori : float
        Initial orientation of the shape in degrees about its origin. Positive
        values will rotate the shape clockwise, while negative values will
        rotate counterclockwise. The default value for `ori` is 0.0 degrees.
    phase : ArrayLike
        Initial phase of the grating along the vertical and horizontal dimension
        `(x, y)`.
    texRes : int
        Resolution of the texture. The higher the resolutions, the less
        aliasing artifacts will be visible. However, this comes at the expense
        of higher video memory use. Power-of-two values are recommended
        (e.g. 256, 512, 1024, etc.)
    color : array_like, str, :class:`~psychopy.colors.Color` or None
        Sets both the initial `lineColor` and `fillColor` of the shape.
    colorSpace : str
        Sets the colorspace, changing how values passed to `lineColor` and
        `fillColor` are interpreted.
    contrast : float
        Contrast level of the shape (0.0 to 1.0). This value is used to modulate
        the contrast of colors passed to `lineColor` and `fillColor`.
    opacity : float
        Opacity of the shape. A value of 1.0 indicates fully opaque and 0.0 is
        fully transparent (therefore invisible). Values between 1.0 and 0.0 will
        result in colors being blended with objects in the background. This
        value affects the fill (`fillColor`) and outline (`lineColor`) colors of
        the shape.
    depth : int
        Depth layer to draw the shape when `autoDraw` is enabled. *DEPRECATED*
    rgbPedestal : ArrayLike
        Pedestal color `(r, g, b)`, presently unused.
    interpolate : bool
        Enable smoothing (anti-aliasing) when drawing shape outlines. This
        produces a smoother (less-pixelated) outline of the shape.
    draggable : bool
        Can this stimulus be dragged by a mouse click?
    lineRGB, fillRGB: ArrayLike, :class:`~psychopy.colors.Color` or None
        *Deprecated*. Please use `lineColor` and `fillColor`. These arguments
        may be removed in a future version.
    name : str
        Optional name of the stimuli for logging.
    autoLog : bool
        Enable auto-logging of events associated with this stimuli. Useful for
        debugging and to track timing when used in conjunction with `autoDraw`.
    autoDraw : bool
        Enable auto drawing. When `True`, the stimulus will be drawn every frame
        without the need to explicitly call the
        :py:meth:`~psychopy.visual.shape.ShapeStim.draw()` method.

    Examples
    --------
    Creating a circular grating with a sinusoidal pattern::

        myGrat = GratingStim(tex='sin', mask='circle')

    Create a 'Gabor'::

        myGabor = GratingStim(tex='sin', mask='gauss')

    """
    def __init__(self,
                 win,
                 tex="sin",
                 mask="none",
                 units=None,
                 anchor="center",
                 pos=(0.0, 0.0),
                 size=None,
                 sf=None,
                 ori=0.0,
                 phase=(0.0, 0.0),
                 texRes=128,
                 rgb=None,
                 dkl=None,
                 lms=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=None,
                 depth=0,
                 rgbPedestal=(0.0, 0.0, 0.0),
                 interpolate=False,
                 draggable=False,
                 blendmode='avg',
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 maskParams=None):
        """ """  # Empty docstring. All doc is in attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        for unecess in ['self', 'rgb', 'dkl', 'lms']:
            self._initParams.remove(unecess)
        # initialise parent class
        super(GratingStim, self).__init__(win, units=units, name=name,
                                          autoLog=False)
        self.draggable = draggable
        # UGLY HACK: Some parameters depend on each other for processing.
        # They are set "superficially" here.
        # TO DO: postpone calls to _createTexture, setColor and
        # _calcCyclesPerStim whin initiating stimulus
        self.__dict__['contrast'] = 1
        self.__dict__['size'] = 1
        self.__dict__['sf'] = 1
        self.__dict__['tex'] = tex
        self.__dict__['maskParams'] = maskParams

        # initialise textures and masks for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.__dict__['texRes'] = texRes  # must be power of 2
        self.interpolate = interpolate

        # NB Pedestal isn't currently being used during rendering - this is a
        # place-holder
        self.rgbPedestal = val2array(rgbPedestal, False, length=3)
        # No need to invoke decorator for color updating. It is done just
        # below.
        self.colorSpace = colorSpace
        self.color = color
        if rgb is not None:
            logging.warning("Use of rgb arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.color = Color(rgb, 'rgb')
        elif dkl is not None:
            logging.warning("Use of dkl arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.color = Color(dkl, 'dkl')
        elif lms is not None:
            logging.warning("Use of lms arguments to stimuli are deprecated."
                            " Please use color and colorSpace args instead")
            self.color = Color(lms, 'lms')

        # set other parameters
        self.ori = float(ori)
        self.phase = val2array(phase, False)
        self._origSize = None  # updated if an image texture is loaded

        self._requestedSize = size
        self.size = size
        self.sf = val2array(sf)
        self.pos = val2array(pos, False, False)
        self.depth = depth
        self.anchor = anchor

        # self.tex = tex
        self.mask = mask
        self.contrast = float(contrast)
        self.opacity = opacity
        self.autoLog = autoLog
        self.autoDraw = autoDraw
        self.blendmode = blendmode

        # fix scaling to window coords
        self._calcCyclesPerStim()

        # generate a displaylist ID
        self._listID = GL.glGenLists(1)

        # JRG: doing self._updateList() here means MRO issues for RadialStim,
        # which inherits from GratingStim but has its own _updateList code.
        # So don't want to do the update here (= ALSO the init of RadialStim).
        # Could potentially define a BaseGrating class without
        # updateListShaders code, and have GratingStim and RadialStim
        # inherit from it and add their own _updateList stuff.
        # Seems unnecessary. Instead, simply defer the update to the
        # first .draw(), should be fast:
        # self._updateList()  # ie refresh display list
        self._needUpdate = True

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

    @attributeSetter
    def sf(self, value):
        """Spatial frequency of the grating texture.

        Should be a :ref:`x,y-pair <attrib-xy>` or :ref:`scalar <attrib-scalar>`
        or None. If `units` == 'deg' or 'cm' units are in cycles per deg or cm
        as appropriate. If `units` == 'norm' then sf units are in cycles per
        stimulus (and so SF scales with stimulus size). If texture is an image
        loaded from a file then sf=None defaults to 1/stimSize to give one cycle
        of the image.

        """
        # Recode phase to numpy array
        if value is None:
            # Set the sf to default (e.g. to the 1.0/size of the loaded image
            if (self.units in ('pix', 'pixels') or
                    self._origSize is not None and
                    self.units in ('deg', 'cm')):
                value = 1.0 / self.size  # default to one cycle
            else:
                value = numpy.array([1.0, 1.0])
        else:
            value = val2array(value)

        # Set value and update stuff
        self.__dict__['sf'] = value
        self._calcCyclesPerStim()
        self._needUpdate = True

    @attributeSetter
    def phase(self, value):
        """Phase of the stimulus in each dimension of the texture.

        Should be an :ref:`x,y-pair <attrib-xy>` or :ref:`scalar
        <attrib-scalar>`

        **NB** phase has modulus 1 (rather than 360 or 2*pi) This is a little
        unconventional but has the nice effect that setting phase=t*n drifts a
        stimulus at *n* Hz.

        """
        # Recode phase to numpy array
        value = val2array(value)
        self.__dict__['phase'] = value
        self._needUpdate = True

    # overload ColorMixin methods so that they refresh the image after being called
    @property
    def foreColor(self):
        # Call setter of parent mixin
        return ColorMixin.foreColor.fget(self)

    @foreColor.setter
    def foreColor(self, value):
        # Call setter of parent mixin
        ColorMixin.foreColor.fset(self, value)
        # Reset texture
        self._needTextureUpdate = True
        self._needUpdate = True

    @property
    def contrast(self):
        # Call setter of parent mixin
        return ColorMixin.contrast.fget(self)

    @contrast.setter
    def contrast(self, value):
        # Call setter of parent mixin
        ColorMixin.contrast.fset(self, value)
        # Reset texture
        self._needTextureUpdate = True
        self._needUpdate = True

    @property
    def opacity(self):
        # Call setter of parent mixin
        return BaseVisualStim.opacity.fget(self)

    @opacity.setter
    def opacity(self, value):
        # Call setter of parent mixin
        BaseVisualStim.opacity.fset(self, value)
        # Reset texture
        self._needTextureUpdate = True
        self._needUpdate = True

    @attributeSetter
    def tex(self, value):
        """Texture to used on the stimulus as a grating (aka carrier).

        This can be one of various options:
            + **'sin'**,'sqr', 'saw', 'tri', None (resets to default)
            + the name of an image file (most formats supported)
            + a numpy array (1xN or NxN) ranging -1:1

        If specifying your own texture using an image or numpy array you should
        ensure that the image has square power-of-two dimensions (e.g. 256 x
        256). If not then PsychoPy will up-sample your stimulus to the next
        larger power of two.

        """
        self._createTexture(
            value,
            id=self._texID,
            pixFormat=GL.GL_RGB,
            stim=self,
            res=self.texRes,
            maskParams=self.maskParams)

        self.__dict__['tex'] = value
        self._needTextureUpdate = False

    @attributeSetter
    def blendmode(self, value):
        """The OpenGL mode in which the stimulus is draw

        Can the 'avg' or 'add'. Average (avg) places the new stimulus over the
        old one with a transparency given by its opacity. Opaque stimuli will
        hide other stimuli transparent stimuli won't. Add performs the
        arithmetic sum of the new stimulus and the ones already present.

        """
        self.__dict__['blendmode'] = value
        self._needUpdate = True

    def setSF(self, value, operation='', log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('sf', value, operation, log=log)

    def setPhase(self, value, operation='', log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('phase', value, operation, log=log)

    def setTex(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self.tex = value

    def setBlendmode(self, value, log=None):
        """DEPRECATED. Use 'stim.parameter = value' syntax instead
        """
        self._set('blendmode', value, log=log)

    def draw(self, win=None):
        """Draw the stimulus in its relevant window.

        You must call this method after every `MyWin.flip()` if you want the
        stimulus to appear on that frame and then update the screen again.

        Parameters
        ----------
        win : `~psychopy.visual.Window` or `None`
            Window to draw the stimulus to. Context sharing must be enabled if
            any other window beside the one specified during creation of this
            stimulus is specified.

        """
        if win is None:
            win = self.win

        self._selectWindow(win)
        saveBlendMode = win.blendMode
        win.setBlendMode(self.blendmode, log=False)

        # do scaling
        GL.glPushMatrix()  # push before the list, pop after
        win.setScale('pix')
        # the list just does the texture mapping
        GL.glColor4f(*self._foreColor.render('rgba1'))

        if self._needTextureUpdate:
            self.setTex(value=self.tex, log=False)
        if self._needUpdate:
            self._updateList()
        GL.glCallList(self._listID)

        # return the view to previous state
        GL.glPopMatrix()
        win.setBlendMode(saveBlendMode, log=False)

    def _updateListShaders(self):
        """The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False
        GL.glNewList(self._listID, GL.GL_COMPILE)
        # setup the shaderprogram
        _prog = self.win._progSignedTexMask
        GL.glUseProgram(_prog)
        # set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(_prog, b"texture"), 0)
        # mask is texture unit 1
        GL.glUniform1i(GL.glGetUniformLocation(_prog, b"mask"), 1)
        # mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D

        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        Ltex = (-self._cycles[0] / 2) - self.phase[0] + 0.5
        Rtex = (+self._cycles[0] / 2) - self.phase[0] + 0.5
        Ttex = (+self._cycles[1] / 2) - self.phase[1] + 0.5
        Btex = (-self._cycles[1] / 2) - self.phase[1] + 0.5
        Lmask = Bmask = 0.0
        Tmask = Rmask = 1.0  # mask

        # access just once because it's slower than basic property
        vertsPix = self.verticesPix
        GL.glBegin(GL.GL_QUADS)  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rtex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Rmask, Bmask)
        GL.glVertex2f(vertsPix[0, 0], vertsPix[0, 1])
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Ltex, Btex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lmask, Bmask)
        GL.glVertex2f(vertsPix[1, 0], vertsPix[1, 1])
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Ltex, Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Lmask, Tmask)
        GL.glVertex2f(vertsPix[2, 0], vertsPix[2, 1])
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, Rtex, Ttex)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, Rmask, Tmask)
        GL.glVertex2f(vertsPix[3, 0], vertsPix[3, 1])
        GL.glEnd()

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)

        GL.glEndList()

    def __del__(self):
        try:
            GL.glDeleteLists(self._listID, 1)
        except Exception:
            pass  # probably we don't have a _listID property
        try:
            # remove textures from graphics card to prevent crash
            self.clearTextures()
        except Exception:
            pass

    def _calcCyclesPerStim(self):
        if self.units in ('norm', 'height'):
            # this is the only form of sf that is not size dependent
            self._cycles = self.sf
        else:
            self._cycles = self.sf * self.size
