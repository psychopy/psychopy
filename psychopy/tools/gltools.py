#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related helper functions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'VERTEX_ATTRIB_POSITION',
    'VERTEX_ATTRIB_NORMAL',
    'VERTEX_ATTRIB_COLOR',
    'VERTEX_ATTRIB_SECONADRY_COLOR',
    'VERTEX_ATTRIB_COLOR2',
    'VERTEX_ATTRIB_FOGCOORD',
    'VERTEX_ATTRIB_MULTITEXCOORD0',
    'VERTEX_ATTRIB_MULTITEXCOORD1',
    'VERTEX_ATTRIB_MULTITEXCOORD2',
    'VERTEX_ATTRIB_MULTITEXCOORD3',
    'VERTEX_ATTRIB_MULTITEXCOORD4',
    'VERTEX_ATTRIB_MULTITEXCOORD5',
    'VERTEX_ATTRIB_MULTITEXCOORD6',
    'VERTEX_ATTRIB_MULTITEXCOORD7',
    'createProgram',
    'createProgramObjectARB',
    'compileShader',
    'compileShaderObjectARB',
    'embedShaderSourceDefs',
    'deleteShader',
    'deleteProgram',
    'deleteObject',
    'deleteObjectARB',
    'attachShader',
    'attachObjectARB',
    'detachShader',
    'detachObjectARB',
    'linkProgram',
    'linkProgramObjectARB',
    'validateProgram',
    'validateProgramARB',
    'useProgram',
    'useProgramObjectARB',
    'getInfoLog',
    'setUniformValue',
    'setUniformMatrix',
    'getUniformLocation',
    'getUniformLocations',
    'getAttribLocations',
    'createQueryObject',
    'QueryObjectInfo',
    'beginQuery',
    'endQuery',
    'getQuery',
    'getAbsTimeGPU',
    'FramebufferInfo',
    'createFBO',
    'attachImage',
    'isFramebufferComplete',
    'deleteFBO',
    'blitFBO',
    'useFBO',
    'bindFBO',
    'unbindFBO',
    'deleteFBO',
    'clearFramebuffer',
    'setDrawBuffer',
    'setReadBuffer',
    'RenderbufferInfo',
    'createRenderbuffer',
    'deleteRenderbuffer',
    'createTexImage2D',
    'createTexImage2DMultisample',
    'deleteTexture',
    'VertexArrayInfo',
    'createVAO',
    'drawVAO',
    'deleteVAO',
    'drawClientArrays',
    'VertexBufferInfo',
    'createVBO',
    'bindVBO',
    'unbindVBO',
    'mapBuffer',
    'unmapBuffer',
    'mappedBuffer',
    'updateVBO',
    'deleteVBO',
    'setVertexAttribPointer',
    'enableVertexAttribArray',
    'disableVertexAttribArray',
    'createMaterial',
    'useMaterial',
    'createLight',
    'useLights',
    'setAmbientLight',
    'ObjMeshInfo',
    'loadObjFile',
    'loadMtlFile',
    'createUVSphere',
    'createPlane',
    'createMeshGridFromArrays',
    'createMeshGrid',
    'createBox',
    'createDisc',
    'createAnnulus',
    'createCylinder',
    'transformMeshPosOri',
    'calculateVertexNormals',
    'mergeVerticies',
    'smoothCreases',
    'flipFaces',
    'interleaveAttributes',
    'generateTexCoords',
    'tesselate',
    'getIntegerv',
    'getFloatv',
    'getString',
    'getOpenGLInfo',
    'createTexImage2D',
    'createTexImage2dFromFile',
    'bindTexture',
    'unbindTexture',
    'createCubeMap',
    'TexCubeMap',
    'getModelViewMatrix',
    'getProjectionMatrix'
]

import ctypes
from io import StringIO
from collections import namedtuple
import pyglet.gl as GL  # using Pyglet for now
from contextlib import contextmanager
from PIL import Image
import numpy as np
import os
import sys
import platform
import warnings
import psychopy.tools.mathtools as mt
from psychopy.visual.helpers import setColor, findImageFile

_thisPlatform = platform.system()

# create a query counter to get absolute GPU time
QUERY_COUNTER = None  # prevent genQueries from being called

# vertex attribute locations
VERTEX_ATTRIB_POSITION = 0   # gl_Vertex
VERTEX_ATTRIB_NORMAL = 2  # gl_Normal
VERTEX_ATTRIB_COLOR = 3  # gl_Color
VERTEX_ATTRIB_SECONADRY_COLOR = VERTEX_ATTRIB_COLOR2 = 4  # gl_SecondaryColor
VERTEX_ATTRIB_FOGCOORD = 5  # gl_FogCoord
VERTEX_ATTRIB_MULTITEXCOORD0 = 8  # gl_MultiTexCoord0
VERTEX_ATTRIB_MULTITEXCOORD1 = 9  # gl_MultiTexCoord1
VERTEX_ATTRIB_MULTITEXCOORD2 = 10  # gl_MultiTexCoord2
VERTEX_ATTRIB_MULTITEXCOORD3 = 11  # gl_MultiTexCoord3
VERTEX_ATTRIB_MULTITEXCOORD4 = 12  # gl_MultiTexCoord4
VERTEX_ATTRIB_MULTITEXCOORD5 = 13  # gl_MultiTexCoord5 
VERTEX_ATTRIB_MULTITEXCOORD6 = 14  # gl_MultiTexCoord6 
VERTEX_ATTRIB_MULTITEXCOORD7 = 15  # gl_MultiTexCoord7

# mapping human-readable names to the typical attribute locations
VERTEX_ATTRIBS = {
    'gl_Vertex': VERTEX_ATTRIB_POSITION,
    'gl_Normal': VERTEX_ATTRIB_NORMAL,
    'gl_Color': VERTEX_ATTRIB_COLOR,
    'gl_SecondaryColor': VERTEX_ATTRIB_COLOR2,
    'gl_FogCoord': VERTEX_ATTRIB_FOGCOORD,
    'gl_MultiTexCoord0': VERTEX_ATTRIB_MULTITEXCOORD0,
    'gl_MultiTexCoord1': VERTEX_ATTRIB_MULTITEXCOORD1,
    'gl_MultiTexCoord2': VERTEX_ATTRIB_MULTITEXCOORD2,
    'gl_MultiTexCoord3': VERTEX_ATTRIB_MULTITEXCOORD3,
    'gl_MultiTexCoord4': VERTEX_ATTRIB_MULTITEXCOORD4,
    'gl_MultiTexCoord5': VERTEX_ATTRIB_MULTITEXCOORD5,
    'gl_MultiTexCoord6': VERTEX_ATTRIB_MULTITEXCOORD6,
    'gl_MultiTexCoord7': VERTEX_ATTRIB_MULTITEXCOORD7
}

# Mappings between Python/Numpy and OpenGL data types for arrays. Duplication
# simplifies the lookup process when used in functions. Some types are not 
# supported by OpenGL, so they are remapped to the closest compatible type.
ARRAY_TYPES = {
    'float32': (GL.GL_FLOAT, GL.GLfloat, np.float32),
    'float': (GL.GL_FLOAT, GL.GLfloat, np.float32),   
    'double': (GL.GL_DOUBLE, GL.GLdouble, float),
    'float64': (GL.GL_DOUBLE, GL.GLdouble, float),
    'uint16': (GL.GL_UNSIGNED_SHORT, GL.GLushort, np.uint16),
    'unsigned_short': (GL.GL_UNSIGNED_SHORT, GL.GLushort, np.uint16),
    'uint32': (GL.GL_UNSIGNED_INT, GL.GLuint, np.uint32),
    'unsigned_int': (GL.GL_UNSIGNED_INT, GL.GLuint, np.uint32),
    'int': (GL.GL_INT, GL.GLint, np.int32),  # remapped to int32 from int64
    'int32': (GL.GL_INT, GL.GLint, np.int32), 
    'int16': (GL.GL_SHORT, GL.GLshort, np.int16),
    'short': (GL.GL_SHORT, GL.GLshort, np.int16),
    'uint8': (GL.GL_UNSIGNED_BYTE, GL.GLubyte, np.uint8),
    'unsigned_byte': (GL.GL_UNSIGNED_BYTE, GL.GLubyte, np.uint8),
    'int8': (GL.GL_BYTE, GL.GLbyte, np.int8),
    'byte': (GL.GL_BYTE, GL.GLbyte, np.int8),
    np.float32: (GL.GL_FLOAT, GL.GLfloat, np.float32),
    float: (GL.GL_DOUBLE, GL.GLdouble, float),
    np.float64: (GL.GL_DOUBLE, GL.GLdouble, np.float64),
    np.uint16: (GL.GL_UNSIGNED_SHORT, GL.GLushort, np.uint16),
    np.uint32: (GL.GL_UNSIGNED_INT, GL.GLuint, np.uint32),
    int: (GL.GL_INT, GL.GLint, np.int32),  # remapped to int32
    np.int32: (GL.GL_INT, GL.GLint, np.int32),
    np.int16: (GL.GL_SHORT, GL.GLshort, np.int16),
    np.uint8: (GL.GL_UNSIGNED_BYTE, GL.GLubyte, np.uint8),
    np.int8: (GL.GL_BYTE, GL.GLbyte, np.int8),
    GL.GL_FLOAT: (GL.GL_FLOAT, GL.GLfloat, np.float32),
    GL.GL_DOUBLE: (GL.GL_DOUBLE, GL.GLdouble, float),  # python float is 64-bit
    GL.GL_UNSIGNED_SHORT: (GL.GL_UNSIGNED_SHORT, GL.GLushort, np.uint16),
    GL.GL_UNSIGNED_INT: (GL.GL_UNSIGNED_INT, GL.GLuint, np.uint32),
    GL.GL_INT: (GL.GL_INT, GL.GLint, np.int32),
    GL.GL_SHORT: (GL.GL_SHORT, GL.GLshort, np.int16),
    GL.GL_UNSIGNED_BYTE: (GL.GL_UNSIGNED_BYTE, GL.GLubyte, np.uint8),
    GL.GL_BYTE: (GL.GL_BYTE, GL.GLbyte, np.int8),
}


def _getGLEnum(*args):
    """Get the OpenGL enum value from a string or GLEnum.

    Parameters
    ----------
    args : str, GLEnum, int or None
        OpenGL enum value(s) to retrieve. If `None`, `None` is returned.

    Returns
    -------
    int or list
        OpenGL enum value(s) in the order they were passed.

    Examples
    --------
    Get the OpenGL enum value for a single string::

        _getGLEnum('points')  # returns GL.GL_POINTS

    """
    if args is None:
        return None
    elif len(args) == 1:
        return getattr(GL, args[0]) if isinstance(args[0], str) else args[0]
    else:
        return [getattr(GL, i) if isinstance(i, str) else i for i in args]


def getIntegerv(parName):
    """Get a single integer parameter value, return it as a Python integer.

    Parameters
    ----------
    pName : int
        OpenGL property enum to query (e.g. GL_MAJOR_VERSION).

    Returns
    -------
    int

    """
    val = GL.GLint()
    GL.glGetIntegerv(parName, val)

    return int(val.value)


def getFloatv(parName):
    """Get a single float parameter value, return it as a Python float.

    Parameters
    ----------
    pName : float
        OpenGL property enum to query.

    Returns
    -------
    float

    """
    val = GL.GLfloat()
    GL.glGetFloatv(parName, val)

    return float(val.value)


def getString(parName):
    """Get a single string parameter value, return it as a Python UTF-8 string.

    Parameters
    ----------
    pName : int
        OpenGL property enum to query (e.g. GL_VENDOR).

    Returns
    -------
    str

    """
    val = ctypes.cast(GL.glGetString(parName), ctypes.c_char_p).value
    return val.decode('UTF-8')

    
class OpenGLInfo:
    """OpenGL information class.

    This class is used to store information about the OpenGL implementation on
    the current machine. It provides a consistent means of querying the OpenGL
    implementation regardless of the OpenGL interface being used.

    Attributes
    ----------
    vendor : str
        The name of the company responsible for the OpenGL implementation.
    renderer : str
        The name of the renderer.
    version : str
        The version of the OpenGL implementation.
    majorVersion : int
        The major version number of the OpenGL implementation.
    minorVersion : int
        The minor version number of the OpenGL implementation.
    shaderVersion : str
        The version of the GLSL implementation.
    doubleBuffer : int
        Indicates if the OpenGL implementation is double buffered.
    maxTextureSize : int
        The maximum texture size supported by the OpenGL implementation.
    stereo : int
        Indicates if the OpenGL implementation supports stereo rendering.
    maxSamples : int
        The maximum number of samples supported by the OpenGL implementation.
    extensions : list
        A list of supported OpenGL extensions.

    """
    __slots__ = [
        'vendor', 'renderer', 'version', 'shaderVersion', 'doubleBuffer', 
        'maxTextureSize', 'maxTextureUnits', 'stereo', 'maxSamples', 
        'extensions']

    # singleton
    _instance = None

    def __init__(self):
        self.vendor = getString(GL.GL_VENDOR)
        self.renderer = getString(GL.GL_RENDERER)
        self.version = getString(GL.GL_VERSION)
        self.shaderVersion = getString(GL.GL_SHADING_LANGUAGE_VERSION)
        # self.majorVersion = getIntegerv(GL.GL_MAJOR_VERSION)
        # self.minorVersion = getIntegerv(GL.GL_MINOR_VERSION)
        self.doubleBuffer = getIntegerv(GL.GL_DOUBLEBUFFER)
        self.maxTextureSize = getIntegerv(GL.GL_MAX_TEXTURE_SIZE)
        self.maxTextureUnits = getIntegerv(GL.GL_MAX_TEXTURE_IMAGE_UNITS)
        self.stereo = getIntegerv(GL.GL_STEREO)
        self.maxSamples = getIntegerv(GL.GL_MAX_SAMPLES)
        self.extensions = \
            [i for i in getString(GL.GL_EXTENSIONS).split(' ') if i not in ('', ' ')]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenGLInfo, cls).__new__(cls)

        return cls._instance

    def hasExtension(self, extName):
        """Check if the OpenGL implementation supports an extension.

        Parameters
        ----------
        extName : str
            The name of the extension to check for.

        Returns
        -------
        bool
            True if the extension is supported, False otherwise.

        """
        return extName in self.extensions


def getOpenGLInfo():
    """Get general information about the OpenGL implementation on this machine.
    This should provide a consistent means of doing so regardless of the OpenGL
    interface we are using.

    Returns are dictionary with the following fields::

        vendor, renderer, version, majorVersion, minorVersion, doubleBuffer,
        maxTextureSize, stereo, maxSamples, extensions

    Supported extensions are returned as a list in the 'extensions' field. You
    can check if a platform supports an extension by checking the membership of
    the extension name in that list.

    Returns
    -------
    OpenGLInfo

    """
    return OpenGLInfo()


# OpenGL limits for this system
MAX_TEXTURE_UNITS = getOpenGLInfo().maxTextureUnits


# -------------------------------
# Shader Program Helper Functions
# -------------------------------
#

def createProgram():
    """Create an empty program object for shaders.

    Returns
    -------
    int
        OpenGL program object handle retrieved from a `glCreateProgram` call.

    Examples
    --------
    Building a program with vertex and fragment shader attachments::

        myProgram = createProgram()  # new shader object

        # compile vertex and fragment shader sources
        vertexShader = compileShader(vertShaderSource, GL.GL_VERTEX_SHADER)
        fragmentShader = compileShader(fragShaderSource, GL.GL_FRAGMENT_SHADER)

        # attach shaders to program
        attachShader(myProgram, vertexShader)
        attachShader(myProgram, fragmentShader)

        # link the shader, makes `myProgram` attachments executable by their
        # respective processors and available for use
        linkProgram(myProgram)

        # optional, validate the program
        validateProgram(myProgram)

        # optional, detach and discard shader objects
        detachShader(myProgram, vertexShader)
        detachShader(myProgram, fragmentShader)

        deleteObject(vertexShader)
        deleteObject(fragmentShader)

    You can install the program for use in the current rendering state by
    calling::

        useProgram(myShader) # OR glUseProgram(myShader)
        # set uniforms/attributes and start drawing here ...

    """
    return GL.glCreateProgram()


def createProgramObjectARB():
    """Create an empty program object for shaders.

    This creates an *Architecture Review Board* (ARB) program variant which is
    compatible with older GLSL versions and OpenGL coding practices (eg.
    immediate mode) on some platforms. Use *ARB variants of shader helper
    functions (eg. `compileShaderObjectARB` instead of `compileShader`) when
    working with these ARB program objects. This was included for legacy support
    of existing PsychoPy shaders. However, it is recommended that you use
    :func:`createShader` and follow more recent OpenGL design patterns for new
    code (if possible of course).

    Returns
    -------
    int
        OpenGL program object handle retrieved from a `glCreateProgramObjectARB`
        call.

    Examples
    --------
    Building a program with vertex and fragment shader attachments::

        myProgram = createProgramObjectARB()  # new shader object

        # compile vertex and fragment shader sources
        vertexShader = compileShaderObjectARB(
            vertShaderSource, GL.GL_VERTEX_SHADER_ARB)
        fragmentShader = compileShaderObjectARB(
            fragShaderSource, GL.GL_FRAGMENT_SHADER_ARB)

        # attach shaders to program
        attachObjectARB(myProgram, vertexShader)
        attachObjectARB(myProgram, fragmentShader)

        # link the shader, makes `myProgram` attachments executable by their
        # respective processors and available for use
        linkProgramObjectARB(myProgram)

        # optional, validate the program
        validateProgramARB(myProgram)

        # optional, detach and discard shader objects
        detachObjectARB(myProgram, vertexShader)
        detachObjectARB(myProgram, fragmentShader)

        deleteObjectARB(vertexShader)
        deleteObjectARB(fragmentShader)

    Use the program in the current OpenGL state::

        useProgramObjectARB(myProgram)

    """
    return GL.glCreateProgramObjectARB()


