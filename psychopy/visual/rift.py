#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Oculus Rift HMD support for PsychoPy.

Copyright (C) 2019 - Matthew D. Cutone, The Centre for Vision Research, Toronto,
Ontario, Canada

Uses PsychXR to interface with the Oculus Rift runtime (LibOVR) and SDK. See
http://psychxr.org for more information. The Oculus PC SDK is Copyright (c)
Facebook Technologies, LLC and its affiliates. All rights reserved.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Rift']

# ----------
# Initialize
# ----------

# Check if they system has PsychXR installed and is importable. If not, this
# module will still load, but the `Rift` class will fail to load. This allows
# the Rift library to be lazy-loaded on systems without PsychXR.
#
_HAS_PSYCHXR_ = True

try:
    import psychxr.drivers.libovr as libovr
except ImportError:
    _HAS_PSYCHXR_ = False

# -------
# Imports
# -------

import warnings
import platform
import ctypes
import numpy as np
import pyglet.gl as GL
from psychopy.visual import window
from psychopy.hardware.base import DeviceNotConnectedError
from psychopy import platform_specific, logging, core
from psychopy.tools.attributetools import setAttribute

try:
    from PIL import Image
except ImportError:
    import Image

reportNDroppedFrames = 5

# -------------------------------------------
# Look-up tables for PsychXR/LibOVR constants
#

if _HAS_PSYCHXR_:
    # Controller types supported by PsychXR
    RIFT_CONTROLLER_TYPES = {
        'Xbox': libovr.CONTROLLER_TYPE_XBOX,
        'Remote': libovr.CONTROLLER_TYPE_REMOTE,
        'Touch': libovr.CONTROLLER_TYPE_TOUCH,
        'LeftTouch': libovr.CONTROLLER_TYPE_LTOUCH,
        'RightTouch': libovr.CONTROLLER_TYPE_RTOUCH,
        'Object0': libovr.CONTROLLER_TYPE_OBJECT0,
        'Object1': libovr.CONTROLLER_TYPE_OBJECT1,
        'Object2': libovr.CONTROLLER_TYPE_OBJECT2,
        'Object3': libovr.CONTROLLER_TYPE_OBJECT3,
        libovr.CONTROLLER_TYPE_XBOX: 'Xbox',
        libovr.CONTROLLER_TYPE_REMOTE: 'Remote',
        libovr.CONTROLLER_TYPE_TOUCH: 'Touch',
        libovr.CONTROLLER_TYPE_LTOUCH: 'LeftTouch',
        libovr.CONTROLLER_TYPE_RTOUCH: 'RightTouch',
        libovr.CONTROLLER_TYPE_OBJECT0: 'Object0',
        libovr.CONTROLLER_TYPE_OBJECT1: 'Object1',
        libovr.CONTROLLER_TYPE_OBJECT2: 'Object2',
        libovr.CONTROLLER_TYPE_OBJECT3: 'Object3'
    }

    # Button types supported by PsychXR
    RIFT_BUTTON_TYPES = {
        "A": libovr.BUTTON_A,
        "B": libovr.BUTTON_B,
        "RThumb": libovr.BUTTON_RTHUMB,
        "RShoulder": libovr.BUTTON_RSHOULDER,
        "X": libovr.BUTTON_X,
        "Y": libovr.BUTTON_Y,
        "LThumb": libovr.BUTTON_LTHUMB,
        "LShoulder": libovr.BUTTON_LSHOULDER,
        "Up": libovr.BUTTON_UP,
        "Down": libovr.BUTTON_DOWN,
        "Left": libovr.BUTTON_LEFT,
        "Right": libovr.BUTTON_RIGHT,
        "Enter": libovr.BUTTON_ENTER,
        "Back": libovr.BUTTON_BACK,
        "VolUp": libovr.BUTTON_VOLUP,
        "VolDown": libovr.BUTTON_VOLDOWN,
        "Home": libovr.BUTTON_HOME,
    }

    # Touch types supported by PsychXR
    RIFT_TOUCH_TYPES = {
        "A": libovr.TOUCH_A,
        "B": libovr.TOUCH_B,
        "RThumb": libovr.TOUCH_RTHUMB,
        "RThumbRest": libovr.TOUCH_RTHUMBREST,
        "RThumbUp": libovr.TOUCH_RTHUMBUP,
        "RIndexPointing": libovr.TOUCH_RINDEXPOINTING,
        "X": libovr.TOUCH_X,
        "Y": libovr.TOUCH_Y,
        "LThumb": libovr.TOUCH_LTHUMB,
        "LThumbRest": libovr.TOUCH_LTHUMBREST,
        "LThumbUp": libovr.TOUCH_LTHUMBUP,
        "LIndexPointing": libovr.TOUCH_LINDEXPOINTING
    }

    # Tracked device identifiers
    RIFT_TRACKED_DEVICE_TYPES = {
        "HMD": libovr.TRACKED_DEVICE_TYPE_HMD,
        "LTouch": libovr.TRACKED_DEVICE_TYPE_LTOUCH,
        "RTouch": libovr.TRACKED_DEVICE_TYPE_RTOUCH,
        "Touch": libovr.TRACKED_DEVICE_TYPE_TOUCH,
        "Object0": libovr.TRACKED_DEVICE_TYPE_OBJECT0,
        "Object1": libovr.TRACKED_DEVICE_TYPE_OBJECT1,
        "Object2": libovr.TRACKED_DEVICE_TYPE_OBJECT2,
        "Object3": libovr.TRACKED_DEVICE_TYPE_OBJECT3
    }

    # Tracking origin types
    RIFT_TRACKING_ORIGIN_TYPE = {
        "floor": libovr.TRACKING_ORIGIN_FLOOR_LEVEL,
        "eye": libovr.TRACKING_ORIGIN_EYE_LEVEL
    }

    # Performance hud modes
    RIFT_PERF_HUD_MODES = {
        'PerfSummary': libovr.PERF_HUD_PERF_SUMMARY,
        'LatencyTiming': libovr.PERF_HUD_LATENCY_TIMING,
        'AppRenderTiming': libovr.PERF_HUD_APP_RENDER_TIMING,
        'CompRenderTiming': libovr.PERF_HUD_COMP_RENDER_TIMING,
        'AswStats': libovr.PERF_HUD_ASW_STATS,
        'VersionInfo': libovr.PERF_HUD_VERSION_INFO,
        'Off': libovr.PERF_HUD_OFF
    }

    # stereo debug hud modes
    RIFT_STEREO_DEBUG_HUD_MODES = {
        'Off': libovr.DEBUG_HUD_STEREO_MODE_OFF,
        'Quad': libovr.DEBUG_HUD_STEREO_MODE_QUAD,
        'QuadWithCrosshair': libovr.DEBUG_HUD_STEREO_MODE_QUAD_WITH_CROSSHAIR,
        'CrosshairAtInfinity': libovr.DEBUG_HUD_STEREO_MODE_CROSSHAIR_AT_INFINITY
    }

    # Boundary types
    RIFT_BOUNDARY_TYPE = {
        'PlayArea': libovr.BOUNDARY_PLAY_AREA,
        'Outer': libovr.BOUNDARY_OUTER
    }

    # mirror modes
    RIFT_MIRROR_MODES = {
        'left': libovr.MIRROR_OPTION_LEFT_EYE_ONLY,
        'right': libovr.MIRROR_OPTION_RIGHT_EYE_ONLY,
        'distortion': libovr.MIRROR_OPTION_POST_DISTORTION,
        'default': libovr.MIRROR_OPTION_DEFAULT
    }

    # eye types
    RIFT_EYE_TYPE = {'left': libovr.EYE_LEFT, 'right': libovr.EYE_RIGHT}


# ------------------------------------------------------------------------------
# LibOVR Error Handler
#
# Exceptions raised by LibOVR will wrapped with this Python exception. This will
# display the error string passed from LibOVR.
#

class LibOVRError(Exception):
    """Exception for LibOVR errors."""
    pass


