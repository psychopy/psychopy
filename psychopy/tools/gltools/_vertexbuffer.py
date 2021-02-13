#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with OpenGL vertex buffer objects (VBO) and
vertex array objects (VAO).

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
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
]

import ctypes
import pyglet.gl as GL
import numpy as np
import warnings

# compatible Numpy and OpenGL types for common GL type enums
GL_COMPAT_TYPES = {
    GL.GL_FLOAT: (np.float32, GL.GLfloat),
    GL.GL_DOUBLE: (np.float64, GL.GLdouble),
    GL.GL_UNSIGNED_SHORT: (np.uint16, GL.GLushort),
    GL.GL_UNSIGNED_INT: (np.uint32, GL.GLuint),
    GL.GL_INT: (np.int32, GL.GLint),
    GL.GL_SHORT: (np.int16, GL.GLshort),
    GL.GL_HALF_FLOAT: (np.float16, GL.GLhalfARB),
    GL.GL_UNSIGNED_BYTE: (np.uint8, GL.GLubyte),
    GL.GL_BYTE: (np.int8, GL.GLbyte),
    np.float32: (GL.GL_FLOAT, GL.GLfloat),
    np.float64: (GL.GL_DOUBLE, GL.GLdouble),
    np.uint16: (GL.GL_UNSIGNED_SHORT, GL.GLushort),
    np.uint32: (GL.GL_UNSIGNED_INT, GL.GLuint),
    np.int32: (GL.GL_INT, GL.GLint),
    np.int16: (GL.GL_SHORT, GL.GLshort),
    np.float16: (GL.GL_HALF_FLOAT, GL.GLhalfARB),
    np.uint8: (GL.GL_UNSIGNED_BYTE, GL.GLubyte),
    np.int8: (GL.GL_BYTE, GL.GLbyte)
}

# OpenGL vertex attributes for shaders using GLSL 1.1 spec
gl_Vertex = 0
gl_Normal = 2
gl_Color = 3
gl_SecondaryColor = 4
gl_FogCoord = 5
gl_MultiTexCoord0 = 8
gl_MultiTexCoord1 = 9
gl_MultiTexCoord2 = 10
gl_MultiTexCoord3 = 11
gl_MultiTexCoord4 = 12
gl_MultiTexCoord5 = 13
gl_MultiTexCoord6 = 14
gl_MultiTexCoord7 = 15


# --------------------------
# Vertex Array Objects (VAO)
#

class VertexArrayInfo(object):
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
        attribute pointer indices or capabilities (ie. `GL_VERTEX_ARRAY`).
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

    def __del__(self):
        try:
            GL.glDeleteVertexArrays(1, GL.GLuint(self.name))
        except TypeError:
            pass


