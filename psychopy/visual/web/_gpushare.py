#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Frame slots in GPU memory shared by the web browser server and stimulus.

The server allocates each slot's memory, and two semaphores per slot, with
Vulkan (see `_vkshare`) and both processes import them into OpenGL as
textures, so frames are passed without copying them through the CPU. Who may
use a slot follows the same messages as frames in shared memory (`frame` and
`release`, see `_protocol`), and the semaphores order the GPU's work to match:

* the server renders into a slot, signals its *ready* semaphore and sends
  `frame`; the stimulus waits on *ready* before drawing it;
* the stimulus signals the slot's *done* semaphore once it no longer draws it
  and sends `release`; the server waits on *done* before rendering into it
  again.

Each side only waits on a semaphore after the message saying the other side
has signalled it (and flushed), as waiting on one nobody signals stalls the
GPU.

A new set of slots is first checked: the server fills each with a color, and
the stimulus reads them back, so a driver that can't share memory this way is
found before any frame is lost, and the stimulus falls back to frames in
shared memory.

This module only uses the standard library, as the server imports it without
importing PsychoPy.
"""

import ctypes
import os

try:
    import _glext as G  # imported by the server, as a script
except ImportError:
    from . import _glext as G

__all__ = ['GPUShareError', 'GLSlots', 'checkColor']

# the semaphores carry no layout transitions between APIs (only OpenGL uses
# the textures), so the general layout is used throughout
_LAYOUT = G.GL_LAYOUT_GENERAL_EXT


class GPUShareError(RuntimeError):
    """Frames can't be shared on the GPU."""


def checkColor(slot):
    """Color (RGBA bytes) a slot is filled with to check it was shared."""
    return (40 + 70 * slot) % 256, 200 - 50 * slot, 90 + slot, 255