def compileShader(shaderSrc, shaderType):
    """Compile shader GLSL code and return a shader object. Shader objects can
    then be attached to programs an made executable on their respective
    processors.

    Parameters
    ----------
    shaderSrc : str, list of str
        GLSL shader source code.
    shaderType : GLenum
        Shader program type (eg. `GL_VERTEX_SHADER`, `GL_FRAGMENT_SHADER`,
        `GL_GEOMETRY_SHADER`, etc.)

    Returns
    -------
    int
        OpenGL shader object handle retrieved from a `glCreateShader` call.

    Examples
    --------
    Compiling GLSL source code and attaching it to a program object::

        # GLSL vertex shader source
        vertexSource = \
            '''
            #version 330 core
            layout (location = 0) in vec3 vertexPos;

            void main()
            {
                gl_Position = vec4(vertexPos, 1.0);
            }
            '''
        # compile it, specifying `GL_VERTEX_SHADER`
        vertexShader = compileShader(vertexSource, GL.GL_VERTEX_SHADER)
        attachShader(myProgram, vertexShader)  # attach it to `myProgram`

    """
    shaderId = GL.glCreateShader(shaderType)

    if isinstance(shaderSrc, (list, tuple,)):
        nSources = len(shaderSrc)
        srcPtr = (ctypes.c_char_p * nSources)()
        srcPtr[:] = [i.encode() for i in shaderSrc]
    else:
        nSources = 1
        srcPtr = ctypes.c_char_p(shaderSrc.encode())

    GL.glShaderSource(
        shaderId,
        nSources,
        ctypes.cast(
            ctypes.byref(srcPtr),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
        None)
    GL.glCompileShader(shaderId)

    result = GL.GLint()
    GL.glGetShaderiv(
        shaderId, GL.GL_COMPILE_STATUS, ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to compile for whatever reason
        print(getInfoLog(shaderId) + '\n')
        deleteObject(shaderId)
        raise RuntimeError("Shader compilation failed, check log output.")

    return shaderId


def compileShaderObjectARB(shaderSrc, shaderType):
    """Compile shader GLSL code and return a shader object. Shader objects can
    then be attached to programs an made executable on their respective
    processors.

    Parameters
    ----------
    shaderSrc : str, list of str
        GLSL shader source code text.
    shaderType : GLenum
        Shader program type. Must be `*_ARB` enums such as `GL_VERTEX_SHADER_ARB`,
        `GL_FRAGMENT_SHADER_ARB`, `GL_GEOMETRY_SHADER_ARB`, etc.

    Returns
    -------
    int
        OpenGL shader object handle retrieved from a `glCreateShaderObjectARB`
        call.

    """
    shaderId = GL.glCreateShaderObjectARB(shaderType)

    if isinstance(shaderSrc, (list, tuple,)):
        nSources = len(shaderSrc)
        srcPtr = (ctypes.c_char_p * nSources)()
        srcPtr[:] = [i.encode() for i in shaderSrc]
    else:
        nSources = 1
        srcPtr = ctypes.c_char_p(shaderSrc.encode())

    GL.glShaderSourceARB(
        shaderId,
        nSources,
        ctypes.cast(
            ctypes.byref(srcPtr),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_char))),
        None)
    GL.glCompileShaderARB(shaderId)

    result = GL.GLint()
    GL.glGetObjectParameterivARB(
        shaderId, GL.GL_OBJECT_COMPILE_STATUS_ARB, ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to compile for whatever reason
        sys.stderr.write(getInfoLog(shaderId) + '\n')
        deleteObjectARB(shaderId)
        raise RuntimeError("Shader compilation failed, check log output.")

    return shaderId


def embedShaderSourceDefs(shaderSrc, defs):
    """Embed preprocessor definitions into GLSL source code.

    This function generates and inserts ``#define`` statements into existing
    GLSL source code, allowing one to use GLSL preprocessor statements to alter
    program source at compile time.

    Passing ``{'MAX_LIGHTS': 8, 'NORMAL_MAP': False}`` to `defs` will create and
    insert the following ``#define`` statements into `shaderSrc`::

        #define MAX_LIGHTS 8
        #define NORMAL_MAP 0

    As per the GLSL specification, the ``#version`` directive must be specified
    at the top of the file before any other statement (with the exception of
    comments). If a ``#version`` directive is present, generated ``#define``
    statements will be inserted starting at the following line. If no
    ``#version`` directive is found in `shaderSrc`, the statements will be
    prepended to `shaderSrc`.

    Using preprocessor directives, multiple shader program routines can reside
    in the same source text if enclosed by ``#ifdef`` and ``#endif`` statements
    as shown here::

        #ifdef VERTEX
            // vertex shader code here ...
        #endif

        #ifdef FRAGMENT
            // pixel shader code here ...
        #endif

    Both the vertex and fragment shader can be built from the same GLSL code
    listing by setting either ``VERTEX`` or ``FRAGMENT`` as `True`::

        vertexShader = gltools.compileShaderObjectARB(
            gltools.embedShaderSourceDefs(glslSource, {'VERTEX': True}),
            GL.GL_VERTEX_SHADER_ARB)
        fragmentShader = gltools.compileShaderObjectARB(
            gltools.embedShaderSourceDefs(glslSource, {'FRAGMENT': True}),
            GL.GL_FRAGMENT_SHADER_ARB)

    In addition, ``#ifdef`` blocks can be used to prune render code paths. Here,
    this GLSL snippet shows a shader having diffuse color sampled from a texture
    is conditional on ``DIFFUSE_TEXTURE`` being `True`, if not, the material
    color is used instead::

        #ifdef DIFFUSE_TEXTURE
            uniform sampler2D diffuseTexture;
        #endif
        ...
        #ifdef DIFFUSE_TEXTURE
            // sample color from texture
            vec4 diffuseColor = texture2D(diffuseTexture, gl_TexCoord[0].st);
        #else
            // code path for no textures, just output material color
            vec4 diffuseColor = gl_FrontMaterial.diffuse;
        #endif

    This avoids needing to provide two separate GLSL program sources to build
    shaders to handle cases where a diffuse texture is or isn't used.

    Parameters
    ----------
    shaderSrc : str
        GLSL shader source code.
    defs : dict
       Names and values to generate ``#define`` statements. Keys must all be
       valid GLSL preprocessor variable names of type `str`. Values can only be
       `int`, `float`, `str`, `bytes`, or `bool` types. Boolean values `True`
       and `False` are converted to integers `1` and `0`, respectively.

    Returns
    -------
    str
        GLSL source code with ``#define`` statements inserted.

    Examples
    --------
    Defining ``MAX_LIGHTS`` as `8` in a fragment shader program at runtime::

        fragSrc = embedShaderSourceDefs(fragSrc, {'MAX_LIGHTS': 8})
        fragShader = compileShaderObjectARB(fragSrc, GL_FRAGMENT_SHADER_ARB)

    """
    # generate GLSL `#define` statements
    glslDefSrc = ""
    for varName, varValue in defs.items():
        if not isinstance(varName, str):
            raise ValueError("Definition name must be type `str`.")

        if isinstance(varValue, (int, bool,)):
            varValue = int(varValue)
        elif isinstance(varValue, (float,)):
            pass
            #varValue = varValue
        elif isinstance(varValue, bytes):
            varValue = '"{}"'.format(varValue.decode('UTF-8'))
        elif isinstance(varValue, str):
            varValue = '"{}"'.format(varValue)
        else:
            raise TypeError("Invalid type for value of `{}`.".format(varName))

        glslDefSrc += '#define {n} {v}\n'.format(n=varName, v=varValue)

    # find where the `#version` directive occurs
    versionDirIdx = shaderSrc.find("#version")
    if versionDirIdx != -1:
        srcSplitIdx = shaderSrc.find("\n", versionDirIdx) + 1  # after newline
        srcOut = shaderSrc[:srcSplitIdx] + glslDefSrc + shaderSrc[srcSplitIdx:]
    else:
        # no version directive in source, just prepend defines
        srcOut = glslDefSrc + shaderSrc

    return srcOut


def deleteShader(shader):
    """Delete a shader object.

    Parameters
    ----------
    shader : int
        Shader object handle to delete. Must have originated from a
        :func:`compileShader` or `glCreateShader` call.

    """
    GL.glDeleteShader(shader)


def deleteProgram(program):
    """Delete a shader program object.

    Parameters
    ----------
    program : int
        Program object handle to delete. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.

    """
    GL.glDeleteProgram(program)


def deleteObject(obj):
    """Delete a shader or program object.

    Parameters
    ----------
    obj : int
        Shader or program object handle. Must have originated from a
        :func:`createProgram`, :func:`compileShader`, `glCreateProgram` or
        `glCreateShader` call.

    """
    if GL.glIsShader(obj):
        GL.glDeleteShader(obj)
    elif GL.glIsProgram(obj):
        GL.glDeleteProgram(obj)
    else:
        raise ValueError('Cannot delete, not a program or shader object.')


def deleteObjectARB(obj):
    """Delete a program or shader object.

    Parameters
    ----------
    obj : int
        Program handle to attach `shader` to. Must have originated from a
        :func:`createProgramObjectARB`, :func:`compileShaderObjectARB,
        `glCreateProgramObjectARB` or `glCreateShaderObjectARB` call.

    """
    GL.glDeleteObjectARB(obj)


def attachShader(program, shader):
    """Attach a shader to a program.

    Parameters
    ----------
    program : int
        Program handle to attach `shader` to. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.
    shader : int
        Handle of shader object to attach. Must have originated from a
        :func:`compileShader` or `glCreateShader` call.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program object.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glAttachShader(program, shader)


def attachObjectARB(program, shader):
    """Attach a shader object to a program.

    Parameters
    ----------
    program : int
        Program handle to attach `shader` to. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.
    shader : int
        Handle of shader object to attach. Must have originated from a
        :func:`compileShaderObjectARB` or `glCreateShaderObjectARB` call.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program object.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glAttachObjectARB(program, shader)


def detachShader(program, shader):
    """Detach a shader object from a program.

    Parameters
    ----------
    program : int
        Program handle to detach `shader` from. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.
    shader : int
        Handle of shader object to detach. Must have been previously attached
        to `program`.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glDetachShader(program, shader)


def detachObjectARB(program, shader):
    """Detach a shader object from a program.

    Parameters
    ----------
    program : int
        Program handle to detach `shader` from. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.
    shader : int
        Handle of shader object to detach. Must have been previously attached
        to `program`.

    """
    if not GL.glIsProgram(program):
        raise ValueError("Value `program` is not a program.")
    elif not GL.glIsShader(shader):
        raise ValueError("Value `shader` is not a shader object.")
    else:
        GL.glDetachObjectARB(program, shader)


def linkProgram(program):
    """Link a shader program. Any attached shader objects will be made
    executable to run on associated GPU processor units when the program is
    used.

    Parameters
    ----------
    program : int
        Program handle to link. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.

    Raises
    ------
    ValueError
        Specified `program` handle is invalid.
    RuntimeError
        Program failed to link. Log will be dumped to `sterr`.

    """
    if GL.glIsProgram(program):
        GL.glLinkProgram(program)
    else:
        raise ValueError("Value `program` is not a shader program.")

    # check for errors
    result = GL.GLint()
    GL.glGetProgramiv(program, GL.GL_LINK_STATUS, ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to link for whatever reason
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError(
            'Failed to link shader program. Check log output.')


def linkProgramObjectARB(program):
    """Link a shader program object. Any attached shader objects will be made
    executable to run on associated GPU processor units when the program is
    used.

    Parameters
    ----------
    program : int
        Program handle to link. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.

    Raises
    ------
    ValueError
        Specified `program` handle is invalid.
    RuntimeError
        Program failed to link. Log will be dumped to `sterr`.

    """
    if GL.glIsProgram(program):
        GL.glLinkProgramARB(program)
    else:
        raise ValueError("Value `program` is not a shader program.")

    # check for errors
    result = GL.GLint()
    GL.glGetObjectParameterivARB(
        program,
        GL.GL_OBJECT_LINK_STATUS_ARB,
        ctypes.byref(result))

    if result.value == GL.GL_FALSE:  # failed to link for whatever reason
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError(
            'Failed to link shader program. Check log output.')


def validateProgram(program):
    """Check if the program can execute given the current OpenGL state.

    Parameters
    ----------
    program : int
        Handle of program to validate. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call.

    """
    # check validation info
    result = GL.GLint()
    GL.glValidateProgram(program)
    GL.glGetProgramiv(program, GL.GL_VALIDATE_STATUS, ctypes.byref(result))

    if result.value == GL.GL_FALSE:
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError('Shader program validation failed.')


def validateProgramARB(program):
    """Check if the program can execute given the current OpenGL state. If
    validation fails, information from the driver is dumped giving the reason.

    Parameters
    ----------
    program : int
        Handle of program object to validate. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call.

    """
    # check validation info
    result = GL.GLint()
    GL.glValidateProgramARB(program)
    GL.glGetObjectParameterivARB(
        program,
        GL.GL_OBJECT_VALIDATE_STATUS_ARB,
        ctypes.byref(result))

    if result.value == GL.GL_FALSE:
        sys.stderr.write(getInfoLog(program) + '\n')
        raise RuntimeError('Shader program validation failed.')


def useProgram(program):
    """Use a program object's executable shader attachments in the current
    OpenGL rendering state.

    In order to install the program object in the current rendering state, a
    program must have been successfully linked by calling :func:`linkProgram` or
    `glLinkProgram`.

    Parameters
    ----------
    program : int
        Handle of program to use. Must have originated from a
        :func:`createProgram` or `glCreateProgram` call and was successfully
        linked. Passing `0` or `None` disables shader programs.

    Examples
    --------
    Install a program for use in the current rendering state::

        useProgram(myShader)

    Disable the current shader program by specifying `0`::

        useProgram(0)

    """
    if program is None:
        program = 0

    if GL.glIsProgram(program) or program == 0:
        GL.glUseProgram(program)
    else:
        raise ValueError('Specified `program` is not a program object.')


def useProgramObjectARB(program):
    """Use a program object's executable shader attachments in the current
    OpenGL rendering state.

    In order to install the program object in the current rendering state, a
    program must have been successfully linked by calling
    :func:`linkProgramObjectARB` or `glLinkProgramObjectARB`.

    Parameters
    ----------
    program : int
        Handle of program object to use. Must have originated from a
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call and
        was successfully linked. Passing `0` or `None` disables shader programs.

    Examples
    --------
    Install a program for use in the current rendering state::

        useProgramObjectARB(myShader)

    Disable the current shader program by specifying `0`::

        useProgramObjectARB(0)

    Notes
    -----
    Some drivers may support using `glUseProgram` for objects created by calling
    :func:`createProgramObjectARB` or `glCreateProgramObjectARB`.

    """
    if program is None:
        program = 0

    if GL.glIsProgram(program) or program == 0:
        GL.glUseProgramObjectARB(program)
    else:
        raise ValueError('Specified `program` is not a program object.')


def getInfoLog(obj):
    """Get the information log from a shader or program.

    This retrieves a text log from the driver pertaining to the shader or
    program. For instance, a log can report shader compiler output or validation
    results. The verbosity and formatting of the logs are platform-dependent,
    where one driver may provide more information than another.

    This function works with both standard and ARB program object variants.

    Parameters
    ----------
    obj : int
        Program or shader to retrieve a log from. If a shader, the handle must
        have originated from a :func:`compileShader`, `glCreateShader`,
        :func:`createProgramObjectARB` or `glCreateProgramObjectARB` call. If a
        program, the handle must have came from a :func:`createProgram`,
        :func:`createProgramObjectARB`, `glCreateProgram` or
        `glCreateProgramObjectARB` call.

    Returns
    -------
    str
        Information log data. Logs can be empty strings if the driver has no
        information available.

    """
    logLength = GL.GLint()
    if GL.glIsShader(obj) == GL.GL_TRUE:
        GL.glGetShaderiv(
            obj, GL.GL_INFO_LOG_LENGTH, ctypes.byref(logLength))
    elif GL.glIsProgram(obj) == GL.GL_TRUE:
        GL.glGetProgramiv(
            obj, GL.GL_INFO_LOG_LENGTH, ctypes.byref(logLength))
    else:
        raise ValueError(
            "Specified value of `obj` is not a shader or program.")

    logBuffer = ctypes.create_string_buffer(logLength.value)
    GL.glGetShaderInfoLog(obj, logLength, None, logBuffer)

    return logBuffer.value.decode('UTF-8')


def getUniformLocation(program, name, error=True):
    """Get the location of a uniform variable in a shader program.

    Parameters
    ----------
    program : int
        Handle of program to retrieve uniform location. Must have originated
        from a :func:`createProgram`, :func:`createProgramObjectARB`,
        `glCreateProgram` or `glCreateProgramObjectARB` call.
    name : str
        Name of the uniform variable to retrieve the location of.
    error : bool, optional
        Raise an error if the uniform is not found. Default is `True`.

    Returns
    -------
    int
        Location of the uniform variable in the program. If the uniform is not
        found, `-1` is returned.

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")

    if type(name) is not bytes:
        name = bytes(name, 'utf-8')

    loc = GL.glGetUniformLocation(program, name)

    if error:
        if loc == -1:
            raise ValueError(
                "Uniform not found in program, it may not be defined or has "
                "been optimized out by the GLSL compiler.")
        raise ValueError("Uniform '{}' not found in program.".format(name))
    
    return loc


# functions for setting uniform values
_unifValueFuncs = {
    'float': {
        1: GL.glUniform1f,
        2: GL.glUniform2f,
        3: GL.glUniform3f,
        4: GL.glUniform4f
    },
    'int': {
        1: GL.glUniform1i,
        2: GL.glUniform2i,
        3: GL.glUniform3i,
        4: GL.glUniform4i
    },
    'uint': {
        1: GL.glUniform1ui,
        2: GL.glUniform2ui,
        3: GL.glUniform3ui,
        4: GL.glUniform4ui
    }
}
    

def setUniformValue(program, loc, value, unifType='float', 
                    ignoreNotDefined=False):
    """Set a uniform variable value in a shader program.

    This function sets the value of a uniform variable in a shader program to 
    the specified value. The type of the value must match the type of the 
    uniform variable in the shader program. The location of the uniform variable 
    can be specified as an integer or string name. If the uniform variable is 
    not found in the program, a `ValueError` is raised.

    Parameters
    ----------
    program : int
        Handle of program to set the uniform value. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    loc : str or int
        Location of the uniform variable in the program obtained from a
        :func:`getUniformLocation` call. You may also specify the name of the
        uniform variable as a string to look-up the location before setting.
    value : int, float, list, tuple, numpy.ndarray
        Value to set the uniform to. The type of the value must match the type
        of the uniform variable in the shader program.
    unifType : str, optional
        Type of the uniform value elements. This is used to determine the 
        appropritate setter function. Must be one of 'float', 'int' or 'uint'.
    ignoreNotDefined : bool, optional
        Do not raise an error if the uniform is not found in the program.
        Default is `False`.

    Notes
    -----
    * If you get a "Invalid operation. The specified operation is not allowed in 
      the current state" error, it is likely that the shader program is not 
      currently in use or the data is not the correct type or length. Make sure
      the `unifType` matches the type of the uniform variable in the shader and 
      the length of the data matches the dimensions of the uniform variable.

    Examples
    --------
    Set a single float uniform value::

        # define uniform in shader as `uniform float myFloat;`
        setUniformValue(myProgram, 'myFloat', 0.5)

    Set a 3-element float vector uniform value::

        # define uniform in shader as `uniform vec3 myVec3;`
        setUniformValue(myProgram, 'myVec3', [0.5, 0.2, 0.8])

    Set an integer uniform value (eg. texture unit index)::

        # define uniform in shader as `uniform sampler2d colorTexture;`
        setUniformValue(myProgram, 'colorTexture', 0, unifType='int')
    
    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")
    
    if isinstance(loc, bytes):
        loc = GL.glGetUniformLocation(program, loc)
    elif isinstance(loc, str):
        loc = GL.glGetUniformLocation(program, bytes(loc, 'utf-8'))
    else:
        if not isinstance(loc, int):
            raise ValueError("Invalid type for uniform location.")

    if loc == -1:
        if ignoreNotDefined:
            return  # ignore if not found
        raise ValueError("Uniform '{}' not found in program.".format(loc))
    
    # handle scalar values
    if isinstance(value, (float, int)):
        if unifType == 'float':
            GL.glUniform1f(loc, float(value))
        elif unifType == 'int':
            GL.glUniform1i(loc, int(value))
        elif unifType == 'uint':
            if value < 0:
                raise ValueError(
                    "Invalid unsigned integer value, must be >= 0.")
            GL.glUniform1ui(loc, int(value))
        else:
            raise ValueError("Invalid uniform value type.")
        return
    
    # passed as list, tuple or numpy array
    unifLen = len(value)
    if unifLen > 4:
        raise ValueError("Invalid uniform data length, must be 1-4 elements.")

    unifSetFunc = _unifValueFuncs[unifType].get(unifLen, None)
    if unifSetFunc is None:
        raise ValueError("Invalid uniform data length.")

    unifSetFunc(loc, *value)


def setUniformSampler2D(program, loc, unit, ignoreNotDefined=False):
    """Set a 2D texture sampler uniform value in a shader program.

    Parameters
    ----------
    program : int
        Handle of program to set the uniform value. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    loc : str or int
        Location of the uniform variable in the program obtained from a
        :func:`getUniformLocation` call. You may also specify the name of the
        uniform variable as a string to look-up the location before setting.
    unit : int
        Texture unit index to bind to the sampler uniform.
    ignoreNotDefined : bool, optional
        Do not raise an error if the uniform is not found in the program.
        Default is `False`.

    Examples
    --------
    Set a 2D texture sampler uniform value::

        # define uniform in shader as `uniform sampler2D colorTexture;`
        setUniformSampler2D(myProgram, 'colorTexture', 0)
    
    Use the enum value for the texture unit::

        setUniformSampler2D(myProgram, 'colorTexture', GL.GL_TEXTURE0)
        # or ...
        setUniformSampler2D(myProgram, 'colorTexture', 'GL_TEXTURE0')

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")
    
    if isinstance(loc, bytes):
        loc = GL.glGetUniformLocation(program, loc)
    elif isinstance(loc, str):
        loc = GL.glGetUniformLocation(program, bytes(loc, 'utf-8'))
    else:
        if not isinstance(loc, int):
            raise ValueError("Invalid type for uniform location.")

    if loc == -1:
        if ignoreNotDefined:
            return  # ignore if not found
        raise ValueError("Uniform '{}' not found in program.".format(loc))
    
    if isinstance(unit, str):
        unit = getattr(GL, unit)

    if unit >= GL.GL_TEXTURE0:  # got enum value
        unit = unit - GL.GL_TEXTURE0
    
    GL.glUniform1i(loc, unit)


# lookup table for matrix uniform setter functions, the keys are hashable 
# tuples of the matrix dimensions
_unifMatrixFuncs = {
        (2, 2): GL.glUniformMatrix2fv,
        (3, 3): GL.glUniformMatrix3fv,
        (4, 4): GL.glUniformMatrix4fv,
        (2, 3): GL.glUniformMatrix2x3fv,
        (3, 2): GL.glUniformMatrix3x2fv,
        (2, 4): GL.glUniformMatrix2x4fv,
        (4, 2): GL.glUniformMatrix4x2fv,
        (3, 4): GL.glUniformMatrix3x4fv,
        (4, 3): GL.glUniformMatrix4x3fv
}


def setUniformMatrix(program, loc, value, transpose=False, 
                     ignoreNotDefined=False):
    """Set the value of a matrix uniform variable in a shader program.

    Arrays are converted to contiguous arrays with 'float32' data type before
    setting.

    Parameters
    ----------
    program : int
        Handle of program to set the uniform value. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    loc : str or int
        Location of the uniform variable in the program obtained from a
        :func:`getUniformLocation` call. You may also specify the name of the
        uniform variable as a string to look-up the location before setting.
    value : numpy.ndarray
        Matrix value to set the uniform to. The shape of the matrix must match
        the dimensions of the uniform variable in the shader program. The data
        type of the matrix must be `float32` or else it will be cast to 
        `float32`.
    transpose : bool, optional
        Transpose the matrix before setting. Default is `False`.
    ignoreNotDefined : bool, optional
        Do not raise an error if the uniform is not found in the program.
        Default is `False`.

    Notes
    -----
    * If you get a "Invalid operation. The specified operation is not allowed in 
      the current state" error, it is likely that the shader program is not 
      currently in use or the data is not the correct type or length. Make sure
      the `unifType` matches the type of the uniform variable in the shader and 
      the length of the data matches the dimensions of the uniform variable.

    Examples
    --------
    Set a 4x4 matrix uniform value::

        # define uniform in shader as `uniform mat4 projectionMatrix;`
        setUniformMatrix(myProgram, 'projectionMatrix', np.eye(4))

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")
    
    locInput = loc  # for error message
    if isinstance(loc, bytes):
        loc = GL.glGetUniformLocation(program, loc)
    elif isinstance(loc, str):
        loc = GL.glGetUniformLocation(program, bytes(loc, 'utf-8'))
    else:
        if not isinstance(loc, int):
            raise ValueError("Invalid type for uniform location.")

    if loc == -1:
        if ignoreNotDefined:
            return  # ignore if not found
        raise ValueError((
            "Uniform '{}' not found in program. It is either not defined "
            "or it is unused.").format(locInput))

    # convert to contiguous array
    value = np.ascontiguousarray(value, dtype=np.float32)

    # handle scalar values
    matrixFunc = _unifMatrixFuncs.get(value.shape, None)
    if matrixFunc is None:
        raise ValueError("Invalid matrix dimensions")
    
    transpose = GL.GL_TRUE if transpose else GL.GL_FALSE

    # recast as pointer
    matrixFunc(loc, 1, transpose, value.ctypes.data_as(
        ctypes.POINTER(GL.GLfloat)))


def getUniformLocations(program, builtins=False):
    """Get uniform names and locations from a given shader program object.

    This function works with both standard and ARB program object variants.

    Parameters
    ----------
    program : int
        Handle of program to retrieve uniforms. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    builtins : bool, optional
        Include built-in GLSL uniforms (eg. `gl_ModelViewProjectionMatrix`).
        Default is `False`.

    Returns
    -------
    dict
        Uniform names and locations.

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")

    arraySize = GL.GLint()
    nameLength = GL.GLsizei()

    # cache uniform locations to avoid looking them up before setting them
    nUniforms = GL.GLint()
    GL.glGetProgramiv(program, GL.GL_ACTIVE_UNIFORMS, ctypes.byref(nUniforms))

    unifLoc = None
    if nUniforms.value > 0:
        maxUniformLength = GL.GLint()
        GL.glGetProgramiv(
            program,
            GL.GL_ACTIVE_UNIFORM_MAX_LENGTH,
            ctypes.byref(maxUniformLength))

        unifLoc = {}
        for uniformIdx in range(nUniforms.value):
            unifType = GL.GLenum()
            unifName = (GL.GLchar * maxUniformLength.value)()

            GL.glGetActiveUniform(
                program,
                uniformIdx,
                maxUniformLength,
                ctypes.byref(nameLength),
                ctypes.byref(arraySize),
                ctypes.byref(unifType),
                unifName)

            # get location
            loc = GL.glGetUniformLocation(program, unifName)
            # don't include if -1, these are internal types like 'gl_Vertex'
            if not builtins:
                if loc != -1:
                    unifLoc[unifName.value] = loc
            else:
                unifLoc[unifName.value] = loc

    return unifLoc


def getAttribLocations(program, builtins=False):
    """Get attribute names and locations from the specified program object.

    This function works with both standard and ARB program object variants.

    Parameters
    ----------
    program : int
        Handle of program to retrieve attributes. Must have originated from a
        :func:`createProgram`, :func:`createProgramObjectARB`, `glCreateProgram`
        or `glCreateProgramObjectARB` call.
    builtins : bool, optional
        Include built-in GLSL attributes (eg. `gl_Vertex`). Default is `False`.

    Returns
    -------
    dict
        Attribute names and locations.

    """
    if not GL.glIsProgram(program):
        raise ValueError(
            "Specified value of `program` is not a program object handle.")

    arraySize = GL.GLint()
    nameLength = GL.GLsizei()

    nAttribs = GL.GLint()
    GL.glGetProgramiv(program, GL.GL_ACTIVE_ATTRIBUTES, ctypes.byref(nAttribs))

    attribLoc = None
    if nAttribs.value > 0:
        maxAttribLength = GL.GLint()
        GL.glGetProgramiv(
            program,
            GL.GL_ACTIVE_ATTRIBUTE_MAX_LENGTH,
            ctypes.byref(maxAttribLength))

        attribLoc = {}
        for attribIdx in range(nAttribs.value):
            attribType = GL.GLenum()
            attribName = (GL.GLchar * maxAttribLength.value)()

            GL.glGetActiveAttrib(
                program,
                attribIdx,
                maxAttribLength,
                ctypes.byref(nameLength),
                ctypes.byref(arraySize),
                ctypes.byref(attribType),
                attribName)

            # get location
            loc = GL.glGetAttribLocation(program, attribName.value)
            # don't include if -1, these are internal types like 'gl_Vertex'
            if not builtins:
                if loc != -1:
                    attribLoc[attribName.value] = loc
            else:
                attribLoc[attribName.value] = loc

    return attribLoc

# -----------------------------------
# GL Query Objects
# -----------------------------------


class QueryObjectInfo:
    """Object for querying information. This includes GPU timing information."""
    __slots__ = ['name', 'target']

    def __init__(self, name, target):
        self.name = name
        self.target = target

    def isValid(self):
        """Check if the name associated with this object is valid."""
        return GL.glIsQuery(self.name) == GL.GL_TRUE


def createQueryObject(target=GL.GL_TIME_ELAPSED):
    """Create a GL query object.

    Parameters
    ----------
    target : Glenum or int
        Target for the query.

    Returns
    -------
    QueryObjectInfo
        Query object.

    Examples
    --------

    Get GPU time elapsed executing rendering/GL calls associated with some
    stimuli (this is not the difference in absolute time between consecutive
    `beginQuery` and `endQuery` calls!)::

        # create a new query object
        qGPU = createQueryObject(GL_TIME_ELAPSED)

        beginQuery(query)
        myStim.draw()  # OpenGL calls here
        endQuery(query)

        # get time elapsed in seconds spent on the GPU
        timeRendering = getQueryValue(qGPU) * 1e-9

    You can also use queries to test if vertices are occluded, as their samples
    would be rejected during depth testing::

        drawVAO(shape0, GL_TRIANGLES)  # draw the first object

        # check if the object was completely occluded
        qOcclusion = createQueryObject(GL_ANY_SAMPLES_PASSED)

        # draw the next shape within query context
        beginQuery(qOcclusion)
        drawVAO(shape1, GL_TRIANGLES)  # draw the second object
        endQuery(qOcclusion)

        isOccluded = getQueryValue(qOcclusion) == 1

    This can be leveraged to perform occlusion testing/culling, where you can
    render a `cheap` version of your mesh/shape, then the more expensive version
    if samples were passed.

    """
    result = GL.GLuint()
    GL.glGenQueries(1, ctypes.byref(result))

    return QueryObjectInfo(result, target)


def beginQuery(query):
    """Begin query.

    Parameters
    ----------
    query : QueryObjectInfo
        Query object descriptor returned by :func:`createQueryObject`.

    """
    if isinstance(query, (QueryObjectInfo,)):
        GL.glBeginQuery(query.target, query.name)
    else:
        raise TypeError('Type of `query` must be `QueryObjectInfo`.')


def endQuery(query):
    """End a query.

    Parameters
    ----------
    query : QueryObjectInfo
        Query object descriptor returned by :func:`createQueryObject`,
        previously passed to :func:`beginQuery`.

    """
    if isinstance(query, (QueryObjectInfo,)):
        GL.glEndQuery(query.target)
    else:
        raise TypeError('Type of `query` must be `QueryObjectInfo`.')


def getQuery(query):
    """Get the value stored in a query object.

    Parameters
    ----------
    query : QueryObjectInfo
        Query object descriptor returned by :func:`createQueryObject`,
        previously passed to :func:`endQuery`.

    """
    params = GL.GLuint64(0)
    if isinstance(query, QueryObjectInfo):
        GL.glGetQueryObjectui64v(
            query.name,
            GL.GL_QUERY_RESULT,
            ctypes.byref(params))

        return params.value
    else:
        raise TypeError('Argument `query` must be `QueryObjectInfo` instance.')


def getAbsTimeGPU():
    """Get the absolute GPU time in nanoseconds.

    Returns
    -------
    int
        Time elapsed in nanoseconds since the OpenGL context was fully realized.

    Examples
    --------
    Get the current GPU time in seconds::

        timeInSeconds = getAbsTimeGPU() * 1e-9

    Get the GPU time elapsed::

        t0 = getAbsTimeGPU()
        # some drawing commands here ...
        t1 = getAbsTimeGPU()
        timeElapsed = (t1 - t0) * 1e-9  # take difference, convert to seconds

    """
    global QUERY_COUNTER
    if QUERY_COUNTER is None:
        GL.glGenQueries(1, ctypes.byref(QUERY_COUNTER))

    GL.glQueryCounter(QUERY_COUNTER, GL.GL_TIMESTAMP)

    params = GL.GLuint64(0)
    GL.glGetQueryObjectui64v(
        QUERY_COUNTER,
        GL.GL_QUERY_RESULT,
        ctypes.byref(params))

    return params.value


# -----------------------------------
# Framebuffer Objects (FBO) Functions
# -----------------------------------
#
# The functions below simplify the creation and management of Framebuffer
# Objects (FBOs). FBO are containers for image buffers (textures or
# renderbuffers) frequently used for off-screen rendering.
#

# FBO descriptor
Framebuffer = namedtuple(
    'Framebuffer',
    ['id',
     'target',
     'userData']
)


class FramebufferInfo:
    """Framebuffer object (VBO) descriptor.

    This class only stores information about the FBO it refers to, it does not
    contain any actual array data associated with the FBO. Calling
    :func:`createFBO` returns instances of this class.

    It is recommended to use `gltools` functions :func:`bindFBO`, 
    :func:`unbindFBO` and :func:`deleteFBO` to manage FBOs.

    Parameters
    ----------
    name : int
        Handle of the FBO.
    target : int
        Target of the FBO.
    attachments : dict, optional
        Dictionary of attachments associated with the FBO. The keys are
        attachment points (e.g. GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT, etc.)
        and the values are buffer descriptors (`RenderbufferInfo` or 
        `TexImage2DInfo`).
    sizeHint : tuple, optional
        Size hint for the FBO. This is used to specify the dimensions of logical
        buffers attached to the FBO. The size hint is a tuple of two integers
        (width, height).
    userData : dict, optional
        User-defined data associated with the FBO.  
    
    """
    __slots__ = [
        'name', 'target', '_attachments', 'sizeHint', 'userData', '_lastBound']

    def __init__(self, name, target=GL.GL_FRAMEBUFFER, attachments=None, 
                 sizeHint=None, userData=None):
        self.name = name
        self.target = target
        self._attachments = {} if attachments is None else attachments
        self.sizeHint = sizeHint
        self.userData = userData

        self._lastBound = GL.GLint()

    def __enter__(self):
        GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(self.lastBound))
        GL.glBindFramebuffer(self.fbo.target, self.fbo.id)

    def __exit__(self, exc_type, exc_val, exc_tb):
        GL.glBindFramebuffer(self.fbo.target, self.lastBound.value)

    @property
    def attachments(self):
        """Image buffer attachments associated with the FBO (`dict`).

        Do not modify this dictionary directly. Use :func:`attachImage` to
        attach images to the FBO.

        """
        return self._attachments


