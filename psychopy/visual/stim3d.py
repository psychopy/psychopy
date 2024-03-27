#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for 3D stimuli."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import logging
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.visual.basevisual import WindowMixin, ColorMixin
from psychopy.visual.helpers import setColor
from psychopy.colors import Color, colorSpaces
import psychopy.tools.mathtools as mt
import psychopy.tools.gltools as gt
import psychopy.tools.arraytools as at
import psychopy.tools.viewtools as vt
import psychopy.visual.shaders as _shaders

import os
from io import StringIO
from PIL import Image

import numpy as np

import pyglet.gl as GL


class LightSource:
    """Class for representing a light source in a scene. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import LightSource` when inheriting from it.


    Only point and directional lighting is supported by this object for now. The
    ambient color of the light source contributes to the scene ambient color
    defined by :py:attr:`~psychopy.visual.Window.ambientLight`.

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    """
    def __init__(self,
                 win,
                 pos=(0., 0., 0.),
                 diffuseColor=(1., 1., 1.),
                 specularColor=(1., 1., 1.),
                 ambientColor=(0., 0., 0.),
                 colorSpace='rgb',
                 contrast=1.0,
                 lightType='point',
                 attenuation=(1, 0, 0)):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window associated with this light source.
        pos : array_like
            Position of the light source (x, y, z, w). If `w=1.0` the light will
            be a point source and `x`, `y`, and `z` is the position in the
            scene. If `w=0.0`, the light source will be directional and `x`,
            `y`, and `z` will define the vector pointing to the direction the
            light source is coming from. For instance, a vector of (0, 1, 0, 0)
            will indicate that a light source is coming from above.
        diffuseColor : array_like
            Diffuse light color.
        specularColor : array_like
            Specular light color.
        ambientColor : array_like
            Ambient light color.
        colorSpace : str or None
            Colorspace for diffuse, specular, and ambient color components.
        contrast : float
            Contrast of the lighting color components. This acts as a 'gain'
            factor which scales color values. Must be between 0.0 and 1.0.
        attenuation : array_like
            Values for the constant, linear, and quadratic terms of the lighting
            attenuation formula. Default is (1, 0, 0) which results in no
            attenuation.

        """
        self.win = win

        self._pos = np.zeros((4,), np.float32)
        self._diffuseColor = Color()
        self._specularColor = Color()
        self._ambientColor = Color()
        self._lightType = None  # set later

        # internal RGB values post colorspace conversion
        self._diffuseRGB = np.array((0., 0., 0., 1.), np.float32)
        self._specularRGB = np.array((0., 0., 0., 1.), np.float32)
        self._ambientRGB = np.array((0., 0., 0., 1.), np.float32)

        self.contrast = contrast
        self.colorSpace = colorSpace

        # set the colors
        self.diffuseColor = diffuseColor
        self.specularColor = specularColor
        self.ambientColor = ambientColor

        self.lightType = lightType
        self.pos = pos

        # attenuation factors
        self._kAttenuation = np.asarray(attenuation, np.float32)

    # --------------------------------------------------------------------------
    # Lighting
    #
    # Properties about the lighting position and type. This affects the shading
    # of the material.
    #

    @property
    def pos(self):
        """Position of the light source in the scene in scene units."""
        return self._pos[:3]

    @pos.setter
    def pos(self, value):
        self._pos = np.zeros((4,), np.float32)
        self._pos[:3] = value

        if self._lightType == 'point':  # if a point source then `w` == 1.0
            self._pos[3] = 1.0

    @property
    def lightType(self):
        """Type of light source, can be 'point' or 'directional'."""
        return self._lightType

    @lightType.setter
    def lightType(self, value):
        self._lightType = value

        if self._lightType == 'point':
            self._pos[3] = 1.0
        elif self._lightType == 'directional':
            self._pos[3] = 0.0
        else:
            raise ValueError(
                "Unknown `lightType` specified, must be 'directional' or "
                "'point'.")

    @property
    def attenuation(self):
        """Values for the constant, linear, and quadratic terms of the lighting
        attenuation formula.
        """
        return self._kAttenuation

    @attenuation.setter
    def attenuation(self, value):
        self._kAttenuation = np.asarray(value, np.float32)

    # --------------------------------------------------------------------------
    # Lighting colors
    #

    @property
    def colorSpace(self):
        """The name of the color space currently being used (`str` or `None`).

        For strings and hex values this is not needed. If `None` the default
        `colorSpace` for the stimulus is used (defined during initialisation).

        Please note that changing `colorSpace` does not change stimulus
        parameters. Thus, you usually want to specify `colorSpace` before
        setting the color.

        """
        if hasattr(self, '_colorSpace'):
            return self._colorSpace
        else:
            return 'rgba'

    @colorSpace.setter
    def colorSpace(self, value):
        if value in colorSpaces:
            self._colorSpace = value
        else:
            logging.error(f"'{value}' is not a valid color space")

    @property
    def contrast(self):
        """A value that is simply multiplied by the color (`float`).

        This may be used to adjust the gain of the light source. This is applied
        to all lighting color components.

        Examples
        --------
        Basic usage::

            stim.contrast =  1.0  # unchanged contrast
            stim.contrast =  0.5  # decrease contrast
            stim.contrast =  0.0  # uniform, no contrast
            stim.contrast = -0.5  # slightly inverted
            stim.contrast = -1.0  # totally inverted

        Setting contrast outside range -1 to 1 is permitted, but may
        produce strange results if color values exceeds the monitor limits.::

            stim.contrast =  1.2  # increases contrast
            stim.contrast = -1.2  # inverts with increased contrast

        """
        return self._diffuseColor.contrast

    @contrast.setter
    def contrast(self, value):
        self._diffuseColor.contrast = value
        self._specularColor.contrast = value
        self._ambientColor.contrast = value

    @property
    def diffuseColor(self):
        """Diffuse color for the light source (`psychopy.color.Color`,
        `ArrayLike` or None).
        """
        return self._diffuseColor.render(self.colorSpace)

    @diffuseColor.setter
    def diffuseColor(self, value):
        if isinstance(value, Color):
            self._diffuseColor = value
        else:
            self._diffuseColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._diffuseColor:
            # If given an invalid color, set as transparent and log error
            self._diffuseColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        # set the RGB values
        self._diffuseRGB[:3] = self._diffuseColor.rgb1
        self._diffuseRGB[3] = self._diffuseColor.opacity

    def setDiffuseColor(self, color, colorSpace=None, operation='', log=None):
        """Set the diffuse color for the light source. Use this function if you
        wish to supress logging or apply operations on the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the diffuse component of the light source.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `diffuseColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="diffuseColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    @property
    def specularColor(self):
        """Specular color of the light source (`psychopy.color.Color`,
        `ArrayLike` or None).
        """
        return self._specularColor.render(self.colorSpace)

    @specularColor.setter
    def specularColor(self, value):
        if isinstance(value, Color):
            self._specularColor = value
        else:
            self._specularColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._specularColor:
            # If given an invalid color, set as transparent and log error
            self._specularColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        self._specularRGB[:3] = self._specularColor.rgb1
        self._specularRGB[3] = self._specularColor.opacity

    def setSpecularColor(self, color, colorSpace=None, operation='', log=None):
        """Set the diffuse color for the light source. Use this function if you
        wish to supress logging or apply operations on the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the specular component of the light source.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `diffuseColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="specularColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    @property
    def ambientColor(self):
        """Ambient color of the light source (`psychopy.color.Color`,
        `ArrayLike` or None).

        The ambient color component is used to simulate indirect lighting caused
        by the light source. For instance, light bouncing off adjacent surfaces
        or atmospheric scattering if the light source is a sun. This is
        independent of the global ambient color.

        """
        return self._ambientColor.render(self.colorSpace)

    @ambientColor.setter
    def ambientColor(self, value):
        if isinstance(value, Color):
            self._ambientColor = value
        else:
            self._ambientColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._ambientColor:
            # If given an invalid color, set as transparent and log error
            self._ambientColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        self._ambientRGB[:3] = self._ambientColor.rgb1
        self._ambientRGB[3] = self._ambientColor.opacity

    def setAmbientColor(self, color, colorSpace=None, operation='', log=None):
        """Set the ambient color for the light source.

        Use this function if you wish to supress logging or apply operations on
        the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the ambient component of the light source.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `ambientColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="ambientColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    # --------------------------------------------------------------------------
    # Lighting RGB colors
    #
    # These are the color values for the light which will be passed to the
    # shader. We protect these values since we don't want the user changing the
    # array type or size.
    #

    @property
    def diffuseRGB(self):
        """Diffuse RGB1 color of the material. This value is passed to OpenGL.
        """
        return self._diffuseRGB

    @property
    def specularRGB(self):
        """Specular RGB1 color of the material. This value is passed to OpenGL.
        """
        return self._specularRGB

    @property
    def ambientRGB(self):
        """Ambient RGB1 color of the material. This value is passed to OpenGL.
        """
        return self._ambientRGB


class SceneSkybox:
    """Class to render scene skyboxes. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import SceneSkybox` when inheriting from it.

    A skybox provides background imagery to serve as a visual reference for the
    scene. Background images are projected onto faces of a cube centered about
    the viewpoint regardless of any viewpoint translations, giving the illusion
    that the background is very far away. Usually, only one skybox can be
    rendered per buffer each frame. Render targets must have a depth buffer
    associated with them.

    Background images are specified as a set of image paths passed to
    `faceTextures`::

        sky = SceneSkybox(
            win, ('rt.jpg', 'lf.jpg', 'up.jpg', 'dn.jpg', 'bk.jpg', 'ft.jpg'))

    The skybox is rendered by calling `draw()` after drawing all other 3D
    stimuli.

    Skyboxes are not affected by lighting, however, their colors can be
    modulated by setting the window's `sceneAmbient` value. Skyboxes should be
    drawn after all other 3D stimuli, but before any successive call that clears
    the depth buffer (eg. `setPerspectiveView`, `resetEyeTransform`, etc.)


    """
    def __init__(self, win, tex=(), ori=0.0, axis=(0, 1, 0)):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this skybox is associated with.
        tex : list or tuple or TexCubeMap
            List of files paths to images to use for each face. Images are
            assigned to faces depending on their index within the list ([+X,
            -X, +Y, -Y, +Z, -Z] or [right, left, top, bottom, back, front]). If
            `None` is specified, the cube map may be specified later by setting
            the `cubemap` attribute. Alternatively, you can specify a
            `TexCubeMap` object to set the cube map directly.
        ori : float
            Rotation of the skybox about `axis` in degrees.
        axis : array_like
            Axis [ax, ay, az] to rotate about, default is (0, 1, 0).

        """
        self.win = win

        self._ori = ori
        self._axis = np.ascontiguousarray(axis, dtype=np.float32)

        if tex:
            if isinstance(tex, (list, tuple,)):
                if len(tex) == 6:
                    imgFace = []
                    for img in tex:
                        im = Image.open(img)
                        im = im.convert("RGBA")
                        pixelData = np.array(im).ctypes
                        imgFace.append(pixelData)

                    width = imgFace[0].shape[1]
                    height = imgFace[0].shape[0]

                    self._skyCubemap = gt.createCubeMap(
                        width,
                        height,
                        internalFormat=GL.GL_RGBA,
                        pixelFormat=GL.GL_RGBA,
                        dataType=GL.GL_UNSIGNED_BYTE,
                        data=imgFace,
                        unpackAlignment=1,
                        texParams={
                            GL.GL_TEXTURE_MAG_FILTER: GL.GL_LINEAR,
                            GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR,
                            GL.GL_TEXTURE_WRAP_S: GL.GL_CLAMP_TO_EDGE,
                            GL.GL_TEXTURE_WRAP_T: GL.GL_CLAMP_TO_EDGE,
                            GL.GL_TEXTURE_WRAP_R: GL.GL_CLAMP_TO_EDGE})
                else:
                   raise ValueError("Not enough textures specified, must be 6.")
            elif isinstance(tex, gt.TexCubeMap):
                self._skyCubemap = tex
            else:
                raise TypeError("Invalid type specified to `tex`.")
        else:
            self._skyCubemap = None

        # create cube vertices and faces, discard texcoords and normals
        vertices, _, _, faces = gt.createBox(1.0, True)

        # upload to buffers
        vertexVBO = gt.createVBO(vertices)

        # create an index buffer with faces
        indexBuffer = gt.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_SHORT)

        # create the VAO for drawing
        self._vao = gt.createVAO(
            {GL.GL_VERTEX_ARRAY: vertexVBO},
            indexBuffer=indexBuffer,
            legacy=True)

        # shader for the skybox
        self._shaderProg = _shaders.compileProgram(
            _shaders.vertSkyBox, _shaders.fragSkyBox)

        # store the skybox transformation matrix, this is not to be updated
        # externally
        self._skyboxViewMatrix = np.identity(4, dtype=np.float32)
        self._prtSkyboxMatrix = at.array2pointer(self._skyboxViewMatrix)

    @property
    def skyCubeMap(self):
        """Cubemap for the sky."""
        return self._skyCubemap

    @skyCubeMap.setter
    def skyCubeMap(self, value):
        self._skyCubemap = value

    def draw(self, win=None):
        """Draw the skybox.

        This should be called last after drawing other 3D stimuli for
        performance reasons.

        Parameters
        ----------
        win : `~psychopy.visual.Window`, optional
            Window to draw the skybox to. If `None`, the window set when
            initializing this object will be used. The window must share a
            context with the window which this objects was initialized with.

        """
        if self._skyCubemap is None:  # nop if no cubemap is assigned
            return

        if win is None:
            win = self.win
        else:
            win._makeCurrent()

        # enable 3D drawing
        win.draw3d = True

        # do transformations
        GL.glPushMatrix()
        GL.glLoadIdentity()

        # rotate the skybox if needed
        if self._ori != 0.0:
            GL.glRotatef(self._ori, *self._axis)

        # get/set the rotation sub-matrix from the current view matrix
        self._skyboxViewMatrix[:3, :3] = win.viewMatrix[:3, :3]
        GL.glMultTransposeMatrixf(self._prtSkyboxMatrix)

        # use the shader program
        gt.useProgram(self._shaderProg)

        # enable texture sampler
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, self._skyCubemap.name)

        # draw the cube VAO
        oldDepthFunc = win.depthFunc
        win.depthFunc = 'lequal'  # optimized for being drawn last
        gt.drawVAO(self._vao, GL.GL_TRIANGLES)
        win.depthFunc = oldDepthFunc
        gt.useProgram(0)

        # disable sampler
        GL.glBindTexture(GL.GL_TEXTURE_CUBE_MAP, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        # return to previous transformation
        GL.glPopMatrix()

        # disable 3D drawing
        win.draw3d = False


class BlinnPhongMaterial:
    """Class representing a material using the Blinn-Phong lighting model.
    This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import BlinnPhongMaterial` when inheriting
    from it.

    This class stores material information to modify the appearance of drawn
    primitives with respect to lighting, such as color (diffuse, specular,
    ambient, and emission), shininess, and textures. Simple materials are
    intended to work with features supported by the fixed-function OpenGL
    pipeline. However, one may use shaders that implement the Blinn-Phong
    shading model for per-pixel lighting.

    If shaders are enabled, the colors of objects will appear different than
    without. This is due to the lighting/material colors being computed on a
    per-pixel basis, and the formulation of the lighting model. The Phong shader
    determines the ambient color/intensity by adding up both the scene and light
    ambient colors, then multiplies them by the diffuse color of the
    material, as the ambient light's color should be a product of the surface
    reflectance (albedo) and the light color (the ambient light needs to reflect
    off something to be visible). Diffuse reflectance is Lambertian, where the
    cosine angle between the incident light ray and surface normal determines
    color. The size of specular highlights are related to the `shininess` factor
    which ranges from 1.0 to 128.0. The greater this number, the tighter the
    specular highlight making the surface appear smoother. If shaders are not
    being used, specular highlights will be computed using the Phong lighting
    model. The emission color is optional, it simply adds to the color of every
    pixel much like ambient lighting does. Usually, you would not really want
    this, but it can be used to add bias to the overall color of the shape.

    If there are no lights in the scene, the diffuse color is simply multiplied
    by the scene and material ambient color to give the final color.

    Lights are attenuated (fall-off with distance) using the formula::

        attenuationFactor = 1.0 / (k0 + k1 * distance + k2 * pow(distance, 2))

    The coefficients for attenuation can be specified by setting `attenuation`
    in the lighting object. Values `k0=1.0, k1=0.0, and k2=0.0` results in a
    light that does not fall-off with distance.

    Parameters
    ----------
    win : `~psychopy.visual.Window` or `None`
        Window this material is associated with, required for shaders and some
        color space conversions.
    diffuseColor : array_like
        Diffuse material color (r, g, b) with values between -1.0 and 1.0.
    specularColor : array_like
        Specular material color (r, g, b) with values between -1.0 and 1.0.
    ambientColor : array_like
        Ambient material color (r, g, b) with values between -1.0 and 1.0.
    emissionColor : array_like
        Emission material color (r, g, b) with values between -1.0 and 1.0.
    shininess : float
        Material shininess, usually ranges from 0.0 to 128.0.
    colorSpace : str
        Color space for `diffuseColor`, `specularColor`, `ambientColor`, and
        `emissionColor`. This is no longer used.
    opacity : float
        Opacity of the material. Ranges from 0.0 to 1.0 where 1.0 is fully
        opaque.
    contrast : float
        Contrast of the material colors.
    diffuseTexture : TexImage2D
        Optional 2D texture to apply to the material. Color values from the
        texture are blended with the `diffuseColor` of the material. The target
        primitives must have texture coordinates to specify how texels are
        mapped to the surface.
    face : str
        Face to apply material to. Values are `front`, `back` or `both`.

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    """
    def __init__(self,
                 win=None,
                 diffuseColor=(-1., -1., -1.),
                 specularColor=(-1., -1., -1.),
                 ambientColor=(-1., -1., -1.),
                 emissionColor=(-1., -1., -1.),
                 shininess=10.0,
                 colorSpace='rgb',
                 diffuseTexture=None,
                 opacity=1.0,
                 contrast=1.0,
                 face='front'):

        self.win = win

        self._diffuseColor = Color()
        self._specularColor = Color()
        self._ambientColor = Color()
        self._emissionColor = Color()
        self._shininess = float(shininess)
        self._face = None  # set later

        # internal RGB values post colorspace conversion
        self._diffuseRGB = np.array((0., 0., 0., 1.), np.float32)
        self._specularRGB = np.array((0., 0., 0., 1.), np.float32)
        self._ambientRGB = np.array((0., 0., 0., 1.), np.float32)
        self._emissionRGB = np.array((0., 0., 0., 1.), np.float32)

        # internal pointers to arrays, initialized below
        self._ptrDiffuse = None
        self._ptrSpecular = None
        self._ptrAmbient = None
        self._ptrEmission = None

        self.diffuseColor = diffuseColor
        self.specularColor = specularColor
        self.ambientColor = ambientColor
        self.emissionColor = emissionColor

        self.colorSpace = colorSpace
        self.opacity = opacity
        self.contrast = contrast
        self.face = face

        self._diffuseTexture = diffuseTexture
        self._normalTexture = None

        self._useTextures = False  # keeps track if textures are being used

    # --------------------------------------------------------------------------
    # Material colors and other properties
    #
    # These properties are used to set the color components of various material
    # properties.
    #

    @property
    def colorSpace(self):
        """The name of the color space currently being used (`str` or `None`).

        For strings and hex values this is not needed. If `None` the default
        `colorSpace` for the stimulus is used (defined during initialisation).

        Please note that changing `colorSpace` does not change stimulus
        parameters. Thus, you usually want to specify `colorSpace` before
        setting the color.

        """
        if hasattr(self, '_colorSpace'):
            return self._colorSpace
        else:
            return 'rgba'

    @colorSpace.setter
    def colorSpace(self, value):
        if value in colorSpaces:
            self._colorSpace = value
        else:
            logging.error(f"'{value}' is not a valid color space")

    @property
    def contrast(self):
        """A value that is simply multiplied by the color (`float`).

        This may be used to adjust the lightness of the material. This is
        applied to all material color components.

        Examples
        --------
        Basic usage::

            stim.contrast =  1.0  # unchanged contrast
            stim.contrast =  0.5  # decrease contrast
            stim.contrast =  0.0  # uniform, no contrast
            stim.contrast = -0.5  # slightly inverted
            stim.contrast = -1.0  # totally inverted

        Setting contrast outside range -1 to 1 is permitted, but may
        produce strange results if color values exceeds the monitor limits.::

            stim.contrast =  1.2  # increases contrast
            stim.contrast = -1.2  # inverts with increased contrast

        """
        return self._diffuseColor.contrast

    @contrast.setter
    def contrast(self, value):
        self._diffuseColor.contrast = value
        self._specularColor.contrast = value
        self._ambientColor.contrast = value
        self._emissionColor.contrast = value

    @property
    def shininess(self):
        """Material shininess coefficient (`float`).

        This is used to specify the 'tightness' of the specular highlights.
        Values usually range between 0 and 128, but the range depends on the
        specular highlight formula used by the shader.

        """
        return self._shininess

    @shininess.setter
    def shininess(self, value):
        self._shininess = float(value)

    @property
    def face(self):
        """Face to apply the material to (`str`). Possible values are one of
        `'front'`, `'back'` or `'both'`.
        """
        return self._face

    @face.setter
    def face(self, value):
        # which faces to apply the material
        if value == 'front':
            self._face = GL.GL_FRONT
        elif value == 'back':
            self._face = GL.GL_BACK
        elif value == 'both':
            self._face = GL.GL_FRONT_AND_BACK
        else:
            raise ValueError(
                "Invalid value for `face` specified, must be 'front', 'back' "
                "or 'both'.")

    @property
    def diffuseColor(self):
        """Diffuse color `(r, g, b)` for the material (`psychopy.color.Color`,
        `ArrayLike` or `None`).
        """
        return self._diffuseColor.render(self.colorSpace)

    @diffuseColor.setter
    def diffuseColor(self, value):
        if isinstance(value, Color):
            self._diffuseColor = value
        else:
            self._diffuseColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._diffuseColor:
            # If given an invalid color, set as transparent and log error
            self._diffuseColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        # compute RGB values for the shader
        self._diffuseRGB[:3] = self._diffuseColor.rgb1
        self._diffuseRGB[3] = self._diffuseColor.opacity

        # need to create a pointer for the shader
        self._ptrDiffuse = np.ctypeslib.as_ctypes(self._diffuseRGB)

    def setDiffuseColor(self, color, colorSpace=None, operation='', log=None):
        """Set the diffuse color for the material.

        Use this method if you wish to supress logging or apply operations on
        the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the diffuse component of the material.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `diffuseColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="diffuseColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    @property
    def specularColor(self):
        """Specular color `(r, g, b)` of the material (`psychopy.color.Color`,
        `ArrayLike` or `None`).
        """
        return self._specularColor.render(self.colorSpace)

    @specularColor.setter
    def specularColor(self, value):
        if isinstance(value, Color):
            self._specularColor = value
        else:
            self._specularColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._specularColor:
            # If given an invalid color, set as transparent and log error
            self._specularColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        self._specularRGB[:3] = self._specularColor.rgb1
        self._specularRGB[3] = self._specularColor.opacity

        self._ptrSpecular = np.ctypeslib.as_ctypes(self._specularRGB)

    def setSpecularColor(self, color, colorSpace=None, operation='', log=None):
        """Set the diffuse color for the material. Use this function if you
        wish to supress logging or apply operations on the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the specular component of the light source.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `diffuseColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="specularColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    @property
    def ambientColor(self):
        """Ambient color `(r, g, b)` of the material (`psychopy.color.Color`,
        `ArrayLike` or `None`).
        """
        return self._ambientColor.render(self.colorSpace)

    @ambientColor.setter
    def ambientColor(self, value):
        if isinstance(value, Color):
            self._ambientColor = value
        else:
            self._ambientColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._ambientColor:
            # If given an invalid color, set as transparent and log error
            self._ambientColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        self._ambientRGB[:3] = self._ambientColor.rgb1
        self._ambientRGB[3] = self._ambientColor.opacity

        self._ptrAmbient = np.ctypeslib.as_ctypes(self._ambientRGB)

    def setAmbientColor(self, color, colorSpace=None, operation='', log=None):
        """Set the ambient color for the material.

        Use this function if you wish to supress logging or apply operations on
        the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the ambient component of the light source.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `ambientColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="ambientColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    @property
    def emissionColor(self):
        """Emission color `(r, g, b)` of the material (`psychopy.color.Color`,
        `ArrayLike` or `None`).
        """
        return self._emissionColor.render(self.colorSpace)

    @emissionColor.setter
    def emissionColor(self, value):
        if isinstance(value, Color):
            self._emissionColor = value
        else:
            self._emissionColor = Color(
                value,
                self.colorSpace,
                contrast=self.contrast)

        if not self._emissionColor:
            # If given an invalid color, set as transparent and log error
            self._emissionColor = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        self._emissionRGB[:3] = self._emissionColor.rgb1
        self._emissionRGB[3] = self._emissionColor.opacity

        self._ptrEmission = np.ctypeslib.as_ctypes(self._emissionRGB)

    def setEmissionColor(self, color, colorSpace=None, operation='', log=None):
        """Set the emission color for the material.

        Use this function if you wish to supress logging or apply operations on
        the color component.

        Parameters
        ----------
        color : ArrayLike or `~psychopy.colors.Color`
            Color to set as the ambient component of the light source.
        colorSpace : str or None
            Colorspace to use. This is only used to set the color, the value of
            `ambientColor` after setting uses the color space of the object.
        operation : str
            Operation string.
        log : bool or None
            Enable logging.

        """
        setColor(
            obj=self,
            colorAttrib="emissionColor",
            color=color,
            colorSpace=colorSpace or self.colorSpace,
            operation=operation,
            log=log)

    # --------------------------------------------------------------------------
    # Material RGB colors
    #
    # These are the color values formatted for use in OpenGL.
    #

    @property
    def diffuseRGB(self):
        """RGB values of the diffuse color of the material (`numpy.ndarray`).
        """
        return self._diffuseRGB[:3]

    @property
    def specularRGB(self):
        """RGB values of the specular color of the material (`numpy.ndarray`).
        """
        return self._specularRGB[:3]

    @property
    def ambientRGB(self):
        """RGB values of the ambient color of the material (`numpy.ndarray`).
        """
        return self._ambientRGB[:3]

    @property
    def emissionRGB(self):
        """RGB values of the emission color of the material (`numpy.ndarray`).
        """
        return self._emissionRGB[:3]

    # Texture setter -----------------------------------------------------------

    @property
    def diffuseTexture(self):
        """Diffuse texture of the material (`psychopy.tools.gltools.TexImage2D`
        or `None`).
        """
        return self._diffuseTexture

    @diffuseTexture.setter
    def diffuseTexture(self, value):
        self._diffuseTexture = value

    # --------------------------------------------------------------------------

    def begin(self, useTextures=True):
        """Use this material for successive rendering calls.

        Parameters
        ----------
        useTextures : bool
            Enable textures.

        """
        GL.glDisable(GL.GL_COLOR_MATERIAL)  # disable color tracking
        face = self._face

        # check if lighting is enabled, otherwise don't render lights
        nLights = len(self.win.lights) if self.win.useLights else 0

        useTextures = useTextures and self.diffuseTexture is not None
        shaderKey = (nLights, useTextures)
        gt.useProgram(self.win._shaders['stim3d_phong'][shaderKey])

        # pass values to OpenGL
        GL.glMaterialfv(face, GL.GL_DIFFUSE, self._ptrDiffuse)
        GL.glMaterialfv(face, GL.GL_SPECULAR, self._ptrSpecular)
        GL.glMaterialfv(face, GL.GL_AMBIENT, self._ptrAmbient)
        GL.glMaterialfv(face, GL.GL_EMISSION, self._ptrEmission)
        GL.glMaterialf(face, GL.GL_SHININESS, self.shininess)

        # setup textures
        if useTextures and self.diffuseTexture is not None:
            self._useTextures = True
            GL.glEnable(GL.GL_TEXTURE_2D)
            gt.bindTexture(self.diffuseTexture, 0)

    def end(self, clear=True):
        """Stop using this material.

        Must be called after `begin` before using another material or else later
        drawing operations may have undefined behavior.

        Upon returning, `GL_COLOR_MATERIAL` is enabled so material colors will
        track the current `glColor`.

        Parameters
        ----------
        clear : bool
            Overwrite material state settings with default values. This
            ensures material colors are set to OpenGL defaults. You can forgo
            clearing if successive materials are used which overwrite
            `glMaterialfv` values for `GL_DIFFUSE`, `GL_SPECULAR`, `GL_AMBIENT`,
            `GL_EMISSION`, and `GL_SHININESS`. This reduces a bit of overhead
            if there is no need to return to default values intermittently
            between successive material `begin` and `end` calls. Textures and
            shaders previously enabled will still be disabled.

        """
        if clear:
            GL.glMaterialfv(
                self._face,
                GL.GL_DIFFUSE,
                (GL.GLfloat * 4)(0.8, 0.8, 0.8, 1.0))
            GL.glMaterialfv(
                self._face,
                GL.GL_SPECULAR,
                (GL.GLfloat * 4)(0.0, 0.0, 0.0, 1.0))
            GL.glMaterialfv(
                self._face,
                GL.GL_AMBIENT,
                (GL.GLfloat * 4)(0.2, 0.2, 0.2, 1.0))
            GL.glMaterialfv(
                self._face,
                GL.GL_EMISSION,
                (GL.GLfloat * 4)(0.0, 0.0, 0.0, 1.0))
            GL.glMaterialf(self._face, GL.GL_SHININESS, 0.0)

        if self._useTextures:
            self._useTextures = False
            gt.unbindTexture(self.diffuseTexture)
            GL.glDisable(GL.GL_TEXTURE_2D)

        gt.useProgram(0)

        GL.glEnable(GL.GL_COLOR_MATERIAL)


class RigidBodyPose:
    """Class for representing rigid body poses. This is a lazy-imported
    class, therefore import using full path
    `from psychopy.visual.stim3d import RigidBodyPose` when inheriting
    from it.

    This class is an abstract representation of a rigid body pose, where the
    position of the body in a scene is represented by a vector/coordinate and
    the orientation with a quaternion. Pose can be manipulated and interacted
    with using class methods and attributes. Rigid body poses assume a
    right-handed coordinate system (-Z is forward and +Y is up).

    Poses can be converted to 4x4 transformation matrices with `getModelMatrix`.
    One can use these matrices when rendering to transform the vertices of a
    model associated with the pose by passing them to OpenGL. Matrices are
    cached internally to avoid recomputing them if `pos` and `ori` attributes
    have not been updated.

    Operators `*` and `~` can be used on `RigidBodyPose` objects to combine and
    invert poses. For instance, you can multiply (`*`) poses to get a new pose
    which is the combination of both orientations and translations by::

        newPose = rb1 * rb2

    Likewise, a pose can be inverted by using the `~` operator::

        invPose = ~rb

    Multiplying a pose by its inverse will result in an identity pose with no
    translation and default orientation where `pos=[0, 0, 0]` and
    `ori=[0, 0, 0, 1]`::

        identityPose = ~rb * rb

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    """
    def __init__(self, pos=(0., 0., 0.), ori=(0., 0., 0., 1.)):
        """
        Parameters
        ----------
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real.

        """
        self._pos = np.ascontiguousarray(pos, dtype=np.float32)
        self._ori = np.ascontiguousarray(ori, dtype=np.float32)

        self._modelMatrix = mt.posOriToMatrix(
            self._pos, self._ori, dtype=np.float32)

        # computed only if needed
        self._normalMatrix = np.zeros((4, 4), dtype=np.float32, order='C')
        self._invModelMatrix = np.zeros((4, 4), dtype=np.float32, order='C')

        # additional useful vectors
        self._at = np.zeros((3,), dtype=np.float32, order='C')
        self._up = np.zeros((3,), dtype=np.float32, order='C')

        # compute matrices only if `pos` and `ori` attributes have been updated
        self._matrixNeedsUpdate = False
        self._invMatrixNeedsUpdate = True
        self._normalMatrixNeedsUpdate = True

        self.pos = pos
        self.ori = ori

        self._bounds = None

    def __repr__(self):
        return 'RigidBodyPose({}, {}), %s)'.format(self.pos, self.ori)

    @property
    def bounds(self):
        """Bounding box associated with this pose."""
        return self._bounds

    @bounds.setter
    def bounds(self, value):
        self._bounds = value

    @property
    def pos(self):
        """Position vector (X, Y, Z)."""
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = np.ascontiguousarray(value, dtype=np.float32)
        self._normalMatrixNeedsUpdate = self._matrixNeedsUpdate = \
            self._invMatrixNeedsUpdate = True

    @property
    def ori(self):
        """Orientation quaternion (X, Y, Z, W)."""
        return self._ori

    @ori.setter
    def ori(self, value):
        self._ori = np.ascontiguousarray(value, dtype=np.float32)
        self._normalMatrixNeedsUpdate = self._matrixNeedsUpdate = \
            self._invMatrixNeedsUpdate = True

    @property
    def posOri(self):
        """The position (x, y, z) and orientation (x, y, z, w)."""
        return self._pos, self._ori

    @posOri.setter
    def posOri(self, value):
        self._pos = np.ascontiguousarray(value[0], dtype=np.float32)
        self._ori = np.ascontiguousarray(value[1], dtype=np.float32)
        self._matrixNeedsUpdate = self._invMatrixNeedsUpdate = \
            self._normalMatrixNeedsUpdate = True

    @property
    def at(self):
        """Vector defining the forward direction (-Z) of this pose."""
        if self._matrixNeedsUpdate:  # matrix needs update, this need to be too
            atDir = [0., 0., -1.]
            self._at = mt.applyQuat(self.ori, atDir, out=self._at)

        return self._at

    @property
    def up(self):
        """Vector defining the up direction (+Y) of this pose."""
        if self._matrixNeedsUpdate:  # matrix needs update, this need to be too
            upDir = [0., 1., 0.]
            self._up = mt.applyQuat(self.ori, upDir, out=self._up)

        return self._up

    def __mul__(self, other):
        """Multiply two poses, combining them to get a new pose."""
        newOri = mt.multQuat(self._ori, other.ori)
        return RigidBodyPose(mt.transform(other.pos, newOri, self._pos), newOri)

    def __imul__(self, other):
        """Inplace multiplication. Transforms this pose by another."""
        self._ori = mt.multQuat(self._ori, other.ori)
        self._pos = mt.transform(other.pos, self._ori, self._pos)

    def copy(self):
        """Get a new `RigidBodyPose` object which copies the position and
        orientation of this one. Copies are independent and do not reference
        each others data.

        Returns
        -------
        RigidBodyPose
            Copy of this pose.

        """
        return RigidBodyPose(self._pos, self._ori)

    def isEqual(self, other):
        """Check if poses have similar orientation and position.

        Parameters
        ----------
        other : `RigidBodyPose`
            Other pose to compare.

        Returns
        -------
        bool
            Returns `True` is poses are effectively equal.

        """
        return np.isclose(self._pos, other.pos) and \
            np.isclose(self._ori, other.ori)

    def setIdentity(self):
        """Clear rigid body transformations.
        """
        self._pos.fill(0.0)
        self._ori[:3] = 0.0
        self._ori[3] = 1.0
        self._matrixNeedsUpdate = self._normalMatrixNeedsUpdate = \
            self._invMatrixNeedsUpdate = True

    def getOriAxisAngle(self, degrees=True):
        """Get the axis and angle of rotation for the rigid body. Converts the
        orientation defined by the `ori` quaternion to and axis-angle
        representation.

        Parameters
        ----------
        degrees : bool, optional
            Specify ``True`` if `angle` is in degrees, or else it will be
            treated as radians. Default is ``True``.

        Returns
        -------
        tuple
            Axis [rx, ry, rz] and angle.

        """
        return mt.quatToAxisAngle(self._ori, degrees)

    def setOriAxisAngle(self, axis, angle, degrees=True):
        """Set the orientation of the rigid body using an `axis` and
        `angle`. This sets the quaternion at `ori`.

        Parameters
        ----------
        axis : array_like
            Axis of rotation [rx, ry, rz].
        angle : float
            Angle of rotation.
        degrees : bool, optional
            Specify ``True`` if `angle` is in degrees, or else it will be
            treated as radians. Default is ``True``.

        """
        self.ori = mt.quatFromAxisAngle(axis, angle, degrees)

    def getYawPitchRoll(self, degrees=True):
        """Get the yaw, pitch and roll angles for this pose relative to the -Z
        world axis.

        Parameters
        ----------
        degrees : bool, optional
            Specify ``True`` if `angle` is in degrees, or else it will be
            treated as radians. Default is ``True``.

        """
        return mt.quatYawPitchRoll(self._ori, degrees)

    @property
    def modelMatrix(self):
        """Pose as a 4x4 model matrix (read-only)."""
        if not self._matrixNeedsUpdate:
            return self._modelMatrix
        else:
            return self.getModelMatrix()

    @property
    def inverseModelMatrix(self):
        """Inverse of the pose as a 4x4 model matrix (read-only)."""
        if not self._invMatrixNeedsUpdate:
            return self._invModelMatrix
        else:
            return self.getModelMatrix(inverse=True)

    @property
    def normalMatrix(self):
        """The normal transformation matrix."""
        if not self._normalMatrixNeedsUpdate:
            return self._normalMatrix
        else:
            return self.getNormalMatrix()

    def getNormalMatrix(self, out=None):
        """Get the present normal matrix.

        Parameters
        ----------
        out : ndarray or None
            Optional 4x4 array to write values to. Values written are computed
            using 32-bit float precision regardless of the data type of `out`.

        Returns
        -------
        ndarray
            4x4 normal transformation matrix.

        """
        if not self._normalMatrixNeedsUpdate:
            return self._normalMatrix

        self._normalMatrix[:, :] = np.linalg.inv(self.modelMatrix).T

        if out is not None:
            out[:, :] = self._normalMatrix[:, :]

        self._normalMatrixNeedsUpdate = False

        return self._normalMatrix

    def getModelMatrix(self, inverse=False, out=None):
        """Get the present rigid body transformation as a 4x4 matrix.

        Matrices are computed only if the `pos` and `ori` attributes have been
        updated since the last call to `getModelMatrix`. The returned matrix is
        an `ndarray` and row-major.

        Parameters
        ----------
        inverse : bool, optional
            Return the inverse of the model matrix.
        out : ndarray or None
            Optional 4x4 array to write values to. Values written are computed
            using 32-bit float precision regardless of the data type of `out`.

        Returns
        -------
        ndarray
            4x4 transformation matrix.

        Examples
        --------
        Using a rigid body pose to transform something in OpenGL::

            rb = RigidBodyPose((0, 0, -2))  # 2 meters away from origin

            # Use `array2pointer` from `psychopy.tools.arraytools` to convert
            # array to something OpenGL accepts.
            mv = array2pointer(rb.modelMatrix)

            # use the matrix to transform the scene
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            glMultTransposeMatrixf(mv)

            # draw the thing here ...

            glPopMatrix()

        """
        if self._matrixNeedsUpdate:
            self._modelMatrix = mt.posOriToMatrix(
                self._pos, self._ori, out=self._modelMatrix)

            self._matrixNeedsUpdate = False
            self._normalMatrixNeedsUpdate = self._invMatrixNeedsUpdate = True

        # only update and return the inverse matrix if requested
        if inverse:
            if self._invMatrixNeedsUpdate:
                self._invModelMatrix = mt.invertMatrix(
                    self._modelMatrix, out=self._invModelMatrix)
                self._invMatrixNeedsUpdate = False

            if out is not None:
                out[:, :] = self._invModelMatrix[:, :]

            return self._invModelMatrix  # return the inverse

        if out is not None:
            out[:, :] = self._modelMatrix[:, :]

        return self._modelMatrix

    def getViewMatrix(self, inverse=False):
        """Convert this pose into a view matrix.

        Creates a view matrix which transforms points into eye space using the
        current pose as the eye position in the scene. Furthermore, you can use
        view matrices for rendering shadows if light positions are defined
        as `RigidBodyPose` objects.

        Parameters
        ----------
        inverse : bool
            Return the inverse of the view matrix. Default is `False`.

        Returns
        -------
        ndarray
            4x4 transformation matrix.

        """
        axes = np.asarray([[0, 0, -1], [0, 1, 0]], dtype=np.float32)

        rotMatrix = mt.quatToMatrix(self._ori, dtype=np.float32)
        transformedAxes = mt.applyMatrix(rotMatrix, axes, dtype=np.float32)

        fwdVec = transformedAxes[0, :] + self._pos
        upVec = transformedAxes[1, :]

        viewMatrix = vt.lookAt(self._pos, fwdVec, upVec, dtype=np.float32)

        if inverse:
            viewMatrix = mt.invertMatrix(viewMatrix)

        return viewMatrix

    def transform(self, v, out=None):
        """Transform a vector using this pose.

        Parameters
        ----------
        v : array_like
            Vector to transform [x, y, z].
        out : ndarray or None, optional
            Optional array to write values to. Must have the same shape as
            `v`.

        Returns
        -------
        ndarray
            Transformed points.

        """
        return mt.transform(self._pos, self._ori, points=v, out=out)

    def transformNormal(self, n):
        """Rotate a normal vector with respect to this pose.

        Rotates a normal vector `n` using the orientation quaternion at `ori`.

        Parameters
        ----------
        n : array_like
            Normal to rotate (1-D with length 3).

        Returns
        -------
        ndarray
            Rotated normal `n`.

        """
        pout = np.zeros((3,), dtype=np.float32)
        pout[:] = n
        t = np.cross(self._ori[:3], n[:3]) * 2.0
        u = np.cross(self._ori[:3], t)
        t *= self._ori[3]
        pout[:3] += t
        pout[:3] += u

        return pout

    def __invert__(self):
        """Operator `~` to invert the pose. Returns a `RigidBodyPose` object."""
        return RigidBodyPose(
            -self._pos, mt.invertQuat(self._ori, dtype=np.float32))

    def invert(self):
        """Invert this pose.
        """
        self._ori = mt.invertQuat(self._ori, dtype=np.float32)
        self._pos *= -1.0

    def inverted(self):
        """Get a pose which is the inverse of this one.

        Returns
        -------
        RigidBodyPose
            This pose inverted.

        """
        return RigidBodyPose(
            -self._pos, mt.invertQuat(self._ori, dtype=np.float32))

    def distanceTo(self, v):
        """Get the distance to a pose or point in scene units.

        Parameters
        ----------
        v : RigidBodyPose or array_like
            Pose or point [x, y, z] to compute distance to.

        Returns
        -------
        float
            Distance to `v` from this pose's origin.

        """
        if hasattr(v, 'pos'):  # v is pose-like object
            targetPos = v.pos
        else:
            targetPos = np.asarray(v[:3])

        return np.sqrt(np.sum(np.square(targetPos - self.pos)))

    def interp(self, end, s):
        """Interpolate between poses.

        Linear interpolation is used on position (Lerp) while the orientation
        has spherical linear interpolation (Slerp) applied taking the shortest
        arc on the hypersphere.

        Parameters
        ----------
        end : LibOVRPose
            End pose.
        s : float
            Interpolation factor between interval 0.0 and 1.0.

        Returns
        -------
        RigidBodyPose
            Rigid body pose whose position and orientation is at `s` between
            this pose and `end`.

        """
        if not (hasattr(end, 'pos') and hasattr(end, 'ori')):
            raise TypeError("Object for `end` does not have attributes "
                            "`pos` and `ori`.")

        interpPos = mt.lerp(self._pos, end.pos, s)
        interpOri = mt.slerp(self._ori, end.ori, s)

        return RigidBodyPose(interpPos, interpOri)

    def alignTo(self, alignTo):
        """Align this pose to another point or pose.

        This sets the orientation of this pose to one which orients the forward
        axis towards `alignTo`.

        Parameters
        ----------
        alignTo : array_like or LibOVRPose
            Position vector [x, y, z] or pose to align to.

        """
        if hasattr(alignTo, 'pos'):  # v is pose-like object
            targetPos = alignTo.pos
        else:
            targetPos = np.asarray(alignTo[:3])

        fwd = np.asarray([0, 0, -1], dtype=np.float32)
        toTarget = targetPos - self._pos
        invPos = mt.applyQuat(
            mt.invertQuat(self._ori, dtype=np.float32),
            toTarget, dtype=np.float32)
        invPos = mt.normalize(invPos)

        self.ori = mt.multQuat(
            self._ori, mt.alignTo(fwd, invPos, dtype=np.float32))


class BoundingBox:
    """Class for representing object bounding boxes. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import BoundingBox` when inheriting from it.


    A bounding box is a construct which represents a 3D rectangular volume about
    some pose, defined by its minimum and maximum extents in the reference frame
    of the pose. The axes of the bounding box are aligned to the axes of the
    world or the associated pose.

    Bounding boxes are primarily used for visibility testing; to determine if
    the extents of an object associated with a pose (eg. the vertices of a
    model) falls completely outside of the viewing frustum. If so, the model can
    be culled during rendering to avoid wasting CPU/GPU resources on objects not
    visible to the viewer.

    """
    def __init__(self, extents=None):
        self._extents = np.zeros((2, 3), np.float32)
        self._posCorners = np.zeros((8, 4), np.float32)

        if extents is not None:
            self._extents[0, :] = extents[0]
            self._extents[1, :] = extents[1]
        else:
            self.clear()

        self._computeCorners()

    def _computeCorners(self):
        """Compute the corners of the bounding box.

        These values are cached to speed up computations if extents hasn't been
        updated.

        """
        for i in range(8):
            self._posCorners[i, 0] = \
                self._extents[1, 0] if (i & 1) else self._extents[0, 0]
            self._posCorners[i, 1] = \
                self._extents[1, 1] if (i & 2) else self._extents[0, 1]
            self._posCorners[i, 2] = \
                self._extents[1, 2] if (i & 4) else self._extents[0, 2]
            self._posCorners[i, 3] = 1.0

    @property
    def isValid(self):
        """`True` if the bounding box is valid."""
        return np.all(self._extents[0, :] <= self._extents[1, :])

    @property
    def extents(self):
        return self._extents

    @extents.setter
    def extents(self, value):
        self._extents[0, :] = value[0]
        self._extents[1, :] = value[1]
        self._computeCorners()

    def fit(self, verts):
        """Fit the bounding box to vertices."""
        np.amin(verts, axis=0, out=self._extents[0])
        np.amax(verts, axis=0, out=self._extents[1])
        self._computeCorners()

    def clear(self):
        """Clear a bounding box, invalidating it."""
        self._extents[0, :] = np.finfo(np.float32).max
        self._extents[1, :] = np.finfo(np.float32).min
        self._computeCorners()


class BaseRigidBodyStim(ColorMixin, WindowMixin):
    """Base class for rigid body 3D stimuli.

    This class handles the pose of a rigid body 3D stimulus. Poses are
    represented by a `RigidBodyClass` object accessed via `thePose` attribute.

    Any class the implements `pos` and `ori` attributes can be used in place of
    a `RigidBodyPose` instance for `thePose`. This common interface allows for
    custom classes which handle 3D transformations to be used for stimulus
    transformations (eg. `LibOVRPose` in PsychXR can be used instead of
    `RigidBodyPose` which supports more VR specific features).

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    """
    def __init__(self,
                 win,
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 color=(0.0, 0.0, 0.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 name='',
                 autoLog=True):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real.

        """
        self.name = name

        super(BaseRigidBodyStim, self).__init__()

        self.win = win
        self.autoLog = autoLog
        self.colorSpace = colorSpace
        self.contrast = contrast
        self.opacity = opacity
        self.color = color

        self._thePose = RigidBodyPose(pos, ori)
        self.material = None

        self._vao = None

    @property
    def thePose(self):
        """The pose of the rigid body. This is a class which has `pos` and `ori`
        attributes."""
        return self._thePose

    @thePose.setter
    def thePose(self, value):
        if hasattr(value, 'pos') and hasattr(value, 'ori'):
            self._thePose = value
        else:
            raise AttributeError(
                'Class set to `thePose` does not implement `pos` or `ori`.')

    @property
    def pos(self):
        """Position vector (X, Y, Z)."""
        return self.thePose.pos

    @pos.setter
    def pos(self, value):
        self.thePose.pos = value

    def getPos(self):
        return self.thePose.pos

    def setPos(self, pos):
        self.thePose.pos = pos

    @property
    def ori(self):
        """Orientation quaternion (X, Y, Z, W)."""
        return self.thePose.ori

    @ori.setter
    def ori(self, value):
        self.thePose.ori = value

    def getOri(self):
        return self.thePose.ori

    def setOri(self, ori):
        self.thePose.ori = ori

    def getOriAxisAngle(self, degrees=True):
        """Get the axis and angle of rotation for the 3D stimulus. Converts the
        orientation defined by the `ori` quaternion to and axis-angle
        representation.

        Parameters
        ----------
        degrees : bool, optional
            Specify ``True`` if `angle` is in degrees, or else it will be
            treated as radians. Default is ``True``.

        Returns
        -------
        tuple
            Axis `[rx, ry, rz]` and angle.

        """
        return self.thePose.getOriAxisAngle(degrees)

    def setOriAxisAngle(self, axis, angle, degrees=True):
        """Set the orientation of the 3D stimulus using an `axis` and
        `angle`. This sets the quaternion at `ori`.

        Parameters
        ----------
        axis : array_like
            Axis of rotation [rx, ry, rz].
        angle : float
            Angle of rotation.
        degrees : bool, optional
            Specify ``True`` if `angle` is in degrees, or else it will be
            treated as radians. Default is ``True``.

        """
        self.thePose.setOriAxisAngle(axis, angle, degrees)

    def _createVAO(self, vertices, textureCoords, normals, faces):
        """Create a vertex array object for handling vertex attribute data.
        """
        self.thePose.bounds = BoundingBox()
        self.thePose.bounds.fit(vertices)

        # upload to buffers
        vertexVBO = gt.createVBO(vertices)
        texCoordVBO = gt.createVBO(textureCoords)
        normalsVBO = gt.createVBO(normals)

        # create an index buffer with faces
        indexBuffer = gt.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        return gt.createVAO({GL.GL_VERTEX_ARRAY: vertexVBO,
                             GL.GL_TEXTURE_COORD_ARRAY: texCoordVBO,
                             GL.GL_NORMAL_ARRAY: normalsVBO},
                            indexBuffer=indexBuffer, legacy=True)

    def draw(self, win=None):
        """Draw the stimulus.

        This should work for stimuli using a single VAO and material. More
        complex stimuli with multiple materials should override this method to
        correctly handle that case.

        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.

        """
        if win is None:
            win = self.win
        else:
            self._selectWindow(win)

        # nop if there is no VAO to draw
        if self._vao is None:
            return

        win.draw3d = True

        # apply transformation to mesh
        GL.glPushMatrix()
        GL.glMultTransposeMatrixf(at.array2pointer(self.thePose.modelMatrix))

        if self.material is not None:  # has a material, use it
            useTexture = self.material.diffuseTexture is not None
            self.material.begin(useTexture)
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)
            self.material.end()
        else:  # doesn't have a material, use class colors
            r, g, b = self._foreColor.render('rgb')
            color = np.ctypeslib.as_ctypes(
                np.array((r, g, b, self.opacity), np.float32))

            nLights = len(self.win.lights)
            shaderKey = (nLights, False)
            gt.useProgram(self.win._shaders['stim3d_phong'][shaderKey])

            # pass values to OpenGL as material
            GL.glColor4f(r, g, b, self.opacity)
            GL.glMaterialfv(GL.GL_FRONT, GL.GL_DIFFUSE, color)
            GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT, color)

            gt.drawVAO(self._vao, GL.GL_TRIANGLES)

            gt.useProgram(0)

        GL.glPopMatrix()

        win.draw3d = False

    @attributeSetter
    def units(self, value):
        """
        None, 'norm', 'cm', 'deg', 'degFlat', 'degFlatPos', or 'pix'

        If None then the current units of the
        :class:`~psychopy.visual.Window` will be used.
        See :ref:`units` for explanation of other options.

        Note that when you change units, you don't change the stimulus
        parameters and it is likely to change appearance. Example::

            # This stimulus is 20% wide and 50% tall with respect to window
            stim = visual.PatchStim(win, units='norm', size=(0.2, 0.5)

            # This stimulus is 0.2 degrees wide and 0.5 degrees tall.
            stim.units = 'deg'
        """
        if value is not None and len(value):
            self.__dict__['units'] = value
        else:
            self.__dict__['units'] = self.win.units

    def _updateList(self):
        """The user shouldn't need this method since it gets called
        after every call to .set()
        Chooses between using and not using shaders each call.
        """
        pass

    def isVisible(self):
        """Check if the object is visible to the observer.

        Test if a pose's bounding box or position falls outside of an eye's view
        frustum.

        Poses can be assigned bounding boxes which enclose any 3D models
        associated with them. A model is not visible if all the corners of the
        bounding box fall outside the viewing frustum. Therefore any primitives
        (i.e. triangles) associated with the pose can be culled during rendering
        to reduce CPU/GPU workload.

        Returns
        -------
        bool
            `True` if the object's bounding box is visible.

        Examples
        --------
        You can avoid running draw commands if the object is not visible by
        doing a visibility test first::

            if myStim.isVisible():
                myStim.draw()

        """
        if self.thePose.bounds is None:
            return True

        if not self.thePose.bounds.isValid:
            return True

        # transformation matrix
        mvpMatrix = np.zeros((4, 4), dtype=np.float32)
        np.matmul(self.win.projectionMatrix, self.win.viewMatrix, out=mvpMatrix)
        np.matmul(mvpMatrix, self.thePose.modelMatrix, out=mvpMatrix)

        # compute bounding box corners in current view
        corners = self.thePose.bounds._posCorners.dot(mvpMatrix.T)

        # check if corners are completely off to one side of the frustum
        if not np.any(corners[:, 0] > -corners[:, 3]):
            return False

        if not np.any(corners[:, 0] < corners[:, 3]):
            return False

        if not np.any(corners[:, 1] > -corners[:, 3]):
            return False

        if not np.any(corners[:, 1] < corners[:, 3]):
            return False

        if not np.any(corners[:, 2] > -corners[:, 3]):
            return False

        if not np.any(corners[:, 2] < corners[:, 3]):
            return False

        return True

    def getRayIntersectBounds(self, rayOrig, rayDir):
        """Get the point which a ray intersects the bounding box of this mesh.

        Parameters
        ----------
        rayOrig : array_like
            Origin of the ray in space [x, y, z].
        rayDir : array_like
            Direction vector of the ray [x, y, z], should be normalized.

        Returns
        -------
        tuple
            Coordinate in world space of the intersection and distance in scene
            units from `rayOrig`. Returns `None` if there is no intersection.

        """
        if self.thePose.bounds is None:
            return None  # nop

        return mt.intersectRayOBB(rayOrig,
                                  rayDir,
                                  self.thePose.modelMatrix,
                                  self.thePose.bounds.extents,
                                  dtype=np.float32)


class SphereStim(BaseRigidBodyStim):
    """Class for drawing a UV sphere. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import SphereStim` when inheriting from it.


    The resolution of the sphere mesh can be controlled by setting `sectors`
    and `stacks` which controls the number of latitudinal and longitudinal
    subdivisions, respectively. The radius of the sphere is defined by setting
    `radius` expressed in scene units (meters if using a perspective
    projection).

    Calling the `draw` method will render the sphere to the current buffer. The
    render target (FBO or back buffer) must have a depth buffer attached to it
    for the object to be rendered correctly. Shading is used if the current
    window has light sources defined and lighting is enabled (by setting
    `useLights=True` before drawing the stimulus).

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    Examples
    --------
    Creating a red sphere 1.5 meters away from the viewer with radius 0.25::

        redSphere = SphereStim(win,
                               pos=(0., 0., -1.5),
                               radius=0.25,
                               color=(1, 0, 0))

    """
    def __init__(self,
                 win,
                 radius=0.5,
                 subdiv=(32, 32),
                 flipFaces=False,
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 color=(0., 0., 0.),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 useMaterial=None,
                 name='',
                 autoLog=True):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.
        radius : float
            Radius of the sphere in scene units.
        subdiv : array_like
            Number of latitudinal and longitudinal subdivisions `(lat, long)`
            for the sphere mesh. The greater the number, the smoother the sphere
            will appear.
        flipFaces : bool, optional
            If `True`, normals and face windings will be set to point inward
            towards the center of the sphere. Texture coordinates will remain
            the same. Default is `False`.
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real. If you prefer specifying rotations in
            axis-angle format, call `setOriAxisAngle` after initialization.
        useMaterial : PhongMaterial, optional
            Material to use. The material can be configured by accessing the
            `material` attribute after initialization. If not material is
            specified, the diffuse and ambient color of the shape will be set
            by `color`.
        color : array_like
            Diffuse and ambient color of the stimulus if `useMaterial` is not
            specified. Values are with respect to `colorSpace`.
        colorSpace : str
            Colorspace of `color` to use.
        contrast : float
            Contrast of the stimulus, value modulates the `color`.
        opacity : float
            Opacity of the stimulus ranging from 0.0 to 1.0. Note that
            transparent objects look best when rendered from farthest to
            nearest.
        name : str
            Name of this object for logging purposes.
        autoLog : bool
            Enable automatic logging on attribute changes.

        """
        super(SphereStim, self).__init__(win,
                                         pos=pos,
                                         ori=ori,
                                         color=color,
                                         colorSpace=colorSpace,
                                         contrast=contrast,
                                         opacity=opacity,
                                         name=name,
                                         autoLog=autoLog)

        # create a vertex array object for drawing
        vertices, textureCoords, normals, faces = gt.createUVSphere(
            sectors=subdiv[0],
            stacks=subdiv[1],
            radius=radius,
            flipFaces=flipFaces)
        self._vao = self._createVAO(vertices, textureCoords, normals, faces)

        self.material = useMaterial

        self._radius = radius  # for raypicking

        self.extents = (vertices.min(axis=0), vertices.max(axis=0))

    def getRayIntersectSphere(self, rayOrig, rayDir):
        """Get the point which a ray intersects the sphere.

        Parameters
        ----------
        rayOrig : array_like
            Origin of the ray in space [x, y, z].
        rayDir : array_like
            Direction vector of the ray [x, y, z], should be normalized.

        Returns
        -------
        tuple
            Coordinate in world space of the intersection and distance in scene
            units from `rayOrig`. Returns `None` if there is no intersection.

        """
        return mt.intersectRaySphere(rayOrig,
                                     rayDir,
                                     self.thePose.pos,
                                     self._radius,
                                     dtype=np.float32)


