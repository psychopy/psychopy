#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""OpenGL types as `ctypes` types.

These match the definitions in `pyglet.gl`, so values created with either can
be passed to the functions of both.

"""

import sys
from ctypes import (
    CFUNCTYPE, POINTER, Structure, c_byte, c_char, c_double, c_float, c_int,
    c_int64, c_short, c_ssize_t, c_ubyte, c_uint, c_uint64, c_ushort,
    c_void_p)

__all__ = [
    'GLenum', 'GLboolean', 'GLbitfield', 'GLvoid', 'GLbyte', 'GLubyte',
    'GLshort', 'GLushort', 'GLint', 'GLuint', 'GLclampx', 'GLsizei', 'GLfloat',
    'GLclampf', 'GLdouble', 'GLclampd', 'GLchar', 'GLcharARB', 'GLhandleARB',
    'GLhalf', 'GLhalfARB', 'GLhalfNV', 'GLfixed', 'GLintptr', 'GLintptrARB',
    'GLsizeiptr', 'GLsizeiptrARB', 'GLint64', 'GLint64EXT', 'GLuint64',
    'GLuint64EXT', 'GLsync', 'GLeglImageOES', 'GLeglClientBufferEXT',
    'GLvdpauSurfaceNV', 'GLDEBUGPROC', 'GLDEBUGPROCARB', 'GLDEBUGPROCKHR',
    'GLDEBUGPROCAMD', 'GLVULKANPROCNV']

if sys.platform == 'win32':
    from ctypes import WINFUNCTYPE as FUNCTYPE  # `APIENTRY` is `__stdcall`
else:
    FUNCTYPE = CFUNCTYPE

GLenum = c_uint
GLboolean = c_ubyte
GLbitfield = c_uint
GLvoid = None  # so `POINTER(GLvoid)` is `c_void_p`
GLbyte = c_byte
GLubyte = c_ubyte
GLshort = c_short
GLushort = c_ushort
GLint = c_int
GLuint = c_uint
GLclampx = c_int
GLsizei = c_int
GLfloat = c_float
GLclampf = c_float
GLdouble = c_double
GLclampd = c_double
GLchar = GLcharARB = c_char
# `GL_ARB_shader_objects` handles are pointers on macOS only
GLhandleARB = c_void_p if sys.platform == 'darwin' else c_uint
GLhalf = GLhalfARB = GLhalfNV = c_ushort
GLfixed = c_int
GLintptr = GLintptrARB = c_ssize_t
GLsizeiptr = GLsizeiptrARB = c_ssize_t
GLint64 = GLint64EXT = c_int64
GLuint64 = GLuint64EXT = c_uint64
GLeglImageOES = GLeglClientBufferEXT = c_void_p
GLvdpauSurfaceNV = GLintptr


class _GLsync(Structure):
    """Opaque sync object."""
    _fields_ = [('_opaque', c_int)]


GLsync = POINTER(_GLsync)

GLDEBUGPROC = GLDEBUGPROCARB = GLDEBUGPROCKHR = FUNCTYPE(
    None, GLenum, GLenum, GLuint, GLenum, GLsizei, POINTER(GLchar),
    POINTER(GLvoid))
GLDEBUGPROCAMD = FUNCTYPE(
    None, GLuint, GLenum, GLenum, GLsizei, POINTER(GLchar), POINTER(GLvoid))
GLVULKANPROCNV = FUNCTYPE(None)