def createFBO(attachments=(), sizeHint=None):
    """Create a Framebuffer Object.

    Parameters
    ----------
    attachments : :obj:`list` or :obj:`tuple` of :obj:`tuple`
        Optional attachments to initialize the Framebuffer with. Attachments are
        specified as a list of tuples. Each tuple must contain an attachment
        point (e.g. GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT, etc.) and a
        buffer descriptor type (RenderbufferInfo or TexImage2DInfo). If using a 
        combined depth/stencil format such as GL_DEPTH24_STENCIL8, 
        GL_DEPTH_ATTACHMENT and GL_STENCIL_ATTACHMENT must be passed the same 
        buffer. Alternatively, one can use GL_DEPTH_STENCIL_ATTACHMENT instead. 
        If using multisample buffers, all attachment images must use the same 
        number of samples!. As an example, one may specify attachments as 
        'attachments=((GL.GL_COLOR_ATTACHMENT0, frameTexture), 
        (GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRenderBuffer))'.
    sizeHint : :obj:`tuple`, optional
        Size hint for the FBO. This is used to specify the dimensions of logical
        buffers attached to the FBO. The size hint is a tuple of two integers
        (width, height).

    Returns
    -------
    FramebufferInfo
        Framebuffer descriptor.

    Notes
    -----
        - All buffers must have the same number of samples.
        - The 'userData' field of the returned descriptor is a dictionary that
          can be used to store arbitrary data associated with the FBO.
        - Framebuffers need a single attachment to be complete.

    Examples
    --------
    Create an empty framebuffer with no attachments::

        fbo = createFBO()  # invalid until attachments are added

    Create a render target with multiple color texture attachments::

        fbo = gt.createFBO(sizeHint=(512, 512))
        gt.bindFBO(fbo)
        gt.attachImage(  # color 
            fbo, GL.GL_COLOR_ATTACHMENT0, gt.createTexImage2D(512, 512))
        gt.attachImage(  # normal map
            fbo, GL.GL_COLOR_ATTACHMENT1, gt.createTexImage2D(512, 512))
        gt.attachImage(  # depth/stencil
            fbo, 
            GL.GL_DEPTH_STENCIL_ATTACHMENT, 
            gt.createRenderbuffer(512, 512, GL.GL_DEPTH24_STENCIL8))
        print(gt.isFramebufferComplete(fbo))  # True
        gt.unbindFBO(None)

    Examples of userData some custom function might access::

        fbo.userData['flags'] = ['left_eye', 'clear_before_use']

    Using a depth only texture (for shadow mapping?)::

        depthTex = createTexImage2D(800, 600,
                                    internalFormat=GL.GL_DEPTH_COMPONENT24,
                                    pixelFormat=GL.GL_DEPTH_COMPONENT)
        fbo = createFBO([(GL.GL_DEPTH_ATTACHMENT, depthTex)])  # is valid

        # discard FBO descriptor, just give me the ID
        frameBuffer = createFBO().id

    """
    fboId = GL.GLuint()
    GL.glGenFramebuffers(1, ctypes.byref(fboId))

    # create a framebuffer descriptor
    fboDesc = FramebufferInfo(
        fboId, 
        GL.GL_FRAMEBUFFER, 
        attachments=None,  # set later 
        sizeHint=sizeHint,
        userData=dict())

    # initial attachments for this framebuffer
    if attachments:
        bindFBO(fboDesc)
        for attachPoint, imageBuffer in attachments:
            attachImage(fboDesc, attachPoint, imageBuffer)
        unbindFBO()

    return fboDesc


def attachImage(fbo, attachPoint, imageBuffer):
    """Attach an image to a specified attachment point on the presently bound
    FBO.

    Parameters
    ----------
    fbo : :obj:`FramebufferInfo`
        Framebuffer descriptor to attach buffer to.
    attachPoint :obj:`int`
        Attachment point for 'imageBuffer' (e.g. GL.GL_COLOR_ATTACHMENT0).
    imageBuffer : :obj:`TexImage2D` or :obj:`RenderbufferInfo`
        Framebuffer-attachable buffer descriptor.

    Examples
    --------
    Attach an image to attachment points on the framebuffer::

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fbo)
        attachImage(GL.GL_COLOR_ATTACHMENT0, colorTex)
        attachImage(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, lastBoundFbo)

        # same as above, but using a context manager
        with useFBO(fbo):
            attachImage(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attachImage(GL.GL_DEPTH_STENCIL_ATTACHMENT, depthRb)

    """
    if not isinstance(fbo, FramebufferInfo):
        raise ValueError("Invalid type for `fbo`, must be `FramebufferInfo`.")

    if isinstance(attachPoint, str):
        attachPoint = getattr(GL, attachPoint)

    # get the last framebuffer bound
    lastBound = GL.GLint()
    GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(lastBound))

    # bind the framebuffer
    changeBinding = fbo.name != lastBound.value
    if changeBinding:
        bindFBO(fbo)

    if fbo.sizeHint is not None:
        if (fbo.sizeHint[0] != imageBuffer.width or 
            fbo.sizeHint[1] != imageBuffer.height):
            raise ValueError(
                "Imagebuffer dimensions do not match FBO size hint. Expected "
                "({}, {}), got ({}, {}).".format(
                    fbo.sizeHint[0], fbo.sizeHint[1], 
                    imageBuffer.width, imageBuffer.height))

    # We should also support binding GL names specified as integers. Right now
    # you need as descriptor which contains the target and name for the buffer.
    #
    if isinstance(imageBuffer, (TexImage2DInfo, TexImage2DMultisampleInfo)):
        GL.glFramebufferTexture2D(
            fbo.target,
            attachPoint,
            imageBuffer.target,
            imageBuffer.name, 0)
    elif isinstance(imageBuffer, RenderbufferInfo):
        GL.glFramebufferRenderbuffer(
            fbo.target,
            attachPoint,
            imageBuffer.target,
            imageBuffer.name)
        
    fbo.attachments[attachPoint] = imageBuffer

    # restore the last framebuffer
    if changeBinding:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, lastBound.value)
        

# legacy
attach = attachImage


def isFramebufferComplete(fbo):
    """Check if the currently bound framebuffer is complete.

    Parameters
    ----------
    fbo : :obj:`FramebufferInfo`
        Framebuffer descriptor to check for completeness.

    Returns
    -------
    bool
        `True` if the presently bound FBO is complete.

    """
    # get the last framebuffer bound
    lastBound = GL.GLint()
    GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(lastBound))

    # bind the framebuffer
    changeBinding = fbo.name != lastBound.value
    if changeBinding:
        bindFBO(fbo)

    status = GL.glCheckFramebufferStatus(fbo.target) == \
           GL.GL_FRAMEBUFFER_COMPLETE
    
    # restore the last framebuffer
    if changeBinding:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, lastBound.value)
    
    return status


def deleteFBO(fbo, deleteAttachments=True):
    """Delete a framebuffer.

    Parameters
    ----------
    fbo : :obj:`FramebufferInfo` or :obj:`int`
        Framebuffer descriptor or name to delete.
    deleteAttachments : bool, optional
        Delete attachments associated with the framebuffer. Default is `True`.

    """
    if not isinstance(fbo, FramebufferInfo):
        raise ValueError("Invalid type for `fbo`, must be `FramebufferInfo`.")
    
    if deleteAttachments:
        for attachment in fbo.attachments.values():
            if isinstance(attachment, RenderbufferInfo):
                deleteRenderbuffer(attachment)
            elif isinstance(attachment, 
                            (TexImage2DInfo, TexImage2DMultisampleInfo)):
                deleteTexture(attachment)

    GL.glDeleteFramebuffers(1, fbo.name)

    # invalidate the descriptor
    fbo.name = 0
    fbo.target = 0
    fbo.attachments.clear()


def blitFBO(srcRect, dstRect=None, filter=GL.GL_LINEAR, mask=GL.GL_COLOR_BUFFER_BIT):
    """Copy a block of pixels between framebuffers via blitting. Read and draw
    framebuffers must be bound prior to calling this function. Beware, the
    scissor box and viewport are changed when this is called to dstRect.

    Parameters
    ----------
    srcRect : :obj:`list` of :obj:`int`
        List specifying the top-left and bottom-right coordinates of the region
        to copy from (<X0>, <Y0>, <X1>, <Y1>).
    dstRect : :obj:`list` of :obj:`int` or :obj:`None`
        List specifying the top-left and bottom-right coordinates of the region
        to copy to (<X0>, <Y0>, <X1>, <Y1>). If None, srcRect is used for
        dstRect.
    filter : :obj:`int` or :obj:`str`
        Interpolation method to use if the image is stretched, default is
        GL_LINEAR, but can also be GL_NEAREST.
    mask : :obj:`int` or :obj:`str`
        Bitmask specifying which buffers to copy. Default is GL_COLOR_BUFFER_BIT.

    Examples
    --------
    Blitting pixels from on FBO to another::

        # set buffers for reading and drawing
        gt.setReadBuffer(fbo, 'GL_COLOR_ATTACHMENT0')  
        gt.setDrawBuffer(None, 'GL_BACK')  # default back buffer for window
        gt.blitFBO((0 ,0, 512, 512), (0, 0, 512, 512))
    
    """
    if isinstance(mask, str):
        mask = getattr(GL, mask)

    if isinstance(filter, str):
        filter = getattr(GL, filter)

    # in most cases srcRect and dstRect will be the same.
    if dstRect is None:
        dstRect = srcRect

    GL.glBlitFramebuffer(srcRect[0], srcRect[1], srcRect[2], srcRect[3],
                         dstRect[0], dstRect[1], dstRect[2], dstRect[3],
                         mask,  # colors only for now
                         filter)
    

def setReadBuffer(fbo, mode):
    """Set the read buffer for the framebuffer.

    Parameters
    ----------
    fbo : :obj:`FramebufferInfo` or `None`
        Framebuffer descriptor. If `None`, the framebuffer with target
        `GL_FRAMEBUFFER` is bound to `0` (default framebuffer).
    mode : :obj:`int`, :obj:`GLenum` or :obj:`str`
        Buffer mode to set as the read buffer. If `fbo` is not `None`, this
        value may be `GL_COLOR_ATTACHMENT(i)` where `i` is the color attachment
        index. If `fbo` is `None`, this value may be one of `GL_FRONT_LEFT`,
        `GL_FRONT_RIGHT`, `GL_BACK_LEFT`, `GL_BACK_RIGHT`, `GL_FRONT`,
        `GL_BACK`, `GL_LEFT`, `GL_RIGHT`.

    Examples
    --------
    Set the read buffer for a framebuffer::

        setReadBuffer(fbo, GL_COLOR_ATTACHMENT0)

    """
    if isinstance(mode, str):
        mode = getattr(GL, mode)

    if fbo is None:
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, 0)
        GL.glReadBuffer(mode)
        return

    if not isinstance(fbo, FramebufferInfo):
        raise ValueError(
            "Invalid type for `fbo`, must be `FramebufferInfo`.")

    GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, fbo.name)
    GL.glReadBuffer(mode)


def setDrawBuffer(fbo, mode):
    """Set the draw buffer for the framebuffer.

    Parameters
    ----------
    fbo : :obj:`FramebufferInfo` or `None`
        Framebuffer descriptor. If `None`, the framebuffer with target
        `GL_FRAMEBUFFER` is bound to `0` (default framebuffer).
    mode : :obj:`int`, :obj:`GLenum` or :obj:`str`
        Buffer mode to set as the draw buffer. If `fbo` is not `None`, this
        value may be `GL_COLOR_ATTACHMENT(i)` where `i` is the color attachment
        index. If `fbo` is `None`, this value may be one of `GL_FRONT_LEFT`,
        `GL_FRONT_RIGHT`, `GL_BACK_LEFT`, `GL_BACK_RIGHT`, `GL_FRONT`,
        `GL_BACK`, `GL_LEFT`, `GL_RIGHT`.

    """
    if isinstance(mode, str):
        mode = getattr(GL, mode)

    if fbo is None:
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)
        GL.glDrawBuffer(mode)
        return

    if not isinstance(fbo, FramebufferInfo):
        raise ValueError(
            "Invalid type for `fbo`, must be `FramebufferInfo`.")

    GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, fbo.name)
    GL.glDrawBuffer(mode)


def clearFramebuffer(color=(0.0, 0.0, 0.0, 1.0), depth=None, stencil=None):
    """Clear the presently bound draw buffer.

    Parameters
    ----------
    color : :obj:`tuple`, optional
        Color to clear the framebuffer to. Default is (0.0, 0.0, 0.0, 1.0).
    depth : :obj:`float`, optional
        Depth value to clear the framebuffer to. Default is 1.0.
    stencil : :obj:`int`, optional
        Stencil value to clear the framebuffer to. Default is 0.

    Examples
    --------
    Clear the framebuffer to green::

        setDrawBuffer(fbo, GL_COLOR_ATTACHMENT0)
        clearFramebuffer(color=(0.0, 1.0, 0.0, 1.0))
    
    Clear the window back buffer to black::

        setDrawBuffer(None, GL_BACK)
        clearFramebuffer()

    """
    clearFlags = 0
    if color is not None:
        GL.glClearColor(*color)
        clearFlags |= GL.GL_COLOR_BUFFER_BIT
    if depth is not None:
        GL.glClearDepth(depth)
        clearFlags |= GL.GL_DEPTH_BUFFER_BIT
    if stencil is not None:
        GL.glClearStencil(stencil)
        clearFlags |= GL.GL_STENCIL_BUFFER_BIT

    GL.glClear(clearFlags)


def setViewport(x, y, width, height):
    """Set the viewport for the current render target.

    Parameters
    ----------
    x : :obj:`int`
        X-coordinate of the lower-left corner of the viewport.
    y : :obj:`int`
        Y-coordinate of the lower-left corner of the viewport.
    width : :obj:`int`
        Width of the viewport.
    height : :obj:`int`
        Height of the viewport.

    """
    GL.glViewport(int(x), int(y), int(width), int(height))


def setScissor(x, y, width, height):
    """Set the scissor box for the current render target.

    Parameters
    ----------
    x : :obj:`int`
        X-coordinate of the lower-left corner of the scissor box.
    y : :obj:`int`
        Y-coordinate of the lower-left corner of the scissor box.
    width : :obj:`int`
        Width of the scissor box.
    height : :obj:`int`
        Height of the scissor box.

    """
    GL.glScissor(int(x), int(y), int(width), int(height))


@contextmanager
def useFBO(fbo):
    """Context manager for Framebuffer Object bindings. This function yields
    the framebuffer name as an integer.

    Parameters
    ----------
    fbo :obj:`int` or :obj:`Framebuffer`
        OpenGL Framebuffer Object name/ID or descriptor.

    Yields
    -------
    int
        OpenGL name of the framebuffer bound in the context.

    Examples
    --------
    Using a framebuffer context manager::

        # FBO bound somewhere deep in our code
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, someOtherFBO)

        ...

        # create a new FBO, but we have no idea what the currently bound FBO is
        fbo = createFBO()

        # use a context to bind attachments
        with bindFBO(fbo):
            attach(GL.GL_COLOR_ATTACHMENT0, colorTex)
            attach(GL.GL_DEPTH_ATTACHMENT, depthRb)
            attach(GL.GL_STENCIL_ATTACHMENT, depthRb)
            isComplete = gltools.isComplete()

        # someOtherFBO is still bound!

    """
    prevFBO = GL.GLint()
    GL.glGetIntegerv(GL.GL_FRAMEBUFFER_BINDING, ctypes.byref(prevFBO))
    toBind = fbo.id if isinstance(fbo, FramebufferInfo) else int(fbo)
    GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, toBind)
    try:
        yield toBind
    finally:
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, prevFBO.value)


def bindFBO(fbo, target=None):
    """Bind a Framebuffer Object (FBO).

    Parameters
    ----------
    fbo :obj:`FramebufferInfo`
        OpenGL Framebuffer Object name/ID or descriptor.
    target :obj:`int`, :obj:`GLenum`, :obj:`str` or `None`
        Target to bind the framebuffer to. If `None`, the target of the
        framebuffer descriptor is used. Valid targets are `GL_FRAMEBUFFER`,
        `GL_DRAW_FRAMEBUFFER` and `GL_READ_FRAMEBUFFER`.

    Examples
    --------
    Bind a framebuffer::

        bindFBO(fbo)

    """
    if target is None:
        target = fbo.target if isinstance(fbo, FramebufferInfo) else GL.GL_FRAMEBUFFER

    if isinstance(target, str):
        target = getattr(GL, target)

    if fbo is None:
        GL.glBindFramebuffer(target, 0)
        return

    if not isinstance(fbo, FramebufferInfo):
        raise ValueError("Invalid type for `fbo`, must be `FramebufferInfo`.")

    GL.glBindFramebuffer(fbo.target, fbo.name)


def unbindFBO(fbo, target=None):
    """Unbind a Framebuffer Object (FBO).

    While the last FBO does not have to be unbound explicitly, passing the 
    descriptor of the FBO to this function will ensure the target is unbound.

    Parameters
    ----------
    fbo :obj:`FramebufferInfo` or `None`
        OpenGL Framebuffer Object name/ID or descriptor. If `None`, the 
        frambuffer with target `GL_FRAMEBUFFER` is bound to `0`. Values are
        `GL_FRAMEBUFFER`, `GL_DRAW_FRAMEBUFFER` and `GL_READ_FRAMEBUFFER`.
    target :obj:`int`, :obj:`GLenum`, :obj:`str` or `None`
        Target to unbind the framebuffer from. If `None`, the target of the
        framebuffer descriptor is used.

    Examples
    --------
    Unbind a framebuffer::

        unbindFBO(fbo)

    """
    if target is None:
        target = fbo.target if isinstance(fbo, FramebufferInfo) else GL.GL_FRAMEBUFFER

    if isinstance(target, str):
        target = getattr(GL, target)

    if fbo is None:
        GL.glBindFramebuffer(target, 0)
        return

    if not isinstance(fbo, FramebufferInfo):
        raise ValueError("Invalid type for `fbo`, must be `FramebufferInfo`.")

    GL.glBindFramebuffer(fbo.target, 0)


# ------------------------------
# Renderbuffer Objects Functions
# ------------------------------
#
# The functions below handle the creation and management of Renderbuffers
# Objects.
#

# Renderbuffer descriptor type
Renderbuffer = namedtuple(
    'Renderbuffer',
    ['id',
     'target',
     'width',
     'height',
     'internalFormat',
     'samples',
     'multiSample',  # boolean, check if a texture is multisample
     'userData']  # dictionary for user defined data
)


class RenderbufferInfo:
    """Renderbuffer object descriptor.

    This class only stores information about the Renderbuffer it refers to, it
    does not contain any actual array data associated with the Renderbuffer.
    Calling :func:`createRenderbuffer` returns instances of this class.

    It is recommended to use `gltools` functions :func:`bindRenderbuffer`,
    :func:`unbindRenderbuffer` and :func:`deleteRenderbuffer` to manage
    Renderbuffers.

    Parameters
    ----------
    name : int
        Handle of the Renderbuffer.
    target : int
        Target of the Renderbuffer.
    width : int
        Width of the Renderbuffer.
    height : int
        Height of the Renderbuffer.
    internalFormat : int
        Internal format of the Renderbuffer.
    samples : int
        Number of samples for multi-sampling.
    multiSample : bool
        True if the Renderbuffer is multi-sampled.
    userData : dict, optional
        User-defined data associated with the Renderbuffer.

    """
    __slots__ = ['name', 'target', 'width', 'height', 'internalFormat',
                 'samples', 'multiSample', 'userData']

    def __init__(self, name, target, width, height, internalFormat, samples,
                 multiSample, userData=None):
        self.name = name
        self.target = target
        self.width = width
        self.height = height
        self.internalFormat = internalFormat
        self.samples = samples
        self.multiSample = multiSample
        self.userData = userData


def createRenderbuffer(width, height, internalFormat=GL.GL_RGBA8, samples=1):
    """Create a new Renderbuffer Object with a specified internal format. A
    multisample storage buffer is created if samples > 1.

    Renderbuffers contain image data and are optimized for use as render
    targets. See https://www.khronos.org/opengl/wiki/Renderbuffer_Object for
    more information.

    Parameters
    ----------
    width : :obj:`int`
        Buffer width in pixels.
    height : :obj:`int`
        Buffer height in pixels.
    internalFormat : :obj:`int`
        Format for renderbuffer data (e.g. GL_RGBA8, GL_DEPTH24_STENCIL8).
    samples : :obj:`int`
        Number of samples for multi-sampling, should be >1 and power-of-two.
        If samples == 1, a single sample buffer is created.

    Returns
    -------
    Renderbuffer
        A descriptor of the created renderbuffer.

    Notes
    -----
    The 'userData' field of the returned descriptor is a dictionary that can
    be used to store arbitrary data associated with the buffer.

    """
    internalFormat = _getGLEnum(internalFormat)

    width = int(width)
    height = int(height)

    # create a new renderbuffer ID
    rbId = GL.GLuint()
    GL.glGenRenderbuffers(1, ctypes.byref(rbId))
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rbId)

    if samples > 1:
        # determine if the 'samples' value is valid
        maxSamples = getIntegerv(GL.GL_MAX_SAMPLES)
        if (samples & (samples - 1)) != 0:
            raise ValueError('Invalid number of samples, must be power-of-two.')
        elif samples > maxSamples:
            raise ValueError('Invalid number of samples, must be <{}.'.format(
                maxSamples))

        # create a multisample render buffer storage
        GL.glRenderbufferStorageMultisample(
            GL.GL_RENDERBUFFER,
            samples,
            internalFormat,
            width,
            height)

    else:
        GL.glRenderbufferStorage(
            GL.GL_RENDERBUFFER,
            internalFormat,
            width,
            height)

    # done, unbind it
    GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

    return RenderbufferInfo(rbId,
                            GL.GL_RENDERBUFFER,
                            width,
                            height,
                            internalFormat,
                            samples,
                            samples > 1,
                            dict())


def deleteRenderbuffer(renderBuffer):
    """Free the resources associated with a renderbuffer. This invalidates the
    renderbuffer's ID.

    """
    GL.glDeleteRenderbuffers(1, renderBuffer.name)

    # invalidate the descriptor
    renderBuffer.name = 0


# -----------------
# Texture Functions
# -----------------

# 2D texture descriptor. You can 'wrap' existing texture IDs with TexImage2D to
# use them with functions that require that type as input.
#

class TexImage2DInfo:
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
        The target texture should only be either GL_TEXTURE_2D or
        GL_TEXTURE_RECTANGLE.
    level : :obj:`int`
        LOD number of the texture, should be 0 if GL_TEXTURE_RECTANGLE is the
        target.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
    pixelFormat : :obj:`int`
        Pixel data format (e.g. GL_RGBA, GL_DEPTH_STENCIL)
    dataType : :obj:`int`
        Data type for pixel data (e.g. GL_FLOAT, GL_UNSIGNED_BYTE).
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

    Previous textures are unbound after calling 'createTexImage2D'.

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

    """
    target, internalFormat, pixelFormat, dataType = _getGLEnum( 
        target, internalFormat, pixelFormat, dataType)

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

    GL.glBindTexture(target, texId.value)
    GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, int(unpackAlignment))
    GL.glTexImage2D(target, level, internalFormat,
                    width, height, 0,
                    pixelFormat, dataType, data)
    GL.glGenerateMipmap(target)

    # apply texture parameters
    if texParams is not None:
        for pname, param in texParams.items():
            GL.glTexParameteri(target, pname, param)

    # new texture descriptor
    tex = TexImage2DInfo(
        name=texId.value,
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

    """
    # Attempt to find file with substitution (handles e.g. default.png)
    tryImg = findImageFile(imgFile, checkResources=True)
    if tryImg is not None:
        imgFile = tryImg
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


