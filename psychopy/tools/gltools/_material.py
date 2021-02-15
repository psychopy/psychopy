#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""OpenGL related helper for materials.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'SimpleMaterial',
    'Material',
    'createMaterial',
    'useMaterial',
    'defaultMaterial',
    'rubberMaterials',
    'metalMaterials',
    'plasticMaterials',
    'mineralMaterials'
]

from collections import namedtuple

import numpy as np

from psychopy.visual.helpers import setColor

from ._glenv import OpenGL
from ._texture import bindTexture, unbindTexture
from ._misc import getIntegerv

GL = OpenGL.gl

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
    textures :obj:`list` of :obj:`tuple`, optional
        List of texture units and TexImage2DInfo descriptors. These will be
        written to the `textures` field of the returned descriptor. For example,
        [(GL.GL_TEXTURE0, texDesc0), (GL.GL_TEXTURE1, texDesc1)]. The number of
        texture units per-material is GL_MAX_COMBINED_TEXTURE_IMAGE_UNITS.
    face : :obj:`int`, optional
        Faces to apply material to. Values can be GL_FRONT_AND_BACK, GL_FRONT
        and GL_BACK. The default is GL_FRONT_AND_BACK.

    Returns
    -------
    Material
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


class SimpleMaterial(object):
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
                 face='front',
                 useShaders=False):
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
        textures : dict, optional
            Texture maps associated with this material. Textures are specified
            as a list. The index of textures in the list will be used to set
            the corresponding texture unit they are bound to.
        useShaders : bool
            Use per-pixel lighting when rendering this stimulus. By default,
            Blinn-Phong shading will be used.
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
        self._useShaders = useShaders

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


# ---------------------
# OpenGL/VRML Materials
# ---------------------
#
# A collection of pre-defined materials for stimuli. Keep in mind that these
# materials only approximate real-world equivalents. Values were obtained from
# http://devernay.free.fr/cours/opengl/materials.html (08/24/18). There are four
# material libraries to use, where individual material descriptors are accessed
# via property names.
#
# Usage:
#
#   useMaterial(metalMaterials.gold)
#   drawVAO(myObject)
#   ...
#
mineralMaterials = namedtuple(
    'mineralMaterials',
    ['emerald', 'jade', 'obsidian', 'pearl', 'ruby', 'turquoise'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0.0215, 0.1745, 0.0215, 1.0)),
         (GL.GL_DIFFUSE, (0.07568, 0.61424, 0.07568, 1.0)),
         (GL.GL_SPECULAR, (0.633, 0.727811, 0.633, 1.0)),
         (GL.GL_SHININESS, 0.6 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.135, 0.2225, 0.1575, 1.0)),
         (GL.GL_DIFFUSE, (0.54, 0.89, 0.63, 1.0)),
         (GL.GL_SPECULAR, (0.316228, 0.316228, 0.316228, 1.0)),
         (GL.GL_SHININESS, 0.1 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05375, 0.05, 0.06625, 1.0)),
         (GL.GL_DIFFUSE, (0.18275, 0.17, 0.22525, 1.0)),
         (GL.GL_SPECULAR, (0.332741, 0.328634, 0.346435, 1.0)),
         (GL.GL_SHININESS, 0.3 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.25, 0.20725, 0.20725, 1.0)),
         (GL.GL_DIFFUSE, (1, 0.829, 0.829, 1.0)),
         (GL.GL_SPECULAR, (0.296648, 0.296648, 0.296648, 1.0)),
         (GL.GL_SHININESS, 0.088 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.1745, 0.01175, 0.01175, 1.0)),
         (GL.GL_DIFFUSE, (0.61424, 0.04136, 0.04136, 1.0)),
         (GL.GL_SPECULAR, (0.727811, 0.626959, 0.626959, 1.0)),
         (GL.GL_SHININESS, 0.6 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.1, 0.18725, 0.1745, 1.0)),
         (GL.GL_DIFFUSE, (0.396, 0.74151, 0.69102, 1.0)),
         (GL.GL_SPECULAR, (0.297254, 0.30829, 0.306678, 1.0)),
         (GL.GL_SHININESS, 0.1 * 128.0)])
)

