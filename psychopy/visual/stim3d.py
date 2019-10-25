#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for 3D stimuli."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


from psychopy.visual.basevisual import ColorMixin
from psychopy.visual.helpers import setColor
import psychopy.tools.mathtools as mt
import psychopy.tools.gltools as gt
import psychopy.tools.arraytools as at
import numpy as np


import pyglet.gl as GL

# shader flags
SHADER_NONE = 0x00
SHADER_USE_TEXTURES = 0x01


class LightSource(object):
    """Class for representing a light source in a scene.

    Only point and directional lighting is supported by this object for now. The
    ambient color of the light source contributes to the scene ambient color
    defined by :py:attr:`~psychopy.visual.Window.ambientLight`.

    """
    def __init__(self,
                 win,
                 pos=(0., 0., 0.),
                 diffuseColor=(1., 1., 1.),
                 specularColor=(1., 1., 1.),
                 ambientColor=(0., 0., 0.),
                 colorSpace='rgb',
                 lightType='point',
                 kAttenuation=(1, 0, 0)):
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
        colorSpace : str
            Colorspace for `diffuse`, `specular`, and `ambient` colors.
        kAttenuation : array_like
            Values for the constant, linear, and quadratic terms of the lighting
            attenuation formula. Default is (1, 0, 0) which results in no
            attenuation.

        """
        self.win = win

        self._pos = np.zeros((4,), np.float32)
        self._diffuseColor = np.zeros((3,), np.float32)
        self._specularColor = np.zeros((3,), np.float32)
        self._ambientColor = np.zeros((3,), np.float32)

        # internal RGB values post colorspace conversion
        self._diffuseRGB = np.array((0., 0., 0., 1.), np.float32)
        self._specularRGB = np.array((0., 0., 0., 1.), np.float32)
        self._ambientRGB = np.array((0., 0., 0., 1.), np.float32)

        self.colorSpace = colorSpace
        self.diffuseColor = diffuseColor
        self.specularColor = specularColor
        self.ambientColor = ambientColor

        self._lightType = lightType
        self.pos = pos

        # attenuation factors
        self._kAttenuation = np.asarray(kAttenuation, np.float32)

    @property
    def pos(self):
        """Position of the light source in the scene in scene units."""
        return self._pos[:3]

    @pos.setter
    def pos(self, value):
        self._pos = np.zeros((4,), np.float32)
        self._pos[:3] = value

        if self._lightType == 'point':
            self._pos[3] = 1.0

    @property
    def lightType(self):
        """Type of light source, can be 'point' or 'directional'."""
        return self._pos[:3]

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
    def diffuseColor(self):
        """Diffuse color of the light."""
        return self._diffuseColor

    @diffuseColor.setter
    def diffuseColor(self, value):
        self._diffuseColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='_diffuseRGB', colorAttrib='diffuseColor',
                 colorSpaceAttrib='colorSpace')

        # make sure the color we got is 32-bit float
        self._diffuseRGB = np.asarray(self._diffuseRGB, np.float32)

    @property
    def specularColor(self):
        """Specular color of the light."""
        return self._specularColor

    @specularColor.setter
    def specularColor(self, value):
        self._specularColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='_specularRGB', colorAttrib='specularColor',
                 colorSpaceAttrib='colorSpace')

        # make sure the color we got is 32-bit float
        self._specularRGB = np.asarray(self._specularRGB, np.float32)

    @property
    def ambientColor(self):
        """Ambient color of the light."""
        return self._ambientColor

    @ambientColor.setter
    def ambientColor(self, value):
        self._ambientColor = np.asarray(value, np.float32)
        setColor(self, value, colorSpace=self.colorSpace, operation=None,
                 rgbAttrib='_ambientRGB', colorAttrib='ambientColor',
                 colorSpaceAttrib='colorSpace')

        # make sure the color we got is 32-bit float
        self._ambientRGB = np.asarray(self._ambientRGB, np.float32)

    @property
    def kAttenuation(self):
        """Values for the constant, linear, and quadratic terms of the lighting
        attenuation formula.
        """
        return self._kAttenuation

    @kAttenuation.setter
    def kAttenuation(self, value):
        self._kAttenuation = np.asarray(value, np.float32)


class RigidBodyPose(object):
    """Class for representing rigid body poses.

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
        self._invModelMatrix = np.zeros(4, dtype=np.float32, order='C')

        # compute matrices only if `pos` and `ori` attributes have been updated
        self._matrixNeedsUpdate = False
        self._invMatrixNeedsUpdate = False

    @property
    def pos(self):
        """Position vector (X, Y, Z)."""
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = np.ascontiguousarray(value, dtype=np.float32)
        self._matrixNeedsUpdate = self._invMatrixNeedsUpdate = True

    @property
    def ori(self):
        """Orientation quaternion (X, Y, Z, W)."""
        return self._ori

    @ori.setter
    def ori(self, value):
        self._ori = np.ascontiguousarray(value, dtype=np.float32)
        self._matrixNeedsUpdate = self._invMatrixNeedsUpdate = True

    def __mul__(self, other):
        """Multiply two poses, combining them to get a new pose."""
        return RigidBodyPose(self._pos + other.pos,
                             mt.multQuat(self._ori, other.ori))

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
        if not self._invModelMatrix:
            return self._invModelMatrix
        else:
            return self.getModelMatrix(inverse=True)

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

    def __invert__(self):
        """Operator `~` to invert the pose. Returns a `RigidBodyPose` object."""
        return RigidBodyPose(
            -self._pos, mt.invertQuat(self._ori, dtype=np.float32))

    def invert(self):
        """Invert this pose."""
        self._ori = mt.invertQuat(self._ori, dtype=np.float32)
        self._pos *= -1.0

    def inverted(self):
        """Get a pose which is the inverse of this one."""
        return RigidBodyPose(
            -self._pos, mt.invertQuat(self._ori, dtype=np.float32))