class TexCubeMap:
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
        Texture width in pixels.
    height : :obj:`int`
        Texture height in pixels.
    level : :obj:`int`
        LOD number of the texture.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
    pixelFormat : :obj:`int`
        Pixel data format (e.g. GL_RGBA, GL_DEPTH_STENCIL)
    dataType : :obj:`int`
        Data type for pixel data (e.g. GL_FLOAT, GL_UNSIGNED_BYTE).
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

    tex = TexCubeMap(name=texId,
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


# def bindTexture(texture, unit=None, enable=True):
#     """Bind a texture.

#     Function binds `texture` to `unit` (if specified). If `unit` is `None`, the
#     texture will be bound but not assigned to a texture unit.

#     Parameters
#     ----------
#     texture : TexImage2DInfo
#         Texture descriptor to bind.
#     unit : int, optional
#         Texture unit to associated the texture with.
#     enable : bool
#         Enable textures upon binding.

#     """
#     if not texture._isBound:
#         if enable:
#             GL.glEnable(texture.target)

#         GL.glBindTexture(texture.target, texture.name)
#         texture._isBound = True

#         if unit is not None:
#             texture._unit = unit
#             GL.glActiveTexture(GL.GL_TEXTURE0 + unit)

#         # update texture parameters if they have been accessed (changed?)
#         if texture._texParamsNeedUpdate:
#             for pname, param in texture._texParams.items():
#                 GL.glTexParameteri(texture.target, pname, param)
#                 texture._texParamsNeedUpdate = False


# def unbindTexture(texture=None):
#     """Unbind a texture.

#     Parameters
#     ----------
#     texture : TexImage2DInfo
#         Texture descriptor to unbind.

#     """
#     if texture._isBound:
#         # set the texture unit
#         if texture._unit is not None:
#             GL.glActiveTexture(GL.GL_TEXTURE0 + texture._unit)
#             texture._unit = None

#         GL.glBindTexture(texture.target, 0)
#         texture._isBound = False

#         GL.glDisable(texture.target)
#     else:
#         raise RuntimeError('Trying to unbind a texture that was not previously'
#                            'bound.')


# Descriptor for 2D mutlisampled texture
TexImage2DMultisample = namedtuple(
    'TexImage2D',
    ['id',
     'target',
     'width',
     'height',
     'internalFormat',
     'samples',
     'multisample',
     'userData'])


class TexImage2DMultisampleInfo:
    """Descriptor for a 2D multisampled texture.

    This class is used for bookkeeping 2D multisampled textures stored in video
    memory. Information about the texture (eg. `width` and `height`) is
    available via class attributes. Attributes should never be modified
    directly.

    """
    __slots__ = ['width',
                 'height',
                 'target',
                 '_name',
                 'internalFormat',
                 'samples',
                 'multisample',
                 'userData']

    def __init__(self,
                 name=0,
                 target=GL.GL_TEXTURE_2D_MULTISAMPLE,
                 width=64,
                 height=64,
                 internalFormat=GL.GL_RGBA8,
                 samples=1,
                 multisample=True,
                 userData=None):
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
        internalFormat : :obj:`int`
            Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
        samples : :obj:`int`
            Number of samples for multi-sampling, should be >1 and power-of-two.
            Work with one sample, but will raise a warning.
        multisample : :obj:`bool`
            True if the texture is multi-sampled.
        userData : :obj:`dict`
            User-defined data associated with the texture.

        """
        self.name = name
        self.width = width
        self.height = height
        self.target = target
        self.internalFormat = internalFormat
        self.samples = samples
        self.multisample = multisample

        if userData is None:
            self.userData = {}
        elif isinstance(userData, dict):
            self.userData = userData
        else:
            raise TypeError('Invalid type for `userData`.')



def createTexImage2DMultisample(width, height,
                                target=GL.GL_TEXTURE_2D_MULTISAMPLE, samples=1,
                                internalFormat=GL.GL_RGBA8, texParameters=()):
    """Create a 2D multisampled texture.

    Parameters
    ----------
    width : :obj:`int`
        Texture width in pixels.
    height : :obj:`int`
        Texture height in pixels.
    target : :obj:`int`
        The target texture (e.g. GL_TEXTURE_2D_MULTISAMPLE).
    samples : :obj:`int`
        Number of samples for multi-sampling, should be >1 and power-of-two.
        Work with one sample, but will raise a warning.
    internalFormat : :obj:`int`
        Internal format for texture data (e.g. GL_RGBA8, GL_R11F_G11F_B10F).
    texParameters : :obj:`list` of :obj:`tuple` of :obj:`int`
        Optional texture parameters specified as a list of tuples. These values
        are passed to 'glTexParameteri'. Each tuple must contain a parameter
        name and value. For example, texParameters=[(GL.GL_TEXTURE_MIN_FILTER,
        GL.GL_LINEAR), (GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)]

    Returns
    -------
    TexImage2DMultisampleInfo
        A TexImage2DMultisampleInfo descriptor.

    """
    width = int(width)
    height = int(height)

    if width <= 0 or height <= 0:
        raise ValueError("Invalid image dimensions {} x {}.".format(
            width, height))

    # determine if the 'samples' value is valid
    maxSamples = getIntegerv(GL.GL_MAX_SAMPLES)
    if (samples & (samples - 1)) != 0:
        raise ValueError('Invalid number of samples, must be power-of-two.')
    elif samples <= 0 or samples > maxSamples:
        raise ValueError('Invalid number of samples, must be <{}.'.format(
            maxSamples))

    colorTexId = GL.GLuint()
    GL.glGenTextures(1, ctypes.byref(colorTexId))
    GL.glBindTexture(target, colorTexId)
    GL.glTexImage2DMultisample(
        target, samples, internalFormat, width, height, GL.GL_TRUE)

    # apply texture parameters
    if texParameters:
        for pname, param in texParameters:
            GL.glTexParameteri(target, pname, param)

    GL.glBindTexture(target, 0)

    return TexImage2DMultisampleInfo(
        colorTexId,
        target,
        width,
        height,
        internalFormat,
        samples,
        True,
        dict())


def deleteTexture(texture):
    """Free the resources associated with a texture. This invalidates the
    texture's ID.

    """
    if not texture._isBound:
        GL.glDeleteTextures(1, texture.name)
        texture.name = 0  # invalidate
    else:
        raise RuntimeError("Attempting to delete texture which is presently "
                           "bound.")


# --------------------------
# Vertex Array Objects (VAO)
#

class VertexArrayInfo:
    """Vertex array object (VAO) descriptor.

    This class only stores information about the VAO it refers to, it does not
    contain any actual array data associated with the VAO. Calling
    :func:`createVAO` returns instances of this class.

    If `isLegacy` is `True`, attribute binding states are using deprecated (but
    still supported) pointer definition calls (eg. `glVertexPointer`). This is
    to ensure backwards compatibility. The keys stored in `activeAttribs` must
    be `GLenum` types such as `GL_VERTEX_ARRAY`.

    Parameters
    ----------
    name : int
        OpenGL handle for the VAO.
    count : int
        Number of vertex elements. If `indexBuffer` is not `None`, count
        corresponds to the number of elements in the index buffer.
    activeAttribs : dict
        Attributes and buffers defined as part of this VAO state. Keys are
        attribute pointer indices or capabilities (ie. GL_VERTEX_ARRAY).
        Modifying these values will not update the VAO state.
    indexBuffer : VertexBufferInfo, optional
        Buffer object for indices.
    attribDivisors : dict, optional
        Divisors for each attribute.
    isLegacy : bool
        Array pointers were defined using the deprecated OpenGL API. If `True`,
        the VAO may work with older GLSL shaders versions and the fixed-function
        pipeline.
    userData : dict or None, optional
        Optional user defined data associated with this VAO.

    """
    __slots__ = ['name', 'count', 'activeAttribs', 'indexBuffer', 'isLegacy',
                 'userData', 'attribDivisors']

    def __init__(self,
                 name=0,
                 count=0,
                 activeAttribs=None,
                 indexBuffer=None,
                 attribDivisors=None,
                 isLegacy=False,
                 userData=None):
        self.name = name
        self.activeAttribs = activeAttribs
        self.count = count
        self.indexBuffer = indexBuffer
        self.attribDivisors = attribDivisors
        self.isLegacy = isLegacy

        if userData is None:
            self.userData = {}
        elif isinstance(userData, dict):
            self.userData = userData
        else:
            raise TypeError('Invalid type for `userData`.')

    def __hash__(self):
        return hash((self.name, self.isLegacy))

    def __eq__(self, other):
        """Equality test between VAO object names."""
        return self.name == other.name

    def __ne__(self, other):
        """Inequality test between VAO object names."""
        return self.name != other.name


def createVAO(attribBuffers, indexBuffer=None, attribDivisors=None, legacy=False):
    """Create a Vertex Array object (VAO). VAOs store buffer binding states,
    reducing CPU overhead when drawing objects with vertex data stored in VBOs.

    Define vertex attributes within a VAO state by passing a mapping for
    generic attribute indices and VBO buffers.

    Parameters
    ----------
    attribBuffers : dict
        Attributes and associated VBOs to add to the VAO state. Keys are
        vertex attribute pointer indices, values are VBO descriptors to define.
        Values can be `tuples` where the first value is the buffer descriptor,
        the second is the number of attribute components (`int`, either 2, 3 or
        4), the third is the offset (`int`), and the last is whether to
        normalize the array (`bool`).
    indexBuffer : VertexBufferInfo
        Optional index buffer.
    attribDivisors : dict
        Attribute divisors to set. Keys are vertex attribute pointer indices,
        values are the number of instances that will pass between updates of an
        attribute. Setting attribute divisors is only permitted if `legacy` is
        `False`.
    legacy : bool, optional
        Use legacy attribute pointer functions when setting the VAO state. This
        is for compatibility with older GL implementations. Key specified to
        `attribBuffers` must be `GLenum` types such as `GL_VERTEX_ARRAY` to
        indicate the capability to use.

    Examples
    --------
    Create a vertex array object and enable buffer states within it::

        vao = createVAO({0: vertexPos, 1: texCoords, 2: vertexNormals})

    Using an interleaved vertex buffer, all attributes are in the same buffer
    (`vertexAttr`). We need to specify offsets for each attribute by passing a
    buffer in a `tuple` with the second value specifying the offset::

        # buffer with interleaved layout `00011222` per-attribute
        vao = createVAO(
            {0: (vertexAttr, 3),            # size 3, offset 0
             1: (vertexAttr, 2, 3),         # size 2, offset 3
             2: (vertexAttr, 3, 5, True)})  # size 3, offset 5, normalize

    You can mix interleaved and single-use buffers::

        vao = createVAO(
            {0: (vertexAttr, 3, 0), 1: (vertexAttr, 3, 3), 2: vertexColors})

    Specifying an optional index array, this is used for indexed drawing of
    primitives::

        vao = createVAO({0: vertexPos}, indexBuffer=indices)

    The returned `VertexArrayInfo` instance will have attribute
    ``isIndexed==True``.

    Drawing vertex arrays using a VAO, will use the `indexBuffer` if available::

        # draw the array
        drawVAO(vao, mode=GL.GL_TRIANGLES)

    Use legacy attribute pointer bindings when building a VAO for compatibility
    with the fixed-function pipeline and older GLSL versions::

        attribBuffers = {GL_VERTEX_ARRAY: vertexPos, GL_NORMAL_ARRAY: normals}
        vao = createVAO(attribBuffers, legacy=True)

    If you wish to used instanced drawing, you can specify attribute divisors
    this way::

        vao = createVAO(
            {0: (vertexAttr, 3, 0), 1: (vertexAttr, 3, 3), 2: vertexColors},
            attribDivisors={2: 1})

    """
    if not attribBuffers:  # in case an empty list is passed
        raise ValueError("No buffers specified.")

    # create a vertex buffer ID
    vaoId = GL.GLuint()

    if _thisPlatform != 'Darwin':
        GL.glGenVertexArrays(1, ctypes.byref(vaoId))
        GL.glBindVertexArray(vaoId)
    else:
        GL.glGenVertexArraysAPPLE(1, ctypes.byref(vaoId))
        GL.glBindVertexArrayAPPLE(vaoId)

    # add attribute pointers
    activeAttribs = {}
    bufferIndices = []
    for i, buffer in attribBuffers.items():
        if isinstance(i, str):
            i = VERTEX_ATTRIBS.get(i, None)
            if i is None:
                raise ValueError('Invalid attribute name specified.')

        if isinstance(buffer, (list, tuple,)):
            if len(buffer) == 1:
                buffer = buffer[0]  # size 1 tuple or list eg. (buffer,)
                size = buffer.shape[1]
                offset = 0
                normalize = False
            elif len(buffer) == 2:
                buffer, size = buffer
                offset = 0
                normalize = False
            elif len(buffer) == 3:
                buffer, size, offset = buffer
                normalize = False
            elif len(buffer) == 4:
                buffer, size, offset, normalize = buffer
            else:
                raise ValueError('Invalid attribute values.')
        else:
            size = buffer.shape[1]
            offset = 0
            normalize = False

        enableVertexAttribArray(i, legacy)
        setVertexAttribPointer(i, buffer, size, offset, normalize, legacy)

        activeAttribs[i] = buffer
        bufferIndices.append(buffer.shape[0])

    # bind the EBO if available
    if indexBuffer is not None:
        if indexBuffer.target == GL.GL_ELEMENT_ARRAY_BUFFER:
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, indexBuffer.name)
            if len(indexBuffer.shape) > 1:
                count = indexBuffer.shape[0] * indexBuffer.shape[1]
            else:
                count = indexBuffer.shape[0]
        else:
            raise ValueError(
                'Index buffer does not have target `GL_ELEMENT_ARRAY_BUFFER`.')
    else:
        if bufferIndices.count(bufferIndices[0]) != len(bufferIndices):
            warnings.warn(
                'Input arrays have unequal number of rows, using shortest for '
                '`count`.')
            count = min(bufferIndices)
        else:
            count = bufferIndices[0]

    # set attribute divisors
    if attribDivisors is not None:
        if legacy is True:
            raise ValueError(
                'Cannot set attribute divisors when `legacy` is `True.')

        for key, val in attribDivisors.items():
            GL.glVertexAttribDivisor(key, val)

    if _thisPlatform != 'Darwin':
        GL.glBindVertexArray(0)
    else:
        GL.glBindVertexArrayAPPLE(0)

    return VertexArrayInfo(vaoId.value,
                           count,
                           activeAttribs,
                           indexBuffer,
                           attribDivisors,
                           legacy)


# use the appropriate VAO binding function for the platform
if _thisPlatform != 'Darwin':
    _glBindVertexArray = GL.glBindVertexArray
else:
    _glBindVertexArray = GL.glBindVertexArrayAPPLE


def drawVAO(vao, mode=GL.GL_TRIANGLES, start=0, count=None, instanceCount=None,
            flush=False):
    """Draw a vertex array object. Uses `glDrawArrays` or `glDrawElements` if
    `instanceCount` is `None`, or else `glDrawArraysInstanced` or
    `glDrawElementsInstanced` is used.

    Parameters
    ----------
    vao : VertexArrayObject
        Vertex Array Object (VAO) to draw.
    mode : int, optional
        Drawing mode to use (e.g. GL_TRIANGLES, GL_QUADS, GL_POINTS, etc.) for
        rasterization. Default is `GL_TRIANGLES`. Strings can be used for
        convenience (e.g. 'GL_TRIANGLES', 'GL_QUADS', 'GL_POINTS').
    start : int, optional
        Starting index for array elements. Default is `0` which is the beginning
        of the array.
    count : int, optional
        Number of indices to draw from `start`. Must not exceed `vao.count` -
        `start`.
    instanceCount : int or None
        Number of instances to draw. If >0 and not `None`, instanced drawing
        will be used.
    flush : bool, optional
        Flush queued drawing commands before returning.

    Examples
    --------
    Creating a VAO and drawing it::

        # draw the VAO, renders the mesh
        drawVAO(vaoDesc, GL.GL_TRIANGLES)

    """
    if isinstance(mode, str):
        mode = getattr(GL, mode, None)
        if mode is None:
            raise ValueError('Invalid drawing mode specified.')

    # draw the array
    _glBindVertexArray(vao.name)

    if count is None:
        count = vao.count
    else:
        if count > vao.count - start:
            raise ValueError(
                "Value of `count` cannot exceed `{}`.".format(
                    vao.count - start))

    if vao.indexBuffer is not None:
        if instanceCount is None:
            GL.glDrawElements(mode, count, vao.indexBuffer.dataType, start)
        else:
            GL.glDrawElementsInstanced(mode, count, vao.indexBuffer.dataType,
                                       start, instanceCount)
    else:
        if instanceCount is None:
            GL.glDrawArrays(mode, start, count)
        else:
            GL.glDrawArraysInstanced(mode, start, count, instanceCount)

    if flush:
        GL.glFlush()

    # reset
    _glBindVertexArray(0)


def deleteVAO(vao):
    """Delete a Vertex Array Object (VAO). This does not delete array buffers
    bound to the VAO.

    Parameters
    ----------
    vao : VertexArrayInfo
        VAO to delete. All fields in the descriptor except `userData` will be
        reset.

    """
    if not isinstance(vao, VertexArrayInfo):
        raise TypeError('Invalid type for `vao`, must be `VertexArrayInfo`.')
    
    if vao.name:
        GL.glDeleteVertexArrays(1, GL.GLuint(vao.name))
        vao.name = 0
        vao.isLegacy = False
        vao.indexBuffer = None
        vao.activeAttribs = {}
        vao.count = 0


def drawClientArrays(attribBuffers, mode=GL.GL_TRIANGLES, indexBuffer=None):
    """Draw vertex arrays using client-side arrays. 
    
    This is a convenience function for drawing vertex arrays by passing 
    client-side (resident in CPU memory space) arrays to the driver directly. 
    Performance may be suboptimal compared to using VBOs and VAOs, as data
    must be transferred to the GPU each time this function is called. This may
    also stall the rendering pipeline, preventing the GPU from processing
    commands in parallel.

    For best performance, use interleaved arrays for vertex attributes and an
    index buffer. Using an index buffer is optional, but it greatly reduces 
    the amount of data that must be transferred to the GPU.

    Parameters
    ----------
    attribBuffers : dict
        Attributes and associated buffers to draw. Keys are vertex attribute
        pointer indices, values are buffer arrays. Values can be `tuples` where
        the first value is the buffer array, the second is the number of
        attribute components (`int`, either 2, 3 or 4), the third is the offset
        (`int`), and the last is whether to normalize the array (`bool`). Buffer
        arrays may be `numpy` arrays or lists. If lists, the arrays will be
        converted to `numpy` arrays with `float` (`GL_DOUBLE`) data type.
    mode : int
        Drawing mode to use (e.g. GL_TRIANGLES, GL_QUADS, GL_POINTS, etc.) for
        rasterization.
    indexBuffer : VertexBufferInfo
        Optional index buffer. If `None`, `glDrawArrays` is used, else
        `glDrawElements` is used. The index buffer must be a 2D array that is
        appropriately sized for the drawing mode. For example, if `mode` is
        `GL_TRIANGLES`, the index buffer must be a 2D array with 3 columns. The
        index array is always assumed to be of type `GL_UNSIGNED_INT`, it will
        be converted if necessary.

    Examples
    --------
    Drawing vertex arrays using client-side arrays::

        attribArrays = {
            'gl_Vertex': vertexPos,  # vertex positions
            'gl_Color': vertexColors}  # per vertex colors

        drawClientArrays('triangles', attribArrays)

    Drawing using index buffers::

        vertex, normal, texCoord, faces = createAnnulus()  # ring geometry

        # bind and setup shader uniforms here...

        attribs = {
            'gl_Vertex': vertex,
            'gl_Normal': normal,
            'gl_MultiTexCoord0': texCoord}
        
        drawClientArrays('triangles', attribs, indexBuffer=faces)

    Using interleaved arrays is recommended for greater performance, all
    attributes are stored in a single array which reduces the number of 
    binding calls::

        vertex, normal, texCoord, faces = createPlane()  # square
        interleaved, sizes, offsets = interleaveArrays(
            [vertex, normal, texCoord])

        # interleaved array layout: 000111222
        attribs = {}
        for i, attrib in enumerate('gl_Vertex', 'gl_Normal', 'gl_TexCoord'):
            attribs[attrib] = (interleaved, sizes[i], offsets[i])

        drawClientArrays('triangles', attribs, indexBuffer=faces)

    """
    mode = _getGLEnum(mode)
    if mode is None:
        raise ValueError('Invalid drawing mode specified.')

    GL.glEnable(GL.GL_VERTEX_ARRAY)
    GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
    GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)
    GL.glBindVertexArray(0)

    useIndexBuffer = indexBuffer is not None
    if useIndexBuffer:
        # always use unsigned int for index buffer
        indexBuffer = np.ascontiguousarray(indexBuffer, dtype=np.uint32)
        if indexBuffer.ndim != 2:
            raise ValueError('Index buffer must be 2D array.')

    boundArrays = []
    for arrIdx, buffer in attribBuffers.items():
        if isinstance(arrIdx, str):
            arrIdx= VERTEX_ATTRIBS.get(arrIdx, None)
            if arrIdx is None:
                raise ValueError('Invalid attribute name specified.')

        if isinstance(buffer, (list, tuple,)):
            normalize = False
            nVals = len(buffer)
            if nVals == 1:
                buffer = buffer[0]  # size 1 tuple or list eg. (buffer,)
                size = buffer.shape[1]
                offset = 0
            elif nVals == 2:
                buffer, size = buffer
                offset = 0
            elif nVals == 3:
                buffer, size, offset = buffer
            elif nVals == 4:
                buffer, size, offset, normalize = buffer
            else:
                raise ValueError('Invalid attribute values.')
        else:
            size = buffer.shape[1]
            offset = 0
            normalize = False

        # make sure the buffer is contiguous array
        if not isinstance(buffer, np.ndarray): 
            buffer = np.ascontiguousarray(buffer, dtype=float)

        if buffer.ndim != 2:
            raise ValueError(
                'Buffer {} must be 2D array.'.format(arrIdx))
        
        numVertices = buffer.shape[0]
        
        # enable and set attribute pointers
        GL.glEnableVertexAttribArray(arrIdx)
        
        arrayTypes = ARRAY_TYPES.get(buffer.dtype.type, None)
        if arrayTypes is None:
            raise ValueError('Unable to determine data type from buffer.')

        GL.glVertexAttribPointer(
            arrIdx,
            size,
            arrayTypes[0],
            GL.GL_TRUE if normalize else GL.GL_FALSE,
            offset,
            buffer.ctypes)

        boundArrays.append(arrIdx)

    # use the appropriate draw function
    if useIndexBuffer:
        GL.glDrawElements(
            mode, indexBuffer.size, GL.GL_UNSIGNED_INT, indexBuffer.ctypes)
    else:
        GL.glDrawArrays(mode, 0, numVertices)

    for arrIdx in boundArrays:  # unbind arrays
        GL.glDisableVertexAttribArray(arrIdx)
    
    GL.glDisable(GL.GL_VERTEX_ARRAY)


# ---------------------------
# Vertex Buffer Objects (VBO)
#


class VertexBufferInfo:
    """Vertex buffer object (VBO) descriptor.

    This class only stores information about the VBO it refers to, it does not
    contain any actual array data associated with the VBO. Calling
    :func:`createVBO` returns instances of this class.

    It is recommended to use `gltools` functions :func:`bindVBO`,
    :func:`unbindVBO`, :func:`mapBuffer`, etc. when working with these objects.

    Parameters
    ----------
    name : GLuint or int
        OpenGL handle for the buffer.
    target : GLenum or int, optional
        Target used when binding the buffer (e.g. `GL_VERTEX_ARRAY` or
        `GL_ELEMENT_ARRAY_BUFFER`). Default is `GL_VERTEX_ARRAY`)
    usage : GLenum or int, optional
        Usage type for the array (i.e. `GL_STATIC_DRAW`).
    dataType : Glenum, optional
        Data type of array. Default is `GL_FLOAT`.
    size : int, optional
        Size of the buffer in bytes.
    stride : int, optional
        Number of bytes between adjacent attributes. If `0`, values are assumed
        to be tightly packed.
    shape : tuple or list, optional
        Shape of the array used to create this VBO.
    userData : dict, optional
        Optional user defined data associated with the VBO. If `None`,
        `userData` will be initialized as an empty dictionary.

    """
    __slots__ = ['name', 'target', 'usage', 'dataType',
                 'size', 'stride', 'shape', 'userData']

    def __init__(self,
                 name=0,
                 target=GL.GL_ARRAY_BUFFER,
                 usage=GL.GL_STATIC_DRAW,
                 dataType=GL.GL_FLOAT,
                 size=0,
                 stride=0,
                 shape=(0,),
                 userData=None):

        self.name = name
        self.target = target
        self.usage = usage
        self.dataType = dataType
        self.size = size
        self.stride = stride
        self.shape = shape

        if userData is None:
            self.userData = {}
        elif isinstance(userData, dict):
            self.userData = userData
        else:
            raise TypeError('Invalid type for `userData`.')

    def __hash__(self):
        return hash((self.name,
                     self.target,
                     self.dataType,
                     self.usage,
                     self.size,
                     self.shape))

    def __eq__(self, other):
        """Equality test between VBO object names."""
        return self.name == other.name

    def __ne__(self, other):
        """Inequality test between VBO object names."""
        return self.name != other.name

    @property
    def hasBuffer(self):
        """Check if the VBO assigned to `name` is a buffer."""
        if self.name != 0 and GL.glIsBuffer(self.name):
            return True

        return False

    @property
    def isIndex(self):
        """`True` if the buffer referred to by this object is an index array."""
        if self.name != 0 and GL.glIsBuffer(self.name):
            return self.target == GL.GL_ELEMENT_ARRAY_BUFFER

        return False

    def validate(self):
        """Check if the data contained in this descriptor matches what is
        actually present in the OpenGL state.

        Returns
        -------
        bool
            `True` if the information contained in this descriptor matches the
            OpenGL state.

        """
        # fail automatically if these conditions are true
        if self.name == 0 or GL.glIsBuffer(self.name) != GL.GL_TRUE:
            return False

        if self.target == GL.GL_ARRAY_BUFFER:
            bindTarget = GL.GL_VERTEX_ARRAY_BINDING
        elif self.target == GL.GL_ELEMENT_ARRAY_BUFFER:
            bindTarget = GL.GL_ELEMENT_ARRAY_BUFFER_BINDING
        else:
            raise ValueError(
                'Invalid `target` type, must be `GL_ARRAY_BUFFER` or '
                '`GL_ELEMENT_ARRAY_BUFFER`.')

        # get current binding so we don't disturb the current state
        currentVBO = GL.GLint()
        GL.glGetIntegerv(bindTarget, ctypes.byref(currentVBO))

        # bind buffer at name to validate
        GL.glBindBuffer(self.target, self.name)

        # get buffer parameters
        actualSize = GL.GLint()
        GL.glGetBufferParameteriv(
            self.target, GL.GL_BUFFER_SIZE, ctypes.byref(actualSize))
        actualUsage = GL.GLint()
        GL.glGetBufferParameteriv(
            self.target, GL.GL_BUFFER_USAGE, ctypes.byref(actualUsage))

        # check values against those in this object
        isValid = False
        if self.usage == actualUsage.value and self.size == actualSize.value:
            isValid = True

        # return to the original binding
        GL.glBindBuffer(self.target, currentVBO.value)

        return isValid


def createVBO(data,
              target=GL.GL_ARRAY_BUFFER,
              dataType=None,
              usage=GL.GL_STATIC_DRAW):
    """Create an array buffer object (VBO).

    Creates a VBO using input data, usually as a `ndarray` or `list`. Attributes
    common to one vertex should occupy a single row of the `data` array.

    Parameters
    ----------
    data : array_like
        A 2D array of values to write to the array buffer. The data type of the
        VBO is inferred by the type of the array. If the input is a Python
        `list` or `tuple` type, the data type of the array will be `GL_DOUBLE`.
    target : :obj:`int` or :obj:`str`, optional
        Target used when binding the buffer (e.g. `GL_VERTEX_ARRAY` or
        `GL_ELEMENT_ARRAY_BUFFER`). Default is `GL_VERTEX_ARRAY`. Strings may 
        also be used to specify the target, where the following are valid:
        'array' (for `GL_VERTEX_ARRAY`) or 'element_array' (for 
        `GL_ELEMENT_ARRAY_BUFFER`).
    dataType : Glenum or None, optional
        Data type of array. Input data will be recast to an appropriate type if
        necessary. Default is `None`. If `None`, the data type will be
        inferred from the input data.
    usage : GLenum or int, optional
        Usage hint for the array (i.e. `GL_STATIC_DRAW`). This will hint to the
        GL driver how the buffer will be used so it can optimize memory
        allocation and access. Default is `GL_STATIC_DRAW`.

    Returns
    -------
    VertexBufferInfo
        A descriptor with vertex buffer information.

    Examples
    --------
    Creating a vertex buffer object with vertex data::

        # vertices of a triangle
        verts = [[ 1.0,  1.0, 0.0],   # v0
                 [ 0.0, -1.0, 0.0],   # v1
                 [-1.0,  1.0, 0.0]]   # v2

        # load vertices to graphics device, return a descriptor
        vboDesc = createVBO(verts)

    Drawing triangles or quads using vertex buffer data::

        nIndices, vSize = vboDesc.shape  # element size

        bindVBO(vboDesc)
        setVertexAttribPointer(
            GL_VERTEX_ARRAY, vSize, vboDesc.dataType, legacy=True)
        enableVertexAttribArray(GL_VERTEX_ARRAY, legacy=True)

        if vSize == 3:
            drawMode = GL_TRIANGLES
        elif vSize == 4:
            drawMode = GL_QUADS

        glDrawArrays(drawMode, 0, nIndices)
        glFlush()

        disableVertexAttribArray(GL_VERTEX_ARRAY, legacy=True)
        unbindVBO()

    Custom data can be associated with this vertex buffer by specifying
    `userData`::

        myVBO = createVBO(data)
        myVBO.userData['startIdx'] = 14  # first index to draw with

        # use it later
        nIndices, vSize = vboDesc.shape  # element size
        startIdx = myVBO.userData['startIdx']
        endIdx = nIndices - startIdx
        glDrawArrays(GL_TRIANGLES, startIdx, endIdx)
        glFlush()

    """
    target, dataType, usage = _getGLEnum(target, dataType, usage)

    # try and infer the data type if not specified
    if dataType is None:  # get data type from input
        if isinstance(data, (list, tuple)):  # default for Python array types
            dataType = GL.GL_DOUBLE
        elif isinstance(data, np.ndarray):  # numpy arrays
            dataType = data.dtype.type
        else:
            raise ValueError('Could not infer data type from input.')
    
    # get the OpenGL data type and numpy type
    typeVals = ARRAY_TYPES.get(dataType, None)
    if typeVals is None:
        raise ValueError('Invalid data type specified.')

    glEnum, glType, npType = typeVals

    # get the usage hint if a string was passed
    if isinstance(usage, str):
        usage = GL_ENUMS.get(usage, None)
        if usage is None:
            raise ValueError('Invalid `usage` hint string.')
    
    # create the input data array
    data = np.ascontiguousarray(data, dtype=npType)
    
    # get buffer size and pointer
    bufferSize = data.size * ctypes.sizeof(glType)
    if data.ndim > 1:
        bufferStride = data.shape[1] * ctypes.sizeof(glType)
    else:
        bufferStride = 0

    bufferPtr = data.ctypes.data_as(ctypes.POINTER(glType))

    # create a vertex buffer ID
    bufferName = GL.GLuint()
    GL.glGenBuffers(1, ctypes.byref(bufferName))

    # bind and upload
    GL.glBindBuffer(target, bufferName)
    GL.glBufferData(target, bufferSize, bufferPtr, usage)
    GL.glBindBuffer(target, 0)

    vboInfo = VertexBufferInfo(
        bufferName,
        target,
        usage,
        glEnum,
        bufferSize,
        bufferStride,
        data.shape)  # leave userData empty

    return vboInfo


def bindVBO(vbo):
    """Bind a VBO to the current GL state.

    Parameters
    ----------
    vbo : VertexBufferInfo
        VBO descriptor to bind.

    Returns
    -------
    bool
        `True` is the binding state was changed. Returns `False` if the state
        was not changed due to the buffer already  being bound.

    """
    if isinstance(vbo, VertexBufferInfo):
        GL.glBindBuffer(vbo.target, vbo.name)
    else:
        raise TypeError('Specified `vbo` is not a `VertexBufferInfo`.')


def unbindVBO(vbo):
    """Unbind a vertex buffer object (VBO).

    Parameters
    ----------
    vbo : VertexBufferInfo
        VBO descriptor to unbind.

    """
    if isinstance(vbo, VertexBufferInfo):
        GL.glBindBuffer(vbo.target, 0)
    else:
        raise TypeError('Specified `vbo` is not a `VertexBufferInfo`.')


def mapBuffer(vbo, start=0, length=None, read=True, write=True, noSync=False):
    """Map a vertex buffer object to client memory. This allows you to modify
    its contents.

    If planning to update VBO vertex data, make sure the VBO `usage` types are
    `GL_DYNAMIC_*` or `GL_STREAM_*` or else serious performance issues may
    arise.

    Warnings
    --------
    Modifying buffer data must be done carefully, or else system stability may
    be affected. Do not use the returned view `ndarray` outside of successive
    :func:`mapBuffer` and :func:`unmapBuffer` calls. Do not use the mapped
    buffer for rendering until after :func:`unmapBuffer` is called.

    Parameters
    ----------
    vbo : VertexBufferInfo
        Vertex buffer to map to client memory.
    start : int
        Initial index of the sub-range of the buffer to modify.
    length : int or None
        Number of elements of the sub-array to map from `offset`. If `None`, all
        elements to from `offset` to the end of the array are mapped.
    read : bool, optional
        Allow data to be read from the buffer (sets `GL_MAP_READ_BIT`). This is
        ignored if `noSync` is `True`.
    write : bool, optional
        Allow data to be written to the buffer (sets `GL_MAP_WRITE_BIT`).
    noSync : bool, optional
        If `True`, GL will not wait until the buffer is free (i.e. not being
        processed by the GPU) to map it (sets `GL_MAP_UNSYNCHRONIZED_BIT`). The
        contents of the previous storage buffer are discarded and the driver
        returns a new one. This prevents the CPU from stalling until the buffer
        is available.

    Returns
    -------
    ndarray
        View of the data. The type of the returned array is one which best
        matches the data type of the buffer.

    Examples
    --------
    Map a buffer and edit it::

        arr = mapBuffer(vbo)
        arr[:, :] += 2.0  # add 2 to all values
        unmapBuffer(vbo)  # call when done
        # Don't ever modify `arr` after calling `unmapBuffer`. Delete it if
        # necessary to prevent it form being used.
        del arr

    Modify a sub-range of data by specifying `start` and `length`, indices
    correspond to values, not byte offsets::

        arr = mapBuffer(vbo, start=12, end=24)
        arr[:, :] *= 10.0
        unmapBuffer(vbo)

    """
    _, glType, npType = ARRAY_TYPES[vbo.dataType]
    start *= ctypes.sizeof(glType)

    if length is None:
        length = vbo.size
    else:
        length *= ctypes.sizeof(glType)

    accessFlags = GL.GL_NONE
    if noSync:  # if set, don't set GL_MAP_READ_BIT
        accessFlags |= GL.GL_MAP_UNSYNCHRONIZED_BIT
    elif read:
        accessFlags |= GL.GL_MAP_READ_BIT

    if write:
        accessFlags |= GL.GL_MAP_WRITE_BIT

    bindVBO(vbo)  # bind the buffer for mapping

    # get pointer to the buffer
    bufferPtr = GL.glMapBufferRange(
        vbo.target,
        GL.GLintptr(start),
        GL.GLintptr(length),
        accessFlags)

    bufferArray = np.ctypeslib.as_array(
        ctypes.cast(bufferPtr, ctypes.POINTER(glType)),
        shape=vbo.shape)

    return bufferArray


def unmapBuffer(vbo):
    """Unmap a previously mapped buffer. Must be called after :func:`mapBuffer`
    is called and before any drawing operations which use the buffer are
    called. Failing to call this before using the buffer could result in a
    system error.

    Parameters
    ----------
    vbo : VertexBufferInfo
        Vertex buffer descriptor.

    Returns
    -------
    bool
        `True` if the buffer has been successfully modified. If `False`, the
        data was corrupted for some reason and needs to be resubmitted.

    """
    return GL.glUnmapBuffer(vbo.target) == GL.GL_TRUE


@contextmanager
def mappedBuffer(vbo, start=0, length=None, read=True, write=True, noSync=False):
    """Context manager for mapping and unmapping a buffer. This is a convenience
    function for using :func:`mapBuffer` and :func:`unmapBuffer` together.

    Parameters
    ----------
    vbo : VertexBufferInfo
        Vertex buffer to map to client memory.
    start : int
        Initial index of the sub-range of the buffer to modify.
    length : int or None
        Number of elements of the sub-array to map from `offset`. If `None`, all
        elements to from `offset` to the end of the array are mapped.
    read : bool, optional
        Allow data to be read from the buffer (sets `GL_MAP_READ_BIT`). This is
        ignored if `noSync` is `True`.
    write : bool, optional
        Allow data to be written to the buffer (sets `GL_MAP_WRITE_BIT`).
    noSync : bool, optional
        If `True`, GL will not wait until the buffer is free (i.e. not being
        processed by the GPU) to map it (sets `GL_MAP_UNSYNCHRONIZED_BIT`). The
        contents of the previous storage buffer are discarded and the driver
        returns a new one. This prevents the CPU from stalling until the buffer
        is available

    Yields
    ------
    ndarray
        View of the data. The type of the returned array is one which best
        matches the data type of the buffer.

    Examples
    --------
    Using the context manager to map and unmap a buffer::

        with mappedBuffer(vbo) as arr:
            arr[:, :] += 2.0
    
    """
    arr = mapBuffer(vbo, start, length, read, write, noSync)
    yield arr
    unmapBuffer(vbo)


def updateVBO(vbo, data, noSync=False):
    """Update the contents of a VBO with new data. 
    
    This is a convenience function for mapping a buffer, updating the data, and 
    then unmapping it if the data shape matches the buffer shape.

    Parameters
    ----------
    vbo : VertexBufferInfo
        Vertex buffer to update.
    data : array_like
        New data to write to the buffer. The shape of the data must match the
        shape of the buffer.
    noSync : bool, optional
        If `True`, GL will not wait until the buffer is free (i.e. not being
        processed by the GPU) to map it (sets `GL_MAP_UNSYNCHRONIZED_BIT`). The
        contents of the previous storage buffer are discarded and the driver
        returns a new one. This prevents the CPU from stalling until the buffer
        is available.

    Returns
    -------
    bool
        `True` if the buffer has been successfully modified. If `False`, the
        data was corrupted for some reason and needs to be resubmitted.

    Examples
    --------
    Update a VBO with new data::

        # new vertices
        verts = [[ 1.0,  1.0, 0.0],   # v0
                 [ 0.0, -1.0, 0.0],   # v1
                 [-1.0,  1.0, 0.0]]   # v2

        # update the VBO
        updateVBO(vboDesc, verts)

    """
    if not isinstance(data, np.ndarray):  # allow lists, tuples, etc.
        data = np.ascontiguousarray(data)

    if data.shape != vbo.shape:
        raise ValueError('Data shape does not match VBO shape, expected {} '
                         'but got {}.'.format(vbo.shape, data.shape))

    mappedArray = mapBuffer(vbo, noSync=noSync)
    mappedArray[:, :] = data[:, :]  # transfer data to GPU buffer array

    return unmapBuffer(vbo)


def deleteVBO(vbo):
    """Delete a vertex buffer object (VBO).

    Parameters
    ----------
    vbo : VertexBufferInfo
        Descriptor of VBO to delete.

    """
    if not isinstance(vbo, VertexBufferInfo):
        raise TypeError('Invalid type for `vbo`, must be `VertexBufferInfo`.')
    
    if GL.glIsBuffer(vbo.name):
        GL.glDeleteBuffers(1, vbo.name)
        vbo.name = GL.GLuint(0)  # reset the object to invalidate it


def setVertexAttribPointer(index,
                           vbo,
                           size=None,
                           offset=0,
                           normalize=False,
                           legacy=False):
    """Define an array of vertex attribute data with a VBO descriptor.

    In modern OpenGL implementations, attributes are 'generic', where an
    attribute pointer index does not correspond to any special vertex property.
    Usually the usage for an attribute is defined in the shader program. It is
    recommended that shader programs define attributes using the `layout`
    parameters::

        layout (location = 0) in vec3 position;
        layout (location = 1) in vec2 texCoord;
        layout (location = 2) in vec3 normal;

    Setting attribute pointers can be done like this::

        setVertexAttribPointer(0, posVbo)
        setVertexAttribPointer(1, texVbo)
        setVertexAttribPointer(2, normVbo)

    For compatibility with older OpenGL specifications, some drivers will alias
    vertex pointers unless they are explicitly defined in the shader. This
    allows VAOs the be used with the fixed-function pipeline or older GLSL
    versions.

    On nVidia graphics drivers (and maybe others), the following attribute
    pointer indices are aliased with reserved GLSL names:

        * gl_Vertex - 0
        * gl_Normal - 2
        * gl_Color - 3
        * gl_SecondaryColor - 4
        * gl_FogCoord - 5
        * gl_MultiTexCoord0 - 8
        * gl_MultiTexCoord1 - 9
        * gl_MultiTexCoord2 - 10
        * gl_MultiTexCoord3 - 11
        * gl_MultiTexCoord4 - 12
        * gl_MultiTexCoord5 - 13
        * gl_MultiTexCoord6 - 14
        * gl_MultiTexCoord7 - 15

    Specifying `legacy` as `True` will allow for old-style pointer definitions.
    You must specify the capability as a `GLenum` associated with the pointer
    in this case::

        setVertexAttribPointer(GL_VERTEX_ARRAY, posVbo, legacy=True)
        setVertexAttribPointer(GL_TEXTURE_COORD_ARRAY, texVbo, legacy=True)
        setVertexAttribPointer(GL_NORMAL_ARRAY, normVbo, legacy=True)

    Parameters
    ----------
    index : int
        Index of the attribute to modify. If `legacy=True`, this value should
        be a `GLenum` type corresponding to the capability to bind the buffer
        to, such as `GL_VERTEX_ARRAY`, `GL_TEXTURE_COORD_ARRAY`,
        `GL_NORMAL_ARRAY`, etc.
    vbo : VertexBufferInfo
        VBO descriptor.
    size : int, optional
        Number of components per vertex attribute, can be either 1, 2, 3, or 4.
        If `None` is specified, the component size will be inferred from the
        `shape` of the VBO. You must specify this value if the VBO is
        interleaved.
    offset : int, optional
        Starting index of the attribute in the buffer.
    normalize : bool, optional
        Normalize fixed-point format values when accessed.
    legacy : bool, optional
        Use legacy vertex attributes (ie. `GL_VERTEX_ARRAY`,
        `GL_TEXTURE_COORD_ARRAY`, etc.) for backwards compatibility.

    Examples
    --------
    Define a generic attribute from a vertex buffer descriptor::

        # set the vertex location attribute
        setVertexAttribPointer(0, vboDesc)  # 0 is vertex in our shader
        GL.glColor3f(1.0, 0.0, 0.0)  # red triangle

        # draw the triangle
        nIndices, vSize = vboDesc.shape  # element size
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, nIndices)

    If our VBO has interleaved attributes, we can specify `offset` to account
    for that::

        # define interleaved vertex attributes
        #        |     Position    | Texture |   Normals   |
        vQuad = [[ -1.0, -1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # v0
                 [ -1.0,  1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],  # v1
                 [  1.0,  1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0],  # v2
                 [  1.0, -1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0]]  # v3

        # create a VBO with interleaved attributes
        vboInterleaved = createVBO(np.asarray(vQuad, dtype=np.float32))

        # ... before rendering, set the attribute pointers
        GL.glBindBuffer(vboInterleaved.target, vboInterleaved.name)
        gltools.setVertexAttribPointer(
            0, vboInterleaved, size=3, offset=0)  # vertex pointer
        gltools.setVertexAttribPointer(
            8, vboInterleaved, size=2, offset=3)  # texture pointer
        gltools.setVertexAttribPointer(
            3, vboInterleaved, size=3, offset=5)  # normals pointer

        # Note, we specified `bind=False` since we are managing the binding
        # state. It is recommended that you do this when setting up interleaved
        # buffers to avoid re-binding the same buffer.

        # draw red, full screen quad
        GL.glColor3f(1.0, 0.0, 0.0)
        GL.glDrawArrays(GL.GL_QUADS, 0, vboInterleaved.shape[1])

        # call these when done if `enable=True`
        gltools.disableVertexAttribArray(0)
        gltools.disableVertexAttribArray(8)
        gltools.disableVertexAttribArray(1)

        # unbind the buffer
        GL.glBindBuffer(vboInterleaved.target, 0)

    """
    if vbo.target != GL.GL_ARRAY_BUFFER:
        raise ValueError('VBO must have `target` type `GL_ARRAY_BUFFER`.')

    _, glType, _ = ARRAY_TYPES[vbo.dataType]

    if size is None:
        size = vbo.shape[1]

    offset *= ctypes.sizeof(glType)

    bindVBO(vbo)

    if not legacy:
        GL.glEnableVertexAttribArray(index)
        GL.glVertexAttribPointer(
            index,
            size,
            vbo.dataType,
            GL.GL_TRUE if normalize else GL.GL_FALSE,
            vbo.stride,
            offset)
    else:
        GL.glEnableClientState(index)
        if index == GL.GL_VERTEX_ARRAY:
            GL.glVertexPointer(size, vbo.dataType, vbo.stride, offset)
        elif index == GL.GL_NORMAL_ARRAY:
            GL.glNormalPointer(vbo.dataType, vbo.stride, offset)
        elif index == GL.GL_TEXTURE_COORD_ARRAY:
            GL.glTexCoordPointer(size, vbo.dataType, vbo.stride, offset)
        elif index == GL.GL_COLOR_ARRAY:
            GL.glColorPointer(size, vbo.dataType, vbo.stride, offset)
        elif index == GL.GL_SECONDARY_COLOR_ARRAY:
            GL.glSecondaryColorPointer(size, vbo.dataType, vbo.stride, offset)
        elif index == GL.GL_FOG_COORD_ARRAY:
            GL.glFogCoordPointer(vbo.dataType, vbo.stride, offset)
        else:
            raise ValueError('Invalid `index` enum specified.')

    unbindVBO(vbo)


def enableVertexAttribArray(index, legacy=False):
    """Enable a vertex attribute array. Attributes will be used for use by
    subsequent draw operations. Be sure to call :func:`disableVertexAttribArray`
    on the same attribute to prevent currently enabled attributes from affecting
    later rendering.

    Parameters
    ----------
    index : int
        Index of the attribute to enable. If `legacy=True`, this value should
        be a `GLenum` type corresponding to the capability to bind the buffer
        to, such as `GL_VERTEX_ARRAY`, `GL_TEXTURE_COORD_ARRAY`,
        `GL_NORMAL_ARRAY`, etc.
    legacy : bool, optional
        Use legacy vertex attributes (ie. `GL_VERTEX_ARRAY`,
        `GL_TEXTURE_COORD_ARRAY`, etc.) for backwards compatibility.

    """
    if not legacy:
        GL.glEnableVertexAttribArray(index)
    else:
        GL.glEnableClientState(index)


def disableVertexAttribArray(index, legacy=False):
    """Disable a vertex attribute array.

    Parameters
    ----------
    index : int
        Index of the attribute to enable. If `legacy=True`, this value should
        be a `GLenum` type corresponding to the capability to bind the buffer
        to, such as `GL_VERTEX_ARRAY`, `GL_TEXTURE_COORD_ARRAY`,
        `GL_NORMAL_ARRAY`, etc.
    legacy : bool, optional
        Use legacy vertex attributes (ie. `GL_VERTEX_ARRAY`,
        `GL_TEXTURE_COORD_ARRAY`, etc.) for backwards compatibility.

    """
    if not legacy:
        GL.glDisableVertexAttribArray(index)
    else:
        GL.glDisableClientState(index)


# ---------------------------
# Draw settings
#


def activeTexture(unit):
    """Set the active texture unit.

    Parameters
    ----------
    unit : GLenum, int or str
        Texture unit to activate. Values can be `GL_TEXTURE0`, `GL_TEXTURE1`,
        `GL_TEXTURE2`, etc.

    """
    if isinstance(unit, str):
        unit = _getGLEnum(unit)
    else:
        if unit < MAX_TEXTURE_UNITS: 
            unit = GL.GL_TEXTURE0 + unit

    GL.glActiveTexture(unit)


def bindTexture(texture, target=None, unit=None):
    """Bind a texture to a target.

    Parameters
    ----------
    texture : GLuint, int, None, TexImage2DInfo or TexImage2DMultisampleInfo
        Texture to bind. If `None`, the texture will be unbound.
    target : GLenum, int or str, optional
        Target to bind the texture to. Default is `None`. If `None`, and the
        texture is a `TexImage2DInfo` or `TexImage2DMultisampleInfo` object,
        the target will be inferred from the texture object. If specified, the
        value will override the target inferred from the texture. If `None` and
        the texture is an integer, the target will default to `GL_TEXTURE_2D`.
    unit : GLenum, int or None, optional
        Texture unit to bind the texture to, this will also set the active
        texture unit. Default is `None`. If `None`, the texture will be bound to 
        the currently active texture unit.

    """
    if isinstance(target, str):
        target = getattr(GL, target, None)
        if target is None:
            raise ValueError('Invalid target string specified.')
        
    if texture is None:
        texture = 0
    else:
        if isinstance(texture, (TexImage2DInfo, TexImage2DMultisampleInfo)):
            texture = texture.name
            if target is None:
                target = texture.target
        else:
            texture = int(texture)
            if target is None:
                target = GL.GL_TEXTURE_2D

    if unit is not None:     # bind the texture to a specific unit
        activeTexture(unit)
    
    GL.glBindTexture(target, texture)


def setPolygonMode(face, mode):
    """Set the polygon rasterization mode for a face.

    Parameters
    ----------
    face : GLenum or str
        Face to set the polygon mode for. Values can be `GL_FRONT`, `GL_BACK`,
        or `GL_FRONT_AND_BACK`. Strings may also be used to specify the face,
        where the following are valid: 'front' (for `GL_FRONT`), 'back' (for
        `GL_BACK`), and 'front_and_back' (for `GL_FRONT_AND_BACK`).
    mode : GLenum or str
        Polygon rasterization mode. Values can be `GL_POINT`, `GL_LINE`, or
        `GL_FILL`. Strings may also be used to specify the mode, where the
        following are valid: 'point' (for `GL_POINT`), 'line' (for `GL_LINE`),
        and 'fill' (for `GL_FILL`).

    """
    if isinstance(face, str):
        face = getattr(GL, face, None)
        if face is None:
            raise ValueError(
                'Invalid face string specified, got {}.'.format(face))
    if isinstance(mode, str):
        mode = getattr(GL, mode, None)
        if mode is None:
            raise ValueError(
                'Invalid mode string specified, got {}.'.format(mode))
    
    GL.glPolygonMode(face, mode)


def setWireframeDraw(face=GL.GL_FRONT_AND_BACK):
    """Set the rasterization mode to wireframe.

    Successive draw operations will render wireframe polygons (i.e. outlines).

    Parameters
    ----------
    face : GLenum or int, optional
        Faces to apply wireframe to. Values can be `GL_FRONT_AND_BACK`,
        `GL_FRONT` and `GL_BACK`. The default is `GL_FRONT_AND_BACK`. Strings
        may also be used to specify the face, where the following are valid:
        'front' (for `GL_FRONT`), 'back' (for `GL_BACK`), and 'front_and_back'
        (for `GL_FRONT_AND_BACK`).

    """
    if isinstance(face, str):
        face = getattr(GL, face, None)
        if face is None:
            raise ValueError(
                'Invalid face string specified, got {}.'.format(face))
        
    setPolygonMode(face, GL.GL_LINE)


def setFillDraw(face=GL.GL_FRONT_AND_BACK):
    """Set the rasterization mode to fill polygons.

    Successive draw operations will render filled polygons.
    
    Parameters
    ----------
    face : GLenum or int, optional
        Faces to apply fill to. Values can be `GL_FRONT_AND_BACK`, `GL_FRONT`
        and `GL_BACK`. The default is `GL_FRONT_AND_BACK`. Strings may also be
        used to specify the face, where the following are valid: 'front' (for
        `GL_FRONT`), 'back' (for `GL_BACK`), and 'front_and_back' (for
        `GL_FRONT_AND_BACK`).

    """
    if isinstance(face, str):
        face = getattr(GL, face, None)
        if face is None:
            raise ValueError(
                'Invalid face string specified, got {}.'.format(face))
        
    setPolygonMode(face, GL.GL_FILL)


def setDepthTest(enable=True):
    """Enable or disable depth testing.

    Parameters
    ----------
    enable : bool, optional
        Enable or disable depth testing. Default is `True`.

    """
    if enable:
        GL.glEnable(GL.GL_DEPTH_TEST)
    else:
        GL.glDisable(GL.GL_DEPTH_TEST)


def setDepthFunc(func):
    """Set the depth comparison function.

    Parameters
    ----------
    func : GLenum or str
        Depth comparison function. Values can be `GL_NEVER`, `GL_LESS`,
        `GL_EQUAL`, `GL_LEQUAL`, `GL_GREATER`, `GL_NOTEQUAL`, `GL_GEQUAL`, or
        `GL_ALWAYS`. Strings may also be used to specify the function, where
        the following are valid: 'never' (for `GL_NEVER`), 'less' (for `GL_LESS`),
        'equal' (for `GL_EQUAL`), 'lequal' (for `GL_LEQUAL`), 'greater' (for
        `GL_GREATER`), 'notequal' (for `GL_NOTEQUAL`), 'gequal' (for `GL_GEQUAL`),
        and 'always' (for `GL_ALWAYS`).

    """
    func = _getGLEnum(func)
    GL.glDepthFunc(func)


def setDepthMask(enable=True):
    """Enable or disable writing to the depth buffer.

    Parameters
    ----------
    enable : bool, optional
        Enable or disable writing to the depth buffer. Default is `True`.

    """
    if enable:
        GL.glDepthMask(GL.GL_TRUE)
    else:
        GL.glDepthMask(GL.GL_FALSE)


def setDepthRange(near, far):
    """Set the range of depth values.

    Parameters
    ----------
    near : float
        Near clipping plane.
    far : float
        Far clipping plane.

    """
    GL.glDepthRange(near, far)


def setClearColor(color):
    """Set the clear color for the color buffer.

    Parameters
    ----------
    color : array_like
        Color to clear the color buffer with. The color should be in RGBA
        format, where each component is in the range [0, 1].

    """
    GL.glClearColor(*color)


def setClearDepth(depth):
    """Set the clear value for the depth buffer.

    Parameters
    ----------
    depth : float
        Value to clear the depth buffer with.

    """
    GL.glClearDepth(depth)


def enable(enum):
    """Enable a GL capability.

    Parameters
    ----------
    enum : GLenum, int or str
        Capability to enable.

    """
    if isinstance(enum, str):
        enum = getattr(GL, enum, None)

    if enum is None:
        raise ValueError('Invalid capability string specified.')
        
    GL.glEnable(enum)


def disable(enum):
    """Disable a GL capability.

    Parameters
    ----------
    enum : GLenum, int or str
        Capability to disable.

    """
    if isinstance(enum, str):
        enum = getattr(GL, enum, None)
        
    if enum is None:
        raise ValueError('Invalid capability string specified.')
        
    GL.glDisable(enum)


def setLineWidth(width):
    """Set the width of rasterized lines.

    Parameters
    ----------
    width : float
        Width of rasterized lines.

    """
    GL.glLineWidth(width)


def setLineSmooth(enable=True):
    """Enable or disable line antialiasing.

    Parameters
    ----------
    enable : bool, optional
        Enable or disable line antialiasing. Default is `True`.

    """
    if enable:
        GL.glEnable(GL.GL_LINE_SMOOTH)
    else:
        GL.glDisable(GL.GL_LINE_SMOOTH)


def setPointSize(size):
    """Set the size of rasterized points.

    Parameters
    ----------
    size : float
        Size of rasterized points.

    """
    GL.glPointSize(size)


def setPointSmooth(enable=True):
    """Enable or disable point antialiasing.

    Parameters
    ----------
    enable : bool, optional
        Enable or disable point antialiasing. Default is `True`.

    """
    if enable:
        GL.glEnable(GL.GL_POINT_SMOOTH)
    else:
        GL.glDisable(GL.GL_POINT_SMOOTH)


def setMultiSample(enable=True):
    """Enable or disable multisample antialiasing.

    Parameters
    ----------
    enable : bool, optional
        Enable or disable multisample antialiasing. Default is `True`.

    """
    if enable:
        GL.glEnable(GL.GL_MULTISAMPLE)
    else:
        GL.glDisable(GL.GL_MULTISAMPLE)


def setBlend(enable=True):
    """Enable or disable blending.

    Parameters
    ----------
    enable : bool, optional
        Enable or disable blending. Default is `True`.

    """
    if enable:
        GL.glEnable(GL.GL_BLEND)
    else:
        GL.glDisable(GL.GL_BLEND)


def setBlendFunc(srcFactor, dstFactor):
    """Set the blending function for source and destination factors.

    Parameters
    ----------
    srcFactor : GLenum or str
        Source blending factor. Eg. `GL_SRC_ALPHA`.
    dstFactor : GLenum or str
        Destination blending factor. Eg. `GL_ONE_MINUS_SRC_ALPHA`.

    Examples
    --------
    Set the blending function to use source alpha and one minus source alpha::

        setBlendFunc('GL_SRC_ALPHA', 'GL_ONE_MINUS_SRC_ALPHA')

    """
    if isinstance(srcFactor, str):
        srcFactor = getattr(GL, srcFactor, None)
        if srcFactor is None:
            raise ValueError(
                'Invalid enum specified for source factor. Got {}.'.format(
                    srcFactor))
    if isinstance(dstFactor, str):
        dstFactor = getattr(GL, dstFactor, None)
        if dstFactor is None:
            raise ValueError(
                'Invalid enum specified for destination factor. Got {}.'.format(
                    dstFactor))
        
    GL.glBlendFunc(srcFactor, dstFactor)


# -------------------------
# Material Helper Functions
# -------------------------
#
# Materials affect the appearance of rendered faces. These helper functions and
# datatypes simplify the creation of materials for rendering stimuli.
#

Material = namedtuple('Material', ['face', 'params', 'textures', 'userData'])


def createMaterial(params=(), textures=(), face=GL.GL_FRONT_AND_BACK):
    """Create a new material.

    Parameters
    ----------

    params : :obj:`list` of :obj:`tuple`, optional
        List of material modes and values. Each mode is assigned a value as
        (mode, color). Modes can be GL_AMBIENT, GL_DIFFUSE, GL_SPECULAR,
        GL_EMISSION, GL_SHININESS or GL_AMBIENT_AND_DIFFUSE. Colors must be
        a tuple of 4 floats which specify reflectance values for each RGBA
        component. The value of GL_SHININESS should be a single float. If no
        values are specified, an empty material will be created.
    textures : :obj:`list` of :obj:`tuple`, optional
        List of texture units and TexImage2D descriptors. These will be written
        to the 'textures' field of the returned descriptor. For example,
        [(GL.GL_TEXTURE0, texDesc0), (GL.GL_TEXTURE1, texDesc1)]. The number of
        texture units per-material is GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS.
    face : :obj:`int`, optional
        Faces to apply material to. Values can be GL_FRONT_AND_BACK, GL_FRONT
        and GL_BACK. The default is GL_FRONT_AND_BACK.

    Returns
    -------
    Material :
        A descriptor with material properties.

    Examples
    --------
    Creating a new material with given properties::

        # The values for the material below can be found at
        # http://devernay.free.fr/cours/opengl/materials.html

        # create a gold material
        gold = createMaterial([
            (GL.GL_AMBIENT, (0.24725, 0.19950, 0.07450, 1.0)),
            (GL.GL_DIFFUSE, (0.75164, 0.60648, 0.22648, 1.0)),
            (GL.GL_SPECULAR, (0.628281, 0.555802, 0.366065, 1.0)),
            (GL.GL_SHININESS, 0.4 * 128.0)])

    Use the material when drawing::

        useMaterial(gold)
        drawVAO( ... )  # all meshes will be gold
        useMaterial(None)  # turn off material when done

    Create a red plastic material, but define reflectance and shine later::

        red_plastic = createMaterial()

        # you need to convert values to ctypes!
        red_plastic.values[GL_AMBIENT] = (GLfloat * 4)(0.0, 0.0, 0.0, 1.0)
        red_plastic.values[GL_DIFFUSE] = (GLfloat * 4)(0.5, 0.0, 0.0, 1.0)
        red_plastic.values[GL_SPECULAR] = (GLfloat * 4)(0.7, 0.6, 0.6, 1.0)
        red_plastic.values[GL_SHININESS] = 0.25 * 128.0

        # set and draw
        useMaterial(red_plastic)
        drawVertexbuffers( ... )  # all meshes will be red plastic
        useMaterial(None)

    """
    # setup material mode/value slots
    matDesc = Material(
        face,
        {mode: None for mode in (
            GL.GL_AMBIENT,
            GL.GL_DIFFUSE,
            GL.GL_SPECULAR,
            GL.GL_EMISSION,
            GL.GL_SHININESS)},
        dict(),
        dict())
    if params:
        for mode, param in params:
            matDesc.params[mode] = \
                (GL.GLfloat * 4)(*param) \
                    if mode != GL.GL_SHININESS else GL.GLfloat(param)
    if textures:
        maxTexUnits = getIntegerv(GL.GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS)
        for unit, texDesc in textures:
            if unit <= GL.GL_TEXTURE0 + (maxTexUnits - 1):
                matDesc.textures[unit] = texDesc
            else:
                raise ValueError("Invalid texture unit enum.")

    return matDesc


class SimpleMaterial:
    """Class representing a simple material.

    This class stores material information to modify the appearance of drawn
    primitives with respect to lighting, such as color (diffuse, specular,
    ambient, and emission), shininess, and textures. Simple materials are
    intended to work with features supported by the fixed-function OpenGL
    pipeline.

    """
    def __init__(self,
                 win=None,
                 diffuseColor=(.5, .5, .5),
                 specularColor=(-1., -1., -1.),
                 ambientColor=(-1., -1., -1.),
                 emissionColor=(-1., -1., -1.),
                 shininess=10.0,
                 colorSpace='rgb',
                 diffuseTexture=None,
                 specularTexture=None,
                 opacity=1.0,
                 contrast=1.0,
                 face='front'):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window` or `None`
            Window this material is associated with, required for shaders and
            some color space conversions.
        diffuseColor : array_like
            Diffuse material color (r, g, b, a) with values between 0.0 and 1.0.
        specularColor : array_like
            Specular material color (r, g, b, a) with values between 0.0 and
            1.0.
        ambientColor : array_like
            Ambient material color (r, g, b, a) with values between 0.0 and 1.0.
        emissionColor : array_like
            Emission material color (r, g, b, a) with values between 0.0 and
            1.0.
        shininess : float
            Material shininess, usually ranges from 0.0 to 128.0.
        colorSpace : float
            Color space for `diffuseColor`, `specularColor`, `ambientColor`, and
            `emissionColor`.
        diffuseTexture : TexImage2DInfo
        specularTexture : TexImage2DInfo
        opacity : float
            Opacity of the material. Ranges from 0.0 to 1.0 where 1.0 is fully
            opaque.
        contrast : float
            Contrast of the material colors.
        face : str
            Face to apply material to. Values are `front`, `back` or `both`.
        """
        self.win = win

        self._diffuseColor = np.zeros((3,), np.float32)
        self._specularColor = np.zeros((3,), np.float32)
        self._ambientColor = np.zeros((3,), np.float32)
        self._emissionColor = np.zeros((3,), np.float32)
        self._shininess = float(shininess)

        # internal RGB values post colorspace conversion
        self._diffuseRGB = np.array((0., 0., 0., 1.), np.float32)
        self._specularRGB = np.array((0., 0., 0., 1.), np.float32)
        self._ambientRGB = np.array((0., 0., 0., 1.), np.float32)
        self._emissionRGB = np.array((0., 0., 0., 1.), np.float32)

        # which faces to apply the material

        if face == 'front':
            self._face = GL.GL_FRONT
        elif face == 'back':
            self._face = GL.GL_BACK
        elif face == 'both':
            self._face = GL.GL_FRONT_AND_BACK
        else:
            raise ValueError("Invalid `face` specified, must be 'front', "
                             "'back' or 'both'.")

        self.colorSpace = colorSpace
        self.opacity = opacity
        self.contrast = contrast

        self.diffuseColor = diffuseColor
        self.specularColor = specularColor
        self.ambientColor = ambientColor
        self.emissionColor = emissionColor

        self._diffuseTexture = diffuseTexture
        self._normalTexture = None

        self._useTextures = False  # keeps track if textures are being used

    @property
    def diffuseTexture(self):
        """Diffuse color of the material."""
        return self._diffuseTexture

    @diffuseTexture.setter
    def diffuseTexture(self, value):
        self._diffuseTexture = value

    @property
    def diffuseColor(self):
        """Diffuse color of the material."""
        return self._diffuseColor

    @diffuseColor.setter
    def diffuseColor(self, value):
        self._diffuseColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='diffuseRGB', colorAttrib='diffuseColor',
                 colorSpaceAttrib='colorSpace')

    @property
    def diffuseRGB(self):
        """Diffuse color of the material."""
        return self._diffuseRGB[:3]

    @diffuseRGB.setter
    def diffuseRGB(self, value):
        # make sure the color we got is 32-bit float
        self._diffuseRGB = np.zeros((4,), np.float32)
        self._diffuseRGB[:3] = (value * self.contrast + 1) / 2.0
        self._diffuseRGB[3] = self.opacity

    @property
    def specularColor(self):
        """Specular color of the material."""
        return self._specularColor

    @specularColor.setter
    def specularColor(self, value):
        self._specularColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='specularRGB', colorAttrib='specularColor',
                 colorSpaceAttrib='colorSpace')

    @property
    def specularRGB(self):
        """Diffuse color of the material."""
        return self._specularRGB[:3]

    @specularRGB.setter
    def specularRGB(self, value):
        # make sure the color we got is 32-bit float
        self._specularRGB = np.zeros((4,), np.float32)
        self._specularRGB[:3] = (value * self.contrast + 1) / 2.0
        self._specularRGB[3] = self.opacity

    @property
    def ambientColor(self):
        """Ambient color of the material."""
        return self._ambientColor

    @ambientColor.setter
    def ambientColor(self, value):
        self._ambientColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='ambientRGB', colorAttrib='ambientColor',
                 colorSpaceAttrib='colorSpace')

    @property
    def ambientRGB(self):
        """Diffuse color of the material."""
        return self._ambientRGB[:3]

    @ambientRGB.setter
    def ambientRGB(self, value):
        # make sure the color we got is 32-bit float
        self._ambientRGB = np.zeros((4,), np.float32)
        self._ambientRGB[:3] = (value * self.contrast + 1) / 2.0
        self._ambientRGB[3] = self.opacity

    @property
    def emissionColor(self):
        """Emission color of the material."""
        return self._emissionColor

    @emissionColor.setter
    def emissionColor(self, value):
        self._emissionColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='emissionRGB', colorAttrib='emissionColor',
                 colorSpaceAttrib='colorSpace')

    @property
    def emissionRGB(self):
        """Diffuse color of the material."""
        return self._emissionRGB[:3]

    @emissionRGB.setter
    def emissionRGB(self, value):
        # make sure the color we got is 32-bit float
        self._emissionRGB = np.zeros((4,), np.float32)
        self._emissionRGB[:3] = (value * self.contrast + 1) / 2.0
        self._emissionRGB[3] = self.opacity

    @property
    def shininess(self):
        return self._shininess

    @shininess.setter
    def shininess(self, value):
        self._shininess = float(value)


