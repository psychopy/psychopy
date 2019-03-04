#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Oculus Rift HMD support for PsychoPy.

Copyright (C) 2018 - Matthew D. Cutone, The Centre for Vision Research, Toronto,
Ontario, Canada

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

_HAS_PSYCHXR_ = True

try:
    import psychxr.ovr as ovr
except ImportError:
    _HAS_PSYCHXR_ = False

from . import window

# if we have PsychXR, do the rest of the importing
if _HAS_PSYCHXR_:
    import sys
    import platform
    import ctypes
    import math
    from psychopy import platform_specific, logging
    import pyglet.gl as GL
    from psychopy.tools.attributetools import setAttribute
    import numpy as np

    ovr.capi.debug_mode = True  # enable debug mode, not much overhead

reportNDroppedFrames = 5


class Rift(window.Window):
    """Class provides a display and peripheral interface for the Oculus Rift
    (see: https://www.oculus.com/) head-mounted display.

    """

    def __init__(
            self,
            fovType='recommended',
            trackingOriginType='eye',
            texelsPerPixel=1.0,
            headLocked=False,
            highQuality=True,
            nearClip=0.1,
            farClip=100.0,
            monoscopic=False,
            samples=1,
            mirrorRes=None,
            legacyOpenGL=True,
            warnAppFrameDropped=True,
            *args,
            **kwargs):
        """

        Parameters
        ----------
        fovType : :obj:`str`
            Field-of-view (FOV) configuration type. Using 'recommended'
            auto-configures the FOV using the recommended parameters computed by
            the runtime. Using 'symmetric' forces a symmetric FOV using optimal
            parameters from the SDK.
        trackingOriginType : :obj:`str`
            Specify the HMD origin type. If 'floor', the height of the user
            is added to the head tracker by LibOVR.
        texelsPerPixel : :obj:`float`
            Texture pixels per display pixel at FOV center. A value of 1.0
            results in 1:1 mapping. A fractional value results in a lower
            resolution draw buffer which may increase performance.
        headLocked : :obj:`bool`
            Lock the head position to the world origin. This cancels out any
            translation and rotation from the headset. Note, hand poses are
            NOT transformed accordingly (this will be addressed eventually).
        highQuality : :obj:`bool`
            Configure the compositor to use anisotropic texture sampling (4x).
            This reduces aliasing artifacts resulting from high frequency
            details particularly in the periphery.
        nearClip : :obj:`float`
            Location of the near clipping plane in GL units (meters by default)
            from the viewer.
        farClip : :obj:`float`
            Location of the far clipping plane in GL units (meters by default)
            from the viewer.
        monoscopic : :obj:`bool`
            Enable monoscopic rendering mode which presents the same image to
            both eyes. Eye poses used will be both centered at the HMD origin.
            Monoscopic mode uses a separate rendering pipeline which reduces
            VRAM usage. When in monoscopic mode, you do not need to call
            'setBuffer' prior to rendering (doing so will do have no effect).
        samples : :obj:`int`
            Specify the number of samples for anti-aliasing. When >1,
            multi-sampling logic is enabled in the rendering pipeline. If 'max'
            is specified, the largest number of samples supported by the
            platform is used. If floating point textures are used, MSAA sampling
            is disabled. Must be power of two value.
        legacyOpenGL : :obj:`bool`
            Disable 'immediate mode' OpenGL calls in the rendering pipeline.
            Specifying False maintains compatibility with existing PsychoPy
            stimuli drawing routines. Use True when computing transformations
            using some other method and supplying shaders matrices directly.
        mirrorRes: :obj:`list` of :obj:`int`
            Resolution of the mirror texture. If None, the resolution will
            match the window size.
        warnAppFrameDropped : :obj:`bool`
            Log a warning if the application drops a frame. This occurs when
            the application fails to submit a frame to the compositor on-time.
            Application frame drops can have many causes, such as running
            routines in your application loop that take too long to complete.
            However, frame drops can happen sporadically due to driver bugs and
            running background processes (such as Windows Update). Use the
            performance HUD to help diagnose the causes of frame drops.

        """

        if not _HAS_PSYCHXR_:
            raise ModuleNotFoundError(
                "PsychXR must be installed to use the Rift class. Exiting.")

        self._closed = False
        self._legacyOpenGL = legacyOpenGL
        self._monoscopic = monoscopic
        self._texelsPerPixel = texelsPerPixel
        self._headLocked = headLocked
        self._highQuality = highQuality

        self._samples = samples
        self._mirrorRes = mirrorRes

        # this can be changed while running
        self.warnAppFrameDropped = warnAppFrameDropped

        # check if we are using Windows
        if platform.system() != 'Windows':
            raise RuntimeError("Rift class only supports Windows OS at this " +
                               "time, exiting.")

        # check if we are using 64-bit Python
        if platform.architecture()[0] != '64bit':  # sys.maxsize != 2**64
            raise RuntimeError("Rift class only supports 64-bit Python, " +
                               "exiting.")

        # check if the background service is running and an HMD is connected
        if not ovr.capi.isOculusServiceRunning():
            raise RuntimeError("HMD service is not available or started, " +
                               "exiting.")

        if not ovr.capi.isHmdConnected():
            raise RuntimeError("Cannot find any connected HMD, check " +
                               "connections and try again.")

        # create a VR session, do some initial configuration
        ovr.capi.startSession()

        # get HMD descriptor, contains information about the unit
        self._hmdDesc = ovr.capi.getHmdDesc()

        # Get additional details about the user from their Oculus Home profile.
        # We don't need this information in most cases, but it might be useful
        # for setting up the VR environment.
        self._playerHeightMeters = ovr.capi.getPlayerHeight()
        self._playerEyeHeightMeters = ovr.capi.getEyeHeight()

        # update session status object
        self._sessionStatus = ovr.capi.getSessionStatus()

        # configure the internal render descriptors based on the requested
        # viewing parameters.
        if fovType == 'symmetric' or self._monoscopic:
            # Use symmetric FOVs for cases where off-center frustums are not
            # desired. This is required for monoscopic rendering to permit
            # comfortable binocular fusion.
            fovLeft = self._hmdDesc.DefaultEyeFov[0]
            fovRight = self._hmdDesc.DefaultEyeFov[1]

            # get the maximum vertical and horizontal FOVs
            fovMax = ovr.math.ovrFovPort.max(fovLeft, fovRight)
            combinedTanHorz = max(fovMax.LeftTan, fovMax.RightTan)
            combinedTanVert = max(fovMax.UpTan, fovMax.DownTan)

            fovBoth = ovr.math.ovrFovPort()
            fovBoth.RightTan = fovBoth.LeftTan = combinedTanHorz
            fovBoth.UpTan = fovBoth.DownTan = combinedTanVert
            self._fov = (fovBoth, fovBoth)

        elif fovType == 'recommended':
            # use the recommended FOVs, these have wider FOVs looking outward
            # due to off-center frustums.
            self._fov = (self._hmdDesc.DefaultEyeFov[0],
                         self._hmdDesc.DefaultEyeFov[1])

        elif fovType == 'max':
            # the maximum FOVs for the HMD supports
            self._fov = (self._hmdDesc.MaxEyeFov[0],
                         self._hmdDesc.MaxEyeFov[1])

        else:
            raise ValueError(
                "Invalid FOV type '{}' specified.".format(fovType))

        # configure the eye render descriptors to use the computed FOVs
        for eye in range(ovr.capi.ovrEye_Count):
            ovr.capi.configEyeRenderDesc(eye, self._fov[eye])

        # Compute texture sizes for render buffers, these are reported by the
        # LibOVR SDK based on the FOV settings specified above.
        texSizeLeft = ovr.capi.getFovTextureSize(
            ovr.capi.ovrEye_Left, self._fov[0], self._texelsPerPixel)
        texSizeRight = ovr.capi.getFovTextureSize(
            ovr.capi.ovrEye_Right, self._fov[1], self._texelsPerPixel)

        # we are using a shared texture, so we need to combine dimensions
        if not self._monoscopic:
            buffer_w = texSizeLeft.w + texSizeRight.w
        else:
            buffer_w = max(texSizeLeft.w, texSizeRight.w)

        buffer_h = max(texSizeLeft.h, texSizeRight.h)

        # buffer viewport size
        self._hmdBufferSize = buffer_w, buffer_h

        # Calculate the swap texture size. These can differ in later
        # configurations, right now they are the same.
        self._swapTextureSize = self._hmdBufferSize

        # Compute the required viewport parameters for the given buffer and
        # texture sizes. If we are using a power of two texture, we need to
        # centre the viewports on the textures.
        if not self._monoscopic:
            self._viewports = [ovr.math.ovrRecti(), ovr.math.ovrRecti()]

            # left eye viewport
            self._viewports[0].x = 0
            self._viewports[0].y = 0
            self._viewports[0].w = int(self._hmdBufferSize[0] / 2)
            self._viewports[0].h = self._hmdBufferSize[1]

            # right eye viewport
            self._viewports[1].x = int(self._swapTextureSize[0] / 2)
            self._viewports[1].y = 0
            self._viewports[1].w = int(self._hmdBufferSize[0] / 2)
            self._viewports[1].h = self._hmdBufferSize[1]

            # give the viewports to PsychXR to setup the render layer
            for eye in range(ovr.capi.ovrEye_Count):
                ovr.capi.setRenderViewport(eye, self._viewports[eye])

            self.scrWidthPIX = int(self._hmdBufferSize[0] / 2)

        else:
            # In mono mode, we use the same viewport for both eyes. Therefore,
            # the swap texture only needs to be half as wide. This save VRAM
            # and does not require buffer changes when rendering.
            self._viewports = ovr.math.ovrRecti(
                0, 0, self._hmdBufferSize[0], self._hmdBufferSize[1])

            # pass the same viewport to both eye
            for eye in range(ovr.capi.ovrEye_Count):
                ovr.capi.setRenderViewport(eye, self._viewports)

            self.scrWidthPIX = int(self._hmdBufferSize[0])

        # frame index
        self._frameIndex = 0

        # setup a mirror texture
        self._mirrorRes = mirrorRes

        # view buffer to divert operations to, if None, drawing is sent to the
        # on-screen window.
        self.buffer = None

        # tracking state object, stores head and hand tracking information
        self._trackingState = None

        # setup clipping planes, these are required for computing the
        # projection matrices
        if 0.0 <= nearClip < farClip:
            self._nearClip = float(nearClip)
            self._farClip = float(farClip)
        else:
            raise ValueError("Invalid 'nearClip' and 'farClip' interval "
                             "specified.")

        # View matrices, these are updated every frame based on computed head
        # position. Projection matrices need only to be computed once.
        if not self._monoscopic:
            self._projectionMatrix = \
                [ovr.math.ovrMatrix4f(), ovr.math.ovrMatrix4f()]
            self._viewMatrix = [ovr.math.ovrMatrix4f(), ovr.math.ovrMatrix4f()]
        else:
            self._projectionMatrix = ovr.math.ovrMatrix4f()
            self._viewMatrix = ovr.math.ovrMatrix4f()

        self._updateProjectionMatrix()

        # buffer flags
        self._bufferFlags = {'left': ovr.capi.ovrEye_Left,
                             'right': ovr.capi.ovrEye_Right,
                             'mono': ovr.capi.ovrEye_Left}

        # if the GLFW backend is being used, disable v-sync since the HMD runs
        # at a different frequency.
        kwargs['swapInterval'] = 0

        # force checkTiming off and quad-buffer stereo
        kwargs["checkTiming"] = False
        kwargs["stereo"] = False
        kwargs['useFBO'] = True
        kwargs['multiSample'] = False
        # kwargs['waitBlanking'] = False

        # do not allow 'endFrame' to be called until _startOfFlip is called
        self._allowHmdRendering = False

        # VR pose data, updated every frame
        self.headPose = ovr.math.ovrPosef()
        self.hmdToEyePoses = ovr.capi.getHmdToEyePose()
        self.eyePoses = self.hmdToEyePoses  # initial values
        self.handPoses = [ovr.math.ovrPosef(), ovr.math.ovrPosef()]

        # set the tracking origin type
        self.trackingOriginType = trackingOriginType

        # specified VR origin, this is where the HMD's pose appears in the scene
        self.hmdOriginPose = ovr.math.ovrPosef()

        # performance information
        self._perfStatsLastFrame = None
        self._perfStatsThisFrame = ovr.capi.getFrameStats()
        self.nDroppedFrames = 0

        # call up a new window object
        super(Rift, self).__init__(*args, **kwargs)

    @property
    def size(self):
        """Size property to get the dimensions of the view buffer instead of
        the window. If there are no view buffers, always return the dims of the
        window.

        """
        if self.buffer is None:
            return self.__dict__['size']
        else:
            if self._monoscopic:
                return np.array(
                    (self._hmdBufferSize[0], self._hmdBufferSize[1]),
                    np.int)
            else:
                return np.array(
                    (int(self._hmdBufferSize[0] / 2), self._hmdBufferSize[1]),
                    np.int)

    @size.setter
    def size(self, value):
        """Set the size of the window.

        """
        self.__dict__['size'] = np.array(value, np.int)

    def setSize(self, value, log=True):
        setAttribute(self, 'size', value, log=log)

    def setHudMode(self, mode='Off'):
        ovr.capi.perfHudMode(mode)

    @property
    def productName(self):
        """Get the HMD's product name.

        Returns
        -------
        str
            UTF-8 encoded string containing the product name.

        """
        return self._hmdDesc.ProductName

    @property
    def manufacturer(self):
        """Get the connected HMD's manufacturer.

        Returns
        -------
        str
            UTF-8 encoded string containing the manufacturer name.

        """
        return self._hmdDesc.Manufacturer

    @property
    def serialNumber(self):
        """Get the connected HMD's unique serial number. Use this to identify
        a particular unit if you own many.

        Returns
        -------
        str
            UTF-8 encoded string containing the devices serial number.

        """
        return self._hmdDesc.SerialNumber

    @property
    def firmwareVersion(self):
        """Get the firmware version of the active HMD. Returns a tuple
        containing the major and minor version.

        Returns
        -------
        tuple (int, int)
            Firmware major and minor version.

        """
        return self._hmdDesc.FirmwareMajor, self._hmdDesc.FirmwareMinor

    @property
    def resolution(self):
        """Get the HMD's raster display size.

        Returns
        -------
        tuple (int, int)
            Width and height in pixels.

        """
        return self._hmdDesc.Resolution

    @property
    def displayRefreshRate(self):
        """Get the HMD's display refresh rate. This rate is independent of the
        monitor display rate.

        Returns
        -------
        float
            Refresh rate in Hz.

        """
        return self._hmdDesc.DisplayRefreshRate

    @property
    def trackingOriginType(self):
        """Current tracking origin type."""
        return self.getTrackingOriginType()

    @trackingOriginType.setter
    def trackingOriginType(self, value):
        self.setTrackinOrigin(value)

    def getTrackingOriginType(self):
        """Get the current tracking origin type.

        Returns
        -------
        str

        """
        return ovr.capi.getTrackingOriginType()

    def setTrackinOrigin(self, origin_type='floor', recenter=False):
        """Set the tracking origin type. Can either be 'floor' or 'eye'. The
        effect of changing types is immediate.

        Parameters
        ----------
        origin_type : str
            Tracking origin type to use, can be either 'floor' or 'eye'.
        recenter : boolean
            If True, the tracking origin is applied immediately.

        Returns
        -------
        None

        """
        if origin_type not in ['floor', 'eye']:
            raise ValueError("Invalid tracking origin type '{}', must be 'eye' "
                             "or 'floor'.")

        ovr.capi.setTrackingOriginType(origin_type)

        if recenter:
            ovr.capi.recenterTrackingOrigin()

    def recenterTrackingOrigin(self):
        """Recenter the tracking origin.

        Returns
        -------
        None

        """
        ovr.capi.recenterTrackingOrigin()

    @property
    def shouldQuit(self):
        """Check if the user requested the application should quit through the
        headset's interface.

        Returns
        -------
        bool
            True if user requested the application quit via some menu in the
            HMD, otherwise False.

        """
        return self._sessionStatus.ShouldQuit

    @property
    def isVisible(self):
        """Check if the app has focus in the HMD and is visible to the viewer.

        Returns
        -------
        bool
            True if app has focus and is visible in the HMD, otherwise False.

        """
        return self._sessionStatus.IsVisible

    @property
    def isHmdMounted(self):
        """Check if the HMD is mounted on the user's head.

        Returns
        -------
        bool
            True if the HMD is being worn, otherwise False.

        """
        return self._sessionStatus.IsHmdMounted

    @property
    def isHmdPresent(self):
        """Check if the HMD is present.

        Returns
        -------
        bool
            True if the HMD is present, otherwise False.

        """
        return self._sessionStatus.IsHmdPresent

    @property
    def shouldRecenter(self):
        """Check if the user requested the origin be recentered through the
        headset's interface.

        Returns
        -------
        bool
            True if user requested the application recenter itself to reposition
            the origin, else False.

        """
        return self._sessionStatus.ShouldRecenter

    @property
    def displayLost(self):
        """Check of the display has been lost.

        Returns
        -------
        bool

        """
        return self._sessionStatus.DisplayLost

    @property
    def hasInputFocus(self):
        """Check if the application currently has input focus.

        Returns
        -------
        bool

        """
        return self._sessionStatus.HasInputFocus

    @property
    def overlayPresent(self):
        return self._sessionStatus.OverlayPresent

    def _setupFrameBuffer(self):
        """Override the default framebuffer init code in window.Window to use
        the HMD swap chain. The HMD's swap texture and render buffer are
        configured here.

        If multisample anti-aliasing (MSAA) is enabled, a secondary render
        buffer is created. Rendering is diverted to the multi-sample buffer
        when drawing, which is then resolved into the HMD's swap chain texture
        prior to committing it to the chain. Consequently, you cannot pass
        the texture attached to the FBO specified by frameBuffer until the MSAA
        buffer is resolved. Doing so will result in a blank texture.

        Returns
        -------
        None

        """
        # configure swap chain
        swap_config = ovr.capi.ovrTextureSwapChainDesc()
        swap_config.Type = ovr.capi.ovrTexture_2D
        swap_config.Format = ovr.capi.OVR_FORMAT_R8G8B8A8_UNORM_SRGB
        swap_config.Width = self._swapTextureSize[0]
        swap_config.Height = self._swapTextureSize[1]
        # swap_config.MipLevels = 8

        # render layer flags
        flags = ovr.capi.ovrLayerFlag_TextureOriginAtBottomLeft  # always set
        if self._highQuality:
            flags |= ovr.capi.ovrLayerFlag_HighQuality

        ovr.capi.setRenderLayerFlags(flags)

        # create the swap chain and keep its handle, the same swap chain texture
        # is used for both eyes here.
        #
        self._swapChain = ovr.capi.createTextureSwapChainGL(swap_config)
        ovr.capi.setRenderSwapChain(ovr.capi.ovrEye_Left, self._swapChain)
        ovr.capi.setRenderSwapChain(ovr.capi.ovrEye_Right, None)

        # Use MSAA if more than one sample is specified. If enabled, a render
        # buffer will be created.
        #
        max_samples = GL.GLint()
        GL.glGetIntegerv(GL.GL_MAX_SAMPLES, max_samples)
        if isinstance(self._samples, int):
            if (self._samples & (self._samples - 1)) != 0:
                # power of two?
                logging.warning(
                    'Invalid number of MSAA samples provided, must be '
                    'power of two. Disabling.')
            elif 0 > self._samples > max_samples.value:
                # check if within range
                logging.warning(
                    'Invalid number of MSAA samples provided, outside of valid '
                    'range. Disabling.')
        elif isinstance(self._samples, str):
            if self._samples == 'max':
                self._samples = max_samples.value

        # create an MSAA render buffer if self._samples > 1
        self.frameBufferMsaa = GL.GLuint()  # is zero if not configured
        if self._samples > 1:
            # multi-sample FBO and rander buffer
            GL.glGenFramebuffers(1, ctypes.byref(self.frameBufferMsaa))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBufferMsaa)

            # we don't need a multi-sample texture
            rb_color_msaa_id = GL.GLuint()
            GL.glGenRenderbuffers(1, ctypes.byref(rb_color_msaa_id))
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rb_color_msaa_id)
            GL.glRenderbufferStorageMultisample(
                GL.GL_RENDERBUFFER, self._samples, GL.GL_RGBA8,
                int(self._swapTextureSize[0]), int(self._swapTextureSize[1]))
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_RENDERBUFFER,
                rb_color_msaa_id)
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

            rb_depth_msaa_id = GL.GLuint()
            GL.glGenRenderbuffers(1, ctypes.byref(rb_depth_msaa_id))
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rb_depth_msaa_id)
            GL.glRenderbufferStorageMultisample(
                GL.GL_RENDERBUFFER, self._samples, GL.GL_DEPTH24_STENCIL8,
                int(self._swapTextureSize[0]), int(self._swapTextureSize[1]))
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER,
                rb_depth_msaa_id)
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER, GL.GL_STENCIL_ATTACHMENT, GL.GL_RENDERBUFFER,
                rb_depth_msaa_id)

            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
            GL.glClear(GL.GL_STENCIL_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

        # create a frame buffer object as a render target for the HMD textures
        self.frameBuffer = GL.GLuint()
        GL.glGenFramebuffers(1, ctypes.byref(self.frameBuffer))
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBuffer)

        # initialize the frame texture variable
        self.frameTexture = 0

        # create depth and stencil render buffers
        depth_rb_id = GL.GLuint()
        GL.glGenRenderbuffers(1, ctypes.byref(depth_rb_id))
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, depth_rb_id)
        GL.glRenderbufferStorage(
            GL.GL_RENDERBUFFER,
            GL.GL_DEPTH24_STENCIL8,
            int(self._swapTextureSize[0]),
            int(self._swapTextureSize[1]))
        GL.glFramebufferRenderbuffer(
            GL.GL_FRAMEBUFFER,
            GL.GL_DEPTH_ATTACHMENT,
            GL.GL_RENDERBUFFER,
            depth_rb_id)
        GL.glFramebufferRenderbuffer(
            GL.GL_FRAMEBUFFER,
            GL.GL_STENCIL_ATTACHMENT,
            GL.GL_RENDERBUFFER,
            depth_rb_id)
        GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        self._frameStencil = depth_rb_id  # should make this the MSAA's?

        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

        # Setup the mirror texture framebuffer. The swap chain is managed
        # internally by PsychXR.
        if self._mirrorRes is None:
            self._mirrorRes = self.size

        mirror_desc = ovr.capi.ovrMirrorTextureDesc()
        mirror_desc.Format = ovr.capi.OVR_FORMAT_R8G8B8A8_UNORM_SRGB
        mirror_desc.Width = self._mirrorRes[0]
        mirror_desc.Height = self._mirrorRes[1]

        self._mirrorFbo = GL.GLuint()
        GL.glGenFramebuffers(1, ctypes.byref(self._mirrorFbo))
        ovr.capi.setupMirrorTexture(mirror_desc)

        GL.glDisable(GL.GL_TEXTURE_2D)
        # GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        return True

    def _resolveMSAA(self):
        """Resolve multisample anti-aliasing (MSAA). If MSAA is enabled, drawing
        operations are diverted to a special multisample render buffer. Pixel
        data must be 'resolved' by blitting it to the swap chain texture. If
        not, the texture will be blank.

        NOTE: You cannot perform operations on the default FBO (at frameBuffer)
        when MSAA is enabled. Any changes will be over-written when 'flip' is
        called.

        Returns
        -------
        None

        """
        # if multi-sampling is off, just return the frame texture
        if self._samples == 1:
            return

        # bind framebuffer
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.frameBufferMsaa)
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, self.frameBuffer)

        # bind the HMD swap texture to the draw buffer
        GL.glFramebufferTexture2D(
            GL.GL_DRAW_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D, self.frameTexture, 0)

        # blit the texture
        fbo_w, fbo_h = self._swapTextureSize
        GL.glViewport(0, 0, fbo_w, fbo_h)
        GL.glScissor(0, 0, fbo_w, fbo_h)
        GL.glBlitFramebuffer(0, 0, fbo_w, fbo_h,
                             0, 0, fbo_w, fbo_h,  # flips texture
                             GL.GL_COLOR_BUFFER_BIT,
                             GL.GL_NEAREST)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def _prepareMonoFrame(self, clear=True):
        """Prepare a frame for monoscopic rendering. This is called
        automatically after 'startHmdFrame' if monoscopic rendering is enabled.

        """
        # bind the framebuffer, if MSAA is enabled binding the texture is
        # deferred until the MSAA buffer is resolved.
        if self._samples > 1:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBufferMsaa)
        else:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBuffer)
            GL.glFramebufferTexture2D(
                GL.GL_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_TEXTURE_2D,
                self.frameTexture,
                0)

        # use the mono viewport
        self.buffer = 'mono'
        GL.glEnable(GL.GL_SCISSOR_TEST)
        viewPort = self._viewports.asTuple()
        GL.glViewport(*viewPort)
        GL.glScissor(*viewPort)

        if clear:
            self.setColor(self.color)  # clear the texture to the window color
            GL.glClear(
                GL.GL_COLOR_BUFFER_BIT |
                GL.GL_DEPTH_BUFFER_BIT |
                GL.GL_STENCIL_BUFFER_BIT
            )

        # if self.sRGB:
        #    GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)

        if self._samples > 1:
            GL.glEnable(GL.GL_MULTISAMPLE)

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)

    def setBuffer(self, buffer, clear=True):
        """Set the active stereo draw buffer.

        Warning! The window.Window.size property will return the buffer's
        dimensions in pixels instead of the window's when setBuffer is set to
        'left' or 'right'.

        Parameters
        ----------
        buffer : str
            View buffer to divert successive drawing operations to, can be
            either 'left' or 'right'.
        clear : boolean
            Clear the color, stencil and depth buffer.

        Returns
        -------
        None

        """
        # if monoscopic, nop
        if self._monoscopic:
            return

        # check if the buffer name is valid
        if buffer not in ('left', 'right'):
            raise RuntimeError("Invalid buffer name specified.")

        # bind the framebuffer, if MSAA is enabled binding the texture is
        # deferred until the MSAA buffer is resolved.
        if self._samples > 1:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBufferMsaa)
        else:
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBuffer)
            GL.glFramebufferTexture2D(
                GL.GL_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_TEXTURE_2D,
                self.frameTexture,
                0)

        self.buffer = buffer  # set buffer string
        GL.glEnable(GL.GL_SCISSOR_TEST)
        viewPort = self._viewports[self._bufferFlags[buffer]].asTuple()
        GL.glViewport(*viewPort)
        GL.glScissor(*viewPort)

        if clear:
            self.setColor(self.color)  # clear the texture to the window color
            GL.glClear(
                GL.GL_COLOR_BUFFER_BIT |
                GL.GL_DEPTH_BUFFER_BIT |
                GL.GL_STENCIL_BUFFER_BIT
            )

        # if self.sRGB:
        #    GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)

        if self._samples > 1:
            GL.glEnable(GL.GL_MULTISAMPLE)

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)

    def _updateTrackingState(self):
        """Update the tracking state and calculate new eye poses.

        The absolute display time is updated when called and used when computing
        new head, eye and hand poses.

        Returns
        -------
        None

        """
        # get the current frame time
        self._absTime = ovr.capi.getDisplayTime(self._frameIndex)

        # Get the current tracking state structure, estimated poses for the
        # head and hands are stored here. The latency marker for computing
        # motion-to-photon latency is set when this function is called.
        self._trackingState = ovr.capi.getTrackingState(self._absTime)

        # Store the current head pose from tracking state.
        self.headPose = self._trackingState.HeadPose.ThePose

        # Calculate eye poses, this needs to be called every frame, do this
        # after calling 'wait_to_begin_frame' to minimize the motion-to-photon
        # latency. This is called regardless if we are using the eye poses
        # returned by the function.
        self.eyePoses = ovr.capi.calcEyePoses(self._trackingState)

        # apply additional transformations to eye poses
        if not self._monoscopic:
            for eye in range(ovr.capi.ovrEye_Count):
                if self._headLocked:
                    self.eyePoses[eye] = \
                        self.hmdOriginPose * self.hmdToEyePoses[eye]
                else:
                    self.eyePoses[eye] = \
                        self.hmdOriginPose * self.eyePoses[eye]

                # compute each eye's transformation matrix from returned poses
                self._viewMatrix[eye] = \
                    ovr.capi.getEyeViewMatrix(self.eyePoses[eye])
        else:
            # view matrix derived from head position when in monoscopic mode
            if self._headLocked:
                self._viewMatrix = ovr.capi.getEyeViewMatrix(self.hmdOriginPose)
            else:
                self._viewMatrix = ovr.capi.getEyeViewMatrix(self.headPose)

        # get the poses for the touch controllers
        # NB - this does not work well when head locked, hands are not
        # transformed accordingly.
        self.handPoses = [
            self.hmdOriginPose * self._trackingState.HandPoses[0].ThePose,
            self.hmdOriginPose * self._trackingState.HandPoses[1].ThePose
        ]

    @property
    def absTime(self):
        """Get the absolute time for this frame."""
        return self._absTime

    @property
    def viewMatrix(self):
        """Get the view matrix for the current buffer."""
        if not self._monoscopic:
            return self._viewMatrix[self._bufferFlags[self.buffer]]
        else:
            return self._viewMatrix

    @property
    def projectionMatrix(self):
        """Get the projection matrix for the current buffer."""
        if not self._monoscopic:
            return self._projectionMatrix[self._bufferFlags[self.buffer]]
        else:
            return self._projectionMatrix

    @property
    def headLocked(self):
        """Enable/disable head locking."""
        return self._headLocked

    @headLocked.setter
    def headLocked(self, val):
        self._headLocked = bool(val)

    def pollControllers(self):
        """Update all connected controller states. This should be called at
        least once per frame.

        Returns
        -------
        None

        """
        for controller in ovr.capi.getConnectedControllerTypes():
            ovr.capi.pollController(controller)

    def _startHmdFrame(self):
        """Prepare to render an HMD frame. This must be called every frame
        before flipping or setting the view buffer.

        This function will wait until the HMD is ready to begin rendering before
        continuing. The current frame texture from the swap chain are pulled
        from the SDK and made available for binding.

        Returns
        -------
        None

        """
        # First time this function is called, make True.
        if not self._allowHmdRendering:
            self._allowHmdRendering = True

        # update session status
        self._sessionStatus = ovr.capi.getSessionStatus()

        # Wait for the buffer to be freed by the compositor, this is like
        # waiting for v-sync.
        ovr.capi.waitToBeginFrame(self._frameIndex)

        # update the tracking state
        self._updateTrackingState()

        # begin frame
        ovr.capi.beginFrame(self._frameIndex)

        # get the next available buffer texture in the swap chain
        self.frameTexture = \
            ovr.capi.getTextureSwapChainBufferGL(self._swapChain)

        # If mono mode, we want to configure the render framebuffer at this
        # point since 'setBuffer' will not be called.
        if self._monoscopic:
            self._prepareMonoFrame()

    def _startOfFlip(self):
        """Custom _startOfFlip for HMD rendering. This finalizes the HMD texture
        before diverting drawing operations back to the on-screen window. This
        allows 'flip()' to swap the on-screen and HMD buffers when called. This
        function always returns True.

        Returns
        -------
        True

        """
        # Switch off multi-sampling
        GL.glDisable(GL.GL_MULTISAMPLE)

        if self._allowHmdRendering:
            # resolve MSAA buffers
            self._resolveMSAA()

            # commit current texture buffer to the swap chain
            ovr.capi.commitSwapChain(self._swapChain)

            # Call end_frame and increment the frame index, no more rendering to
            # HMD's view texture at this point.
            ovr.capi.endFrame(self._frameIndex)
            self._frameIndex += 1

        # Set to None so the 'size' attribute returns the on-screen window
        # size.
        self.buffer = None

        # Make sure this is called after flipping, this updates VR information
        # and diverts rendering to the HMD texture.
        self.callOnFlip(self._startHmdFrame)

        # Poll controller states
        self.callOnFlip(self.pollControllers)

        # Call frame timing routines
        self.callOnFlip(self._updatePerformanceStats)

        # This always returns True
        return True

    def flip(self, clearBuffer=True):
        """Submit view buffer images to the HMD's compositor for display at next
        V-SYNC. This must be called every frame.

        Parameters
        ----------
        clearBuffer : boolean
            Clear the frame after flipping.

        Returns
        -------
        None

        """
        # NOTE: Most of this code is shared with the regular Window's flip
        # function for compatibility. We're only concerned with calling the
        # _startOfFlip function and drawing the mirror texture to the onscreen
        # window. Display timing functions are kept in for now, but they are not
        # active.
        #

        flipThisFrame = self._startOfFlip()
        if self.useFBO:
            if flipThisFrame:
                self._prepareFBOrender()
                # need blit the framebuffer object to the actual back buffer

                # unbind the framebuffer as the render target
                GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, 0)
                GL.glDisable(GL.GL_BLEND)
                stencilOn = GL.glIsEnabled(GL.GL_STENCIL_TEST)
                GL.glDisable(GL.GL_STENCIL_TEST)

                # blit mirror texture
                GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self._mirrorFbo)
                GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)

                GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
                # bind the rift's texture to the framebuffer
                GL.glFramebufferTexture2D(
                    GL.GL_READ_FRAMEBUFFER,
                    GL.GL_COLOR_ATTACHMENT0,
                    GL.GL_TEXTURE_2D, ovr.capi.getMirrorTexture(), 0)

                win_w, win_h = self.__dict__['size']
                tex_w, tex_h = self._mirrorRes

                GL.glViewport(0, 0, win_w, win_h)
                GL.glScissor(0, 0, win_w, win_h)
                GL.glClearColor(0.0, 0.0, 0.0, 1.0)
                GL.glClear(GL.GL_COLOR_BUFFER_BIT)
                GL.glBlitFramebuffer(0, 0, tex_w, tex_h,
                                     0, win_h, win_w, 0,  # flips texture
                                     GL.GL_COLOR_BUFFER_BIT,
                                     GL.GL_LINEAR)

                GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)
                GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
                self._finishFBOrender()

        # call this before flip() whether FBO was used or not
        self._afterFBOrender()

        self.backend.swapBuffers(flipThisFrame)

        if self.useFBO:
            if flipThisFrame:
                # set rendering back to the framebuffer object
                GL.glBindFramebufferEXT(
                    GL.GL_FRAMEBUFFER_EXT, self.frameBuffer)
                GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
                GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
                # set to no active rendering texture
                GL.glActiveTexture(GL.GL_TEXTURE0)
                GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
                if stencilOn:
                    GL.glEnable(GL.GL_STENCIL_TEST)

        # rescale, reposition, & rotate
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        if self.viewScale is not None:
            GL.glScalef(self.viewScale[0], self.viewScale[1], 1)
            absScaleX = abs(self.viewScale[0])
            absScaleY = abs(self.viewScale[1])
        else:
            absScaleX, absScaleY = 1, 1

        if self.viewPos is not None:
            # here we must use normalised units in _viewPosNorm,
            # see the corresponding attributeSetter above
            normRfPosX = self._viewPosNorm[0] / absScaleX
            normRfPosY = self._viewPosNorm[1] / absScaleY

            GL.glTranslatef(normRfPosX, normRfPosY, 0.0)

        if self.viewOri:  # float
            # the logic below for flip is partially correct, but does not
            # handle a nonzero viewPos
            flip = 1
            if self.viewScale is not None:
                _f = self.viewScale[0] * self.viewScale[1]
                if _f < 0:
                    flip = -1
            GL.glRotatef(flip * self.viewOri, 0.0, 0.0, -1.0)

        # reset returned buffer for next frame
        self._endOfFlip(clearBuffer)

        # waitBlanking
        if self.waitBlanking and flipThisFrame:
            GL.glBegin(GL.GL_POINTS)
            GL.glColor4f(0, 0, 0, 0)
            if sys.platform == 'win32' and self.glVendor.startswith('ati'):
                pass
            else:
                # this corrupts text rendering on win with some ATI cards :-(
                GL.glVertex2i(10, 10)
            GL.glEnd()
            GL.glFinish()

        # get timestamp
        now = logging.defaultClock.getTime()

        # run other functions immediately after flip completes
        for callEntry in self._toCall:
            callEntry['function'](*callEntry['args'], **callEntry['kwargs'])
        del self._toCall[:]

        # do bookkeeping
        if self.recordFrameIntervals:
            self.frames += 1
            deltaT = now - self.lastFrameT
            self.lastFrameT = now
            if self.recordFrameIntervalsJustTurnedOn:  # don't do anything
                self.recordFrameIntervalsJustTurnedOn = False
            else:  # past the first frame since turned on
                self.frameIntervals.append(deltaT)
                if deltaT > self.refreshThreshold:
                    self.nDroppedFrames += 1
                    if self.nDroppedFrames < reportNDroppedFrames:
                        txt = 't of last frame was %.2fms (=1/%i)'
                        msg = txt % (deltaT * 1000, 1 / deltaT)
                        logging.warning(msg, t=now)
                    elif self.nDroppedFrames == reportNDroppedFrames:
                        logging.warning("Multiple dropped frames have "
                                        "occurred - I'll stop bothering you "
                                        "about them!")

        # log events
        for logEntry in self._toLog:
            # {'msg':msg, 'level':level, 'obj':copy.copy(obj)}
            logging.log(msg=logEntry['msg'],
                        level=logEntry['level'],
                        t=now,
                        obj=logEntry['obj'])
        del self._toLog[:]

        # keep the system awake (prevent screen-saver or sleep)
        platform_specific.sendStayAwake()

        #    If self.waitBlanking is True, then return the time that
        # GL.glFinish() returned, set as the 'now' variable. Otherwise
        # return None as before
        #
        if self.waitBlanking is True:
            return now

    def multiplyViewMatrixGL(self):
        """Multiply the local eye pose transformation matrix obtained from the
        SDK using glMultMatrixf(). The matrix used depends on the current eye
        buffer set by 'setBuffer()'.

        Returns
        -------
        None

        """
        if not self._legacyOpenGL:
            return

        if not self._monoscopic:
            if self.buffer == 'left':
                GL.glMultMatrixf(
                    self._viewMatrix[0].ctypes)
            elif self.buffer == 'right':
                GL.glMultMatrixf(
                    self._viewMatrix[1].ctypes)
        else:
            GL.glMultMatrixf(
                self._viewMatrix.ctypes)

    def multiplyProjectionMatrixGL(self):
        """Multiply the current projection matrix obtained from the SDK using
        glMultMatrixf(). The matrix used depends on the current eye buffer set
        by 'setBuffer()'.

        Returns
        -------
        None

        """
        if not self._legacyOpenGL:
            return

        if not self._monoscopic:
            if self.buffer == 'left':
                GL.glMultMatrixf(
                    self._projectionMatrix[0].ctypes)
            elif self.buffer == 'right':
                GL.glMultMatrixf(
                    self._projectionMatrix[1].ctypes)
        else:
            GL.glMultMatrixf(
                self._projectionMatrix.ctypes)

    def setRiftView(self, clearDepth=True):
        """Set head-mounted display view. Gets the projection and view matrices
        from the HMD and applies them.

        Note: This only has an effect if using Rift in legacy immediate mode
        OpenGL mode by setting ~Rift.legacy_opengl=True.

        Parameters
        ----------
        clearDepth : boolean
            Clear the depth buffer prior after configuring the view parameters.

        Returns
        -------
        None

        """
        if self._legacyOpenGL:
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            self.multiplyProjectionMatrixGL()

            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            self.multiplyViewMatrixGL()

        if clearDepth:
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    def setDefaultView(self, clearDepth=True):
        """Return to default projection. Call this before drawing PsychoPy's
        2D stimuli after a stereo projection change.

        Note: This only has an effect if using Rift in legacy immediate mode
        OpenGL mode by setting ~Rift.legacy_opengl=True.

        Parameters
        ----------
        clearDepth : boolean
            Clear the depth buffer prior after configuring the view parameters.

        Returns
        -------
        None

        """
        if self._legacyOpenGL:
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glOrtho(-1, 1, -1, 1, -1, 1)
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()

        if clearDepth:
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    def _updateProjectionMatrix(self):
        """Update or re-calculate projection matrices based on the current
        render descriptor configuration.

        Returns
        -------
        None

        """
        if not self._monoscopic:
            self._projectionMatrix[0] = ovr.capi.getEyeProjectionMatrix(
                0, self._nearClip, self._farClip)
            self._projectionMatrix[1] = ovr.capi.getEyeProjectionMatrix(
                1, self._nearClip, self._farClip)
        else:
            self._projectionMatrix = ovr.capi.getEyeProjectionMatrix(
                0, self._nearClip, self._farClip)

    def controllerConnected(self, controller='xbox'):
        """Check if a given device is connected to the Haptics engine.

        Parameters
        ----------
        controller : str
            Name of the controller to check if connected.

        Returns
        -------
        boolean
            True if specified controller connected, else False.

        """
        query_result = ovr.capi.getConnectedControllerTypes()
        return controller in query_result

    def getConectedControllers(self):
        """Get a list of connected input devices (controllers) managed by the
        LibOVR runtime. Valid names are 'xbox', 'remote', 'left_touch',
        'right_touch' and 'touch'.

        Returns
        -------
        list
            List of connected controller names.

        """
        return ovr.capi.getConnectedControllerTypes()

    def getThumbstickValues(self, controller='xbox', deadzone=False):
        """Get a list of tuples containing the displacement values (with
        deadzone) for each thumbstick on a specified controller.

        Axis displacements are represented in each tuple by a floats ranging
        from -1.0 (full left/down) to 1.0 (full right/up). The SDK library
        pre-filters stick input to apply a dead-zone where 0.0 will be returned
        if the sticks return a displacement within -0.2746 to 0.2746. Index 0 of
        the returned tuple contains the X,Y displacement values of the left
        thumbstick, and the right thumbstick values at index 1.

        Possible values for 'controller' are 'xbox' and 'touch'; the only
        devices with thumbsticks the SDK manages.

        Parameters
        ----------
        controller : str
            Name of the controller to get thumbstick values.
        deadzone : bool
            Apply the deadzone to thumbstick values.

        Returns
        -------
        tuple
            Left and right, X and Y thumbstick values.

        """
        if controller not in ("xbox", "touch"):
            raise (
                "Invalid controller value '{}' specified.".format(controller))

        return ovr.capi.getThumbstickValues(controller, deadzone)

    def getIndexTriggerValues(self, controller='xbox', deadzone=False):
        """Get the values of the index triggers representing the amount they
        are being displaced.

        Parameters
        ----------
        controller : str
            Name of the controller to get index trigger values.
        deadzone : bool
            Apply the deadzone to index trigger values.

        Returns
        -------
        tuple
            Left and right index trigger values.

        """
        if controller not in ("xbox", "touch"):
            raise (
                "Invalid controller value '{}' specified.".format(controller))

        return ovr.capi.getIndexTriggerValues(controller, deadzone)

    def getHandTriggerValues(self, controller='xbox', deadzone=False):
        """Get the values of the hand triggers representing the amount they
        are being displaced.

        Parameters
        ----------
        controller : str
            Name of the controller to get hand trigger values.
        deadzone : bool
            Apply the deadzone to hand trigger values.

        Returns
        -------
        tuple
            Left and right index trigger values.


        """
        if controller not in ("xbox", "touch"):
            raise (
                "Invalid controller value '{}' specified.".format(controller))

        return ovr.capi.getHandTriggerValues(controller, deadzone)

    def getButtons(
            self, buttonNames, controller='xbox', edgeTrigger='continuous'):
        """Returns True if any of the buttons in button_list are held down. All
        buttons are ORed together and tested. Edge triggering can be enabled by
        specifying either 'rising' or 'falling' to edge_trigger. When enabled,
        True is returned only when a button's state changes. If button_list is
        empty, will return True when no buttons are pressed.

        Valid button values are 'A', 'B', 'RThumb', 'X', 'Y', 'LThumb', 
        'LShoulder', 'Up', 'Down', 'Left', 'Right', 'Enter', 'Back', 'VolUp',
        'VolDown', 'Home', 'RMask' and 'LMask'.

        Returns
        -------
        bool

        Examples
        --------
        # check if the 'Enter' button on the Oculus remote was released
        isPressed = getButtons(['Enter'], 'remote', 'falling')

        """
        return ovr.capi.getButtons(controller, buttonNames, edgeTrigger)

    def getTouches(self, touchNames, edgeTrigger='continuous'):
        """Returns True if any buttons are touched using sensors. This feature
        is used to estimate finger poses and can be used to read gestures. An
        example of a possible use case is a pointing task, where responses are
        only valid if the user's index finger is extended away from the index
        trigger button.

        Currently, this feature is only available with the Oculus Touch
        controllers.

        Returns
        -------
        None

        """
        return ovr.capi.getTouches('touch', touchNames, edgeTrigger)

    def isIndexPointing(self, hand='right'):
        """Check if the user is doing a pointing gesture with the given hand, or
        if the index finger is not touching the controller. Only applicable when
        using Oculus Touch controllers.

        Returns
        -------
        None

        """
        if hand == 'right':
            return ovr.capi.getTouches('touch', 'RIndexPointing')
        elif hand == 'left':
            return ovr.capi.getTouches('touch', 'LIndexPointing')
        else:
            raise RuntimeError("Invalid hand '{}' specified.".format(hand))

    def isThumbUp(self, hand='right'):
        """Check if the user's thumb is pointing upwards with a given hand, or
        if not touching the controller. Only applicable when using Oculus Touch
        controllers.

        Returns
        -------
        None

        """
        if hand == 'right':
            return ovr.capi.getTouches('touch', 'RThumbUp')
        elif hand == 'left':
            return ovr.capi.getTouches('touch', 'RThumbUp')
        else:
            raise RuntimeError("Invalid hand '{}' specified.".format(hand))

    def raycastSphere(self,
                      originPose,
                      targetPose,
                      targetRadius=0.5,
                      rayDirection=None,
                      maxRange=None):
        """Project an invisible ray of finite or infinite length from the
        originPose in rayDirection and check if it intersects with the
        targetPose bounding sphere.

        Specifying maxRange as >0.0 casts a ray of finite length in world
        units. The distance between the target and ray origin position are
        checked prior to casting the ray; automatically failing if the ray can
        never reach the edge of the bounding sphere centered about targetPose.
        This avoids having to do the costly transformations required for
        picking.

        This raycast implementation can only determine if contact is being made
        with the object's bounding sphere, not where on the object the ray
        intersects. This method might not work for irregular or elongated
        objects since bounding spheres may not approximate those shapes well. In
        such cases, one may use multiple spheres at different locations and
        radii to pick the same object.

        Parameters
        ----------
        originPose :obj:`ovrPosef`
            Origin pose of the ray.
        targetPose :obj:`ovrPosef` or :obj:`ovrVector3f'
            Pose of the target.
        targetRadius :obj:`float`
            The radius of the target.
        rayDirection :obj:`ovrVector3f`
            Vector indicating the direction for the ray. If None is specified,
            then -Z is used.
        maxRange
            The maximum range of the ray. Ray testing will fail automatically if
            the target is out of range. The ray has infinite length if None is
            specified.

        Returns
        -------
        bool
            True if the ray intersects anywhere on the bounding sphere, False in
            every other condition.

        Examples
        --------
        # raycast from the head pose to a target
        headPose = hmd.headPose
        targetPos = rift.math.ovrVector3f(0.0, 0.0, -5.0)  # 5 meters front
        isLooking = hmd.raycast(headPose, targetPos)

        # now with touch controller positions
        rightHandPose = hmd.getHandPose(1)  # 1 = right hand
        fingerLength = 0.10  # 10 cm
        pointing = hmd.raycast(rightHandPose, targetPos, maxRange=fingerLength)

        """
        # convert a pose to a vector
        if isinstance(targetPose, ovr.math.ovrPosef):
            targetPose = targetPose.translation

        # if no ray direction is specified, create one to define forward (-Z)
        if rayDirection is None:
            rayDirection = ovr.math.ovrVector3f(0.0, 0.0, -1.0)

        # apply origin offset
        originPose = originPose * self.hmdOriginPose

        # check if we can touch the sphere with a finite ray
        if maxRange is not None:
            targetDistance = targetPose.distance(
                originPose.translation) - targetRadius
            if targetDistance > maxRange:
                return False

        # put the target in the caster's local coordinate system
        offset = -originPose.inverseTransform(targetPose)

        # find the discriminant
        desc = math.pow(rayDirection.dot(offset), 2.0) - \
               (offset.dot(offset) - math.pow(targetRadius, 2.0))

        # one or more roots? if so we are touching the sphere
        return desc >= 0.0

    def _updatePerformanceStats(self):
        """Run profiling routines. This just reports if the application drops a
        frame. Nothing too fancy yet.

        Returns
        -------

        """
        # get timestamp
        now = logging.defaultClock.getTime()

        # don't profile if nothing is on the HMD
        if not self._sessionStatus.IsVisible or not self.warnAppFrameDropped:
            return

        # update performance data
        self._perfStatsLastFrame = self._perfStatsThisFrame
        self._perfStatsThisFrame = ovr.capi.getFrameStats()

        # check if a frame missed it's deadline
        dropLast = self._perfStatsLastFrame.FrameStats[0].AppDroppedFrameCount
        dropNow = self._perfStatsThisFrame.FrameStats[0].AppDroppedFrameCount

        if dropNow > dropLast:
            self.nDroppedFrames += 1
            if self.nDroppedFrames < reportNDroppedFrames:
                txt = 'LibOVR reported frame dropped by application'
                logging.warning(txt, t=now)
            elif self.nDroppedFrames == reportNDroppedFrames:
                logging.warning("Multiple dropped frames have "
                                "occurred - I'll stop bothering you "
                                "about them!")
