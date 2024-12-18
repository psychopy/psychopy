#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display an image on `psycopy.visual.Window`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet

from psychopy.layout import Size

pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import numpy
from fractions import Fraction

import psychopy  # so we can get the __path__
from psychopy import logging, colors, layout
from psychopy.tools import gltools as gt

from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.visual.basevisual import (
    BaseVisualStim, DraggingMixin, ContainerMixin, ColorMixin, TextureMixin
)

USE_LEGACY_GL = pyglet.version < '2.0'


class ImageStim(BaseVisualStim, DraggingMixin, ContainerMixin, ColorMixin,
                TextureMixin):
    """Display an image on a :class:`psychopy.visual.Window`
    """

    def __init__(self,
                 win,
                 image=None,
                 mask=None,
                 units="",
                 pos=(0.0, 0.0),
                 size=None,
                 anchor="center",
                 ori=0.0,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=None,
                 depth=0,
                 interpolate=False,
                 draggable=False,
                 flipHoriz=False,
                 flipVert=False,
                 texRes=128,
                 name=None,
                 autoLog=None,
                 maskParams=None):
        """ """  # Empty docstring. All doc is in attributes
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(ImageStim, self).__init__(win, units=units, name=name,
                                        autoLog=False)  # set at end of init
        self.draggable = draggable
        # use shaders if available by default, this is a good thing
        self.__dict__['useShaders'] = win._haveShaders

        # initialise textures for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self._pixbuffID = GL.GLuint()
        GL.glGenBuffers(1, ctypes.byref(self._pixbuffID))
        self.__dict__['maskParams'] = maskParams
        self.__dict__['mask'] = mask
        # Not pretty (redefined later) but it works!
        self.__dict__['texRes'] = texRes

        # Other stuff
        self._imName = image
        self.isLumImage = None
        self.interpolate = interpolate
        self.vertices = None
        self.anchor = anchor
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        self._requestedSize = size
        self._origSize = None  # updated if an image texture gets loaded
        self.size = size
        self.pos = numpy.array(pos, float)
        self.ori = float(ori)
        self.depth = depth

        # color and contrast etc
        self.rgbPedestal = [0, 0, 0] # does an rgb pedestal make sense for an image?
        self.colorSpace = colorSpace  # omit decorator
        self.color = color
        self.contrast = float(contrast)
        self.opacity = opacity

        # Set the image and mask-
        self.setImage(image, log=False)
        self.texRes = texRes  # rebuilds the mask
        self.size = size

        # normalized texture coordinates
        self._texCoords = numpy.array(
            [[1, 0], [0, 0], [0, 1], [1, 1]], dtype=float)
        self._maskCoords = self._texCoords.copy()

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def __del__(self):
        """Remove textures from graphics card to prevent crash
        """
        try:
            #if hasattr(self, '_listID'):
                # GL.glDeleteLists(self._listID, 1)
            self.clearTextures()
        except (ImportError, ModuleNotFoundError, TypeError):
            pass  # has probably been garbage-collected already

    def draw(self, win=None):
        """Draw the stimulus on the window.

        Parameters
        ----------
        win : `~psychopy.visual.Window`, optional
            The window to draw the stimulus on. If None, the stimulus will be
            drawn on the window that was passed to the constructor.

        """
        # check the type of image we're dealing with
        if (type(self.image) != numpy.ndarray and
                self.image in (None, "None", "none")):
            return

        # make the context for the window current
        if win is None:
            win = self.win
        self._selectWindow(win)
        win.setOrthographicView()
        win.setScale('pix')

        # If our image is a movie stim object, pull pixel data from the most
        # recent frame and write it to the memory
        if hasattr(self.image, 'getVideoFrame'):
            videoFrame = self.image.getVideoFrame()
            if videoFrame is not None:
                self._movieFrameToTexture(videoFrame)

        # GL.glColor4f(*self._foreColor.render('rgba1'))

        if self._needTextureUpdate:
            self.setImage(value=self._imName, log=False)

        if self.isLumImage:  # select the appropriate shader
            # for a luminance image do recoloring
            _prog = self.win._progSignedTexMask
        else:
            # for an rgb image there is no recoloring
            _prog = self.win._progImageStim

        gt.useProgram(_prog)

        # bind textures
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE1)  # mask
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glActiveTexture(GL.GL_TEXTURE0)  # color/lum image
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

        if USE_LEGACY_GL:
            GL.glPushMatrix()  
            # projectionMatrix = gt.getProjectionMatrix()
            # modelViewMatrix = gt.getModelViewMatrix()
            GL.glColor4f(*self._foreColor.render('rgba1'))
        # else:
        #     projectionMatrix = win._projectionMatrix
        #     modelViewMatrix = win._viewMatrix

        # set the shader uniforms
        gt.setUniformSampler2D(_prog, b'uTexture', 0)  # is texture unit 0
        gt.setUniformSampler2D(_prog, b'uMask', 1)  # mask is texture unit 1
        gt.setUniformValue(_prog, b'uColor', self._foreColor.render('rgba1'))
        gt.setUniformMatrix(_prog, b'uProjectionMatrix', win._projectionMatrix)
        gt.setUniformMatrix(_prog, b'uModelViewMatrix', win._viewMatrix)

        # draw the image
        gt.drawClientArrays({
            'gl_Vertex': self.verticesPix,
            'gl_MultiTexCoord0': self._texCoords,
            'gl_MultiTexCoord1': self._maskCoords}, 
            'GL_QUADS')
        
        gt.useProgram(None)

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        if USE_LEGACY_GL:
            GL.glPopMatrix()

    def _movieFrameToTexture(self, movieSrc):
        """Convert a movie frame to a texture and use it.

        This method is used internally to copy pixel data from a camera object
        into a texture. This enables the `ImageStim` to be used as a
        'viewfinder' of sorts for the camera to view a live video stream on a
        window.

        Parameters
        ----------
        movieSrc : `~psychopy.hardware.camera.Camera`
            Movie source object.

        """
        # get the most recent video frame and extract color data
        colorData = movieSrc.colorData

        # get the size of the movie frame and compute the buffer size
        vidWidth, vidHeight = movieSrc.size
        nBufferBytes = vidWidth * vidHeight * 3

        # bind pixel unpack buffer
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffID)

        # Free last storage buffer before mapping and writing new frame
        # data. This allows the GPU to process the extant buffer in VRAM
        # uploaded last cycle without being stalled by the CPU accessing it.
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            nBufferBytes * ctypes.sizeof(GL.GLubyte),
            None,
            GL.GL_STREAM_DRAW)

        # Map the buffer to client memory, `GL_WRITE_ONLY` to tell the
        # driver to optimize for a one-way write operation if it can.
        bufferPtr = GL.glMapBuffer(
            GL.GL_PIXEL_UNPACK_BUFFER,
            GL.GL_WRITE_ONLY)

        bufferArray = numpy.ctypeslib.as_array(
            ctypes.cast(bufferPtr, ctypes.POINTER(GL.GLubyte)),
            shape=(nBufferBytes,))

        # copy data
        bufferArray[:] = colorData[:]

        # Very important that we unmap the buffer data after copying, but
        # keep the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # bind the texture in OpenGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

        # copy the PBO to the texture
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0,
            vidWidth, vidHeight,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            0)  # point to the presently bound buffer

        # update texture filtering only if needed
        if self.interpolate:
            texFilter = GL.GL_LINEAR
        else:
            texFilter = GL.GL_NEAREST

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MAG_FILTER,
            texFilter)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MIN_FILTER,
            texFilter)

        # important to unbind the PBO
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

    @attributeSetter
    def image(self, value):
        """The image file to be presented (most formats supported).

        This can be a path-like object to an image file, or a numpy array of
        shape [H, W, C] where C are channels. The third dim will usually have
        length 1 (defining an intensity-only image), 3 (defining an RGB image)
        or 4 (defining an RGBA image).

        If passing a numpy array to the image attribute, the size attribute of
        ImageStim must be set explicitly.
        """
        self.__dict__['image'] = self._imName = value

        # If given a color array, get it in rgb1
        if isinstance(value, colors.Color):
            value = value.render('rgb1')

        wasLumImage = self.isLumImage
        if type(value) != numpy.ndarray and value == "color":
            datatype = GL.GL_FLOAT
        else:
            datatype = GL.GL_UNSIGNED_BYTE

        if type(value) != numpy.ndarray and value in (None, "None", "none"):
            self.isLumImage = True
        else:
            self.isLumImage = self._createTexture(
                value, id=self._texID,
                stim=self,
                pixFormat=GL.GL_RGB,
                dataType=datatype,
                maskParams=self.maskParams,
                forcePOW2=False,
                wrapping=False)

        # update size
        self.size = self._requestedSize

        if hasattr(value, 'getVideoFrame'):  # make sure we invert vertices
            self.flipVert = True

        # if we switched to/from lum image then need to update shader rule
        if wasLumImage != self.isLumImage:
            self._needUpdate = True

        self._needTextureUpdate = False

    def setImage(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'image', value, log)

    @property
    def aspectRatio(self):
        """
        Aspect ratio of original image, before taking into account the `.size` attribute of this object.

        returns :
            Aspect ratio as a (w, h) tuple, simplified using the smallest common denominator (e.g. 1080x720 pixels
            becomes (3, 2))
        """
        # Return None if we don't have a texture yet
        if (not hasattr(self, "_origSize")) or self._origSize is None:
            return
        # Work out aspect ratio (w/h)
        frac = Fraction(*self._origSize)
        return frac.numerator, frac.denominator

    @property
    def size(self):
        return BaseVisualStim.size.fget(self)

    @size.setter
    def size(self, value):
        # store requested size
        self._requestedSize = value
        isNone = numpy.asarray(value) == None
        if (self.aspectRatio is not None) and (isNone.any()) and (not isNone.all()):
            # If only one value is None, replace it with a value which maintains aspect ratio
            pix = layout.Size(value, units=self.units, win=self.win).pix
            # Replace None value with scaled pix value
            i = isNone.argmax()
            ni = isNone.argmin()
            pix[i] = pix[ni] * self.aspectRatio[i] / self.aspectRatio[ni]
            # Recreate layout object from pix
            value = layout.Size(pix, units="pix", win=self.win)
        elif (self.aspectRatio is not None) and (isNone.all()):
            # If both values are None, use pixel size
            value = layout.Size(self._origSize, units="pix", win=self.win)

        # Do base setting
        BaseVisualStim.size.fset(self, value)

    @attributeSetter
    def mask(self, value):
        """The alpha mask that can be used to control the outer
        shape of the stimulus

                + **None**, 'circle', 'gauss', 'raisedCos'
                + or the name of an image file (most formats supported)
                + or a numpy array (1xN or NxN) ranging -1:1
        """
        self.__dict__['mask'] = value
        self._createTexture(value, id=self._maskID,
                            pixFormat=GL.GL_ALPHA,
                            dataType=GL.GL_UNSIGNED_BYTE,
                            stim=self,
                            res=self.texRes,
                            maskParams=self.maskParams,
                            forcePOW2=False,
                            wrapping=True)

    def setMask(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'mask', value, log)