def useMaterial(material, useTextures=True):
    """Use a material for proceeding vertex draws.

    Parameters
    ----------
    material : :obj:`Material` or None
        Material descriptor to use. Default material properties are set if None
        is specified. This is equivalent to disabling materials.
    useTextures : :obj:`bool`
        Enable textures. Textures specified in a material descriptor's 'texture'
        attribute will be bound and their respective texture units will be
        enabled. Note, when disabling materials, the value of useTextures must
        match the previous call. If there are no textures attached to the
        material, useTexture will be silently ignored.

    Returns
    -------
    None

    Notes
    -----
    1.  If a material mode has a value of None, a color with all components 0.0
        will be assigned.
    2.  Material colors and shininess values are accessible from shader programs
        after calling 'useMaterial'. Values can be accessed via built-in
        'gl_FrontMaterial' and 'gl_BackMaterial' structures (e.g.
        gl_FrontMaterial.diffuse).

    Examples
    --------
    Use a material when drawing::

        useMaterial(metalMaterials.gold)
        drawVAO( ... )  # all meshes drawn will be gold
        useMaterial(None)  # turn off material when done

    """
    if material is not None:
        GL.glDisable(GL.GL_COLOR_MATERIAL)  # disable color tracking
        face = material._face
        GL.glColorMaterial(face, GL.GL_AMBIENT_AND_DIFFUSE)

        # convert data in light class to ctypes
        diffuse = np.ctypeslib.as_ctypes(material._diffuseRGB)
        specular = np.ctypeslib.as_ctypes(material._specularRGB)
        ambient = np.ctypeslib.as_ctypes(material._ambientRGB)
        emission = np.ctypeslib.as_ctypes(material._emissionRGB)

        # pass values to OpenGL
        GL.glMaterialfv(face, GL.GL_DIFFUSE, diffuse)
        GL.glMaterialfv(face, GL.GL_SPECULAR, specular)
        GL.glMaterialfv(face, GL.GL_AMBIENT, ambient)
        GL.glMaterialfv(face, GL.GL_EMISSION, emission)
        GL.glMaterialf(face, GL.GL_SHININESS, material.shininess)

        # setup textures
        if useTextures and material.diffuseTexture is not None:
            material._useTextures = True
            GL.glEnable(GL.GL_TEXTURE_2D)
            if material.diffuseTexture is not None:
                bindTexture(material.diffuseTexture, 0)
        else:
            material._useTextures = False
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glDisable(GL.GL_TEXTURE_2D)
    else:
        for mode, param in defaultMaterial.params.items():
            GL.glEnable(GL.GL_COLOR_MATERIAL)
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK, mode, param)


