# JRG: add contrib/tesselate.py, copied from svgbatch / svgload project
# bug ??FIXED: `pointer` not defined in `combineCallback()`, removed
# changed: explicitly use the default winding rule GLU_TESS_WINDING_ODD

# downloaded Nov 2015 https://github.com/tartley/svgload/blob/master
# svgload LICENSE.txt contains:
'''
This is a BSD license.
http://www.opensource.org/licenses/bsd-license.php

tessellate.py Copyright (c) 2008, Martin O'Leary
The remainder Copyright (c) 2009, Jonathan Hartley
All rights reserved

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name(s) of the copyright holders nor the names of its
      contributors may be used to endorse or promote products derived from
      this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''

# Many thanks to Martin O'Leary of supereffective.org, whos Squirtle module
# formed a major inspiration for this entire project [svgbatch], and in particular for
# his sublime tesselation code. This has been copied wholesale, under the terms
# of the BSD.
# http://www.supereffective.org/pages/Squirtle-SVG-Library

from __future__ import absolute_import, print_function

from builtins import chr
from builtins import object
from ctypes import CFUNCTYPE, POINTER, byref, cast

import sys

from pyglet.gl import (
    GLdouble, GLenum, GLfloat, GLvoid,
    GL_TRIANGLES, GL_TRIANGLE_FAN, GL_TRIANGLE_STRIP,
    gluErrorString, gluNewTess, gluTessBeginContour, gluTessBeginPolygon,
    gluTessCallback, gluTessEndContour, gluTessEndPolygon, gluTessNormal,
    gluTessProperty, gluTessVertex,
    GLU_TESS_BEGIN, GLU_TESS_COMBINE, GLU_TESS_END, GLU_TESS_ERROR,
    GLU_TESS_VERTEX, GLU_TESS_WINDING_ODD, GLU_TESS_WINDING_RULE,
)


class TesselateError(Exception):
    pass


tess = gluNewTess()
gluTessNormal(tess, 0, 0, 1)
default_winding_rule = GLU_TESS_WINDING_ODD
gluTessProperty(tess, GLU_TESS_WINDING_RULE, default_winding_rule)


if sys.platform == 'win32':
    from ctypes import WINFUNCTYPE
    c_functype = WINFUNCTYPE
else:
    c_functype = CFUNCTYPE


callback_types = {
    GLU_TESS_VERTEX: c_functype(None, POINTER(GLvoid)),
    GLU_TESS_BEGIN: c_functype(None, GLenum),
    GLU_TESS_END: c_functype(None),
    GLU_TESS_ERROR: c_functype(None, GLenum),
    GLU_TESS_COMBINE: c_functype(
        None, POINTER(GLdouble), POINTER(POINTER(GLvoid)), POINTER(GLfloat),
        POINTER(POINTER(GLvoid))
    )
}


def tesselate(loops):
    return Tesselate().tesselate(loops)


def set_tess_callback(which):
    def set_call(func):
        cb = callback_types[which](func)
        gluTessCallback(tess, which, cast(cb, CFUNCTYPE(None)))
        return cb
    return set_call


class Tesselate(object):

    def fan_to_triangles(self):
        c = self.curr_shape.pop(0)
        p1 = self.curr_shape.pop(0)
        while self.curr_shape:
            p2 = self.curr_shape.pop(0)
            self.tlist.extend([c, p1, p2])
            p1 = p2

    def strip_to_triangles(self):
        p1 = self.curr_shape.pop(0)
        p2 = self.curr_shape.pop(0)
        while self.curr_shape:
            p3 = self.curr_shape.pop(0)
            self.tlist.extend([p1, p2, p3])
            p1 = p2
            p2 = p3

    def tesselate(self, looplist):
        self.tlist = []
        self.curr_shape = []
        spareverts = []

        @set_tess_callback(GLU_TESS_VERTEX)
        def vertexCallback(vertex):
            vertex = cast(vertex, POINTER(GLdouble))
            self.curr_shape.append(tuple(vertex[0:2]))

        @set_tess_callback(GLU_TESS_BEGIN)
        def beginCallback(which):
            self.tess_style = which

        @set_tess_callback(GLU_TESS_END)
        def endCallback():
            if self.tess_style == GL_TRIANGLE_FAN:
                self.fan_to_triangles()
            elif self.tess_style == GL_TRIANGLE_STRIP:
                self.strip_to_triangles()
            elif self.tess_style == GL_TRIANGLES:
                self.tlist.extend(self.curr_shape)
            else:
                self.warn("Unknown tesselation style: %d" % (self.tess_style,))
            self.tess_style = None
            self.curr_shape = []

        @set_tess_callback(GLU_TESS_ERROR)
        def errorCallback(code):
            ptr = gluErrorString(code)
            err = ''
            idx = 0
            while ptr[idx]:
                err += chr(ptr[idx])
                idx += 1
            self.warn("GLU Tesselation Error: " + err)

        @set_tess_callback(GLU_TESS_COMBINE)
        def combineCallback(coords, vertex_data, weights, dataOut):
            x, y, z = coords[0:3]
            data = (GLdouble * 3)(x, y, z)
            #dataOut[0] = cast(pointer(data), POINTER(GLvoid))  # original
            dataOut[0] = cast(data, POINTER(GLvoid))
            spareverts.append(data)

        data_lists = self.create_data_lists(looplist)
        return self.perform_tessellation(data_lists)

    def create_data_lists(self, looplist):
        data_lists = []
        for vlist in looplist:
            d_list = []
            for x, y in vlist:
                v_data = (GLdouble * 3)(x, y, 0)
                d_list.append(v_data)
            data_lists.append(d_list)
        return data_lists

    def perform_tessellation(self, data_lists):
        gluTessBeginPolygon(tess, None)
        for d_list in data_lists:
            gluTessBeginContour(tess)
            for v_data in d_list:
                gluTessVertex(tess, v_data, v_data)
            gluTessEndContour(tess)
        gluTessEndPolygon(tess)
        return self.tlist

    def warn(self, message):
        raise TesselateError(message)