class BaseRigidBodyStim(ColorMixin):
    """Base class for rigid body 3D stimuli.

    This class handles the pose of a rigid body 3D stimulus. Poses are
    represented by a `RigidBodyClass` object accessed via `thePose` attribute.

    Any class the implements `pos` and `ori` attributes can be used in place of
    a `RigidBodyPose` instance for `thePose`. This common interface allows for
    custom classes which handle 3D transformations to be used for stimulus
    transformations (eg. `LibOVRPose` in PsychXR can be used instead of
    `RigidBodyPose` which supports more VR specific features).

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
        self.win = win
        self.name = name
        self.autoLog = autoLog
        super(BaseRigidBodyStim, self).__init__()

        self.colorSpace = colorSpace
        self.contrast = contrast
        self.opacity = opacity
        self.color = color

        self._thePose = RigidBodyPose(pos, ori)

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

    def draw(self):
        raise NotImplementedError(
            '3D stimulus classes must override visual.BaseRigidBodyStim.draw')

    def _createVAO(self, vertices, textureCoords, normals, faces):
        """Create a vertex array object for handling vertex attribute data.
        """
        # upload to buffers
        vertexVBO = gt.createVBO(vertices)
        texCoordVBO = gt.createVBO(textureCoords)
        normalsVBO = gt.createVBO(normals)

        # create an index buffer with faces
        indexBuffer = gt.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        return gt.createVAO({0: vertexVBO, 8: texCoordVBO, 2: normalsVBO},
            indexBuffer=indexBuffer)


class SphereStim(BaseRigidBodyStim):
    """Class for drawing a UV sphere.

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

    """
    def __init__(self,
                 win,
                 radius=0.5,
                 subdiv=(32, 32),
                 flipFaces=False,
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 useMaterial=None,
                 color=(0., 0., 0.),
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
        useMaterial : SimpleMaterial, optional
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
        self._vao = self._createVAO(
            *gt.createUVSphere(sectors=subdiv[0],
                               stacks=subdiv[1],
                               radius=radius,
                               flipFaces=flipFaces))

        self.setColor(color, colorSpace=self.colorSpace, log=False)
        self.material = useMaterial

    def draw(self, win=None):
        """Draw the sphere.

        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.

        """
        if win is None:
            win = self.win

        win.draw3d = True

        # apply transformation to mesh
        GL.glPushMatrix()
        GL.glLoadTransposeMatrixf(at.array2pointer(self.thePose.modelMatrix))

        if self.material is not None:
            gt.useMaterial(self.material)
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)
            gt.clearMaterial(self.material)
        else:
            # material tracks color
            GL.glEnable(GL.GL_COLOR_MATERIAL)  # enable color tracking
            GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
            # 'rgb' is created and set when color is set
            r, g, b = self._getDesiredRGB(
                self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(r, g, b, self.opacity)

            # draw the shape
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)

        GL.glPopMatrix()

        win.draw3d = False


class BoxStim(BaseRigidBodyStim):
    """Class for drawing 3D boxes.

    Draws a rectangular box with dimensions specified by `size` (length, width,
    height) in scene units.

    Calling the `draw` method will render the box to the current buffer. The
    render target (FBO or back buffer) must have a depth buffer attached to it
    for the object to be rendered correctly. Shading is used if the current
    window has light sources defined and lighting is enabled (by setting
    `useLights=True` before drawing the stimulus).

    """
    def __init__(self,
                 win,
                 size=(.5, .5, .5),
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 flipFaces=False,
                 useMaterial=None,
                 color=(0., 0., 0.),
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
            Dimensions of the mesh. If a single value is specified, the box will
            be a cube. Provide a tuple of floats to specify the width, length,
            and height of the box (eg. `size=(0.2, 1.3, 2.1)`) in scene units.
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real. If you prefer specifying rotations in
            axis-angle format, call `setOriAxisAngle` after initialization.
        flipFaces : bool, optional
            If `True`, normals and face windings will be set to point inward
            towards the center of the box. Texture coordinates will remain the
            same. Default is `False`.
        useMaterial : SimpleMaterial, optional
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
        self._vao = self._createVAO(*gt.createBox(size, flipFaces))

        self.setColor(color, colorSpace=self.colorSpace, log=False)
        self.material = useMaterial

    def draw(self, win=None):
        """Draw the box.

        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.

        """
        if win is None:
            win = self.win

        win.draw3d = True

        # apply transformation to mesh
        GL.glPushMatrix()
        GL.glLoadTransposeMatrixf(at.array2pointer(self.thePose.modelMatrix))

        if self.material is not None:
            gt.useMaterial(self.material)
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)
            gt.clearMaterial(self.material)
        else:
            # material tracks color
            GL.glEnable(GL.GL_COLOR_MATERIAL)  # enable color tracking
            GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
            # 'rgb' is created and set when color is set
            r, g, b = self._getDesiredRGB(
                self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(r, g, b, 1.0)

            # draw the shape
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)

        GL.glPopMatrix()

        win.draw3d = False


class PlaneStim(BaseRigidBodyStim):
    """Class for drawing planes.

    Draws a plane with dimensions specified by `size` (length, width) in scene
    units.

    Calling the `draw` method will render the plane to the current buffer. The
    render target (FBO or back buffer) must have a depth buffer attached to it
    for the object to be rendered correctly. Shading is used if the current
    window has light sources defined and lighting is enabled (by setting
    `useLights=True` before drawing the stimulus).

    """
    def __init__(self,
                 win,
                 size=(.5, .5),
                 pos=(0., 0., 0.),
                 ori=(0., 0., 0., 1.),
                 useMaterial=None,
                 color=(0., 0., 0.),
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
            length of the plane (eg. `size=(0.2, 1.3)`).
        pos : array_like
            Position vector `[x, y, z]` for the origin of the rigid body.
        ori : array_like
            Orientation quaternion `[x, y, z, w]` where `x`, `y`, `z` are
            imaginary and `w` is real. If you prefer specifying rotations in
            axis-angle format, call `setOriAxisAngle` after initialization. By
            default, the plane is oriented with normal facing the +Z axis of the
            scene.
        useMaterial : SimpleMaterial, optional
            Material to use. The material can be configured by accessing the
            `material` attribute after initialization. If not material is
            specified, the diffuse and ambient color of the shape will track the
            current color specified by `glColor`.

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
        self._vao = self._createVAO(*gt.createPlane(size))

        self.setColor(color, colorSpace=self.colorSpace, log=False)
        self.material = useMaterial

    def draw(self, win=None):
        """Draw the plane.

        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window this stimulus is associated with. Stimuli cannot be shared
            across windows unless they share the same context.

        """
        if win is None:
            win = self.win

        win.draw3d = True

        # apply transformation to mesh
        GL.glPushMatrix()
        GL.glLoadTransposeMatrixf(at.array2pointer(self.thePose.modelMatrix))

        if self.material is not None:
            gt.useMaterial(self.material)
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)
            gt.clearMaterial(self.material)
        else:
            # material tracks color
            GL.glEnable(GL.GL_COLOR_MATERIAL)  # enable color tracking
            GL.glColorMaterial(GL.GL_FRONT, GL.GL_AMBIENT_AND_DIFFUSE)
            # 'rgb' is created and set when color is set
            r, g, b = self._getDesiredRGB(
                self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(r, g, b, 1.0)

            # draw the shape
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)

        GL.glPopMatrix()

        win.draw3d = False


class ObjMeshStim(BaseRigidBodyStim):
    """Class for loading and presenting 3D stimuli in the Wavefront OBJ format.

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
        of any time-critical routines!

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
                 useMaterial=None):
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
        useMaterial : SimpleMaterial, optional
            Material to use. The material can be configured by accessing the
            `material` attribute after initialization. If not material is
            specified, the diffuse and ambient color of the shape will track the
            current color specified by `glColor`.

        """
        super(ObjMeshStim, self).__init__(win, pos=pos, ori=ori)

        objModel = gt.loadObjFile(objFile)

        if objModel.mtlFile is not None:
            self.materials = gt.loadMtlFile(objModel.mtlFile)
        else:
            self.materials = None

        # load vertex data into VBOs
        vertexPosVBO = gt.createVBO(objModel.vertexPos)
        texCoordVBO = gt.createVBO(objModel.texCoords)
        normalsVBO = gt.createVBO(objModel.normals)

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
                {0: vertexPosVBO,  # 0 = gl_Vertex
                 8: texCoordVBO,   # 8 = gl_MultiTexCoord0
                 2: normalsVBO},   # 2 = gl_Normal
                 indexBuffer=indexBuffer)

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

        win.draw3d = True

        GL.glPushMatrix()
        GL.glLoadTransposeMatrixf(at.array2pointer(self.thePose.modelMatrix))

        # iterate over materials, draw associated VAOs
        if self.materials is not None:
            mtlIndex = 0
            nMaterials = len(self.materials)
            for materialName, materialDesc in self.materials.items():
                gt.useMaterial(materialDesc)
                gt.drawVAO(self._vao[materialName], GL.GL_TRIANGLES)
                mtlIndex += 1

                # clear the material when done
                if mtlIndex == nMaterials:
                    gt.clearMaterial(materialDesc)

        else:
            gt.drawVAO(self._vao, GL.GL_TRIANGLES)

        GL.glPopMatrix()

        win.draw3d = False