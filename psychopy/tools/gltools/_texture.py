#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with OpenGL textures.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'TexImage2DInfo',
    'TexImage2DMultisampleInfo',
    'createTexImage2D',
    'createTexImage2DMultisample',
    'deleteTexture',
    'createTexImage2dFromFile',
    'bindTexture',
    'unbindTexture',
    'createCubeMap',
    'TexCubeMapInfo'
]

import ctypes

import numpy as np
from PIL import Image
import pyglet.gl as GL  # using Pyglet for now

from ._misc import maxSamples


# -----------------
# Texture Functions
# -----------------

# 2D texture descriptor. You can 'wrap' existing texture IDs with TexImage2D to
# use them with functions that require that type as input.
#

class TexImage2DInfo(object):
    """Descriptor for a 2D texture.

    This class is used for bookkeeping 2D textures stored in video memory.
    Information about the texture (eg. `width` and `height`) is available via
    class attributes. Attributes should never be modified directly.

    """
    __slots__ = ['width',
                 'height',
                 'target',
                 '_name',
                 'level',
                 'internalFormat',
                 'pixelFormat',
                 'dataType',
                 'unpackAlignment',
                 '_texParams',
                 '_isBound',
                 '_unit',
                 '_texParamsNeedUpdate']

    def __init__(self,
                 name=0,
                 target=GL.GL_TEXTURE_2D,
                 width=64,
                 height=64,
                 level=0,
                 internalFormat=GL.GL_RGBA,
                 pixelFormat=GL.GL_RGBA,
                 dataType=GL.GL_FLOAT,
                 unpackAlignment=4,
                 texParams=None):
        """
        Parameters
        ----------
        name : `int` or `GLuint`
            OpenGL handle for texture. Is `0` if uninitialized.
        target : :obj:`int`
            The target texture should only be either GL_TEXTURE_2D or
            GL_TEXTURE_RECTANGLE.
        width : :obj:`int`
            Texture width in pixels.
        height : :obj:`int`
            Texture height in pixels.
        level : :obj:`int`
            LOD number of the texture, should be 0 if GL_TEXTURE_RECTANGLE is
            the target.
        internalFormat : :obj:`int`
            Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
        pixelFormat : :obj:`int`
            Pixel data format (e.g. GL_RGBA, GL_DEPTH_STENCIL)
        dataType : :obj:`int`
            Data type for pixel data (e.g. GL_FLOAT, GL_UNSIGNED_BYTE).
        unpackAlignment : :obj:`int`
            Alignment requirements of each row in memory. Default is 4.
        texParams : :obj:`list` of :obj:`tuple` of :obj:`int`
            Optional texture parameters specified as `dict`. These values are
            passed to `glTexParameteri`. Each tuple must contain a parameter
            name and value. For example, `texParameters={
            GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR, GL.GL_TEXTURE_MAG_FILTER:
            GL.GL_LINEAR}`. These can be changed and will be updated the next
            time this instance is passed to :func:`bindTexture`.

        """
        # fields for texture information
        self.name = name
        self.width = width
        self.height = height
        self.target = target
        self.level = level
        self.internalFormat = internalFormat
        self.pixelFormat = pixelFormat
        self.dataType = dataType
        self.unpackAlignment = unpackAlignment
        self._texParams = {}

        # set texture parameters
        if texParams is not None:
            for key, val in texParams.items():
                self._texParams[key] = val

        # internal data
        self._isBound = False  # True if the texture has been bound
        self._unit = None  # texture unit assigned to this texture
        self._texParamsNeedUpdate = True  # update texture parameters

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, GL.GLuint):
            self._name = GL.GLuint(int(value))
        else:
            self._name = value

    @property
    def size(self):
        """Size of the texture [w, h] in pixels (`int`, `int`)."""
        return self.width, self.height

    @property
    def texParams(self):
        """Texture parameters."""
        self._texParamsNeedUpdate = True
        return self._texParams

    @texParams.setter
    def texParams(self, value):
        """Texture parameters."""
        self._texParamsNeedUpdate = True
        self._texParams = value

    def __del__(self):
        """Deletes the texture when there are no more references to it."""
        try:
            GL.glDeleteTextures(1, self.name)
        except ValueError:
            pass