class Rift(window.Window):
    """Class provides a display and peripheral interface for the Oculus Rift
    (see: https://www.oculus.com/) head-mounted display. This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.rift import Rift` when inheriting from it.


    Requires PsychXR 0.2.4 to be installed. Setting the `winType='glfw'` is
    preferred for VR applications.

    """
    def __init__(
            self,
            fovType='recommended',
            trackingOriginType='floor',
            texelsPerPixel=1.0,
            headLocked=False,
            highQuality=True,
            monoscopic=False,
            samples=1,
            mirrorMode='default',
            mirrorRes=None,
            warnAppFrameDropped=True,
            autoUpdateInput=True,
            legacyOpenGL=True,
            *args,
            **kwargs):
        """
        Parameters
        ----------
        fovType : str
            Field-of-view (FOV) configuration type. Using 'recommended'
            auto-configures the FOV using the recommended parameters computed by
            the runtime. Using 'symmetric' forces a symmetric FOV using optimal
            parameters from the SDK, this mode is required for displaying 2D
            stimuli. Specifying 'max' will use the maximum FOVs supported by the
            HMD.
        trackingOriginType : str
            Specify the HMD origin type. If 'floor', the height of the user
            is added to the head tracker by LibOVR.
        texelsPerPixel : float
            Texture pixels per display pixel at FOV center. A value of 1.0
            results in 1:1 mapping. A fractional value results in a lower
            resolution draw buffer which may increase performance.
        headLocked : bool
            Lock the compositor render layer in-place, disabling Asynchronous
            Space Warp (ASW). Enable this if you plan on computing eye poses
            using custom or modified head poses.
        highQuality : bool
            Configure the compositor to use anisotropic texture sampling (4x).
            This reduces aliasing artifacts resulting from high frequency
            details particularly in the periphery.
        nearClip, farClip : float
            Location of the near and far clipping plane in GL units (meters by
            default) from the viewer. These values can be updated after
            initialization.
        monoscopic : bool
            Enable monoscopic rendering mode which presents the same image to
            both eyes. Eye poses used will be both centered at the HMD origin.
            Monoscopic mode uses a separate rendering pipeline which reduces
            VRAM usage. When in monoscopic mode, you do not need to call
            'setBuffer' prior to rendering (doing so will do have no effect).
        samples : int or str
            Specify the number of samples for multi-sample anti-aliasing (MSAA).
            When >1, multi-sampling logic is enabled in the rendering pipeline.
            If 'max' is specified, the largest number of samples supported by
            the platform is used. If floating point textures are used, MSAA
            sampling is disabled. Must be power of two value.
        mirrorMode : str
            On-screen mirror mode. Values 'left' and 'right' show rectilinear
            images of a single eye. Value 'distortion` shows the post-distortion
            image after being processed by the compositor. Value 'default'
            displays rectilinear images of both eyes side-by-side.
        mirrorRes : list of int
            Resolution of the mirror texture. If `None`, the resolution will
            match the window size. The value of `mirrorRes` is used for to
            define the resolution of movie frames.
        warnAppFrameDropped : bool
            Log a warning if the application drops a frame. This occurs when
            the application fails to submit a frame to the compositor on-time.
            Application frame drops can have many causes, such as running
            routines in your application loop that take too long to complete.
            However, frame drops can happen sporadically due to driver bugs and
            running background processes (such as Windows Update). Use the
            performance HUD to help diagnose the causes of frame drops.
        autoUpdateInput : bool
            Automatically update controller input states at the start of each
            frame. If `False`, you must manually call `updateInputState` before
            getting input values from `LibOVR` managed input devices.
        legacyOpenGL : bool
            Disable 'immediate mode' OpenGL calls in the rendering pipeline.
            Specifying False maintains compatibility with existing PsychoPy
            stimuli drawing routines. Use True when computing transformations
            using some other method and supplying shaders matrices directly.

        """
        if not _HAS_PSYCHXR_:
            raise ModuleNotFoundError(
                "PsychXR must be installed to use the `Rift` class. Exiting.")

        self._closed = False
        self._legacyOpenGL = legacyOpenGL
        self._monoscopic = monoscopic
        self._texelsPerPixel = texelsPerPixel
        self._headLocked = headLocked
        self._highQuality = highQuality

        self._samples = samples
        self._mirrorRes = mirrorRes
        self._mirrorMode = mirrorMode

        self.autoUpdateInput = autoUpdateInput

        # performance statistics
        # this can be changed while running
        self.warnAppFrameDropped = warnAppFrameDropped

        # check if we are using Windows
        if platform.system() != 'Windows':
            raise RuntimeError("`Rift` class only supports Windows OS at this " +
                               "time, exiting.")

        # check if we are using 64-bit Python
        if platform.architecture()[0] != '64bit':  # sys.maxsize != 2**64
            raise RuntimeError("`Rift` class only supports 64-bit Python, " +
                               "exiting.")

        # check if the background service is running and an HMD is connected
        if not libovr.isOculusServiceRunning():
            raise RuntimeError("HMD service is not available or started, " +
                               "exiting.")

        if not libovr.isHmdConnected():
            raise DeviceNotConnectedError(
                "Cannot find any connected HMD, check connections and try again.",
                deviceClass=Rift
            )

        # create a VR session, do some initial configuration
        initResult = libovr.initialize()  # removed logging callback
        if libovr.failure(initResult):
            _, msg = libovr.getLastErrorInfo()
            raise LibOVRError(msg)

        if libovr.failure(libovr.create()):
            libovr.shutdown()  # shutdown the session
            _, msg = libovr.getLastErrorInfo()
            raise LibOVRError(msg)

        if libovr.failure(libovr.resetPerfStats()):
            logging.warn('Failed to reset performance stats.')

        self._perfStats = libovr.getPerfStats()
        self._lastAppDroppedFrameCount = 0

        # update session status object
        _, status = libovr.getSessionStatus()
        self._sessionStatus = status

        # get HMD information
        self._hmdInfo = libovr.getHmdInfo()

        # configure the internal render descriptors based on the requested
        # viewing parameters.
        if fovType == 'symmetric' or self._monoscopic:
            # Use symmetric FOVs for cases where off-center frustums are not
            # desired. This is required for monoscopic rendering to permit
            # comfortable binocular fusion.
            eyeFovs = self._hmdInfo.symmetricEyeFov
            logging.info('Using symmetric eye FOVs.')
        elif fovType == 'recommended' or fovType == 'default':
            # use the recommended FOVs, these have wider FOVs looking outward
            # due to off-center frustums.
            eyeFovs = self._hmdInfo.defaultEyeFov
            logging.info('Using default/recommended eye FOVs.')
        elif fovType == 'max':
            # the maximum FOVs for the HMD supports
            eyeFovs = self._hmdInfo.maxEyeFov
            logging.info('Using maximum eye FOVs.')
        else:
            raise ValueError(
                "Invalid FOV type '{}' specified.".format(fovType))

        # pass the FOVs to PsychXR
        for eye, fov in enumerate(eyeFovs):
            libovr.setEyeRenderFov(eye, fov)

        libovr.setHeadLocked(headLocked)  # enable head locked mode
        libovr.setHighQuality(highQuality)  # enable high quality mode

        # Compute texture sizes for render buffers, these are reported by the
        # LibOVR SDK based on the FOV settings specified above.
        texSizeLeft = libovr.calcEyeBufferSize(libovr.EYE_LEFT)
        texSizeRight = libovr.calcEyeBufferSize(libovr.EYE_RIGHT)

        # we are using a shared texture, so we need to combine dimensions
        if not self._monoscopic:
            hmdBufferWidth = texSizeLeft[0] + texSizeRight[0]
        else:
            hmdBufferWidth = max(texSizeLeft[0], texSizeRight[0])

        hmdBufferHeight = max(texSizeLeft[1], texSizeRight[1])

        # buffer viewport size
        self._hmdBufferSize = hmdBufferWidth, hmdBufferHeight
        logging.debug(
            'Required HMD buffer size is {}x{}.'.format(*self._hmdBufferSize))

        # Calculate the swap texture size. These can differ in later
        # configurations, right now they are the same.
        self._swapTextureSize = self._hmdBufferSize

        # Compute the required viewport parameters for the given buffer and
        # texture sizes. If we are using a power of two texture, we need to
        # centre the viewports on the textures.
        if not self._monoscopic:
            leftViewport = (0, 0, texSizeLeft[0], texSizeLeft[1])
            rightViewport = (texSizeLeft[0], 0, texSizeRight[0], texSizeRight[1])
        else:
            # In mono mode, we use the same viewport for both eyes. Therefore,
            # the swap texture only needs to be half as wide. This save VRAM
            # and does not require buffer changes when rendering.
            leftViewport = (0, 0, texSizeLeft[0], texSizeLeft[1])
            rightViewport = (0, 0, texSizeRight[0], texSizeRight[1])

        libovr.setEyeRenderViewport(libovr.EYE_LEFT, leftViewport)
        logging.debug(
            'Set left eye viewport to: x={}, y={}, w={}, h={}.'.format(
                *leftViewport))

        libovr.setEyeRenderViewport(libovr.EYE_RIGHT, rightViewport)
        logging.debug(
            'Set right eye viewport to: x={}, y={}, w={}, h={}.'.format(
                *rightViewport))

        self.scrWidthPIX = max(texSizeLeft[0], texSizeRight[0])

        # frame index
        self._frameIndex = 0

        # setup a mirror texture
        self._mirrorRes = mirrorRes

        # view buffer to divert operations to, if None, drawing is sent to the
        # on-screen window.
        self.buffer = None

        # View matrices, these are updated every frame based on computed head
        # position. Projection matrices need only to be computed once.
        if not self._monoscopic:
            self._projectionMatrix = [
                np.identity(4, dtype=np.float32),
                np.identity(4, dtype=np.float32)]
            self._viewMatrix = [
                np.identity(4, dtype=np.float32),
                np.identity(4, dtype=np.float32)]
        else:
            self._projectionMatrix = np.identity(4, dtype=np.float32)
            self._viewMatrix = np.identity(4, dtype=np.float32)

        # disable v-sync since the HMD runs at a different frequency
        kwargs['waitBlanking'] = False

        # force checkTiming and quad-buffer stereo off
        kwargs["checkTiming"] = False  # not used here for now
        kwargs["stereo"] = False  # false, using our own stuff for stereo
        kwargs['useFBO'] = True  # true, but uses it's ow FBO logic
        kwargs['multiSample'] = False  # not for the back buffer of the widow

        # do not allow 'endFrame' to be called until _startOfFlip is called
        self._allowHmdRendering = False

        # VR pose data, updated every frame
        self._headPose = libovr.LibOVRPose()

        # set the tracking origin type
        self.trackingOriginType = trackingOriginType

        # performance information
        self.nDroppedFrames = 0
        self.controllerPollTimes = {}

        # call up a new window object
        super(Rift, self).__init__(*args, **kwargs)

        self._updateProjectionMatrix()

    def close(self):
        """Close the window and cleanly shutdown the LibOVR session.
        """
        logging.info('Closing `Rift` window, de-allocating resources and '
                     'shutting down VR session.')

        # switch off persistent HUD features
        self.perfHudMode = 'Off'
        self.stereoDebugHudMode = 'Off'

        # clean up allocated LibOVR resources before closing the window
        logging.debug('Destroying mirror texture.')
        libovr.destroyMirrorTexture()
        logging.debug('Destroying texture GL swap chain.')
        libovr.destroyTextureSwapChain(libovr.TEXTURE_SWAP_CHAIN0)
        logging.debug('Destroying LibOVR session.')
        libovr.destroy()

        # start closing the window
        self._closed = True
        logging.debug('Closing window associated with LibOVR session.')
        self.backend.close()

        try:
            core.openWindows.remove(self)
        except Exception:
            pass

        try:
            self.mouseVisible = True
        except Exception:
            pass

        # shutdown the session completely
        #libovr.shutdown()
        logging.info('LibOVR session shutdown cleanly.')

        try:
            logging.flush()
        except Exception:
            pass

    @property
    def size(self):
        """Size property to get the dimensions of the view buffer instead of
        the window. If there are no view buffers, always return the dims of the
        window.

        """
        # this is a hack to get stimuli to draw correctly
        if self.buffer is None:
            return self.frameBufferSize
        else:
            if self._monoscopic:
                return np.array(
                    (self._hmdBufferSize[0], self._hmdBufferSize[1]),
                    int)
            else:
                return np.array(
                    (int(self._hmdBufferSize[0] / 2), self._hmdBufferSize[1]),
                    int)

    @size.setter
    def size(self, value):
        """Set the size of the window.

        """
        self.__dict__['size'] = np.array(value, int)

    def setSize(self, value, log=True):
        setAttribute(self, 'size', value, log=log)

    def perfHudMode(self, mode='Off'):
        """Set the performance HUD mode.

        Parameters
        ----------
        mode : str
            HUD mode to use.

        """
        result = libovr.setInt(libovr.PERF_HUD_MODE, RIFT_PERF_HUD_MODES[mode])
        if libovr.success(result):
            logging.info("Performance HUD mode set to '{}'.".format(mode))
        else:
            logging.error('Failed to set performance HUD mode to "{}".'.format(
                mode))

    def hidePerfHud(self):
        """Hide the performance HUD."""
        libovr.setInt(libovr.PERF_HUD_MODE, libovr.PERF_HUD_OFF)
        logging.info('Performance HUD disabled.')

    def stereoDebugHudMode(self, mode):
        """Set the debug stereo HUD mode.

        This makes the compositor add stereoscopic reference guides to the
        scene. You can configure the HUD can be configured using other methods.

        Parameters
        ----------
        mode : str
            Stereo debug mode to use. Valid options are `Off`, `Quad`,
            `QuadWithCrosshair`, and `CrosshairAtInfinity`.

        Examples
        --------
        Enable a stereo debugging guide::

            hmd.stereoDebugHudMode('CrosshairAtInfinity')

        Hide the debugging guide. Should be called before exiting the
        application since it's persistent until the Oculus service is
        restarted::

            hmd.stereoDebugHudMode('Off')

        """
        result = libovr.setInt(
            libovr.DEBUG_HUD_STEREO_MODE, RIFT_STEREO_DEBUG_HUD_MODES[mode])

        if result:
            logging.info("Stereo debug HUD mode set to '{}'.".format(mode))
        else:
            logging.warning(
                "Failed to set stereo debug HUD mode set to '{}'.".format(mode))

    def setStereoDebugHudOption(self, option, value):
        """Configure stereo debug HUD guides.

        Parameters
        ----------
        option : str
            Option to set. Valid options are `InfoEnable`, `Size`, `Position`,
            `YawPitchRoll`, and `Color`.
        value : array_like or bool
            Value to set for a given `option`. Appropriate types for each
            option are:

            * `InfoEnable` - bool, `True` to show, `False` to hide.
            * `Size` - array_like, [w, h] in meters.
            * `Position` - array_like, [x, y, z] in meters.
            * `YawPitchRoll` - array_like, [pitch, yaw, roll] in degrees.
            * `Color` - array_like, [r, g, b] as floats ranging 0.0 to 1.0.

        Returns
        -------
        bool
            ``True`` if the option was successfully set.

        Examples
        --------
        Configuring a stereo debug HUD guide::

            # show a quad with a crosshair
            hmd.stereoDebugHudMode('QuadWithCrosshair')
            # enable displaying guide information
            hmd.setStereoDebugHudOption('InfoEnable', True)
            # set the position of the guide quad in the scene
            hmd.setStereoDebugHudOption('Position', [0.0, 1.7, -2.0])

        """
        if option == 'InfoEnable':
            result = libovr.setBool(
                libovr.DEBUG_HUD_STEREO_GUIDE_INFO_ENABLE, value)
        elif option == 'Size':
            value = np.asarray(value, dtype=np.float32)
            result = libovr.setFloatArray(
                libovr.DEBUG_HUD_STEREO_GUIDE_SIZE, value)
        elif option == 'Position':
            value = np.asarray(value, dtype=np.float32)
            result = libovr.setFloatArray(
                libovr.DEBUG_HUD_STEREO_GUIDE_POSITION, value)
        elif option == 'YawPitchRoll':
            value = np.asarray(value, dtype=np.float32)
            result = libovr.setFloatArray(
                libovr.DEBUG_HUD_STEREO_GUIDE_YAWPITCHROLL, value)
        elif option == 'Color' or option == 'Colour':
            value = np.asarray(value, dtype=np.float32)
            result = libovr.setFloatArray(
                libovr.DEBUG_HUD_STEREO_GUIDE_COLOR, value)
        else:
            raise ValueError("Invalid option `{}` specified.".format(option))

        if result:
            logging.info(
                "Stereo debug HUD option '{}' set to {}.".format(
                    option, str(value)))
        else:
            logging.warning(
                "Failed to set stereo debug HUD option '{}' set to {}.".format(
                    option, str(value)))

    @property
    def userHeight(self):
        """Get user height in meters (`float`)."""
        return libovr.getFloat(libovr.KEY_PLAYER_HEIGHT,
                               libovr.DEFAULT_PLAYER_HEIGHT)

    @property
    def eyeHeight(self):
        """Eye height in meters (`float`)."""
        return libovr.getFloat(libovr.KEY_EYE_HEIGHT,
                               libovr.DEFAULT_EYE_HEIGHT)

    @property
    def eyeToNoseDistance(self):
        """Eye to nose distance in meters (`float`).

        Examples
        --------
        Generate your own eye poses. These are used when
        :py:meth:`calcEyePoses` is called::

            leftEyePose = Rift.createPose((-self.eyeToNoseDistance, 0., 0.))
            rightEyePose = Rift.createPose((self.eyeToNoseDistance, 0., 0.))

        Get the inter-axial separation (IAS) reported by `LibOVR`::

            iad = self.eyeToNoseDistance * 2.0

        """
        eyeToNoseDist = np.zeros((2,), dtype=np.float32)
        libovr.getFloatArray(libovr.KEY_EYE_TO_NOSE_DISTANCE, eyeToNoseDist)

        return eyeToNoseDist

    @property
    def eyeOffset(self):
        """Eye separation in centimeters (`float`).

        """
        leftEyeHmdPose = libovr.getHmdToEyePose(libovr.EYE_LEFT)
        rightEyeHmdPose = libovr.getHmdToEyePose(libovr.EYE_RIGHT)

        return (-leftEyeHmdPose.pos[0] + rightEyeHmdPose.pos[0]) / 100.0

    @eyeOffset.setter
    def eyeOffset(self, value):
        halfIAS = (value / 2.0) * 100.0
        libovr.setHmdToEyePose(
            libovr.EYE_LEFT, libovr.LibOVRPose((halfIAS, 0.0, 0.0)))
        libovr.setHmdToEyePose(
            libovr.EYE_RIGHT, libovr.LibOVRPose((-halfIAS, 0.0, 0.0)))

        logging.info(
            'Eye separation set to {} centimeters.'.format(value))

    @property
    def hasPositionTracking(self):
        """``True`` if the HMD is capable of tracking position."""
        return self._hmdInfo.hasPositionTracking

    @property
    def hasOrientationTracking(self):
        """``True`` if the HMD is capable of tracking orientation."""
        return self._hmdInfo.hasOrientationTracking

    @property
    def hasMagYawCorrection(self):
        """``True`` if this HMD supports yaw drift correction."""
        return self._hmdInfo.hasMagYawCorrection

    @property
    def productName(self):
        """Get the HMD's product name (`str`).
        """
        return self._hmdInfo.productName

    @property
    def manufacturer(self):
        """Get the connected HMD's manufacturer (`str`).
        """
        return self._hmdInfo.manufacturer

    @property
    def serialNumber(self):
        """Get the connected HMD's unique serial number (`str`).

        Use this to identify a particular unit if you own many.
        """
        return self._hmdInfo.serialNumber

    @property
    def hid(self):
        """USB human interface device (HID) identifiers (`int`, `int`).

        """
        return self._hmdInfo.hid

    @property
    def firmwareVersion(self):
        """Get the firmware version of the active HMD (`int`, `int`).

        """
        return self._hmdInfo.firmwareVersion

    @property
    def displayResolution(self):
        """Get the HMD's raster display size (`int`, `int`).

        """
        return self._hmdInfo.resolution

    @property
    def displayRefreshRate(self):
        """Get the HMD's display refresh rate in Hz (`float`).

        """
        return self._hmdInfo.refreshRate

    @property
    def pixelsPerTanAngleAtCenter(self):
        """Horizontal and vertical pixels per tangent angle (=1) at the center
        of the display.

        This can be used to compute pixels-per-degree for the display.

        """
        return [libovr.getPixelsPerTanAngleAtCenter(libovr.EYE_LEFT),
                libovr.getPixelsPerTanAngleAtCenter(libovr.EYE_RIGHT)]

    def tanAngleToNDC(self, horzTan, vertTan):
        """Convert tan angles to the normalized device coordinates for the
        current buffer.

        Parameters
        ----------
        horzTan : float
            Horizontal tan angle.
        vertTan : float
            Vertical tan angle.

        Returns
        -------
        tuple of float
            Normalized device coordinates X, Y. Coordinates range between -1.0
            and 1.0. Returns `None` if an invalid buffer is selected.

        """
        if self.buffer == 'left':
            return libovr.getTanAngleToRenderTargetNDC(
                libovr.EYE_LEFT, (horzTan, vertTan))
        elif self.buffer == 'right':
            return libovr.getTanAngleToRenderTargetNDC(
                libovr.EYE_RIGHT, (horzTan, vertTan))

    @property
    def trackerCount(self):
        """Number of attached trackers."""
        return libovr.getTrackerCount()

    def getTrackerInfo(self, trackerIdx):
        """Get tracker information.

        Parameters
        ----------
        trackerIdx : int
            Tracker index, ranging from 0 to :py:class:`~Rift.trackerCount`.

        Returns
        -------
        :py:class:`~psychxr.libovr.LibOVRTrackerInfo`
            Object containing tracker information.

        Raises
        ------
        IndexError
            Raised when `trackerIdx` out of range.

        """
        if 0 <= trackerIdx < libovr.getTrackerCount():
            return libovr.getTrackerInfo(trackerIdx)
        else:
            raise IndexError(
                "Tracker index '{}' out of range.".format(trackerIdx))

    @property
    def headLocked(self):
        """`True` if head locking is enabled."""
        return libovr.isHeadLocked()

    @headLocked.setter
    def headLocked(self, value):
        libovr.setHeadLocked(bool(value))

    @property
    def trackingOriginType(self):
        """Current tracking origin type (`str`).

        Valid tracking origin types are 'floor' and 'eye'.

        """
        originType = libovr.getTrackingOriginType()

        if originType == libovr.TRACKING_ORIGIN_FLOOR_LEVEL:
            return 'floor'
        elif originType == libovr.TRACKING_ORIGIN_EYE_LEVEL:
            return 'eye'
        else:
            raise ValueError("LibOVR returned unknown tracking origin type.")

    @trackingOriginType.setter
    def trackingOriginType(self, value):
        libovr.setTrackingOriginType(RIFT_TRACKING_ORIGIN_TYPE[value])

    def recenterTrackingOrigin(self):
        """Recenter the tracking origin using the current head position."""
        libovr.recenterTrackingOrigin()

    def specifyTrackingOrigin(self, pose):
        """Specify a tracking origin. If `trackingOriginType='floor'`, this
        function sets the origin of the scene in the ground plane. If
        `trackingOriginType='eye'`, the scene origin is set to the known eye
        height.

        Parameters
        ----------
        pose : LibOVRPose
            Tracking origin pose.

        """
        libovr.specifyTrackingOrigin(pose)

    def specifyTrackingOriginPosOri(self, pos=(0., 0., 0.), ori=(0., 0., 0., 1.)):
        """Specify a tracking origin using a pose and orientation. This is the
        same as `specifyTrackingOrigin`, but accepts a position vector [x, y, z]
        and orientation quaternion [x, y, z, w].

        Parameters
        ----------
        pos : tuple or list of float, or ndarray
            Position coordinate of origin (x, y, z).
        ori : tuple or list of float, or ndarray
            Quaternion specifying orientation (x, y, z, w).

        """
        libovr.specifyTrackingOrigin(libovr.LibOVRPose(pos, ori))

    def clearShouldRecenterFlag(self):
        """Clear the 'shouldRecenter' status flag at the API level."""
        libovr.clearShouldRecenterFlag()

    def testBoundary(self, deviceType, bounadryType='PlayArea'):
        """Test if tracked devices are colliding with the play area boundary.

        This returns an object containing test result data.

        Parameters
        ----------
        deviceType : str, list or tuple
            The device to check for boundary collision. If a list of names is
            provided, they will be combined and all tested.
        boundaryType : str
            Boundary type to test.

        """
        if isinstance(deviceType, (list, tuple,)):
            deviceBits = 0x00000000
            for device in deviceType:
                deviceBits |= RIFT_TRACKED_DEVICE_TYPES[device]
        elif isinstance(deviceType, str):
            deviceBits = RIFT_TRACKED_DEVICE_TYPES[deviceType]
        elif isinstance(deviceType, int):
            deviceBits = deviceType
        else:
            raise TypeError("Invalid type specified for `deviceType`.")

        result, testResult = libovr.testBoundary(
            deviceBits, RIFT_BOUNDARY_TYPE[bounadryType])

        if libovr.failure(result):
            raise RuntimeError('Failed to get boundary test result')

        return testResult

    @property
    def sensorSampleTime(self):
        """Sensor sample time (`float`). This value corresponds to the time the
        head (HMD) position was sampled, which is required for computing
        motion-to-photon latency. This does not need to be specified if
        `getTrackingState` was called with `latencyMarker=True`.
        """
        return libovr.getSensorSampleTime()

    @sensorSampleTime.setter
    def sensorSampleTime(self, value):
        libovr.setSensorSampleTime(value)

    def getDevicePose(self, deviceName, absTime=None, latencyMarker=False):
        """Get the pose of a tracked device. For head (HMD) and hand poses
        (Touch controllers) it is better to use :py:meth:`getTrackingState`
        instead.

        Parameters
        ----------
        deviceName : str
            Name of the device. Valid device names are: 'HMD', 'LTouch',
            'RTouch', 'Touch', 'Object0', 'Object1', 'Object2', and 'Object3'.
        absTime : float, optional
            Absolute time in seconds the device pose refers to. If not
            specified, the predicted time is used.
        latencyMarker : bool
            Insert a marker for motion-to-photon latency calculation. Should
            only be `True` if the HMD pose is being used to compute eye poses.

        Returns
        -------
        `LibOVRPoseState` or `None`
            Pose state object. `None` if device tracking was lost.

        """
        if absTime is None:
            absTime = self.getPredictedDisplayTime()

        deviceStatus, devicePose = libovr.getDevicePoses(
            [RIFT_TRACKED_DEVICE_TYPES[deviceName]], absTime, latencyMarker)

        # check if tracking was lost
        if deviceStatus == libovr.ERROR_LOST_TRACKING:
            return None

        return devicePose[0]

    def getTrackingState(self, absTime=None, latencyMarker=True):
        """Get the tracking state of the head and hands.

        Calling this function retrieves the tracking state of the head (HMD)
        and hands at `absTime` from the `LibOVR` runtime. The returned object is
        a :py:class:`~psychxr.libovr.LibOVRTrackingState` instance with poses,
        motion derivatives (i.e. linear and angular velocity/acceleration), and
        tracking status flags accessible through its attributes.

        The pose states of the head and hands are available by accessing the
        `headPose` and `handPoses` attributes, respectively.

        Parameters
        ----------
        absTime : float, optional
            Absolute time the tracking state refers to. If not specified,
            the predicted display time is used.
        latencyMarker : bool, optional
            Set a latency marker upon getting the tracking state. This is used
            for motion-to-photon calculations.

        Returns
        -------
        :py:class:`~psychxr.libovr.LibOVRTrackingState`
            Tracking state object. For more information about this type see:

        See Also
        --------
        getPredictedDisplayTime
            Time at mid-frame for the current frame index.

        Examples
        --------
        Get the tracked head pose and use it to calculate render eye poses::

            # get tracking state at predicted mid-frame time
            absTime = getPredictedDisplayTime()
            trackingState = hmd.getTrackingState(absTime)

            # get the head pose from the tracking state
            headPose = trackingState.headPose.thePose
            hmd.calcEyePoses(headPose)  # compute eye poses

        Get linear/angular velocity and acceleration vectors of the right
        touch controller::

            # right hand is the second value (index 1) at `handPoses`
            rightHandState = trackingState.handPoses[1]  # is `LibOVRPoseState`

            # access `LibOVRPoseState` fields to get the data
            linearVel = rightHandState.linearVelocity  # m/s
            angularVel = rightHandState.angularVelocity  # rad/s
            linearAcc = rightHandState.linearAcceleration  # m/s^2
            angularAcc = rightHandState.angularAcceleration  # rad/s^2

            # extract components like this if desired
            vx, vy, vz = linearVel
            ax, ay, az = angularVel

        Above is useful for physics simulations, where one can compute the
        magnitude and direction of a force applied to a virtual object.

        It's often the case that object tracking becomes unreliable for some
        reason, for instance, if it becomes occluded and is no longer visible to
        the sensors. In such cases, the reported pose state is invalid and may
        not be useful. You can check if the position and orientation of a
        tracked object is invalid using flags associated with the tracking
        state. This shows how to check if head position and orientation tracking
        was valid when sampled::

            if trackingState.positionValid and trackingState.orientationValid:
                print('Tracking valid.')

        It's up to the programmer to determine what to do in such cases. Note
        that tracking may still be valid even if

        Get the calibrated origin used for tracking during the sample period
        of the tracking state::

            calibratedOrigin = trackingState.calibratedOrigin
            calibPos, calibOri = calibratedOrigin.posOri

        Time integrate a tracking state. This extrapolates the pose over time
        given the present computed motion derivatives. The contrived example
        below shows how to implement head pose forward prediction::

            # get current system time
            absTime = getTimeInSeconds()

            # get the elapsed time from `absTime` to predicted v-sync time,
            # again this is an example, you would usually pass predicted time to
            # `getTrackingState` directly.
            dt = getPredictedDisplayTime() - absTime

            # get the tracking state for the current time, poses will lag where
            # they are expected at predicted time by `dt` seconds
            trackingState = hmd.getTrackingState(absTime)

            # time integrate a pose by `dt`
            headPoseState = trackingState.headPose
            headPosePredicted = headPoseState.timeIntegrate(dt)

            # calc eye poses with predicted head pose, this is a custom pose to
            # head-locking should be enabled!
            hmd.calcEyePoses(headPosePredicted)

        The resulting head pose is usually very close to what `getTrackingState`
        would return if the predicted time was used. Simple forward prediction
        with time integration becomes increasingly unstable as the prediction
        interval increases. Under normal circumstances, let the runtime handle
        forward prediction by using the pose states returned at the predicted
        display time. If you plan on doing your own forward prediction, you need
        enable head-locking, clamp the prediction interval, and apply some sort
        of smoothing to keep the image as stable as possible.

        """
        if absTime is None:
            absTime = self.getPredictedDisplayTime()

        return libovr.getTrackingState(absTime, latencyMarker)

    def calcEyePoses(self, headPose, originPose=None):
        """Calculate eye poses for rendering.

        This function calculates the eye poses to define the viewpoint
        transformation for each eye buffer. Upon starting a new frame, the
        application loop is halted until this function is called and returns.

        Once this function returns, `setBuffer` may be called and frame
        rendering can commence. The computed eye pose for the selected buffer is
        accessible through the :py:attr:`eyeRenderPose` attribute after calling
        :py:meth:`setBuffer`. If `monoscopic=True`, the eye poses are set to
        the head pose.

        The source data specified to `headPose` can originate from the tracking
        state retrieved by calling :py:meth:`getTrackingState`, or from
        other sources. If a custom head pose is specified (for instance, from a
        motion tracker), you must ensure `head-locking` is enabled to prevent
        the ASW feature of the compositor from engaging. Furthermore, you must
        specify sensor sample time for motion-to-photon calculation derived from
        the sample time of the custom tracking source.

        Parameters
        ----------
        headPose : LibOVRPose
            Head pose to use.
        originPose : LibOVRPose, optional
            Origin of tracking in the VR scene.

        Examples
        --------
        Get the tracking state and calculate the eye poses::

            # get tracking state at predicted mid-frame time
            trackingState = hmd.getTrackingState()

            # get the head pose from the tracking state
            headPose = trackingState.headPose.thePose
            hmd.calcEyePoses(headPose)  # compute eye poses

            # begin rendering to each eye
            for eye in ('left', 'right'):
                hmd.setBuffer(eye)
                hmd.setRiftView()
                # draw stuff here ...

        Using a custom head pose (make sure ``headLocked=True`` before doing
        this)::

            headPose = createPose((0., 1.75, 0.))
            hmd.calcEyePoses(headPose)  # compute eye poses

        """
        if not self._allowHmdRendering:
            return

        libovr.calcEyePoses(headPose, originPose)
        self._headPose = headPose

        # Calculate eye poses, this needs to be called every frame.
        # apply additional transformations to eye poses
        if not self._monoscopic:
            for eye, matrix in enumerate(self._viewMatrix):
                # compute each eye's transformation modelMatrix from returned poses
                libovr.getEyeViewMatrix(eye, matrix)
        else:
            # view modelMatrix derived from head position when in monoscopic mode
            self._viewMatrix = headPose.getViewMatrix()

        self._startHmdFrame()

    @property
    def eyeRenderPose(self):
        """Computed eye pose for the current buffer. Only valid after calling
        :func:`calcEyePoses`.

        """
        if not self._monoscopic:
            if self.buffer == 'left':
                return libovr.getEyeRenderPose(libovr.EYE_LEFT)
            elif self.buffer == 'right':
                return libovr.getEyeRenderPose(libovr.EYE_RIGHT)
        else:
            return self._headPose

    @property
    def shouldQuit(self):
        """`True` if the user requested the application should quit through the
        headset's interface.
        """
        return self._sessionStatus.shouldQuit

    @property
    def isVisible(self):
        """`True` if the app has focus in the HMD and is visible to the viewer.
        """
        return self._sessionStatus.isVisible

    @property
    def hmdMounted(self):
        """`True` if the HMD is mounted on the user's head.
        """
        return self._sessionStatus.hmdMounted

    @property
    def hmdPresent(self):
        """`True` if the HMD is present.
        """
        return self._sessionStatus.hmdPresent

    @property
    def shouldRecenter(self):
        """`True` if the user requested the origin be re-centered through the
        headset's interface.
        """
        return self._sessionStatus.shouldRecenter

    @property
    def hasInputFocus(self):
        """`True` if the application currently has input focus.
        """
        return self._sessionStatus.hasInputFocus

    @property
    def overlayPresent(self):
        return self._sessionStatus.overlayPresent

    def _setupFrameBuffer(self):
        """Override the default framebuffer init code in window.Window to use
        the HMD swap chain. The HMD's swap texture and render buffer are
        configured here.

        If multisample anti-aliasing (MSAA) is enabled, a secondary render
        buffer is created. Rendering is diverted to the multi-sample buffer
        when drawing, which is then resolved into the HMD's swap chain texture
        prior to committing it to the chain. Consequently, you cannot pass
        the texture attached to the FBO specified by `frameBuffer` until the
        MSAA buffer is resolved. Doing so will result in a blank texture.

        """
        # create a texture swap chain for both eye textures
        result = libovr.createTextureSwapChainGL(
            libovr.TEXTURE_SWAP_CHAIN0,
            self._swapTextureSize[0],
            self._swapTextureSize[1])

        if libovr.success(result):
            logging.info(
                'Created texture swap chain with dimensions {w}x{h}.'.format(
                    w=self._swapTextureSize[0],
                    h=self._swapTextureSize[1]))
        else:
            _, msg = libovr.getLastErrorInfo()
            raise LibOVRError(msg)

        # assign the same swap chain to both eyes
        for eye in range(libovr.EYE_COUNT):
            libovr.setEyeColorTextureSwapChain(eye, libovr.TEXTURE_SWAP_CHAIN0)

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
            logging.info(
                'Samples > 1, creating multi-sample framebuffer with dimensions'
                '{w}x{h}.'.format(w=int(self._swapTextureSize[0]),
                                  h=int(self._swapTextureSize[1])))

            # multi-sample FBO and rander buffer
            GL.glGenFramebuffers(1, ctypes.byref(self.frameBufferMsaa))
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.frameBufferMsaa)

            # we don't need a multi-sample texture
            rb_color_msaa_id = GL.GLuint()
            GL.glGenRenderbuffers(1, ctypes.byref(rb_color_msaa_id))
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rb_color_msaa_id)
            GL.glRenderbufferStorageMultisample(
                GL.GL_RENDERBUFFER,
                self._samples,
                GL.GL_RGBA8,
                int(self._swapTextureSize[0]),
                int(self._swapTextureSize[1]))
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_RENDERBUFFER,
                rb_color_msaa_id)
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, 0)

            rb_depth_msaa_id = GL.GLuint()
            GL.glGenRenderbuffers(1, ctypes.byref(rb_depth_msaa_id))
            GL.glBindRenderbuffer(GL.GL_RENDERBUFFER, rb_depth_msaa_id)
            GL.glRenderbufferStorageMultisample(
                GL.GL_RENDERBUFFER,
                self._samples,
                GL.GL_DEPTH24_STENCIL8,
                int(self._swapTextureSize[0]),
                int(self._swapTextureSize[1]))
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_DEPTH_ATTACHMENT,
                GL.GL_RENDERBUFFER,
                rb_depth_msaa_id)
            GL.glFramebufferRenderbuffer(
                GL.GL_FRAMEBUFFER,
                GL.GL_STENCIL_ATTACHMENT,
                GL.GL_RENDERBUFFER,
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
        self._mirrorFbo = GL.GLuint()
        GL.glGenFramebuffers(1, ctypes.byref(self._mirrorFbo))

        if self._mirrorRes is None:
            self._mirrorRes = self.frameBufferSize

        mirrorW, mirrorH = self._mirrorRes
        if libovr.success(libovr.createMirrorTexture(
                mirrorW,
                mirrorH,
                mirrorOptions=RIFT_MIRROR_MODES[self._mirrorMode])):
            logging.info(
                'Created mirror texture with dimensions {w} x {h}'.format(
                    w=mirrorW, h=mirrorH))
        else:
            _, msg = libovr.getLastErrorInfo()
            raise LibOVRError(msg)

        GL.glDisable(GL.GL_TEXTURE_2D)

        return True  # assume the FBOs are complete for now

    def _resolveMSAA(self):
        """Resolve multisample anti-aliasing (MSAA). If MSAA is enabled, drawing
        operations are diverted to a special multisample render buffer. Pixel
        data must be 'resolved' by blitting it to the swap chain texture. If
        not, the texture will be blank.

        Notes
        -----
        You cannot perform operations on the default FBO (at `frameBuffer`) when
        MSAA is enabled. Any changes will be over-written when 'flip' is called.

        """
        # if multi-sampling is off just NOP
        if self._samples == 1:
            return

        # bind framebuffer
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.frameBufferMsaa)
        GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, self.frameBuffer)

        # bind the HMD swap texture to the draw buffer
        GL.glFramebufferTexture2D(
            GL.GL_DRAW_FRAMEBUFFER,
            GL.GL_COLOR_ATTACHMENT0,
            GL.GL_TEXTURE_2D,
            self.frameTexture,
            0)

        # blit the texture
        fbo_w, fbo_h = self._swapTextureSize
        self.viewport = self.scissor = (0, 0, fbo_w, fbo_h)
        GL.glBlitFramebuffer(
            0, 0, fbo_w, fbo_h,
            0, 0, fbo_w, fbo_h,  # flips texture
            GL.GL_COLOR_BUFFER_BIT,
            GL.GL_NEAREST)

        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)

    def _prepareMonoFrame(self, clear=True):
        """Prepare a frame for monoscopic rendering. This is called
        automatically after :func:`_startHmdFrame` if monoscopic rendering is
        enabled.

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

        self.viewport = self.scissor = \
            libovr.getEyeRenderViewport(libovr.EYE_LEFT)  # mono mode
        GL.glDepthMask(GL.GL_TRUE)

        if clear:
            self.setColor(self.color, colorSpace=self.colorSpace)  # clear the texture to the window color
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
        """Set the active draw buffer.

        Warnings
        --------
        The window.Window.size property will return the buffer's dimensions in
        pixels instead of the window's when `setBuffer` is set to 'left' or
        'right'.

        Parameters
        ----------
        buffer : str
            View buffer to divert successive drawing operations to, can be
            either 'left' or 'right'.
        clear : boolean
            Clear the color, stencil and depth buffer.

        """
        # if monoscopic, nop
        if self._monoscopic:
            warnings.warn("`setBuffer` called in monoscopic mode.", RuntimeWarning)
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

        # set the viewport and scissor rect for the buffer
        if buffer == 'left':
            self.viewport = self.scissor = libovr.getEyeRenderViewport(
                libovr.EYE_LEFT)
        elif buffer == 'right':
            self.viewport = self.scissor = libovr.getEyeRenderViewport(
                libovr.EYE_RIGHT)

        if clear:
            self.setColor(self.color, colorSpace=self.colorSpace)  # clear the texture to the window color
            GL.glClearDepth(1.0)
            GL.glDepthMask(GL.GL_TRUE)
            GL.glClear(
                GL.GL_COLOR_BUFFER_BIT |
                GL.GL_DEPTH_BUFFER_BIT |
                GL.GL_STENCIL_BUFFER_BIT)

        # if self.sRGB:
        #    GL.glDisable(GL.GL_FRAMEBUFFER_SRGB)

        if self._samples > 1:
            GL.glEnable(GL.GL_MULTISAMPLE)

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)

    def getPredictedDisplayTime(self):
        """Get the predicted time the next frame will be displayed on the HMD.
        The returned time is referenced to the clock `LibOVR` is using.

        Returns
        -------
        float
            Absolute frame mid-point time for the given frame index in seconds.

        """
        return libovr.getPredictedDisplayTime(self._frameIndex)

    def getTimeInSeconds(self):
        """Absolute time in seconds. The returned time is referenced to the
        clock `LibOVR` is using.

        Returns
        -------
        float
            Time in seconds.

        """
        return libovr.timeInSeconds()

    @property
    def viewMatrix(self):
        """The view matrix for the current eye buffer. Only valid after a
        :py:meth:`calcEyePoses` call. Note that setting `viewMatrix` manually
        will break visibility culling.

        """
        if not self._monoscopic:
            if self.buffer == 'left':
                return self._viewMatrix[libovr.EYE_LEFT]
            elif self.buffer == 'right':
                return self._viewMatrix[libovr.EYE_RIGHT]
        else:
            return self._viewMatrix

    @property
    def nearClip(self):
        """Distance to the near clipping plane in meters."""
        return self._nearClip

    @nearClip.setter
    def nearClip(self, value):
        self._nearClip = value
        self._updateProjectionMatrix()

    @property
    def farClip(self):
        """Distance to the far clipping plane in meters."""
        return self._farClip

    @farClip.setter
    def farClip(self, value):
        self._farClip = value
        self._updateProjectionMatrix()

    @property
    def projectionMatrix(self):
        """Get the projection matrix for the current eye buffer. Note that
        setting `projectionMatrix` manually will break visibility culling.

        """
        if not self._monoscopic:
            if self.buffer == 'left':
                return self._projectionMatrix[libovr.EYE_LEFT]
            elif self.buffer == 'right':
                return self._projectionMatrix[libovr.EYE_RIGHT]
        else:
            return self._projectionMatrix

    @property
    def isBoundaryVisible(self):
        """True if the VR boundary is visible.
        """
        result, isVisible = libovr.getBoundaryVisible()
        return bool(isVisible)

    def getBoundaryDimensions(self, boundaryType='PlayArea'):
        """Get boundary dimensions.

        Parameters
        ----------
        boundaryType : str
            Boundary type, can be 'PlayArea' or 'Outer'.

        Returns
        -------
        ndarray
            Dimensions of the boundary meters [x, y, z].

        """
        result, dims = libovr.getBoundaryDimensions(
            RIFT_BOUNDARY_TYPE[boundaryType])

        return dims

    @property
    def connectedControllers(self):
        """Connected controller types (`list` of `str`)"""
        controllers = libovr.getConnectedControllerTypes()
        ctrlKeys = {val: key for key, val in RIFT_CONTROLLER_TYPES.items()}

        return [ctrlKeys[ctrl] for ctrl in controllers]

    def updateInputState(self, controllers=None):
        """Update all connected controller states. This updates controller input
        states for an input device managed by `LibOVR`.

        The polling time for each device is accessible through the
        `controllerPollTimes` attribute. This attribute returns a dictionary
        where the polling time from the last `updateInputState` call for a
        given controller can be retrieved by using the name as a key.

        Parameters
        ----------
        controllers : tuple or list, optional
            List of controllers to poll. If `None`, all available controllers
            will be polled.

        Examples
        --------
        Poll the state of specific controllers by name::

            controllers = ['XBox', 'Touch']
            updateInputState(controllers)

        """
        if controllers is None:
            toPoll = libovr.getConnectedControllerTypes()
        elif isinstance(controllers, (list, tuple,)):
            toPoll = [RIFT_CONTROLLER_TYPES[ctrl] for ctrl in controllers]
        else:
            raise TypeError("Argument 'controllers' must be iterable type.")

        for i in toPoll:
            result, t_sec = libovr.updateInputState(i)
            self.controllerPollTimes[RIFT_CONTROLLER_TYPES[i]] = t_sec

    def _waitToBeginHmdFrame(self):
        """Wait until the HMD surfaces are available for rendering.
        """
        # First time this function is called, make True.
        if not self._allowHmdRendering:
            self._allowHmdRendering = True

        # update session status
        result, status = libovr.getSessionStatus()
        self._sessionStatus = status

        # get performance stats for the last frame
        self._updatePerfStats()

        # Wait for the buffer to be freed by the compositor, this is like
        # waiting for v-sync.
        libovr.waitToBeginFrame(self._frameIndex)

        # update input states
        if self.autoUpdateInput:
            self.updateInputState()

        #if result == ovr.SUCCESS_NOT_VISIBLE:
        #    pass
        #self.updateInputState()  # poll controller states

        # # update the tracking state
        # if self.autoUpdatePoses:
        #     # get the current frame time
        #     absTime = libovr.getPredictedDisplayTime(self._frameIndex)
        #     # Get the current tracking state structure, estimated poses for the
        #     # head and hands are stored here. The latency marker for computing
        #     # motion-to-photon latency is set when this function is called.
        #     self.calcEyePoses()

    def _startHmdFrame(self):
        """Prepare to render an HMD frame. This must be called every frame
        before flipping or setting the view buffer.

        This function will wait until the HMD is ready to begin rendering before
        continuing. The current frame texture from the swap chain are pulled
        from the SDK and made available for binding.

        """
        # begin frame
        libovr.beginFrame(self._frameIndex)
        # get the next available buffer texture in the swap chain
        result, swapChainIdx = libovr.getTextureSwapChainCurrentIndex(
            libovr.TEXTURE_SWAP_CHAIN0)
        result, colorTextureId = libovr.getTextureSwapChainBufferGL(
            libovr.TEXTURE_SWAP_CHAIN0, swapChainIdx)
        self.frameTexture = colorTextureId

        # If mono mode, we want to configure the render framebuffer at this
        # point since 'setBuffer' will not be called.
        if self._monoscopic:
            self._prepareMonoFrame()

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
        # Switch off multi-sampling
        GL.glDisable(GL.GL_MULTISAMPLE)

        if self._allowHmdRendering:
            # resolve MSAA buffers
            self._resolveMSAA()

            # commit current texture buffer to the swap chain
            libovr.commitTextureSwapChain(libovr.TEXTURE_SWAP_CHAIN0)

            # Call end_frame and increment the frame index, no more rendering to
            # HMD's view texture at this point.
            result, _ = libovr.endFrame(self._frameIndex)

            if libovr.failure(result):
                if result == libovr.ERROR_DISPLAY_LOST:  # display lost!
                    libovr.destroyMirrorTexture()
                    libovr.destroyTextureSwapChain(libovr.TEXTURE_SWAP_CHAIN0)
                    libovr.destroy()
                    #libovr.shutdown()  # avoid error

                _, msg = libovr.getLastErrorInfo()
                raise LibOVRError(msg)

            self._frameIndex += 1  # increment frame index

        # Set to None so the 'size' attribute returns the on-screen window size.
        self.buffer = None

        # Make sure this is called after flipping, this updates VR information
        # and diverts rendering to the HMD texture.
        #self.callOnFlip(self._waitToBeginHmdFrame)

        # Call frame timing routines
        #self.callOnFlip(self._updatePerformanceStats)

        # This always returns True
        return True

    def flip(self, clearBuffer=True, drawMirror=True):
        """Submit view buffer images to the HMD's compositor for display at next
        V-SYNC and draw the mirror texture to the on-screen window. This must
        be called every frame.

        Parameters
        ----------
        clearBuffer : bool
            Clear the frame after flipping.
        drawMirror : bool
            Draw the HMD mirror texture from the compositor to the window.

        Returns
        -------
        float
            Absolute time in seconds when control was given back to the
            application. The difference between the current and previous values
            should be very close to 1 / refreshRate of the HMD.

        Notes
        -----

        * The HMD compositor and application are asynchronous, therefore there
          is no guarantee that the timestamp returned by 'flip' corresponds to
          the exact vertical retrace time of the HMD.

        """
        # NOTE: Most of this code is shared with the regular Window's flip
        # function for compatibility. We're only concerned with calling the
        # _startOfFlip function and drawing the mirror texture to the onscreen
        # window. Display timing functions are kept in for now, but they are not
        # active.
        #

        flipThisFrame = self._startOfFlip()
        if flipThisFrame:
            self._prepareFBOrender()
            # need blit the framebuffer object to the actual back buffer
            result, mirrorTexId = libovr.getMirrorTexture()
            if libovr.failure(result):
                _, msg = libovr.getLastErrorInfo()
                raise LibOVRError(msg)

            # unbind the framebuffer as the render target
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, 0)
            GL.glDisable(GL.GL_BLEND)
            stencilOn = GL.glIsEnabled(GL.GL_STENCIL_TEST)
            GL.glDisable(GL.GL_STENCIL_TEST)

            win_w, win_h = self.frameBufferSize
            self.viewport = self.scissor = (0, 0, win_w, win_h)

            # draw the mirror texture, if not anything drawn to the backbuffer
            # will be displayed instead
            if drawMirror:
                # blit mirror texture
                GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self._mirrorFbo)
                GL.glBindFramebuffer(GL.GL_DRAW_FRAMEBUFFER, 0)

                GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
                # bind the rift's texture to the framebuffer
                GL.glFramebufferTexture2D(
                    GL.GL_READ_FRAMEBUFFER,
                    GL.GL_COLOR_ATTACHMENT0,
                    GL.GL_TEXTURE_2D, mirrorTexId, 0)

                win_w, win_h = self.frameBufferSize

                tex_w, tex_h = self._mirrorRes
                self.viewport = self.scissor = (0, 0, win_w, win_h)
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

        # flip the mirror window
        self.backend.swapBuffers(flipThisFrame)

        if flipThisFrame:
            # set rendering back to the framebuffer object
            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
            #GL.glReadBuffer(GL.GL_BACK)
            #GL.glDrawBuffer(GL.GL_BACK)
            GL.glClearColor(0.0, 0.0, 0.0, 1.0)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)
            # set to no active rendering texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            if stencilOn:
                GL.glEnable(GL.GL_STENCIL_TEST)

        # reset returned buffer for next frame
        self._endOfFlip(clearBuffer)

        # wait until surfaces are available for drawing
        self._waitToBeginHmdFrame()

        # get timestamp at the point control is handed back to the application
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

        return now

    def multiplyViewMatrixGL(self):
        """Multiply the local eye pose transformation modelMatrix obtained from the
        SDK using ``glMultMatrixf``. The modelMatrix used depends on the current eye
        buffer set by :func:`setBuffer`.

        Returns
        -------
        None

        """
        if not self._legacyOpenGL:
            return

        if not self._monoscopic:
            if self.buffer == 'left':
                GL.glMultTransposeMatrixf(
                    self._viewMatrix[0].flatten().ctypes.data_as(
                        ctypes.POINTER(ctypes.c_float)))
            elif self.buffer == 'right':
                GL.glMultTransposeMatrixf(
                    self._viewMatrix[1].flatten().ctypes.data_as(
                        ctypes.POINTER(ctypes.c_float)))
        else:
            GL.glMultTransposeMatrixf(self._viewMatrix.ctypes.data_as(
                        ctypes.POINTER(ctypes.c_float)))

    def multiplyProjectionMatrixGL(self):
        """Multiply the current projection modelMatrix obtained from the SDK
        using ``glMultMatrixf``. The projection matrix used depends on the
        current eye buffer set by :func:`setBuffer`.

        """
        if not self._legacyOpenGL:
            return

        if not self._monoscopic:
            if self.buffer == 'left':
                GL.glMultTransposeMatrixf(
                    self._projectionMatrix[0].flatten().ctypes.data_as(
                        ctypes.POINTER(ctypes.c_float)))
            elif self.buffer == 'right':
                GL.glMultTransposeMatrixf(
                    self._projectionMatrix[1].flatten().ctypes.data_as(
                        ctypes.POINTER(ctypes.c_float)))
        else:
            GL.glMultTransposeMatrixf(
                self._projectionMatrix.flatten().ctypes.data_as(
                    ctypes.POINTER(ctypes.c_float)))

    def setRiftView(self, clearDepth=True):
        """Set head-mounted display view. Gets the projection and view matrices
        from the HMD and applies them.

        Note: This only has an effect if using Rift in legacy immediate mode
        OpenGL.

        Parameters
        ----------
        clearDepth : bool
            Clear the depth buffer prior after configuring the view parameters.

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
        OpenGL.

        Parameters
        ----------
        clearDepth : bool
            Clear the depth buffer prior after configuring the view parameters.

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
        """
        if not self._monoscopic:
            libovr.getEyeProjectionMatrix(
                libovr.EYE_LEFT,
                self._projectionMatrix[0])
            libovr.getEyeProjectionMatrix(
                libovr.EYE_RIGHT,
                self._projectionMatrix[1])
        else:
            libovr.getEyeProjectionMatrix(
                libovr.EYE_LEFT,
                self._projectionMatrix)

    def getMovieFrame(self, buffer='mirror'):
        """Capture the current HMD frame as an image.

        Saves to stack for :py:attr:`~Window.saveMovieFrames()`. As of v1.81.00
        this also returns the frame as a PIL image.

        This can be done at any time (usually after a :py:attr:`~Window.flip()`
        command).

        Frames are stored in memory until a :py:attr:`~Window.saveMovieFrames()`
        command is issued. You can issue :py:attr:`~Window.getMovieFrame()` as
        often as you like and then save them all in one go when finished.

        For HMD frames, you should call `getMovieFrame` after calling `flip` to
        ensure that the mirror texture saved reflects what is presently being
        shown on the HMD. Note, that this function is somewhat slow and may
        impact performance. Only call this function when you're not collecting
        experimental data.

        Parameters
        ----------
        buffer : str, optional
            Buffer to capture. For the HMD, only 'mirror' is available at this
            time.

        Returns
        -------
        Image
            Buffer pixel contents as a PIL/Pillow image object.

        """
        im = self._getFrame(buffer=buffer)
        self.movieFrames.append(im)
        return im

    def _getFrame(self, rect=None, buffer='mirror'):
        """Return the current HMD view as an image.

        Parameters
        ----------
        rect : array_like
            Rectangle [x, y, w, h] defining a sub-region of the frame to
            capture. This should remain `None` for HMD frames.
        buffer : str, optional
            Buffer to capture. For the HMD, only 'mirror' is available at this
            time.

        Returns
        -------
        Image
            Buffer pixel contents as a PIL/Pillow image object.

        """
        if buffer == 'mirror':
            result, mirrorTexId = libovr.getMirrorTexture()
            if libovr.failure(result):
                _, msg = libovr.getLastErrorInfo()
                raise LibOVRError(msg)

            GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self._mirrorFbo)

            # GL.glEnable(GL.GL_FRAMEBUFFER_SRGB)
            # bind the rift's texture to the framebuffer
            GL.glFramebufferTexture2D(
                GL.GL_READ_FRAMEBUFFER,
                GL.GL_COLOR_ATTACHMENT0,
                GL.GL_TEXTURE_2D, mirrorTexId, 0)
        else:
            raise ValueError("Requested read from buffer '{}' but should be "
                             "'mirror'.".format(buffer))

        if rect:
            x, y = self._mirrorRes

            # box corners in pix
            left = int((rect[0] / 2. + 0.5) * x)
            top = int((rect[1] / -2. + 0.5) * y)
            w = int((rect[2] / 2. + 0.5) * x) - left
            h = int((rect[3] / -2. + 0.5) * y) - top
        else:
            left = top = 0
            w, h = self.size  # of window, not image

        # http://www.opengl.org/sdk/docs/man/xhtml/glGetTexImage.xml
        bufferDat = (GL.GLubyte * (4 * w * h))()
        GL.glReadPixels(left, top, w, h,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, bufferDat)
        try:
            im = Image.fromstring(mode='RGBA', size=(w, h),
                                  data=bufferDat)
        except Exception:
            im = Image.frombytes(mode='RGBA', size=(w, h),
                                 data=bufferDat)

        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        im = im.convert('RGB')

        if self.buffer is not None:
            self.setBuffer(self.buffer, clear=False)  # go back to previous buffer
        else:
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, self.frameBuffer)

        return im

    def getThumbstickValues(self, controller='Xbox', deadzone=False):
        """Get controller thumbstick values.

        Parameters
        ----------
        controller : str
            Name of the controller to get thumbstick values. Possible values for
            `controller` are 'Xbox', 'Touch', 'RTouch', 'LTouch', 'Object0',
            'Object1', 'Object2', and 'Object3'; the only devices with
            thumbsticks the SDK manages. For additional controllers, use
            PsychPy's built-in event or hardware support.
        deadzone : bool
            Apply the deadzone to thumbstick values. This pre-filters stick
            input to apply a dead-zone where 0.0 will be returned if the sticks
            return a displacement within -0.2746 to 0.2746.

        Returns
        -------
        tuple
            Left and right, X and Y thumbstick values. Axis displacements are
            represented in each tuple by floats ranging from -1.0 (full
            left/down) to 1.0 (full right/up). The returned values reflect the
            controller state since the last :py:class:`~Rift.updateInputState`
            or :py:class:`~Rift.flip` call.

        """
        return libovr.getThumbstickValues(RIFT_CONTROLLER_TYPES[controller],
                                          deadzone)

    def getIndexTriggerValues(self, controller='Xbox', deadzone=False):
        """Get the values of the index triggers.

        Parameters
        ----------
        controller : str
            Name of the controller to get index trigger values. Possible values
            for `controller` are 'Xbox', 'Touch', 'RTouch', 'LTouch', 'Object0',
            'Object1', 'Object2', and 'Object3'; the only devices with index
            triggers the SDK manages. For additional controllers, use PsychPy's
            built-in event or hardware support.
        deadzone : bool
            Apply the deadzone to index trigger values. This pre-filters stick
            input to apply a dead-zone where 0.0 will be returned if the trigger
            returns a displacement within 0.2746.

        Returns
        -------
        tuple of float
            Left and right index trigger values. Displacements are represented
            as `tuple` of two float representing the left anr right displacement
            values, which range from 0.0 to 1.0. The returned values reflect the
            controller state since the last :py:class:`~Rift.updateInputState`
            or :py:class:`~Rift.flip` call.

        """
        return libovr.getIndexTriggerValues(RIFT_CONTROLLER_TYPES[controller],
                                            deadzone)

    def getHandTriggerValues(self, controller='Touch', deadzone=False):
        """Get the values of the hand triggers.

        Parameters
        ----------
        controller : str
            Name of the controller to get hand trigger values. Possible values
            for `controller` are 'Touch', 'RTouch', 'LTouch', 'Object0',
            'Object1', 'Object2', and 'Object3'; the only devices with hand
            triggers the SDK manages. For additional controllers, use PsychPy's
            built-in event or hardware support.
        deadzone : bool
            Apply the deadzone to hand trigger values. This pre-filters stick
            input to apply a dead-zone where 0.0 will be returned if the trigger
            returns a displacement within 0.2746.

        Returns
        -------
        tuple
            Left and right hand trigger values. Displacements are represented
            as `tuple` of two float representing the left anr right displacement
            values, which range from 0.0 to 1.0. The returned values reflect the
            controller state since the last :py:class:`~Rift.updateInputState`
            or :py:class:`~Rift.flip` call.

        """
        return libovr.getHandTriggerValues(RIFT_CONTROLLER_TYPES[controller],
                                           deadzone)

    def getButtons(self, buttons, controller='Xbox', testState='continuous'):
        """Get button states from a controller.

        Returns `True` if any names specified to `buttons` reflect `testState`
        since the last :py:class:`~Rift.updateInputState` or
        :py:class:`~Rift.flip` call. If multiple button names are specified as a
        `list` or `tuple` to `buttons`, multiple button states are tested,
        returning `True` if all the buttons presently satisfy the `testState`.
        Note that not all controllers available share the same buttons. If a
        button is not available, this function will always return `False`.

        Parameters
        ----------
        buttons : `list` of `str` or `str`
            Buttons to test. Valid `buttons` names are 'A', 'B', 'RThumb',
            'RShoulder' 'X', 'Y', 'LThumb', 'LShoulder', 'Up', 'Down', 'Left',
            'Right', 'Enter', 'Back', 'VolUp', 'VolDown', and 'Home'. Names can
            be passed as a `list` to test multiple button states.
        controller : `str`
            Controller name.
        testState : `str`
            State to test. Valid values are:

            * **continuous** - Button is presently being held down.
            * **rising** or **pressed** - Button has been *pressed* since
              the last update.
            * **falling** or **released** - Button has been *released* since
              the last update.

        Returns
        -------
        tuple of bool, float
            Button state and timestamp in seconds the controller was polled.

        Examples
        --------

        Check if the 'Enter' button on the Oculus remote was released::

            isPressed, tsec = hmd.getButtons(['Enter'], 'Remote', 'falling')

        Check if the 'A' button was pressed on the touch controller::

            isPressed, tsec = hmd.getButtons(['A'], 'Touch', 'pressed')

        """
        if isinstance(buttons, str):  # single value
            return libovr.getButton(
                RIFT_CONTROLLER_TYPES[controller],
                RIFT_BUTTON_TYPES[buttons],
                testState)
        elif isinstance(buttons, (list, tuple,)):  # combine buttons
            buttonBits = 0x00000000
            for buttonName in buttons:
                buttonBits |= RIFT_BUTTON_TYPES[buttonName]
            return libovr.getButton(
                RIFT_CONTROLLER_TYPES[controller],
                buttonBits,
                testState)
        elif isinstance(buttons, int):  # using enums directly
            return libovr.getButton(
                RIFT_CONTROLLER_TYPES[controller],
                buttons,
                testState)
        else:
            raise ValueError("Invalid 'buttons' specified.")

    def getTouches(self, touches, controller='Touch', testState='continuous'):
        """Get touch states from a controller.

        Returns `True` if any names specified to `touches` reflect `testState`
        since the last :py:class:`~Rift.updateInputState` or
        :py:class:`~Rift.flip` call. If multiple button names are specified as a
        `list` or `tuple` to `touches`, multiple button states are tested,
        returning `True` if all the touches presently satisfy the `testState`.
        Note that not all controllers available support touches. If a touch is
        not supported or available, this function will always return `False`.

        Special states can be used for basic gesture recognition, such as
        'LThumbUp', 'RThumbUp', 'LIndexPointing', and 'RIndexPointing'.

        Parameters
        ----------
        touches : `list` of `str` or `str`
            Buttons to test. Valid `touches` names are 'A', 'B', 'RThumb',
            'RThumbRest' 'RThumbUp', 'RIndexPointing', 'LThumb', 'LThumbRest',
            'LThumbUp', 'LIndexPointing', 'X', and 'Y'. Names can be passed as a
            `list` to test multiple button states.
        controller : `str`
            Controller name.
        testState : `str`
            State to test. Valid values are:

            * **continuous** - User is touching something on the controller.
            * **rising** or **pressed** - User began touching something since
              the last call to `updateInputState`.
            * **falling** or **released** - User stopped touching something
              since the last call to `updateInputState`.

        Returns
        -------
        tuple of bool, float
            Touch state and timestamp in seconds the controller was polled.

        Examples
        --------

        Check if the 'Enter' button on the Oculus remote was released::

            isPressed, tsec = hmd.getButtons(['Enter'], 'Remote', 'falling')

        Check if the 'A' button was pressed on the touch controller::

            isPressed, tsec = hmd.getButtons(['A'], 'Touch', 'pressed')

        """
        if isinstance(touches, str):  # single value
            return libovr.getTouch(
                RIFT_CONTROLLER_TYPES[controller],
                RIFT_TOUCH_TYPES[touches],
                testState)
        elif isinstance(touches, (list, tuple,)):  # combine buttons
            touchBits = 0x00000000
            for buttonName in touches:
                touchBits |= RIFT_TOUCH_TYPES[buttonName]
            return libovr.getTouch(
                RIFT_CONTROLLER_TYPES[controller],
                touchBits,
                testState)
        elif isinstance(touches, int):  # using enums directly
            return libovr.getTouch(
                RIFT_CONTROLLER_TYPES[controller],
                touches,
                testState)
        else:
            raise ValueError("Invalid 'touches' specified.")

    def startHaptics(self, controller, frequency='low', amplitude=1.0):
        """Start haptic feedback (vibration).

        Vibration is constant at fixed frequency and amplitude. Vibration lasts
        2.5 seconds, so this function needs to be called more often than that
        for sustained vibration. Only controllers which support vibration can be
        used here.

        There are only two frequencies permitted 'high' and 'low', however,
        amplitude can vary from 0.0 to 1.0. Specifying `frequency`='off' stops
        vibration if in progress.

        Parameters
        ----------
        controller : str
            Name of the controller to vibrate.
        frequency : str
            Vibration frequency. Valid values are: 'off', 'low', or 'high'.
        amplitude : float
            Vibration amplitude in the range of [0.0 and 1.0]. Values outside
            this range are clamped.

        """
        libovr.setControllerVibration(
            RIFT_CONTROLLER_TYPES[controller],
            frequency,
            amplitude)

    def stopHaptics(self, controller):
        """Stop haptic feedback.

        Convenience function to stop controller vibration initiated by the last
        :py:class:`~Rift.vibrateController` call. This is the same as calling
        ``vibrateController(controller, frequency='off')``.

        Parameters
        ----------
        controller : str
            Name of the controller to stop vibrating.

        """
        libovr.setControllerVibration(
            RIFT_CONTROLLER_TYPES[controller], 'off', 0.0)

    @staticmethod
    def createHapticsBuffer(samples):
        """Create a new haptics buffer.

        A haptics buffer is object which stores vibration amplitude samples for
        playback through the Touch controllers. To play a haptics buffer, pass
        it to :py:meth:`submitHapticsBuffer`.

        Parameters
        ----------
        samples : array_like
            1-D array of amplitude samples, ranging from 0 to 1. Values outside
            of this range will be clipped. The buffer must not exceed
            `HAPTICS_BUFFER_SAMPLES_MAX` samples, any additional samples will be
            dropped.

        Returns
        -------
        LibOVRHapticsBuffer
            Haptics buffer object.

        Notes
        -----
        Methods `startHaptics` and `stopHaptics` cannot be used interchangeably
        with this function.

        Examples
        --------
        Create a haptics buffer where vibration amplitude ramps down over the
        course of playback::

            samples = np.linspace(
                1.0, 0.0, num=HAPTICS_BUFFER_SAMPLES_MAX-1, dtype=np.float32)
            hbuff = Rift.createHapticsBuffer(samples)

            # vibrate right Touch controller
            hmd.submitControllerVibration(CONTROLLER_TYPE_RTOUCH, hbuff)

        """
        if len(samples) > libovr.HAPTICS_BUFFER_SAMPLES_MAX:
            samples = samples[:libovr.HAPTICS_BUFFER_SAMPLES_MAX]

        return libovr.LibOVRHapticsBuffer(samples)

    def submitControllerVibration(self, controller, hapticsBuffer):
        """Submit a haptics buffer to begin controller vibration.

        Parameters
        ----------
        controller : str
            Name of controller to vibrate.
        hapticsBuffer : LibOVRHapticsBuffer
            Haptics buffer to playback.

        Notes
        -----
        Methods `startHaptics` and `stopHaptics` cannot be used interchangeably
        with this function.

        """
        libovr.submitControllerVibration(
            RIFT_CONTROLLER_TYPES[controller], hapticsBuffer)

    @staticmethod
    def createPose(pos=(0., 0., 0.), ori=(0., 0., 0., 1.)):
        """Create a new Rift pose object
        (:py:class:`~psychxr.libovr.LibOVRPose`).

        :py:class:`~psychxr.libovr.LibOVRPose` is used to represent a rigid body
        pose mainly for use with the PsychXR's LibOVR module. There are several
        methods associated with the object to manipulate the pose.

        This function exposes the :py:class:`~psychxr.libovr.LibOVRPose` class
        so you don't need to access it by importing `psychxr`.

        Parameters
        ----------
        pos : tuple, list, or ndarray of float
            Position vector/coordinate (x, y, z).
        ori : tuple, list, or ndarray of float
            Orientation quaternion (x, y, z, w).

        Returns
        -------
        :py:class:`~psychxr.libovr.LibOVRPose`
            Object representing a rigid body pose for use with LibOVR.

        """
        return libovr.LibOVRPose(pos, ori)

    @staticmethod
    def createBoundingBox(extents=None):
        """Create a new bounding box object
        (:py:class:`~psychxr.libovr.LibOVRBounds`).

        :py:class:`~psychxr.libovr.LibOVRBounds` represents an axis-aligned
        bounding box with dimensions defined by `extents`. Bounding boxes are
        primarily used for visibility testing and culling by `PsychXR`. The
        dimensions of the bounding box can be specified explicitly, or fitted
        to meshes by passing vertices to the
        :py:meth:`~psychxr.libovr.LibOVRBounds.fit` method after initialization.

        This function exposes the :py:class:`~psychxr.libovr.LibOVRBounds` class
        so you don't need to access it by importing `psychxr`.

        Parameters
        ----------
        extents : array_like or None
            Extents of the bounding box as (`mins`, `maxs`). Where `mins`
            (x, y, z) is the minimum and `maxs` (x, y, z) is the maximum extents
            of the bounding box in world units. If `None` is specified, the
            returned bounding box will be invalid. The bounding box can be later
            constructed using the :py:meth:`~psychxr.libovr.LibOVRBounds.fit`
            method or the :py:attr:`~psychxr.libovr.LibOVRBounds.extents`
            attribute.

        Returns
        -------
        `~psychxr.libovr.LibOVRBounds`
            Object representing a bounding box.

        Examples
        --------
        Add a bounding box to a pose::

            # create a 1 meter cube bounding box centered with the pose
            bbox = Rift.createBoundingBox(((-.5, -.5, -.5), (.5, .5, .5)))

            # create a pose and attach the bounding box
            modelPose = Rift.createPose()
            modelPose.boundingBox = bbox

        Perform visibility culling on the pose using the bounding box by
        using the :py:meth:`~psychxr.libovr.LibOVRBounds.isVisible` method::

            if hmd.isPoseVisible(modelPose):
                modelPose.draw()

        """
        return libovr.LibOVRBounds(extents)

    def isPoseVisible(self, pose):
        """Check if a pose object if visible to the present eye. This method can
        be used to perform visibility culling to avoid executing draw commands
        for objects that fall outside the FOV for the current eye buffer.

        If :py:attr:`~psychxr.libovr.LibOVRPose.boundingBox` has a valid
        bounding box object, this function will return `False` if all the box
        points fall completely to one side of the view frustum. If
        :py:attr:`~psychxr.libovr.LibOVRPose.boundingBox` is `None`, the point
        at :py:attr:`~psychxr.libovr.LibOVRPose.pos` is checked, returning
        `False` if it falls outside of the frustum. If the present buffer is not
        'left' or 'right', this function will always return `False`.

        Parameters
        ----------
        pose : :py:class:`~psychxr.libovr.LibOVRPose`
            Pose to test for visibility.

        Returns
        -------
        bool
            `True` if pose's bounding box or origin is outside of the view
            frustum.

        """
        if self.buffer == 'left' or self.buffer == 'mono':
            return pose.isVisible(libovr.EYE_LEFT)
        elif self.buffer == 'right':
            return pose.isVisible(libovr.EYE_RIGHT)

        return False

    def _updatePerfStats(self):
        """Update and process performance statistics obtained from LibOVR. This
        should be called at the beginning of each frame to get the stats of the
        last frame.

        This is called automatically when
        :py:meth:`~psychopy.visual.Rift._waitToBeginHmdFrame` is called at the
        beginning of each frame.

        """
        # update perf stats
        self._perfStats = libovr.getPerfStats()

        # if we have more >1 stat available, process the stats
        if self._perfStats.frameStatsCount > 0:
            recentStat = self._perfStats.frameStats[0]  # get the most recent
            # check for dropped frames since last call
            if self.warnAppFrameDropped and \
                    reportNDroppedFrames > self._lastAppDroppedFrameCount:
                appDroppedFrameCount = recentStat.appDroppedFrameCount
                if appDroppedFrameCount > self._lastAppDroppedFrameCount:
                    logging.warn(
                        'Application failed to meet deadline to submit frame '
                        'to HMD ({}).'.format(self._frameIndex))

                self._lastAppDroppedFrameCount = appDroppedFrameCount

                if reportNDroppedFrames == self._lastAppDroppedFrameCount:
                    logging.warn(
                        "Maximum number of dropped frames detected. I'll stop "
                        "warning you about them.")


# def _logCallback(level, msg):
#     """Callback function for log messages generated by LibOVR."""
#     if level == libovr.LOG_LEVEL_INFO:
#         logging.info(msg)
#     elif level == libovr.LOG_LEVEL_DEBUG:
#         logging.debug(msg)
#     elif level == libovr.LOG_LEVEL_ERROR:
#         logging.error(msg)
