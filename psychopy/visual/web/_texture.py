#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A texture frames are streamed to, as `MovieStim` streams video frames (see
its `_setupTextureBuffers` and `_pixelTransfer`).
"""

import ctypes

import psychopy.tools.pygletgl as GL

__all__ = ['StreamingTexture']

# OpenGL formats to upload frames in, by `_protocol.FORMATS` name, matching how
# their bytes are ordered so the driver can copy them as they are
_GL_FORMATS_ = {
    'rgba_pm': (GL.GL_RGBA, GL.GL_UNSIGNED_BYTE),
    'bgra_pm': (GL.GL_BGRA, GL.GL_UNSIGNED_INT_8_8_8_8_REV)
}


class StreamingTexture:
    """An RGBA texture which frames are copied into through a pixel buffer.

    Make, use and delete it on the thread of the window's OpenGL context, with
    the context current.

    Parameters
    ----------
    width, height : int
        Size of the frames in pixels.
    fmt : str
        Pixel format of the frames, `'rgba_pm'` or `'bgra_pm'`.
    interpolate : bool
        Whether to interpolate linearly when scaling the texture.

    """
    def __init__(self, width, height, fmt, interpolate=True):
        self.width = int(width)
        self.height = int(height)
        self.fmt = fmt
        self._glFormat, self._glType = _GL_FORMATS_[fmt]
        self._nBytes = self.width * self.height * 4
        self._interpolate = bool(interpolate)
        self._filterNeedsUpdate = False

        self.textureId = GL.GLuint()
        self._bufferId = GL.GLuint()
        GL.glGenBuffers(1, ctypes.byref(self._bufferId))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._bufferId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER, self._nBytes, None, GL.GL_STREAM_DRAW)
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        GL.glGenTextures(1, ctypes.byref(self.textureId))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureId)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, self.width, self.height, 0,
            self._glFormat, self._glType, None)
        self._applyFilter()
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def matches(self, width, height, fmt):
        """Whether frames of a size and format can be uploaded to this."""
        return (self.width, self.height, self.fmt) == (width, height, fmt)

    @property
    def interpolate(self):
        """Whether to interpolate linearly when scaling the texture (`bool`),
        applied when next bound."""
        return self._interpolate

    @interpolate.setter
    def interpolate(self, value):
        value = bool(value)
        if value != self._interpolate:
            self._interpolate = value
            self._filterNeedsUpdate = True

    def _applyFilter(self):
        texFilter = GL.GL_LINEAR if self._interpolate else GL.GL_NEAREST
        for param in (GL.GL_TEXTURE_MAG_FILTER, GL.GL_TEXTURE_MIN_FILTER):
            GL.glTexParameteri(GL.GL_TEXTURE_2D, param, texFilter)
        self._filterNeedsUpdate = False

    def upload(self, address, stride):
        """Copy a frame into the texture.

        Parameters
        ----------
        address : int
            Memory address of the frame's first byte.
        stride : int
            Bytes per row of the frame, at least `width * 4`.

        """
        nBytes = stride * self.height
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._bufferId)
        # orphan the last frame's storage, so the GPU can keep reading it
        # without the copy below waiting for it to finish
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER, nBytes, None, GL.GL_STREAM_DRAW)
        bufferPtr = GL.glMapBuffer(GL.GL_PIXEL_UNPACK_BUFFER, GL.GL_WRITE_ONLY)
        if not bufferPtr:
            GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
            raise RuntimeError("Couldn't map the pixel buffer for a frame")
        ctypes.memmove(bufferPtr, address, nBytes)
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureId)
        GL.glPushClientAttrib(GL.GL_CLIENT_PIXEL_STORE_BIT)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 4)
        GL.glPixelStorei(GL.GL_UNPACK_ROW_LENGTH, stride // 4)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
            self._glFormat, self._glType, 0)  # from the bound buffer
        GL.glPopClientAttrib()
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def bind(self):
        """Bind the texture to the active texture unit."""
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.textureId)
        if self._filterNeedsUpdate:
            self._applyFilter()

    def delete(self):
        """Delete the texture and pixel buffer."""
        try:
            if self._bufferId.value:
                GL.glDeleteBuffers(1, self._bufferId)
            if self.textureId.value:
                GL.glDeleteTextures(1, self.textureId)
        except Exception:  # e.g. the context has gone at exit
            pass
        self._bufferId = GL.GLuint()
        self.textureId = GL.GLuint()