def createTexImage2D(width, height, target=GL.GL_TEXTURE_2D, level=0,
                     internalFormat=GL.GL_RGBA8, pixelFormat=GL.GL_RGBA,
                     dataType=GL.GL_FLOAT, data=None, unpackAlignment=4,
                     texParams=None):
    """Create a 2D texture in video memory. This can only create a single 2D
    texture with targets `GL_TEXTURE_2D` or `GL_TEXTURE_RECTANGLE`.

    Parameters
    ----------
    width : :obj:`int`
        Texture width in pixels.
    height : :obj:`int`
        Texture height in pixels.
    target : :obj:`int`
        The target texture should only be either `GL_TEXTURE_2D` or
        `GL_TEXTURE_RECTANGLE`.
    level : :obj:`int`
        LOD number of the texture, should be 0 if GL_TEXTURE_RECTANGLE is the
        target.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. `GL_RGBA8`, `GL_R11F_G11F_B10F`).
    pixelFormat : :obj:`int`
        Pixel data format (e.g. `GL_RGBA`, `GL_DEPTH_STENCIL`)
    dataType : :obj:`int`
        Data type for pixel data (e.g. `GL_FLOAT`, `GL_UNSIGNED_BYTE`).
    data : :obj:`ctypes` or :obj:`None`
        Ctypes pointer to image data. If None is specified, the texture will be
        created but pixel data will be uninitialized.
    unpackAlignment : :obj:`int`
        Alignment requirements of each row in memory. Default is 4.
    texParams : :obj:`dict`
        Optional texture parameters specified as `dict`. These values are passed
        to `glTexParameteri`. Each tuple must contain a parameter name and
        value. For example, `texParameters={GL.GL_TEXTURE_MIN_FILTER:
        GL.GL_LINEAR, GL.GL_TEXTURE_MAG_FILTER: GL.GL_LINEAR}`.

    Returns
    -------
    TexImage2DInfo
        A `TexImage2DInfo` descriptor.

    Notes
    -----
    The 'userData' field of the returned descriptor is a dictionary that can
    be used to store arbitrary data associated with the texture.

    Previous textures are unbound after calling :func:`createTexImage2D`.

    Examples
    --------
    Creating a texture from an image file::

        import pyglet.gl as GL  # using Pyglet for now

        # empty texture
        textureDesc = createTexImage2D(1024, 1024, internalFormat=GL.GL_RGBA8)

        # load texture data from an image file using Pillow and NumPy
        from PIL import Image
        import numpy as np
        im = Image.open(imageFile)  # 8bpp!
        im = im.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL origin is at bottom
        im = im.convert("RGBA")
        pixelData = np.array(im).ctypes  # convert to ctypes!

        width = pixelData.shape[1]
        height = pixelData.shape[0]
        textureDesc = gltools.createTexImage2D(
            width,
            height,
            internalFormat=GL.GL_RGBA,
            pixelFormat=GL.GL_RGBA,
            dataType=GL.GL_UNSIGNED_BYTE,
            data=pixelData,
            unpackAlignment=1,
            texParameters=[(GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR),
                           (GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)])

        GL.glBindTexture(GL.GL_TEXTURE_2D, textureDesc.id)

    Notes
    -----
    * Texture 0 is bound after creating the texture.

    """
    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("Invalid image dimensions {} x {}.".format(
            width, height))

    if target == GL.GL_TEXTURE_RECTANGLE:
        if level != 0:
            raise ValueError("Invalid level for target GL_TEXTURE_RECTANGLE, "
                             "must be 0.")
        GL.glEnable(GL.GL_TEXTURE_RECTANGLE)

    texId = GL.GLuint()
    GL.glGenTextures(1, ctypes.byref(texId))

    GL.glBindTexture(target, texId)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, int(unpackAlignment))
    GL.glTexImage2D(target, level, internalFormat,
                    width, height, 0,
                    pixelFormat, dataType, data)

    # apply texture parameters
    if texParams is not None:
        for pname, param in texParams.items():
            GL.glTexParameteri(target, pname, param)

    # new texture descriptor
    tex = TexImage2DInfo(name=texId,
                         target=target,
                         width=width,
                         height=height,
                         internalFormat=internalFormat,
                         level=level,
                         pixelFormat=pixelFormat,
                         dataType=dataType,
                         unpackAlignment=unpackAlignment,
                         texParams=texParams)

    tex._texParamsNeedUpdate = False

    GL.glBindTexture(target, 0)

    return tex