def createVAO(attribBuffers, indexBuffer=None, attribDivisors=None, legacy=False):
    """Create a Vertex Array object (VAO). VAOs store buffer binding states,
    reducing CPU overhead when drawing objects with vertex data stored in VBOs.

    Define vertex attributes within a VAO state by passing a mapping for
    generic attribute indices and VBO buffers.

    Parameters
    ----------
    attribBuffers : dict
        Attributes and associated VBOs to add to the VAO state. Keys are
        vertex attribute pointer indices, values are VBO descriptors to
        associate with them. Values can be `tuples` where the first value is the
        buffer descriptor, the second is the number of attribute components
        (`int`, either 2, 3 or 4), the third is the offset (`int`), and the last
        is whether to normalize the array (`bool`).
    indexBuffer : VertexBufferInfo
        Optional index buffer for faces.
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
    Create a VAO using user supplied vertex arrays::

        from psychopy.tools.gltools import createVAO, createVBO
        import pyglet.gl as GL

        # Create vertex buffers for each array, this uploads the buffers to
        # the video driver in the correct format.
        vertexPos = createVBO(vertexPos)
        texCoords = createVBO(texCoords)
        vertexNormals = createVBO(vertexNormals)
        indexBuffer = createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        # Create the VAO, passing a mapping to `attribBuffers` to indicate which
        # shader input pointer location each buffer is associated with.

        attribMapping = {0: vertexPos, 1: texCoords, 2: vertexNormals}
        vao = createVAO(attribMapping)

    You can use the constants defined in this module for pointers if you are
    using GLSL version 1.1 shaders::

        from psychopy.tools.gltools import (gl_Vertex,
            gl_Normal, gl_MultiTexCoord0, createVAO, createVBO)
        import pyglet.gl as GL

        # create vertex buffers ...

        vao = createVAO(
            {gl_Vertex: vertexPos,
             gl_MultiTexCoord0: texCoords,
             gl_Normal: vertexNormals})

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
    ``isIndexed==True``. Drawing vertex arrays using a VAO, will use the
    `indexBuffer` if available::

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
    GL.glGenVertexArrays(1, ctypes.byref(vaoId))
    GL.glBindVertexArray(vaoId)

    # add attribute pointers
    activeAttribs = {}
    bufferIndices = []
    lastBuffer = None
    for i, buffer in attribBuffers.items():
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
        lastBuffer = buffer

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

    # unbind the VAO
    GL.glBindVertexArray(0)

    # unbind the buffers afterwards, seems to be needed on MacOS
    unbindVBO(lastBuffer)

    if indexBuffer is not None:
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, 0)

    return VertexArrayInfo(vaoId.value,
                           count,
                           activeAttribs,
                           indexBuffer,
                           attribDivisors,
                           legacy)


def createVAOSimple(vertices, textureCoords, normals, faces, legacy=False):
    """Create a VAO using default attribute pointers.

    This function can be used to quickly (in terms of code) create a VAO using
    default values for vertex attribute pointers. You can pass values returned
    directly from the various shapes creation functions without needing to
    create the VBOs and attribute pointer mapping first.

    Parameters
    ----------
    vertices : ndarray
        Nx3 array of vertex positions.
    textureCoords : ndarray
        Nx3 array of texture coordinates.
    normals : ndarray
        Nx3 array of vertex normals.
    faces : ndarray
        Nx3 array of face indices where each row contains the indices of the
        faces.
    legacy : bool, optional
        Use legacy attribute pointer functions when setting the VAO state. This
        is for compatibility with older GL implementations. Key specified to
        `attribBuffers` must be `GLenum` types such as `GL_VERTEX_ARRAY` to
        indicate the capability to use.

    Returns
    -------
    VertexArrayInfo
        Vertex array object.

    Notes
    -----
    * This function is less flexible than `createVAO` and may not be supported
      on some platforms.
    * Assigned vertex pointers assume default shaders or fixed-pipeline are
      being used. Instanced drawing is not supported.
    * If you need to access any of the buffers after creating the VAO, do so
      through the `activeAttribs` property of the returned VAO instance.

    Examples
    --------
    Create a VAO to draw a disc::

        vao = createVAOSimple(*createDisc(edges=64))

        # above is equivalent to using `createVAO` with the following statements
        vertices, textureCoords, normals, faces = createDisc(edges=64)
        vertexVBO = createVBO(vertices)
        texCoordVBO = createVBO(textureCoords)
        normalsVBO = createVBO(normals)
        indexBuffer = createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        vao = createVAO({0: vertexVBO, 8: texCoordVBO, 2: normalsVBO},
                        indexBuffer=indexBuffer)

        # see! much simpler :)

    """
    # attribute arrays
    vertexVBO = createVBO(
        np.ascontiguousarray(vertices, dtype=np.float32))
    texCoordVBO = createVBO(
        np.ascontiguousarray(textureCoords, dtype=np.float32))
    normalsVBO = createVBO(
        np.ascontiguousarray(normals, dtype=np.float32))

    # prepare the array for faces
    faces = np.ascontiguousarray(faces, dtype=np.float32).flatten()
    indexBuffer = createVBO(
        faces, target=GL.GL_ELEMENT_ARRAY_BUFFER, dataType=GL.GL_UNSIGNED_INT)

    # pick the appropriate vertex pointers
    if not legacy:
        attribs = {gl_Vertex: vertexVBO,
                   gl_MultiTexCoord0: texCoordVBO,
                   gl_Normal: normalsVBO}
    else:
        attribs = {GL.GL_VERTEX_ARRAY: vertexVBO,
                   GL.GL_NORMAL_ARRAY: normalsVBO,
                   GL.GL_TEXTURE_COORD_ARRAY: texCoordVBO}

    return createVAO(attribs, indexBuffer=indexBuffer, legacy=legacy)


def drawVAO(vao, mode=GL.GL_TRIANGLES, start=0, count=None, instances=None,
            flush=False):
    """Draw a vertex array object. Uses `glDrawArrays` or `glDrawElements` if
    `instanceCount` is `None`, or else `glDrawArraysInstanced` or
    `glDrawElementsInstanced` is used.

    Parameters
    ----------
    vao : VertexArrayObject
        Vertex Array Object (VAO) to draw.
    mode : int, optional
        Drawing mode to use (e.g. GL_TRIANGLES, GL_QUADS, GL_POINTS, etc.)
    start : int, optional
        Starting index for array elements. Default is `0` which is the beginning
        of the array.
    count : int, optional
        Number of indices to draw from `start`. Must not exceed `vao.count` -
        `start`.
    instances : int or None
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
    # draw the array
    GL.glBindVertexArray(vao.name)
    if count is None:
        count = vao.count
    else:
        if count > vao.count - start:
            raise ValueError(
                "Value of `count` cannot exceed `{}`.".format(
                    vao.count - start))

    if vao.indexBuffer is not None:
        if instances is None:
            GL.glDrawElements(mode, count, vao.indexBuffer.dataType, start)
        else:
            GL.glDrawElementsInstanced(mode, count, vao.indexBuffer.dataType,
                                       start, instances)
    else:
        if instances is None:
            GL.glDrawArrays(mode, start, count)
        else:
            GL.glDrawArraysInstanced(mode, start, count, instances)

    if flush:
        GL.glFlush()

    # reset
    GL.glBindVertexArray(0)