metalMaterials = namedtuple(
    'metalMaterials',
    ['brass', 'bronze', 'chrome', 'copper', 'gold', 'silver'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0.329412, 0.223529, 0.027451, 1.0)),
         (GL.GL_DIFFUSE, (0.780392, 0.568627, 0.113725, 1.0)),
         (GL.GL_SPECULAR, (0.992157, 0.941176, 0.807843, 1.0)),
         (GL.GL_SHININESS, 0.21794872 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.2125, 0.1275, 0.054, 1.0)),
         (GL.GL_DIFFUSE, (0.714, 0.4284, 0.18144, 1.0)),
         (GL.GL_SPECULAR, (0.393548, 0.271906, 0.166721, 1.0)),
         (GL.GL_SHININESS, 0.2 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.25, 0.25, 0.25, 1.0)),
         (GL.GL_DIFFUSE, (0.4, 0.4, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.774597, 0.774597, 0.774597, 1.0)),
         (GL.GL_SHININESS, 0.6 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.19125, 0.0735, 0.0225, 1.0)),
         (GL.GL_DIFFUSE, (0.7038, 0.27048, 0.0828, 1.0)),
         (GL.GL_SPECULAR, (0.256777, 0.137622, 0.086014, 1.0)),
         (GL.GL_SHININESS, 0.1 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.24725, 0.1995, 0.0745, 1.0)),
         (GL.GL_DIFFUSE, (0.75164, 0.60648, 0.22648, 1.0)),
         (GL.GL_SPECULAR, (0.628281, 0.555802, 0.366065, 1.0)),
         (GL.GL_SHININESS, 0.4 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.19225, 0.19225, 0.19225, 1.0)),
         (GL.GL_DIFFUSE, (0.50754, 0.50754, 0.50754, 1.0)),
         (GL.GL_SPECULAR, (0.508273, 0.508273, 0.508273, 1.0)),
         (GL.GL_SHININESS, 0.4 * 128.0)])
)

plasticMaterials = namedtuple(
    'plasticMaterials',
    ['black', 'cyan', 'green', 'red', 'white', 'yellow'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.01, 0.01, 0.01, 1.0)),
         (GL.GL_SPECULAR, (0.5, 0.5, 0.5, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0.1, 0.06, 1.0)),
         (GL.GL_DIFFUSE, (0.06, 0, 0.50980392, 1.0)),
         (GL.GL_SPECULAR, (0.50196078, 0.50196078, 0.50196078, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.1, 0.35, 0.1, 1.0)),
         (GL.GL_SPECULAR, (0.45, 0.55, 0.45, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0, 0, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.6, 0.6, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.55, 0.55, 0.55, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.7, 0.7, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.5, 0, 1.0)),
         (GL.GL_SPECULAR, (0.6, 0.6, 0.5, 1.0)),
         (GL.GL_SHININESS, 0.25 * 128.0)])
)

rubberMaterials = namedtuple(
    'rubberMaterials',
    ['black', 'cyan', 'green', 'red', 'white', 'yellow'])(
    createMaterial(
        [(GL.GL_AMBIENT, (0.02, 0.02, 0.02, 1.0)),
         (GL.GL_DIFFUSE, (0.01, 0.01, 0.01, 1.0)),
         (GL.GL_SPECULAR, (0.4, 0.4, 0.4, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0.05, 0.05, 1.0)),
         (GL.GL_DIFFUSE, (0.4, 0.5, 0.5, 1.0)),
         (GL.GL_SPECULAR, (0.04, 0.7, 0.7, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0, 0.05, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.4, 0.5, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.04, 0.7, 0.04, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05, 0, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.4, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.04, 0.04, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05, 0.05, 0.05, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.7, 0.7, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)]),
    createMaterial(
        [(GL.GL_AMBIENT, (0.05, 0.05, 0, 1.0)),
         (GL.GL_DIFFUSE, (0.5, 0.5, 0.4, 1.0)),
         (GL.GL_SPECULAR, (0.7, 0.7, 0.04, 1.0)),
         (GL.GL_SHININESS, 0.078125 * 128.0)])
)

# default material according to the OpenGL spec.
defaultMaterial = createMaterial(
    [(GL.GL_AMBIENT, (0.2, 0.2, 0.2, 1.0)),
     (GL.GL_DIFFUSE, (0.8, 0.8, 0.8, 1.0)),
     (GL.GL_SPECULAR, (0.0, 0.0, 0.0, 1.0)),
     (GL.GL_EMISSION, (0.0, 0.0, 0.0, 1.0)),
     (GL.GL_SHININESS, 0)])