class BoxStim(BaseRigidBodyStim):
    """Class for drawing 3D boxes. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import BoxStim` when inheriting from it.


    Draws a rectangular box with dimensions specified by `size` (length, width,
    height) in scene units.

    Calling the `draw` method will render the box to the current buffer. The
    render target (FBO or back buffer) must have a depth buffer attached to it
    for the object to be rendered correctly. Shading is used if the current
    window has light sources defined and lighting is enabled (by setting
    `useLights=True` before drawing the stimulus).

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    """
    def __init__(self,
                 win,
                 size=(.5, .5, .5),
                 flipFaces=False,
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 color=(0., 0., 0.),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 useMaterial=None,
                 textureScale=None,
                 name='',
                 autoLog=True):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.
        size : tuple or float
            Dimensions of the mesh. If a single value is specified, the box will
            be a cube. Provide a tuple of floats to specify the width, length,
            and height of the box (eg. `size=(0.2, 1.3, 2.1)`) in scene units.
        flipFaces : bool, optional
            If `True`, normals and face windings will be set to point inward
            towards the center of the box. Texture coordinates will remain the
            same. Default is `False`.
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real. If you prefer specifying rotations in
            axis-angle format, call `setOriAxisAngle` after initialization.
        useMaterial : PhongMaterial, optional
            Material to use. The material can be configured by accessing the
            `material` attribute after initialization. If not material is
            specified, the diffuse and ambient color of the shape will track the
            current color specified by `glColor`.
            color : array_like
            Diffuse and ambient color of the stimulus if `useMaterial` is not
            specified. Values are with respect to `colorSpace`.
        colorSpace : str
            Colorspace of `color` to use.
        contrast : float
            Contrast of the stimulus, value modulates the `color`.
        opacity : float
            Opacity of the stimulus ranging from 0.0 to 1.0. Note that
            transparent objects look best when rendered from farthest to
            nearest.
        textureScale : array_like or float, optional
            Scaling factors for texture coordinates (sx, sy). By default,
            a factor of 1 will have the entire texture cover the surface of the
            mesh. If a single number is provided, the texture will be scaled
            uniformly.
        name : str
            Name of this object for logging purposes.
        autoLog : bool
            Enable automatic logging on attribute changes.

        """
        super(BoxStim, self).__init__(
            win,
            pos=pos,
            ori=ori,
            color=color,
            colorSpace=colorSpace,
            contrast=contrast,
            opacity=opacity,
            name=name,
            autoLog=autoLog)

        # create a vertex array object for drawing
        vertices, texCoords, normals, faces = gt.createBox(size, flipFaces)

        # scale the texture
        if textureScale is not None:
            if isinstance(textureScale, (int, float)):
                texCoords *= textureScale
            else:
                texCoords *= np.asarray(textureScale, dtype=np.float32)

        self._vao = self._createVAO(vertices, texCoords, normals, faces)

        self.setColor(color, colorSpace=self.colorSpace, log=False)
        self.material = useMaterial

        self.extents = (vertices.min(axis=0), vertices.max(axis=0))


class PlaneStim(BaseRigidBodyStim):
    """Class for drawing planes. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import PlaneStim` when inheriting from it.


    Draws a plane with dimensions specified by `size` (length, width) in scene
    units.

    Calling the `draw` method will render the plane to the current buffer. The
    render target (FBO or back buffer) must have a depth buffer attached to it
    for the object to be rendered correctly. Shading is used if the current
    window has light sources defined and lighting is enabled (by setting
    `useLights=True` before drawing the stimulus).

    Warnings
    --------
    This class is experimental and may result in undefined behavior.

    """
    def __init__(self,
                 win,
                 size=(.5, .5),
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 color=(0., 0., 0.),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 useMaterial=None,
                 textureScale=None,
                 name='',
                 autoLog=True):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.
        size : tuple or float
            Dimensions of the mesh. If a single value is specified, the plane
            will be a square. Provide a tuple of floats to specify the width and
            length of the plane (eg. `size=(0.2, 1.3)`).
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real. If you prefer specifying rotations in
            axis-angle format, call `setOriAxisAngle` after initialization. By
            default, the plane is oriented with normal facing the +Z axis of the
            scene.
        useMaterial : PhongMaterial, optional
            Material to use. The material can be configured by accessing the
            `material` attribute after initialization. If not material is
            specified, the diffuse and ambient color of the shape will track the
            current color specified by `glColor`.
        colorSpace : str
            Colorspace of `color` to use.
        contrast : float
            Contrast of the stimulus, value modulates the `color`.
        opacity : float
            Opacity of the stimulus ranging from 0.0 to 1.0. Note that
            transparent objects look best when rendered from farthest to
            nearest.
        textureScale : array_like or float, optional
            Scaling factors for texture coordinates (sx, sy). By default,
            a factor of 1 will have the entire texture cover the surface of the
            mesh. If a single number is provided, the texture will be scaled
            uniformly.
        name : str
            Name of this object for logging purposes.
        autoLog : bool
            Enable automatic logging on attribute changes.

        """
        super(PlaneStim, self).__init__(
            win,
            pos=pos,
            ori=ori,
            color=color,
            colorSpace=colorSpace,
            contrast=contrast,
            opacity=opacity,
            name=name,
            autoLog=autoLog)

        # create a vertex array object for drawing
        vertices, texCoords, normals, faces = gt.createPlane(size)

        # scale the texture
        if textureScale is not None:
            if isinstance(textureScale, (int, float)):
                texCoords *= textureScale
            else:
                texCoords *= np.asarray(textureScale, dtype=np.float32)

        self._vao = self._createVAO(vertices, texCoords, normals, faces)

        self.setColor(color, colorSpace=self.colorSpace, log=False)
        self.material = useMaterial

        self.extents = (vertices.min(axis=0), vertices.max(axis=0))


class ObjMeshStim(BaseRigidBodyStim):
    """Class for loading and presenting 3D stimuli in the Wavefront OBJ format.
    This is a lazy-imported class, therefore import using full path 
    `from psychopy.visual.stim3d import ObjMeshStim` when inheriting from it.


    Calling the `draw` method will render the mesh to the current buffer. The
    render target (FBO or back buffer) must have a depth buffer attached to it
    for the object to be rendered correctly. Shading is used if the current
    window has light sources defined and lighting is enabled (by setting
    `useLights=True` before drawing the stimulus).

    Vertex positions, texture coordinates, and normals are loaded and packed
    into a single vertex buffer object (VBO). Vertex array objects (VAO) are
    created for each material with an index buffer referencing vertices assigned
    that material in the VBO. For maximum performance, keep the number of
    materials per object as low as possible, as switching between VAOs has some
    overhead.

    Material attributes are read from the material library file (*.MTL)
    associated with the *.OBJ file. This file will be automatically searched for
    and read during loading. Afterwards you can edit material properties by
    accessing the data structure of the `materials` attribute.

    Keep in mind that OBJ shapes are rigid bodies, the mesh itself cannot be
    deformed during runtime. However, meshes can be positioned and rotated as
    desired by manipulating the `RigidBodyPose` instance accessed through the
    `thePose` attribute.

    Warnings
    --------
        Loading an *.OBJ file is a slow process, be sure to do this outside
        of any time-critical routines! This class is experimental and may result
        in undefined behavior.

    Examples
    --------
    Loading an *.OBJ file from a disk location::

        myObjStim = ObjMeshStim(win, '/path/to/file/model.obj')

    """
    def __init__(self,
                 win,
                 objFile,
                 pos=(0, 0, 0),
                 ori=(0, 0, 0, 1),
                 useMaterial=None,
                 loadMtllib=True,
                 color=(0.0, 0.0, 0.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 name='',
                 autoLog=True):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.
        size : tuple or float
            Dimensions of the mesh. If a single value is specified, the plane
            will be a square. Provide a tuple of floats to specify the width and
            length of the box (eg. `size=(0.2, 1.3)`).
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real. If you prefer specifying rotations in
            axis-angle format, call `setOriAxisAngle` after initialization. By
            default, the plane is oriented with normal facing the +Z axis of the
            scene.
        useMaterial : PhongMaterial, optional
            Material to use for all sub-meshes. The material can be configured
            by accessing the `material` attribute after initialization. If no
            material is specified, `color` will modulate the diffuse and
            ambient colors for all meshes in the model. If `loadMtllib` is
            `True`, this value should be `None`.
        loadMtllib : bool
            Load materials from the MTL file associated with the mesh. This will
            override `useMaterial` if it is `None`. The value of `materials`
            after initialization will be a dictionary where keys are material
            names and values are materials. Any textures associated with the
            model will be loaded as per the material requirements.

        """
        super(ObjMeshStim, self).__init__(
            win,
            pos=pos,
            ori=ori,
            color=color,
            colorSpace=colorSpace,
            contrast=contrast,
            opacity=opacity,
            name=name,
            autoLog=autoLog)

        # load the OBJ file
        objModel = gt.loadObjFile(objFile)

        # load materials from file if requested
        if loadMtllib and self.material is None:
            self.material = self._loadMtlLib(objModel.mtlFile)
        else:
            self.material = useMaterial

        # load vertex data into an interleaved VBO
        buffers = np.ascontiguousarray(
            np.hstack((objModel.vertexPos,
                       objModel.texCoords,
                       objModel.normals)),
            dtype=np.float32)

        # upload to buffer
        vertexAttr = gt.createVBO(buffers)

        # load vertex data into VAOs
        self._vao = {}  # dictionary for VAOs
        # for each material create a VAO
        # keys are material names, values are index buffers
        for material, faces in objModel.faces.items():
            # convert index buffer to VAO
            indexBuffer = \
                gt.createVBO(
                    faces.flatten(),  # flatten face index for element array
                    target=GL.GL_ELEMENT_ARRAY_BUFFER,
                    dataType=GL.GL_UNSIGNED_INT)

            # see `setVertexAttribPointer` for more information about attribute
            # pointer indices
            self._vao[material] = gt.createVAO(
                {GL.GL_VERTEX_ARRAY: (vertexAttr, 3),
                 GL.GL_TEXTURE_COORD_ARRAY: (vertexAttr, 2, 3),
                 GL.GL_NORMAL_ARRAY: (vertexAttr, 3, 5, True)},
                indexBuffer=indexBuffer, legacy=True)

        self.extents = objModel.extents

        self.thePose.bounds = BoundingBox()
        self.thePose.bounds.fit(objModel.vertexPos)

    def _loadMtlLib(self, mtlFile):
        """Load a material library associated with the OBJ file. This is usually
        called by the constructor for this class.

        Parameters
        ----------
        mtlFile : str
            Path to MTL file.

        """
        with open(mtlFile, 'r') as mtl:
            mtlBuffer = StringIO(mtl.read())

        foundMaterials = {}
        foundTextures = {}
        thisMaterial = 0
        for line in mtlBuffer.readlines():
            line = line.strip()
            if line.startswith('newmtl '):  # new material
                thisMaterial = line[7:]
                foundMaterials[thisMaterial] = BlinnPhongMaterial(self.win)
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
                        os.path.join(os.path.split(mtlFile)[0], textureName))
                    im = im.transpose(Image.FLIP_TOP_BOTTOM)
                    im = im.convert("RGBA")
                    pixelData = np.array(im).ctypes
                    width = pixelData.shape[1]
                    height = pixelData.shape[0]
                    foundTextures[textureName] = gt.createTexImage2D(
                        width,
                        height,
                        internalFormat=GL.GL_RGBA,
                        pixelFormat=GL.GL_RGBA,
                        dataType=GL.GL_UNSIGNED_BYTE,
                        data=pixelData,
                        unpackAlignment=1,
                        texParams={GL.GL_TEXTURE_MAG_FILTER: GL.GL_LINEAR,
                                   GL.GL_TEXTURE_MIN_FILTER: GL.GL_LINEAR})
                foundMaterials[thisMaterial].diffuseTexture = \
                    foundTextures[textureName]

        return foundMaterials

    def draw(self, win=None):
        """Draw the mesh.

        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.

        """
        if win is None:
            win = self.win
        else:
            self._selectWindow(win)

        win.draw3d = True

        GL.glPushMatrix()
        GL.glMultTransposeMatrixf(at.array2pointer(self.thePose.modelMatrix))

        # iterate over materials, draw associated VAOs
        if self.material is not None:
            # if material is a dictionary
            if isinstance(self.material, dict):
                for materialName, materialDesc in self.material.items():
                    materialDesc.begin()
                    gt.drawVAO(self._vao[materialName], GL.GL_TRIANGLES)
                    materialDesc.end()
            else:
                # material is a single item
                self.material.begin()
                for materialName, _ in self._vao.items():
                    gt.drawVAO(self._vao[materialName], GL.GL_TRIANGLES)
                self.material.end()
        else:
            r, g, b = self._foreColor.render('rgb')
            color = np.ctypeslib.as_ctypes(
                np.array((r, g, b, self.opacity), np.float32))

            nLights = len(self.win.lights)
            shaderKey = (nLights, False)
            gt.useProgram(self.win._shaders['stim3d_phong'][shaderKey])

            # pass values to OpenGL as material
            GL.glColor4f(r, g, b, self.opacity)
            GL.glMaterialfv(GL.GL_FRONT, GL.GL_DIFFUSE, color)
            GL.glMaterialfv(GL.GL_FRONT, GL.GL_AMBIENT, color)

            for materialName, _ in self._vao.items():
                gt.drawVAO(self._vao[materialName], GL.GL_TRIANGLES)

            gt.useProgram(0)

        GL.glPopMatrix()

        win.draw3d = False
