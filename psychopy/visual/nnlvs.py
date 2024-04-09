#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Window class for the NordicNeuralLab's VisualSystemHD(tm) fMRI display
system.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import ctypes
import numpy as np
import pyglet.gl as GL
from psychopy.visual import window
from psychopy import logging
import psychopy.tools.mathtools as mt
import psychopy.tools.viewtools as vt
import psychopy.tools.gltools as gt

try:
    from PIL import Image
except ImportError:
    import Image

reportNDroppedFrames = 5


# ------------------------------------------------------------------------------
# Configurations for the model of VSHD
#

vshdModels = {
    'vshd': {
        # store the configuration for FOV and viewing distance by diopters
        'configByDiopters': {
            -9: {'vfov': 29.70, 'dist': 0.111},
            -8: {'vfov': 29.75, 'dist': 0.125},
            -7: {'vfov': 29.8, 'dist': 0.143},
            -6: {'vfov': 29.86, 'dist': 0.167},
            -5: {'vfov': 29.92, 'dist': 0.20},
            -4: {'vfov': 29.98, 'dist': 0.25},
            -3: {'vfov': 30.04, 'dist': 0.333},
            -2: {'vfov': 30.08, 'dist': 0.5},
            -1: {'vfov': 30.14, 'dist': 1.0},
            0:  {'vfov': 30.18, 'dist': 1.0},  # TODO: handle this case
            1:  {'vfov': 30.24, 'dist': -1.0},  # image gets inverted
            2:  {'vfov': 30.3, 'dist': -0.5},
            3:  {'vfov': 30.36, 'dist': -0.333},
            4:  {'vfov': 30.42, 'dist': -0.25},
            5:  {'vfov': 30.46, 'dist': -0.2},
        },
        'scrHeightM': 9.6 * 1200. / 1e-6,  # screen height in meters
        'scrWidthM': 9.6 * 1920. / 1e-6,  # screen width in meters
        'distCoef': -0.02,  # distortion coef. depends on screen size
        'resolution': (1920, 1200)  # resolution for the display per eye
    }
}


# ------------------------------------------------------------------------------
# Window subclass class for VSHD hardware
#

