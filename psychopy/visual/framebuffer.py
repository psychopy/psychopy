#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Framebuffer related classes and functions.

This module is intended to provide simplified interface for creating image
buffers (including textures) in OpenGL without the need to work with OpenGL
objects directly. This allows for multiple OpenGL implementations to use the
same objects.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import pyglet.gl as GL  # using only pyglet for now
import ctypes
import psychopy.tools.gltools as gltools
import psychopy.tools.viewtools as viewtools
import numpy as np


depthFuncs = {'never': GL.GL_NEVER, 'less': GL.GL_LESS,
              'equal': GL.GL_EQUAL, 'lequal': GL.GL_LEQUAL,
              'greater': GL.GL_GREATER, 'notequal': GL.GL_NOTEQUAL,
              'gequal': GL.GL_GEQUAL, 'always': GL.GL_ALWAYS}

cullFaceMode = {'back': GL.GL_BACK,
                'front': GL.GL_FRONT,
                'both': GL.GL_FRONT_AND_BACK,
                'frontBack': GL.GL_FRONT_AND_BACK}

frontFace = {'ccw': GL.GL_CCW, 'cw': GL.GL_CW}


class Framebuffer(object):
    """Class representing an image buffer in video memory for off-screen
    rendering of stimuli.

    A render surface references a framebuffer with attachments for color, depth,
    and stencil data. When bound, OpenGL draw operations will be diverted to
    the buffers associated with this object. Usually, `RenderSurface` is used
    internally by the `Window` class for creating images to be presented.
    However, you can also use a `RenderSurface` for general purpose off-screen
    rendering to textures and use them elsewhere.

    Multi-sample anti-aliasing (MSAA) is supported with `RenderSurface`, however
    you must call `finalize` before using color image data.

    """
    def __init__(self, win, name, size=None, samples=1):
        self._win = win
        self._name = name
        self._size = np.array(win.size if size is None else size, dtype=int)

        self._samples = samples

        # IDs for FBO and its attachments
        w, h = self._size
        colorTex = gltools.createTexImage2D(w, h)
        depthRb = gltools.createRenderbuffer(
            w, h, internalFormat=GL.GL_DEPTH24_STENCIL8)

        # framebuffer object
        self.fbo = gltools.createFBO(
            {GL.GL_COLOR_ATTACHMENT0: colorTex,
             GL.GL_DEPTH_STENCIL_ATTACHMENT: depthRb})

        # multisample framebuffer if needed
        self.fboMSAA = None

    @property
    def size(self):
        return self._size  # read-only

    def isMultisample(self):
        """`True` if this is a multisample buffer."""
        return self._samples > 1

    def bind(self, mode='readDraw'):
        """Bind the framebuffer associated with this object. Successive draw
        operations will be diverted to that framebuffer.

        Parameters
        ----------
        mode : str
            Mode to bind framebuffer.

        """
        if mode == 'readDraw':
            target = GL.GL_FRAMEBUFFER
        elif mode == 'draw':
            target = GL.GL_DRAW_FRAMEBUFFER
        elif mode == 'read':
            target = GL.GL_READ_FRAMEBUFFER
        else:
            raise ValueError("Invalid option for `mode` in call `bind()`.")

        gltools.bindFBO(self.fbo, target)


