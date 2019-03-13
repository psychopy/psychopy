#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A class representing a window for displaying one or more stimuli"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

import ctypes
import os
import sys
import weakref
import atexit

from builtins import map
from builtins import object
from builtins import range
from builtins import str
from past.builtins import basestring

from psychopy.contrib.lazy_import import lazy_import
from psychopy import colors
# try to find avbin (we'll overload pyglet's load_library tool and then
# add some paths)
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
from . import backends

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import convertToPix
import psychopy.tools.viewtools as viewtools
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

# keep track of windows that have been opened
# Use a list of weak references so that we don't stop the window being deleted
class OpenWinList(list):

    def append(self, item):
        list.append(self, weakref.ref(item))

    def remove(self, item):
        for ref in self:
            obj = ref()
            if obj is None or item == obj:
                list.remove(self, ref)
openWindows = core.openWindows = OpenWinList()  # core needs this for wait()


class Window(object):
    """Used to set up a context in which to draw objects,
    using either `pyglet <http://www.pyglet.org>`_,
    `pygame <http://www.pygame.org>`_, or `glfw <https://www.glfw.org/>_`.

    The pyglet backend allows multiple windows to be created, allows the user
    to specify which screen to use (if more than one is available, duh!) and
    allows movies to be rendered.

    The glfw backend is a new addition which provides most of the same features
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
                 checkTiming=True,
                 useFBO=False,
                 useRetina=True,
                 autoLog=True,
                 *args,
                 **kwargs):
        """
        These attributes can only be set at initialization. See further down
        for a list of attributes which can be changed after initialization
        of the Window, e.g. color, colorSpace, gamma etc.

        :Parameters:

            size : (800,600)
                Size of the window in pixels (X,Y)
            pos : *None* or (x,y)
                Location of the window on the screen
            color : [0,0,0]
                Color of background as [r,g,b] list or single value.
                Each gun can take values between -1 and 1
            fullscr : *None*, True or False
                Better timing can be achieved in full-screen mode
            allowGUI :  *None*, True or False (if None prefs are used)
                If set to False, window will be drawn with no frame and
                no buttons to close etc...
            winType :  *None*, 'pyglet', 'pygame'
                If None then PsychoPy will revert to user/site preferences
            monitor : *None*, string or a `~psychopy.monitors.Monitor` object
                The monitor to be used during the experiment
            units :  *None*, 'height' (of the window), 'norm' (normalised),
                'deg', 'cm', 'pix'
                Defines the default units of stimuli drawn in the window
                (can be overridden by each stimulus)
                See :ref:`units` for explanation of options.
            screen : *0*, 1 (or higher if you have many screens)
                Specifies the physical screen that stimuli will appear on
                (pyglet winType only)
            viewScale : *None* or [x,y]
                Can be used to apply a custom scaling to the current units
                of the :class:`~psychopy.visual.Window`.
            viewPos : *None*, or [x,y]
                If not None, redefines the origin within the window, in the
                ref:`units` of the window. Values outside the borders will be
                clamped to lie on the border.
            viewOri : *0* or any numeric value
                A single value determining the orientation of the view in degs
            waitBlanking : *None*, True or False.
                After a call to flip() should we wait for the blank before
                the script continues
            bitsMode :
                DEPRECATED in 1.80.02. Use BitsSharp class from pycrsltd
                instead.
            checkTiming: True of False
                Whether to calculate frame duration on initialization.
                Estimated duration is saved in [Window].monitorFramePeriod.
            allowStencil : True or *False*
                When set to True, this allows operations that use
                the OpenGL stencil buffer
                (notably, allowing the class:`~psychopy.visual.Aperture`
                to be used).
            multiSample : True or *False*
                If True and your graphics driver supports multisample buffers,
                multiple color samples will be taken per-pixel, providing an
                anti-aliased image through spatial filtering.
                (Cannot be changed after opening a window, pyglet only)
            numSamples : *2* or integer >2
                A single value specifying the number of samples per pixel if
                multisample is enabled. The higher the number, the better the
                image quality, but can delay frame flipping.
                (The largest number of samples is determined by GL_MAX_SAMPLES,
                usually 16 or 32 on newer hardware, will crash if number
                is invalid)
            stereo : True or *False*
                If True and your graphics card supports quad buffers then
                this will be enabled.
                You can switch between left and right-eye scenes for drawing
                operations using :func:`~psychopy.visual.Window.setBuffer`
            useRetina : *True* or False
                In PsychoPy >1.85.3 this should always be True as pyglet
                (or Apple) no longer allows us to create a non-retina display.
                NB when you use Retina display the initial win size
                request will be in the larger pixels but subsequent use of
                units='pix' should refer to the tiny Retina pixels. Window.size
                will give the actual size of the screen in Retina pixels

            :note: Preferences. Some parameters (e.g. units) can now be given
                default values in the user/site preferences and these will be
                used if None is given here. If you do specify a value here it
                will take precedence over preferences.

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
        self.size = numpy.array(size, numpy.int)
        self.pos = pos
        # this will get overridden once the window is created
        self.winHandle = None
        self.useFBO = useFBO
        self.useRetina = useRetina and sys.platform == 'darwin'

        self._toLog = []
        self._toCall = []
        # settings for the monitor: local settings (if available) override
        # monitor
        # if we have a monitors.Monitor object (psychopy 0.54 onwards)
        # convert to a Monitor object
        if not monitor:
            self.monitor = monitors.Monitor('__blank__', autoLog=autoLog)
        elif isinstance(monitor, basestring):
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

        if units is None:
            units = prefs.general['units']
        self.units = units

        if allowGUI is None:
            allowGUI = prefs.general['allowGUI']
        self.allowGUI = allowGUI

        self.screen = screen

        # parameters for transforming the overall view
        self.viewScale = val2array(viewScale)
        if self.viewPos is not None and self.units is None:
            raise ValueError('You must define the window units to use viewPos')
        self.viewPos = val2array(viewPos, withScalar=False)
        self.viewOri = float(viewOri)
        if self.viewOri != 0. and self.viewPos is not None:
            msg = "Window: viewPos & viewOri are currently incompatible"
            raise NotImplementedError(msg)
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
            self._projectionMatrix = viewtools.orthoProjectionMatrix(-1, 1, -1, 1, -1, 1)

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
            winType = prefs.general['winType']
        self.winType = winType

        # setup the context
        self.backend = backends.getBackend(win=self, *args, **kwargs)
        self.winHandle = self.backend.winHandle
        global GL
        GL = self.backend.GL

        # Code to allow iohub to know id of any psychopy windows created
        # so kb and mouse event filtering by window id can be supported.
        #
        # If an iohubConnection is active, give this window os handle to
        # to the ioHub server. If windows were already created before the
        # iohub was active, also send them to iohub.
        #
        if IOHUB_ACTIVE:
            from psychopy.iohub.client import ioHubConnection
            if ioHubConnection.ACTIVE_CONNECTION:
                winhwnds = []
                for w in openWindows:
                    winhwnds.append(w()._hw_handle)
                if self.winHandle not in winhwnds:
                    winhwnds.append(self._hw_handle)
                conn = ioHubConnection.ACTIVE_CONNECTION
                conn.registerWindowHandles(*winhwnds)

        # near and far clipping planes
        self._nearClip = 0.1
        self._farClip = 100.0

        # check whether shaders are supported
        # also will need to check for ARB_float extension,
        # but that should be done after context is created
        self._haveShaders = self.backend.shadersSupported

        self._setupGL()

        self.blendMode = self.blendMode

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

        self._toDraw = []
        self._toDrawDepths = []
        self._eventDispatchers = []

        self.lastFrameT = core.getTime()
        self.waitBlanking = waitBlanking

        # set the swap interval if using GLFW
        if self.winType == 'glfw':
            self.backend.setSwapInterval(int(waitBlanking))

        self.refreshThreshold = 1.0  # initial val needed by flip()

        # over several frames with no drawing
        self._monitorFrameRate = None
        # for testing when to stop drawing a stim:
        self.monitorFramePeriod = 0.0
        if checkTiming:
            self._monitorFrameRate = self.getActualFrameRate()
        if self._monitorFrameRate is not None:
            self.monitorFramePeriod = 1.0 / self._monitorFrameRate
            self.refreshThreshold = 1.0 / self._monitorFrameRate * 1.2
        else:
            self.refreshThreshold = 1.0 / 60 * 1.2  # maybe a flat panel?
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
    def units(self, value):
        """*None*, 'height' (of the window), 'norm', 'deg', 'cm', 'pix'
        Defines the default units of stimuli initialized in the window.
        I.e. if you change units, already initialized stimuli won't change
        their units.

        Can be overridden by each stimulus, if units is specified on
        initialization.
        See :ref:`units` for explanation of options."""
        self.__dict__['units'] = value

    def setUnits(self, value, log=True):
        setAttribute(self, 'units', value, log=log)

    @attributeSetter
    def viewPos(self, value):
        """The origin of the window onto which stimulus-objects are drawn.

        The value should be given in the units defined for the window. NB:
        Never change a single component (x or y) of the origin, instead replace
        the viewPos-attribute in one shot, e.g.:
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
        """Set whether fullscreen mode is True or False (not all backends can
        toggle an open window)
        """
        self.backend.setFullScr(value)
        self.__dict__['fullscr'] = value
        self._isFullScr = value

    @attributeSetter
    def waitBlanking(self, value):
        """*None*, True or False.
        After a call to flip() should we wait for the blank before the
        script continues
        """
        self.__dict__['waitBlanking'] = value

    @attributeSetter
    def recordFrameIntervals(self, value):
        """To provide accurate measures of frame intervals, to determine
        whether frames are being dropped. The intervals are the times between
        calls to `.flip()`. Set to `True` only during the time-critical parts
        of the script. Set this to `False` while the screen is not being
        updated, i.e., during any slow, non-frame-time-critical sections of
        your code, including inter-trial-intervals, `event.waitkeys()`,
        `core.wait()`, or `image.setImage()`.

        see also:
            Window.saveFrameIntervals()
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

        :Parameters:

        fileName : *None* or the filename (including path if necessary) in
            which to store the data.
            If None then 'lastFrameIntervals.log' will be used.

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
        """Make this window current. If useFBO=True, the framebuffer is bound
        after the context switch.
        """
        self.backend.setCurrent()

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
        """Send a log message that should be time-stamped at the next .flip()
        command.

        :parameters:
            - msg: the message to be logged
            - level: the level of importance for the message
            - obj (optional): the python object that might be associated with
              this message if desired
        """

        self._toLog.append({'msg': msg, 'level': level, 'obj': repr(obj)})

    def callOnFlip(self, function, *args, **kwargs):
        """Call a function immediately after the next .flip() command.

        The first argument should be the function to call, the following args
        should be used exactly as you would for your normal call to the
        function (can use ordered arguments or keyword arguments as normal).

        e.g. If you have a function that you would normally call like this::

            pingMyDevice(portToPing, channel=2, level=0)

        then you could call callOnFlip() to have the function call
        synchronized with the frame flip like this::

            win.callOnFlip(pingMyDevice, portToPing, channel=2, level=0)

        """
        self._toCall.append({'function': function,
                             'args': args,
                             'kwargs': kwargs})

    def timeOnFlip(self, obj, attrib):
        """Retrieves the time on the next flip and assigns it to the attrib
        for this obj.

        usage:
            win.getTimeOnFlip(myTimingDict, 'tStartRefresh')

        :parameters:
            - obj:
                must be a mutable object (usually a dict of class instance)
            - attrib: str
                if obj has this
        """
        self.callOnFlip(self._assignFlipTime, obj, attrib)

    def _assignFlipTime(self, obj, attrib):
        """Helper function to assign the time of last flip to the obj.attrib

        :parameters:
            - obj:
                must be a mutable object (usually a dict of class instance)
            - attrib: str
                if obj has this
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


    @classmethod
    def dispatchAllWindowEvents(cls):
        """
        Dispatches events for all pyglet windows. Used by iohub 2.0
        psychopy kb event integration.
        """
        self.backend.dispatchEvents()

    def flip(self, clearBuffer=True):
        """Flip the front and back buffers after drawing everything for your
        frame. (This replaces the win.update() method, better reflecting what
        is happening underneath).

        Examples
        --------

        Results in a clear screen after flipping::

            win.flip(clearBuffer=True)

        The screen is not cleared (so represent the previous screen)::

            win.flip(clearBuffer=False)

        """
        for thisStim in self._toDraw:
            thisStim.draw()

        flipThisFrame = self._startOfFlip()
        self.resetEyeTransform(False)  # reset transformations
        if self.useFBO:
            if flipThisFrame:
                self._prepareFBOrender()
                # need blit the framebuffer object to the actual back buffer

                # unbind the framebuffer as the render target
                GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, 0)
                GL.glDisable(GL.GL_BLEND)
                stencilOn = GL.glIsEnabled(GL.GL_STENCIL_TEST)
                GL.glDisable(GL.GL_STENCIL_TEST)

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
        self._frameTime = now = logging.defaultClock.getTime()

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

    def update(self):
        """Deprecated: use Window.flip() instead
        """
        # clearBuffer was the original behaviour for win.update()
        self.flip(clearBuffer=True)

    def multiFlip(self, flips=1, clearBuffer=True):
        """
        Flip multiple times while maintaining the display constant.
        Use this method for precise timing.

        WARNING: This function should not be used. See the `Notes` section
        for details.

        :Parameters:

        flips: int, optional
            The number of monitor frames to flip. Floats will be
            rounded to integers, and a warning will be emitted.
            ``Window.multiFlip(flips=1)`` is equivalent to ``Window.flip()``.
            Defaults to `1`.

        clearBuffer: bool, optional
            Whether to clear the screen after the last flip.
            Defaults to `True`.

        Example::

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

        :Notes:
        This function can behave unpredictably, and the PsychoPy authors
        recommend against using it.
        See https://github.com/psychopy/psychopy/issues/867 for more
        information.

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
        GL_BACK_LEFT This then needs to be flipped once both eye's buffers
        have been rendered.

        Typical usage::

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

    def clearBuffer(self):
        """Clear the back buffer (to which you are currently drawing) without
        flipping the window. Useful if you want to generate movie sequences
        from the back buffer without actually taking the time to flip the
        window.
        """
        # reset returned buffer for next frame
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

    @property
    def nearClip(self):
        """Distance to the near clipping plane in meters."""
        # internally stored as meters, but PsychoPy uses centimeters elsewhere
        # so let's keep that consistent.
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

    @property
    def viewMatrix(self):
        """View matrix defined as a 4x4 numpy array."""
        return self._viewMatrix

    @viewMatrix.setter
    def viewMatrix(self, value):
        self._viewMatrix = numpy.asarray(value, numpy.float32)

    def setPerspectiveView(self, applyTransform=True, **kwargs):
        """Set the projection and view matrix to render with perspective.
        Matrices are computed using values specified in the monitor
        configuration with the scene origin on the screen plane. Calculations
        assume units are in meters.

        Note that the values of 'projectionMatrix' and 'viewMatrix' will be
        replaced when calling this function.

        Parameters
        ----------
        applyTransform : bool
            Apply transformations after computing them in immediate mode. Same
            as calling 'applyEyeTransform' afterwards.
        **kwargs
            Additional arguments to pass to 'applyEyeTransform()'

        Returns
        -------
        None

        """
        # NB - we should eventually compute these matrices lazily since they may
        # not change over the course of an experiment under most circumstances.
        #
        scrDistM = self.scrDistCM / 100.0
        frustum = viewtools.computeFrustum(
            self.scrWidthCM / 100.0,  # width of screen
            self.size[0] / self.size[1],  # aspect ratio
            scrDistM,  # distance to screen
            nearClip=self._nearClip,
            farClip=self._farClip)

        self._projectionMatrix = viewtools.perspectiveProjectionMatrix(*frustum)

        # translate away from screen
        self._viewMatrix = numpy.identity(4, dtype=numpy.float32)
        self._viewMatrix[2, 3] = -scrDistM  # displace scene away from viewer

        if applyTransform:
            self.applyEyeTransform(**kwargs)

    def applyEyeTransform(self, clearDepth=True):
        """Apply the current view and projection matrices specified by
        'viewMatrix' and 'projectionMatrix' using 'immediate mode' OpenGL.
        Subsequent drawing operations will be affected until 'flip()' is called.

        All transformations in GL_PROJECTION and GL_MODELVIEW matrix stacks will
        be cleared (set to identity) prior to applying.

        Parameters
        ----------
        clearDepth : bool
            Clear the depth buffer. This may be required prior to rendering 3D
            objects.

        """
        GL.glViewport(0, 0, self.size[0], self.size[1])
        GL.glScissor(0, 0, self.size[0], self.size[1])

        # apply the projection and view transformations
        GL.glMatrixMode(GL.GL_PROJECTION)
        #GL.glLoadIdentity()
        projMat = self._projectionMatrix.T.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float))
        GL.glLoadMatrixf(projMat)

        GL.glMatrixMode(GL.GL_MODELVIEW)
        #GL.glLoadIdentity()
        viewMat = self._viewMatrix.T.ctypes.data_as(
            ctypes.POINTER(ctypes.c_float))
        GL.glLoadMatrixf(viewMat)

        if clearDepth:
            #GL.glDepthMask(GL.GL_TRUE)
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    def resetEyeTransform(self, clearDepth=True):
        """Restore the default projection and view settings to PsychoPy
        defaults. Call this prior to drawing 2D stimuli objects (i.e.
        GratingStim, ImageStim, Rect, etc.) if any eye transformations were
        applied for the stimuli to be drawn correctly.

        Returns
        -------
        None

        Notes
        -----
        Calling 'flip()' automatically resets the view and projection to
        defaults. So you don't need to call this unless you are mixing views.

        """
        # should eventually have the same effect as calling _onResize(), so we
        # need to add the retina mode stuff eventually
        GL.glViewport(0, 0, self.size[0], self.size[1])
        GL.glScissor(0, 0, self.size[0], self.size[1])
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-1, 1, -1, 1, -1, 1)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        if clearDepth:
            GL.glClear(GL.GL_DEPTH_BUFFER_BIT)

    def getMovieFrame(self, buffer='front'):
        """Capture the current Window as an image.

        Saves to stack for saveMovieFrames().
        As of v1.81.00 this also returns the frame as a PIL image

        This can be done at any time (usually after a .flip() command).

        Frames are stored in memory until a .saveMovieFrames(filename)
        command is issued. You can issue getMovieFrame() as often
        as you like and then save them all in one go when finished.

        The back buffer will return the frame that hasn't yet been 'flipped'
        to be visible on screen but has the advantage that the mouse and any
        other overlapping windows won't get in the way.

        The default front buffer is to be called immediately after a
        win.flip() and gives a complete copy of the screen at the window's
        coordinates.
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
            top = int((rect[1] / -2. + 0.5) * y)
            w = int((rect[2] / 2. + 0.5) * x) - left
            h = int((rect[3] / -2. + 0.5) * y) - top
        else:
            left = top = 0
            w, h = self.size


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

        if self.useFBO and buffer == 'front':
            GL.glBindFramebufferEXT(GL.GL_FRAMEBUFFER_EXT, self.frameBuffer)
        return im

    def saveMovieFrames(self, fileName, codec='libx264',
                        fps=30, clearFrames=True):
        """Writes any captured frames to disk.

        Will write any format that is understood by PIL (tif, jpg, png, ...)

        :parameters:

            filename: name of file, including path (required)
                The extension at the end of the file determines the type of
                file(s) created. If an image type (e.g. .png) is given, then
                multiple static frames are created. If it is .gif then an
                animated GIF image is created (although you will get higher
                quality GIF by saving PNG files and then combining them in
                dedicated image manipulation software, such as GIMP). On
                Windows and Linux `.mpeg` files can be created if `pymedia`
                is installed. On macOS `.mov` files can be created if the
                pyobjc-frameworks-QTKit is installed.

                Unfortunately the libs used for movie generation can be flaky
                and poor quality. As for animated GIFs, better results can be
                achieved by saving as individual .png frames and then
                combining them into a movie using software like ffmpeg.

            codec: the codec to be used **by moviepy** for mp4/mpg/mov files.
                If None then the default will depend on file extension.
                Can be one of 'libx264','mpeg4' for mp4/mov files.
                Can be 'rawvideo','png' for avi files (not recommended).
                Can be 'libvorbis' for ogv files.

            fps: the frame rate to be used throughout the movie
                **only for quicktime (.mov) movies**

            clearFrames: set this to False if you want the frames to be kept
                for additional calls to `saveMovieFrames`

        Examples::

            # writes a series of static frames as frame001.tif,
            # frame002.tif etc...
            myWin.saveMovieFrames('frame.tif')

            #as of PsychoPy 1.84.1 the following are written with moviepy
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
        _getFrame() and specify a rect to get a sub-region, just as used here

        power2 can be useful with older OpenGL versions to avoid interpolation
        in PatchStim. If power2 or squarePower2, it will expand rect
        dimensions up to next power of two. squarePower2 uses the max
        dimensions. You need to check what your hardware & OpenGL supports,
        and call _getRegionOfFrame as appropriate.
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

    @attributeSetter
    def blendMode(self, blendMode):
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

    @attributeSetter
    def color(self, color):
        """Set the color of the window.

        NB This command sets the color that the blank screen will have on the
        next clear operation. As a result it effectively takes TWO `flip()`
        operations to become visible (the first uses the color to create the
        new screen, the second presents that screen to the viewer). For this
        reason, if you want to changed background color of the window "on the
        fly", it might be a better idea to draw a `visual.Rect` that fills the
        whole window with the desired `Rect.fillColor` attribute.
        That'll show up on first flip.

        See other stimuli (e.g. :ref:`GratingStim.color`) for more info on the
        color attribute which essentially works the same on all PsychoPy
        stimuli.

        See :ref:`colorspaces` for further information about the ways to
        specify colors and their various implications.
        """
        self.setColor(color)

    @attributeSetter
    def colorSpace(self, colorSpace):
        """string. (Documentation for colorSpace is in the stimuli.)

        e.g. :ref:`GratingStim.colorSpace`.

        Usually used in conjunction with ``color`` like this::

            win.colorSpace = 'rgb255'  # changes colorSpace but not
                                       # the value of win.color
            win.color = [0, 0, 255]    # clear blue in rgb255

        See :ref:`colorspaces` for further information about the ways to
        specify colors and their various implications.
        """
        self.__dict__['colorSpace'] = colorSpace

    def setColor(self, color, colorSpace=None, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you want to set color and colorSpace
        simultaneously.
        See `Window.color` for documentation on colors.
        """
        # Set color
        setColor(self, color, colorSpace=colorSpace, operation=operation,
                 rgbAttrib='rgb',  # or 'fillRGB' etc
                 colorAttrib='color')

        # These spaces are 0-centred
        if self.colorSpace in ['rgb', 'dkl', 'lms', 'hsv']:
            # RGB in range 0:1 and scaled for contrast
            desiredRGB = (self.rgb + 1) / 2.0
        # rgb255 and named are not...
        elif self.colorSpace in ['rgb255', 'named']:
            desiredRGB = self.rgb / 255.0
        elif self.colorSpace in ['hex']:
            desiredRGB = [rgbs/255.0 for rgbs in colors.hex2rgb255(color)]
        else:  # some array / numeric stuff
            msg = 'invalid value %r for Window.colorSpace'
            raise ValueError(msg % colorSpace)

        # if it is None then this will be done during window setup
        if self.backend is not None:
            self.backend.setCurrent()  # make sure this window is active
            GL.glClearColor(desiredRGB[0], desiredRGB[1], desiredRGB[2], 1.0)

    def setRGB(self, newRGB):
        """Deprecated: As of v1.61.00 please use `setColor()` instead
        """
        global GL
        self.rgb = val2array(newRGB, False, length=3)
        if self.winType == 'pyglet' and globalVars.currWindow != self:
            self.winHandle.switch_to()
            globalVars.currWindow = self
        GL.glClearColor(((self.rgb[0] + 1.0) / 2.0),
                        ((self.rgb[1] + 1.0) / 2.0),
                        ((self.rgb[2] + 1.0) / 2.0),
                        1.0)

    def _setupGamma(self, gammaVal):
        """A private method to work out how to handle gamma for this Window
        given that the user might have specified an explicit value, or maybe
        gave a Monitor
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
        """Set the monitor gamma for linearization

        (don't use this if using a Bits++ or Bits#)
        Overrides monitor settings.
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
            self.size = numpy.array(actual)

    def _setupGL(self):

        # setup screen color
        self.color = self.color  # call attributeSetter
        GL.glClearDepth(1.0)

        GL.glViewport(0, 0, int(self.size[0]), int(self.size[1]))

        GL.glMatrixMode(GL.GL_PROJECTION)  # Reset The Projection Matrix
        GL.glLoadIdentity()
        GL.gluOrtho2D(-1, 1, -1, 1)

        GL.glMatrixMode(GL.GL_MODELVIEW)  # Reset The Projection Matrix
        GL.glLoadIdentity()

        GL.glDisable(GL.GL_DEPTH_TEST)
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

        If Window was initialized with noGUI=True then the mouse is initially
        set to invisible, otherwise it will initially be visible.

        Usage::

            ``win.mouseVisible = False``
            ``win.mouseVisible = True``
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

        - 'arrow' : Default pointer
        - 'ibeam' : Indicates text can be edited
        - 'crosshair' : Crosshair with hot-spot at center
        - 'hand' : A pointing hand
        - 'hresize' : Double arrows pointing horizontally
        - 'vresize' : Double arrows pointing vertically

        Requires the GLFW backend, otherwise this function does nothing! Note,
        on Windows the 'crosshair' option is XORed with the background color. It
        will not be visible when placed over 50% grey fields.

        :param name: str, type of standard cursor to use
        :return:

        """
        pass

    def getActualFrameRate(self, nIdentical=10, nMaxFrames=100,
                           nWarmUpFrames=10, threshold=1):
        """Measures the actual fps for the screen.

        This is done by waiting (for a max of nMaxFrames) until [nIdentical]
        frames in a row have identical frame times
        (std dev below [threshold] ms).

        If there is no such sequence of identical frames a warning is logged
        and `None` will be returned.

        :parameters:
            nIdentical:
                the number of consecutive frames that will be evaluated.
                Higher --> greater precision. Lower --> faster.

            nMaxFrames:
                the maximum number of frames to wait for a matching set of
                nIdentical

            nWarmUpFrames:
                the number of frames to display before starting the test
                (this is in place to allow the system to settle after opening
                the `Window` for the first time.

            threshold:
                the threshold for the std deviation (in ms) before the set
                are considered a match

        """
        if nIdentical > nMaxFrames:
            raise ValueError('nIdentical must be equal to or '
                             'less than nMaxFrames')
        recordFrmIntsOrig = self.recordFrameIntervals
        # run warm-ups
        self.recordFrameIntervals = False
        for frameN in range(nWarmUpFrames):
            self.flip()
        # run test frames
        self.recordFrameIntervals = True
        for frameN in range(nMaxFrames):
            self.flip()
            if (len(self.frameIntervals) >= nIdentical and
                    (numpy.std(self.frameIntervals[-nIdentical:]) <
                     (threshold / 1000.0))):
                rate = 1.0 / numpy.mean(self.frameIntervals[-nIdentical:])
                if self.screen is None:
                    scrStr = ""
                else:
                    scrStr = " (%i)" % self.screen
                if self.autoLog:
                    msg = 'Screen%s actual frame rate measured at %.2f'
                    logging.debug(msg % (scrStr, rate))
                self.recordFrameIntervals = recordFrmIntsOrig
                self.frameIntervals = []
                return rate
        # if we got here we reached end of maxFrames with no consistent value
        msg = ("Couldn't measure a consistent frame rate.\n"
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
        e.g., msg='(testing refresh rate...)'; setting msg implies
        showVisual == False.

        To simulate refresh rate under cpu load, you can specify a time to
        wait within the loop prior to doing the win.flip().
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
        occurring and can override this method as needed. Return True to
        indicate hardware flip.
        """
        return True

    def _renderFBO(self):
        """Perform a warp operation
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
        """Override end of flip with custom color channel masking if required
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

