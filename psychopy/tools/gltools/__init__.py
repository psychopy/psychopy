#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related helper functions and classes.

This module grants access to the complete OpenGL API and provides additional
tools to simplify many common tasks (e.g., creating vertex buffers, loading
textures from files, etc.)

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'OpenGL',
    'getOpenGL',
    'gl_Vertex',
    'gl_Normal',
    'gl_Color',
    'gl_SecondaryColor',
    'gl_FogCoord',
    'gl_MultiTexCoord0',
    'gl_MultiTexCoord1',
    'gl_MultiTexCoord2',
    'gl_MultiTexCoord3',
    'gl_MultiTexCoord4',
    'gl_MultiTexCoord5',
    'gl_MultiTexCoord6',
    'gl_MultiTexCoord7',
    'createProgram',
    'createProgramObjectARB',
    'compileShader',
    'compileShaderObjectARB',
    'embedShaderSourceDefs',
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
    'attachBuffer',
    'detachBuffer',
    'attach',
    'detach',
    'isComplete',
    'checkFBO',
    'deleteFBO',
    'blitFBO',
    'useFBO',
    'bindFBO',
    'unbindFBO',
    'drawBuffers',
    'readBuffer',
    'getFramebufferBinding',
    'RenderbufferInfo',
    'createRenderbuffer',
    'deleteRenderbuffer',
    'createTexImage2D',
    'createTexImage2DMultisample',
    'deleteTexture',
    'VertexArrayInfo',
    'createVAO',
    'createVAOSimple',
    'drawVAO',
    'deleteVAO',
    'VertexBufferInfo',
    'createVBO',
    'bindVBO',
    'unbindVBO',
    'mapBuffer',
    'unmapBuffer',
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
    'createDisc',
    'createAnnulus',
    'createCylinder',
    'createMeshGridFromArrays',
    'createMeshGrid',
    'createBox',
    'mergeVertices',
    'smoothCreases',
    'flipFaces',
    'transformMeshPosOri',
    'calculateVertexNormals',
    'getIntegerv',
    'getFloatv',
    'getString',
    'getOpenGLInfo',
    'createTexImage2dFromFile',
    'bindTexture',
    'unbindTexture',
    'createCubeMap',
    'TexImage2DInfo',
    'TexImage2DMultisampleInfo',
    'TexCubeMapInfo',
    'getModelViewMatrix',
    'getProjectionMatrix',
    'maxSamples',
    'quadBuffersSupported',
    'pixelUpload',
    'clearColor',
    'clearDepth',
    'clearStencil',
    'clearBuffer',
    'enable',
    'disable',
    'isEnabled'
]


# all these imports define their own __all__ directives
from ._glenv import *
from ._misc import *
from ._texture import *
from ._renderbuffer import *
from ._framebuffer import *
from ._material import *
from ._light import *
from ._query import *
from ._vertexbuffer import *
from ._shader import *
from ._mesh import *


if __name__ == "__main__":
    pass