def deleteVAO(vao):
    """Delete a Vertex Array Object (VAO). This does not delete array buffers
    bound to the VAO.

    Parameters
    ----------
    vao : VertexArrayInfo
        VAO to delete. All fields in the descriptor except `userData` will be
        reset.

    """
    if isinstance(vao, VertexArrayInfo):
        if vao.name:
            GL.glDeleteVertexArrays(1, vao.name)
            vao.name = 0
            vao.isLegacy = False
            vao.indexBuffer = None
            vao.activeAttribs = {}
            vao.count = 0


# ---------------------------
# Vertex Buffer Objects (VBO)
#


class VertexBufferInfo(object):
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
            bindTarget = GL.GL_VERTEX_ARRAY_BUFFER_BINDING
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

    def __del__(self):
        try:
            GL.glDeleteBuffers(1, self.name)
        except TypeError:
            pass


def createVBO(data,
              target=GL.GL_ARRAY_BUFFER,
              dataType=GL.GL_FLOAT,
              usage=GL.GL_STATIC_DRAW):
    """Create an array buffer object (VBO).

    Creates a VBO using input data, usually as a `ndarray` or `list`. Attributes
    common to one vertex should occupy a single row of the `data` array.

    Parameters
    ----------
    data : array_like
        A 2D array of values to write to the array buffer. The data type of the
        VBO is inferred by the type of the array. If the input is a Python
        `list` or `tuple` type, the data type of the array will be `GL_FLOAT`.
    target : :obj:`int`
        Target used when binding the buffer (e.g. `GL_VERTEX_ARRAY` or
        `GL_ELEMENT_ARRAY_BUFFER`). Default is `GL_VERTEX_ARRAY`.
    dataType : Glenum, optional
        Data type of array. Input data will be recast to an appropriate type if
        necessary. Default is `GL_FLOAT`.
    usage : GLenum or int, optional
        Usage type for the array (i.e. `GL_STATIC_DRAW`).

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
    # build input array
    npType, glType = GL_COMPAT_TYPES[dataType]
    data = np.asarray(data, dtype=npType)

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
        dataType,
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
        raise TypeError('Specified `vbo` is not at `VertexBufferInfo`.')


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
        raise TypeError('Specified `vbo` is not at `VertexBufferInfo`.')


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
    npType, glType = GL_COMPAT_TYPES[vbo.dataType]
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


def deleteVBO(vbo):
    """Delete a vertex buffer object (VBO).

    Parameters
    ----------
    vbo : VertexBufferInfo
        Descriptor of VBO to delete.

    """
    if GL.glIsBuffer(vbo.name):
        GL.glDeleteBuffers(1, vbo.name)
        vbo.name = GL.GLuint(0)


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
    versions. On nVidia graphics drivers (and most others), the following
    attribute pointer indices are aliased with reserved GLSL names within the
    shader:

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

    The above constants are defined in this module (i.e. `gl_Vertex`). You can
    use those instead of specifying the integers directly.

    Specifying `legacy` as `True` will allow for old-style pointer definitions.
    You must specify the capability as a `GLenum` associated with the pointer
    in this case::

        setVertexAttribPointer(GL_VERTEX_ARRAY, posVbo, legacy=True)
        setVertexAttribPointer(GL_TEXTURE_COORD_ARRAY, texVbo, legacy=True)
        setVertexAttribPointer(GL_NORMAL_ARRAY, normVbo, legacy=True)

    Parameters
    ----------
    index : int
        Index of the attribute to modify. You can speify integers indicating the
        shader attribute location to bind, or use the constants (e.g.
        `gl_Vertex`) if the GLSL version supports them. If `legacy=True`, this
        value should be a `GLenum` type corresponding to the capability to bind
        the buffer to, such as `GL_VERTEX_ARRAY`, `GL_TEXTURE_COORD_ARRAY`,
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

        # ... before rendering, set the attribute pointers.
        GL.glBindBuffer(vboInterleaved.target, vboInterleaved.name)
        gltools.setVertexAttribPointer(
            gl_Vertex, vboInterleaved, size=3, offset=0)  # vertex pointer
        gltools.setVertexAttribPointer(
            gl_MultiTexCoord0, vboInterleaved, size=2, offset=3)  # texture pointer
        gltools.setVertexAttribPointer(
            gl_Normal, vboInterleaved, size=3, offset=5)  # normals pointer

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

    _, glType = GL_COMPAT_TYPES[vbo.dataType]

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


if __name__ == "__main__":
    pass
