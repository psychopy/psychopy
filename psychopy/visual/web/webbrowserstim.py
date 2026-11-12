#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A stimulus showing a web page, which participants can use with the mouse
and keyboard."""

import collections
import itertools
import time
import weakref

import numpy as np

from psychopy import core, layout, logging
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin
from psychopy.visual.helpers import callOnGLThread
from psychopy.visual.backends import _events
import psychopy.tools.pygletgl as GL

from . import _geometry, _glext, _gpushare, _host, _protocol
from ._shm import FrameRing
from ._texture import StreamingTexture

__all__ = ['WebBrowserStim']

# page size when neither `size` nor `resolution` give one
DEFAULT_RESOLUTION = (1024, 768)

# seconds to wait for the size to stop changing before resizing the page to
# match it (with `resolution='auto'`), as each resize re-lays out the page
_RESIZE_DELAY = 0.2

# input is only passed on if the stimulus was drawn this recently (seconds)
_DRAWN_RECENTLY = 0.25

# seconds between mouse movements passed on, others in between are merged
_MOVE_INTERVAL = 0.004

# modifier flags as `pyglet.window.key` defines them
_MOD_CTRL = 1 << 1
_MOD_COMMAND = 1 << 6

# keys which type text, named as window listeners name them, besides letters
# and digits
_TEXT_KEYS_ = {
    'space', 'minus', 'equal', 'bracketleft', 'bracketright', 'backslash',
    'semicolon', 'apostrophe', 'grave', 'comma', 'period', 'slash', 'num_add',
    'num_subtract', 'num_multiply', 'num_divide', 'num_decimal', 'num_equal'
} | {'num_{}'.format(i) for i in range(10)}

# window cursor to show for each Qt cursor shape the page asks for
_CURSORS_ = {
    'ArrowCursor': 'arrow', 'IBeamCursor': 'ibeam',
    'PointingHandCursor': 'hand', 'CrossCursor': 'crosshair',
    'SizeHorCursor': 'hresize', 'SizeVerCursor': 'vresize',
    'SplitHCursor': 'hresize', 'SplitVCursor': 'vresize',
    'ForbiddenCursor': 'no', 'WhatsThisCursor': 'help'
}


# whether each window can share frames on the GPU, worked out once for each
_gpuSupport = weakref.WeakKeyDictionary()


def _gpuSupportFor(win):
    """Whether frames can be shared on the GPU with a window's OpenGL context
    (see `_gpushare`).

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        The window.

    Returns
    -------
    tuple
        `(gl, uuids)`, the context's OpenGL functions and its device and
        driver UUIDs, or `(None, reason)` if it can't.

    """
    try:
        return _gpuSupport[win]
    except KeyError:
        pass
    if not _protocol.GPU_SHARING_PLATFORM:
        result = (None, "it is only done on Linux and Windows")
    elif not _host.gpuSharingAllowed():
        result = (None, "the {} environment variable turns it off".format(
            _host.ENV_GPU_SHARING))
    elif win.winType not in ('pyglet', 'glfw'):
        result = (None, "it isn't done with {} windows".format(win.winType))
    else:
        try:
            win._setCurrent()
            gl = _glext.GLFunctions(_glext.platformGetProcAddress())
            if gl.supportsSharing():
                result = (gl, gl.uuids())
            else:
                result = (None, "the graphics driver can't import memory "
                                "and semaphores ({})".format(
                                    ', '.join(_glext.SHARING_EXTENSIONS)))
        except Exception as err:
            result = (None, "checking the graphics driver failed: {}".format(
                err))
    _gpuSupport[win] = result
    return result


class WebBrowserStim(BaseVisualStim, ContainerMixin):
    """A web page drawn as a stimulus, which participants can use with the
    mouse and keyboard.

    Pages are rendered with Chromium (Qt WebEngine) in a separate process,
    started when the first `WebBrowserStim` is made, and copied into the window
    each time they change. Install it with ``pip install psychopy[web]``.

    When `interactive`, mouse input over the stimulus is passed to the page,
    clicking it gives it keyboard focus (as for an editable `TextBox2`), and
    keys typed while it has focus are passed to the page. Keys also still go
    to keyboards and `event.getKeys()` as usual, including the escape key.

    Pages can send data to the experiment with ``psychopy.send(data)`` in
    JavaScript, which `getMessages` returns, and receive data sent with
    `sendMessage` by registering a function with
    ``psychopy.onMessage(handler)``.

    Frames are passed to the window on the GPU when the graphics driver can
    (see `gpuSharing`), and through shared memory otherwise.

    Each page is a private (incognito) browsing session: nothing it stores is
    kept once the experiment ends. Downloads, file uploads, new windows (by
    default), and permissions such as the camera and location are refused, and
    dialogs (``alert()``, ``confirm()``, ``prompt()``) are dismissed straight
    away and logged.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window to draw the page in.
    url : str or None
        Address of the page to show.
    html : str or None
        HTML of the page to show, in place of `url`.
    baseUrl : str or None
        Address relative links in `html` are relative to, e.g. a ``file://``
        folder to load local images from (see `setHtml`).
    resolution : str or ArrayLike
        Size `(w, h)` of the page in pixels. `'auto'` uses the size it is
        drawn at on screen, so it is as sharp as possible.
    zoom : float or None
        How much the page is zoomed. `None` zooms so that the page's pixels
        are the size of the window's 'pix' units with `resolution='auto'`
        (e.g. 2 on Retina displays), and 1 otherwise.
    pos : ArrayLike
        Position of the stimulus.
    size : ArrayLike or None
        Size of the stimulus. `None` uses `resolution` (or 1024 x 768 pixels
        if that is `'auto'`), and if one dimension is `None` it is set to keep
        the aspect ratio of `resolution`.
    units : str
        Units of `pos` and `size`, the window's if empty.
    ori : float
        Orientation in degrees.
    anchor : str
        Point of the stimulus `pos` gives the position of, e.g. `'center'`.
    opacity : float
        Opacity, from 0 (transparent) to 1 (opaque).
    interactive : bool
        Whether mouse and keyboard input is passed to the page.
    allowedUrls : list of str or None
        Addresses the page may navigate to, as glob patterns (e.g.
        ``'https://example.org/*'``). `None` allows any.
    javascript : bool
        Whether the page may run JavaScript.
    transparent : bool
        Whether parts of the page without a background are transparent, rather
        than white.
    muted : bool
        Whether the page's audio is muted.
    maxFrameRate : float
        Most frames per second to copy from the page, 0 for no limit.
    newWindowPolicy : str
        What to do with links which would open a new window, `'same'` opens
        them in this page, `'block'` ignores them.
    interpolate : bool
        Whether to interpolate linearly when the page is scaled to its size.
    gpuSharing : bool or str
        Whether frames may be passed from the web browser to the window on the
        GPU, which saves copying them through the CPU and memory. `'auto'`
        does so when the window's graphics driver supports it (on Linux and
        Windows) and otherwise uses shared memory, `True` does the same but
        warns when it can't, and `False` always uses shared memory. If frames
        on the GPU fail, or the check made when they start fails, shared
        memory is used. Setting the environment variable
        `PSYCHOPY_WEB_GPU_SHARING` to `0` turns it off for every page.
        `frameTransport` says which is used.
    flipHoriz, flipVert : bool
        Whether to mirror the page horizontally or vertically.
    waitForLoad : bool
        Whether to wait for the page to load before returning.
    timeout : float
        Seconds to wait for the page to load if `waitForLoad`.
    name : str or None
        Name of the stimulus, for logging.
    autoLog : bool or None
        Whether to log changes automatically.
    autoDraw : bool
        Whether to draw the stimulus on every flip.
    depth : float
        Depth, for ordering stimuli drawn automatically.

    Examples
    --------
    Show a questionnaire, and wait for it to send its answers::

        page = visual.WebBrowserStim(win, url='https://example.org/form',
                                     size=(1.6, 0.9), units='height')
        answers = None
        while answers is None:
            page.draw()
            win.flip()
            for msg in page.getMessages():
                answers = msg

    """
    def __init__(self,
                 win,
                 url=None,
                 html=None,
                 baseUrl=None,
                 resolution='auto',
                 zoom=None,
                 pos=(0, 0),
                 size=None,
                 units='',
                 ori=0.0,
                 anchor='center',
                 opacity=1.0,
                 interactive=True,
                 allowedUrls=None,
                 javascript=True,
                 transparent=False,
                 muted=False,
                 maxFrameRate=60,
                 newWindowPolicy='same',
                 interpolate=True,
                 gpuSharing='auto',
                 flipHoriz=False,
                 flipVert=False,
                 waitForLoad=False,
                 timeout=10.0,
                 name=None,
                 autoLog=None,
                 autoDraw=False,
                 depth=0):

        # what local vars are defined (these are the init params) for use
        self._initParams = dir()
        self._initParams.remove('self')

        super(WebBrowserStim, self).__init__(
            win, units=units, name=name, autoLog=False)

        if gpuSharing not in (True, False, 'auto'):
            raise ValueError(
                "`gpuSharing` must be True, False or 'auto', not {!r}".format(
                    gpuSharing))
        if newWindowPolicy not in ('same', 'block'):
            raise ValueError(
                "`newWindowPolicy` must be 'same' or 'block', not {!r}".format(
                    newWindowPolicy))

        # used by property setters, so set first
        self._channel = None
        self._closed = False
        self._resolutionSetting = resolution
        self._resolution = None
        self._resizeAt = None
        self._interactive = False
        self._texture = None

        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.anchor = anchor
        self.pos = pos
        self.ori = ori
        self.size = size
        self.depth = depth
        self.opacity = opacity
        self._interpolate = bool(interpolate)
        if zoom is None:
            zoom = win.pixScaleFactor if resolution == 'auto' else 1.0
        self._zoom = float(zoom)
        self._muted = bool(muted)
        self._maxFrameRate = float(maxFrameRate or 0)

        # page state, from the server's messages
        self._url = url or ''
        self._title = ''
        self._loadProgress = 0
        self._isLoading = True
        self._loadOk = False
        self._loadError = None
        self._serverGone = False
        self._messages = collections.deque()
        self.consoleMessages = collections.deque(maxlen=1000)
        self._jsIds = itertools.count(1)
        self._jsCallbacks = {}
        self._jsResults = {}

        # frames, in shared memory or on the GPU (see `_gpushare`): slots the
        # server sent to check, the slots frames come in, and what is drawn,
        # as `(transport, slots, slot, gen)`
        self._gpuSharing = gpuSharing
        self._gpuPending = None
        self._gpuSlots = None
        self._gpuGen = None
        self._gpuRetired = False
        self._shown = None
        self._ring = None
        self._dpr = 1.0
        self._heldFrames = []
        self.frameSeq = 0
        self.lastFrameCaptureTime = None
        # where the page drawn was scrolled to, its zoom and document size
        self._frameScroll = (0., 0.)
        self._frameZoom = self._zoom
        self._frameDocSize = None
        # server frame times are `time.perf_counter()`, which is the same
        # clock in every process
        self._clockOffset = core.getTime() - time.perf_counter()
        self._lastDrawTime = -np.inf

        # input
        self._hasFocus = False
        self._hover = False
        self._capture = None
        self._buttons = set()
        self._pendingMove = None
        self._lastMoveTime = -np.inf
        self._pendingKey = None
        self._cursorShape = None
        self._cursorShown = None

        # open the page
        host = _host.BrowserHost.get()
        self._channel = host.openChannel()
        cfg = dict(
            w=self._resolution[0], h=self._resolution[1], zoom=self._zoom,
            javascript=bool(javascript), transparent=bool(transparent),
            bgColor=None if transparent else (255, 255, 255, 255),
            muted=self._muted, maxFps=self._maxFrameRate,
            allowedUrls=list(allowedUrls) if allowedUrls else None,
            newWindowPolicy=newWindowPolicy)
        if html is not None:
            cfg.update(html=html, baseUrl=baseUrl)
        elif url:
            cfg.update(url=url)
        if gpuSharing:
            if host.info.get('gpu') != 'auto':
                gl, info = None, "it is turned off for the web browser"
            else:
                gl, info = _gpuSupportFor(win)
            if gl is not None:
                cfg['gpu'] = dict(deviceUUID=info[0], driverUUID=info[1])
            else:
                self._gpuUnavailable(info)
        self._channel.send('create', **cfg)

        self._pump_ = _host.WindowPump.forWindow(win)
        self._pump_.add(self)
        win.addEventListener(self._onWindowEvent)
        self.interactive = interactive
        self.autoDraw = autoDraw

        # set autoLog now that params have been initialised
        wantLog = autoLog is None and self.win.autoLog
        self.__dict__['autoLog'] = autoLog or wantLog
        if self.autoLog:
            logging.exp("Created {} = {}".format(self.name, self))

        if waitForLoad:
            self.waitForLoad(timeout)

    # ----------------------------------------------------------------------
    # Size and resolution
    #

    @property
    def size(self):
        """Size of the stimulus, in its `units`.

        `None` uses `resolution`, and if one dimension is `None` it is set to
        keep the aspect ratio of `resolution`.
        """
        return BaseVisualStim.size.fget(self)

    @size.setter
    def size(self, value):
        self._requestedSize = value
        if value is None or isinstance(value, (int, float)):
            value = [value, value]
        value = list(value)
        if value[0] is None or value[1] is None:
            if self._resolutionSetting == 'auto':
                res = DEFAULT_RESOLUTION
            else:
                res = self._resolutionSetting
            if value[0] is None and value[1] is None:
                value = layout.Size(
                    np.asarray(res, dtype=float) / self.win.pixScaleFactor,
                    units='pix', win=self.win)
            elif value[0] is None:
                value[0] = value[1] * res[0] / res[1]
            else:
                value[1] = value[0] * res[1] / res[0]
        BaseVisualStim.size.fset(self, value)
        self._updateResolution()

    @property
    def resolution(self):
        """Size `(w, h)` of the page in pixels (`tuple` of `int`).

        Set to `'auto'` to use the size the stimulus is drawn at on screen.
        """
        return self._resolution

    @resolution.setter
    def resolution(self, value):
        self._resolutionSetting = value
        self._updateResolution()

    def _updateResolution(self):
        """Work out the page's size, resizing it if it has changed."""
        if self._resolutionSetting == 'auto':
            sizePix = np.abs(self._size.pix) * self.win.pixScaleFactor
            res = (max(1, int(round(sizePix[0]))),
                   max(1, int(round(sizePix[1]))))
            delay = _RESIZE_DELAY
        else:
            res = tuple(int(round(v)) for v in self._resolutionSetting)
            delay = 0.
        if res == self._resolution:
            return
        first = self._resolution is None
        self._resolution = res
        if not first:
            self._resizeAt = time.perf_counter() + delay

    def _sendResize(self):
        if self._resizeAt is not None and time.perf_counter() >= self._resizeAt:
            self._resizeAt = None
            self._send('resize', w=self._resolution[0], h=self._resolution[1])

    @property
    def zoom(self):
        """How much the page is zoomed (`float`)."""
        return self._zoom

    @zoom.setter
    def zoom(self, value):
        self._zoom = float(value)
        self._send('zoom', factor=self._zoom)

    @property
    def interpolate(self):
        """Whether to interpolate linearly when the page is scaled to its size
        (`bool`)."""
        return self._interpolate

    @interpolate.setter
    def interpolate(self, value):
        self._interpolate = bool(value)
        if self._texture is not None:
            self._texture.interpolate = self._interpolate
        for slots in (self._gpuSlots, self._shown and self._shown[1]):
            if slots:
                slots.interpolate = self._interpolate

    @property
    def muted(self):
        """Whether the page's audio is muted (`bool`)."""
        return self._muted

    @muted.setter
    def muted(self, value):
        self._muted = bool(value)
        self._send('setMuted', muted=self._muted)

    @property
    def maxFrameRate(self):
        """Most frames per second to copy from the page, 0 for no limit
        (`float`)."""
        return self._maxFrameRate

    @maxFrameRate.setter
    def maxFrameRate(self, value):
        self._maxFrameRate = float(value or 0)
        self._send('setMaxFps', fps=self._maxFrameRate)

    @property
    def gpuSharing(self):
        """Whether frames may be passed on the GPU (`bool` or `'auto'`), as
        given when the stimulus was made. See `frameTransport` for whether they
        are."""
        return self._gpuSharing

    @property
    def frameTransport(self):
        """How the frame drawn reached the window (`str` or `None`): `'gpu'`
        on the GPU, `'shm'` through shared memory, `None` before the first."""
        return None if self._shown is None else self._shown[0]

    def _gpuUnavailable(self, reason):
        """Note that frames won't be passed on the GPU, and why."""
        msg = "{}: using shared memory for frames, as they can't be passed " \
              "on the GPU ({})".format(self.name, reason)
        if self._gpuSharing is True:
            logging.warning(msg)
        else:
            logging.info(msg)

    # ----------------------------------------------------------------------
    # The page
    #

    def _send(self, op, **msg):
        if self._channel is not None:
            self._channel.send(op, **msg)

    @property
    def url(self):
        """Address of the page shown (`str`). Set it to go to another page."""
        self._pump()
        return self._url

    @url.setter
    def url(self, value):
        self.setUrl(value)

    def setUrl(self, url, log=None):
        """Go to another page.

        Parameters
        ----------
        url : str
            Address of the page.
        log : bool or None
            Whether to log the change, `autoLog` if `None`.

        Notes
        -----
        A page on another site than the one shown, whether gone to with this
        or by the page itself (e.g. a link), is loaded twice, as Qt WebEngine
        doesn't always show it otherwise. Its scripts run twice, and a page a
        form sent data to is loaded again without the data.

        """
        self._isLoading = True
        self._loadError = None
        self._send('navigate', url=str(url))
        if log or (log is None and self.autoLog):
            self.win.logOnFlip(
                "Set {} url={}".format(self.name, url), level=logging.EXP,
                obj=self)

    def setHtml(self, html, baseUrl=None, log=None):
        """Show a page made from HTML.

        Parameters
        ----------
        html : str
            HTML of the page.
        baseUrl : str or None
            Address relative links in it are relative to.
        log : bool or None
            Whether to log the change, `autoLog` if `None`.

        Notes
        -----
        The page is loaded from a temporary file, with a ``<base>`` element
        added for `baseUrl` (unless it has one), so its origin is that file's
        (``file://``) rather than `baseUrl`'s. It can load scripts, images
        etc. from anywhere, but scripts' requests to other origins (with
        `fetch` etc.) need those to allow them (CORS), and it doesn't see
        `baseUrl`'s cookies or storage. `url` is `baseUrl` (or
        ``about:blank``) while it's shown.

        """
        self._isLoading = True
        self._loadError = None
        self._send('setHtml', html=html, baseUrl=baseUrl)
        if log or (log is None and self.autoLog):
            self.win.logOnFlip(
                "Set {} html ({} characters)".format(self.name, len(html)),
                level=logging.EXP, obj=self)

    def back(self):
        """Go back to the previous page."""
        self._send('history', action='back')

    def forward(self):
        """Go forward to the next page, after going back."""
        self._send('history', action='forward')

    def reload(self):
        """Load the page again."""
        self._isLoading = True
        self._loadError = None
        self._send('history', action='reload')

    def stopLoading(self):
        """Stop loading the page."""
        self._send('history', action='stop')

    @property
    def title(self):
        """Title of the page (`str`)."""
        self._pump()
        return self._title

    @property
    def loadProgress(self):
        """How much of the page has loaded, from 0 to 100 (`int`)."""
        self._pump()
        return self._loadProgress

    @property
    def isLoading(self):
        """Whether the page is loading (`bool`)."""
        self._pump()
        return self._isLoading

    @property
    def isLoaded(self):
        """Whether the page has finished loading successfully (`bool`)."""
        self._pump()
        return not self._isLoading and self._loadOk

    @property
    def loadError(self):
        """Why the page couldn't be shown, or `None` if it could (`str` or
        `None`)."""
        self._pump()
        return self._loadError

    @property
    def scrollPosition(self):
        """Where the page drawn last was scrolled to, `(x, y)` in CSS pixels
        from the top-left of its document (`tuple` of `float`).

        This is for the frame drawn, so it matches what participants saw. Log
        it each frame to map positions onto the document later (see
        `windowToDocument`).
        """
        return self._frameScroll

    @property
    def documentSize(self):
        """Size `(w, h)` of the document of the page drawn last, in CSS pixels
        (`tuple` of `float`), or `None` before the first frame. Useful as the
        extent of a heatmap made with `windowToDocument`.
        """
        return self._frameDocSize

    def windowToDocument(self, pos, units=None):
        """Get the position on the page's HTML document of a position in the
        window, e.g. where an eye tracker says a participant is looking.

        Positions are mapped onto the page as it was drawn last, taking its
        position, size, orientation, flips, zoom and where it was scrolled to
        into account. So that a position matches what the participant saw, call
        this each frame (after drawing) with the latest sample, or log
        `scrollPosition` with each frame and map samples later.

        Positions are in CSS pixels from the top-left of the document, `y`
        increasing downwards, as `event.pageX` and `event.pageY` are in
        JavaScript, and as the bounds of an element are given by
        ``el.getBoundingClientRect()`` plus ``(scrollX, scrollY)``, so they can
        be matched with what is on the page.

        Only the scrolling of the page itself is taken into account, not that
        of elements scrolled within it (e.g. with ``overflow: auto``) or of
        frames in it.

        Parameters
        ----------
        pos : ArrayLike
            Position `(x, y)` in the window, or positions `(N, 2)`, measured
            from the window's center as stimulus positions are. Positions which
            are `nan` (e.g. while an eye tracker loses the eyes) give `nan`.
        units : str or None
            Units of `pos`, the stimulus' `units` if `None`.

        Returns
        -------
        ndarray
            Position `(x, y)` on the document, or positions `(N, 2)`. Positions
            which aren't on the page are `nan`.

        Examples
        --------
        Collect where a participant looked on a page, and make a heatmap of
        it::

            gaze = []
            while not done:
                page.draw()
                win.flip()
                gaze.append(page.windowToDocument(tracker.getPosition()))
            gaze = np.array(gaze)
            gaze = gaze[~np.isnan(gaze).any(axis=1)]
            w, h = page.documentSize
            heatmap, _, _ = np.histogram2d(
                gaze[:, 1], gaze[:, 0], bins=(int(h // 20), int(w // 20)),
                range=((0, h), (0, w)))

        """
        pos = np.asarray(pos, dtype=float)
        single = pos.ndim == 1
        pos = pos.reshape(-1, 2)
        if units is None:
            units = self.units
        valid = ~np.isnan(pos).any(axis=1)
        # converted with `nan` left out, as `layout` would replace it
        pix = np.full(pos.shape, np.nan)
        if valid.any():
            if units == 'pix':
                pix[valid] = pos[valid]
            else:
                pix[valid] = np.asarray(layout.Position(
                    pos[valid], units, self.win).pix).reshape(-1, 2)
        pagePos, inside = _geometry.windowPixToPageArray(
            pix, self.verticesPix, self._resolution)
        docPos = pagePos / self._frameZoom + np.asarray(self._frameScroll)
        docPos[~(valid & inside)] = np.nan

        return docPos[0] if single else docPos

    def waitForLoad(self, timeout=10.0):
        """Wait for the page to finish loading.

        The window isn't flipped while waiting.

        Parameters
        ----------
        timeout : float
            Most seconds to wait.

        Returns
        -------
        bool
            `True` if the page loaded, `False` if it failed or didn't load in
            time.

        """
        deadline = time.perf_counter() + timeout
        while time.perf_counter() < deadline:
            self._pump()
            if self._serverGone or self._loadError is not None:
                return False
            if not self._isLoading:
                return self._loadOk
            time.sleep(0.005)
        logging.warning("{}: page didn't load within {} s".format(
            self.name, timeout))
        return False

    def runJavaScript(self, code, callback=None):
        """Run JavaScript in the page, without waiting for it to finish.

        Parameters
        ----------
        code : str
            JavaScript to run.
        callback : callable or None
            Function called with the value of the last expression in `code`
            once it has run (from `draw` or `win.flip()`). Objects and arrays
            are given as dicts and lists, `undefined` as `None`. Errors aren't
            reported, other than in `consoleMessages`.

        """
        jsId = next(self._jsIds)
        if callback is not None:
            self._jsCallbacks[jsId] = callback
        self._send('js', id=jsId, code=code)

    def evaluateJavaScript(self, code, timeout=5.0):
        """Run JavaScript in the page and get the value of its last expression.

        The window isn't flipped while waiting.

        Parameters
        ----------
        code : str
            JavaScript to run.
        timeout : float
            Most seconds to wait.

        Returns
        -------
        object
            Value of the last expression in `code`, objects and arrays as dicts
            and lists, `undefined` as `None`.

        Raises
        ------
        TimeoutError
            If it doesn't finish in time.

        """
        jsId = next(self._jsIds)
        self._jsResults[jsId] = None
        self._send('js', id=jsId, code=code)
        deadline = time.perf_counter() + timeout
        try:
            while time.perf_counter() < deadline and not self._serverGone:
                self._pump()
                result = self._jsResults.get(jsId)
                if result is not None:
                    return result.get('value')
                time.sleep(0.001)
        finally:
            self._jsResults.pop(jsId, None)
        raise TimeoutError(
            "{}: JavaScript didn't finish within {} s".format(
                self.name, timeout))

    def getMessages(self, clear=True):
        """Get data the page sent with ``psychopy.send(data)``.

        Parameters
        ----------
        clear : bool
            Whether to clear the messages, so they aren't returned again.

        Returns
        -------
        list
            Data sent, oldest first, as decoded from JSON.

        """
        self._pump()
        messages = list(self._messages)
        if clear:
            self._messages.clear()
        return messages

    def sendMessage(self, data):
        """Send data to the page, to the functions it registered with
        ``psychopy.onMessage(handler)``.

        Parameters
        ----------
        data : object
            Data to send, which must be JSON serializable.

        """
        self._send('message', data=data)

    # ----------------------------------------------------------------------
    # Messages from the server
    #

    def _pump(self):
        """Handle messages from the server and pending input. Called each flip
        (by the window's `_host.WindowPump`) and when drawn."""
        if self._channel is None:
            return
        for msg in self._channel.receive():
            try:
                self._handleMessage(msg)
            except Exception as err:
                logging.error("{}: error handling {!r} message: {}".format(
                    self.name, msg.get('op'), err))
        self._sendResize()
        self._flushInput()
        self._updateFocus()
        held = self._heldFrames
        if len(held) > 1 and self._drawnRecently() and \
                not any(frame.get('gpu') for frame in held):
            # only the newest is drawn, free the others for the server (frames
            # on the GPU need OpenGL, see `_pumpGL`)
            for frame in held[:-1]:
                self._release(frame)
            del held[:-1]

    def _pumpGL(self):
        """As `_pump`, plus what needs the window's OpenGL context current,
        which it is when the window's pump calls this during a flip, and when
        drawing."""
        self._pump()
        if self._channel is None:
            return
        if self._gpuPending is not None:
            self._checkGpuSlots()
        slots = self._gpuSlots
        if self._gpuRetired and slots is not None and \
                not (self._shown and self._shown[1] is slots):
            # the server went back to shared memory
            slots.delete()
            self._gpuSlots = self._gpuGen = None
            self._gpuRetired = False
        if len(self._heldFrames) > 1 and self._drawnRecently():
            self._releaseFrames(self._heldFrames[:-1])
            del self._heldFrames[:-1]

    def _dropHeldFrames(self):
        """Let go of frames held from slots being replaced. Those in shared
        memory are released; those on the GPU aren't waited on again."""
        for frame in self._heldFrames:
            if not frame.get('gpu'):
                self._release(frame)
        self._heldFrames = []

    def _handleMessage(self, msg):
        op = msg['op']
        if op == 'frame':
            if self._gpuSlots is not None and msg['gen'] == self._gpuGen:
                msg['gpu'] = True
                self._heldFrames.append(msg)
            elif self._ring is not None and msg['gen'] == self._ring.gen:
                self._heldFrames.append(msg)
            else:
                self._release(msg)
        elif op == 'surface' and msg.get('transport') == 'gpu':
            # checked (and frames start) once OpenGL is current, see `_pumpGL`
            if self._gpuPending is not None:
                _gpushare.closeHandles(self._gpuPending.get('fds', ()))
            self._gpuPending = msg
            self._dropHeldFrames()
            self._dpr = msg.get('dpr', 1.0)
        elif op == 'surface':
            self._dropHeldFrames()
            if self._ring is not None:
                self._ring.close()
            self._ring = FrameRing.attach(
                msg['shm'], msg['w'], msg['h'], msg['stride'], msg['fmt'],
                msg['slots'], msg['gen'])
            self._dpr = msg.get('dpr', 1.0)
        elif op == 'gpuFallback':
            self._gpuRetired = True
            reason = msg.get('reason')
            _gpuSupport[self.win] = (None, reason)  # nor for later pages
            self._gpuUnavailable(reason)
        elif op == 'loadStarted':
            self._isLoading = True
            self._loadError = None
        elif op == 'loadProgress':
            self._loadProgress = msg['pct']
        elif op == 'loadFinished':
            self._isLoading = False
            self._loadOk = msg['ok']
            if not msg['ok']:
                self._loadError = "Couldn't load {}".format(msg.get('url'))
                logging.warning("{}: {}".format(self.name, self._loadError))
        elif op == 'urlChanged':
            self._url = msg['url']
            if self.autoLog:
                logging.exp("{}: page url={}".format(self.name, self._url))
        elif op == 'titleChanged':
            self._title = msg['title']
        elif op == 'pageMessage':
            self._messages.append(msg['data'])
            if self.autoLog:
                logging.data("{}: page sent {!r}".format(
                    self.name, msg['data']))
        elif op == 'console':
            self.consoleMessages.append(msg)
            logging.debug("{}: page console ({}): {}".format(
                self.name, msg.get('level'), msg.get('msg')))
        elif op == 'dialog':
            logging.warning("{}: dismissed page {} dialog: {}".format(
                self.name, msg['kind'], msg['msg']))
        elif op == 'navBlocked':
            logging.warning("{}: blocked page from going to {}".format(
                self.name, msg['url']))
        elif op == 'reloaded':
            # pages which went to another site aren't always shown otherwise,
            # see `_qtbrowser.ViewHost.acceptNavigation`
            if msg.get('form'):
                logging.warning(
                    "{}: loaded {} again after a form went there, so what was "
                    "sent may not be shown".format(self.name, msg['url']))
            else:
                logging.info("{}: loaded {} again after going to another "
                             "site".format(self.name, msg['url']))
        elif op == 'permissionDenied':
            logging.info("{}: refused page permission for {} ({})".format(
                self.name, msg['feature'], msg['origin']))
        elif op == 'cursor':
            self._cursorShape = msg['shape']
            self._updateCursor()
        elif op == 'renderGone':
            self._loadError = "The page stopped ({}, code {})".format(
                msg['status'], msg['code'])
            logging.error("{}: {}".format(self.name, self._loadError))
        elif op == 'jsResult':
            if msg['id'] in self._jsResults:
                self._jsResults[msg['id']] = msg
            callback = self._jsCallbacks.pop(msg['id'], None)
            if callback is not None:
                callback(msg.get('value'))
        elif op == 'error':
            logging.error("{}: web browser error: {}".format(
                self.name, msg.get('msg')))
        elif op == 'serverGone':
            if not self._serverGone:
                self._serverGone = True
                self._loadError = "The web browser server stopped"
                logging.error("{}: {}, see web_browser_last_session.log in "
                              "the user preferences folder".format(
                                  self.name, self._loadError))

    def _release(self, frame):
        self._send('release', slot=frame['slot'], gen=frame['gen'])

    def _releaseFrames(self, frames):
        """Release frames which won't be drawn (with OpenGL current): those on
        the GPU are waited for and signalled done first."""
        slots = self._gpuSlots
        gpuFrames = [frame for frame in frames if frame.get('gpu')]
        if gpuFrames and slots is not None:
            for frame in gpuFrames:
                slots.waitReady(frame['slot'])
                slots.signalDone(frame['slot'])
            slots.gl.glFlush()  # signalled before the server hears
        for frame in frames:
            self._release(frame)

    def _checkGpuSlots(self):
        """Import the shared slots the server sent and check them (with
        OpenGL current), going back to shared memory if they don't work."""
        msg, self._gpuPending = self._gpuPending, None
        fds = list(msg.pop('fds', ()))
        n = msg['slots']
        gl, info = _gpuSupportFor(self.win)
        slots = None
        problem = None
        if gl is None:
            problem = info
        elif len(fds) != 3 * n:
            problem = "expected {} handles, got {}".format(
                3 * n, len(fds))
        if problem is not None:
            _gpushare.closeHandles(fds)
        else:
            try:
                slots = _gpushare.GLSlots(
                    gl, msg['w'], msg['h'], msg['memSize'], fds[:n],
                    fds[n:2 * n], fds[2 * n:], self._interpolate)
                colors = slots.readCheckColors()
                expected = [_gpushare.checkColor(i) for i in range(n)]
                if any(max(abs(a - b) for a, b in zip(color, want)) > 2
                       for color, want in zip(colors, expected)):
                    problem = "frames read back wrong ({} rather than " \
                              "{})".format(colors, expected)
            except _gpushare.GPUShareError as err:
                problem = str(err)
        if problem is not None:
            if slots is not None:
                slots.delete()
            self._send('gpuStatus', gen=msg['gen'], ok=False, reason=problem)
            _gpuSupport[self.win] = (None, problem)  # nor for later pages
            self._gpuUnavailable(problem)
            return
        old = self._gpuSlots
        self._gpuSlots, self._gpuGen = slots, msg['gen']
        self._gpuRetired = False
        if old is not None and not (self._shown and self._shown[1] is old):
            old.delete()
        self._send('gpuStatus', gen=msg['gen'], ok=True)

    # ----------------------------------------------------------------------
    # Drawing
    #

    def _drawnRecently(self):
        return core.getTime() - self._lastDrawTime < _DRAWN_RECENTLY

    def draw(self, win=None):
        """Draw the latest frame of the page.

        Parameters
        ----------
        win : :class:`~psychopy.visual.Window` or None
            Window to draw to, the one the stimulus was made with if `None`.

        """
        if win is None:
            win = self.win
        self._selectWindow(win)
        self._lastDrawTime = core.getTime()
        self._pumpGL()
        self._takeFrame()
        if self._shown is not None:
            self._drawTexture()

    def _takeFrame(self):
        """Make the newest frame from the server the one drawn: upload it to
        the texture if it is in shared memory, or wait for its slot if it is
        on the GPU. The others are released."""
        if not self._heldFrames:
            return
        frame = self._heldFrames[-1]
        older = self._heldFrames[:-1]
        self._heldFrames = []
        previous = self._shown
        try:
            if frame.get('gpu'):
                self._gpuSlots.waitReady(frame['slot'])
                self._shown = ('gpu', self._gpuSlots, frame['slot'],
                               frame['gen'])
            else:
                ring = self._ring
                if ring is None or frame['gen'] != ring.gen:
                    self._release(frame)
                    return
                try:
                    texture = self._texture
                    if texture is None or not texture.matches(
                            ring.width, ring.height, ring.fmt):
                        if texture is not None:
                            texture.delete()
                        texture = self._texture = StreamingTexture(
                            ring.width, ring.height, ring.fmt,
                            self._interpolate)
                    texture.upload(ring.address(frame['slot']), ring.stride)
                    self._shown = ('shm', None, None, frame['gen'])
                finally:
                    self._release(frame)
            self.frameSeq = frame['seq']
            self.lastFrameCaptureTime = frame['t'] + self._clockOffset
            if 'scroll' in frame:
                self._frameScroll = tuple(float(v) for v in frame['scroll'])
            if frame.get('zoom'):
                self._frameZoom = float(frame['zoom'])
            if frame.get('docSize') is not None:
                self._frameDocSize = tuple(
                    float(v) for v in frame['docSize'])
        finally:
            self._releaseFrames(older)
            if previous is not None and previous != self._shown:
                self._letGoOfShown(previous)

    def _letGoOfShown(self, shown):
        """Stop drawing a frame on the GPU: signal its slot done and release
        it, or delete its slots if they have been replaced (with OpenGL
        current)."""
        transport, slots, slot, gen = shown
        if transport != 'gpu':
            return
        if slots is self._gpuSlots:
            slots.signalDone(slot)
            slots.gl.glFlush()  # signalled before the server hears
            self._send('release', slot=slot, gen=gen)
        elif self._shown is None or slots is not self._shown[1]:
            slots.delete()

    def _drawTexture(self):
        """Draw the frame on the stimulus' rectangle."""
        vertsPix = self.verticesPix
        if self._shown[0] == 'gpu':
            # rendered by OpenGL, so the bottom of the page is at t = 0
            texCoords = ((1, 0), (0, 0), (0, 1), (1, 1))
        else:
            # top row first, so the top of the page is at t = 0
            texCoords = ((1, 1), (0, 1), (0, 0), (1, 0))
        array = (GL.GLfloat * 20)(*[
            value for (s, t), (x, y) in zip(texCoords, vertsPix[:4])
            for value in (s, t, x, y, 0.)])

        GL.glPushAttrib(GL.GL_ENABLE_BIT | GL.GL_COLOR_BUFFER_BIT)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        # frame colors are premultiplied by alpha, so opacity scales them all
        opacity = self.opacity
        GL.glColor4f(opacity, opacity, opacity, opacity)
        GL.glEnable(GL.GL_BLEND)
        if self.win.blendMode == 'add':
            GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        else:
            GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glPushMatrix()
        self.win.setScale('pix')
        if self._shown[0] == 'gpu':
            self._shown[1].bind(self._shown[2])
        else:
            self._texture.bind()
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopMatrix()
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glPopAttrib()

    # ----------------------------------------------------------------------
    # Input
    #

    @property
    def interactive(self):
        """Whether mouse and keyboard input is passed to the page (`bool`)."""
        return self._interactive

    @interactive.setter
    def interactive(self, value):
        value = bool(value)
        if value == self._interactive:
            return
        self._interactive = value
        if value:
            self.win.addEditable(self)
        else:
            self._removeEditable()
            self._endPointer()

    @property
    def editable(self):
        """Whether the stimulus can take keyboard focus, as `interactive`
        (`bool`)."""
        return self._interactive

    def _removeEditable(self):
        win = self.win
        for ref in weakref.getweakrefs(self):
            if ref in win._editableChildren:
                win.removeEditable(self)
                return

    def _onText(self, text):
        """Keys reach the page from window events, see `_onWindowEvent`."""

    def _onCursorKeys(self, key):
        """Keys reach the page from window events, see `_onWindowEvent`."""

    @property
    def hasFocus(self):
        """Whether keys typed are passed to the page (`bool`)."""
        return self._interactive and self.win.currentEditable is self

    def focus(self):
        """Give the page keyboard focus, as clicking on it does."""
        if self._interactive:
            self.win.currentEditable = self
            self._updateFocus()

    def _updateFocus(self):
        focused = self.hasFocus
        if focused != self._hasFocus:
            self._hasFocus = focused
            self._send('input', kind='focus', focused=focused)

    def _pagePos(self, pos):
        """Position on the page of a position in the window, and whether it
        is on the page."""
        return _geometry.windowPixToPage(
            pos, self.verticesPix, self._resolution)

    def _sendMouse(self, action, x, y, button=None, mods=0):
        self._send('input', kind='mouse', action=action, x=x, y=y,
                   button=button, buttons=sorted(self._buttons), mods=mods)

    def _flushInput(self):
        """Send input held back to be merged with what followed it."""
        if self._pendingMove is not None:
            x, y, mods = self._pendingMove
            self._pendingMove = None
            self._lastMoveTime = core.getTime()
            self._sendMouse('move', x, y, mods=mods)
        if self._pendingKey is not None:
            evt, self._pendingKey = self._pendingKey, None
            self._sendKey('press', evt, '')

    def _sendKey(self, action, evt, text):
        self._send('input', kind='key', action=action, key=evt.key, text=text,
                   mods=evt.modifiers, repeat=evt.repeat)

    def _endPointer(self):
        """Stop passing on the mouse, telling the page it has left."""
        if self._hover or self._capture is not None:
            self._send('input', kind='mouse', action='leave')
        self._hover = False
        self._capture = None
        self._buttons.clear()
        self._updateCursor()

    def _onWindowEvent(self, evt):
        """Pass input from the window on to the page."""
        if evt.type == _events.WINDOW_CLOSE:
            self.close()
            return
        if not self._interactive or self._channel is None:
            return
        if evt.type in (_events.MOUSE_MOTION, _events.MOUSE_PRESS,
                        _events.MOUSE_RELEASE, _events.MOUSE_SCROLL):
            self._onMouse(evt)
        elif evt.type == _events.MOUSE_LEAVE:
            self._endPointer()
        elif evt.type in (_events.KEY_PRESS, _events.KEY_RELEASE,
                          _events.TEXT):
            if self.hasFocus and self._drawnRecently():
                self._onKey(evt)

    def _onMouse(self, evt):
        x, y, inside = self._pagePos(evt.pos)
        if not self._drawnRecently():
            inside = False
        captured = self._capture is not None
        if evt.type == _events.MOUSE_MOTION:
            if inside or captured:
                self._hover = inside
                self._pendingMove = (x, y, evt.modifiers)
                if core.getTime() - self._lastMoveTime >= _MOVE_INTERVAL:
                    self._flushInput()
            elif self._hover:
                self._pendingMove = None
                self._endPointer()
            self._updateCursor()
            return

        # anything held back goes first, so the page sees events in order
        self._flushInput()
        if evt.type == _events.MOUSE_PRESS:
            if not inside:
                return
            if self._capture is None:
                self._capture = evt.button
            self._buttons.add(evt.button)
            self.focus()
            self._sendMouse('press', x, y, evt.button, evt.modifiers)
        elif evt.type == _events.MOUSE_RELEASE:
            if evt.button not in self._buttons:
                return
            self._buttons.discard(evt.button)
            if evt.button == self._capture:
                self._capture = None
            self._sendMouse('release', x, y, evt.button, evt.modifiers)
            if not inside and self._capture is None:
                self._endPointer()
        elif evt.type == _events.MOUSE_SCROLL and inside:
            self._send('input', kind='wheel', x=x, y=y, dx=evt.scroll[0],
                       dy=evt.scroll[1], buttons=sorted(self._buttons),
                       mods=evt.modifiers)

    def _onKey(self, evt):
        if evt.type == _events.TEXT:
            text = ''.join(c for c in evt.text
                           if c >= ' ' and c != '\x7f')
            if not text:  # control characters go with their keys
                return
            if self._pendingKey is not None:
                pending, self._pendingKey = self._pendingKey, None
                self._sendKey('press', pending, text)
            else:  # text without a key, e.g. from an input method
                self._send('input', kind='ime', text=text)
            return

        # a key which didn't type anything goes without text
        self._flushInput()
        if evt.type == _events.KEY_RELEASE:
            self._sendKey('release', evt, '')
            return
        typesText = not evt.modifiers & (_MOD_CTRL | _MOD_COMMAND) and (
            evt.key is None or len(evt.key) == 1 or evt.key in _TEXT_KEYS_)
        if typesText:
            self._pendingKey = evt  # sent with the text event that follows
        else:
            self._sendKey('press', evt, '')

    def _updateCursor(self):
        """Show the cursor the page asks for while over it."""
        want = None
        if self._hover:
            want = _CURSORS_.get(self._cursorShape, 'arrow')
        if want == self._cursorShown:
            return
        self._cursorShown = want
        # may be closing from the garbage collector, on any thread
        callOnGLThread(self.win, self._setCursor, want or 'arrow')

    def _setCursor(self, name):
        try:
            self.win.setMouseType(name)
        except Exception:
            pass

    # scripted input, e.g. for testing

    def click(self, pagePos, button='left'):
        """Click on the page, as if with the mouse.

        Parameters
        ----------
        pagePos : ArrayLike
            Position `(x, y)` on the page, in its pixels from its top-left
            corner.
        button : str
            Button to click, `'left'`, `'middle'` or `'right'`.

        """
        x, y = (float(v) for v in pagePos)
        self.focus()
        self._send('input', kind='mouse', action='move', x=x, y=y,
                   buttons=[], mods=0)
        self._send('input', kind='mouse', action='press', x=x, y=y,
                   button=button, buttons=[button], mods=0)
        self._send('input', kind='mouse', action='release', x=x, y=y,
                   button=button, buttons=[], mods=0)

    def typeText(self, text):
        """Type text into the page, as if with the keyboard, into whatever has
        focus in it.

        Parameters
        ----------
        text : str
            Text to type.

        """
        self.focus()
        for char in text:
            key = char.lower() if char.isascii() and char.isalnum() else None
            for action in ('press', 'release'):
                self._send('input', kind='key', action=action, key=key,
                           text=char, mods=0, repeat=False)

    def scroll(self, dx=0., dy=0., pagePos=None):
        """Scroll the page, as if with the mouse wheel.

        Parameters
        ----------
        dx, dy : float
            Wheel steps to scroll by, positive `dy` scrolls up.
        pagePos : ArrayLike or None
            Position `(x, y)` on the page to scroll at, in its pixels from its
            top-left corner, its center if `None`.

        """
        if pagePos is None:
            pagePos = (self._resolution[0] / 2., self._resolution[1] / 2.)
        self._send('input', kind='wheel', x=float(pagePos[0]),
                   y=float(pagePos[1]), dx=float(dx), dy=float(dy), buttons=[],
                   mods=0)

    # ----------------------------------------------------------------------

    def close(self):
        """Close the page, freeing what it uses. The stimulus can't be used
        after.
        """
        if self._closed:
            return
        self._closed = True
        win = self.win
        try:
            self.autoDraw = False
        except Exception:
            pass
        try:
            self._endPointer()
            self.interactive = False
            win.removeEventListener(self._onWindowEvent)
        except Exception:
            pass
        self._pump_.remove(self)
        channel, self._channel = self._channel, None
        if channel is not None:
            channel.close()
        self._heldFrames = []
        if self._ring is not None:
            self._ring.close()
            self._ring = None
        if self._gpuPending is not None:
            _gpushare.closeHandles(self._gpuPending.get('fds', ()))
            self._gpuPending = None
        texture, self._texture = self._texture, None
        if texture is not None:
            callOnGLThread(win, texture.delete)
        allSlots = {id(slots): slots for slots in (
            self._gpuSlots, self._shown and self._shown[1]) if slots}
        self._gpuSlots = self._shown = None
        for slots in allSlots.values():
            callOnGLThread(win, slots.delete)

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