def createTexImage2dFromFile(imgFile, transpose=True):
    """Load an image from file directly into a texture.

    This is a convenience function to quickly get an image file loaded into a
    2D texture. The image is converted to RGBA format. Texture parameters are
    set for linear interpolation.

    Parameters
    ----------
    imgFile : str
        Path to the image file.
    transpose : bool
        Flip the image so it appears upright when displayed in OpenGL image
        coordinates.

    Returns
    -------
    TexImage2DInfo
        Texture descriptor.

    Notes
    -----
    * Texture 0 is bound after creating the texture.

    """
    im = Image.open(imgFile)  # 8bpp!
    if transpose:
        im = im.transpose(Image.FLIP_TOP_BOTTOM)  # OpenGL origin is at bottom

    im = im.convert("RGBA")
    pixelData = np.array(im).ctypes  # convert to ctypes!

    width = pixelData.shape[1]
    height = pixelData.shape[0]
    textureDesc = createTexImage2D(
        width,
        height,
        internalFormat=GL.GL_RGBA,
        pixelFormat=GL.GL_RGBA,
        dataType=GL.GL_UNSIGNED_BYTE,
        data=pixelData,
        unpackAlignment=1,
        texParams={GL.GL_TEXTURE_MAG_FILTER: GL.GL_LINEAR,
                   GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR})

    return textureDesc


class TexCubeMapInfo(object):
    """Descriptor for a cube map texture..

    This class is used for bookkeeping cube maps stored in video memory.
    Information about the texture (eg. `width` and `height`) is available via
    class attributes. Attributes should never be modified directly.

    """
    __slots__ = ['width',
                 'height',
                 'target',
                 '_name',
                 'level',
                 'internalFormat',
                 'pixelFormat',
                 'dataType',
                 'unpackAlignment',
                 '_texParams',
                 '_isBound',
                 '_unit',
                 '_texParamsNeedUpdate']

    def __init__(self,
                 name=0,
                 target=GL.GL_TEXTURE_CUBE_MAP,
                 width=64,
                 height=64,
                 level=0,
                 internalFormat=GL.GL_RGBA,
                 pixelFormat=GL.GL_RGBA,
                 dataType=GL.GL_FLOAT,
                 unpackAlignment=4,
                 texParams=None):
        """
        Parameters
        ----------
        name : `int` or `GLuint`
            OpenGL handle for texture. Is `0` if uninitialized.
        target : :obj:`int`
            The target texture should only be `GL_TEXTURE_CUBE_MAP`.
        width : :obj:`int`
            Texture width in pixels.
        height : :obj:`int`
            Texture height in pixels.
        level : :obj:`int`
            LOD number of the texture.
        internalFormat : :obj:`int`
            Internal format for texture data (e.g. `GL_RGBA8`,
            `GL_R11F_G11F_B10F`).
        pixelFormat : :obj:`int`
            Pixel data format (e.g. `GL_RGBA`, `GL_DEPTH_STENCIL`)
        dataType : :obj:`int`
            Data type for pixel data (e.g. `GL_FLOAT`, `GL_UNSIGNED_BYTE`).
        unpackAlignment : :obj:`int`
            Alignment requirements of each row in memory. Default is 4.
        texParams : :obj:`list` of :obj:`tuple` of :obj:`int`
            Optional texture parameters specified as `dict`. These values are
            passed to `glTexParameteri`. Each tuple must contain a parameter
            name and value. For example, `texParameters={
            GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR, GL.GL_TEXTURE_MAG_FILTER:
            GL.GL_LINEAR}`. These can be changed and will be updated the next
            time this instance is passed to :func:`bindTexture`.

        """
        # fields for texture information
        self.name = name
        self.width = width
        self.height = height
        self.target = target
        self.level = level
        self.internalFormat = internalFormat
        self.pixelFormat = pixelFormat
        self.dataType = dataType
        self.unpackAlignment = unpackAlignment
        self._texParams = {}

        # set texture parameters
        if texParams is not None:
            for key, val in texParams.items():
                self._texParams[key] = val

        # internal data
        self._isBound = False  # True if the texture has been bound
        self._unit = None  # texture unit assigned to this texture
        self._texParamsNeedUpdate = True  # update texture parameters

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, GL.GLuint):
            self._name = GL.GLuint(int(value))
        else:
            self._name = value

    @property
    def size(self):
        """Size of a single cubemap face [w, h] in pixels (`int`, `int`)."""
        return self.width, self.height

    @property
    def texParams(self):
        """Texture parameters."""
        self._texParamsNeedUpdate = True
        return self._texParams

    @texParams.setter
    def texParams(self, value):
        """Texture parameters."""
        self._texParamsNeedUpdate = True
        self._texParams = value

    @property
    def samples(self):
        """Number of samples per-pixel for this texture. Always returns 1."""
        return 1

    @property
    def isMultisample(self):
        """Is this texture multisample? This always returns `False` but allows
        you to check this property instead of using `isInstance`.
        """
        return False