def clearMaterial(material):
    """Stop using a material."""
    for mode, param in defaultMaterial.params.items():
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK, mode, param)

    if material._useTextures:
        if material.diffuseTexture is not None:
            unbindTexture(material.diffuseTexture)

        GL.glDisable(GL.GL_TEXTURE_2D)

    GL.glDisable(GL.GL_COLOR_MATERIAL)  # disable color tracking


# -------------------------
# Lighting Helper Functions
# -------------------------

Light = namedtuple('Light', ['params', 'userData'])


def createLight(params=()):
    """Create a point light source.

    """
    # setup light mode/value slots
    lightDesc = Light({mode: None for mode in (
        GL.GL_AMBIENT,
        GL.GL_DIFFUSE,
        GL.GL_SPECULAR,
        GL.GL_POSITION,
        GL.GL_SPOT_CUTOFF,
        GL.GL_SPOT_DIRECTION,
        GL.GL_SPOT_EXPONENT,
        GL.GL_CONSTANT_ATTENUATION,
        GL.GL_LINEAR_ATTENUATION,
        GL.GL_QUADRATIC_ATTENUATION)}, dict())

    # configure lights
    if params:
        for mode, value in params:
            if value is not None:
                if mode in [GL.GL_AMBIENT, GL.GL_DIFFUSE, GL.GL_SPECULAR,
                            GL.GL_POSITION]:
                    lightDesc.params[mode] = (GL.GLfloat * 4)(*value)
                elif mode == GL.GL_SPOT_DIRECTION:
                    lightDesc.params[mode] = (GL.GLfloat * 3)(*value)
                else:
                    lightDesc.params[mode] = GL.GLfloat(value)

    return lightDesc


def useLights(lights, setupOnly=False):
    """Use specified lights in successive rendering operations. All lights will
    be transformed using the present modelview matrix.

    Parameters
    ----------
    lights : :obj:`List` of :obj:`Light` or None
        Descriptor of a light source. If None, lighting is disabled.
    setupOnly : :obj:`bool`, optional
        Do not enable lighting or lights. Specify True if lighting is being
        computed via fragment shaders.

    """
    if lights is not None:
        if len(lights) > getIntegerv(GL.GL_MAX_LIGHTS):
            raise IndexError("Number of lights specified > GL_MAX_LIGHTS.")

        GL.glEnable(GL.GL_NORMALIZE)

        for index, light in enumerate(lights):
            enumLight = GL.GL_LIGHT0 + index
            # light properties
            for mode, value in light.params.items():
                if value is not None:
                    GL.glLightfv(enumLight, mode, value)

            if not setupOnly:
                GL.glEnable(enumLight)

        if not setupOnly:
            GL.glEnable(GL.GL_LIGHTING)
    else:
        # disable lights
        if not setupOnly:
            for enumLight in range(getIntegerv(GL.GL_MAX_LIGHTS)):
                GL.glDisable(GL.GL_LIGHT0 + enumLight)

            GL.glDisable(GL.GL_NORMALIZE)
            GL.glDisable(GL.GL_LIGHTING)


def setAmbientLight(color):
    """Set the global ambient lighting for the scene when lighting is enabled.
    This is equivalent to GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, color)
    and does not contribute to the GL_MAX_LIGHTS limit.

    Parameters
    ----------
    color : :obj:`tuple`
        Ambient lighting RGBA intensity for the whole scene.

    Notes
    -----
    If unset, the default value is (0.2, 0.2, 0.2, 1.0) when GL_LIGHTING is
    enabled.

    """
    GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT, (GL.GLfloat * 4)(*color))


# -------------------------
# 3D Model Helper Functions
# -------------------------
#
# These functions are used in the creation, manipulation and rendering of 3D
# model data.
#


class ObjMeshInfo:
    """Descriptor for mesh data loaded from a Wavefront OBJ file.

    """
    __slots__ = [
        'vertexPos',
        'texCoords',
        'normals',
        'faces',
        'extents',
        'mtlFile']

    def __init__(self,
                 vertexPos=None,
                 texCoords=None,
                 normals=None,
                 faces=None,
                 extents=None,
                 mtlFile=None):

        self.vertexPos = vertexPos
        self.texCoords = texCoords
        self.normals = normals
        self.faces = faces
        self.extents = extents
        self.mtlFile = mtlFile


def loadObjFile(objFile):
    """Load a Wavefront OBJ file (*.obj).

    Loads vertex, normals, and texture coordinates from the provided `*.obj` file
    into arrays. These arrays can be processed then loaded into vertex buffer
    objects (VBOs) for rendering. The `*.obj` file must at least specify vertex
    position data to be loaded successfully. Normals and texture coordinates are
    optional.

    Faces can be either triangles or quads, but not both. Faces are grouped by
    their materials. Index arrays are generated for each material present in the
    file.

    Data from the returned `ObjMeshInfo` object can be used to create vertex
    buffer objects and arrays for rendering. See `Examples` below for details on
    how to do this.

    Parameters
    ----------
    objFile : :obj:`str`
        Path to the `*.OBJ` file to load.

    Returns
    -------
    ObjMeshInfo
        Mesh data.

    See Also
    --------
    loadMtlFile : Load a `*.mtl` file.

    Notes
    -----
    1. This importer should work fine for most sanely generated files. Export
       your model with Blender for best results, even if you used some other
       package to create it.
    2. The mesh cannot contain both triangles and quads.

    Examples
    --------
    Loading a `*.obj` mode from file::

        objModel = loadObjFile('/path/to/file.obj')
        # load the material (*.mtl) file, textures are also loaded
        mtllib = loadMtl('/path/to/' + objModel.mtlFile)

    Creating separate vertex buffer objects (VBOs) for each vertex attribute::

        vertexPosVBO = createVBO(objModel.vertexPos)
        texCoordVBO = createVBO(objModel.texCoords)
        normalsVBO = createVBO(objModel.normals)

    Create vertex array objects (VAOs) to draw the mesh. We create VAOs for each
    face material::

        objVAOs = {}  # dictionary for VAOs
        # for each material create a VAO
        # keys are material names, values are index buffers
        for material, faces in objModel.faces.items():
            # convert index buffer to VAO
            indexBuffer = \
                gltools.createVBO(
                    faces.flatten(),  # flatten face index for element array
                    target=GL.GL_ELEMENT_ARRAY_BUFFER,
                    dataType=GL.GL_UNSIGNED_INT)

            # see `setVertexAttribPointer` for more information about attribute
            # pointer indices
            objVAOs[material] = gltools.createVAO(
                {0: vertexPosVBO,  # 0 = gl_Vertex
                 8: texCoordVBO,   # 8 = gl_MultiTexCoord0
                 2: normalsVBO},   # 2 = gl_Normal
                 indexBuffer=indexBuffer)

            # if using legacy attribute pointers, do this instead ...
            # objVAOs[key] = createVAO({GL_VERTEX_ARRAY: vertexPosVBO,
            #                           GL_TEXTURE_COORD_ARRAY: texCoordVBO,
            #                           GL_NORMAL_ARRAY: normalsVBO},
            #                           indexBuffer=indexBuffer,
            #                           legacy=True)  # this needs to be `True`

    To render the VAOs using `objVAOs` created above, do the following::

        for material, vao in objVAOs.items():
            useMaterial(mtllib[material])
            drawVAO(vao)

        useMaterial(None)  # disable materials when done

    Optionally, you can create a single-storage, interleaved VBO by using
    `numpy.hstack`. On some GL implementations, using single-storage buffers
    offers better performance::

        interleavedData = numpy.hstack(
            (objModel.vertexPos, objModel.texCoords, objModel.normals))
        vertexData = createVBO(interleavedData)

    Creating VAOs with interleaved, single-storage buffers require specifying
    additional information, such as `size` and `offset`::

        objVAOs = {}
        for key, val in objModel.faces.items():
            indexBuffer = \
                gltools.createVBO(
                    faces.flatten(),
                    target=GL.GL_ELEMENT_ARRAY_BUFFER,
                    dataType=GL.GL_UNSIGNED_INT)

            objVAOs[key] = createVAO({0: (vertexData, 3, 0),  # size=3, offset=0
                                      8: (vertexData, 2, 3),  # size=2, offset=3
                                      2: (vertexData, 3, 5),  # size=3, offset=5
                                      indexBuffer=val)

    Drawing VAOs with interleaved buffers is exactly the same as shown before
    with separate buffers.

    """
    # open the file, read it into memory
    with open(objFile, 'r') as f:
        objBuffer = StringIO(f.read())

    mtlFile = None

    # unsorted attribute data lists
    positionDefs = []
    texCoordDefs = []
    normalDefs = []
    vertexAttrs = {}

    # material groups
    materialGroup = None
    materialGroups = {}

    nVertices = nTextureCoords = nNormals = nFaces = 0
    vertexIdx = 0
    # first pass, examine the file and load up vertex attributes
    for line in objBuffer.readlines():
        line = line.strip()  # clean up like
        if line.startswith('v '):
            positionDefs.append(tuple(map(float, line[2:].split(' '))))
            nVertices += 1
        elif line.startswith('vt '):
            texCoordDefs.append(tuple(map(float, line[3:].split(' '))))
            nTextureCoords += 1
        elif line.startswith('vn '):
            normalDefs.append(tuple(map(float, line[3:].split(' '))))
            nNormals += 1
        elif line.startswith('f '):
            faceAttrs = []  # attributes this face
            for attrs in line[2:].split(' '):  # triangle vertex attrs
                if attrs not in vertexAttrs.keys():
                    vertexAttrs[attrs] = vertexIdx
                    vertexIdx += 1
                faceAttrs.append(vertexAttrs[attrs])
            materialGroups[materialGroup].append(faceAttrs)
            nFaces += 1
        elif line.startswith('o '):  # ignored for now
            pass
        elif line.startswith('g '):  # ignored for now
            pass
        elif line.startswith('usemtl '):
            foundMaterial = line[7:]
            if foundMaterial not in materialGroups.keys():
                materialGroups[foundMaterial] = []
            materialGroup = foundMaterial
        elif line.startswith('mtllib '):
            mtlFile = line.strip()[7:]

    # at the very least, we need vertices and facedefs
    if nVertices == 0 or nFaces == 0:
        raise RuntimeError(
            "Failed to load OBJ file, file contains no vertices or faces.")

    # convert indices for materials to numpy arrays
    for key, val in materialGroups.items():
        materialGroups[key] = np.asarray(val, dtype=int)

    # indicate if file has any texture coordinates of normals
    hasTexCoords = nTextureCoords > 0
    hasNormals = nNormals > 0

    # lists for vertex attributes
    vertexPos = []
    vertexTexCoord = []
    vertexNormal = []

    # populate vertex attribute arrays
    for attrs, idx in vertexAttrs.items():
        attr = attrs.split('/')
        vertexPos.append(positionDefs[int(attr[0]) - 1])
        if len(attr) > 1:  # has texture coords
            if hasTexCoords:
                if attr[1] != '':  # texcoord field not empty
                    vertexTexCoord.append(texCoordDefs[int(attr[1]) - 1])
                else:
                    vertexTexCoord.append([0., 0.])  # fill with zeros
        if len(attr) > 2:  # has normals too
            if hasNormals:
                vertexNormal.append(normalDefs[int(attr[2]) - 1])
            else:
                vertexNormal.append([0., 0., 0.])  # fill with zeros

    # convert vertex attribute lists to numeric arrays
    vertexPos = np.asarray(vertexPos)
    vertexTexCoord = np.asarray(vertexTexCoord)
    vertexNormal = np.asarray(vertexNormal)

    # compute the extents of the model, needed for axis-aligned bounding boxes
    extents = (vertexPos.min(axis=0), vertexPos.max(axis=0))

    # resolve the path to the material file associated with the mesh
    if mtlFile is not None:
        mtlFile = os.path.join(os.path.split(objFile)[0], mtlFile)

    return ObjMeshInfo(vertexPos,
                       vertexTexCoord,
                       vertexNormal,
                       materialGroups,
                       extents,
                       mtlFile)


