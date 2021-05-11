#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related helper functions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
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
    'calculateVertexNormals'
]

import os
from io import StringIO
from PIL import Image
import numpy as np
import psychopy.tools.mathtools as mt
from ._glenv import OpenGL
from ._texture import createTexImage2D
from ._material import SimpleMaterial

GL = OpenGL.gl

# -------------------------
# 3D Model Helper Functions
# -------------------------
#
# These functions are used in the creation, manipulation and rendering of 3D
# model data.
#


class ObjMeshInfo(object):
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

    Loads vertex, normals, and texture coordinates from the provided *.obj file
    into arrays. These arrays can be processed then loaded into vertex buffer
    objects (VBOs) for rendering. The *.obj file must at least specify vertex
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
        Path to the *.OBJ file to load.

    Returns
    -------
    ObjMeshInfo
        Mesh data.

    See Also
    --------
    loadMtlFile : Load a *.mtl file.

    Notes
    -----
    1. This importer should work fine for most sanely generated files. Export
       your model with Blender for best results, even if you used some other
       package to create it.
    2. The mesh cannot contain both triangles and quads.

    Examples
    --------
    Loading a *.OBJ mode from file::

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
        materialGroups[key] = np.asarray(val, dtype=np.int)

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
    loadObjFile : Load an *.OBJ file.

    Examples
    --------
    Load material associated with an *.OBJ file::

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
    # based of the code found here http://www.songho.ca/opengl/gl_sphere.html
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

    if flipFaces:  # flip normals so they point inwards
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
        [[-1., 1., 0.],
         [1., 1., 0.],
         [-1., -1., 0.],
         [1., -1., 0.]],
        dtype=np.float32)

    if sx != 1.:
        vertices[:, 0] *= sx

    if sy != 1.:
        vertices[:, 1] *= sy

    # texture coordinates
    texCoords = np.ascontiguousarray([[0., 1.], [1., 1.], [0., 0.], [1., 0.]],
                                     dtype=np.float32)

    # normals, facing +Z
    normals = np.zeros_like(vertices, dtype=np.float32)
    normals[:, 0] = 0.
    normals[:, 1] = 0.
    normals[:, 2] = 1.

    # generate face index
    faces = np.ascontiguousarray([[0, 2, 1], [1, 2, 3]], dtype=np.uint32)

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


def createMeshGridFromArrays(xvals, yvals, zvals=None, tessMode='diag',
                             computeNormals=True):
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
        [1., 1., 1.], [1., 1., -1.], [1., -1., 1.],
        [1., -1., -1.], [-1., 1., -1.], [-1., 1., 1.],
        [-1., -1., -1.], [-1., -1., 1.], [-1., 1., -1.],
        [1., 1., -1.], [-1., 1., 1.], [1., 1., 1.],
        [1., -1., -1.], [-1., -1., -1.], [1., -1., 1.],
        [-1., -1., 1.], [-1., 1., 1.], [1., 1., 1.],
        [-1., -1., 1.], [1., -1., 1.], [1., 1., -1.],
        [-1., 1., -1.], [1., -1., -1.], [-1., -1., -1.]
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
        [[1., 0., 0.],  # +X
         [-1., 0., 0.],  # -X
         [0., 1., 0.],  # +Y
         [0., -1., 0.],  # -Y
         [0., 0., 1.],  # +Z
         [0., 0., -1.]],  # -Z
        4, axis=0)

    normals = np.ascontiguousarray(normals, dtype=np.float32)

    # texture coordinates for each side
    texCoords = np.tile([[0., 1.], [1., 1.], [0., 0.], [1., 0.]], (6, 1))
    texCoords = np.ascontiguousarray(texCoords, dtype=np.float32)

    # vertex indices for faces
    faces = np.ascontiguousarray([
        [0, 2, 1], [1, 2, 3],  # +X
        [4, 6, 5], [5, 6, 7],  # -X
        [8, 10, 9], [9, 10, 11],  # +Y
        [12, 14, 13], [13, 14, 15],  # -Y
        [16, 18, 17], [17, 18, 19],  # +Z
        [20, 22, 21], [21, 22, 23]  # -Z
    ], dtype=np.uint32)

    if flipFaces:
        faces = np.fliplr(faces)
        normals *= -1.0

    return vertices, texCoords, normals, faces


def transformMeshPosOri(vertices, normals, pos=(0., 0., 0.),
                        ori=(0., 0., 0., 1.)):
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
        vertices = mt.transform(pos, ori, vertices)

    if not np.allclose(ori, [0., 0., 0., 1.]):
        normals = mt.applyQuat(ori, normals)

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
    * This function only work on meshes consisting of triangle faces.

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
    """Remove creases caused my misaligned surface normals.

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


if __name__ == "__main__":
    pass
