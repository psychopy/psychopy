#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Passing pages' frames to the stimulus on the GPU, for the web browser
server (see `_gpushare` for how the two processes share them).

Each widget a page renders in (and each popup it opens) has its render copied,
on the GPU, into a texture of ours from inside its render pass
(`RetainedCapture`), instead of being read back with `grabFramebuffer()`, which
also renders it again. When a frame is due, those textures are drawn into a
free shared slot (`GpuSurface`), in a context of our own which shares objects
with the widgets' (`GpuCompositor`).

Imported by `_qtbrowser`, so only in the server.
"""

import ctypes
import sys
import traceback

from PyQt6 import QtCore, QtGui, sip

import _glext as G
from _gpushare import GLSlots, GPUShareError
from _vkshare import VulkanAllocator, VulkanError

Qt = QtCore.Qt

__all__ = ['GpuCompositor', 'RetainedCapture', 'GpuSurface', 'GPUShareError']


def _contextKey(context):
    """Identity of a context, for objects which are made per context."""
    return int(sip.unwrapinstance(context))


class GpuCompositor:
    """A context of our own, sharing objects with the pages' contexts, where
    frames are drawn into the shared slots; and the Vulkan device the slots
    are allocated on.

    Needs `Qt.AA_ShareOpenGLContexts` to have been set before the application
    was made.

    Raises
    ------
    GPUShareError
        If the context can't be made, or can't share memory.

    """
    def __init__(self):
        share = QtGui.QOpenGLContext.globalShareContext()
        if share is None:
            raise GPUShareError("Qt has no shared OpenGL context")
        self.context = QtGui.QOpenGLContext()
        self.context.setShareContext(share)
        self.context.setFormat(share.format())
        if not self.context.create():
            raise GPUShareError("Couldn't make an OpenGL context")
        self.surface = QtGui.QOffscreenSurface()
        self.surface.setFormat(self.context.format())
        self.surface.create()
        self.makeCurrent()
        try:
            self.gl = G.GLFunctions(
                lambda name: self.context.getProcAddress(name))
            if not self.gl.supportsSharing():
                raise GPUShareError(
                    "OpenGL can't import memory and semaphores ({} "
                    "needed)".format(', '.join(G.SHARING_EXTENSIONS)))
            self.uuids = self.gl.uuids()
        finally:
            self.doneCurrent()
        self._allocator = None

    def makeCurrent(self):
        if not self.context.makeCurrent(self.surface):
            raise GPUShareError("Couldn't make the OpenGL context current")

    def doneCurrent(self):
        self.context.doneCurrent()

    def allocatorFor(self, uuids):
        """Get the Vulkan allocator, checking the stimulus' GPU is ours.

        Parameters
        ----------
        uuids : sequence of str
            Device and driver UUIDs of the stimulus' OpenGL context.

        """
        if tuple(uuids) != tuple(self.uuids):
            raise GPUShareError(
                "The window and the web browser are on different GPUs or "
                "drivers ({} and {})".format(tuple(uuids), tuple(self.uuids)))
        if self._allocator is None:
            try:
                self._allocator = VulkanAllocator(*self.uuids)
            except VulkanError as err:
                raise GPUShareError(str(err))
        return self._allocator


class RetainedCapture:
    """Copies of what a widget renders, kept in a texture of ours.

    Parameters
    ----------
    widget : QQuickWidget
        The widget (a page's render widget, or a popup's).
    onError : callable
        Called with a message if copying fails, after which nothing more is
        copied.

    """
    def __init__(self, widget, onError):
        self.widget = widget
        self.window = widget.quickWindow()
        self.onError = onError
        self.texture = None
        self.size = None
        self.fence = None
        self._gl = {}
        self._framebuffers = {}  # (context, texture) -> framebuffer
        self._readFramebuffer = None  # ours, in the compositor's context
        self.window.afterRenderPassRecording.connect(
            self._capture, Qt.ConnectionType.DirectConnection)

    def _glFor(self, context):
        key = _contextKey(context)
        if key not in self._gl:
            self._gl[key] = G.GLFunctions(
                lambda name, c=context: c.getProcAddress(name))
        return self._gl[key]

    def _capture(self):
        """Copy what the widget just rendered (from inside its render pass,
        where its render target is bound)."""
        self.window.beginExternalCommands()
        try:
            context = QtGui.QOpenGLContext.currentContext()
            gl = self._glFor(context)
            draw = ctypes.c_int(0)
            read = ctypes.c_int(0)
            viewport = (ctypes.c_int * 4)()
            gl.glGetIntegerv(G.GL_DRAW_FRAMEBUFFER_BINDING, ctypes.byref(draw))
            gl.glGetIntegerv(G.GL_READ_FRAMEBUFFER_BINDING, ctypes.byref(read))
            gl.glGetIntegerv(G.GL_VIEWPORT, viewport)
            width, height = viewport[2], viewport[3]
            if width <= 0 or height <= 0:
                return
            if self.texture is None or self.size != (width, height):
                self._newTexture(gl, width, height)
            key = (_contextKey(context), self.texture)
            framebuffer = self._framebuffers.get(key)
            if framebuffer is None:
                fb = ctypes.c_uint()
                gl.glGenFramebuffers(1, ctypes.byref(fb))
                gl.glBindFramebuffer(G.GL_DRAW_FRAMEBUFFER, fb)
                gl.glFramebufferTexture2D(
                    G.GL_DRAW_FRAMEBUFFER, G.GL_COLOR_ATTACHMENT0,
                    G.GL_TEXTURE_2D, self.texture, 0)
                framebuffer = self._framebuffers[key] = fb.value
            scissor = gl.glIsEnabled(G.GL_SCISSOR_TEST)
            gl.glDisable(G.GL_SCISSOR_TEST)
            gl.glBindFramebuffer(G.GL_READ_FRAMEBUFFER, draw.value)
            gl.glBindFramebuffer(G.GL_DRAW_FRAMEBUFFER, framebuffer)
            gl.glBlitFramebuffer(0, 0, width, height, 0, 0, width, height,
                                 G.GL_COLOR_BUFFER_BIT, G.GL_NEAREST)
            gl.glBindFramebuffer(G.GL_READ_FRAMEBUFFER, read.value)
            gl.glBindFramebuffer(G.GL_DRAW_FRAMEBUFFER, draw.value)
            if scissor:
                gl.glEnable(G.GL_SCISSOR_TEST)
            if self.fence:
                gl.glDeleteSync(self.fence)
            # the compositor waits for this before drawing from the texture
            self.fence = gl.glFenceSync(G.GL_SYNC_GPU_COMMANDS_COMPLETE, 0)
            gl.glFlush()
        except Exception as err:
            traceback.print_exc()
            self.disconnect()
            self.onError("Copying the page's frames failed: {}".format(err))
        finally:
            self.window.endExternalCommands()

    def _newTexture(self, gl, width, height):
        texture = ctypes.c_uint()
        previous = ctypes.c_int(0)
        gl.glGetIntegerv(G.GL_TEXTURE_BINDING_2D, ctypes.byref(previous))
        gl.glGenTextures(1, ctypes.byref(texture))
        gl.glBindTexture(G.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(G.GL_TEXTURE_2D, 0, G.GL_RGBA8, width, height, 0,
                        G.GL_RGBA, G.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_MIN_FILTER,
                           G.GL_NEAREST)
        gl.glTexParameteri(G.GL_TEXTURE_2D, G.GL_TEXTURE_MAG_FILTER,
                           G.GL_NEAREST)
        gl.glBindTexture(G.GL_TEXTURE_2D, previous.value)
        self.texture = texture.value  # the old one is deleted by `destroy`
        self.size = (width, height)
        self.fence = None

    def drawInto(self, gl, framebuffer, dstRect):
        """Draw the latest copy into a framebuffer, in the compositor's
        context.

        Parameters
        ----------
        gl : _glext.GLFunctions
            The compositor's functions.
        framebuffer : int
            Framebuffer to draw into.
        dstRect : tuple
            `(x0, y0, x1, y1)` to draw it to, in OpenGL's orientation (y up).

        """
        if self.texture is None:
            return
        if self.fence:
            gl.glWaitSync(self.fence, 0, G.GL_TIMEOUT_IGNORED)
        if self._readFramebuffer is None or \
                self._readFramebuffer[1] != self.texture:
            if self._readFramebuffer is not None:
                old = (ctypes.c_uint * 1)(self._readFramebuffer[0])
                gl.glDeleteFramebuffers(1, old)
            fb = ctypes.c_uint()
            gl.glGenFramebuffers(1, ctypes.byref(fb))
            gl.glBindFramebuffer(G.GL_READ_FRAMEBUFFER, fb)
            gl.glFramebufferTexture2D(
                G.GL_READ_FRAMEBUFFER, G.GL_COLOR_ATTACHMENT0, G.GL_TEXTURE_2D,
                self.texture, 0)
            self._readFramebuffer = (fb.value, self.texture)
        width, height = self.size
        gl.glBindFramebuffer(G.GL_READ_FRAMEBUFFER, self._readFramebuffer[0])
        gl.glBindFramebuffer(G.GL_DRAW_FRAMEBUFFER, framebuffer)
        gl.glBlitFramebuffer(0, 0, width, height, *dstRect,
                             G.GL_COLOR_BUFFER_BIT, G.GL_NEAREST)

    def disconnect(self):
        try:
            self.window.afterRenderPassRecording.disconnect(self._capture)
        except (TypeError, RuntimeError):
            pass

    def destroy(self, compositor):
        """Stop copying and delete the texture (with the compositor's context
        current)."""
        self.disconnect()
        gl = compositor.gl
        if self._readFramebuffer is not None:
            gl.glDeleteFramebuffers(
                1, (ctypes.c_uint * 1)(self._readFramebuffer[0]))
            self._readFramebuffer = None
        if self.texture is not None:
            gl.glDeleteTextures(1, (ctypes.c_uint * 1)(self.texture))
            self.texture = None
        # framebuffers in the widgets' contexts go with those contexts


class GpuSurface:
    """Shared slots for one page's frames of one size.

    Parameters
    ----------
    compositor : GpuCompositor
        Where the slots are drawn into.
    uuids : sequence of str
        Device and driver UUIDs of the stimulus' context.
    width, height : int
        Size of the frames in pixels.
    nSlots : int
        Number of slots.
    gen : int
        Generation of the page's frames these are.

    Raises
    ------
    GPUShareError
        If the slots can't be allocated or imported.

    """
    def __init__(self, compositor, uuids, width, height, nSlots, gen):
        self.compositor = compositor
        self.width = int(width)
        self.height = int(height)
        self.gen = gen
        allocator = compositor.allocatorFor(uuids)
        self._images = []
        self._semaphores = []
        self.slots = None
        try:
            self._images = [allocator.allocateImage(width, height)
                            for _ in range(nSlots)]
            ready = [allocator.createSemaphore() for _ in range(nSlots)]
            done = [allocator.createSemaphore() for _ in range(nSlots)]
            self._semaphores = ready + done
            self.memSize = max(image.size for image in self._images)
            compositor.makeCurrent()
            try:
                self.slots = GLSlots(
                    compositor.gl, width, height, self.memSize,
                    [image.exportFd() for image in self._images],
                    [s.exportFd() for s in ready],
                    [s.exportFd() for s in done])
                self.slots.fillCheckColors()
            finally:
                compositor.doneCurrent()
            # the stimulus' own references, sent with the `surface` message
            self.stimulusFds = (
                [image.exportFd() for image in self._images] +
                [s.exportFd() for s in ready] + [s.exportFd() for s in done])
        except VulkanError as err:
            self.destroy()
            raise GPUShareError(str(err))
        except Exception:
            self.destroy()
            raise
        self.nSlots = nSlots
        # slots the stimulus has checked and released, and those it has
        # signalled done which haven't been waited on
        self.checked = False
        self.free = set()
        self.needsDone = set()

    def checkPassed(self):
        """The stimulus read the check colors back, and signalled each slot
        done: all are free."""
        self.checked = True
        self.free = set(range(self.nSlots))
        self.needsDone = set(range(self.nSlots))

    def release(self, slot):
        self.free.add(slot)
        self.needsDone.add(slot)

    def compose(self, layers):
        """Draw a frame into a free slot and signal it ready.

        Parameters
        ----------
        layers : list of tuple
            `(capture, dstRect)` to draw, bottom first, each rectangle
            `(x0, y0, x1, y1)` in OpenGL's orientation.

        Returns
        -------
        int
            The slot drawn into.

        """
        slot = min(self.free)
        self.free.discard(slot)
        compositor = self.compositor
        gl = compositor.gl
        compositor.makeCurrent()
        try:
            if slot in self.needsDone:
                self.slots.waitDone(slot)
                self.needsDone.discard(slot)
            framebuffer = self.slots.framebuffer(slot)
            gl.glDisable(G.GL_SCISSOR_TEST)
            for capture, dstRect in layers:
                capture.drawInto(gl, framebuffer, dstRect)
            gl.glBindFramebuffer(G.GL_FRAMEBUFFER, 0)
            self.slots.signalReady(slot)
            gl.glFlush()
            errors = gl.clearErrors()
        finally:
            compositor.doneCurrent()
        if errors:
            raise GPUShareError("Drawing a frame failed (OpenGL errors "
                                "{})".format([hex(e) for e in errors]))
        return slot

    def destroy(self):
        """Delete the slots here. The stimulus' imports stay valid."""
        if self.slots is not None:
            try:
                self.compositor.makeCurrent()
                self.slots.delete()
                self.compositor.doneCurrent()
            except Exception:
                print("Couldn't delete shared frames:", file=sys.stderr)
                traceback.print_exc()
            self.slots = None
        for item in self._images + self._semaphores:
            item.destroy()
        self._images = []
        self._semaphores = []