def loadMtlFile(mtllib, texParams=None):
    """Load a material library file (*.mtl).

    Parameters
    ----------
    mtllib : str
        Path to the material library file.
    texParams : list or tuple
        Optional texture parameters for loaded textures. Texture parameters are
        specified as a list of tuples. Each item specifies the option and
        parameter. For instance,
        `[(GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR), ...]`. By default, linear
        filtering is used for both the minifying and magnification filter
        functions. This is adequate for most uses.

    Returns
    -------
    dict
        Dictionary of materials. Where each key is the material name found in
        the file, and values are `Material` namedtuple objects.

    See Also
    --------
    loadObjFile : Load an `*.OBJ` file.

    Examples
    --------
    Load material associated with an `*.OBJ` file::

        objModel = loadObjFile('/path/to/file.obj')
        # load the material (*.mtl) file, textures are also loaded
        mtllib = loadMtl('/path/to/' + objModel.mtlFile)

    Use a material when rendering vertex arrays::

        useMaterial(mtllib[material])
        drawVAO(vao)
        useMaterial(None)  # disable materials when done

    """
    # open the file, read it into memory
    with open(mtllib, 'r') as mtlFile:
        mtlBuffer = StringIO(mtlFile.read())

    # default texture parameters
    if texParams is None:
        texParams = {GL.GL_TEXTURE_MAG_FILTER: GL.GL_LINEAR,
                     GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR}

    foundMaterials = {}
    foundTextures = {}
    thisMaterial = 0
    for line in mtlBuffer.readlines():
        line = line.strip()
        if line.startswith('newmtl '):  # new material
            thisMaterial = line[7:]
            foundMaterials[thisMaterial] = SimpleMaterial()
        elif line.startswith('Ns '):  # specular exponent
            foundMaterials[thisMaterial].shininess = line[3:]
        elif line.startswith('Ks '):  # specular color
            specularColor = np.asarray(list(map(float, line[3:].split(' '))))
            specularColor = 2.0 * specularColor - 1
            foundMaterials[thisMaterial].specularColor = specularColor
        elif line.startswith('Kd '):  # diffuse color
            diffuseColor = np.asarray(list(map(float, line[3:].split(' '))))
            diffuseColor = 2.0 * diffuseColor - 1
            foundMaterials[thisMaterial].diffuseColor = diffuseColor
        elif line.startswith('Ka '):  # ambient color
            ambientColor = np.asarray(list(map(float, line[3:].split(' '))))
            ambientColor = 2.0 * ambientColor - 1
            foundMaterials[thisMaterial].ambientColor = ambientColor
        elif line.startswith('map_Kd '):  # diffuse color map
            # load a diffuse texture from file
            textureName = line[7:]
            if textureName not in foundTextures.keys():
                im = Image.open(
                    os.path.join(os.path.split(mtllib)[0], textureName))
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.convert("RGBA")
                pixelData = np.array(im).ctypes
                width = pixelData.shape[1]
                height = pixelData.shape[0]
                foundTextures[textureName] = createTexImage2D(
                    width,
                    height,
                    internalFormat=GL.GL_RGBA,
                    pixelFormat=GL.GL_RGBA,
                    dataType=GL.GL_UNSIGNED_BYTE,
                    data=pixelData,
                    unpackAlignment=1,
                    texParams=texParams)
            foundMaterials[thisMaterial].diffuseTexture = \
                foundTextures[textureName]

    return foundMaterials


def createUVSphere(radius=0.5, sectors=16, stacks=16, flipFaces=False):
    """Create a UV sphere.

    Procedurally generate a UV sphere by specifying its radius, and number of
    stacks and sectors. The poles of the resulting sphere will be aligned with
    the Z-axis.

    Surface normals and texture coordinates are automatically generated. The
    returned normals are computed to produce smooth shading.

    Parameters
    ----------
    radius : float, optional
        Radius of the sphere in scene units (usually meters). Default is 0.5.
    sectors, stacks : int, optional
        Number of longitudinal and latitudinal sub-divisions. Default is 16 for
        both.
    flipFaces : bool, optional
        If `True`, normals and face windings will be set to point inward towards
        the center of the sphere. Texture coordinates will remain the same.
        Default is `False`.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    Examples
    --------
    Create a UV sphere and VAO to render it::

        vertices, textureCoords, normals, faces = \
            gltools.createUVSphere(sectors=32, stacks=32)

        vertexVBO = gltools.createVBO(vertices)
        texCoordVBO = gltools.createVBO(textureCoords)
        normalsVBO = gltools.createVBO(normals)
        indexBuffer = gltools.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        vao = gltools.createVAO({0: vertexVBO, 8: texCoordVBO, 2: normalsVBO},
            indexBuffer=indexBuffer)

        # in the rendering loop
        gltools.drawVAO(vao, GL.GL_TRIANGLES)

    The color of the sphere can be changed by calling `glColor*`::

        glColor4f(1.0, 0.0, 0.0, 1.0)  # red
        gltools.drawVAO(vao, GL.GL_TRIANGLES)

    Raw coordinates can be transformed prior to uploading to VBOs. Here we can
    rotate vertex positions and normals so the equator rests on Z-axis::

        r = mt.rotationMatrix(90.0, (1.0, 0, 0.0))  # 90 degrees about +X axis
        vertices = mt.applyMatrix(r, vertices)
        normals = mt.applyMatrix(r, normals)

    """
    # based of the code found here https://www.songho.ca/opengl/gl_sphere.html
    sectorStep = 2.0 * np.pi / sectors
    stackStep = np.pi / stacks
    lengthInv = 1.0 / radius

    vertices = []
    normals = []
    texCoords = []

    for i in range(stacks + 1):
        stackAngle = np.pi / 2.0 - i * stackStep
        xy = radius * np.cos(stackAngle)
        z = radius * np.sin(stackAngle)

        for j in range(sectors + 1):
            sectorAngle = j * sectorStep
            x = xy * np.cos(sectorAngle)
            y = xy * np.sin(sectorAngle)

            vertices.append((x, y, z))

            nx = x * lengthInv
            ny = y * lengthInv
            nz = z * lengthInv

            normals.append((nx, ny, nz))

            s = 1.0 - j / float(sectors)
            t = i / float(stacks)

            texCoords.append((s, t))

    # generate index
    indices = []
    for i in range(stacks):
        k1 = i * (sectors + 1)
        k2 = k1 + sectors + 1

        for j in range(sectors):
            # case for caps
            if not flipFaces:
                if i != 0:
                    indices.append((k1, k2, k1 + 1))

                if i != stacks - 1:
                    indices.append((k1 + 1, k2, k2 + 1))
            else:
                if i != 0:
                    indices.append((k1, k1 + 1, k2))

                if i != stacks - 1:
                    indices.append((k1 + 1, k2 + 1, k2))

            k1 += 1
            k2 += 1

    # convert to numpy arrays
    vertices = np.ascontiguousarray(vertices, dtype=np.float32)
    normals = np.ascontiguousarray(normals, dtype=np.float32)
    texCoords = np.ascontiguousarray(texCoords, dtype=np.float32)
    faces = np.ascontiguousarray(indices, dtype=np.uint32)

    if flipFaces:   # flip normals so they point inwards
        normals *= -1.0

    return vertices, texCoords, normals, faces


def createPlane(size=(1., 1.)):
    """Create a plane.

    Procedurally generate a plane (or quad) mesh by specifying its size. Texture
    coordinates are computed automatically, with origin at the bottom left of
    the plane. The generated plane is perpendicular to the +Z axis, origin of
    the plane is at its center.

    Parameters
    ----------
    size : tuple or float
        Dimensions of the plane. If a single value is specified, the plane will
        be square. Provide a tuple of floats to specify the width and length of
        the plane (eg. `size=(0.2, 1.3)`).

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    Examples
    --------
    Create a plane mesh and draw it::

        vertices, textureCoords, normals, faces = gltools.createPlane()

        vertexVBO = gltools.createVBO(vertices)
        texCoordVBO = gltools.createVBO(textureCoords)
        normalsVBO = gltools.createVBO(normals)
        indexBuffer = gltools.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        vao = gltools.createVAO({0: vertexVBO, 8: texCoordVBO, 2: normalsVBO},
            indexBuffer=indexBuffer)

        # in the rendering loop
        gltools.drawVAO(vao, GL.GL_TRIANGLES)

    """
    if isinstance(size, (int, float,)):
        sx = sy = float(size) / 2.
    else:
        sx = size[0] / 2.
        sy = size[1] / 2.

    vertices = np.ascontiguousarray(
        [[-1.,  1., 0.],
         [ 1.,  1., 0.],
         [-1., -1., 0.],
         [ 1., -1., 0.]])

    if sx != 1.:
        vertices[:, 0] *= sx

    if sy != 1.:
        vertices[:, 1] *= sy

    # texture coordinates
    texCoords = np.ascontiguousarray([[0., 1.], [1., 1.], [0., 0.], [1., 0.]])

    # normals, facing +Z
    normals = np.zeros_like(vertices)
    normals[:, 0] = 0.
    normals[:, 1] = 0.
    normals[:, 2] = 1.

    # generate face index
    faces = np.ascontiguousarray([[0, 2, 1], [1, 2, 3]], dtype=np.uint32)

    return vertices, texCoords, normals, faces


def createMeshGridFromArrays(xvals, yvals, zvals=None, tessMode='diag', computeNormals=True):
    """Create a mesh grid using coordinates from arrays.

    Generates a mesh using data in provided in 2D arrays of vertex coordinates.
    Triangle faces are automatically computed by this function by joining
    adjacent vertices at neighbouring indices in the array. Texture coordinates
    are generated covering the whole mesh, with origin at the bottom left.

    Parameters
    ----------
    xvals, yvals : array_like
        NxM arrays of X and Y coordinates. Both arrays must have the same
        shape. the resulting mesh will have a single vertex for each X and Y
        pair. Faces will be generated to connect adjacent coordinates in the
        array.
    zvals : array_like, optional
        NxM array of Z coordinates for each X and Y. Must have the same shape
        as X and Y. If not specified, the Z coordinates will be filled with
        zeros.
    tessMode : str, optional
        Tessellation mode. Specifies how faces are generated. Options are
        'center', 'radial', and 'diag'. Default is 'diag'. Modes 'radial' and
        'center' work best with odd numbered array dimensions.
    computeNormals : bool, optional
        Compute normals for the generated mesh. If `False`, all normals are set
        to face in the +Z direction. Presently, computing normals is a slow
        operation and may not be needed for some meshes.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    Examples
    --------
    Create a 3D sine grating mesh using 2D arrays::

        x = np.linspace(0, 1.0, 32)
        y = np.linspace(1.0, 0.0, 32)
        xx, yy = np.meshgrid(x, y)
        zz = np.tile(np.sin(np.linspace(0.0, 32., 32)) * 0.02, (32, 1))

        vertices, textureCoords, normals, faces = \
            gltools.createMeshGridFromArrays(xx, yy, zz)

    """
    vertices = np.vstack([xvals.ravel(), yvals.ravel()]).T

    if zvals is not None:
        assert xvals.shape == yvals.shape == zvals.shape
    else:
        assert xvals.shape == yvals.shape

    if zvals is None:
        # fill z with zeros if not provided
        vertices = np.hstack([vertices, np.zeros((vertices.shape[0], 1))])
    else:
        vertices = np.hstack([vertices, np.atleast_2d(zvals.ravel()).T])

    ny, nx = xvals.shape

    # texture coordinates
    u = np.linspace(0.0, 1.0, nx)
    v = np.linspace(1.0, 0.0, ny)
    uu, vv = np.meshgrid(u, v)

    texCoords = np.vstack([uu.ravel(), vv.ravel()]).T

    # generate face index
    faces = []

    if tessMode == 'diag':
        for i in range(ny - 1):
            k1 = i * nx
            k2 = k1 + nx

            for j in range(nx - 1):
                faces.append([k1, k2, k1 + 1])
                faces.append([k1 + 1, k2, k2 + 1])

                k1 += 1
                k2 += 1

    else:
        raise ValueError('Invalid value for `tessMode`.')

    # convert to numpy arrays
    vertices = np.ascontiguousarray(vertices, dtype=np.float32)
    texCoords = np.ascontiguousarray(texCoords, dtype=np.float32)
    faces = np.ascontiguousarray(faces, dtype=np.uint32)

    # calculate surface normals for the mesh
    if computeNormals:
        normals = calculateVertexNormals(vertices, faces, shading='smooth')
    else:
        normals = np.zeros_like(vertices, dtype=np.float32)
        normals[:, 2] = 1.

    return vertices, texCoords, normals, faces


def createMeshGrid(size=(1., 1.), subdiv=0, tessMode='diag'):
    """Create a grid mesh.

    Procedurally generate a grid mesh by specifying its size and number of
    sub-divisions. Texture coordinates are computed automatically. The origin is
    at the center of the mesh. The generated grid is perpendicular to the +Z
    axis, origin of the grid is at its center.

    Parameters
    ----------
    size : tuple or float
        Dimensions of the mesh. If a single value is specified, the plane will
        be square. Provide a tuple of floats to specify the width and length of
        the plane (eg. `size=(0.2, 1.3)`).
    subdiv : int, optional
        Number of subdivisions. Zero subdivisions are applied by default, and
        the resulting mesh will only have vertices at the corners.
    tessMode : str, optional
        Tessellation mode. Specifies how faces are subdivided. Options are
        'center', 'radial', and 'diag'. Default is 'diag'. Modes 'radial' and
        'center' work best with an odd number of subdivisions.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    Examples
    --------
    Create a grid mesh and draw it::

        vertices, textureCoords, normals, faces = gltools.createPlane()

        vertexVBO = gltools.createVBO(vertices)
        texCoordVBO = gltools.createVBO(textureCoords)
        normalsVBO = gltools.createVBO(normals)
        indexBuffer = gltools.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        vao = gltools.createVAO({0: vertexVBO, 8: texCoordVBO, 2: normalsVBO},
            indexBuffer=indexBuffer)

        # in the rendering loop
        gltools.drawVAO(vao, GL.GL_TRIANGLES)

    Randomly displace vertices off the plane of the grid by setting the `Z`
    value per vertex::

        vertices, textureCoords, normals, faces = \
            gltools.createMeshGrid(subdiv=11)

        numVerts = vertices.shape[0]
        vertices[:, 2] = np.random.uniform(-0.02, 0.02, (numVerts,)))  # Z

        # you must recompute surface normals to get correct shading!
        normals = gltools.calculateVertexNormals(vertices, faces)

        # create a VAO as shown in the previous example here to draw it ...

    """
    if isinstance(size, (int, float,)):
        divx = divy = float(size) / 2.
    else:
        divx = size[0] / 2.
        divy = size[1] / 2.

    # generate plane vertices
    x = np.linspace(-divx, divx, subdiv + 2)
    y = np.linspace(divy, -divy, subdiv + 2)
    xx, yy = np.meshgrid(x, y)

    vertices = np.vstack([xx.ravel(), yy.ravel()]).T
    vertices = np.hstack([vertices, np.zeros((vertices.shape[0], 1))])  # add z

    # texture coordinates
    u = np.linspace(0.0, 1.0, subdiv + 2)
    v = np.linspace(1.0, 0.0, subdiv + 2)
    uu, vv = np.meshgrid(u, v)

    texCoords = np.vstack([uu.ravel(), vv.ravel()]).T

    # normals, facing +Z
    normals = np.zeros_like(vertices)
    normals[:, 0] = 0.
    normals[:, 1] = 0.
    normals[:, 2] = 1.

    # generate face index
    faces = []

    if tessMode == 'diag':
        for i in range(subdiv + 1):
            k1 = i * (subdiv + 2)
            k2 = k1 + subdiv + 2

            for j in range(subdiv + 1):
                faces.append([k1, k2, k1 + 1])
                faces.append([k1 + 1, k2, k2 + 1])

                k1 += 1
                k2 += 1

    elif tessMode == 'center':
        lx = len(x)
        ly = len(y)

        for i in range(subdiv + 1):
            k1 = i * (subdiv + 2)
            k2 = k1 + subdiv + 2

            for j in range(subdiv + 1):
                if k1 + j < k1 + int((lx / 2)):
                    if int(k1 / ly) + 1 > int(ly / 2):
                        faces.append([k1, k2, k1 + 1])
                        faces.append([k1 + 1, k2, k2 + 1])
                    else:
                        faces.append([k1, k2, k2 + 1])
                        faces.append([k1 + 1, k1, k2 + 1])
                else:
                    if int(k1 / ly) + 1 > int(ly / 2):
                        faces.append([k1, k2, k2 + 1])
                        faces.append([k1 + 1, k1, k2 + 1])
                    else:
                        faces.append([k1, k2, k1 + 1])
                        faces.append([k1 + 1, k2, k2 + 1])

                k1 += 1
                k2 += 1

    elif tessMode == 'radial':
        lx = len(x)
        ly = len(y)

        for i in range(subdiv + 1):
            k1 = i * (subdiv + 2)
            k2 = k1 + subdiv + 2

            for j in range(subdiv + 1):
                if k1 + j < k1 + int((lx / 2)):
                    if int(k1 / ly) + 1 > int(ly / 2):
                        faces.append([k1, k2, k2 + 1])
                        faces.append([k1 + 1, k1, k2 + 1])
                    else:
                        faces.append([k1, k2, k1 + 1])
                        faces.append([k1 + 1, k2, k2 + 1])
                else:
                    if int(k1 / ly) + 1 > int(ly / 2):
                        faces.append([k1, k2, k1 + 1])
                        faces.append([k1 + 1, k2, k2 + 1])
                    else:
                        faces.append([k1, k2, k2 + 1])
                        faces.append([k1 + 1, k1, k2 + 1])

                k1 += 1
                k2 += 1

    else:
        raise ValueError('Invalid value for `tessMode`.')

    # convert to numpy arrays
    vertices = np.ascontiguousarray(vertices, dtype=np.float32)
    texCoords = np.ascontiguousarray(texCoords, dtype=np.float32)
    normals = np.ascontiguousarray(normals, dtype=np.float32)
    faces = np.ascontiguousarray(faces, dtype=np.uint32)

    return vertices, texCoords, normals, faces


def createBox(size=(1., 1., 1.), flipFaces=False):
    """Create a box mesh.

    Create a box mesh by specifying its `size` in three dimensions (x, y, z),
    or a single value (`float`) to create a cube. The resulting box will be
    centered about the origin. Texture coordinates and normals are automatically
    generated for each face.

    Setting `flipFaces=True` will make faces and normals point inwards, this
    allows boxes to be viewed and lit correctly from the inside.

    Parameters
    ----------
    size : tuple or float
        Dimensions of the mesh. If a single value is specified, the box will
        be a cube. Provide a tuple of floats to specify the width, length, and
        height of the box (eg. `size=(0.2, 1.3, 2.1)`).
    flipFaces : bool, optional
        If `True`, normals and face windings will be set to point inward towards
        the center of the box. Texture coordinates will remain the same.
        Default is `False`.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    Examples
    --------
    Create a box mesh and draw it::

        vertices, textureCoords, normals, faces = gltools.createBox()

        vertexVBO = gltools.createVBO(vertices)
        texCoordVBO = gltools.createVBO(textureCoords)
        normalsVBO = gltools.createVBO(normals)
        indexBuffer = gltools.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        vao = gltools.createVAO({0: vertexVBO, 8: texCoordVBO, 2: normalsVBO},
            indexBuffer=indexBuffer)

        # in the rendering loop
        gltools.drawVAO(vao, GL.GL_TRIANGLES)

    """
    if isinstance(size, (int, float,)):
        sx = sy = sz = float(size) / 2.
    else:
        sx, sy, sz = size
        sx /= 2.
        sy /= 2.
        sz /= 2.

    # vertices
    vertices = np.ascontiguousarray([
        [ 1.,  1.,  1.], [ 1.,  1., -1.], [ 1., -1.,  1.],
        [ 1., -1., -1.], [-1.,  1., -1.], [-1.,  1.,  1.],
        [-1., -1., -1.], [-1., -1.,  1.], [-1.,  1., -1.],
        [ 1.,  1., -1.], [-1.,  1.,  1.], [ 1.,  1.,  1.],
        [ 1., -1., -1.], [-1., -1., -1.], [ 1., -1.,  1.],
        [-1., -1.,  1.], [-1.,  1.,  1.], [ 1.,  1.,  1.],
        [-1., -1.,  1.], [ 1., -1.,  1.], [ 1.,  1., -1.],
        [-1.,  1., -1.], [ 1., -1., -1.], [-1., -1., -1.]
    ], dtype=np.float32)
    
    # multiply vertex coordinates by box dimensions
    if sx != 1.:
        vertices[:, 0] *= sx

    if sy != 1.:
        vertices[:, 1] *= sy

    if sz != 1.:
        vertices[:, 2] *= sz

    # normals for each side
    normals = np.repeat(
        [[ 1.,  0.,  0.],   # +X
         [-1.,  0.,  0.],   # -X
         [ 0.,  1.,  0.],   # +Y
         [ 0., -1.,  0.],   # -Y
         [ 0.,  0.,  1.],   # +Z
         [ 0.,  0., -1.]],  # -Z
        4, axis=0)

    normals = np.ascontiguousarray(normals, dtype=np.float32)

    # texture coordinates for each side
    texCoords = np.tile([[0., 1.], [1., 1.], [0., 0.], [1., 0.]], (6, 1))
    texCoords = np.ascontiguousarray(texCoords, dtype=np.float32)

    # vertex indices for faces
    faces = np.ascontiguousarray([
        [ 0,  2,  1], [ 1,  2,  3],  # +X
        [ 4,  6,  5], [ 5,  6,  7],  # -X
        [ 8, 10,  9], [ 9, 10, 11],  # +Y
        [12, 14, 13], [13, 14, 15],  # -Y
        [16, 18, 17], [17, 18, 19],  # +Z
        [20, 22, 21], [21, 22, 23]   # -Z
    ], dtype=np.uint32)

    if flipFaces:
        faces = np.fliplr(faces)
        normals *= -1.0

    return vertices, texCoords, normals, faces


def createDisc(radius=1.0, edges=16):
    """Create a disc (filled circle) mesh.

    Generates a flat disc mesh with the specified radius and number of `edges`.
    The origin of the disc is located at the center. Textures coordinates will
    be mapped to a square which bounds the circle. Normals are perpendicular to
    the face of the circle.

    Parameters
    ----------
    radius : float
        Radius of the disc in scene units.
    edges : int
        Number of segments to use to define the outer rim of the disc. Higher
        numbers will result in a smoother circle but will use more triangles.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    Examples
    --------
    Create a vertex array object to draw a disc::

        vertices, textureCoords, normals, faces = gltools.createDisc(edges=128)
        vertexVBO = gltools.createVBO(vertices)
        texCoordVBO = gltools.createVBO(textureCoords)
        normalsVBO = gltools.createVBO(normals)
        indexBuffer = gltools.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        vao = gltools.createVAO(
            {gltools.gl_Vertex: vertexVBO,
             gltools.gl_MultiTexCoord0: texCoordVBO,
             gltools.gl_Normal: normalsVBO},
            indexBuffer=indexBuffer)

    """
    # get number of steps for vertices to get the number of edges we want
    nVerts = edges + 1
    steps = np.linspace(0, 2 * np.pi, num=nVerts, dtype=np.float32)

    # offset since the first vertex is the centre
    vertices = np.zeros((nVerts + 1, 3), dtype=np.float32)
    vertices[1:, 0] = np.sin(steps)
    vertices[1:, 1] = np.cos(steps)

    # compute the face indices
    faces = []
    for i in range(nVerts):
        faces.append([0, i + 1, i])

    faces = np.ascontiguousarray(faces, dtype=np.uint32)

    # compute the texture coordinates for each vertex
    normals = np.zeros_like(vertices, dtype=np.float32)
    normals[:, 2] = 1.

    # compute texture coordinates
    texCoords = vertices.copy()
    texCoords[:, :] += 1.0
    texCoords[:, :] *= 0.5

    # scale to specified radius
    vertices *= radius

    return vertices, texCoords, normals, faces


def createAnnulus(innerRadius=0.5, outerRadius=1.0, edges=16):
    """Create an annulus (ring) mesh.

    Generates a flat ring mesh with the specified inner/outer radii and number
    of `edges`. The origin of the ring is located at the center. Textures
    coordinates will be mapped to a square which bounds the ring. Normals are
    perpendicular to the plane of the ring.

    Parameters
    ----------
    innerRadius, outerRadius : float
        Radius of the inner and outer rims of the ring in scene units.
    edges : int
        Number of segments to use to define the band of the ring. The higher the
        value, the rounder the ring will look.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    """
    # error checks
    if innerRadius >= outerRadius:
        raise ValueError("Inner radius must be less than outer.")
    elif outerRadius <= 0.:
        raise ValueError("Outer radius must be >0.")
    elif innerRadius < 0.:
        raise ValueError("Inner radius must be positive.")
    elif edges <= 2:
        raise ValueError("Number of edges must be >2.")

    # generate inner and outer vertices
    nVerts = edges + 1
    steps = np.linspace(0, 2 * np.pi, num=nVerts, dtype=np.float32)

    innerVerts = np.zeros((nVerts, 3), dtype=np.float32)
    outerVerts = np.zeros((nVerts, 3), dtype=np.float32)
    innerVerts[:, 0] = outerVerts[:, 0] = np.sin(steps)
    innerVerts[:, 1] = outerVerts[:, 1] = np.cos(steps)

    # Keep the ring size between -1 and 1 to simplify computing texture
    # coordinates. We'll scale the vertices to the correct dimensions
    # afterwards.
    frac = innerRadius / float(outerRadius)
    innerVerts[:, :2] *= frac

    # combine inner and outer vertex rings
    vertPos = np.vstack((innerVerts, outerVerts))

    # generate faces
    faces = []
    for i in range(nVerts):
        faces.append([i, edges + i + 1, edges + i])
        faces.append([i, i + 1, edges + i + 1])

    vertPos = np.ascontiguousarray(vertPos, dtype=np.float32)
    normals = np.zeros_like(vertPos, dtype=np.float32)
    normals[:, 2] = 1.0
    faces = np.ascontiguousarray(faces, dtype=np.uint32)

    # compute texture coordinates
    texCoords = vertPos.copy()
    texCoords[:, :] += 1.0
    texCoords[:, :] *= 0.5

    # scale to specified outer radius
    vertPos[:, :2] *= outerRadius

    return vertPos, texCoords, normals, faces