def createCubeMap(width, height, target=GL.GL_TEXTURE_CUBE_MAP, level=0,
                  internalFormat=GL.GL_RGBA, pixelFormat=GL.GL_RGBA,
                  dataType=GL.GL_UNSIGNED_BYTE, data=None, unpackAlignment=4,
                  texParams=None):
    """Create a cubemap.

    Parameters
    ----------
    name : `int` or `GLuint`
        OpenGL handle for the cube map. Is `0` if uninitialized.
    target : :obj:`int`
        The target texture should only be `GL_TEXTURE_CUBE_MAP`.
    width : :obj:`int`
        Texture width in pixels for each face.
    height : :obj:`int`
        Texture height in pixels for each face.
    level : :obj:`int`
        LOD number of the texture.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. `GL_RGBA8`, `GL_R11F_G11F_B10F`).
    pixelFormat : :obj:`int`
        Pixel data format (e.g. `GL_RGBA`, `GL_DEPTH_STENCIL`)
    dataType : :obj:`int`
        Data type for pixel data (e.g. `GL_FLOAT`, `GL_UNSIGNED_BYTE`).
    data : list or tuple
        List of six ctypes pointers to image data for each cubemap face. Image
        data is assigned to a face by index [+X, -X, +Y, -Y, +Z, -Z]. All images
        must have the same size as specified by `width` and `height`.
    unpackAlignment : :obj:`int`
        Alignment requirements of each row in memory. Default is 4.
    texParams : :obj:`list` of :obj:`tuple` of :obj:`int`
        Optional texture parameters specified as `dict`. These values are
        passed to `glTexParameteri`. Each tuple must contain a parameter
        name and value. For example, `texParameters={
        GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR, GL.GL_TEXTURE_MAG_FILTER:
        GL.GL_LINEAR}`. These can be changed and will be updated the next
        time this instance is passed to :func:`bindTexture`.

    Notes
    -----
    * Texture 0 is bound after creating the texture.

    """
    texId = GL.GLuint()
    GL.glGenTextures(1, ctypes.byref(texId))
    GL.glBindTexture(target, texId)

    # create faces of the cube map
    for face in range(6):
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, int(unpackAlignment))
        GL.glTexImage2D(GL.GL_TEXTURE_CUBE_MAP_POSITIVE_X + face, level,
                        internalFormat, width, height, 0, pixelFormat, dataType,
                        data[face] if data is not None else data)

    # apply texture parameters
    if texParams is not None:
        for pname, param in texParams.items():
            GL.glTexParameteri(target, pname, param)

    GL.glBindTexture(target, 0)

    tex = TexCubeMapInfo(name=texId,
                         target=target,
                         width=width,
                         height=height,
                         internalFormat=internalFormat,
                         level=level,
                         pixelFormat=pixelFormat,
                         dataType=dataType,
                         unpackAlignment=unpackAlignment,
                         texParams=texParams)

    return tex