class VisualSystemHD(window.Window):
    """Class provides support for NordicNeuralLab's VisualSystemHD(tm) fMRI
    display hardware. This is a lazy-imported class, therefore import using
    full path `from psychopy.visual.nnlvs import VisualSystemHD` when
    inheriting from it.


    Use this class in-place of the `Window` class for use with the VSHD
    hardware. Ensure that the VSHD headset display output is configured in
    extended desktop mode (eg. nVidia Surround). Extended desktops are only
    supported on Windows and Linux systems.

    The VSHD is capable of both 2D and stereoscopic 3D rendering. You can select
    which eye to draw to by calling `setBuffer`, much like how stereoscopic
    rendering is implemented in the base `Window` class.

    Notes
    -----
    * This class handles drawing differently than the default window class, as
      a result, stimuli `autoDraw` is not supported.
    * Edges of the warped image may appear jagged. To correct this, create a
      window using `multiSample=True` and `numSamples > 1` to smooth out these
      artifacts.

    Examples
    --------
    Here is a basic example of 2D rendering using the VisualSystemHD(tm). This
    is the binocular version of the dynamic 'plaid.py' demo::

        from psychopy import visual, core, event

        # Create a visual window
        win = visual.VisualSystemHD(fullscr=True, screen=1)

        # Initialize some stimuli, note contrast, opacity, ori
        grating1 = visual.GratingStim(win, mask="circle", color='white',
            contrast=0.5, size=(1.0, 1.0), sf=(4, 0), ori = 45, autoLog=False)
        grating2 = visual.GratingStim(win, mask="circle", color='white',
            opacity=0.5, size=(1.0, 1.0), sf=(4, 0), ori = -45, autoLog=False,
            pos=(0.1, 0.1))

        trialClock = core.Clock()
        t = 0
        while not event.getKeys() and t < 20:
            t = trialClock.getTime()

            for eye in ('left', 'right'):
                win.setBuffer(eye)  # change the buffer
                grating1.phase = 1 * t  # drift at 1Hz
                grating1.draw()  # redraw it
                grating2.phase = 2 * t    # drift at 2Hz
                grating2.draw()  # redraw it

            win.flip()

        win.close()
        core.quit()

    As you can see above, there are few changes needed to convert an existing 2D
    experiment to run on the VSHD. For 3D rendering with perspective, you need
    set `eyeOffset` and apply the projection by calling `setPerspectiveView`.
    (other projection modes are not implemented or supported right now)::

        from psychopy import visual, core, event

        # Create a visual window
        win = visual.VisualSystemHD(fullscr=True, screen=1,
            multiSample=True, nSamples=8)

        # text to display
        instr = visual.TextStim(win, text="Any key to quit", pos=(0, -.7))

        # create scene light at the pivot point
        win.lights = [
            visual.LightSource(win, pos=(0.4, 4.0, -2.0), lightType='point',
                        diffuseColor=(0, 0, 0), specularColor=(1, 1, 1))
        ]
        win.ambientLight = (0.2, 0.2, 0.2)

        # Initialize some stimuli, note contrast, opacity, ori
        ball = visual.SphereStim(win, radius=0.1, pos=(0, 0, -2), color='green',
            useShaders=False)

        iod = 6.2  # interocular separation in CM
        win.setEyeOffset(-iod / 2.0, 'left')
        win.setEyeOffset(iod / 2.0, 'right')

        trialClock = core.Clock()
        t = 0
        while not event.getKeys() and t < 20:
            t = trialClock.getTime()

            for eye in ('left', 'right'):
                win.setBuffer(eye)  # change the buffer

                # setup drawing with perspective
                win.setPerspectiveView()

                win.useLights = True  # switch on lights
                ball.draw()  # draw the ball
                # shut the lights, needed to prevent light color from affecting
                # 2D stim
                win.useLights = False

                # reset transform to draw text correctly
                win.resetEyeTransform()

                instr.draw()

            win.flip()

        win.close()
        core.quit()

    """
    def __init__(self, monoscopic=False, diopters=(-1, -1), lensCorrection=True,
                 distCoef=None, directDraw=False, model='vshd', *args,
                 **kwargs):
        """
        Parameters
        ----------
        monoscopic : bool
            Use monoscopic rendering. If `True`, the same image will be drawn to
            both eye buffers. You will not need to call `setBuffer`. It is not
            possible to set monoscopic mode after the window is created. It is
            recommended that you use monoscopic mode if you intend to display
            only 2D stimuli about the center of the display as it uses a less
            memory intensive rendering pipeline.
        diopters : tuple or list
            Initial diopter values for the left and right eye. Default is
            `(-1, -1)`, values must be integers.
        lensCorrection : bool
            Apply lens correction (barrel distortion) to the output. The amount
            of distortion applied can be specified using `distCoef`. If `False`,
            no distortion will be applied to the output and the entire display
            will be used. Not applying correction will result in pincushion
            distortion which produces a non-rectilinear output.
        distCoef : float
            Distortion coefficient for barrel distortion. If `None`, the
            recommended value will be used for the model of display. You can
            adjust the value to fine-tune the barrel distortion.
        directDraw : bool
            Direct drawing mode. Stimuli are drawn directly to the back buffer
            instead of creating separate buffer. This saves video memory but
            does not permit barrel distortion or monoscopic rendering. If
            `False`, drawing is done with two FBOs containing each eye's image.
        hwModel : str
            Model of the VisualSystemHD in use. Used to set viewing parameters
            accordingly. Default is 'vshd'. Cannot be changed after starting the
            application.

        """
        # warn if given `useFBO`
        if kwargs.get('useFBO', False):
            logging.warning(
                "Creating a window with `useFBO` is not recommended.")

        # call up a new window object
        super(VisualSystemHD, self).__init__(*args, **kwargs)

        # direct draw mode
        self._directDraw = directDraw

        # is monoscopic mode enabled?
        self._monoscopic = monoscopic and not self._directDraw
        self._lensCorrection = lensCorrection and not self._directDraw

        # hardware information for a given model of the display, used for
        # configuration
        self._hwModel = model
        self._hwDesc = vshdModels[self._hwModel]

        # distortion coefficient
        self._distCoef = \
            self._hwDesc['distCoef'] if distCoef is None else float(distCoef)

        # diopter settings for each eye, needed to compute actual FOV
        self._diopters = {'left': diopters[0], 'right': diopters[1]}

        # eye offsets, this will be standard when multi-buffer rendering gets
        # implemented in the main window class
        self._eyeOffsets = {'left': -3.1, 'right': 3.1}

        # look-up table of FOV values for each diopter setting
        self._fovLUT = self._hwDesc['configByDiopters']

        # get the dimensions of the buffer for each eye
        bufferWidth, bufferHieght = self.frameBufferSize
        bufferWidth = int(bufferWidth / 2.0)

        # viewports for each buffer
        self._bufferViewports = dict()
        self._bufferViewports['left'] = (0, 0, bufferWidth, bufferHieght)
        self._bufferViewports['right'] = \
            (bufferWidth if self._directDraw else 0,
             0, bufferWidth, bufferHieght)
        self._bufferViewports['back'] = \
            (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])

        # create render targets for each eye buffer
        self.buffer = None
        self._eyeBuffers = dict()

        # VAOs for distortion mesh
        self._warpVAOs = dict()

        # extents of the barrel distortion needed to compute FOV after
        # distortion
        self._distExtents = {
            'left': np.array([[-1, 0], [1, 0], [0, 1], [0, -1]]),
            'right': np.array([[-1, 0], [1, 0], [0, 1], [0, -1]])
        }

        # if we are using an FBO, keep a reference to its handles
        if self.useFBO:
            self._eyeBuffers['back'] = {
                'frameBuffer': self.frameBuffer,
                'frameTexture': self.frameTexture,
                'frameStencil': self._stencilTexture}

        self._setupEyeBuffers()  # setup additional framebuffers
        self._setupLensCorrection()  # setup lens correction meshes
        self.setBuffer('left')  # set to the back buffer on start

    @property
    def monoscopic(self):
        """`True` if using monoscopic mode."""
        return self._monoscopic

    @property
    def lensCorrection(self):
        """`True` if using lens correction."""
        return self._lensCorrection

    @lensCorrection.setter
    def lensCorrection(self, value):
        self._lensCorrection = value

    @property
    def distCoef(self):
        """Distortion coefficient (`float`)."""
        return self._distCoef

    @distCoef.setter
    def distCoef(self, value):
        if isinstance(value, (float, int,)):
            self._distCoef = float(value)
        elif value is None:
            self._distCoef = self._hwDesc['distCoef']
        else:
            raise ValueError('Invalid value for `distCoef`.')

        self._setupLensCorrection()  # deletes old VAOs

    @property
    def diopters(self):
        """Diopters value of the current eye buffer."""
        return self._diopters[self.buffer]

    @diopters.setter
    def diopters(self, value):
        self.setDiopters(value)

    def setDiopters(self, diopters, eye=None):
        """Set the diopters for a given eye.

        Parameters
        ----------
        diopters : int
            Set diopters for a given eye, ranging between -7 and +5.
        eye : str or None
            Eye to set, either 'left' or 'right'. If `None`, the currently
            set buffer will be used.

        """
        eye = self.buffer if eye is None else eye

        # check if diopters value in config
        if diopters not in self._hwDesc['configByDiopters'].keys():
            raise ValueError("Diopter setting invalid for display model.")

        try:
            self._diopters[eye] = int(diopters)
        except KeyError:
            raise ValueError(
                "Invalid `eye` specified, must be 'left' or 'right'.")

    @property
    def eyeOffset(self):
        """Eye offset for the current buffer in centimeters used for
        stereoscopic rendering. This works differently than the main window
        class as it sets the offset for the current buffer. The offset is saved
        and automatically restored when the buffer is selected.
        """
        return self._eyeOffsets[self.buffer] * 100.  # to centimeters

    @eyeOffset.setter
    def eyeOffset(self, value):
        self._eyeOffsets[self.buffer] = float(value) / 100.  # to meters

    def setEyeOffset(self, dist, eye=None):
        """Set the eye offset in centimeters.

        When set, successive rendering operations will use the new offset.

        Parameters
        ----------
        dist : float or int
            Lateral offset in centimeters from the nose, usually half the
            interocular separation. The distance is signed.
        eye : str or None
            Eye offset to set. Can either be 'left', 'right' or `None`. If
            `None`, the offset of the current buffer is used.

        """
        eye = self.buffer if eye is None else eye

        try:
            self._eyeOffsets[eye] = float(dist) / 100.  # to meters
        except KeyError:
            raise ValueError(
                "Invalid `eye` specified, must be 'left' or 'right'.")

    # def _getFocalLength(self, eye=None):
    #     """Get the focal length for a given `eye` in meters.
    #
    #     Parameters
    #     ----------
    #     eye : str or None
    #         Eye to use, either 'left' or 'right'. If `None`, the currently
    #         set buffer will be used.
    #
    #     """
    #     try:
    #         focalLength = 1. / self._diopters[eye]
    #     except KeyError:
    #         raise ValueError(
    #             "Invalid value for `eye`, must be 'left' or 'right'.")
    #     except ZeroDivisionError:
    #         raise ValueError("Value for diopters cannot be zero.")
    #
    #     return focalLength
    #
    # def _getMagFactor(self, eye=None):
    #     """Get the magnification factor of the lens for a given eye. Used to
    #     in part to compute the actual size of the object.
    #
    #     Parameters
    #     ----------
    #     eye : str or None
    #         Eye to use, either 'left' or 'right'. If `None`, the currently
    #         set buffer will be used.
    #
    #     """
    #     eye = self.buffer if eye is None else eye
    #     return (self._diopters[eye] / 4.) + 1.
    #
    # def _getScreenFOV(self, eye, direction='horizontal', degrees=True):
    #     """Compute the FOV of the display."""
    #     if direction not in ('horizontal', 'vertical'):
    #         raise ValueError("Invalid `direction` specified, must be "
    #                          "'horizontal' or 'vertical'.")
    #
    #     # todo: figure this out
    #
    # def _getPredictedFOV(self, size, eye=None):
    #     """Get the predicted vertical FOV of the display for a given eye.
    #
    #     Parameters
    #     ----------
    #     size : float
    #         Size of the object on screen in meters.
    #     eye : str or None
    #         Eye to use, either 'left' or 'right'. If `None`, the currently
    #         set buffer will be used.
    #
    #     """
    #     return np.degrees(2. * np.arctan(size / (2. * self._getFocalLength(eye))))
    #
    # def _getActualFOV(self, size, eye=None):
    #     """Get the actual FOV of an object of `size` for a given eye."""
    #     if eye not in ('left', 'right'):
    #         raise ValueError(
    #             "Invalid value for `eye`, must be 'left' or 'right'.")
    #
    #     # predFOV = self._getPredictedFOV(size, eye)
    #     actualFOV = 0.0098 * size ** 3 - 0.0576 * size ** 2 + 2.6728 * size - 0.0942
    #
    #     return actualFOV
    #
    # def getDistortion(self, size, eye=None):
    #     """Get the optical distortion amount (percent) for a stimulus of given
    #     `size` in degrees positioned at the center of the display."""
    #     predFOV = self._getPredictedFOV(size, eye)
    #     actualFOV = self._getActualFOV(size, eye)
    #
    #     return ((actualFOV - predFOV) * predFOV) * 100.

    def _getWarpExtents(self, eye):
        """Get the horizontal and vertical extents of the barrel distortion in
        normalized device coordinates. This is used to determine the FOV along
        each axis after barrel distortion.

        Parameters
        ----------
        eye : str
            Eye to compute the extents for.

        Returns
        -------
        ndarray
            2d array of coordinates [+X, -X, +Y, -Y] of the extents of the
            barrel distortion.

        """
        coords = np.array([
            [-1.0,  0.0],
            [ 1.0,  0.0],
            [ 0.0,  1.0],
            [ 0.0, -1.0]])

        try:
            bufferW, bufferH = self._bufferViewports[eye][2:]
        except KeyError:
            raise ValueError("Invalid eye buffer specified.")

        warpedCoords = mt.lensCorrectionSpherical(
            coords, self._distCoef, bufferW / bufferH)

        return warpedCoords

    def _setupLensCorrection(self):
        """Setup the VAOs needed for lens correction.
        """
        # don't create warp mesh if direct draw enabled
        if self._directDraw:
            return

        # clean up previous distortion data
        if self._warpVAOs:
            for vao in self._warpVAOs.values():
                gt.deleteVAO(vao)

        self._warpVAOs = {}
        for eye in ('left', 'right'):
            # setup vertex arrays for the output quad
            bufferW, bufferH = self._bufferViewports[eye][2:]
            aspect = bufferW / bufferH
            vertices, texCoord, normals, faces = gt.createMeshGrid(
                (2.0, 2.0), subdiv=256, tessMode='radial')

            # recompute vertex positions
            vertices[:, :2] = mt.lensCorrectionSpherical(
                vertices[:, :2], coefK=self.distCoef, aspect=aspect)

            # create the VAO for the eye buffer
            vertexVBO = gt.createVBO(vertices, usage=GL.GL_DYNAMIC_DRAW)
            texCoordVBO = gt.createVBO(texCoord, usage=GL.GL_DYNAMIC_DRAW)
            indexBuffer = gt.createVBO(
                faces.flatten(),
                target=GL.GL_ELEMENT_ARRAY_BUFFER,
                dataType=GL.GL_UNSIGNED_INT)
            attribBuffers = {GL.GL_VERTEX_ARRAY: vertexVBO,
                             GL.GL_TEXTURE_COORD_ARRAY: texCoordVBO}
            self._warpVAOs[eye] = gt.createVAO(attribBuffers,
                                               indexBuffer=indexBuffer,
                                               legacy=True)

            # get the extents of the warping
            self._distExtents[eye] = self._getWarpExtents(eye)

    def _setupEyeBuffers(self):
        """Setup additional buffers for rendering content to each eye.
        """
        if self._directDraw:  # don't create additional buffers is direct draw
            return

        def createFramebuffer(width, height):
            """Function for setting up additional buffer"""
            # create a new framebuffer
            fboId = GL.GLuint()
            GL.glGenFramebuffers(1, ctypes.byref(fboId))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fboId)

            # create a texture to render to, required for warping
            texId = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(texId))
            GL.glBindTexture(GL.GL_TEXTURE_2D, texId)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,
                               GL.GL_TEXTURE_MAG_FILTER,
                               GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,
                               GL.GL_TEXTURE_MIN_FILTER,
                               GL.GL_LINEAR)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32F_ARB,
                            int(width), int(height), 0,
                            GL.GL_RGBA, GL.GL_FLOAT, None)
            GL.glFramebufferTexture2D(GL.GL_FRAMEBUFFER,
                                      GL.GL_COLOR_ATTACHMENT0,
                                      GL.GL_TEXTURE_2D,
                                      texId,
                                      0)

            # create a render buffer
            rbId = GL.GLuint()
            GL.glGenRenderbuffers(1, ctypes.byref(rbId))
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rbId)
            GL.glRenderbufferStorage(
                GL.GL_RENDERBUFFER,
                GL.GL_DEPTH24_STENCIL8,
                int(width),
                int(height))
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_DEPTH_ATTACHMENT,
                GL.GL_RENDERBUFFER,
                rbId)
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_STENCIL_ATTACHMENT,
                GL.GL_RENDERBUFFER,
                rbId)
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

            # clear the buffer
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

            return fboId, texId, rbId

        if not self._monoscopic:
            # create eye buffers
            for eye in ('left', 'right'):
                # get dimensions of required buffer
                bufferW, bufferH = self._bufferViewports[eye][2:]
                fboId, texId, rbId = createFramebuffer(bufferW, bufferH)

                # add new buffers
                self._eyeBuffers[eye] = {
                    'frameBuffer': fboId,
                    'frameTexture': texId,
                    'frameStencil': rbId}
        else:
            # only the left eye buffer is created
            bufferW, bufferH = self._bufferViewports['left'][2:]
            fboId, texId, rbId = createFramebuffer(bufferW, bufferH)
            self._eyeBuffers['left'] = {
                'frameBuffer': fboId,
                'frameTexture': texId,
                'frameStencil': rbId}

            self._eyeBuffers['right'] = self._eyeBuffers['left']

    def setBuffer(self, buffer, clear=True):
        """Set the eye buffer to draw to. Subsequent draw calls will be diverted
        to the specified eye.

        Parameters
        ----------
        buffer : str
            Eye buffer to draw to. Values can either be 'left' or 'right'.
        clear : bool
            Clear the buffer prior to drawing.

        """
        # check if the buffer name is valid
        if buffer not in ('left', 'right', 'back'):
            raise RuntimeError("Invalid buffer name specified.")

        # don't change the buffer if same, but allow clearing
        if buffer != self.buffer:
            if not self._directDraw:
                # handle when the back buffer is selected
                if buffer == 'back':
                    if self.useFBO:
                        GL.glBindFramebuffer(
                            GL.GL_FRAMEBUFFER,
                            self._eyeBuffers[buffer]['frameBuffer'])
                    else:
                        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
                else:
                    GL.glBindFramebuffer(
                        GL.GL_FRAMEBUFFER, self._eyeBuffers[buffer]['frameBuffer'])

            self.viewport = self.scissor = self._bufferViewports[buffer]

            GL.glEnable(GL.GL_SCISSOR_TEST)
            self.buffer = buffer  # set buffer string

        if clear:
            self.setColor(self.color)  # clear the buffer to the window color
            GL.glClearDepth(1.0)
            GL.glDepthMask(GL.GL_TRUE)
            GL.glClear(
                GL.GL_COLOR_BUFFER_BIT |
                GL.GL_DEPTH_BUFFER_BIT |
                GL.GL_STENCIL_BUFFER_BIT)

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)

    def setPerspectiveView(self, applyTransform=True, clearDepth=True):
        """Set the projection and view matrix to render with perspective.

        Matrices are computed using values specified in the monitor
        configuration with the scene origin on the screen plane. Calculations
        assume units are in meters. If `eyeOffset != 0`, the view will be
        transformed laterally, however the frustum shape will remain the
        same.

        Note that the values of :py:attr:`~Window.projectionMatrix` and
        :py:attr:`~Window.viewMatrix` will be replaced when calling this
        function.

        Parameters
        ----------
        applyTransform : bool
            Apply transformations after computing them in immediate mode. Same
            as calling :py:attr:`~Window.applyEyeTransform()` afterwards if
            `False`.
        clearDepth : bool, optional
            Clear the depth buffer.

        """
        # Not in full screen mode? Need to compute the dimensions of the display
        # area to ensure disparities are correct even when in windowed-mode.
        aspect = self.size[0] / self.size[1]

        # use these instead of those from the monitor configuration
        vfov = self._fovLUT[self._diopters[self.buffer]]['vfov']
        scrDist = self._fovLUT[self._diopters[self.buffer]]['dist']

        frustum = vt.computeFrustumFOV(
            vfov,
            aspect,  # aspect ratio
            scrDist,
            nearClip=self._nearClip,
            farClip=self._farClip)

        self._projectionMatrix = \
            vt.perspectiveProjectionMatrix(*frustum, dtype=np.float32)

        # translate away from screen
        self._viewMatrix = np.identity(4, dtype=np.float32)
        self._viewMatrix[0, 3] = -self._eyeOffsets[self.buffer]  # apply eye offset
        self._viewMatrix[2, 3] = -scrDist  # displace scene away from viewer

        if applyTransform:
            self.applyEyeTransform(clearDepth=clearDepth)

    def _blitEyeBuffer(self, eye):
        """Warp and blit to the appropriate eye buffer.

        Parameters
        ----------
        eye : str
            Eye buffer being used.

        """
        GL.glBindTexture(GL.GL_TEXTURE_2D,
                         self._eyeBuffers[eye]['frameTexture'])

        GL.glEnable(GL.GL_SCISSOR_TEST)
        # set the viewport and scissor rect for the buffer
        frameW, frameH = self._bufferViewports[eye][2:]

        offset = 0 if eye == 'left' else frameW
        self.viewport = self.scissor = (offset, 0, frameW, frameH)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1, 1, -1, 1, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        # anti-aliasing the edges of the polygon
        GL.glEnable(GL.GL_MULTISAMPLE)

        # blit the quad covering the side of the display the eye is viewing
        if self.lensCorrection:
            gt.drawVAO(self._warpVAOs[eye])
        else:
            self._renderFBO()

        GL.glDisable(GL.GL_MULTISAMPLE)

        # reset
        GL.glDisable(GL.GL_SCISSOR_TEST)
        self.viewport = self.scissor = \
            (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])

    def _startOfFlip(self):
        """Custom :py:class:`~Rift._startOfFlip` for HMD rendering. This
        finalizes the HMD texture before diverting drawing operations back to
        the on-screen window. This allows :py:class:`~Rift.flip` to swap the
        on-screen and HMD buffers when called. This function always returns
        `True`.

        Returns
        -------
        True

        """
        # nop if we are still setting up the window
        if not hasattr(self, '_eyeBuffers'):
            return True

        # direct draw being used, don't do FBO blit
        if self._directDraw:
            return True

        # Switch off multi-sampling
        # GL.glDisable(GL.GL_MULTISAMPLE)
        oldColor = self.color
        self.setColor((-1, -1, -1))
        self.setBuffer('back', clear=True)

        self._prepareFBOrender()
        # need blit the framebuffer object to the actual back buffer

        # unbind the framebuffer as the render target
        GL.glDisable(GL.GL_BLEND)
        stencilOn = self.stencilTest
        self.stencilTest = False

        # before flipping need to copy the renderBuffer to the
        # frameBuffer
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glColor3f(1.0, 1.0, 1.0)  # glColor multiplies with texture
        GL.glColorMask(True, True, True, True)

        # blit the textures to the back buffer
        for eye in ('left', 'right'):
            self._blitEyeBuffer(eye)

        GL.glEnable(GL.GL_BLEND)
        self._finishFBOrender()

        self.stencilTest = stencilOn

        self.setColor(oldColor)

        # This always returns True
        return True

    def _endOfFlip(self, clearBuffer):
        """Override end of flip with custom color channel masking if required.
        """
        if clearBuffer:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # nop if we are still setting up the window
        if hasattr(self, '_eyeBuffers'):
            self.setBuffer('left', clear=clearBuffer)


if __name__ == "__main__":
    pass