class RenderContext(object):
    """Class representing a render context.

    A render context describes how stimuli are drawn to a framebuffer. When
    `setBuffer` is called, the render context is made current and successive
    draw/read operations will be

    """
    def __init__(self, win, viewport, name):
        """Constructor for DeviceContext."""
        self.win = win

        # name of buffer, used to determine whether the window is using the
        # device context
        self.name = name

        self._viewport = np.asarray(viewport, dtype=int)
        self._scissor = np.array(self._viewport, dtype=int)
        self._size = np.array(self.viewport[2:])

        # retain binding information
        self._bindMode = None

        # transformations related to the device context
        self._viewMatrix = np.identity(4, dtype=np.float32)
        self._projectionMatrix = viewtools.orthoProjectionMatrix(
            -1, 1, -1, 1, -1, 1, dtype=np.float32)

        # stereo rendering settings, set later by the user
        self._eyeOffset = 0.0
        self._convergeOffset = 0.0

        # Pointers to transforms, reduces overhead when passing these off to
        # OpenGL.
        self._viewMatrixPtr = self._viewMatrix.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float))
        self._projectionMatrixPtr = self._projectionMatrix.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float))

        # OpenGL states
        self._scissorTest = self._stencilTest = self._depthTest = \
            self._depthMask = self._cullFace = False
        self._depthFunc = 'less'
        self._cullFaceMode = 'back'
        self._frontFace = 'ccw'

        # Keep track of the shader program used the last time transforms were
        # called. Uniform locations are cached until this changes.
        self._shaderProg = None

        self._viewMatUnifLoc = self._viewMatUnifName = None
        self._projMatUnifLoc = self._projMatUnifName = None

        # scene light sources
        self._lights = []
        self._useLights = False
        self._nLights = 0
        self._ambientLight = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32)

    @property
    def aspect(self):
        """Aspect ratio of the current viewport (width / height)."""
        return self._viewport[2] / float(self._viewport[3])

    @property
    def eyeOffset(self):
        """Eye offset in centimeters.

        This value is used by `setPerspectiveView` to apply a lateral
        offset to the view, therefore it must be set prior to calling it. Use a
        positive offset for the right eye, and a negative one for the left.
        Offsets should be the distance to from the middle of the face to the
        center of the eye, or half the inter-ocular distance.

        """
        return self._eyeOffset * 100.0

    @eyeOffset.setter
    def eyeOffset(self, value):
        self._eyeOffset = value / 100.0

    @property
    def convergeOffset(self):
        """Convergence offset from monitor in centimeters.

        This is value corresponds to the offset from screen plane to set the
        convergence plane (or point for `toe-in` projections). Positive offsets
        move the plane farther away from the viewer, while negative offsets
        nearer. This value is used by `setPerspectiveView` and should be set
        before calling it to take effect.

        Notes
        -----
        * This value is only applicable for `setToeIn` and `setOffAxisView`.

        """
        return self._convergeOffset * 100.0

    @convergeOffset.setter
    def convergeOffset(self, value):
        self._convergeOffset = value / 100.0

    @property
    def viewport(self):
        """Viewport rectangle (x, y, w, h) for the current draw buffer.

        Values `x` and `y` define the origin, and `w` and `h` the size of the
        rectangle in pixels.

        This is typically set to cover the whole buffer, however it can be
        changed for applications like multi-view rendering. Stimuli will draw
        according to the new shape of the viewport, for instance and stimulus
        with position (0, 0) will be drawn at the center of the viewport, not
        the window.

        Examples
        --------
        Constrain drawing to the left and right halves of the screen, where
        stimuli will be drawn centered on the new rectangle. Note that you need
        to set both the `viewport` and the `scissor` rectangle::

            x, y, w, h = win.frameBufferSize  # size of the framebuffer
            win.viewport = win.scissor = [x, y, w / 2.0, h]
            # draw left stimuli ...

            win.viewport = win.scissor = [x + (w / 2.0), y, w / 2.0, h]
            # draw right stimuli ...

            # restore drawing to the whole screen
            win.viewport = win.scissor = [x, y, w, h]

        """
        return self._viewport

    @viewport.setter
    def viewport(self, value):
        self._viewport[:] = value
        self._size[:] = self._viewport[2:]
        GL.glViewport(*self._viewport)

    @property
    def scissor(self):
        """Scissor rectangle (x, y, w, h) for the current draw buffer.

        Values `x` and `y` define the origin, and `w` and `h` the size
        of the rectangle in pixels. The scissor operation is only active
        if `scissorTest=True`.

        Usually, the scissor and viewport are set to the same rectangle
        to prevent drawing operations from `spilling` into other regions
        of the screen. For instance, calling `clearBuffer` will only
        clear within the scissor rectangle.

        Setting the scissor rectangle but not the viewport will restrict
        drawing within the defined region (like a rectangular aperture),
        not changing the positions of stimuli.

        """
        return self._scissor

    @scissor.setter
    def scissor(self, value):
        self._scissor[:] = value
        GL.glScissor(*self._scissor)

    @property
    def size(self):
        return self._size

    @property
    def origin(self):
        return self._viewport[:2]

    @property
    def scissorTest(self):
        """`True` if scissor testing is enabled."""
        return self._scissorTest

    @scissorTest.setter
    def scissorTest(self, value):
        if self.win.buffer == self.name:
            if value is True:
                GL.glEnable(GL.GL_SCISSOR_TEST)
            elif value is False:
                GL.glDisable(GL.GL_SCISSOR_TEST)
            else:
                raise TypeError("Value must be boolean.")

        self._scissorTest = value

    @property
    def stencilTest(self):
        """`True` if stencil testing is enabled."""
        return self._stencilTest

    @stencilTest.setter
    def stencilTest(self, value):
        if self.win.buffer == self.name:
            if value is True:
                GL.glEnable(GL.GL_STENCIL_TEST)
            elif value is False:
                GL.glDisable(GL.GL_STENCIL_TEST)
            else:
                raise TypeError("Value must be boolean.")

        self._stencilTest = value

    @property
    def depthTest(self):
        """`True` if depth testing is enabled."""
        return self._depthTest

    @depthTest.setter
    def depthTest(self, value):
        if self.win.buffer == self.name:
            if value is True:
                GL.glEnable(GL.GL_DEPTH_TEST)
            elif value is False:
                GL.glDisable(GL.GL_DEPTH_TEST)
            else:
                raise TypeError("Value must be boolean.")

        self._depthTest = value

    @property
    def depthFunc(self):
        """Depth test comparison function for rendering."""
        return self._depthFunc

    @depthFunc.setter
    def depthFunc(self, value):
        depthFuncs = {'never': GL.GL_NEVER, 'less': GL.GL_LESS,
                      'equal': GL.GL_EQUAL, 'lequal': GL.GL_LEQUAL,
                      'greater': GL.GL_GREATER, 'notequal': GL.GL_NOTEQUAL,
                      'gequal': GL.GL_GEQUAL, 'always': GL.GL_ALWAYS}

        try:
            if self.win.buffer == self.name:
                GL.glDepthFunc(depthFuncs[value])
        except KeyError:
            raise KeyError(
                "Invalid value for `depthFunc` specified, given `{}` but should"
                "be either, `never`, `less`, `equal`, `lequal`, `greater`, "
                "`notequal`, `gequal` or `always`.".format(value))

        self._depthFunc = value

    @property
    def depthMask(self):
        """`True` if depth masking is enabled. Writing to the depth buffer will
        be disabled.
        """
        return self._depthMask

    @depthMask.setter
    def depthMask(self, value):
        if self.win.buffer == self.name:
            if value is True:
                GL.glDepthMask(GL.GL_TRUE)
            elif value is False:
                GL.glDepthMask(GL.GL_FALSE)
            else:
                raise TypeError("Value must be boolean.")

        self._depthMask = value

    @property
    def cullFaceMode(self):
        """Face culling mode, either `back`, `front` or `both`."""
        return self._cullFaceMode

    @cullFaceMode.setter
    def cullFaceMode(self, value):
        if self.win.buffer == self.name:
            if value == 'back':
                GL.glCullFace(GL.GL_BACK)
            elif value == 'front':
                GL.glCullFace(GL.GL_FRONT)
            elif value == 'both':
                GL.glCullFace(GL.GL_FRONT_AND_BACK)
            else:
                raise ValueError('Invalid face cull mode.')

        self._cullFaceMode = value

    @property
    def cullFace(self):
        """`True` if face culling is enabled.`"""
        return self._cullFace

    @cullFace.setter
    def cullFace(self, value):
        if self.win.buffer == self.name:
            if value is True:
                GL.glEnable(GL.GL_CULL_FACE)
            elif value is False:
                GL.glDisable(GL.GL_CULL_FACE)
            else:
                raise TypeError('Value must be type `bool`.')

        self._cullFace = value

    @property
    def frontFace(self):
        """Face winding order to define front, either `ccw` or `cw`."""
        return self._frontFace

    @frontFace.setter
    def frontFace(self, value):
        if self.win.buffer == self.name:
            if value == 'ccw':
                GL.glFrontFace(GL.GL_CCW)
            elif value == 'cw':
                GL.glFrontFace(GL.GL_CW)
            else:
                raise ValueError('Invalid value, must be `ccw` or `cw`.')

        self._frontFace = value

    def use(self):
        """Make this DeviceContext active."""
        # set the viewport and scissor
        GL.glViewport(*self._viewport)
        GL.glScissor(*self._scissor)

        # set OpenGL capabilities related to this device context
        if self._scissorTest:
            GL.glEnable(GL.GL_SCISSOR_TEST)
        else:
            GL.glDisable(GL.GL_SCISSOR_TEST)

        if self._stencilTest:
            GL.glEnable(GL.GL_STENCIL_TEST)
        else:
            GL.glDisable(GL.GL_STENCIL_TEST)

        if self._depthTest:
            GL.glEnable(GL.GL_DEPTH_TEST)
        else:
            GL.glDisable(GL.GL_DEPTH_TEST)

        GL.glDepthMask(GL.GL_TRUE if self._depthMask else GL.GL_FALSE)
        GL.glDepthFunc(depthFuncs[self._depthFunc])

        if self._cullFace:
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(cullFaceMode[self._cullFaceMode])
        else:
            GL.glDisable(GL.GL_CULL_FACE)

        GL.glFrontFace(frontFace[self._frontFace])

        self.applyEyeTransform()

    def clearBuffer(self, color=True, depth=False, stencil=False):
        """Clear the buffer."""
        flags = GL.GL_NONE

        if color:
            flags |= GL.GL_COLOR_BUFFER_BIT

        if depth:
            flags |= GL.GL_DEPTH_BUFFER_BIT

        if stencil:
            flags |= GL.GL_STENCIL_BUFFER_BIT

        GL.glClear(flags)

    def resetEyeTransform(self, clearDepth=True):
        """Restore the default projection and view settings to PsychoPy
        defaults. Call this prior to drawing 2D stimuli objects (i.e.
        GratingStim, ImageStim, Rect, etc.) if any eye transformations were
        applied for the stimuli to be drawn correctly.

        Parameters
        ----------
        clearDepth : bool
            Clear the depth buffer upon reset. This ensures successive draw
            commands are not affected by previous data written to the depth
            buffer. Default is `True`.

        Notes
        -----
        * Calling :py:attr:`~Window.flip()` automatically resets the view and
          projection to defaults. So you don't need to call this unless you are
          mixing 3D and 2D stimuli.

        Examples
        --------
        Going between 3D and 2D stimuli::

            # 2D stimuli can be drawn before setting a perspective projection
            win.setPerspectiveView()
            # draw 3D stimuli here ...
            win.resetEyeTransform()
            # 2D stimuli can be drawn here again ...
            win.flip()

        """
        # should eventually have the same effect as calling _onResize(), so we
        # need to add the retina mode stuff eventually
        if hasattr(self, '_viewMatrix'):
            self._viewMatrix = np.identity(4, dtype=np.float32)

        if hasattr(self, '_projectionMatrix'):
            self._projectionMatrix = viewtools.orthoProjectionMatrix(
                -1, 1, -1, 1, -1, 1, dtype=np.float32)

        self.applyEyeTransform(clearDepth)

    def applyEyeTransform(self, clearDepth=True, shaderProg=None):
        """Apply the current view and projection matrices.

        Matrices specified by attributes :py:attr:`~Window.viewMatrix` and
        :py:attr:`~Window.projectionMatrix` are applied using 'immediate mode'
        OpenGL functions. Subsequent drawing operations will be affected until
        :py:attr:`~Window.flip()` is called.

        All transformations in ``GL_PROJECTION`` and ``GL_MODELVIEW`` matrix
        stacks will be cleared (set to identity) prior to applying.

        Parameters
        ----------
        clearDepth : bool
            Clear the depth buffer. This may be required prior to rendering 3D
            objects.
        shaderProg : int, object or None
            Optional handle for the active shader.

        Examples
        --------
        Using a custom view and projection matrix::

            # Must be called every frame since these values are reset after
            # `flip()` is called!
            win.viewMatrix = viewtools.lookAt( ... )
            win.projectionMatrix = viewtools.perspectiveProjectionMatrix( ... )
            win.applyEyeTransform()
            # draw 3D objects here ...

        """
        # check if we need to update the shader program
        if shaderProg != self._shaderProg:
            self._shaderProg = shaderProg
            if self._shaderProg is not None:
                # Cache shader uniform location, this prevents redundantly
                # querying their location each frame.
                if self._viewMatUnifName is not None:
                    self._viewMatUnifLoc = GL.glGetUniformLocation(
                        shaderProg, self._viewMatUnifName)
                else:
                    self._viewMatUnifLoc = None

                if self._projMatUnifName is not None:
                    self._projMatUnifLoc = GL.glGetUniformLocation(
                        shaderProg, self._projMatUnifName)
                else:
                    self._projMatUnifLoc = None

        # apply the projection and view transformations
        if self._shaderProg is not None:
            # set transformation matrices to shader uniforms
            if self._viewMatUnifLoc is not None:
                GL.glUniformMatrix4fv(
                    self._viewMatUnifLoc, 1, GL.GL_TRUE, self._viewMatrixPtr)

            if self._projMatUnifLoc is not None:
                GL.glUniformMatrix4fv(
                    self._projMatUnifLoc, 1, GL.GL_TRUE,
                    self._projectionMatrixPtr)
        else:
            # called if no shader (or a legacy shader) is used
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glMultTransposeMatrixf(self._projectionMatrixPtr)
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            GL.glMultTransposeMatrixf(self._viewMatrixPtr)

        # clear the depth buffer
        oldDepthMask = self._depthMask
        if clearDepth:
            GL.glDepthMask(GL.GL_TRUE)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            if oldDepthMask is False:   # return to old state if needed
                GL.glDepthMask(GL.GL_FALSE)

    @property
    def ambientLight(self):
        """Ambient light color for the scene [r, g, b, a]. Values range from 0.0
        to 1.0. Only applicable if `useLights` is `True`.

        Examples
        --------
        Setting the ambient light color::

            win.ambientLight = [0.5, 0.5, 0.5]

            # don't do this!!!
            win.ambientLight[0] = 0.5
            win.ambientLight[1] = 0.5
            win.ambientLight[2] = 0.5

        """
        # TODO - use signed color and colorspace instead
        return self._ambientLight[:3]

    @ambientLight.setter
    def ambientLight(self, value):
        self._ambientLight[:3] = value
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT,
                          np.ctypeslib.as_ctypes(self._ambientLight))

    @property
    def lights(self):
        """Scene lights.

        This is specified as an array of `~psychopy.visual.LightSource`
        objects. If a single value is given, it will be converted to a `list`
        before setting. Set `useLights` to `True` before rendering to enable
        lighting/shading on subsequent objects. If `lights` is `None` or an
        empty `list`, no lights will be enabled if `useLights=True`, however,
        the scene ambient light set with `ambientLight` will be still be used.

        Examples
        --------
        Create a directional light source and add it to scene lights::

            dirLight = gltools.LightSource((0., 1., 0.), lightType='directional')
            win.lights = dirLight  # `win.lights` will be a list when accessed!

        Multiple lights can be specified by passing values as a list::

            myLights = [gltools.LightSource((0., 5., 0.)),
                        gltools.LightSource((-2., -2., 0.))
            win.lights = myLights

        """
        return self._lights

    @lights.setter
    def lights(self, value):
        # if None or empty list, disable all lights
        if value is None or not value:
            for index in range(self._nLights):
                GL.glDisable(GL.GL_LIGHT0 + index)

            self._nLights = 0  # set number of lights to zero
            self._lights = value

            return

        # set the lights and make sure it's a list if a single value was passed
        self._lights = value if isinstance(value, (list, tuple,)) else [value]

        # disable excess lights if less lights were specified this time
        oldNumLights = self._nLights
        self._nLights = len(self._lights)  # number of lights enabled
        if oldNumLights > self._nLights:
            for index in range(self._nLights, oldNumLights):
                GL.glDisable(GL.GL_LIGHT0 + index)

        # Setup legacy lights, new spec shader programs should access the
        # `lights` attribute directly to setup lighting uniforms.
        # The index of the lights is defined by the order it appears in
        # `self._lights`.
        for index, light in enumerate(self._lights):
            enumLight = GL.GL_LIGHT0 + index

            # convert data in light class to ctypes
            #pos = numpy.ctypeslib.as_ctypes(light.pos)
            diffuse = np.ctypeslib.as_ctypes(light._diffuseRGB)
            specular = np.ctypeslib.as_ctypes(light._specularRGB)
            ambient = np.ctypeslib.as_ctypes(light._ambientRGB)

            # pass values to OpenGL
            #GL.glLightfv(enumLight, GL.GL_POSITION, pos)
            GL.glLightfv(enumLight, GL.GL_DIFFUSE, diffuse)
            GL.glLightfv(enumLight, GL.GL_SPECULAR, specular)
            GL.glLightfv(enumLight, GL.GL_AMBIENT, ambient)

            constant, linear, quadratic = light._kAttenuation
            GL.glLightf(enumLight, GL.GL_CONSTANT_ATTENUATION, constant)
            GL.glLightf(enumLight, GL.GL_LINEAR_ATTENUATION, linear)
            GL.glLightf(enumLight, GL.GL_QUADRATIC_ATTENUATION, quadratic)

            # enable the light
            GL.glEnable(enumLight)

    @property
    def useLights(self):
        """Enable scene lighting.

        Lights will be enabled if using legacy OpenGL lighting. Stimuli using
        shaders for lighting should check if `useLights` is `True` since this
        will have no effect on them, and disable or use a no lighting shader
        instead. Lights will be transformed to the current view matrix upon
        setting to `True`.

        Lights are transformed by the present `GL_MODELVIEW` matrix. Setting
        `useLights` will result in their positions being transformed by it.
        If you want lights to appear at the specified positions in world space,
        make sure the current matrix defines the view/eye transformation when
        setting `useLights=True`.

        This flag is reset to `False` at the beginning of each frame. Should be
        `False` if rendering 2D stimuli or else the colors will be incorrect.
        """
        return self._useLights

    @useLights.setter
    def useLights(self, value):
        self._useLights = value

        # Setup legacy lights, new spec shader programs should access the
        # `lights` attribute directly to setup lighting uniforms.
        if self._useLights and self._lights:
            GL.glEnable(GL.GL_LIGHTING)
            # make sure specular lights are computed relative to eye position,
            # this is more realistic than the default. Does not affect shaders.
            GL.glLightModeli(GL.GL_LIGHT_MODEL_LOCAL_VIEWER, GL.GL_TRUE)

            # update light positions for current model matrix
            for index, light in enumerate(self._lights):
                enumLight = GL.GL_LIGHT0 + index
                pos = np.ctypeslib.as_ctypes(light.pos)
                GL.glLightfv(enumLight, GL.GL_POSITION, pos)
        else:
            # disable lights
            GL.glDisable(GL.GL_LIGHTING)

    def updateLights(self, index=None):
        """Explicitly update scene lights if they were modified.

        This is required if modifications to objects referenced in `lights` have
        been changed since assignment. If you removed or added items of `lights`
        you must refresh all of them.

        Parameters
        ----------
        index : int, optional
            Index of light source in `lights` to update. If `None`, all lights
            will be refreshed.

        Examples
        --------
        Call `updateLights` if you modified lights directly like this::

            win.lights[1].diffuseColor = [1., 0., 0.]
            win.updateLights(1)

        """
        if self._lights is None:
            return  # nop if there are no lights

        if index is None:
            self.lights = self._lights
        else:
            if index > len(self._lights) - 1:
                raise IndexError('Invalid index for `lights`.')

            enumLight = GL.GL_LIGHT0 + index

            # light object to modify
            light = self._lights[index]

            # convert data in light class to ctypes
            # pos = numpy.ctypeslib.as_ctypes(light.pos)
            diffuse = np.ctypeslib.as_ctypes(light.diffuse)
            specular = np.ctypeslib.as_ctypes(light.specular)
            ambient = np.ctypeslib.as_ctypes(light.ambient)

            # pass values to OpenGL
            # GL.glLightfv(enumLight, GL.GL_POSITION, pos)
            GL.glLightfv(enumLight, GL.GL_DIFFUSE, diffuse)
            GL.glLightfv(enumLight, GL.GL_SPECULAR, specular)
            GL.glLightfv(enumLight, GL.GL_AMBIENT, ambient)
