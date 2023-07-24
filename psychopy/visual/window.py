#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A class representing a window for displaying one or more stimuli"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).




import ctypes
import os
import sys
import weakref
import atexit
from itertools import product
from collections import deque

from psychopy.contrib.lazy_import import lazy_import
from psychopy import colors, event
import math
# from psychopy.clock import monotonicClock

# try to find avbin (we'll overload pyglet's load_library tool and then
# add some paths)
from ..colors import Color, colorSpaces
from .textbox2 import TextBox2


haveAvbin = False

# on windows try to load avbin now (other libs can interfere)
if sys.platform == 'win32':
    # make sure we also check in SysWOW64 if on 64-bit windows
    if 'C:\\Windows\\SysWOW64' not in os.environ['PATH']:
        os.environ['PATH'] += ';C:\\Windows\\SysWOW64'

    try:
        from pyglet.media import avbin
        haveAvbin = True
    except ImportError:
        haveAvbin = False
        # either avbin isn't installed or scipy.stats has been imported
        # (prevents avbin loading)
    except AttributeError:
        # avbin is not found, causing exception in pyglet 1.2??
        # (running psychopy 1.81 standalone on windows 7):
        #
        # File "C:\Program Files (x86)\PsychoPy2\lib\site-packages\
        #           pyglet\media\avbin.py", line 158, in <module>
        # av.avbin_get_version.restype = ctypes.c_int
        # AttributeError: 'NoneType' object has no attribute
        # 'avbin_get_version'
        haveAvbin = False
    except Exception:
        # WindowsError on some systems
        # AttributeError if using avbin5 from pyglet 1.2?
        haveAvbin = False

    # for pyglet 1.3
    if not haveAvbin:
        try:
            from pyglet.media.sources import avbin
            haveAvbin = True
        except ImportError:
            haveAvbin = False
        except AttributeError:
            haveAvbin = False
        except Exception:
            haveAvbin = False

import psychopy  # so we can get the __path__
from psychopy import core, platform_specific, logging, prefs, monitors
import psychopy.event
from . import backends, image

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import convertToPix
import psychopy.tools.viewtools as viewtools
import psychopy.tools.gltools as gltools
from .text import TextStim
from .grating import GratingStim
from .helpers import setColor
from . import globalVars

try:
    from PIL import Image
except ImportError:
    import Image

import numpy

from psychopy.core import rush

reportNDroppedFrames = 5  # stop raising warning after this

# import pyglet.gl, pyglet.window, pyglet.image, pyglet.font, pyglet.event
from . import shaders as _shaders
try:
    from pyglet import media
    havePygletMedia = True
except Exception:
    havePygletMedia = False

# lazy_import puts pygame into the namespace but delays import until needed
lazy_import(globals(), "import pygame")

DEBUG = False
IOHUB_ACTIVE = False
retinaContext = None  # only needed for retina-ready displays


class OpenWinList(list):
    """Class to keep keep track of windows that have been opened.

    Uses a list of weak references so that we don't stop the window
    being deleted.

    """
    def append(self, item):
        list.append(self, weakref.ref(item))

    def remove(self, item):
        for ref in self:
            obj = ref()
            if obj is None or item == obj:
                list.remove(self, ref)


openWindows = core.openWindows = OpenWinList()  # core needs this for wait()


