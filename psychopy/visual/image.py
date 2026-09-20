#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Display an image on `psycopy.visual.Window`"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
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

        # Layout of the pixel buffer mirroring the colour texture, filled in by
        # `_createTexture()` and left as `None` while there is no texture whose
        # storage we own (e.g. before the first image is set, or when the image
        # is another object's texture).
        self._texBufferShape = None
        self._texBufferDType = None
        self._texBufferPixFormat = None
        self._texBufferDataType = None

        # Size of the pixel buffer backing the colour texture, and whether it
        # still needs allocating and filling from that texture. Deferred until
        # something actually asks to map it (see `mapImageData`).
        self._texBufferNBytes = 0
        self._texBufferNeedsFill = False

        # uniform locations per shader program, filled in on first use
        self._uniformCache = {}
        self._matrixScratch = None

        # mapping of that buffer handed out by `imageData`, if any
        self._imageDataPtr = None
        self._imageDataArray = None
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

        if self.win.USE_LEGACY_GL:
            # generate a displaylist ID
            self._listID = GL.glGenLists(1)
            self._updateList()  # ie refresh display list
        else:
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
        except (ImportError, ModuleNotFoundError, TypeError, GL.lib.GLException):
            pass  # has probably been garbage-collected already

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False
        GL.glNewList(self._listID, GL.GL_COMPILE)

        # setup the shaderprogram
        if self.isLumImage:
            # for a luminance image do recoloring
            _prog = self.win._progSignedTexMask
            GL.glUseProgram(_prog)
            # set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(_prog, b"texture"), 0)
            # mask is texture unit 1
            GL.glUniform1i(GL.glGetUniformLocation(_prog, b"mask"), 1)
        else:
            # for an rgb image there is no recoloring
            _prog = self.win._progImageStim
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

        # access just once because it's slower than basic property
        vertsPix = self.verticesPix
        GL.glBegin(GL.GL_QUADS)  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1, 0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, 1, 0)
        GL.glVertex2f(vertsPix[0, 0], vertsPix[0, 1])
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0, 0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, 0, 0)
        GL.glVertex2f(vertsPix[1, 0], vertsPix[1, 1])
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 0, 1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, 0, 1)
        GL.glVertex2f(vertsPix[2, 0], vertsPix[2, 1])
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0, 1, 1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1, 1, 1)
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

    def _drawLegacyGL(self, win):
        """Legacy draw routine.
        """
        GL.glPushMatrix()  # push before the list, pop after
        win.setScale('pix')
        GL.glColor4f(*self._foreColor.render('rgba1'))

        if self._needTextureUpdate:
            self.setImage(value=self._imName, log=False)
        if self._needUpdate:
            self._updateList()
        GL.glCallList(self._listID)

        # return the view to previous state
        GL.glPopMatrix()

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

        # Push any edits made through `imageData` to the texture. Done here so
        # that writing to the array is all the user needs to do to change what
        # gets drawn.
        if self._imageDataArray is not None:
            self._unmapImageData()

        # If our image is a movie stim object, pull pixel data from the most
        # recent frame and write it to the memory
        if hasattr(self.image, 'colorTexture'):
            if hasattr(self.image, 'update'):
                self.image.update()
            self._texID = self.image.colorTexture

        if win.USE_LEGACY_GL:
            self._drawLegacyGL(win)
            return

        # `clearDepth=False` since depth testing is off for 2D drawing, so
        # clearing the depth buffer once per stimulus achieves nothing.
        win.setOrthographicView(clearDepth=False)

        # GL.glColor4f(*self._foreColor.render('rgba1'))

        if self._needTextureUpdate:
            self.setImage(value=self._imName, log=False)

        if self.isLumImage:  # select the appropriate shader
            # for a luminance image do recoloring
            _prog = self.win._progSignedTexMask
        else:
            # for an rgb image there is no recoloring
            _prog = self.win._progImageStim

        GL.glUseProgram(_prog)

        # bind textures
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE1)  # mask
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glActiveTexture(GL.GL_TEXTURE0)  # color/lum image
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

        # Set the shader uniforms. The locations are looked up once per program
        # and kept, since resolving them by name means a driver query per
        # uniform per stimulus per frame.
        uniforms = self._uniformLocations(_prog)

        loc = uniforms[b'uTexture']
        if loc != -1:
            GL.glUniform1i(loc, 0)  # is texture unit 0
        loc = uniforms[b'uMask']
        if loc != -1:
            GL.glUniform1i(loc, 1)  # mask is texture unit 1
        loc = uniforms[b'uColor']
        if loc != -1:
            GL.glUniform4f(loc, *self._foreColor.render('rgba1'))
        loc = uniforms[b'uProjectionMatrix']
        if loc != -1:
            GL.glUniformMatrix4fv(
                loc, 1, GL.GL_TRUE, self._asMatrixPtr(win._projectionMatrix))
        loc = uniforms[b'uModelViewMatrix']
        if loc != -1:
            GL.glUniformMatrix4fv(
                loc, 1, GL.GL_TRUE, self._asMatrixPtr(win._viewMatrix))

        # draw the image
        gt.drawClientArrays({
            'gl_Vertex': self.verticesPix,
            'gl_MultiTexCoord0': self._texCoords,
            'gl_MultiTexCoord1': self._maskCoords}, 
            'GL_QUADS')
        
        GL.glUseProgram(0)

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

    #: Names of the uniforms `draw()` sets, looked up once per shader program.
    _UNIFORM_NAMES = (b'uTexture', b'uMask', b'uColor', b'uProjectionMatrix',
                      b'uModelViewMatrix')

    def _uniformLocations(self, program):
        """Locations of the uniforms used when drawing, for a given program.

        Resolving a uniform by name is a query to the driver, and `draw()` sets
        five of them, so the locations are worked out the first time a program
        is used and kept from then on. They are a property of the linked
        program and don't change while it lives.

        Parameters
        ----------
        program : int
            Handle of the shader program about to be used.

        Returns
        -------
        dict
            Maps each name in `_UNIFORM_NAMES` to its location, which is `-1`
            for a uniform the program doesn't define or doesn't use.

        """
        handle = getattr(program, 'value', program)
        locations = self._uniformCache.get(handle)
        if locations is None:
            locations = {
                name: GL.glGetUniformLocation(program, name)
                for name in self._UNIFORM_NAMES}
            self._uniformCache[handle] = locations

        return locations

    def _asMatrixPtr(self, matrix):
        """Present a 4x4 matrix as something `glUniformMatrix4fv` can read.

        Parameters
        ----------
        matrix : numpy.ndarray
            The matrix to pass, converted to contiguous `float32` if it isn't
            already.

        Returns
        -------
        ctypes pointer
            Pointer to the matrix data. Only valid while `matrix` (or the
            conversion of it held in `_matrixScratch`) is alive, which is why
            the conversion is kept on the stimulus rather than discarded.

        """
        if matrix.dtype != numpy.float32 or not matrix.flags['C_CONTIGUOUS']:
            self._matrixScratch = numpy.ascontiguousarray(
                matrix, dtype=numpy.float32)
            matrix = self._matrixScratch

        return matrix.ctypes.data_as(ctypes.POINTER(GL.GLfloat))

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

        # The texture we own is about to be replaced, so drop anything mapped
        # over its pixel buffer and forget the old layout. `_createTexture()`
        # fills these in again if it ends up allocating storage for us.
        self._unmapImageData(upload=False)
        self._texBufferShape = None
        self._texBufferNBytes = 0
        self._texBufferNeedsFill = False

        # handle a matplotlib object as image
        if hasattr(value, 'canvas'):  # matplotlib figure
            if hasattr(value.canvas, 'draw'):
                value.canvas.draw()  # make sure the figure is drawn
            figDPI = value.get_dpi()
            figWidth = value.get_figwidth() * figDPI
            figHeight = value.get_figheight() * figDPI
            self._origSize = (int(figWidth), int(figHeight))
            ncol, nrow = value.canvas.get_width_height()
            value = numpy.flip(numpy.frombuffer(
                value.canvas.tostring_argb(), dtype="uint8").reshape(
                    int(nrow), int(ncol), 4), axis=0)
            # value = value[..., [1, 2, 3, 0]]  # swizzle alpha channel
            # discard alpha channel, keep RGB
            value = value[..., 1:]
            # convert to float32
            value = numpy.ascontiguousarray(
                value, dtype=numpy.float32) / 127.5 - 1
            # pixFormat = GL.GL_RGBA
        elif isinstance(value, colors.Color):
            value = value.render('rgb1')
        else:
            pass

        # determine data type
        wasLumImage = self.isLumImage
        if hasattr(value, 'colorTexture'):
            # reference to object that provides texture data
            value = value.colorTexture
            datatype = GL.GL_UNSIGNED_BYTE
            self.isLumImage = hasattr(value, 'isLumImage') and value.isLumImage
            self.flipVert = True
        else:
            # If given a color array, get it in rgb1
            if isinstance(value, colors.Color):
                value = value.render('rgb1')

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

        # if we switched to/from lum image then need to update shader rule
        if wasLumImage != self.isLumImage:
            self._needUpdate = True

        self._needTextureUpdate = False

    def setImage(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'image', value, log)

    def mapImageData(self):
        """Map the pixel buffer holding the texture data into memory.

        This is what the `imageData` property defers to; call it directly if
        you prefer the mapping to be an explicit step, or want to pair it with
        `unmapImageData()` yourself.

        The buffer is mapped for both reading and writing, and presented as an
        array which is a view onto that memory rather than a copy. Calling this
        again while the buffer is already mapped hands back the same array, it
        doesn't map it a second time.

        Returns
        -------
        numpy.ndarray or None
            Texture data of shape `[H, W, C]`, in whatever data type and number
            of channels the texture was created with. `None` if the stimulus
            has no texture of its own to map, i.e. before an image has been
            set, or when the image is another object's texture (such as a movie
            or camera frame).

        Raises
        ------
        RuntimeError
            If the driver refused to map the buffer.

        See Also
        --------
        imageData : Property giving the same array.
        unmapImageData : Release the mapping and update the texture.

        """
        if self._imageDataArray is not None:  # already mapped, hand it back
            return self._imageDataArray

        if self._texBufferShape is None:  # no storage of ours to map
            return None

        self._selectWindow(self.win)

        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffID)

        # First time this texture's buffer is mapped, so it still needs sizing
        # and filling. `_createTexture()` leaves this until now rather than
        # uploading every image twice on the off-chance it gets mapped.
        #
        # The pixels come back out of the texture rather than from a copy kept
        # on our side, which costs nothing until someone maps the buffer and
        # reflects any change made to the texture since it was created.
        if self._texBufferNeedsFill:
            GL.glBufferData(
                GL.GL_PIXEL_UNPACK_BUFFER,
                self._texBufferNBytes,
                None,
                GL.GL_DYNAMIC_DRAW)
            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

            # Read the texture into the buffer. It is bound as the pack target
            # for this, which is where `glGetTexImage` writes to, then put back
            # on the unpack target for mapping and for uploading later.
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, self._pixbuffID)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            # Rows are tightly packed, unlike the default alignment of 4 which
            # would skew the image for most widths.
            GL.glPixelStorei(GL.GL_PACK_ALIGNMENT, 1)
            GL.glGetTexImage(
                GL.GL_TEXTURE_2D, 0,
                self._texBufferPixFormat,
                self._texBufferDataType,
                0)  # write into the bound pixel buffer
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glBindBuffer(GL.GL_PIXEL_PACK_BUFFER, 0)

            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffID)
            self._texBufferNeedsFill = False

        # Map the buffer into client memory. `GL_READ_WRITE` since the caller
        # may want to read the present pixel values as well as replace them.
        bufferPtr = GL.glMapBuffer(
            GL.GL_PIXEL_UNPACK_BUFFER, GL.GL_READ_WRITE)
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        if not bufferPtr:
            # The driver refused the mapping, which can happen if the context
            # has been lost. Building an array over the null pointer it hands
            # back in that case would take the whole process down on first use.
            raise RuntimeError(
                "Failed to map the pixel buffer holding the texture data for "
                "`{}`.".format(self.name))

        # Present those bytes as an array without copying them.
        ptrType = ctypes.POINTER(
            numpy.ctypeslib.as_ctypes_type(self._texBufferDType))
        self._imageDataPtr = bufferPtr
        self._imageDataArray = numpy.ctypeslib.as_array(
            ctypes.cast(bufferPtr, ptrType), shape=self._texBufferShape)

        return self._imageDataArray

    @property
    def imageData(self):
        """Texture memory as an array (`numpy.ndarray` or `None`).

        Accessing this maps the pixel buffer backing the stimulus' texture into
        the application's address space and presents it as an array of shape
        `[H, W, C]`. The array is a view onto that memory rather than a copy, so
        writing to it writes to the texture's storage directly, without
        allocating or copying a frame's worth of pixels::

            stim = visual.ImageStim(win, 'face.png')
            stim.imageData[:, :, 0] = 0  # drop the red channel
            stim.draw()

        The data type and the number of channels are whatever the texture was
        created with, which depends on the image the stimulus was given. Check
        `.dtype` and `.shape` rather than assuming them. Row 0 is the bottom of
        the image, as in OpenGL, not the top.

        Edits are transferred to the texture on the next call to `draw()`, or
        immediately if `unmapImageData()` is called. **The array is only valid
        until then** -- it points at memory the driver hands back once the
        mapping is released, so keep the edits and the draw together and fetch
        the array again afterwards rather than holding on to it.

        Is `None` when the stimulus has no texture of its own to map, i.e.
        before an image has been set, or when the image is another object's
        texture (such as a movie or camera frame).

        See Also
        --------
        mapImageData : The method this defers to, same value.
        unmapImageData : Release the mapping and update the texture.

        """
        return self.mapImageData()

    @imageData.setter
    def imageData(self, value):
        imageData = self.imageData
        if imageData is None:
            raise AttributeError(
                "Cannot set `imageData` for `{}`, it has no texture of its own "
                "to write to. Set `image` first.".format(self.name))

        imageData[:] = value  # numpy checks the shape and type for us
        self.unmapImageData()

    def unmapImageData(self):
        """Release the mapping held by `imageData` and update the texture.

        Any edits made through the `imageData` array are transferred to the
        texture, and the array becomes invalid. You don't usually need to call
        this, since `draw()` does it for you; use it when you want the texture
        updated at a particular point instead.

        Returns
        -------
        bool
            `True` if a mapping was released and the texture updated. `False`
            if there was nothing mapped, or if the buffer's contents were lost
            while it was mapped (which the driver may do if the display mode
            changes) and so could not be used.

        See Also
        --------
        mapImageData : Map the buffer and get the array back.

        """
        return self._unmapImageData()

    def _unmapImageData(self, upload=True):
        """Release the mapping held by `imageData`.

        Parameters
        ----------
        upload : bool
            Transfer the buffer's contents to the texture afterwards. Pass
            `False` when the texture the buffer belongs to is being replaced or
            deleted, making the transfer pointless.

        Returns
        -------
        bool
            `True` if a mapping was released and, where requested, the texture
            updated.

        """
        # `getattr` since this is reachable from `__del__` by way of
        # `clearTextures()`, potentially on a part-initialised stimulus.
        if getattr(self, '_imageDataArray', None) is None:  # nothing mapped
            return False

        # Drop our references first, so that a failure below still leaves the
        # stimulus thinking the (now unusable) mapping is gone. Marking the
        # array read-only as we go is a small courtesy to anyone still holding
        # it, since writing to it after this point writes to memory the driver
        # has taken back.
        self._imageDataArray.flags.writeable = False
        self._imageDataArray = None
        self._imageDataPtr = None

        self._selectWindow(self.win)

        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixbuffID)
        # A false return means the driver discarded the buffer's contents while
        # it was mapped, in which case there is nothing worth uploading.
        dataIntact = bool(GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER))

        if not dataIntact:
            logging.warning(
                "Contents of the pixel buffer holding the texture data for "
                "`{}` were lost while it was mapped, the edits made to "
                "`imageData` have been discarded.".format(self.name))

        if upload and dataIntact and self._texBufferShape is not None:
            height, width = self._texBufferShape[:2]
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            # Rows are tightly packed, unlike the default alignment of 4 which
            # would skew the image for most widths.
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            GL.glTexSubImage2D(
                GL.GL_TEXTURE_2D, 0, 0, 0,
                width, height,
                self._texBufferPixFormat,
                self._texBufferDataType,
                0)  # read from the bound pixel buffer
            # no mipmaps, see the note in `TextureMixin._createTexture()`
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        return dataIntact

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