def bindTexture(texture, unit=None, enable=True):
    """Bind a texture.

    Function binds `texture` to `unit` (if specified). If `unit` is `None`, the
    texture will be bound but not assigned to a texture unit.

    Parameters
    ----------
    texture : TexImage2DInfo
        Texture descriptor to bind.
    unit : int, optional
        Texture unit to associated the texture with.
    enable : bool
        Enable textures upon binding.

    """
    if not texture._isBound:
        if enable:
            GL.glEnable(texture.target)

        GL.glBindTexture(texture.target, texture.name)
        texture._isBound = True

        if unit is not None:
            texture._unit = unit
            GL.glActiveTexture(GL.GL_TEXTURE0 + unit)

        # update texture parameters if they have been accessed (changed?)
        if texture._texParamsNeedUpdate:
            for pname, param in texture._texParams.items():
                GL.glTexParameteri(texture.target, pname, param)
                texture._texParamsNeedUpdate = False


def unbindTexture(texture=None):
    """Unbind a texture.

    Parameters
    ----------
    texture : TexImage2DInfo
        Texture descriptor to unbind.

    """
    if texture._isBound:
        # set the texture unit
        if texture._unit is not None:
            GL.glActiveTexture(GL.GL_TEXTURE0 + texture._unit)
            texture._unit = None

        GL.glBindTexture(texture.target, 0)
        texture._isBound = False

        GL.glDisable(texture.target)
    else:
        raise RuntimeError('Trying to unbind a texture that was not previously'
                           'bound.')


class TexImage2DMultisampleInfo(object):
    """Descriptor for a multisampled 2D texture.

    This class is used for bookkeeping 2D textures stored in video memory.
    Information about the texture (eg. `width` and `height`) is available via
    class attributes. Attributes should never be modified directly.

    """
    __slots__ = ['width',
                 'height',
                 'target',
                 '_name',
                 'internalFormat',
                 '_samples',
                 'multisample',
                 '_texParams',
                 '_isBound',
                 '_unit',
                 '_texParamsNeedUpdate']

    def __init__(self,
                 name=0,
                 target=GL.GL_TEXTURE_2D,
                 width=64,
                 height=64,
                 samples=2,
                 internalFormat=GL.GL_RGBA,
                 texParams=None):
        """
        Parameters
        ----------
        name : `int` or `GLuint`
            OpenGL handle for texture. Is `0` if uninitialized.
        target : :obj:`int`
            The target texture should only be `GL_TEXTURE_2D_MULTISAMPLE`.
        width : :obj:`int`
            Texture width in pixels.
        height : :obj:`int`
            Texture height in pixels.
        samples : :obj:`int`
            Number of samples for the texture per-pixel. This should be a
            power-of-two (eg. 2, 4, 8, 16, etc.) Number of samples is limited
            by the graphics hardware.
        internalFormat : :obj:`int`
            Internal format for texture data (e.g. `GL_RGBA8`,
            `GL_R11F_G11F_B10F`).
        texParams : :obj:`list` of :obj:`tuple` of :obj:`int`
            Optional texture parameters specified as `dict`. These values are
            passed to `glTexParameteri`. Each tuple must contain a parameter
            name and value. For example, `texParameters={
            GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR, GL.GL_TEXTURE_MAG_FILTER:
            GL.GL_LINEAR}`. These can be changed and will be updated the next
            time this instance is passed to :func:`bindTexture`.

        """
        # fields for texture information
        self.name = name
        self.width = width
        self.height = height
        self.target = target
        self._samples = samples
        self.internalFormat = internalFormat
        self._texParams = {}

        # set texture parameters
        if texParams is not None:
            for key, val in texParams.items():
                self._texParams[key] = val

        # internal data
        self._isBound = False  # True if the texture has been bound
        self._unit = None  # texture unit assigned to this texture
        self._texParamsNeedUpdate = True  # update texture parameters

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, GL.GLuint):
            self._name = GL.GLuint(int(value))
        else:
            self._name = value

    @property
    def size(self):
        """Size of the texture [w, h] in pixels (`int`, `int`)."""
        return self.width, self.height

    @property
    def texParams(self):
        """Texture parameters."""
        self._texParamsNeedUpdate = True
        return self._texParams

    @texParams.setter
    def texParams(self, value):
        """Texture parameters."""
        self._texParamsNeedUpdate = True
        self._texParams = value

    @property
    def samples(self):
        """Number of samples per-pixel for this texture."""
        return self._samples

    @property
    def isMultisample(self):
        """Is this texture multisample, always returns `True`."""
        return True

    def __del__(self):
        """Deletes the texture when there are no more references to it."""
        GL.glDeleteTextures(1, self.name)


