#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes related to setting up windows for stereoscopy and VR."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy.visual.windowbuffer import WindowBuffer
# import psychopy.tools.gltools as gltools
import pyglet.gl as GL
import sys
import inspect

# Cache for stereo shaders stored here. Shaders are compiled once per session so
# you can switch between stereo modes quickly without recompiling the shaders.
stereoShaderCache = dict()

# Dictionary of supported stereo modes, populated when `registerStereoModes` is
# called. This happens automatically when this module is imported. Keys are
# names for the stereo mode and values are references to the classes. Names that
# appear in this dictionary can be specified to `stereo` when creating a window
# to use that stereo mode.
stereoModes = dict()


class BaseStereo(object):
    """Base class for stereo mode classes.

    A stereo mode class sets up a window for stereoscopy and handles any other
    requirements for the target display (eg. a stereoscope or HMD). You can pass
    options specific to a stereo mode for additional customization. Stereo modes
    can also add attributes to the window instance which are unique to the
    display type.

    Classes in this module which are subclasses of `BaseStereo` will be
    registered automatically as stereo modes that can be used when creating a
    window.

    """
    stereoModeName = None

    def __init__(self, win, config=None):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window being configured for stereoscopy.
        config : dict or None
            Configuration options for this stereo mode.
        """
        self.win = win
        self.config = config if config is None else dict()

        self._setupWindow()

    def _setupBuffers(self):
        """Setup window buffers for stereoscopy.
        """
        rect = (0, 0, self.win.frameBufferSize[0], self.win.frameBufferSize[1])

        self.win.windowBuffers['left'] = WindowBuffer(
            self.win, rect, 'left')
        self.win.windowBuffers['right'] = WindowBuffer(
            self.win, rect, 'right')

        if not self.win.useFBO:
            self.win.frameBuffers['left'] = GL.GL_BACK
            self.win.frameBuffers['right'] = GL.GL_NONE
        else:
            self.win.frameBuffers['left'] = self.win.frameBuffers['main']
            self.win.frameBuffers['right'] = GL.GL_NONE

        self.win.leftEyeBuffer = 'left'
        self.win.rightEyeBuffer = 'right'

    def _setupWindow(self):
        """Setup the associated window.

        This patches attributes into the Window object and configures the video
        mode if needed by the display type.

        """
        # patch in required methods and attributes to window class
        self.win._beginLeftEyeDraw = self._beginLeftEyeDraw
        self.win._beginRightEyeDraw = self._beginRightEyeDraw
        self.win.syncLights = self._syncLights

        self._setupBuffers()  # setup the window buffers

    def _beginLeftEyeDraw(self, clear=True):
        """Begin drawing to the left eye buffer.

        This call is used to ensure that all buffers associated with the left
        eye are properly configured. Override this method if you need to make
        additional calls other than just setting the buffer.

        Parameters
        ----------
        clear : bool
            Clear the eye buffer.

        """
        self.win.setBuffer(self.win.leftEyeBuffer, clear)

    def _beginRightEyeDraw(self, clear=True):
        """Begin drawing to the right eye buffer.

        This call is used to ensure that all buffers associated with the right
        eye are properly configured. Override this method if you need to make
        additional calls other than just setting the buffer.

        Parameters
        ----------
        clear : bool
            Clear the eye buffer.

        """
        self.win.setBuffer(self.win.rightEyeBuffer, clear)

    def _finalizeBuffers(self):
        """Finalize buffers before flipping the window back/front buffers.

        This function contains routines to build the final image that will be
        presented on the display. Called right before the window's back/front
        buffers are flipped. Any buffers that need to be passed to a swap chain
        should be done so here.

        """
        pass

    def _startOfFlip(self):
        """Called before swapping back buffer of the window to present the
        image."""
        return True

    def _endOfFlip(self, clear=True):
        """Called after window buffers have been flipped."""
        return True

    def _syncLights(self, syncWith=None, bufferNames=()):
        """Called when the user requests lighting to be synchronized across
        views. Override this if the stereo mode requires lighting configuration
        changes across multiple buffers or special handling for shaders.

        Parameters
        ----------
        syncWith : str or None
            Name of buffer whose lighting settings other buffers will be
            synchronized to use. If `None`, the current buffer's lighting
            settings will be used.
        bufferNames : str, tuple or list
            Name of or list of names of buffers to apply the lighting settings
            of `syncWith` to.

        """
        if syncWith is None:
            syncWith = self.win.buffer

        bufferToSync = self.win.windowBuffers[syncWith]

        if isinstance(bufferNames, str):
            bufferNames = (bufferNames,)

        for name in bufferNames:
            self.win.windowBuffers[name].lights = bufferToSync.lights
            self.win.windowBuffers[name].ambientLight = \
                bufferToSync.ambientLight

    def __del__(self):
        """Cleanup code for the stereo mode."""
        pass


class Spanned(BaseStereo):
    """Class for 'spanned' stereo displays.

    Side-by-side with aspect ratio preserved, this mode is used for presenting
    using 'extended desktop' mode across independent displays. Displays are
    assumed to be matched.

    """
    stereoModeName = 'spanned'

    def __init__(self, win, config):
        super(Spanned, self).__init__(win, config)

    def _setupBuffers(self):
        """Setup buffers for stereoscopy.
        """
        leftEyeRect = (0, 0, int(self.win.frameBufferSize[0] / 2),
                       self.win.frameBufferSize[1])
        rightEyeRect = (leftEyeRect[2], 0, leftEyeRect[2], leftEyeRect[3])

        self.win.windowBuffers['left'] = WindowBuffer(
            self.win, leftEyeRect, 'left')
        self.win.windowBuffers['right'] = WindowBuffer(
            self.win, rightEyeRect, 'right')

        self.win.frameBuffers['left'] = self.win.frameBuffers['back']
        self.win.frameBuffers['right'] = self.win.frameBuffers['back']

        self.win.leftEyeBuffer = 'left'
        self.win.rightEyeBuffer = 'right'

    def _setupWindow(self):
        """Setup the associated window."""
        # patch in required methods and attributes to window class
        self.win._beginLeftEyeDraw = self._beginLeftEyeDraw
        self.win._beginRightEyeDraw = self._beginRightEyeDraw

        self._setupBuffers()  # setup the window buffers


class Wheatstone(BaseStereo):
    """Class for 'Wheatstone-like' stereo displays.

    This mode is intended for Wheatstone-like stereoscopes which have mirrors in
    the optical path between the display and viewer. Similar to 'spanned' mode,
    but the output images are mirrored horizontally. Requires the display to be
    configured in 'extended desktop' mode.

    """
    stereoModeName = 'wheatstone'

    def __init__(self, win, config):
        super(Wheatstone, self).__init__(win, config)

    def _setupBuffers(self):
        """Setup buffers for stereoscopy.
        """
        leftEyeRect = (0, 0, int(self.win.frameBufferSize[0] / 2),
                       self.win.frameBufferSize[1])
        rightEyeRect = (leftEyeRect[2], 0, leftEyeRect[2], leftEyeRect[3])

        self.win.windowBuffers['left'] = WindowBuffer(
            self.win, leftEyeRect, 'left')
        self.win.windowBuffers['right'] = WindowBuffer(
            self.win, rightEyeRect, 'right')

        self.win.frameBuffers['left'] = self.win.frameBuffers['back']
        self.win.frameBuffers['right'] = self.win.frameBuffers['back']

        self.win.leftEyeBuffer = 'left'
        self.win.rightEyeBuffer = 'right'

    def _setupWindow(self):
        """Setup the associated window."""
        # patch in required methods and attributes to window class
        self.win._beginLeftEyeDraw = self._beginLeftEyeDraw
        self.win._beginRightEyeDraw = self._beginRightEyeDraw

        self._setupBuffers()  # setup the window buffers


class CrossFusion(BaseStereo):
    """Class for 'cross-fusion' stereo displays.

    Side-by-side with aspect ratio preserved, this mode is used for presenting
    using 'extended desktop' mode across independent displays. Displays are
    assumed to be matched.

    """
    stereoModeName = 'freeFuse'

    def __init__(self, win, config):
        super(CrossFusion, self).__init__(win, config)

    def _setupBuffers(self):
        """Setup buffers for stereoscopy.
        """
        w = int(self.win.frameBufferSize[0] / 2)
        leftEyeRect = (w, 0, w, self.win.frameBufferSize[1])
        rightEyeRect = (0, 0, leftEyeRect[2], leftEyeRect[3])

        self.win.windowBuffers['left'] = WindowBuffer(
            self.win, leftEyeRect, 'left')
        self.win.windowBuffers['right'] = WindowBuffer(
            self.win, rightEyeRect, 'right')

        self.win.frameBuffers['left'] = self.win.frameBuffers['back']
        self.win.frameBuffers['right'] = self.win.frameBuffers['back']

        self.win.leftEyeBuffer = 'left'
        self.win.rightEyeBuffer = 'right'


class QuadBuffered(BaseStereo):
    """Class for 'quad-buffered' stereo.

    Side-by-side with aspect ratio preserved, this mode is used for presenting
    using 'extended desktop' mode across independent displays. Displays are
    assumed to be matched.

    """
    stereoModeName = 'quad'

    def __init__(self, win, config):
        super(QuadBuffered, self).__init__(win, config)

    def _setupBuffers(self):
        """Setup buffers for stereoscopy.
        """
        rect = (0, 0, self.win.frameBufferSize[0], self.win.frameBufferSize[1])
        self.win.windowBuffers['left'] = WindowBuffer(self.win, rect, 'left')
        self.win.windowBuffers['right'] = WindowBuffer(self.win, rect, 'right')
        self.win.frameBuffers['left'] = GL.GL_BACK_LEFT
        self.win.frameBuffers['right'] = GL.GL_BACK_RIGHT

        self.win.leftEyeBuffer = 'left'
        self.win.rightEyeBuffer = 'right'


class Rift(BaseStereo):
    """Class for VR using the Oculus Rift (DK2, CV1, and S) HMD.

    """
    stereoModeName = 'rift'

    def __init__(self, win, config):
        super(Rift, self).__init__(win, config)


def registerStereoModes():
    """Finds stereo modes in this module and add them to `stereoModes`. This
    is needed to find stereo modes added with plugins. Usually this is called
    only once per session.

    """
    global stereoModes
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj):
            if issubclass(obj, BaseStereo) and hasattr(obj, 'stereoModeName'):
                if obj.stereoModeName is not None:
                    stereoModes[obj.stereoModeName] = obj


# register all stereo mode contained in the module
registerStereoModes()