def createCylinder(radius=1.0, height=1.0, edges=16, stacks=1):
    """Create a cylinder mesh.

    Generate a cylinder mesh with a given `height` and `radius`. The origin of
    the mesh will centered on it and offset to the base. Texture coordinates
    will be generated allowing a texture to wrap around it.

    Parameters
    ----------
    radius : float
        Radius of the cylinder in scene units.
    height : float
        Height in scene units.
    edges : int
        Number of edges, the greater the number, the smoother the cylinder will
        appear when drawn.
    stacks : int
        Number of subdivisions along the height of cylinder to make. Setting to
        1 will result in vertex data only being generated for the base and end
        of the cylinder.

    Returns
    -------
    tuple
        Vertex attribute arrays (position, texture coordinates, and normals) and
        triangle indices.

    """
    # generate vertex positions
    nEdgeVerts = edges + 1
    rings = stacks + 1
    steps = np.linspace(0, 2 * np.pi, num=nEdgeVerts)
    vertPos = np.zeros((nEdgeVerts, 3))
    vertPos[:, 0] = np.sin(steps)
    vertPos[:, 1] = np.cos(steps)
    vertPos = np.tile(vertPos, (rings, 1))

    # apply offset in height for each stack
    stackHeight = np.linspace(0, height, num=rings)
    vertPos[:, 2] = np.repeat(stackHeight, nEdgeVerts)

    # generate texture coordinates to they wrap around the cylinder
    u = np.linspace(0.0, 1.0, nEdgeVerts)
    v = np.linspace(1.0, 0.0, rings)
    uu, vv = np.meshgrid(u, v)
    texCoords = np.vstack([uu.ravel(), vv.ravel()]).T

    # generate vertex normals, since our vertices all on a unit circle, we can
    # do a trick here
    normals = vertPos.copy()
    normals[:, 2] = 0.0

    # create face indices
    faces = []
    for i in range(0, stacks):
        stackOffset = nEdgeVerts * i
        for j in range(nEdgeVerts):
            j = stackOffset + j
            faces.append([j, edges + j, edges + j + 1])
            faces.append([j, edges + j + 1, j + 1])

    vertPos, texCoords, normals = [
        np.ascontiguousarray(i, dtype=np.float32) for i in (
            vertPos, texCoords, normals)]
    faces = np.ascontiguousarray(faces, dtype=np.uint32)

    # scale the cylinder's radius and height to what the user specified
    vertPos[:, :2] *= radius

    return vertPos, texCoords, normals, faces


def transformMeshPosOri(vertices, normals, pos=(0., 0., 0.), ori=(0., 0., 0., 1.)):
    """Transform a mesh.

    Transform mesh vertices and normals to a new position and orientation using
    a position coordinate and rotation quaternion. Values `vertices` and
    `normals` must be the same shape. This is intended to be used when editing
    raw vertex data prior to rendering. Do not use this to change the
    configuration of an object while rendering.

    Parameters
    ----------
    vertices : array_like
        Nx3 array of vertices.
    normals : array_like
        Nx3 array of normals.
    pos : array_like, optional
        Position vector to transform mesh vertices. If Nx3, `vertices` will be
        transformed by corresponding rows of `pos`.
    ori : array_like, optional
        Orientation quaternion in form [x, y, z, w]. If Nx4, `vertices` and
        `normals` will be transformed by corresponding rows of `ori`.

    Returns
    -------
    tuple
        Transformed vertices and normals.

    Examples
    --------
    Create and re-orient a plane to face upwards::

        vertices, textureCoords, normals, faces = createPlane()

        # rotation quaternion
        qr = quatFromAxisAngle((1., 0., 0.), -90.0)  # -90 degrees about +X axis

        # transform the normals and points
        vertices, normals = transformMeshPosOri(vertices, normals, ori=qr)

    Any `create*` primitive generating function can be used inplace of
    `createPlane`.

    """
    # ensure these are contiguous
    vertices = np.ascontiguousarray(vertices)
    normals = np.ascontiguousarray(normals)

    if not np.allclose(pos, [0., 0., 0.]):
        vertices = mt.transform(pos, ori, vertices, dtype=np.float32)

    if not np.allclose(ori, [0., 0., 0., 1.]):
        normals = mt.applyQuat(ori, normals, dtype=np.float32)

    return vertices, normals


# ------------------------------
# Mesh editing and cleanup tools
# ------------------------------
#

def calculateVertexNormals(vertices, faces, shading='smooth'):
    """Calculate vertex normals given vertices and triangle faces.

    Finds all faces sharing a vertex index and sets its normal to either
    the face normal if `shading='flat'` or the average normals of adjacent
    faces if `shading='smooth'`. Note, this function does not convert between
    flat and smooth shading. Flat shading only works correctly if each
    vertex belongs to exactly one face.

    The direction of the normals are determined by the winding order of
    triangles, assumed counter clock-wise (OpenGL default). Most 3D model
    editing software exports using this convention. If not, winding orders
    can be reversed by calling::

        faces = numpy.fliplr(faces)

    In some case when using 'smooth', creases may appear if vertices are at the
    same location, but do not share the same index. This may be desired in some
    cases, however one may use the :func:`smoothCreases` function computing
    normals to smooth out creases.

    Parameters
    ----------
    vertices : array_like
        Nx3 vertex positions.
    faces : array_like
        Nx3 vertex indices.
    shading : str, optional
        Shading mode. Options are 'smooth' and 'flat'. Flat only works with
        meshes where no vertex index is shared across faces, if not, the
        returned normals will be invalid.

    Returns
    -------
    ndarray
        Vertex normals array with the shame shape as `vertices`. Computed
        normals are normalized.

    Examples
    --------
    Recomputing vertex normals for a UV sphere::

        # create a sphere and discard normals
        vertices, textureCoords, _, faces = gltools.createUVSphere()
        normals = gltools.calculateVertexNormals(vertices, faces)

    """
    # compute surface normals for all faces
    faceNormals = mt.surfaceNormal(vertices[faces])

    normals = []  # new list of normals to return
    if shading == 'flat':
        for vertexIdx in np.unique(faces):
            match, _ = np.where(faces == vertexIdx)
            normals.append(faceNormals[match, :])
    elif shading == 'smooth':
        # get all faces the vertex belongs to
        for vertexIdx in np.unique(faces):
            match, _ = np.where(faces == vertexIdx)
            normals.append(mt.vertexNormal(faceNormals[match, :]))

    return np.ascontiguousarray(np.vstack(normals), np.float32) + 0.0


def mergeVertices(vertices, faces, textureCoords=None, vertDist=0.0001,
                  texDist=0.0001):
    """Simplify a mesh by removing redundant vertices.

    This function simplifies a mesh by merging overlapping (doubled) vertices,
    welding together adjacent faces and removing sharp creases that appear when
    rendering. This is useful in cases where a mesh's triangles do not share
    vertices and one wishes to have it appear smoothly shaded when rendered. One
    can also use this function reduce the detail of a mesh, however the quality
    of the results may vary.

    The position of the new vertex after merging will be the average position
    of the adjacent vertices. Re-indexed faces and recalculated normals are also
    returned with the cleaned-up vertex data. If texture coordinates are
    supplied, adjacent vertices will not be removed if their is a distance in
    texel space is greater than `texDist`. This avoids discontinuities in the
    texture of the simplified mesh.

    Parameters
    ----------
    vertices : ndarray
        Nx3 array of vertex positions.
    faces : ndarray
        Nx3 integer array of face vertex indices.
    textureCoords : ndarray
        Nx2 array of texture coordinates.
    vertDist : float
        Maximum distance between two adjacent vertices to merge in scene units.
    texDist : float
        Maximum distance between texels to permit merging of vertices. If a
        vertex is within merging distance, it will be moved instead of merged.

    Returns
    -------
    tuple
        Tuple containing newly computed vertices, normals and face indices. If
        `textureCoords` was specified, a new array of texture coordinates will
        be returned too at the second index.

    Notes
    -----
    * This function only works on meshes consisting of triangle faces.

    Examples
    --------
    Remove redundant vertices from a sphere::

        vertices, textureCoords, normals, faces = gltools.createUVSphere()
        vertices, textureCoords, normals, faces = gltools.removeDoubles(
            vertices, faces, textureCoords)

    Same but no texture coordinates are specified::

        vertices, normals, faces = gltools.removeDoubles(vertices, faces)

    """
    # keep track of vertices that we merged
    vertsProcessed = np.zeros((vertices.shape[0],), dtype=np.bool)

    faces = faces.flatten()  # existing faces but flattened
    # new array of faces that will get updated
    newFaces = np.zeros_like(faces, dtype=np.uint32)

    # loop over all vertices in the original mesh
    newVerts = []
    newTexCoords = []
    lastProcIdx = 0  # last index processed, used to reindex
    for i, vertex in enumerate(vertices):
        if vertsProcessed[i]:  # don't do merge check if already processed
            continue

        # get the distance to all other vertices in mesh
        vertDists = mt.distance(vertex, vertices)

        # get vertices that fall with the threshold distance
        toProcess = np.where(vertDists <= vertDist)[0]

        # if all adjacent vertices were processed, move on to the next
        if np.all(vertsProcessed[toProcess]):
            continue

        # if we have close verts and they have not been processed, merge them
        if len(toProcess) > 1:
            # If we have texture coords, merge those whose texture coords are
            # close. Move the vertex to the new location for any that are not.
            if textureCoords is not None:
                # create a new vertex by averaging out positions
                texCoordDists = mt.distance(textureCoords[i, :],
                                            textureCoords[toProcess, :])

                # get the vertices to merge or move
                toMerge = toProcess[texCoordDists <= texDist]
                toMove = toProcess[texCoordDists > texDist]

                # compute mean positions
                newPos = np.mean(vertices[toMerge, :], axis=0)
                newTexCoord = np.mean(textureCoords[toMerge, :], axis=0)

                newVerts.append(newPos)
                newTexCoords.append(newTexCoord)
                newFaces[np.in1d(faces, toMerge).nonzero()[0]] = lastProcIdx

                # handle vertices that were moved
                for j, idx in enumerate(toMove):
                    newVerts.append(newPos)
                    newTexCoords.append(textureCoords[idx, :])
                    newFaces[np.argwhere(faces == idx)] = lastProcIdx + j

                lastProcIdx += len(toMove)

                vertsProcessed[toProcess] = 1  # update verts we processed

            else:
                newPos = np.mean(vertices[toProcess, :], axis=0)
                newVerts.append(newPos)
                newFaces[np.in1d(faces, toProcess).nonzero()[0]] = lastProcIdx
                vertsProcessed[toProcess] = 1  # update verts we processed

        else:
            # single vertices need to be added too
            newVerts.append(vertex)
            if textureCoords is not None:
                newTexCoords.append(textureCoords[i, :])
            vertsProcessed[i] = 1  # update merged list
            newFaces[np.argwhere(faces == i)] = lastProcIdx

        lastProcIdx += 1

        # all vertices have been processed, exit loop early
        if np.all(vertsProcessed):
            break

    # create new output arrays
    newVerts = np.ascontiguousarray(np.vstack(newVerts), dtype=np.float32)
    newFaces = np.ascontiguousarray(newFaces.reshape((-1, 3)), dtype=np.uint32)
    newNormals = calculateVertexNormals(newVerts, newFaces, 'smooth')

    if textureCoords is not None:
        newTexCoords = np.ascontiguousarray(
            np.vstack(newTexCoords), dtype=np.float32)
        toReturn = (newVerts, newTexCoords, newNormals, newFaces)
    else:
        toReturn = (newVerts, newNormals, newFaces)

    return toReturn


def smoothCreases(vertices, normals, vertDist=0.0001):
    """Remove creases caused by misaligned surface normals.

    A problem arises where surface normals are not correctly interpolated across
    the edge where two faces meet, resulting in a visible 'crease' or sharp
    discontinuity in shading. This is usually caused by the normals of the
    overlapping vertices forming the edge being mis-aligned (not pointing in the
    same direction).

    If you notice these crease artifacts are present in your mesh *after*
    computing surface normals, you can use this function to smooth them out.

    Parameters
    ----------
    vertices : ndarray
        Nx3 array of vertex coordinates.
    normals : ndarray
        Nx3 array of vertex normals.
    vertDist : float
        Maximum distance between vertices to average. Avoid using large numbers
        here, vertices to be smoothed should be overlapping. This distance
        should be as small as possible, just enough to account for numeric
        rounding errors between vertices intended which would otherwise be at
        the exact same location.

    Returns
    -------
    ndarray
        Array of smoothed surface normals with the same shape as `normals`.

    """
    newNormals = normals.copy()

    # keep track of vertices that we processed
    vertsProcessed = np.zeros((vertices.shape[0],), dtype=np.bool)

    for i, vertex in enumerate(vertices):
        if vertsProcessed[i]:  # don't do merge check if already processed
            continue

        # get the distance to all other vertices in mesh
        dist = mt.distance(vertex, vertices)

        # get vertices that fall with the threshold distance
        adjacentIdx = list(np.where(dist <= vertDist)[0])

        if np.all(vertsProcessed[adjacentIdx]):
            continue

        # now get their normals and average them
        if len(adjacentIdx) > 1:
            toAverage = vertices[adjacentIdx, :]
            newNormal = np.mean(toAverage, axis=0)

            # normalize
            newNormal = mt.normalize(newNormal, out=newNormal)

            # overwrite the normals we used to compute this one
            newNormals[adjacentIdx, :] = newNormal

            # flag these normals as used
            vertsProcessed[adjacentIdx] = 1

    return newNormals


def flipFaces(normals, faces):
    """Change the winding order of face indices.

    OpenGL uses the winding order of face vertices to determine which side of
    the face is either the front and back. This function reverses the winding
    order of face indices and flips vertex normals so faces can be correctly
    shaded.

    Parameters
    ----------
    normals : ndarray
        Nx3 array of surface normals.
    faces : ndarray
        Nx3 array of face indices.

    Returns
    -------
    ndarray
        Face indices with winding order reversed.

    Examples
    --------
    Flip faces and normals of a box mesh so it can be viewed and lit from the
    inside::

        vertices, texCoords, normals, faces = createBox((5, 5, 5))
        faces = flipFaces(faces)

    """
    normals = -normals  # invert normal vectors
    faces = np.fliplr(faces)

    return normals, faces


def interleaveAttributes(attribArrays):
    """Interleave vertex attributes into a single array.

    Interleave vertex attributes into a single array for use with OpenGL's
    vertex array objects. This function is useful when creating a VBO from
    separate arrays of vertex positions, normals, and texture coordinates.

    Parameters
    ----------
    attribArrays : list of array_like
        List of arrays containing vertex attributes. Each array must have the
        same number of rows.

    Returns
    -------
    tuple
        A tuple containing the interleaved vertex attribute array, a list of
        attribute sizes, and a list of attribute offsets.
    
    Examples
    --------
    Interleave vertex attributes for use with a VAO::

        vertices, textureCoords, normals, faces = createBox()
        interleaved, sizes, offsets = interleaveAttributes(
            [vertices, textureCoords, normals])
        
        # create a VBO with interleaved attributes
        vboInterleaved = createVBO(interleaved)

        # ... before rendering, set the attribute pointers
        GL.glBindBuffer(vboInterleaved.target, vboInterleaved.name)
        for i, attrib in enumerate([0, 8, 3]):
            gltools.setVertexAttribPointer(
                attrib, vboInterleaved, size=sizes[i], offset=offsets[i])

    """
    # get the number of rows in the first array
    nRows = attribArrays[0].shape[0]

    # check if all arrays have the same number of rows
    if  any([i.shape[0] != nRows for i in attribArrays]):
        raise ValueError("All arrays must have the same number of rows.")

    # get a list of attribute widths
    sizes = [i.shape[1] for i in attribArrays]
    offsets = [0] + [sum(sizes[:i]) for i in range(1, len(sizes))]

    # combine all arrays horizontally
    toReturn = np.hstack(attribArrays)

    return np.ascontiguousarray(toReturn, dtype=np.float32), sizes, offsets


def generateTexCoords(vertices):
    """Generate texture coordinates for a mesh.

    Generate texture coordinates for a mesh by normalizing the vertex positions
    to the bounding box of the mesh.

    Parameters
    ----------
    vertices : ndarray
        Nx2 or Nx3 array of vertex positions.

    Returns
    -------
    ndarray
        Nx2 array of normalized texture coordinates.

    Examples
    --------
    Generate texture coordinates for a box mesh::

        vertices, textureCoords, normals, faces = createBox()
        texCoords = generateTexCoords(vertices)

    """
    # normalize the vertex positions to the bounding box
    texCoords = (vertices - np.min(vertices, axis=0)) / np.ptp(vertices, axis=0)

    return np.ascontiguousarray(texCoords, dtype=np.float32)


def tesselate(points, mode='triangle', config=None):
    """Tesselate (or fill) a 2D polygon edge loop.

    Tesselate a 2D polygon defined by a set of vertices. This creates a 'filled'
    polygon where the vertices are connected by a set of triangles. The function 
    will return a tesselated mesh with vertex positions, surface normals, and 
    face indices. Texture coordinates are generated by normalizing the vertex 
    positions.
    
    Parameters
    ----------
    points : ndarray
        Nx2 array of vertex positions of the outer boundary.
    mode : str, optional
        Tesselation mode (algorithm) to use. Options are 'triangle', 'delaunay', 
        'fan' or 'simple'. Default is 'triangle' (recommended) which is the most 
        robust method that can handle concave polygons and holes. Use 'fan' for
        equilateral polygons.
    config : dict, optional
        Configuration options for the tesselation. This can be used to specify
        additional options for the tesselation algorithm.
    
    Returns
    -------
    tuple
        A tuple containing the vertex positions, surface normals, texture 
        coordinates, and face indices of the tesselated mesh.

    Examples
    --------
    Tesselate a simple square::

        vertices = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        vertices, normals, texCoords, faces = tesselate(points)

    Notes
    -----
    * The 'triangle' mode uses the Triangle library (via MeshPy) to tesselate
      the polygon, see: https://www.cs.cmu.edu/~quake/triangle.html
    * The 'delaunay' mode uses the `scipy.spatial.Delaunay` for tesselation
      (using the Qhull library). However, it cannot handle holes or concave 
      polygons.
    * The 'fan' mode creates a fan tesselation where the first vertex is the
      center of the fan and the rest are the outer boundary. This is useful for
      creating simple, nonconcave shapes like circles.

    """
    config = config or dict()  # ensure we have a config dictionary

    nPoints = len(points)
    if nPoints < 3:
        raise ValueError(
            "At least 3 points are required to tesselate a polygon.")
    elif nPoints == 3:
        # if we only have 3 points, we can't tesselate the polygon
        vertices = np.array(points, dtype=np.float32)
        faces = np.array([[0, 1, 2]], dtype=np.uint32)
        normals = np.ascontiguousarray(
            np.tile([0., 0., -1.], (faces.shape[0], 1)), dtype=np.float32)
        texCoords = generateTexCoords(vertices)

        return vertices, normals, texCoords, faces

    # perform tesselation based on the mode
    if mode == 'triangle' or mode == 'meshpy':
        # trinagulation using meshpy (triangle)
        from meshpy.triangle import MeshInfo, build

        # create a mesh info object
        meshInfo = MeshInfo()
        meshInfo.set_points(points)

        # compute facets
        facetEnd = len(points) - 1
        facets = [(i, i + 1) for i in range(0, facetEnd)] + [(facetEnd, 0)]
        meshInfo.set_facets(facets)

        # build the mesh
        mesh = build(meshInfo, **config)

        # get the vertices and faces
        vertices = mesh.points
        faces = mesh.elements

    elif mode == 'fan' or mode == 'equilateral':
        # This mode creates a fan tesselation where the first vertex is the
        # centroid of the polygon and the rest are the outer boundary. Works 
        # well for equilateral polygons that have not concavities. This is 
        # probably the fastest method to tesselate an equilateral polygon with
        # good results.        

        # find the centroid of the polygon
        centroid = np.mean(points, axis=0)

        # add the centroid to the list of vertices
        vertices = np.vstack((centroid, points))

        # generate faces
        faces = np.zeros((len(points), 3), dtype=np.uint32)
        faces[:, 0] = 0
        faces[:, 1] = np.arange(1, len(points) + 1)
        faces[:, 2] = np.roll(faces[:, 1], 1)

    elif mode == 'delaunay' or mode == 'scipy':
        # Delaunay triangulation using scipy. This triangulates the polygon
        # using the Qhull library. This method is reasonably fast however it
        # outputs the convex hull of the polygon which may not be desired.

        # do a delaunay triangulation
        from scipy.spatial import Delaunay

        # create a delaunay triangulation
        result = Delaunay(points, **config)

        # get the face indices
        vertices = result.points
        faces = result.simplices

    elif mode == 'simple':
        # Simple tesselation mode where the vertices are connected in a simple
        # fan pattern from the first vertex in the provided array. This is
        # useful for simple shapes like circles or squares.
        vertices = np.vstack((points, points[0]))
        faces = np.array(
            [[0, i + 1, i + 2] for i in range(len(points) - 1)])

    else:
        raise ValueError("Invalid mode '{}' specified.".format(mode))

    # compute surface normals for all faces
    vertices = np.ascontiguousarray(vertices, dtype=np.float32)
    faces = np.ascontiguousarray(faces, dtype=np.uint32)

    # generate normals for each vertex, facing outwards
    normals = np.ascontiguousarray(
        np.tile([0., 0., -1.], (faces.shape[0], 1)), 
        dtype=np.float32)

    # generate texture coordinates which are normalized vertex positions
    texCoords = generateTexCoords(vertices)

    return vertices, normals, texCoords, faces


def mergeMeshes(meshData):
    """Merge multiple meshes into a single mesh.
    
    Merge multiple meshes into a single mesh by combining their vertex positions,
    normals, texture coordinates, and face indices. 

    Parameters
    ----------
    meshData : list of tuple
        List of tuples containing vertex positions, normals, texture coordinates,
        and face indices for each mesh to merge. Each tuple must contain the
        vertex positions, and may optionally contain the normals and texture
        coordinates. The face indices must be provided.

    Returns
    -------
    tuple
        A tuple containing the merged vertex positions, normals, texture 
        coordinates, and face indices. If `normals` or `texCoords` are not
        provided, they will be set to `None`.
    
    Examples
    --------
    Merge two meshes into a single mesh::

        vertices1, normals1, texCoords1, faces1 = createBox()
        vertices2, normals2, texCoords2, faces2 = createUVSphere()

        # merge the two meshes
        vertices, normals, texCoords, faces = mergeMeshes([
            (vertices1, normals1, texCoords1, faces1),
            (vertices2, normals2, texCoords2, faces2)])
    
    Create a tube using primatives::

        tubeOuter = createCylinder(1.0, 1.0, 16, 1)
        tubeInner = createCylinder(0.5, 1.0, 16, 1)

        # merge the tube parts
        vertices, normals, texCoords, faces = mergeMeshes(
            tubeOuter, tubeInner])

    """
    vertices = np.ascontiguousarray(
        np.vstack([i[0] for i in meshData]), dtype=np.float32)
    
    newFaces = []
    offset = 0
    for i in meshData:
        newFaces.append(i[3] + offset)
        offset += np.max(i[3]) + 1

    faces = np.ascontiguousarray(np.vstack(newFaces), dtype=np.uint32)

    # check if normals and texture coordinates are provided
    if all([i[1] is not None for i in meshData]):
        normals = np.ascontiguousarray(
            np.vstack([i[1] for i in meshData]), dtype=np.float32)
    else:
        normals = None

    if all([i[2] is not None for i in meshData]):
        texCoords = np.ascontiguousarray(
            np.vstack([i[2] for i in meshData]), dtype=np.float32)
    else:
        texCoords = None

    return vertices, normals, texCoords, faces


def nextPowerOfTwo(value):
    """Compute the next power of two for a given value.

    Parameters
    ----------
    value : int
        The value to compute the next power of two for.

    Returns
    -------
    int
        The next power of two for the given value.

    """
    return 2 ** int(np.ceil(np.log2(value)))


def fitTextureToPowerOfTwo(width, height, square=False):
    """Determine the horizontal and vertical dimensions of a image buffer that
    can contain the specified width and height, fitted to the next power of two.

    Parameters
    ----------
    width : int
        The width of the texture in pixels.
    height : int
        The height of the texture in pixels.
    square : bool, optional
        If True, the texture will be fitted to the next power of two in both
        dimensions. Default is False.

    Returns
    -------
    tuple
        A tuple containing the width and height of the texture fitted to the
        next power of two.

    Raises
    ------
    ValueError
        If the texture dimensions exceed the maximum texture size
        supported by the OpenGL implementation.

    """
    maxTexSize = getOpenGLInfo().maxTextureSize

    newWidth = nextPowerOfTwo(width)
    newHeight = nextPowerOfTwo(height)

    if newWidth > maxTexSize or newHeight > maxTexSize:
        raise ValueError("Texture dimensions exceed maximum texture size.")
    
    if square:
        newWidth = newHeight = max(newWidth, newHeight)
    
    return newWidth, newHeight


# -----------------------------
# Misc. OpenGL Helper Functions
# -----------------------------

def getIntegerv(parName):
    """Get a single integer parameter value, return it as a Python integer.

    Parameters
    ----------
    pName : int
        OpenGL property enum to query (e.g. GL_MAJOR_VERSION).

    Returns
    -------
    int

    """
    val = GL.GLint()
    GL.glGetIntegerv(parName, val)

    return int(val.value)


def getFloatv(parName):
    """Get a single float parameter value, return it as a Python float.

    Parameters
    ----------
    pName : float
        OpenGL property enum to query.

    Returns
    -------
    float

    """
    val = GL.GLfloat()
    GL.glGetFloatv(parName, val)

    return float(val.value)


def getString(parName):
    """Get a single string parameter value, return it as a Python UTF-8 string.

    Parameters
    ----------
    pName : int
        OpenGL property enum to query (e.g. GL_VENDOR).

    Returns
    -------
    str

    """
    val = ctypes.cast(GL.glGetString(parName), ctypes.c_char_p).value
    return val.decode('UTF-8')


def getModelViewMatrix():
    """Get the present model matrix from the OpenGL matrix stack.

    Returns
    -------
    ndarray
        4x4 model/view matrix.

    """
    modelview = np.zeros((4, 4), dtype=np.float32)
    
    GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX, modelview.ctypes.data_as(
        ctypes.POINTER(ctypes.c_float)))

    modelview[:, :] = np.transpose(modelview)

    return modelview


def getProjectionMatrix():
    """Get the present projection matrix from the OpenGL matrix stack.

    Returns
    -------
    ndarray
        4x4 projection matrix.

    """
    proj = np.zeros((4, 4), dtype=np.float32, order='C')

    GL.glGetFloatv(GL.GL_PROJECTION_MATRIX, proj.ctypes.data_as(
        ctypes.POINTER(ctypes.c_float)))

    proj[:, :] = np.transpose(proj)

    return proj


if __name__ == "__main__":
    pass
