#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function  # for compatibility with python3

from pyglet.gl import gl_info, GLint, glGetIntegerv, GL_MAX_ELEMENTS_VERTICES
from psychopy import visual, preferences
import sys, platform

print("Paths to files on the system:")
for key in ['userPrefsFile', 'appDataFile', 'demos', 'appFile']:
    print("    %s: %s" % (key, preferences.prefs.paths[key]))

print("\nSystem info:")
print(platform.platform())
if sys.platform == 'darwin':
    OSXver, junk, architecture = platform.mac_ver()
    print("macOS %s running on %s" % (OSXver, architecture))

print("\nPython info")
print(sys.executable)
print(sys.version)
import numpy
print("numpy", numpy.__version__)
import scipy
print("scipy", scipy.__version__)
import matplotlib
print("matplotlib", matplotlib.__version__)
import pyglet
print("pyglet", pyglet.version)
# pyo is a new dependency, for sound:
try:
    import pyo
    print("pyo", '%i.%i.%i' % pyo.getVersion())
except Exception:
    print('pyo [not installed]')

from psychopy import __version__
print("\nPsychoPy", __version__)

win = visual.Window([100, 100])  # some drivers want a window open first
print("have shaders:", win._haveShaders)
print("\nOpenGL info:")
# get info about the graphics card and drivers
print("vendor:", gl_info.get_vendor())
print("rendering engine:", gl_info.get_renderer())
print("OpenGL version:", gl_info.get_version())
print("(Selected) Extensions:")
extensionsOfInterest = ['GL_ARB_multitexture',
                        'GL_EXT_framebuffer_object', 'GL_ARB_fragment_program',
                        'GL_ARB_shader_objects', 'GL_ARB_vertex_shader',
                        'GL_ARB_texture_non_power_of_two', 'GL_ARB_texture_float', 'GL_STEREO']
for ext in extensionsOfInterest:
    print("\t", bool(gl_info.have_extension(ext)), ext)
# also determine nVertices that can be used in vertex arrays
maxVerts = GLint()
glGetIntegerv(GL_MAX_ELEMENTS_VERTICES, maxVerts)
print('\tmax vertices in vertex array:', maxVerts.value)