class GLSlots:
    """Shared frame slots, imported into the current OpenGL context.

    Make, use and delete it with that context (or one sharing its objects)
    current.

    Parameters
    ----------
    gl : _glext.GLFunctions
        OpenGL functions of the context.
    width, height : int
        Size of the frames in pixels.
    memSize : int
        Size of each slot's memory in bytes.
    memFds, readyFds, doneFds : list of int
        File descriptors of each slot's memory and semaphores. Importing them
        hands them over to OpenGL, so the caller mustn't close them, even if
        this raises.
    interpolate : bool
        Whether to interpolate linearly when drawing the textures scaled.

    Raises
    ------
    GPUShareError
        If importing them fails.

    """
    def __init__(self, gl, width, height, memSize, memFds, readyFds, doneFds,
                 interpolate=True):
        self.gl = gl
        self.width = int(width)
        self.height = int(height)
        self.nSlots = len(memFds)
        n = self.nSlots
        self.memories = (ctypes.c_uint * n)()
        self.textures = (ctypes.c_uint * n)()
        self.ready = (ctypes.c_uint * n)()
        self.done = (ctypes.c_uint * n)()
        self._framebuffers = None
        self._interpolate = bool(interpolate)
        self._filterNeedsUpdate = False
        gl.clearErrors()
        try:
            gl.glCreateMemoryObjectsEXT(n, self.memories)
            dedicated = ctypes.c_int(1)
            for i in range(n):
                gl.glMemoryObjectParameterivEXT(
                    self.memories[i], G.GL_DEDICATED_MEMORY_OBJECT_EXT,
                    ctypes.byref(dedicated))
                gl.glImportMemoryFdEXT(self.memories[i], int(memSize),
                                       G.GL_HANDLE_TYPE_OPAQUE_FD_EXT,
                                       memFds[i])
            gl.glGenTextures(n, self.textures)
            for i in range(n):
                gl.glBindTexture(G.GL_TEXTURE_2D, self.textures[i])
                gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_TILING_EXT,
                                   G.GL_OPTIMAL_TILING_EXT)
                gl.glTexStorageMem2DEXT(
                    G.GL_TEXTURE_2D, 1, G.GL_RGBA8, self.width, self.height,
                    self.memories[i], 0)
                self._applyFilter()
                gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_WRAP_S,
                                   G.GL_CLAMP_TO_EDGE)
                gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_WRAP_T,
                                   G.GL_CLAMP_TO_EDGE)
            gl.glBindTexture(G.GL_TEXTURE_2D, 0)
            gl.glGenSemaphoresEXT(n, self.ready)
            gl.glGenSemaphoresEXT(n, self.done)
            for i in range(n):
                gl.glImportSemaphoreFdEXT(
                    self.ready[i], G.GL_HANDLE_TYPE_OPAQUE_FD_EXT, readyFds[i])
                gl.glImportSemaphoreFdEXT(
                    self.done[i], G.GL_HANDLE_TYPE_OPAQUE_FD_EXT, doneFds[i])
        except AttributeError as err:  # a function the driver doesn't have
            self.delete()
            raise GPUShareError(str(err))
        errors = gl.clearErrors()
        if errors:
            self.delete()
            raise GPUShareError("Importing shared frames failed (OpenGL "
                                "errors {})".format([hex(e) for e in errors]))

    def _applyFilter(self):
        texFilter = G.GL_LINEAR if self._interpolate else G.GL_NEAREST
        self.gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_MAG_FILTER,
                                texFilter)
        self.gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_MIN_FILTER,
                                texFilter)

    @property
    def interpolate(self):
        """Whether to interpolate linearly when drawing scaled (`bool`),
        applied as each texture is next bound."""
        return self._interpolate

    @interpolate.setter
    def interpolate(self, value):
        if bool(value) != self._interpolate:
            self._interpolate = bool(value)
            self._filterNeedsUpdate = True

    def bind(self, slot):
        """Bind a slot's texture to the active texture unit."""
        self.gl.glBindTexture(G.GL_TEXTURE_2D, self.textures[slot])
        if self._filterNeedsUpdate:
            for i in range(self.nSlots):
                self.gl.glBindTexture(G.GL_TEXTURE_2D, self.textures[i])
                self._applyFilter()
            self._filterNeedsUpdate = False
            self.gl.glBindTexture(G.GL_TEXTURE_2D, self.textures[slot])

    def _semaphoreOp(self, func, semaphores, slot):
        texture = (ctypes.c_uint * 1)(self.textures[slot])
        layout = (ctypes.c_uint * 1)(_LAYOUT)
        func(semaphores[slot], 0, None, 1, texture, layout)

    def waitReady(self, slot):
        """Make the GPU wait until the server has rendered into a slot (only
        after its `frame` message)."""
        self._semaphoreOp(self.gl.glWaitSemaphoreEXT, self.ready, slot)

    def signalReady(self, slot):
        """Signal that a slot has been rendered into (flush before telling the
        stimulus)."""
        self._semaphoreOp(self.gl.glSignalSemaphoreEXT, self.ready, slot)

    def waitDone(self, slot):
        """Make the GPU wait until the stimulus has finished with a slot (only
        after its `release` message)."""
        self._semaphoreOp(self.gl.glWaitSemaphoreEXT, self.done, slot)

    def signalDone(self, slot):
        """Signal that a slot is no longer drawn (flush before telling the
        server)."""
        self._semaphoreOp(self.gl.glSignalSemaphoreEXT, self.done, slot)

    def framebuffer(self, slot):
        """Framebuffer drawing to a slot's texture, made in the current context
        when first asked for (framebuffers aren't shared between contexts)."""
        gl = self.gl
        if self._framebuffers is None:
            self._framebuffers = (ctypes.c_uint * self.nSlots)()
            gl.glGenFramebuffers(self.nSlots, self._framebuffers)
            previous = ctypes.c_int(0)
            gl.glGetIntegerv(G.GL_DRAW_FRAMEBUFFER_BINDING,
                             ctypes.byref(previous))
            for i in range(self.nSlots):
                gl.glBindFramebuffer(G.GL_FRAMEBUFFER, self._framebuffers[i])
                gl.glFramebufferTexture2D(
                    G.GL_FRAMEBUFFER, G.GL_COLOR_ATTACHMENT0, G.GL_TEXTURE_2D,
                    self.textures[i], 0)
                status = gl.glCheckFramebufferStatus(G.GL_FRAMEBUFFER)
                if status != G.GL_FRAMEBUFFER_COMPLETE:
                    gl.glBindFramebuffer(G.GL_FRAMEBUFFER, previous.value)
                    raise GPUShareError(
                        "Shared frame can't be drawn to (framebuffer status "
                        "{})".format(hex(status)))
            gl.glBindFramebuffer(G.GL_FRAMEBUFFER, previous.value)
        return self._framebuffers[slot]

    def fillCheckColors(self):
        """Fill each slot with its check color and signal it ready (server)."""
        gl = self.gl
        previous = ctypes.c_int(0)
        gl.glGetIntegerv(G.GL_DRAW_FRAMEBUFFER_BINDING, ctypes.byref(previous))
        scissor = gl.glIsEnabled(G.GL_SCISSOR_TEST)
        gl.glDisable(G.GL_SCISSOR_TEST)
        for i in range(self.nSlots):
            gl.glBindFramebuffer(G.GL_FRAMEBUFFER, self.framebuffer(i))
            r, g, b, a = checkColor(i)
            gl.glClearColor(r / 255., g / 255., b / 255., a / 255.)
            gl.glClear(G.GL_COLOR_BUFFER_BIT)
            self.signalReady(i)
        if scissor:
            gl.glEnable(G.GL_SCISSOR_TEST)
        gl.glBindFramebuffer(G.GL_FRAMEBUFFER, previous.value)
        gl.glFlush()

    def readCheckColors(self):
        """Wait for each slot, read its center pixel back, then signal it done
        (stimulus). Stalls until the GPU has finished, so only done once.

        Returns
        -------
        list of tuple
            RGBA bytes read from each slot.

        """
        gl = self.gl
        previousDraw = ctypes.c_int(0)
        previousRead = ctypes.c_int(0)
        gl.glGetIntegerv(G.GL_DRAW_FRAMEBUFFER_BINDING,
                         ctypes.byref(previousDraw))
        gl.glGetIntegerv(G.GL_READ_FRAMEBUFFER_BINDING,
                         ctypes.byref(previousRead))
        pixel = (ctypes.c_ubyte * 4)()
        colors = []
        for i in range(self.nSlots):
            self.waitReady(i)
            gl.glBindFramebuffer(G.GL_READ_FRAMEBUFFER, self.framebuffer(i))
            gl.glPixelStorei(G.GL_PACK_ALIGNMENT, 1)
            gl.glReadPixels(self.width // 2, self.height // 2, 1, 1,
                            G.GL_RGBA, G.GL_UNSIGNED_BYTE, pixel)
            colors.append(tuple(pixel))
            self.signalDone(i)
        gl.glBindFramebuffer(G.GL_READ_FRAMEBUFFER, previousRead.value)
        gl.glBindFramebuffer(G.GL_DRAW_FRAMEBUFFER, previousDraw.value)
        gl.glFlush()
        return colors

    def delete(self):
        """Delete the textures, framebuffers, memory and semaphores."""
        gl = self.gl
        try:
            if self._framebuffers is not None:
                gl.glDeleteFramebuffers(self.nSlots, self._framebuffers)
                self._framebuffers = None
            if any(self.textures):
                gl.glDeleteTextures(self.nSlots, self.textures)
            if any(self.ready):
                gl.glDeleteSemaphoresEXT(self.nSlots, self.ready)
            if any(self.done):
                gl.glDeleteSemaphoresEXT(self.nSlots, self.done)
            if any(self.memories):
                gl.glDeleteMemoryObjectsEXT(self.nSlots, self.memories)
        except Exception:  # e.g. the context has gone at exit
            pass
        n = self.nSlots
        self.textures = (ctypes.c_uint * n)()
        self.ready = (ctypes.c_uint * n)()
        self.done = (ctypes.c_uint * n)()
        self.memories = (ctypes.c_uint * n)()


def closeFds(fds):
    """Close file descriptors which weren't handed to OpenGL."""
    for fd in fds:
        try:
            os.close(fd)
        except OSError:
            pass