def createTexImage2DMultisample(width, height,
                                target=GL.GL_TEXTURE_2D_MULTISAMPLE, samples=1,
                                internalFormat=GL.GL_RGBA8, texParameters=None):
    """Create a 2D multisampled texture.

    Parameters
    ----------
    width : :obj:`int`
        Texture width in pixels.
    height : :obj:`int`
        Texture height in pixels.
    target : :obj:`int`
        The target texture (e.g. `GL_TEXTURE_2D_MULTISAMPLE`).
    samples : :obj:`int`
        Number of samples for multi-sampling, should be >1 and power-of-two.
        Work with one sample, but will raise a warning.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. `GL_RGBA8`, `GL_R11F_G11F_B10F`).
    texParameters : :obj:`list` of :obj:`tuple` of :obj:`int`
        Optional texture parameters specified as a list of tuples. These values
        are passed to 'glTexParameteri'. Each tuple must contain a parameter
        name and value. For example, texParameters=[(GL.GL_TEXTURE_MIN_FILTER,
        GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)]

    Returns
    -------
    TexImage2DMultisampleInfo
        A `TexImage2DMultisampleInfo` descriptor.

    Notes
    -----
    * Texture 0 is bound after creating the texture.

    """
    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("Invalid image dimensions {} x {}.".format(
            width, height))

    # determine if the 'samples' value is valid
    maximum = maxSamples()
    if (samples & (samples - 1)) != 0:
        raise ValueError('Invalid number of samples, must be power-of-two.')
    elif samples <= 0 or samples > maximum:
        raise ValueError('Invalid number of samples, must be <{}.'.format(
            maximum))

    colorTexId = GL.GLuint()
    GL.glGenTextures(1, ctypes.byref(colorTexId))
    GL.glBindTexture(target, colorTexId)
    GL.glTexImage2DMultisample(
        target, samples, internalFormat, width, height, GL.GL_TRUE)

    texParameters = dict() if texParameters is None else texParameters

    # apply texture parameters
    if texParameters:
        for pname, param in texParameters.items():
            GL.glTexParameteri(target, pname, param)

    GL.glBindTexture(target, 0)

    return TexImage2DMultisampleInfo(colorTexId,
                                     target,
                                     width,
                                     height,
                                     samples,
                                     internalFormat,
                                     dict())


def deleteTexture(texture):
    """Free the resources associated with a texture. This invalidates the
    texture's ID.

    """
    if not isinstance(texture, (TexImage2DInfo, TexImage2DMultisampleInfo)):
        raise TypeError("Object specified to `texture` is not a texture.")

    if not texture._isBound:
        GL.glDeleteTextures(1, texture.name)
        texture.name = 0  # invalidate
    else:
        raise RuntimeError("Attempting to delete texture which is presently "
                           "bound.")


if __name__ == "__main__":
    pass