class Window():
    """Used to set up a context in which to draw objects,
    using either `pyglet <http://www.pyglet.org>`_,
    `pygame <http://www.pygame.org>`_, or `glfw <https://www.glfw.org>`_.

    The pyglet backend allows multiple windows to be created, allows the user
    to specify which screen to use (if more than one is available, duh!) and
    allows movies to be rendered.

    The GLFW backend is a new addition which provides most of the same features
    as pyglet, but provides greater flexibility for complex display
    configurations.

    Pygame may still work for you but it's officially deprecated in this
    project (we won't be fixing pygame-specific bugs).

    """
    def __init__(self,
                 size=(800, 600),
                 pos=None,
                 color=(0, 0, 0),
                 colorSpace='rgb',
                 backgroundImage=None,
                 backgroundFit="cover",
                 rgb=None,
                 dkl=None,
                 lms=None,
                 fullscr=None,
                 allowGUI=None,
                 monitor=None,
                 bitsMode=None,
                 winType=None,
                 units=None,
                 gamma=None,
                 blendMode='avg',
                 screen=0,
                 viewScale=None,
                 viewPos=None,
                 viewOri=0.0,
                 waitBlanking=True,
                 allowStencil=False,
                 multiSample=False,
                 numSamples=2,
                 stereo=False,
                 name='window1',
                 title="PsychoPy",
                 checkTiming=True,
                 useFBO=False,
                 useRetina=True,
                 autoLog=True,
                 gammaErrorPolicy='raise',
                 bpc=(8, 8, 8),
                 depthBits=8,
                 stencilBits=8,
                 backendConf=None):
        """
        These attributes can only be set at initialization. See further down
        for a list of attributes which can be changed after initialization
        of the Window, e.g. color, colorSpace, gamma etc.

        Parameters
        ----------
        size : array-like of int
            Size of the window in pixels [x, y].
        pos : array-like of int
            Location of the top-left corner of the window on the screen [x, y].
        color : array-like of float
            Color of background as [r, g, b] list or single value. Each gun can
            take values between -1.0 and 1.0.
        fullscr : bool or None
            Create a window in 'full-screen' mode. Better timing can be achieved
            in full-screen mode.
        allowGUI : bool or None
            If set to False, window will be drawn with no frame and no buttons
            to close etc., use `None` for value from preferences.
        winType : str or None
            Set the window type or back-end to use. If `None` then PsychoPy will
            revert to user/site preferences.
        monitor : :class:`~psychopy.monitors.Monitor` or None
            The monitor to be used during the experiment. If `None` a default
            monitor profile will be used.
        units : str or None
            Defines the default units of stimuli drawn in the window (can be
            overridden by each stimulus). Values can be *None*, 'height' (of the
            window), 'norm' (normalised), 'deg', 'cm', 'pix'. See :ref:`units`
            for explanation of options.
        screen : int
            Specifies the physical screen that stimuli will appear on ('pyglet'
            and 'glfw' `winType` only). Values can be >0 if more than one screen
            is present.
        viewScale : array-like of float or None
            Scaling factors [x, y] to apply custom scaling to the current units
            of the :class:`~psychopy.visual.Window` instance.
        viewPos : array-like of float or None
            If not `None`, redefines the origin within the window, in the units
            of the window. Values outside the borders will be clamped to lie on
            the border.
        viewOri : float
            A single value determining the orientation of the view in degrees.
        waitBlanking : bool or None
            After a call to :py:attr:`~Window.flip()` should we wait for the
            blank before the script continues.
        bitsMode : bool
            DEPRECATED in 1.80.02. Use BitsSharp class from pycrsltd
            instead.
        checkTiming : bool
            Whether to calculate frame duration on initialization. Estimated
            duration is saved in :py:attr:`~Window.monitorFramePeriod`.
        allowStencil : bool
            When set to `True`, this allows operations that use the OpenGL
            stencil buffer (notably, allowing the
            :class:`~psychopy.visual.Aperture` to be used).
        multiSample : bool
            If `True` and your graphics driver supports multisample buffers,
            multiple color samples will be taken per-pixel, providing an
            anti-aliased image through spatial filtering. This setting cannot
            be changed after opening a window. Only works with 'pyglet' and
            'glfw' `winTypes`, and `useFBO` is `False`.
        numSamples : int
            A single value specifying the number of samples per pixel if
            multisample is enabled. The higher the number, the better the
            image quality, but can delay frame flipping. The largest number of
            samples is determined by ``GL_MAX_SAMPLES``, usually 16 or 32 on
            newer hardware, will crash if number is invalid.
        stereo : bool
            If `True` and your graphics card supports quad buffers then
            this will be enabled. You can switch between left and right-eye
            scenes for drawing operations using
            :py:attr:`~psychopy.visual.Window.setBuffer()`.
        title : str
            Name of the Window according to your Operating System. This is
            the text which appears on the title sash.
        useRetina : bool
            In PsychoPy >1.85.3 this should always be `True` as pyglet
            (or Apple) no longer allows us to create a non-retina display.
            NB when you use Retina display the initial win size
            request will be in the larger pixels but subsequent use of
            ``units='pix'`` should refer to the tiny Retina pixels. Window.size
            will give the actual size of the screen in Retina pixels.
        gammaErrorPolicy: str
            If `raise`, an error is raised if the gamma table is unable to be
            retrieved or set. If `warn`, a warning is raised instead. If
            `ignore`, neither an error nor a warning are raised.
        bpc : array_like or int
            Bits per color (BPC) for the back buffer as a tuple to specify
            bit depths for each color channel separately (red, green, blue), or
            a single value to set all of them to the same value. Valid values
            depend on the output color depth of the display (screen) the window
            is set to use and the system graphics configuration. By default, it
            is assumed the display has 8-bits per color (8, 8, 8). Behaviour may
            be undefined for non-fullscreen windows, or if multiple screens are
            attached with varying color output depths.
        depthBits : int
            Back buffer depth bits. Default is 8, but can be set higher (eg. 24)
            if drawing 3D stimuli to minimize artifacts such a 'Z-fighting'.
        stencilBits : int
            Back buffer stencil bits. Default is 8.
        backendConf : dict or None
            Additional options to pass to the backend specified by `winType`.
            Each backend may provide unique functionality which may not be
            available across all of them. This allows you to pass special
            configuration options to a specific backend to configure the
            feature.

        Notes
        -----
        * Some parameters (e.g. units) can now be given default values in the
          user/site preferences and these will be used if `None` is given here.
          If you do specify a value here it will take precedence over
          preferences.

        Attributes
        ----------
        size : array-like (float)
            Dimensions of the window's drawing area/buffer in pixels [w, h].
        monitorFramePeriod : float
            Refresh rate of the display if ``checkTiming=True`` on window
            instantiation.

        """
        # what local vars are defined (these are the init params) for use by
        # __repr__
        self._initParams = dir()
        self._closed = False
        self.backend = None  # this will be set later
        for unecess in ['self', 'checkTiming', 'rgb', 'dkl', ]:
            self._initParams.remove(unecess)

        # Check autoLog value
        if autoLog not in (True, False):
            raise ValueError(
                'autoLog must be either True or False for visual.Window')

        self.autoLog = False  # to suppress log msg during init
        self.name = name
        self.clientSize = numpy.array(size, int)  # size of window, not buffer
        # size of the window when restored (not fullscreen)
        self._windowedSize = self.clientSize.copy()

        self.pos = pos
        # this will get overridden once the window is created
        self.winHandle = None
        self.useFBO = useFBO
        self.useRetina = useRetina and sys.platform == 'darwin'

        if gammaErrorPolicy not in ['raise', 'warn', 'ignore']:
            raise ValueError('Unexpected `gammaErrorPolicy`')
        self.gammaErrorPolicy = gammaErrorPolicy

        self._toLog = []
        self._toCall = []
        # settings for the monitor: local settings (if available) override
        # monitor
        # if we have a monitors.Monitor object (psychopy 0.54 onwards)
        # convert to a Monitor object
        if not monitor:
            self.monitor = monitors.Monitor('__blank__', autoLog=autoLog)
        elif isinstance(monitor, str):
            self.monitor = monitors.Monitor(monitor, autoLog=autoLog)
        elif hasattr(monitor, 'keys'):
            # convert into a monitor object
            self.monitor = monitors.Monitor('temp', currentCalib=monitor,
                                            verbose=False, autoLog=autoLog)
        else:
            self.monitor = monitor

        # otherwise monitor will just be a dict
        self.scrWidthCM = self.monitor.getWidth()
        self.scrDistCM = self.monitor.getDistance()

        scrSize = self.monitor.getSizePix()
        if scrSize is None:
            self.scrWidthPIX = None
        else:
            self.scrWidthPIX = scrSize[0]

        if fullscr is None:
            fullscr = prefs.general['fullscr']
        self._isFullScr = fullscr

        self.units = units

        if allowGUI is None:
            allowGUI = prefs.general['allowGUI']
        self.allowGUI = allowGUI

        self.screen = screen
        self.stereo = stereo  # use quad buffer if requested (and if possible)

        # enable multisampling
        self.multiSample = multiSample
        self.numSamples = numSamples

        # load color conversion matrices
        self.dkl_rgb = self.monitor.getDKL_RGB()
        self.lms_rgb = self.monitor.getLMS_RGB()

        # Projection and view matrices, these can be lists if multiple views are
        # being used.
        # NB - attribute checks needed for Rift compatibility
        if not hasattr(self, '_viewMatrix'):
            self._viewMatrix = numpy.identity(4, dtype=numpy.float32)

        if not hasattr(self, '_projectionMatrix'):
            self._projectionMatrix = viewtools.orthoProjectionMatrix(
                -1, 1, -1, 1, -1, 1, dtype=numpy.float32)

        # set screen color
        self.__dict__['colorSpace'] = colorSpace
        if rgb is not None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. "
                            "Please use color and colorSpace args instead")
            color = rgb
            colorSpace = 'rgb'
        elif dkl is not None:
            logging.warning("Use of dkl arguments to stimuli are deprecated. "
                            "Please use color and colorSpace args instead")
            color = dkl
            colorSpace = 'dkl'
        elif lms is not None:
            logging.warning("Use of lms arguments to stimuli are deprecated. "
                            "Please use color and colorSpace args instead")
            color = lms
            colorSpace = 'lms'
        self.setColor(color, colorSpace=colorSpace, log=False)

        self.allowStencil = allowStencil
        # check whether FBOs are supported
        if blendMode == 'add' and not self.useFBO:
            logging.warning('User requested a blendmode of "add" but '
                            'window requires useFBO=True')
            # resort to the simpler blending without float rendering
            self.__dict__['blendMode'] = 'avg'
        else:
            self.__dict__['blendMode'] = blendMode
            # then set up gl context and then call self.setBlendMode

        # setup context and openGL()
        if winType is None:  # choose the default windowing
            winType = "pyglet"
        self.winType = winType

        # setup the context

        # backend specific options are passed as a dictionary
        backendConf = backendConf if backendConf is not None else {}

        # Here we make sure all the open windows use the same `winType` and have
        # context sharing enabled. The context to share is passed as an option
        # to `backendConf`.
        if openWindows:
            primaryWindow = openWindows[0]()  # resolve ref
            if primaryWindow.winType != self.winType:
                raise ValueError(
                    "Only one kind of `winType` can be used per session.")

            # Allow for context sharing, only used by the GLFW backend, Pyglet
            # uses `shadow_window` by default here so we don't need to worry
            # about it.
            backendConf['share'] = self

        if not isinstance(backendConf, dict):  # type check on options
            raise TypeError(
                'Object passed to `backendConf` must be type `dict`.')

        # augment settings with dedicated attributes
        backendConf['bpc'] = bpc
        backendConf['depthBits'] = depthBits
        backendConf['stencilBits'] = stencilBits

        # get the backend, pass the options to it
        self.backend = backends.getBackend(win=self, backendConf=backendConf)

        self.winHandle = self.backend.winHandle
        global GL
        GL = self.backend.GL

        # check whether shaders are supported
        # also will need to check for ARB_float extension,
        # but that should be done after context is created
        self._haveShaders = self.backend.shadersSupported

        self._setupGL()

        self.blendMode = self.blendMode

        # now that we have a window handle, set title
        self.title = title

        # parameters for transforming the overall view
        self.viewScale = val2array(viewScale)
        if self.viewPos is not None and self.units is None:
            raise ValueError('You must define the window units to use viewPos')
        self.viewPos = val2array(viewPos, withScalar=False)
        self.viewOri = float(viewOri)
        if self.viewOri != 0. and self.viewPos is not None:
            msg = "Window: viewPos & viewOri are currently incompatible"
            raise NotImplementedError(msg)

        # scaling factor for HiDPI displays, `None` until initialized
        self._contentScaleFactor = None

        # Code to allow iohub to know id of any psychopy windows created
        # so kb and mouse event filtering by window id can be supported.
        #
        # If an iohubConnection is active, give this window os handle to
        # to the ioHub server. If windows were already created before the
        # iohub was active, also send them to iohub.
        #
        if IOHUB_ACTIVE:
            from psychopy.iohub.client import ioHubConnection as ioconn
            if ioconn.ACTIVE_CONNECTION:
                from psychopy.iohub.client import windowInfoDict
                win_infos = []
                win_handles = []
                for w in openWindows:
                    winfo = windowInfoDict(w())
                    win_infos.append(winfo)
                    win_handles.append(w()._hw_handle)

                if self._hw_handle not in win_handles:
                    winfo = windowInfoDict(self)
                    win_infos.append(winfo)
                    win_handles.append(self._hw_handle)
                ioconn.ACTIVE_CONNECTION.registerWindowHandles(*win_infos)
                self.backend.onMoveCallback = ioconn.ACTIVE_CONNECTION.updateWindowPos

        # near and far clipping planes
        self._nearClip = 0.1
        self._farClip = 100.0

        # 3D rendering related attributes
        self.frontFace = 'ccw'
        self.depthFunc = 'less'
        self.depthMask = False
        self.cullFace = False
        self.cullFaceMode = 'back'
        self.draw3d = False

        # gl viewport and scissor
        self._viewport = self._scissor = None  # set later

        # scene light sources
        self._lights = []
        self._useLights = False
        self._nLights = 0
        self._ambientLight = numpy.array([0.0, 0.0, 0.0, 1.0],
                                         dtype=numpy.float32)

        # stereo rendering settings, set later by the user
        self._eyeOffset = 0.0
        self._convergeOffset = 0.0

        # gamma
        self.bits = None  # this may change in a few lines time!
        self.__dict__['gamma'] = gamma
        self._setupGamma(gamma)

        # setup bits++ if needed. NB The new preferred method is for this
        # to be handled by the bits class instead. (we pass the Window to
        # bits not passing bits to the window)
        if bitsMode is not None:
            logging.warn("Use of Window(bitsMode=******) is deprecated. See "
                         "the Coder>Demos>Hardware demo for new methods")
            self.bitsMode = bitsMode  # could be [None, 'fast', 'slow']
            logging.warn("calling Window(...,bitsMode='fast') is deprecated."
                         " XXX provide further info")
            from psychopy.hardware.crs.bits import BitsPlusPlus
            self.bits = self.interface = BitsPlusPlus(self)
            self.haveBits = True
            if (hasattr(self.monitor, 'linearizeLums') or
                    hasattr(self.monitor, 'lineariseLums')):
                # rather than a gamma value we could use bits++ and provide a
                # complete linearised lookup table using
                # monitor.linearizeLums(lumLevels)
                self.__dict__['gamma'] = None

        self.frameClock = core.Clock()  # from psycho/core
        self.frames = 0  # frames since last fps calc
        self.movieFrames = []  # list of captured frames (Image objects)

        self.recordFrameIntervals = False
        # Be able to omit the long timegap that follows each time turn it off
        self.recordFrameIntervalsJustTurnedOn = False
        self.nDroppedFrames = 0
        self.frameIntervals = []
        self._frameTimes = deque(maxlen=1000)  # 1000 keeps overhead low

        self._toDraw = []
        self._heldDraw = []
        self._toDrawDepths = []
        self._eventDispatchers = []

        self.lastFrameT = core.getTime()
        self.waitBlanking = waitBlanking

        # set the swap interval if using GLFW
        if self.winType == 'glfw':
            self.backend.setSwapInterval(int(waitBlanking))

        self.refreshThreshold = 1.0  # initial val needed by flip()

        # store editable stimuli
        self._editableChildren = []
        self._currentEditableRef = None
        # store draggable stimuli
        self.currentDraggable = None

        # splash screen
        self._splashTextbox = None  # created on first use
        self._showSplash = False
        self.resetViewport()  # set viewport to full window size

        # over several frames with no drawing
        self._monitorFrameRate = None
        # for testing when to stop drawing a stim:
        self.monitorFramePeriod = 0.0
        if checkTiming:
            self._monitorFrameRate = self.getActualFrameRate()

        if self._monitorFrameRate is not None:
            self.monitorFramePeriod = 1.0 / self._monitorFrameRate
        else:
            self.monitorFramePeriod = 1.0 / 60  # assume a flat panel?
        self.refreshThreshold = self.monitorFramePeriod * 1.2
        openWindows.append(self)

        self.autoLog = autoLog
        if self.autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

        # Make sure this window's close method is called when exiting, even in
        # the event of an error we should be able to restore the original gamma
        # table. Note that a reference to this window object will live in this
        # function, preventing it from being garbage collected.
        def close_on_exit():
            if self._closed is False:
                self.close()

        atexit.register(close_on_exit)

        self._mouse = event.Mouse(win=self)
        self.backgroundImage = backgroundImage
        self.backgroundFit = backgroundFit
        if hasattr(self.backgroundImage, "draw"):
            self.backgroundImage.draw()

    def __del__(self):
        if self._closed is False:
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self._closed:
            self.close()

    def __str__(self):
        className = 'Window'
        paramStrings = []
        for param in self._initParams:
            if hasattr(self, param):
                paramStrings.append("%s=%s" %
                                    (param, repr(getattr(self, param))))
            else:
                paramStrings.append("%s=UNKNOWN" % (param))
        # paramStrings = ["%s=%s" %(param, getattr(self, param))
        #                 for param in self._initParams]
        params = ", ".join(paramStrings)
        s = "%s(%s)" % (className, params)
        return s

    @attributeSetter
    def title(self, value):
        self.__dict__['title'] = value
        if hasattr(self.winHandle, "set_caption"):
            # Pyglet backend
            self.winHandle.set_caption(value)
        elif hasattr(self.winHandle, "SetWindowTitle"):
            # GLFW backend
            self.winHandle.SetWindowTitle(value)
        else:
            # Unknown backend
            logging.warning(f"Cannot set Window title in backend {self.winType}")

    @attributeSetter
    def units(self, value):
        """*None*, 'height' (of the window), 'norm', 'deg', 'cm', 'pix'
        Defines the default units of stimuli initialized in the window.
        I.e. if you change units, already initialized stimuli won't change
        their units.

        Can be overridden by each stimulus, if units is specified on
        initialization.

        See :ref:`units` for explanation of options.

        """
        if value is None:
            value = prefs.general['units']
        self.__dict__['units'] = value

    def setUnits(self, value, log=True):
        setAttribute(self, 'units', value, log=log)

    @attributeSetter
    def viewPos(self, value):
        """The origin of the window onto which stimulus-objects are drawn.

        The value should be given in the units defined for the window. NB:
        Never change a single component (x or y) of the origin, instead replace
        the viewPos-attribute in one shot, e.g.::

            win.viewPos = [new_xval, new_yval]  # This is the way to do it
            win.viewPos[0] = new_xval  # DO NOT DO THIS! Errors will result.

        """
        self.__dict__['viewPos'] = value
        if value is not None:
            # let setter take care of normalisation
            setattr(self, '_viewPosNorm', value)

    @attributeSetter
    def _viewPosNorm(self, value):
        """Normalised value of viewPos, hidden from user view."""
        # first convert to pixels, then normalise to window units
        viewPos_pix = convertToPix([0, 0], list(value),
                                   units=self.units, win=self)[:2]
        viewPos_norm = viewPos_pix / (self.size / 2.0)
        # Clip to +/- 1; should going out-of-window raise an exception?
        viewPos_norm = numpy.clip(viewPos_norm, a_min=-1., a_max=1.)
        self.__dict__['_viewPosNorm'] = viewPos_norm

    def setViewPos(self, value, log=True):
        setAttribute(self, 'viewPos', value, log=log)

    @attributeSetter
    def fullscr(self, value):
        """Set whether fullscreen mode is `True` or `False` (not all backends
        can toggle an open window).
        """
        self.backend.setFullScr(value)
        self.__dict__['fullscr'] = value
        self._isFullScr = value

    @attributeSetter
    def waitBlanking(self, value):
        """After a call to :py:attr:`~Window.flip()` should we wait for the
        blank before the script continues.

        """
        self.__dict__['waitBlanking'] = value

    @attributeSetter
    def recordFrameIntervals(self, value):
        """Record time elapsed per frame.

        Provides accurate measures of frame intervals to determine
        whether frames are being dropped. The intervals are the times between
        calls to :py:attr:`~Window.flip()`. Set to `True` only during the
        time-critical parts of the script. Set this to `False` while the screen
        is not being updated, i.e., during any slow, non-frame-time-critical
        sections of your code, including inter-trial-intervals,
        ``event.waitkeys()``, ``core.wait()``, or ``image.setImage()``.

        Examples
        --------
        Enable frame interval recording, successive frame intervals will be
        stored::

            win.recordFrameIntervals = True

        Frame intervals can be saved by calling the
        :py:attr:`~Window.saveFrameIntervals` method::

            win.saveFrameIntervals()

        """
        # was off, and now turning it on
        self.recordFrameIntervalsJustTurnedOn = bool(
            not self.recordFrameIntervals and value)
        self.__dict__['recordFrameIntervals'] = value
        self.frameClock.reset()

    def setRecordFrameIntervals(self, value=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'recordFrameIntervals', value, log)

    def saveFrameIntervals(self, fileName=None, clear=True):
        """Save recorded screen frame intervals to disk, as comma-separated
        values.

        Parameters
        ----------
        fileName : *None* or str
            *None* or the filename (including path if necessary) in which to
            store the data. If None then 'lastFrameIntervals.log' will be used.
        clear : bool
            Clear buffer frames intervals were stored after saving. Default is
            `True`.

        """
        if not fileName:
            fileName = 'lastFrameIntervals.log'
        if len(self.frameIntervals):
            intervalStr = str(self.frameIntervals)[1:-1]
            f = open(fileName, 'w')
            f.write(intervalStr)
            f.close()
        if clear:
            self.frameIntervals = []
            self.frameClock.reset()

    def _setCurrent(self):
        """Make this window's OpenGL context current.

        If called on a window whose context is current, the function will return
        immediately. This reduces the number of redundant calls if no context
        switch is required. If ``useFBO=True``, the framebuffer is bound after
        the context switch.

        """
        # don't configure if we haven't changed context
        if not self.backend.setCurrent():
            return

        # if we are using an FBO, bind it
        if hasattr(self, 'frameBuffer'):
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT,
                                    self.frameBuffer)
            GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
            GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)

            # NB - check if we need these
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        # set these to match the current window or buffer's settings
        fbw, fbh = self.frameBufferSize
        self.viewport = self.scissor = [0, 0, fbw, fbh]
        self.scissorTest = True

        # apply the view transforms for this window
        #self.applyEyeTransform()

    def onResize(self, width, height):
        """A default resize event handler.

        This default handler updates the GL viewport to cover the entire
        window and sets the ``GL_PROJECTION`` matrix to be orthogonal in
        window space.  The bottom-left corner is (0, 0) and the top-right
        corner is the width and height of the :class:`~psychopy.visual.Window`
        in pixels.

        Override this event handler with your own to create another
        projection, for example in perspective.
        """
        # this has to be external so that pyglet can use it too without
        # circular referencing
        self.backend.onResize(width, height)

    def logOnFlip(self, msg, level, obj=None):
        """Send a log message that should be time-stamped at the next
        :py:attr:`~Window.flip()` command.

        Parameters
        ----------
        msg : str
            The message to be logged.
        level : int
            The level of importance for the message.
        obj : object, optional
            The python object that might be associated with this message if
            desired.

        """
        self._toLog.append({'msg': msg, 'level': level, 'obj': repr(obj)})

    def callOnFlip(self, function, *args, **kwargs):
        """Call a function immediately after the next :py:attr:`~Window.flip()`
        command.

        The first argument should be the function to call, the following args
        should be used exactly as you would for your normal call to the
        function (can use ordered arguments or keyword arguments as normal).

        e.g. If you have a function that you would normally call like this::

            pingMyDevice(portToPing, channel=2, level=0)

        then you could call :py:attr:`~Window.callOnFlip()` to have the function
        call synchronized with the frame flip like this::

            win.callOnFlip(pingMyDevice, portToPing, channel=2, level=0)

        """
        self._toCall.append({'function': function,
                             'args': args,
                             'kwargs': kwargs})

    def timeOnFlip(self, obj, attrib):
        """Retrieves the time on the next flip and assigns it to the `attrib`
        for this `obj`.

        Parameters
        ----------
        obj : dict or object
            A mutable object (usually a dict of class instance).
        attrib : str
            Key or attribute of `obj` to assign the flip time to.

        Examples
        --------
        Assign time on flip to the ``tStartRefresh`` key of ``myTimingDict``::

            win.getTimeOnFlip(myTimingDict, 'tStartRefresh')

        """
        self.callOnFlip(self._assignFlipTime, obj, attrib)

    def getFutureFlipTime(self, targetTime=0, clock=None):
        """The expected time of the next screen refresh. This is currently
        calculated as win._lastFrameTime + refreshInterval

        Parameters
        -----------
        targetTime: float
            The delay *from now* for which you want the flip time. 0 will give the
            because that the earliest we can achieve. 0.15 will give the schedule
            flip time that gets as close to 150 ms as possible
        clock : None, 'ptb', 'now' or any Clock object
            If True then the time returned is compatible with ptb.GetSecs()
        verbose: bool
            Set to True to view the calculations along the way
        """
        baseClock = logging.defaultClock
        if not self.monitorFramePeriod:
            raise AttributeError("Cannot calculate nextFlipTime due to unknown "
                                 "monitorFramePeriod")
        lastFlip = self._frameTimes[-1]  # unlike win.lastFrameTime this is always on
        timeNext = lastFlip + self.monitorFramePeriod
        now = baseClock.getTime()
        if (now + targetTime) > timeNext:  # target is more than 1 frame in future
            extraFrames = math.ceil((now + targetTime - timeNext)/self.monitorFramePeriod)
            thisT = timeNext + extraFrames*self.monitorFramePeriod
        else:
            thisT = timeNext
        # convert back to target clock timebase
        if clock=='ptb':  # add back the lastResetTime (that's the clock difference)
            output = thisT + baseClock.getLastResetTime()
        elif clock=='now':  # time from now is easy!
            output = thisT - now
        elif clock:
            output = thisT + baseClock.getLastResetTime() - clock.getLastResetTime()
        else:
            output = thisT

        return output

    def _assignFlipTime(self, obj, attrib):
        """Helper function to assign the time of last flip to the obj.attrib

        Parameters
        ----------
        obj : dict or object
            A mutable object (usually a dict of class instance).
        attrib : str
            Key or attribute of ``obj`` to assign the flip time to.

        """
        if hasattr(obj, attrib):
            setattr(obj, attrib, self._frameTime)
        elif isinstance(obj, dict):
            obj[attrib] = self._frameTime
        else:
            raise TypeError("Window.getTimeOnFlip() should be called with an "
                            "object and its attribute or a dict and its key. "
                            "In this case it was called with obj={}"
                            .format(repr(obj)))

    def _cleanEditables(self):
        """
        Make sure there are no dead refs in the editables list
        """
        for ref in self._editableChildren:
            obj = ref()
            if obj is None:
                self._editableChildren.remove(ref)

    @property
    def currentEditable(self):
        """The editable (Text?) object that currently has key focus"""
        if self._currentEditableRef:
            return self._currentEditableRef()

    @currentEditable.setter
    def currentEditable(self, editable):
        """Keeps the current editable stored as a weak ref"""
        # Ensure that item is added to editables list
        self.addEditable(editable)

        # Set the editable as the current editable stim in the window
        eRef = None
        for ref in weakref.getweakrefs(editable):
            if ref in self._editableChildren:
                eRef = ref
                break
        if eRef:
            self._currentEditableRef = eRef

    def addEditable(self, editable):
        """Adds an editable element to the screen (something to which
        characters can be sent with meaning from the keyboard).

        The current editable object receiving chars is Window.currentEditable

        :param editable:
        :return:
        """
        # Ignore if object is not editable
        if not hasattr(editable, "editable"):
            return
        if not editable.editable:
            return
        # If editable is already present do nothing
        eRef = False
        for ref in weakref.getweakrefs(editable):
            if ref in self._editableChildren:
                eRef = ref
                break
            
        if eRef is False:
            eRef = weakref.ref(editable)
            # If editable is not already present, add it to the editables list
            self._editableChildren.append(eRef)

        # If this is the first editable obj then make it the current
        if len(self._editableChildren) == 1:
            self._currentEditableRef = eRef
        # Clean editables list
        self._cleanEditables()

    def removeEditable(self, editable):
        # If editable is present, remove it from editables list
        for ref in weakref.getweakrefs(editable):
            if ref in self._editableChildren:
                # If editable was current, move on to next current
                if self.currentEditable == editable:
                    self.nextEditable()
                self._editableChildren.remove(ref)
                return True
            else:
                logging.warning(f"Request to remove editable object {editable} could not be completed as weakref "
                                f"to this object could not be found in window.")
        # Clean editables list
        self._cleanEditables()

        return False
    
    def nextEditable(self):
        """Moves focus of the cursor to the next editable window"""
        # Clean editables list
        self._cleanEditables()
        # Progress
        if self.currentEditable is None:
            if len(self._editableChildren):
                self._currentEditableRef = self._editableChildren[0]            
        else:
            for ref in weakref.getweakrefs(self.currentEditable):
                if ref in self._editableChildren:
                    cei = self._editableChildren.index(ref)
                    nei = cei+1
                    if nei >= len(self._editableChildren):
                        nei=0
                    self._currentEditableRef = self._editableChildren[nei]            
        return self.currentEditable

    @classmethod
    def dispatchAllWindowEvents(cls):
        """
        Dispatches events for all pyglet windows. Used by iohub 2.0
        psychopy kb event integration.
        """
        Window.backend.dispatchEvents()

    def clearAutoDraw(self):
        """
        Remove all autoDraw components, meaning they get autoDraw set to False and are not
        added to any list (as in .stashAutoDraw)
        """
        for thisStim in self._toDraw.copy():
            # set autoDraw to False
            thisStim.autoDraw = False

    def stashAutoDraw(self):
        """
        Put autoDraw components on 'hold', meaning they get autoDraw set to False but
        are added to an internal list to be 'released' when .releaseAutoDraw is called.
        """
        for thisStim in self._toDraw.copy():
            # set autoDraw to False
            thisStim.autoDraw = False
            # add stim to held list
            self._heldDraw.append(thisStim)

    def retrieveAutoDraw(self):
        """
        Add all stimuli which are on 'hold' back into the autoDraw list, and clear the
        hold list.
        """
        for thisStim in self._heldDraw:
            # set autoDraw to True
            thisStim.autoDraw = True
        # clear list
        self._heldDraw = []

    def flip(self, clearBuffer=True):
        """Flip the front and back buffers after drawing everything for your
        frame. (This replaces the :py:attr:`~Window.update()` method, better
        reflecting what is happening underneath).

        Parameters
        ----------
        clearBuffer : bool, optional
            Clear the draw buffer after flipping. Default is `True`.

        Returns
        -------
        float or None
            Wall-clock time in seconds the flip completed. Returns `None` if
            :py:attr:`~Window.waitBlanking` is `False`.

        Notes
        -----
        * The time returned when :py:attr:`~Window.waitBlanking` is `True`
          corresponds to when the graphics driver releases the draw buffer to
          accept draw commands again. This time is usually close to the vertical
          sync signal of the display.

        Examples
        --------

        Results in a clear screen after flipping::

            win.flip(clearBuffer=True)

        The screen is not cleared (so represent the previous screen)::

            win.flip(clearBuffer=False)

        """
        # draw message/splash if needed
        if self._showSplash:
            self._splashTextbox.draw()

        if self._toDraw:
            for thisStim in self._toDraw:
                # Draw
                thisStim.draw()
                # Handle dragging
                if getattr(thisStim, "draggable", False):
                    thisStim.doDragging()
        else:
            self.backend.setCurrent()

            # set these to match the current window or buffer's settings
            self.viewport = self.scissor = \
                (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])
            if not self.scissorTest:
                self.scissorTest = True

            # clear the projection and modelview matrix for FBO blit
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glOrtho(-1, 1, -1, 1, -1, 1)
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()

        # disable lighting
        self.useLights = False

        # Check for mouse clicks on editables
        if hasattr(self, '_editableChildren'):
            # Make sure _editableChildren has actually been created
            editablesOnScreen = []
            for thisObj in self._editableChildren:
                # Iterate through editables and decide which one should have focus
                if isinstance(thisObj, weakref.ref):
                    # Solidify weakref if necessary
                    thisObj = thisObj()
                if thisObj is None:
                    continue
                if isinstance(thisObj.autoDraw, (bool, int, float)):
                    # Store whether this editable is on screen
                    editablesOnScreen.append(thisObj.autoDraw)
                else:
                    editablesOnScreen.append(False)
                if self._mouse.isPressedIn(thisObj):
                    # If editable was clicked on, give it focus
                    self.currentEditable = thisObj
            # If there is only one editable on screen, make sure it starts off with focus
            if sum(editablesOnScreen) == 1:
                self.currentEditable = self._editableChildren[editablesOnScreen.index(True)]()

        flipThisFrame = self._startOfFlip()
        if self.useFBO and flipThisFrame:
            self.draw3d = False  # disable 3d drawing
            self._prepareFBOrender()
            # need blit the framebuffer object to the actual back buffer

            # unbind the framebuffer as the render target
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, 0)
            GL.glDisable(GL.GL_BLEND)
            stencilOn = self.stencilTest
            self.stencilTest = False

            if self.bits is not None:
                self.bits._prepareFBOrender()

            # before flipping need to copy the renderBuffer to the
            # frameBuffer
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.frameTexture)
            GL.glColor3f(1.0, 1.0, 1.0)  # glColor multiplies with texture
            GL.glColorMask(True, True, True, True)

            self._renderFBO()

            GL.glEnable(GL.GL_BLEND)
            self._finishFBOrender()

        # call this before flip() whether FBO was used or not
        self._afterFBOrender()

        self.backend.swapBuffers(flipThisFrame)

        if self.useFBO and flipThisFrame:
            # set rendering back to the framebuffer object
            GL.glBindFramebufferEXT(
                GL.GL_FRAMEBUFFER_EXT, self.frameBuffer)
            GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
            GL.glDrawBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
            # set to no active rendering texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            if stencilOn:
                self.stencilTest = True

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
        self._frameTime = now = logging.defaultClock.getTime()
        self._frameTimes.append(self._frameTime)

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

        # Draw background (if present) for next frame
        if hasattr(self.backgroundImage, "draw"):
            self.backgroundImage.draw()

        #    If self.waitBlanking is True, then return the time that
        # GL.glFinish() returned, set as the 'now' variable. Otherwise
        # return None as before
        #
        if self.waitBlanking is True:
            return now

    def update(self):
        """Deprecated: use Window.flip() instead
        """
        # clearBuffer was the original behaviour for win.update()
        self.flip(clearBuffer=True)

    def multiFlip(self, flips=1, clearBuffer=True):
        """Flip multiple times while maintaining the display constant.
        Use this method for precise timing.

        **WARNING:** This function should not be used. See the `Notes` section
        for details.

        Parameters
        ----------
        flips : int, optional
            The number of monitor frames to flip. Floats will be
            rounded to integers, and a warning will be emitted.
            ``Window.multiFlip(flips=1)`` is equivalent to ``Window.flip()``.
            Defaults to `1`.
        clearBuffer : bool, optional
            Whether to clear the screen after the last flip.
            Defaults to `True`.

        Notes
        -----
        - This function can behave unpredictably, and the PsychoPy authors
          recommend against using it. See
          https://github.com/psychopy/psychopy/issues/867 for more information.

        Examples
        --------
        Example of using ``multiFlip``::

            # Draws myStim1 to buffer
            myStim1.draw()
            # Show stimulus for 4 frames (90 ms at 60Hz)
            myWin.multiFlip(clearBuffer=False, flips=6)
            # Draw myStim2 "on top of" myStim1
            # (because buffer was not cleared above)
            myStim2.draw()
            # Show this for 2 frames (30 ms at 60Hz)
            myWin.multiFlip(flips=2)
            # Show blank screen for 3 frames (buffer was cleared above)
            myWin.multiFlip(flips=3)

        """
        if flips < 1:
            logging.error("flips argument for multiFlip should be "
                          "a positive integer")

        if flips != int(flips):
            flips = int(round(flips))
            logging.warning("Number of flips was not an integer; "
                            "rounding to the next integer. Will flip "
                            "%i times." % flips)

        if flips > 1 and not self.waitBlanking:
            logging.warning("Call to Window.multiFlip() with flips > 1 is "
                            "unnecessary because Window.waitBlanking=False")

        # Do the flipping with last flip as special case
        for _ in range(flips - 1):
            self.flip(clearBuffer=False)
        self.flip(clearBuffer=clearBuffer)



    def setBuffer(self, buffer, clear=True):
        """Choose which buffer to draw to ('left' or 'right').

        Requires the Window to be initialised with stereo=True and requires a
        graphics card that supports quad buffering (e,g nVidia Quadro series)

        PsychoPy always draws to the back buffers, so 'left' will use
        ``GL_BACK_LEFT`` This then needs to be flipped once both eye's buffers
        have been rendered.

        Parameters
        ----------
        buffer : str
            Buffer to draw to. Can either be 'left' or 'right'.
        clear : bool, optional
            Clear the buffer before drawing. Default is ``True``.

        Examples
        --------
        Stereoscopic rendering example using quad-buffers::

            win = visual.Window(...., stereo=True)
            while True:
                # clear may not actually be needed
                win.setBuffer('left', clear=True)
                # do drawing for left eye
                win.setBuffer('right', clear=True)
                # do drawing for right eye
                win.flip()

        """
        if buffer == 'left':
            GL.glDrawBuffer(GL.GL_BACK_LEFT)
        elif buffer == 'right':
            GL.glDrawBuffer(GL.GL_BACK_RIGHT)
        else:
            raise "Unknown buffer '%s' requested in Window.setBuffer" % buffer
        if clear:
            self.clearBuffer()

    def clearBuffer(self, color=True, depth=False, stencil=False):
        """Clear the present buffer (to which you are currently drawing) without
        flipping the window.

        Useful if you want to generate movie sequences from the back buffer
        without actually taking the time to flip the window.

        Set `color` prior to clearing to set the color to clear the color buffer
        to. By default, the depth buffer is cleared to a value of 1.0.

        Parameters
        ----------
        color, depth, stencil : bool
            Buffers to clear.

        Examples
        --------
        Clear the color buffer to a specified color::

            win.color = (1, 0, 0)
            win.clearBuffer(color=True)

        Clear only the depth buffer, `depthMask` must be `True` or else this
        will have no effect. Depth mask is usually `True` by default, but
        may change::

            win.depthMask = True
            win.clearBuffer(color=False, depth=True, stencil=False)

        """
        clearBufferBits = GL.GL_NONE

        if color:
            clearBufferBits |= GL.GL_COLOR_BUFFER_BIT

        if depth:
            clearBufferBits |= GL.GL_DEPTH_BUFFER_BIT

        if stencil:
            clearBufferBits |= GL.GL_STENCIL_BUFFER_BIT

        # reset returned buffer for next frame
        GL.glClear(clearBufferBits)

    @property
    def size(self):
        """Size of the drawable area in pixels (w, h)."""
        # report clientSize until we get framebuffer size from
        # the backend, needs to be done properly in the future
        if self.backend is not None:
            return self.viewport[2:]
        else:
            return self.clientSize

    @property
    def frameBufferSize(self):
        """Size of the framebuffer in pixels (w, h)."""
        # Dimensions should match window size unless using a retina display
        return self.backend.frameBufferSize

    @property
    def windowedSize(self):
        """Size of the window to use when not fullscreen (w, h)."""
        return self._windowedSize

    @windowedSize.setter
    def windowedSize(self, value):
        """Size of the window to use when not fullscreen (w, h)."""
        self._windowedSize[:] = value

    def getContentScaleFactor(self):
        """Get the scaling factor required for scaling correctly on high-DPI
        displays.

        If the returned value is 1.0, no scaling needs to be applied to objects
        drawn on the backbuffer. A value >1.0 indicates that the backbuffer is
        larger than the reported client area, requiring points to be scaled to
        maintain constant size across similarly sized displays. In other words,
        the scaling required to convert framebuffer to client coordinates.

        Returns
        -------
        float
            Scaling factor to be applied along both horizontal and vertical
            dimensions.

        Examples
        --------
        Get the size of the client area::

            clientSize = win.frameBufferSize / win.getContentScaleFactor()

        Get the framebuffer size from the client size::

            frameBufferSize = win.clientSize * win.getContentScaleFactor()

        Convert client (window) to framebuffer pixel coordinates (eg., a mouse
        coordinate, vertices, etc.)::

            # `mousePosXY` is an array ...
            frameBufferXY = mousePosXY * win.getContentScaleFactor()
            # you can also use the attribute ...
            frameBufferXY = mousePosXY * win.contentScaleFactor

        Notes
        -----
        * This value is only valid after the window has been fully realized.

        """
        # this might be accessed at lots of points, probably shouldn't compute
        # this all the time
        if self._contentScaleFactor is not None:
            return self._contentScaleFactor

        sx = self.frameBufferSize[0] / float(self.clientSize[0])
        sy = self.frameBufferSize[1] / float(self.clientSize[1])

        if sx != sy:  # messed up DPI settings return 1.0 and show warning
            self._contentScaleFactor = 1.0
        else:
            self._contentScaleFactor = sx

        return self._contentScaleFactor

    @property
    def contentScaleFactor(self):
        """Scaling factor (`float`) to use when drawing to the backbuffer to
        convert framebuffer to client coordinates.

        See Also
        --------
        getContentScaleFactor

        """
        return self.getContentScaleFactor()

    @property
    def aspect(self):
        """Aspect ratio of the current viewport (width / height)."""
        return self._viewport[2] / float(self._viewport[3])

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
                          numpy.ctypeslib.as_ctypes(self._ambientLight))

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
            diffuse = numpy.ctypeslib.as_ctypes(light._diffuseRGB)
            specular = numpy.ctypeslib.as_ctypes(light._specularRGB)
            ambient = numpy.ctypeslib.as_ctypes(light._ambientRGB)

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
                pos = numpy.ctypeslib.as_ctypes(light.pos)
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
            diffuse = numpy.ctypeslib.as_ctypes(light.diffuse)
            specular = numpy.ctypeslib.as_ctypes(light.specular)
            ambient = numpy.ctypeslib.as_ctypes(light.ambient)

            # pass values to OpenGL
            # GL.glLightfv(enumLight, GL.GL_POSITION, pos)
            GL.glLightfv(enumLight, GL.GL_DIFFUSE, diffuse)
            GL.glLightfv(enumLight, GL.GL_SPECULAR, specular)
            GL.glLightfv(enumLight, GL.GL_AMBIENT, ambient)

    def resetViewport(self):
        """Reset the viewport to cover the whole framebuffer.

        Set the viewport to match the dimensions of the back buffer or
        framebuffer (if `useFBO=True`). The scissor rectangle is also set to
        match the dimensions of the viewport.

        """
        # use the framebuffer size here, not the window size (hi-dpi compat)
        bufferWidth, bufferHeight = self.frameBufferSize
        self.scissor = self.viewport = [0, 0, bufferWidth, bufferHeight]

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
        self._viewport = numpy.array(value, int)
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
        self._scissor = numpy.array(value, int)
        GL.glScissor(*self._scissor)

    @property
    def scissorTest(self):
        """`True` if scissor testing is enabled."""
        return self._scissorTest

    @scissorTest.setter
    def scissorTest(self, value):
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
        if value is True:
            GL.glEnable(GL.GL_STENCIL_TEST)
        elif value is False:
            GL.glDisable(GL.GL_STENCIL_TEST)
        else:
            raise TypeError("Value must be boolean.")

        self._stencilTest = value

    @property
    def nearClip(self):
        """Distance to the near clipping plane in meters."""
        return self._nearClip

    @nearClip.setter
    def nearClip(self, value):
        self._nearClip = value

    @property
    def farClip(self):
        """Distance to the far clipping plane in meters."""
        return self._farClip

    @farClip.setter
    def farClip(self, value):
        self._farClip = value

    @property
    def projectionMatrix(self):
        """Projection matrix defined as a 4x4 numpy array."""
        return self._projectionMatrix

    @projectionMatrix.setter
    def projectionMatrix(self, value):
        self._projectionMatrix = numpy.asarray(value, numpy.float32)
        assert self._projectionMatrix.shape == (4, 4)

    @property
    def viewMatrix(self):
        """View matrix defined as a 4x4 numpy array."""
        return self._viewMatrix

    @viewMatrix.setter
    def viewMatrix(self, value):
        self._viewMatrix = numpy.asarray(value, numpy.float32)
        assert self._viewMatrix.shape == (4, 4)

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

    def setOffAxisView(self, applyTransform=True, clearDepth=True):
        """Set an off-axis projection.

        Create an off-axis projection for subsequent rendering calls. Sets the
        `viewMatrix` and `projectionMatrix` accordingly so the scene origin is
        on the screen plane. If `eyeOffset` is correct and the view distance and
        screen size is defined in the monitor configuration, the resulting view
        will approximate `ortho-stereo` viewing.

        The convergence plane can be adjusted by setting `convergeOffset`. By
        default, the convergence plane is set to the screen plane. Any points
        on the screen plane will have zero disparity.

        Parameters
        ----------
        applyTransform : bool
            Apply transformations after computing them in immediate mode. Same
            as calling :py:attr:`~Window.applyEyeTransform()` afterwards.
        clearDepth : bool, optional
            Clear the depth buffer.

        """
        scrDistM = 0.5 if self.scrDistCM is None else self.scrDistCM / 100.0
        scrWidthM = 0.5 if self.scrWidthCM is None else self.scrWidthCM / 100.0

        # Not in full screen mode? Need to compute the dimensions of the display
        # area to ensure disparities are correct even when in windowed-mode.
        aspect = self.size[0] / self.size[1]
        if not self._isFullScr:
            scrWidthM = (self.size[0] / self.scrWidthPIX) * scrWidthM

        frustum = viewtools.computeFrustum(
            scrWidthM,  # width of screen
            aspect,  # aspect ratio
            scrDistM,  # distance to screen
            eyeOffset=self._eyeOffset,
            convergeOffset=self._convergeOffset,
            nearClip=self._nearClip,
            farClip=self._farClip)

        self._projectionMatrix = viewtools.perspectiveProjectionMatrix(*frustum)

        # translate away from screen
        self._viewMatrix = numpy.identity(4, dtype=numpy.float32)
        self._viewMatrix[0, 3] = -self._eyeOffset  # apply eye offset
        self._viewMatrix[2, 3] = -scrDistM  # displace scene away from viewer

        if applyTransform:
            self.applyEyeTransform(clearDepth=clearDepth)

    def setToeInView(self, applyTransform=True, clearDepth=True):
        """Set toe-in projection.

        Create a toe-in projection for subsequent rendering calls. Sets the
        `viewMatrix` and `projectionMatrix` accordingly so the scene origin is
        on the screen plane. The value of `convergeOffset` will define the
        convergence point of the view, which is offset perpendicular to the
        center of the screen plane. Points falling on a vertical line at the
        convergence point will have zero disparity.

        Parameters
        ----------
        applyTransform : bool
            Apply transformations after computing them in immediate mode. Same
            as calling :py:attr:`~Window.applyEyeTransform()` afterwards.
        clearDepth : bool, optional
            Clear the depth buffer.

        Notes
        -----
        * This projection mode is only 'correct' if the viewer's eyes are
          converged at the convergence point. Due to perspective, this
          projection introduces vertical disparities which increase in magnitude
          with eccentricity. Use `setOffAxisView` if you want to display
          something the viewer can look around the screen comfortably.

        """
        scrDistM = 0.5 if self.scrDistCM is None else self.scrDistCM / 100.0
        scrWidthM = 0.5 if self.scrWidthCM is None else self.scrWidthCM / 100.0

        # Not in full screen mode? Need to compute the dimensions of the display
        # area to ensure disparities are correct even when in windowed-mode.
        aspect = self.size[0] / self.size[1]
        if not self._isFullScr:
            scrWidthM = (self.size[0] / self.scrWidthPIX) * scrWidthM

        frustum = viewtools.computeFrustum(
            scrWidthM,  # width of screen
            aspect,  # aspect ratio
            scrDistM,  # distance to screen
            nearClip=self._nearClip,
            farClip=self._farClip)

        self._projectionMatrix = viewtools.perspectiveProjectionMatrix(*frustum)

        # translate away from screen
        eyePos = (self._eyeOffset, 0.0, scrDistM)
        convergePoint = (0.0, 0.0, self.convergeOffset)
        self._viewMatrix = viewtools.lookAt(eyePos, convergePoint)

        if applyTransform:
            self.applyEyeTransform(clearDepth=clearDepth)

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
        # NB - we should eventually compute these matrices lazily since they may
        # not change over the course of an experiment under most circumstances.
        #
        scrDistM = 0.5 if self.scrDistCM is None else self.scrDistCM / 100.0
        scrWidthM = 0.5 if self.scrWidthCM is None else self.scrWidthCM / 100.0

        # Not in full screen mode? Need to compute the dimensions of the display
        # area to ensure disparities are correct even when in windowed-mode.
        aspect = self.size[0] / self.size[1]
        if not self._isFullScr:
            scrWidthM = (self.size[0] / self.scrWidthPIX) * scrWidthM

        frustum = viewtools.computeFrustum(
            scrWidthM,  # width of screen
            aspect,  # aspect ratio
            scrDistM,  # distance to screen
            nearClip=self._nearClip,
            farClip=self._farClip)

        self._projectionMatrix = \
            viewtools.perspectiveProjectionMatrix(*frustum, dtype=numpy.float32)

        # translate away from screen
        self._viewMatrix = numpy.identity(4, dtype=numpy.float32)
        self._viewMatrix[0, 3] = -self._eyeOffset  # apply eye offset
        self._viewMatrix[2, 3] = -scrDistM  # displace scene away from viewer

        if applyTransform:
            self.applyEyeTransform(clearDepth=clearDepth)

    def applyEyeTransform(self, clearDepth=True):
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
        # apply the projection and view transformations
        if hasattr(self, '_projectionMatrix'):
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            projMat = self._projectionMatrix.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float))
            GL.glMultTransposeMatrixf(projMat)

        if hasattr(self, '_viewMatrix'):
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            viewMat = self._viewMatrix.ctypes.data_as(
                ctypes.POINTER(ctypes.c_float))
            GL.glMultTransposeMatrixf(viewMat)

        oldDepthMask = self.depthMask
        if clearDepth:
            GL.glDepthMask(GL.GL_TRUE)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

            if oldDepthMask is False:   # return to old state if needed
                GL.glDepthMask(GL.GL_FALSE)

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
            self._viewMatrix = numpy.identity(4, dtype=numpy.float32)

        if hasattr(self, '_projectionMatrix'):
            self._projectionMatrix = viewtools.orthoProjectionMatrix(
                -1, 1, -1, 1, -1, 1, dtype=numpy.float32)

        self.applyEyeTransform(clearDepth)

    def coordToRay(self, screenXY):
        """Convert a screen coordinate to a direction vector.

        Takes a screen/window coordinate and computes a vector which projects
        a ray from the viewpoint through it (line-of-sight). Any 3D point
        touching the ray will appear at the screen coordinate.

        Uses the current `viewport` and `projectionMatrix` to calculate the
        vector. The vector is in eye-space, where the origin of the scene is
        centered at the viewpoint and the forward direction aligned with the -Z
        axis. A ray of (0, 0, -1) results from a point at the very center of the
        screen assuming symmetric frustums.

        Note that if you are using a flipped/mirrored view, you must invert your
        supplied screen coordinates (`screenXY`) prior to passing them to this
        function.

        Parameters
        ----------
        screenXY : array_like
            X, Y screen coordinate. Must be in units of the window.

        Returns
        -------
        ndarray
            Normalized direction vector [x, y, z].

        Examples
        --------
        Getting the direction vector between the mouse cursor and the eye::

            mx, my = mouse.getPos()
            dir = win.coordToRay((mx, my))

        Set the position of a 3D stimulus object using the mouse, constrained to
        a plane. The object origin will always be at the screen coordinate of
        the mouse cursor::

            # the eye position in the scene is defined by a rigid body pose
            win.viewMatrix = camera.getViewMatrix()
            win.applyEyeTransform()

            # get the mouse location and calculate the intercept
            mx, my = mouse.getPos()
            ray = win.coordToRay([mx, my])
            result = intersectRayPlane(   # from mathtools
                orig=camera.pos,
                dir=camera.transformNormal(ray),
                planeOrig=(0, 0, -10),
                planeNormal=(0, 1, 0))

            # if result is `None`, there is no intercept
            if result is not None:
                pos, dist = result
                objModel.thePose.pos = pos
            else:
                objModel.thePose.pos = (0, 0, -10)  # plane origin

        If you don't define the position of the viewer with a `RigidBodyPose`,
        you can obtain the appropriate eye position and rotate the ray by doing
        the following::

            pos = numpy.linalg.inv(win.viewMatrix)[:3, 3]
            ray = win.coordToRay([mx, my]).dot(win.viewMatrix[:3, :3])
            # then ...
            result = intersectRayPlane(
                orig=pos,
                dir=ray,
                planeOrig=(0, 0, -10),
                planeNormal=(0, 1, 0))

        """
        # put in units of pixels
        if self.units == 'pix':
            scrX, scrY = numpy.asarray(screenXY, numpy.float32)
        else:
            scrX, scrY = convertToPix(numpy.asarray([0, 0]),
                                      numpy.asarray(screenXY),
                                      units=self.units,
                                      win=self)[:2]

        # transform psychopy mouse coordinates to viewport coordinates
        scrX = scrX + (self.size[0] / 2.)
        scrY = scrY + (self.size[1] / 2.)

        # get the NDC coordinates of the
        projX = 2. * (scrX - self.viewport[0]) / self.viewport[2] - 1.
        projY = 2. * (scrY - self.viewport[1]) / self.viewport[3] - 1.

        vecNear = numpy.array((projX, projY, 0., 1.), dtype=numpy.float32)
        vecFar = numpy.array((projX, projY, 1., 1.), dtype=numpy.float32)

        # compute the inverse projection matrix
        invPM = numpy.linalg.inv(self.projectionMatrix)

        vecNear[:] = vecNear.dot(invPM.T)
        vecFar[:] = vecFar.dot(invPM.T)

        vecNear /= vecNear[3]
        vecFar /= vecFar[3]

        # direction vector, get rid of `w`
        dirVec = vecFar[:3] - vecNear[:3]

        return dirVec / numpy.linalg.norm(dirVec)

    def getMovieFrame(self, buffer='front'):
        """Capture the current Window as an image.

        Saves to stack for :py:attr:`~Window.saveMovieFrames()`. As of v1.81.00
        this also returns the frame as a PIL image

        This can be done at any time (usually after a :py:attr:`~Window.flip()`
        command).

        Frames are stored in memory until a :py:attr:`~Window.saveMovieFrames()`
        command is issued. You can issue :py:attr:`~Window.getMovieFrame()` as
        often as you like and then save them all in one go when finished.

        The back buffer will return the frame that hasn't yet been 'flipped'
        to be visible on screen but has the advantage that the mouse and any
        other overlapping windows won't get in the way.

        The default front buffer is to be called immediately after a
        :py:attr:`~Window.flip()` and gives a complete copy of the screen at the
        window's coordinates.

        Parameters
        ----------
        buffer : str, optional
            Buffer to capture.

        Returns
        -------
        Image
            Buffer pixel contents as a PIL/Pillow image object.

        """
        im = self._getFrame(buffer=buffer)
        self.movieFrames.append(im)
        return im

    def _getFrame(self, rect=None, buffer='front'):
        """Return the current Window as an image.
        """
        # GL.glLoadIdentity()
        # do the reading of the pixels
        if buffer == 'back' and self.useFBO:
            GL.glReadBuffer(GL.GL_COLOR_ATTACHMENT0_EXT)
        elif buffer == 'back':
            GL.glReadBuffer(GL.GL_BACK)
        elif buffer == 'front':
            if self.useFBO:
                GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, 0)
            GL.glReadBuffer(GL.GL_FRONT)
        else:
            raise ValueError("Requested read from buffer '{}' but should be "
                             "'front' or 'back'".format(buffer))

        if rect:
            x, y = self.size  # of window, not image
            imType = 'RGBA'  # not tested with anything else

            # box corners in pix
            left = int((rect[0] / 2. + 0.5) * x)
            bottom = int((rect[3] / 2. + 0.5) * y)
            w = int((rect[2] / 2. + 0.5) * x) - left
            h = int((rect[1] / 2. + 0.5) * y) - bottom
        else:
            left = bottom = 0
            w, h = self.size

        # http://www.opengl.org/sdk/docs/man/xhtml/glGetTexImage.xml
        bufferDat = (GL.GLubyte * (4 * w * h))()
        GL.glReadPixels(left, bottom, w, h,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, bufferDat)
        try:
            im = Image.fromstring(mode='RGBA', size=(w, h),
                                  data=bufferDat)
        except Exception:
            im = Image.frombytes(mode='RGBA', size=(w, h),
                                 data=bufferDat)

        im = im.transpose(Image.FLIP_TOP_BOTTOM)
        im = im.convert('RGB')

        if self.useFBO and buffer == 'front':
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, self.frameBuffer)
        return im

    @property
    def screenshot(self):
        return self._getFrame()

    def saveMovieFrames(self, fileName, codec='libx264',
                        fps=30, clearFrames=True):
        """Writes any captured frames to disk.

        Will write any format that is understood by PIL (tif, jpg, png, ...)

        Parameters
        ----------
        filename : str
            Name of file, including path. The extension at the end of the file
            determines the type of file(s) created. If an image type (e.g. .png)
            is given, then multiple static frames are created. If it is .gif
            then an animated GIF image is created (although you will get higher
            quality GIF by saving PNG files and then combining them in dedicated
            image manipulation software, such as GIMP). On Windows and Linux
            `.mpeg` files can be created if `pymedia` is installed. On macOS
            `.mov` files can be created if the pyobjc-frameworks-QTKit is
            installed. Unfortunately the libs used for movie generation can be
            flaky and poor quality. As for animated GIFs, better results can be
            achieved by saving as individual .png frames and then combining them
            into a movie using software like ffmpeg.
        codec : str, optional
            The codec to be used **by moviepy** for mp4/mpg/mov files. If
            `None` then the default will depend on file extension. Can be
            one of ``libx264``, ``mpeg4`` for mp4/mov files. Can be
            ``rawvideo``, ``png`` for avi files (not recommended). Can be
            ``libvorbis`` for ogv files. Default is ``libx264``.
        fps : int, optional
            The frame rate to be used throughout the movie. **Only for
            quicktime (.mov) movies.**. Default is `30`.
        clearFrames : bool, optional
            Set this to `False` if you want the frames to be kept for
            additional calls to ``saveMovieFrames``. Default is `True`.

        Examples
        --------
        Writes a series of static frames as frame001.tif, frame002.tif etc.::

            myWin.saveMovieFrames('frame.tif')

        As of PsychoPy 1.84.1 the following are written with moviepy::

            myWin.saveMovieFrames('stimuli.mp4') # codec = 'libx264' or 'mpeg4'
            myWin.saveMovieFrames('stimuli.mov')
            myWin.saveMovieFrames('stimuli.gif')

        """
        fileRoot, fileExt = os.path.splitext(fileName)
        fileExt = fileExt.lower()  # easier than testing both later
        if len(self.movieFrames) == 0:
            logging.error('no frames to write - did you forget to update '
                          'your window or call win.getMovieFrame()?')
            return
        else:
            logging.info('Writing %i frames to %s' % (len(self.movieFrames),
                                                      fileName))

        if fileExt in ['.gif', '.mpg', '.mpeg', '.mp4', '.mov']:
            # lazy loading of moviepy.editor (rarely needed)
            from moviepy.editor import ImageSequenceClip
            # save variety of movies with moviepy
            numpyFrames = []
            for frame in self.movieFrames:
                numpyFrames.append(numpy.array(frame))
            clip = ImageSequenceClip(numpyFrames, fps=fps)
            if fileExt == '.gif':
                clip.write_gif(fileName, fps=fps, fuzz=0, opt='nq')
            else:
                clip.write_videofile(fileName, codec=codec)
        elif len(self.movieFrames) == 1:
            # save an image using pillow
            self.movieFrames[0].save(fileName)
        else:
            frmc = numpy.ceil(numpy.log10(len(self.movieFrames) + 1))
            frame_name_format = "%s%%0%dd%s" % (fileRoot, frmc, fileExt)
            for frameN, thisFrame in enumerate(self.movieFrames):
                thisFileName = frame_name_format % (frameN + 1,)
                thisFrame.save(thisFileName)
        if clearFrames:
            self.movieFrames = []

    def _getRegionOfFrame(self, rect=(-1, 1, 1, -1), buffer='front',
                          power2=False, squarePower2=False):
        """Deprecated function, here for historical reasons. You may now use
        `:py:attr:`~Window._getFrame()` and specify a rect to get a sub-region,
        just as used here.

        power2 can be useful with older OpenGL versions to avoid interpolation
        in :py:attr:`PatchStim`. If power2 or squarePower2, it will expand rect
        dimensions up to next power of two. squarePower2 uses the max
        dimensions. You need to check what your hardware & OpenGL supports,
        and call :py:attr:`~Window._getRegionOfFrame()` as appropriate.
        """
        # Ideally: rewrite using GL frame buffer object; glReadPixels == slow
        region = self._getFrame(rect=rect, buffer=buffer)
        if power2 or squarePower2:  # use to avoid interpolation in PatchStim
            if squarePower2:
                maxsize = max(region.size)
                xPowerOf2 = int(2**numpy.ceil(numpy.log2(maxsize)))
                yPowerOf2 = xPowerOf2
            else:
                xPowerOf2 = int(2**numpy.ceil(numpy.log2(region.size[0])))
                yPowerOf2 = int(2**numpy.ceil(numpy.log2(region.size[1])))
            imP2 = Image.new('RGBA', (xPowerOf2, yPowerOf2))
            # paste centered
            imP2.paste(region, (int(xPowerOf2 / 2. - region.size[0] / 2.),
                                int(yPowerOf2 / 2.) - region.size[1] / 2))
            region = imP2
        return region

    def close(self):
        """Close the window (and reset the Bits++ if necess).
        """
        self._closed = True

        # If iohub is running, inform it to stop using this win id
        # for mouse events
        try:
            if IOHUB_ACTIVE:
                from psychopy.iohub.client import ioHubConnection
                ioHubConnection.ACTIVE_CONNECTION.unregisterWindowHandles(self._hw_handle)
        except Exception:
            pass

        self.backend.close()  # moved here, dereferencing the window prevents
                              # backend specific actions to take place

        try:
            openWindows.remove(self)
        except Exception:
            pass

        try:
            self.mouseVisible = True
        except Exception:
            # can cause unimportant "'NoneType' object is not callable"
            pass

        try:
            if self.bits is not None:
                self.bits.reset()
        except Exception:
            pass
        try:
            logging.flush()
        except Exception:
            pass

    def fps(self):
        """Report the frames per second since the last call to this function
        (or since the window was created if this is first call)"""
        fps = self.frames / self.frameClock.getTime()
        self.frameClock.reset()
        self.frames = 0
        return fps

    @property
    def depthTest(self):
        """`True` if depth testing is enabled."""
        return self._depthTest

    @depthTest.setter
    def depthTest(self, value):
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

        GL.glDepthFunc(depthFuncs[value])

        self._depthFunc = value

    @property
    def depthMask(self):
        """`True` if depth masking is enabled. Writing to the depth buffer will
        be disabled.
        """
        return self._depthMask

    @depthMask.setter
    def depthMask(self, value):
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
        if value == 'ccw':
            GL.glFrontFace(GL.GL_CCW)
        elif value == 'cw':
            GL.glFrontFace(GL.GL_CW)
        else:
            raise ValueError('Invalid value, must be `ccw` or `cw`.')

        self._frontFace = value

    @property
    def draw3d(self):
        """`True` if 3D drawing is enabled on this window."""
        return self._draw3d

    @draw3d.setter
    def draw3d(self, value):
        if value is True:
            if self.depthMask is False:
                self.depthMask = True
            if self.depthTest is False:
                self.depthTest = True
            if self.cullFace is False:
                self.cullFace = True
        elif value is False:
            if self.depthMask is True:
                self.depthMask = False
            if self.depthTest is True:
                self.depthTest = False
            if self.cullFace is True:
                self.cullFace = False
        else:
            raise TypeError('Value must be type `bool`.')

        self._draw3d = value

    @attributeSetter
    def blendMode(self, blendMode):
        """Blend mode to use."""
        self.__dict__['blendMode'] = blendMode
        if blendMode == 'avg':
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            if hasattr(self, '_shaders'):
                self._progSignedFrag = self._shaders['signedColor']
                self._progSignedTex = self._shaders['signedTex']
                self._progSignedTexMask = self._shaders['signedTexMask']
                self._progSignedTexMask1D = self._shaders['signedTexMask1D']
                self._progImageStim = self._shaders['imageStim']
        elif blendMode == 'add':
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
            if hasattr(self, '_shaders'):
                self._progSignedFrag = self._shaders['signedColor_adding']
                self._progSignedTex = self._shaders['signedTex_adding']
                self._progSignedTexMask = self._shaders['signedTexMask_adding']
                tmp = self._shaders['signedTexMask1D_adding']
                self._progSignedTexMask1D = tmp
                self._progImageStim = self._shaders['imageStim_adding']
        else:
            raise ValueError("Window blendMode should be set to 'avg' or 'add'"
                             " but we received the value {}"
                             .format(repr(blendMode)))

    def setBlendMode(self, blendMode, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'blendMode', blendMode, log)

    @property
    def colorSpace(self):
        """The name of the color space currently being used

        Value should be: a string or None

        For strings and hex values this is not needed.
        If None the default colorSpace for the stimulus is
        used (defined during initialisation).

        Please note that changing colorSpace does not change stimulus
        parameters. Thus you usually want to specify colorSpace before
        setting the color. Example::

            # A light green text
            stim = visual.TextStim(win, 'Color me!',
                                   color=(0, 1, 0), colorSpace='rgb')

            # An almost-black text
            stim.colorSpace = 'rgb255'

            # Make it light green again
            stim.color = (128, 255, 128)
        """
        if hasattr(self, '_colorSpace'):
            return self._colorSpace
        else:
            return 'rgb'
    @colorSpace.setter
    def colorSpace(self, value):
        if value in colorSpaces:
            self._colorSpace = value
        else:
            logging.error(f"'{value}' is not a valid color space")

    @property
    def color(self):
        """Set the color of the window.

        This command sets the color that the blank screen will have on the
        next clear operation. As a result it effectively takes TWO
        :py:attr:`~Window.flip()` operations to become visible (the first uses
        the color to create the new screen, the second presents that screen to
        the viewer). For this reason, if you want to changed background color of
        the window "on the fly", it might be a better idea to draw a
        :py:attr:`Rect` that fills the whole window with the desired
        :py:attr:`Rect.fillColor` attribute. That'll show up on first flip.

        See other stimuli (e.g. :py:attr:`GratingStim.color`)
        for more info on the color attribute which essentially works the same on
        all PsychoPy stimuli.

        See :ref:`colorspaces` for further information about the ways to
        specify colors and their various implications.
        """
        if hasattr(self, '_color'):
            return getattr(self._color, self.colorSpace)
    @color.setter
    def color(self, value):
        if isinstance(value, Color):
            # If supplied with a color object, set as that
            self._color = value
        else:
            # Otherwise, use it to make a color object
            self._color = Color(value, self.colorSpace)
        if not self._color:
            self._color = Color()
            logging.error(f"'{value}' is not a valid {self.colorSpace} color")

        # if it is None then this will be done during window setup
        if self.backend is not None:
            self.backend.setCurrent()  # make sure this window is active
            GL.glClearColor(*self._color.render('rgba1'))

    def setColor(self, color, colorSpace=None, operation='', log=None):
        """Usually you can use ``stim.attribute = value`` syntax instead,
        but use this method if you want to set color and colorSpace
        simultaneously.

        See :py:attr:`~Window.color` for documentation on colors.
        """
        self.colorSpace = colorSpace
        self.color = color

    def setRGB(self, newRGB):
        """Deprecated: As of v1.61.00 please use `setColor()` instead
        """
        self.setColor(newRGB, colorSpace="rgb")

    @property
    def rgb(self):
        if hasattr(self, "_color"):
            return self._color.render("rgb")
    @rgb.setter
    def rgb(self, value):
        self.color = Color(value, 'rgb')

    @attributeSetter
    def backgroundImage(self, value):
        """
        Background image for the window, can be either a visual.ImageStim object or anything which could be passed to
        visual.ImageStim.image to create one. Will be drawn each time `win.flip()` is called, meaning it is always
        below all other contents of the window.
        """
        if value in (None, "None", "none", ""):
            # If given None, store so we know not to use a background image
            self._backgroundImage = None
            self.__dict__['backgroundImage'] = self._backgroundImage
            return
        elif hasattr(value, "draw") and hasattr(value, "win"):
            # If given a visual object, set its parent window to self and use it
            value.win = self
            self._backgroundImage = value
        else:
            # Otherwise, try to make an image from value (start off as if backgroundFit was None)
            self._backgroundImage = image.ImageStim(self, image=value, size=None, pos=(0, 0))

        # Set background fit again now that we have an image
        if hasattr(self, "_backgroundFit"):
            self.backgroundFit = self._backgroundFit

        self.__dict__['backgroundImage'] = self._backgroundImage

    @attributeSetter
    def backgroundFit(self, value):
        """
        How should the background image of this window fit? Options are:

        None, "None", "none"
            No scaling is applied, image is present at its pixel size unaltered.
        "cover"
            Image is scaled such that it covers the whole screen without changing its aspect ratio. In other words,
            both dimensions are evenly scaled such that its SHORTEST dimension matches the window's LONGEST dimension.
        "contain"
            Image is scaled such that it is contained within the screen without changing its aspect ratio. In other
            words, both dimensions are evenly scaled such that its LONGEST dimension matches the window's SHORTEST
            dimension.
        "scaleDown", "scale-down", "scaledown"
            If image is bigger than the window along any dimension, it will behave as if backgroundFit were "contain".
            Otherwise, it will behave as if backgroundFit were None.
        """
        self._backgroundFit = value

        # Skip if no background image
        if (not hasattr(self, "_backgroundImage")) or (self._backgroundImage is None):
            self.__dict__['backgroundFit'] = self._backgroundFit
            return

        # If value is scaleDown or alias, set to None or "contain" based on relative size
        if value in ("scaleDown", "scale-down", "scaledown"):
            overflow = numpy.asarray(self._backgroundImage._origSize) > numpy.asarray(self.size)
            if overflow.any():
                value = "contain"
            else:
                value = None

        if value in (None, "None", "none"):
            # If value is None, don't change the backgroundImage at all
            pass
        elif value == "fill":
            # If value is fill, make backgroundImage fill screen
            self._backgroundImage.units = "norm"
            self._backgroundImage.size = (2, 2)
            self._backgroundImage.pos = (0, 0)
        if value in ("contain", "cover"):
            # If value is contain or cover, set one dimension to fill screen and the other to maintain ratio
            ratios = numpy.asarray(self._backgroundImage._origSize) / numpy.asarray(self.size)
            if value == "cover":
                i = ratios.argmin()
            else:
                i = ratios.argmax()
            size = [None, None]
            size[i] = 2
            self._backgroundImage.units = "norm"
            self._backgroundImage.size = size
            self._backgroundImage.pos = (0, 0)

        self.__dict__['backgroundFit'] = self._backgroundFit

    def _setupGamma(self, gammaVal):
        """A private method to work out how to handle gamma for this Window
        given that the user might have specified an explicit value, or maybe
        gave a Monitor.
        """
        # determine which gamma value to use (or native ramp)
        if gammaVal is not None:
            self._checkGamma()
            self.useNativeGamma = False
        elif not self.monitor.gammaIsDefault():
            if self.monitor.getGamma() is not None:
                self.__dict__['gamma'] = self.monitor.getGamma()
                self.useNativeGamma = False
        else:
            self.__dict__['gamma'] = None  # gamma wasn't set anywhere
            self.useNativeGamma = True

        # then try setting it
        if self.useNativeGamma:
            if self.autoLog:
                logging.info('Using gamma table of operating system')
        else:
            if self.autoLog:
                logging.info('Using gamma: self.gamma' + str(self.gamma))
            self.gamma = gammaVal  # using either pygame or bits++


    @attributeSetter
    def gamma(self, gamma):
        """Set the monitor gamma for linearization.

        Warnings
        --------
        Don't use this if using a Bits++ or Bits#, as it overrides monitor
        settings.

        """
        self._checkGamma(gamma)

        if self.bits is not None:
            msg = ("Do not use try to set the gamma of a window with "
                   "Bits++/Bits# enabled. It was ambiguous what should "
                   "happen. Use the setGamma() function of the bits box "
                   "instead")
            raise DeprecationWarning(msg)

        self.backend.gamma = self.__dict__['gamma']

    def setGamma(self, gamma, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.

        """
        setAttribute(self, 'gamma', gamma, log)

    @attributeSetter
    def gammaRamp(self, newRamp):
        """Sets the hardware CLUT using a specified 3xN array of floats ranging
        between 0.0 and 1.0.

        Array must have a number of rows equal to 2 ^ max(bpc).

        """
        self.backend.gammaRamp = newRamp

    def _checkGamma(self, gamma=None):
        if gamma is None:
            gamma = self.gamma
        if isinstance(gamma, (float, int)):
            self.__dict__['gamma'] = [gamma] * 3
        elif hasattr(gamma, '__iter__'):
            self.__dict__['gamma'] = gamma
        else:
            raise ValueError('gamma must be a numeric scalar or iterable')

    def setScale(self, units, font='dummyFont', prevScale=(1.0, 1.0)):
        """DEPRECATED: this method used to be used to switch between units for
        stimulus drawing but this is now handled by the stimuli themselves and
        the window should always be left in units of 'pix'
        """
        if self.useRetina:
            retinaScale = 2.0
        else:
            retinaScale = 1.0
        # then unit-specific changes
        if units == "norm":
            thisScale = numpy.array([1.0, 1.0])
        elif units == "height":
            thisScale = numpy.array([2.0 * self.size[1] / self.size[0], 2.0])
        elif units in ["pix", "pixels"]:
            thisScale = 2.0 / numpy.array(self.size) * retinaScale
        elif units == "cm":
            # windowPerCM = windowPerPIX / CMperPIX
            #             = (window/winPIX) / (scrCm/scrPIX)
            if self.scrWidthCM in [0, None] or self.scrWidthPIX in [0, None]:
                logging.error('you did not give the width of the screen (pixels'
                              ' and cm). Check settings in MonitorCentre.')
                core.wait(1.0)
                core.quit()
            thisScale = ((numpy.array([2.0, 2.0]) / self.size * retinaScale)
                        / (self.scrWidthCM / self.scrWidthPIX))
        elif units in ["deg", "degs"]:
            # windowPerDeg = winPerCM * CMperDEG
            #              = winPerCM * tan(pi/180) * distance
            if ((self.scrWidthCM in [0, None]) or
                    (self.scrWidthPIX in [0, None])):
                logging.error('you did not give the width of the screen (pixels'
                              ' and cm). Check settings in MonitorCentre.')
                core.wait(1.0)
                core.quit()
            cmScale = ((numpy.array([2.0, 2.0]) / self.size) * retinaScale /
                       (self.scrWidthCM / self.scrWidthPIX))
            thisScale = cmScale * 0.017455 * self.scrDistCM
        elif units == "stroke_font":
            lw = 2 * font.letterWidth
            thisScale = numpy.array([lw, lw] / self.size * retinaScale / 38.0)
        # actually set the scale as appropriate
        # allows undoing of a previous scaling procedure
        thisScale = thisScale / numpy.asarray(prevScale)
        GL.glScalef(thisScale[0], thisScale[1], 1.0)
        return thisScale

    def _checkMatchingSizes(self, requested, actual):
        """Checks whether the requested and actual screen sizes differ.
        If not then a warning is output and the window size is set to actual
        """
        if list(requested) != list(actual):
            logging.warning("User requested fullscreen with size %s, "
                            "but screen is actually %s. Using actual size" %
                            (requested, actual))
            self.clientSize = numpy.array(actual)

    def _setupGL(self):
        """Setup OpenGL state for this window.
        """
        # setup screen color
        self.color = self.color  # call attributeSetter
        GL.glClearDepth(1.0)

        # viewport or drawable area of the framebuffer
        self.viewport = self.scissor = \
            (0, 0, self.frameBufferSize[0], self.frameBufferSize[1])
        self.scissorTest = True
        self.stencilTest = False

        GL.glMatrixMode(GL.GL_PROJECTION)  # Reset the projection matrix
        GL.glLoadIdentity()
        GL.gluOrtho2D(-1, 1, -1, 1)

        GL.glMatrixMode(GL.GL_MODELVIEW)  # Reset the modelview matrix
        GL.glLoadIdentity()

        self.depthTest = False
        # GL.glEnable(GL.GL_DEPTH_TEST)  # Enables Depth Testing
        # GL.glDepthFunc(GL.GL_LESS)  # The Type Of Depth Test To Do
        GL.glEnable(GL.GL_BLEND)

        GL.glShadeModel(GL.GL_SMOOTH)  # Color Shading (FLAT or SMOOTH)
        GL.glEnable(GL.GL_POINT_SMOOTH)

        # check for GL_ARB_texture_float
        # (which is needed for shaders to be useful)
        # this needs to be done AFTER the context has been created
        if not GL.gl_info.have_extension('GL_ARB_texture_float'):
            self._haveShaders = False

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        # identify gfx card vendor
        self.glVendor = GL.gl_info.get_vendor().lower()

        requestedFBO = self.useFBO
        if self._haveShaders:  # do this after setting up FrameBufferObject
            self._setupShaders()
        else:
            self.useFBO = False
        if self.useFBO:
            success = self._setupFrameBuffer()
            if not success:
                self.useFBO = False
        if requestedFBO and not self.useFBO:
            logging.warning("Framebuffer object (FBO) not supported on "
                            "this graphics card")
        if self.blendMode == 'add' and not self.useFBO:
            logging.warning("Framebuffer object (FBO) is required for "
                            "blendMode='add'. Reverting to blendMode='avg'")
            self.blendMode = 'avg'

    def _setupShaders(self):
        self._progSignedTexFont = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTexFont)
        self._progFBOtoFrame = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragFBOtoFrame)
        self._shaders = {}
        self._shaders['signedColor'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColor)
        self._shaders['signedColor_adding'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColor_adding)
        self._shaders['signedTex'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTex)
        self._shaders['signedTexMask'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTexMask)
        self._shaders['signedTexMask1D'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTexMask1D)
        self._shaders['signedTex_adding'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTex_adding)
        self._shaders['signedTexMask_adding'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTexMask_adding)
        self._shaders['signedTexMask1D_adding'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragSignedColorTexMask1D_adding)
        self._shaders['imageStim'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragImageStim)
        self._shaders['imageStim_adding'] = _shaders.compileProgram(
            _shaders.vertSimple, _shaders.fragImageStim_adding)
        self._shaders['stim3d_phong'] = {}

        # Create shader flags, these are used as keys to pick the appropriate
        # shader for the given material and lighting configuration.
        shaderFlags = []
        for i in range(0, 8 + 1):
            for j in product((True, False), repeat=1):
                shaderFlags.append((i, j[0]))

        # Compile shaders based on generated flags.
        for flag in shaderFlags:
            # Define GLSL preprocessor values to enable code paths for specific
            # material properties.
            srcDefs = {'MAX_LIGHTS': flag[0]}

            if flag[1]:  # has diffuse texture map
                srcDefs['DIFFUSE_TEXTURE'] = 1

            # embed #DEFINE statements in GLSL source code
            vertSrc = gltools.embedShaderSourceDefs(
                _shaders.vertPhongLighting, srcDefs)
            fragSrc = gltools.embedShaderSourceDefs(
                _shaders.fragPhongLighting, srcDefs)

            # build a shader program
            prog = gltools.createProgramObjectARB()
            vertexShader = gltools.compileShaderObjectARB(
                vertSrc, GL.GL_VERTEX_SHADER_ARB)
            fragmentShader = gltools.compileShaderObjectARB(
                fragSrc, GL.GL_FRAGMENT_SHADER_ARB)

            gltools.attachObjectARB(prog, vertexShader)
            gltools.attachObjectARB(prog, fragmentShader)
            gltools.linkProgramObjectARB(prog)
            gltools.detachObjectARB(prog, vertexShader)
            gltools.detachObjectARB(prog, fragmentShader)
            gltools.deleteObjectARB(vertexShader)
            gltools.deleteObjectARB(fragmentShader)

            # set the flag
            self._shaders['stim3d_phong'][flag] = prog

    def _setupFrameBuffer(self):

        # Setup framebuffer
        self.frameBuffer = GL.GLuint()
        GL.glGenFramebuffersEXT(1, ctypes.byref(self.frameBuffer))
        GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, self.frameBuffer)

        # Create texture to render to
        self.frameTexture = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self.frameTexture))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.frameTexture)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,
                           GL.GL_TEXTURE_MAG_FILTER,
                           GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D,
                           GL.GL_TEXTURE_MIN_FILTER,
                           GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA32F_ARB,
                        int(self.size[0]), int(self.size[1]), 0,
                        GL.GL_RGBA, GL.GL_FLOAT, None)
        # attach texture to the frame buffer
        GL.glFramebufferTexture2DEXT(GL.GL_FRAMEBUFFER_EXT,
                                     GL.GL_COLOR_ATTACHMENT0_EXT,
                                     GL.GL_TEXTURE_2D, self.frameTexture, 0)

        # add a stencil buffer
        self._stencilTexture = GL.GLuint()
        GL.glGenRenderbuffersEXT(1, ctypes.byref(
            self._stencilTexture))  # like glGenTextures
        GL.glBindRenderbufferEXT(GL.GL_RENDERBUFFER_EXT, self._stencilTexture)
        GL.glRenderbufferStorageEXT(GL.GL_RENDERBUFFER_EXT,
                                    GL.GL_DEPTH24_STENCIL8_EXT,
                                    int(self.size[0]), int(self.size[1]))
        GL.glFramebufferRenderbufferEXT(GL.GL_FRAMEBUFFER_EXT,
                                        GL.GL_DEPTH_ATTACHMENT_EXT,
                                        GL.GL_RENDERBUFFER_EXT,
                                        self._stencilTexture)
        GL.glFramebufferRenderbufferEXT(GL.GL_FRAMEBUFFER_EXT,
                                        GL.GL_STENCIL_ATTACHMENT_EXT,
                                        GL.GL_RENDERBUFFER_EXT,
                                        self._stencilTexture)

        status = GL.glCheckFramebufferStatusEXT(GL.GL_FRAMEBUFFER_EXT)
        if status != GL.GL_FRAMEBUFFER_COMPLETE_EXT:
            logging.error("Error in framebuffer activation")
            # UNBIND THE FRAME BUFFER OBJECT THAT WE HAD CREATED
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, 0)
            return False
        GL.glDisable(GL.GL_TEXTURE_2D)
        # clear the buffers (otherwise the texture memory can contain
        # junk from other app)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glClear(GL.GL_STENCIL_BUFFER_BIT)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT)
        return True

    @attributeSetter
    def mouseVisible(self, visibility):
        """Sets the visibility of the mouse cursor.

        If Window was initialized with ``allowGUI=False`` then the mouse is
        initially set to invisible, otherwise it will initially be visible.

        Usage::

            win.mouseVisible = False
            win.mouseVisible = True

        """
        self.backend.setMouseVisibility(visibility)
        self.__dict__['mouseVisible'] = visibility

    def setMouseVisible(self, visibility, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message."""
        setAttribute(self, 'mouseVisible', visibility, log)

    def setMouseType(self, name='arrow'):
        """Change the appearance of the cursor for this window. Cursor types
        provide contextual hints about how to interact with on-screen objects.

        The graphics used 'standard cursors' provided by the operating system.
        They may vary in appearance and hot spot location across platforms. The
        following names are valid on most platforms:

        * ``arrow`` : Default pointer.
        * ``ibeam`` : Indicates text can be edited.
        * ``crosshair`` : Crosshair with hot-spot at center.
        * ``hand`` : A pointing hand.
        * ``hresize`` : Double arrows pointing horizontally.
        * ``vresize`` : Double arrows pointing vertically.

        Parameters
        ----------
        name : str
            Type of standard cursor to use (see above). Default is ``arrow``.

        Notes
        -----
        * On Windows the ``crosshair`` option is negated with the background
          color. It will not be visible when placed over 50% grey fields.

        """
        if hasattr(self.backend, "setMouseType"):
            self.backend.setMouseType(name)

    def showMessage(self, msg):
        """Show a message in the window. This can be used to show information
        to the participant.

        This creates a TextBox2 object that is displayed in the window. The 
        text can be updated by calling this method again with a new message. 
        The updated text will appear the next time `draw()` is called.

        Parameters
        ----------
        msg : str or None   
            Message text to display. If None, then any existing message is 
            removed.

        """
        if msg is None:
            self.hideMessage()
        else:
            self._showSplash = True
        
        if self._splashTextbox is None:  # create the textbox
            self._splashTextbox = TextBox2(
                self, text=msg,
                units="norm", size=(2, 2), alignment="center",  # full screen and centred
                letterHeight=0.1,  # font size relative to window
                autoDraw=False
            )
        else:
            self._splashTextbox.text = str(msg)  # update the text
        # set text color to contrast with background
        self._splashTextbox.color = self._color.getReadable(contrast=1)

    def hideMessage(self):
        """Remove any message that is currently being displayed."""
        self._showSplash = False

    def getActualFrameRate(self, nIdentical=10, nMaxFrames=100,
                           nWarmUpFrames=10, threshold=1):
        """Measures the actual frames-per-second (FPS) for the screen.

        This is done by waiting (for a max of `nMaxFrames`) until
        `nIdentical` frames in a row have identical frame times (std dev below
        `threshold` ms).

        Parameters
        ----------
        nIdentical : int, optional
            The number of consecutive frames that will be evaluated.
            Higher --> greater precision. Lower --> faster.
        nMaxFrames : int, optional
            The maximum number of frames to wait for a matching set of
            nIdentical.
        nWarmUpFrames : int, optional
            The number of frames to display before starting the test
            (this is in place to allow the system to settle after opening
            the `Window` for the first time.
        threshold : int or float, optional
            The threshold for the std deviation (in ms) before the set
            are considered a match.

        Returns
        -------
        float or None
            Frame rate (FPS) in seconds. If there is no such sequence of
            identical frames a warning is logged and `None` will be returned.

        """
        if nIdentical > nMaxFrames:
            raise ValueError(
                'Parameter `nIdentical` must be equal to or less than '
                '`nMaxFrames`')

        screen = self.screen
        name = self.name

        self.showMessage(
            "Attempting to measure frame rate of screen, please wait ...")

        # log that we're measuring the frame rate now
        if self.autoLog:
            msg = "{}: Attempting to measure frame rate of screen ({:d}) ..."
            logging.exp(msg.format(name, screen))

        # Disable `recordFrameIntervals` prior to the warmup as we expect to see
        # some instability here.
        recordFrmIntsOrig = self.recordFrameIntervals
        self.recordFrameIntervals = False

        # warm-up, allow the system to settle a bit before measuring frames
        for frameN in range(nWarmUpFrames):
            self.flip()

        # run test frames
        self.recordFrameIntervals = True  # record intervals for actual test
        threshSecs = threshold / 1000.0  # must be in seconds
        for frameN in range(nMaxFrames):
            self.flip()
            recentFrames = self.frameIntervals[-nIdentical:]
            nIntervals = len(self.frameIntervals)
            if len(recentFrames) < 3:
                continue  # no need to check variance yet
            recentFramesStd = numpy.std(recentFrames)  # compute variability
            if nIntervals >= nIdentical and recentFramesStd < threshSecs:
                # average duration of recent frames
                period = numpy.mean(recentFrames)  # log this too?
                rate = 1.0 / period  # compute frame rate in Hz
                if self.autoLog:
                    scrStr = "" if screen is None else " (%i)" % screen
                    msg = "Screen{} actual frame rate measured at {:.2f}Hz"
                    logging.exp(msg.format(scrStr, rate))

                self.recordFrameIntervals = recordFrmIntsOrig
                self.frameIntervals = []
                self.hideMessage()  # remove the message
                return rate

        self.hideMessage()  # remove the message

        # if we get here we reached end of `maxFrames` with no consistent value
        msg = ("Couldn't measure a consistent frame rate!\n"
               "  - Is your graphics card set to sync to vertical blank?\n"
               "  - Are you running other processes on your computer?\n")
        logging.warning(msg)

        return None

    def getMsPerFrame(self, nFrames=60, showVisual=False, msg='', msDelay=0.):
        """Assesses the monitor refresh rate (average, median, SD) under
        current conditions, over at least 60 frames.

        Records time for each refresh (frame) for n frames (at least 60),
        while displaying an optional visual. The visual is just eye-candy to
        show that something is happening when assessing many frames. You can
        also give it text to display instead of a visual,
        e.g., ``msg='(testing refresh rate...)'``; setting msg implies
        ``showVisual == False``.

        To simulate refresh rate under cpu load, you can specify a time to
        wait within the loop prior to doing the :py:attr:`~Window.flip()`.
        If 0 < msDelay < 100, wait for that long in ms.

        Returns timing stats (in ms) of:

        - average time per frame, for all frames
        - standard deviation of all frames
        - median, as the average of 12 frame times around the median
          (~monitor refresh rate)

        :Author:
            - 2010 written by Jeremy Gray

        """

        # lower bound of 60 samples--need enough to estimate the SD
        nFrames = max(60, nFrames)
        num2avg = 12  # how many to average from around the median
        if len(msg):
            showVisual = False
            showText = True
            myMsg = TextStim(self, text=msg, italic=True,
                             color=(.7, .6, .5), colorSpace='rgb',
                             height=0.1, autoLog=False)
        else:
            showText = False
        if showVisual:
            x, y = self.size
            myStim = GratingStim(self, tex='sin', mask='gauss',
                                 size=[.6 * y / float(x), .6], sf=3.0,
                                 opacity=.2,
                                 autoLog=False)
        clockt = []  # clock times
        # end of drawing time, in clock time units,
        # for testing how long myStim.draw() takes
        drawt = []

        if msDelay > 0 and msDelay < 100:
            doWait = True
            delayTime = msDelay / 1000.  # sec
        else:
            doWait = False

        winUnitsSaved = self.units
        # norm is required for the visual (or text) display, as coded below
        self.units = 'norm'

        # accumulate secs per frame (and time-to-draw) for a bunch of frames:
        rush(True)
        for i in range(5):  # wake everybody up
            self.flip()
        for i in range(nFrames):  # ... and go for real this time
            clockt.append(core.getTime())
            if showVisual:
                myStim.setPhase(1.0 / nFrames, '+', log=False)
                myStim.setSF(3. / nFrames, '+', log=False)
                myStim.setOri(12. / nFrames, '+', log=False)
                myStim.setOpacity(.9 / nFrames, '+', log=False)
                myStim.draw()
            elif showText:
                myMsg.draw()
            if doWait:
                core.wait(delayTime)
            drawt.append(core.getTime())
            self.flip()
        rush(False)

        self.units = winUnitsSaved  # restore

        frameTimes = [(clockt[i] - clockt[i - 1])
                      for i in range(1, len(clockt))]
        drawTimes = [(drawt[i] - clockt[i]) for
                     i in range(len(clockt))]  # == drawing only
        freeTimes = [frameTimes[i] - drawTimes[i] for
                     i in range(len(frameTimes))]  # == unused time

        # cast to float so that the resulting type == type(0.123)
        # for median
        frameTimes.sort()
        # median-most slice
        msPFmed = 1000. * float(numpy.average(
            frameTimes[((nFrames - num2avg) // 2):((nFrames + num2avg) // 2)]))
        msPFavg = 1000. * float(numpy.average(frameTimes))
        msPFstd = 1000. * float(numpy.std(frameTimes))
        msdrawAvg = 1000. * float(numpy.average(drawTimes))
        msdrawSD = 1000. * float(numpy.std(drawTimes))
        msfree = 1000. * float(numpy.average(freeTimes))

        return msPFavg, msPFstd, msPFmed  # msdrawAvg, msdrawSD, msfree

    def _startOfFlip(self):
        """Custom hardware classes may want to prevent flipping from
        occurring and can override this method as needed.

        Return `True` to indicate hardware flip.
        """
        return True

    def _renderFBO(self):
        """Perform a warp operation.

        (in this case a copy operation without any warping)
        """
        GL.glBegin(GL.GL_QUADS)
        GL.glTexCoord2f(0.0, 0.0)
        GL.glVertex2f(-1.0, -1.0)
        GL.glTexCoord2f(0.0, 1.0)
        GL.glVertex2f(-1.0, 1.0)
        GL.glTexCoord2f(1.0, 1.0)
        GL.glVertex2f(1.0, 1.0)
        GL.glTexCoord2f(1.0, 0.0)
        GL.glVertex2f(1.0, -1.0)
        GL.glEnd()

    def _prepareFBOrender(self):
        GL.glUseProgram(self._progFBOtoFrame)

    def _finishFBOrender(self):
        GL.glUseProgram(0)

    def _afterFBOrender(self):
        pass

    def _endOfFlip(self, clearBuffer):
        """Override end of flip with custom color channel masking if required.
        """
        if clearBuffer:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)


def getMsPerFrame(myWin, nFrames=60, showVisual=False, msg='', msDelay=0.):
    """
    Deprecated: please use the getMsPerFrame method in the
    `psychopy.visual.Window` class.

    Assesses the monitor refresh rate (average, median, SD) under current
    conditions, over at least 60 frames.

    Records time for each refresh (frame) for n frames (at least 60), while
    displaying an optional visual. The visual is just eye-candy to show that
    something is happening when assessing many frames. You can also give it
    text to display instead of a visual, e.g.,
    msg='(testing refresh rate...)'; setting msg implies showVisual == False.
    To simulate refresh rate under
    cpu load, you can specify a time to wait within the loop prior to
    doing the win.flip(). If 0 < msDelay < 100, wait for that long in ms.

    Returns timing stats (in ms) of:

    - average time per frame, for all frames
    - standard deviation of all frames
    - median, as the average of 12 frame times around the median
      (~monitor refresh rate)

    :Author:
        - 2010 written by Jeremy Gray
    """
    return myWin.getMsPerFrame(nFrames=60, showVisual=showVisual, msg=msg,
                               msDelay=0.)
