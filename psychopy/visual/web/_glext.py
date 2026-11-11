#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""OpenGL functions for sharing frames between processes on the GPU.

Frames can be passed from the web browser server to the stimulus without
leaving the GPU, as textures in memory both processes import with the
`GL_EXT_memory_object` extensions, synchronized with semaphores imported with
the `GL_EXT_semaphore` ones (see `_gpushare`). PyQt6 and pyglet don't wrap
these, so they are looked up here, along with the core functions the server
needs (it doesn't import pyglet).

This module only uses the standard library, as the server imports it without
importing PsychoPy.
"""

import ctypes
import ctypes.util
import sys

__all__ = ['GLFunctions', 'platformGetProcAddress', 'SHARING_EXTENSIONS']

# core
GL_NO_ERROR = 0
GL_TEXTURE_2D = 0x0DE1
GL_TEXTURE_MAG_FILTER = 0x2800
GL_TEXTURE_MIN_FILTER = 0x2801
GL_TEXTURE_WRAP_S = 0x2802
GL_TEXTURE_WRAP_T = 0x2803
GL_NEAREST = 0x2600
GL_LINEAR = 0x2601
GL_CLAMP_TO_EDGE = 0x812F
GL_RGBA = 0x1908
GL_RGBA8 = 0x8058
GL_UNSIGNED_BYTE = 0x1401
GL_EXTENSIONS = 0x1F03
GL_NUM_EXTENSIONS = 0x821D
GL_RENDERER = 0x1F01
GL_VIEWPORT = 0x0BA2
GL_SCISSOR_TEST = 0x0C11
GL_PACK_ALIGNMENT = 0x0D05
GL_COLOR_BUFFER_BIT = 0x4000
GL_TEXTURE_BINDING_2D = 0x8069
GL_FRAMEBUFFER = 0x8D40
GL_READ_FRAMEBUFFER = 0x8CA8
GL_DRAW_FRAMEBUFFER = 0x8CA9
GL_DRAW_FRAMEBUFFER_BINDING = 0x8CA6
GL_READ_FRAMEBUFFER_BINDING = 0x8CAA
GL_COLOR_ATTACHMENT0 = 0x8CE0
GL_FRAMEBUFFER_COMPLETE = 0x8CD5
GL_SYNC_GPU_COMMANDS_COMPLETE = 0x9117
GL_TIMEOUT_IGNORED = 0xFFFFFFFFFFFFFFFF

# GL_EXT_memory_object(_fd)
GL_TEXTURE_TILING_EXT = 0x9580
GL_DEDICATED_MEMORY_OBJECT_EXT = 0x9581
GL_OPTIMAL_TILING_EXT = 0x9584
GL_DEVICE_UUID_EXT = 0x9597
GL_DRIVER_UUID_EXT = 0x9598
GL_UUID_SIZE_EXT = 16
GL_HANDLE_TYPE_OPAQUE_FD_EXT = 0x9586

# GL_EXT_semaphore(_fd)
GL_LAYOUT_GENERAL_EXT = 0x958D
GL_LAYOUT_COLOR_ATTACHMENT_EXT = 0x958E
GL_LAYOUT_SHADER_READ_ONLY_EXT = 0x9591
GL_LAYOUT_TRANSFER_SRC_EXT = 0x9592
GL_LAYOUT_TRANSFER_DST_EXT = 0x9593

# extensions both processes need to share frames on the GPU
SHARING_EXTENSIONS = (
    'GL_EXT_memory_object', 'GL_EXT_memory_object_fd', 'GL_EXT_semaphore',
    'GL_EXT_semaphore_fd')

_FUNCTYPE = ctypes.WINFUNCTYPE if sys.platform == 'win32' else ctypes.CFUNCTYPE

_u = ctypes.c_uint
_i = ctypes.c_int
_p = ctypes.c_void_p
_u64 = ctypes.c_uint64
_pu = ctypes.POINTER(ctypes.c_uint)
_pi = ctypes.POINTER(ctypes.c_int)
_pub = ctypes.POINTER(ctypes.c_ubyte)

# (return type, argument types) of each function used
_PROTOTYPES_ = {
    'glGetError': (_u, ()),
    'glGetString': (ctypes.c_char_p, (_u,)),
    'glGetStringi': (ctypes.c_char_p, (_u, _u)),
    'glGetIntegerv': (None, (_u, _pi)),
    'glEnable': (None, (_u,)),
    'glDisable': (None, (_u,)),
    'glIsEnabled': (ctypes.c_ubyte, (_u,)),
    'glFlush': (None, ()),
    'glFinish': (None, ()),
    'glPixelStorei': (None, (_u, _i)),
    'glReadPixels': (None, (_i, _i, _i, _i, _u, _u, _p)),
    'glGenTextures': (None, (_i, _pu)),
    'glDeleteTextures': (None, (_i, _pu)),
    'glBindTexture': (None, (_u, _u)),
    'glTexParameteri': (None, (_u, _u, _i)),
    'glTexImage2D': (None, (_u, _i, _i, _i, _i, _i, _u, _u, _p)),
    'glGenFramebuffers': (None, (_i, _pu)),
    'glDeleteFramebuffers': (None, (_i, _pu)),
    'glBindFramebuffer': (None, (_u, _u)),
    'glFramebufferTexture2D': (None, (_u, _u, _u, _u, _i)),
    'glCheckFramebufferStatus': (_u, (_u,)),
    'glBlitFramebuffer': (None, (_i, _i, _i, _i, _i, _i, _i, _i, _u, _u)),
    'glClearColor': (None, (ctypes.c_float,) * 4),
    'glClear': (None, (_u,)),
    'glFenceSync': (_p, (_u, _u)),
    'glWaitSync': (None, (_p, _u, _u64)),
    'glDeleteSync': (None, (_p,)),
    'glCreateMemoryObjectsEXT': (None, (_i, _pu)),
    'glDeleteMemoryObjectsEXT': (None, (_i, _pu)),
    'glMemoryObjectParameterivEXT': (None, (_u, _u, _pi)),
    'glImportMemoryFdEXT': (None, (_u, _u64, _u, _i)),
    'glTexStorageMem2DEXT': (None, (_u, _i, _u, _i, _i, _u, _u64)),
    'glGenSemaphoresEXT': (None, (_i, _pu)),
    'glDeleteSemaphoresEXT': (None, (_i, _pu)),
    'glImportSemaphoreFdEXT': (None, (_u, _u, _i)),
    'glSignalSemaphoreEXT': (None, (_u, _u, _pu, _u, _pu, _pu)),
    'glWaitSemaphoreEXT': (None, (_u, _u, _pu, _u, _pu, _pu)),
    'glGetUnsignedBytevEXT': (None, (_u, _pub)),
    'glGetUnsignedBytei_vEXT': (None, (_u, _u, _pub)),
}


def _systemGL():
    """The system's OpenGL library, for functions not given by address."""
    if sys.platform == 'win32':
        return ctypes.WinDLL('opengl32')
    if sys.platform == 'darwin':
        return ctypes.CDLL('/System/Library/Frameworks/OpenGL.framework/OpenGL')
    name = ctypes.util.find_library('GL') or 'libGL.so.1'
    return ctypes.CDLL(name)


def platformGetProcAddress():
    """Get a function looking up OpenGL functions in the current context, for
    processes which don't get one from their toolkit (e.g. `QOpenGLContext`).

    Returns
    -------
    callable or None
        Taking the function's name (`bytes`) and returning its address
        (`int`, 0 if unknown), or `None` on platforms this isn't done on.

    """
    if sys.platform.startswith('linux'):
        lib = _systemGL()
        getProc = lib.glXGetProcAddressARB
        getProc.restype = ctypes.c_void_p
        getProc.argtypes = (ctypes.c_char_p,)
        return lambda name: getProc(name) or 0
    if sys.platform == 'win32':
        lib = _systemGL()
        getProc = lib.wglGetProcAddress
        getProc.restype = ctypes.c_void_p
        getProc.argtypes = (ctypes.c_char_p,)
        return lambda name: getProc(name) or 0
    return None


class GLFunctions:
    """OpenGL functions looked up in a context, bound as needed.

    Functions are only valid in the context they were looked up in (and those
    sharing its objects), with it current.

    Parameters
    ----------
    getProcAddress : callable
        Taking a function's name (`bytes`) and returning its address (`int`,
        0 if unknown), e.g. `QOpenGLContext.getProcAddress`.

    """
    def __init__(self, getProcAddress):
        self._getProcAddress = getProcAddress
        self._system = None

    def __getattr__(self, name):
        if name not in _PROTOTYPES_:
            raise AttributeError(name)
        address = int(self._getProcAddress(name.encode('ascii')) or 0)
        if not address:
            # windows only gives OpenGL 1.1 functions from the library itself
            if self._system is None:
                self._system = _systemGL()
            try:
                address = ctypes.cast(
                    getattr(self._system, name), ctypes.c_void_p).value
            except AttributeError:
                address = 0
        if not address:
            raise AttributeError("OpenGL function {} isn't available".format(
                name))
        restype, argtypes = _PROTOTYPES_[name]
        func = _FUNCTYPE(restype, *argtypes)(address)
        setattr(self, name, func)  # bound once
        return func

    def extensions(self):
        """Names of the extensions the current context supports (`set`)."""
        try:
            count = ctypes.c_int(0)
            self.glGetIntegerv(GL_NUM_EXTENSIONS, ctypes.byref(count))
            names = {self.glGetStringi(GL_EXTENSIONS, i).decode('ascii')
                     for i in range(count.value)}
            if names:
                return names
        except AttributeError:
            pass
        while self.glGetError() != GL_NO_ERROR:  # from a legacy context
            pass
        text = self.glGetString(GL_EXTENSIONS) or b''
        return set(text.decode('ascii').split())

    def supportsSharing(self):
        """Whether the current context can share frames on the GPU (`bool`).
        """
        return set(SHARING_EXTENSIONS) <= self.extensions()

    def uuids(self):
        """UUIDs of the device and driver of the current context, which must
        match between processes sharing memory.

        Returns
        -------
        tuple
            `(deviceUUID, driverUUID)` as hex strings.

        """
        device = (ctypes.c_ubyte * GL_UUID_SIZE_EXT)()
        driver = (ctypes.c_ubyte * GL_UUID_SIZE_EXT)()
        self.glGetUnsignedBytei_vEXT(GL_DEVICE_UUID_EXT, 0, device)
        self.glGetUnsignedBytevEXT(GL_DRIVER_UUID_EXT, driver)
        return bytes(device).hex(), bytes(driver).hex()

    def clearErrors(self):
        """Clear and return the pending OpenGL errors (`list` of `int`)."""
        errors = []
        for _ in range(16):
            err = self.glGetError()
            if err == GL_NO_ERROR:
                break
            errors.append(err)
        return errors
