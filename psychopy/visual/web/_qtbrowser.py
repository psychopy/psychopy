#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Pages rendered off screen with Qt WebEngine, for the web browser server.

Imported by `_server` once it has set the environment variables Qt reads, so
not to be imported anywhere else.

Each page is a `QWebEngineView` which is shown but not on screen. When it has
rendered, the frame is grabbed and written to shared memory for the stimulus,
or, when both processes can, drawn into GPU memory they share (see `_qtgpu`).
Input from the stimulus is sent to it as Qt events.
"""

import fnmatch
import json
import os
import sys
import threading
import time
import traceback

from PyQt6 import QtCore, QtGui, QtWidgets, sip
# so `QWebEngineView.focusProxy()` is given as the `QQuickWidget` it is
from PyQt6 import QtQuick, QtQuickWidgets  # noqa: F401
from PyQt6 import QtWebEngineCore
from PyQt6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineProfile, QWebEngineScript, QWebEngineSettings)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import _keymap
import _protocol
from _shm import FrameRing
from _qtgpu import GpuCompositor, GpuSurface, GPUShareError, RetainedCapture

Qt = QtCore.Qt
QE = QtCore.QEvent.Type

_MAC = sys.platform == 'darwin'
_NUM_SLOTS = 3

# frame formats Qt grabs in, as named in `surface` messages
_FORMATS_ = {
    QtGui.QImage.Format.Format_RGBA8888_Premultiplied: 'rgba_pm',
    # 0xAARRGGBB words, so BGRA bytes on little endian machines
    QtGui.QImage.Format.Format_ARGB32_Premultiplied:
        'bgra_pm' if sys.byteorder == 'little' else None
}

# run in every page before its own scripts: gives it `psychopy.send()` and
# `psychopy.onMessage()`, and stops drags, which would start a drag and drop
# loop in this process
_BRIDGE_SCRIPT_ = """
(function () {
  if (window.psychopy && window.psychopy.__bridge) { return; }
  var log = console.debug.bind(console);
  var tag = %s;
  var handlers = [];
  window.psychopy = Object.freeze({
    __bridge: true,
    send: function (data) {
      log(tag + JSON.stringify(data === undefined ? null : data));
    },
    onMessage: function (handler) { handlers.push(handler); }
  });
  window.addEventListener('psychopy:message', function (evt) {
    handlers.forEach(function (handler) {
      try { handler(evt.detail); } catch (err) { console.error(err); }
    });
  });
  document.addEventListener('dragstart', function (evt) {
    evt.preventDefault();
  }, true);
})();
""" % json.dumps(_protocol.MESSAGE_TAG)


def versions():
    """Versions of Qt, PyQt, Qt WebEngine and Chromium (`dict`)."""
    return dict(
        qt=QtCore.qVersion(),
        pyqt=QtCore.PYQT_VERSION_STR,
        webengine=QtWebEngineCore.qWebEngineVersion(),
        chromium=QtWebEngineCore.qWebEngineChromiumVersion())


def checkVersions():
    """Check Qt WebEngine was built for the version of Qt that is running.

    Up to 6.11, Qt WebEngine was released with Qt and numbered the same, and
    pip can install mismatched versions, which crash or fail to render. Since
    then it is numbered on its own (e.g. 6.140 for Chromium 140, which needs Qt
    6.12 or later), and PyQt6-WebEngine requires a version of PyQt6 it works
    with, so those aren't checked.

    Returns
    -------
    str or None
        What is wrong, or `None` if nothing is.

    """
    info = versions()
    qt = info['qt'].split('.')[:2]
    webengine = info['webengine'].split('.')[:2]
    if int(webengine[1]) >= 100:  # numbered on its own
        return None
    if qt != webengine:
        return (
            "Qt WebEngine {} doesn't match Qt {}, install matching versions of "
            "PyQt6-WebEngine and PyQt6-Qt6".format(
                info['webengine'], info['qt']))
    return None


def _flags(enumType, names):
    """Combine the members of a Qt flag enum with the given names."""
    value = enumType(0)
    for name in names:
        value |= getattr(enumType, name)
    return value


class _Page(QWebEnginePage):
    """A page which asks its `ViewHost` about navigation, dialogs, console
    messages and new windows."""

    def __init__(self, host, profile, parent=None):
        super().__init__(profile, parent)
        self.host = host

    def acceptNavigationRequest(self, url, navType, isMainFrame):
        return self.host.acceptNavigation(url, isMainFrame)

    def javaScriptConsoleMessage(self, level, message, line, source):
        self.host.onConsole(level, message, line, source)

    def javaScriptAlert(self, origin, msg):
        self.host.onDialog('alert', msg)

    def javaScriptConfirm(self, origin, msg):
        self.host.onDialog('confirm', msg)
        return False

    def javaScriptPrompt(self, origin, msg, default):
        self.host.onDialog('prompt', msg)
        return False, ''

    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):
        return []  # no uploads

    def createWindow(self, windowType):
        return self.host.createWindow(windowType)


class ViewHost(QtCore.QObject):
    """One page, shown off screen, with its frames and input.

    Parameters
    ----------
    server : BrowserServer
        The server the page belongs to.
    viewId : int
        ID the stimulus gave the page.
    cfg : dict
        The `create` message.

    """
    def __init__(self, server, viewId, cfg):
        super().__init__()
        self.server = server
        self.id = viewId
        self.allowedUrls = cfg.get('allowedUrls') or None
        self.newWindowPolicy = cfg.get('newWindowPolicy', 'same')
        self.maxFps = float(cfg.get('maxFps') or 0)

        # frames
        self.ring = None
        self.gen = 0
        self.free = set()
        self.seq = 0
        self.dirty = True
        self.inGrab = False
        self.lastGrabTime = 0.
        self.proxy = None
        self.cursorShape = None
        # popups the page has open (e.g. a <select>'s options), which are
        # windows of their own drawn into its frames, and whether to ignore
        # the release of a press which closed one
        self.popups = []
        self.ignoreRelease = False
        # frames go in shared memory, or stay on the GPU when the stimulus
        # asked for that and this process can: copies of each widget's
        # renders, and the shared slots they are drawn into
        self.closed = False
        self.transport = 'shm'
        self.gpuUuids = None
        self.gpuSurface = None
        self.captures = {}
        if cfg.get('gpu'):
            compositor, problem = server.gpuCompositor()
            if compositor is None:
                self.send('gpuFallback', reason=problem)
            else:
                self.transport = 'gpu'
                self.gpuUuids = (cfg['gpu']['deviceUUID'],
                                 cfg['gpu']['driverUUID'])
        self.grabTimer = QtCore.QTimer(self)
        self.grabTimer.setSingleShot(True)
        self.grabTimer.timeout.connect(self.grab)
        # for proxies without render signals (not seen with Qt 6.9)
        self.pollTimer = QtCore.QTimer(self)
        self.pollTimer.timeout.connect(self._poll)

        self.page = _Page(self, server.profile)
        settings = self.page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled,
                              bool(cfg.get('javascript', True)))
        # focus is given with focus events from the stimulus, Qt trying to
        # activate the window (which never accepts focus) only warns
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, False)
        if cfg.get('transparent'):
            self.page.setBackgroundColor(QtGui.QColor(0, 0, 0, 0))
        elif cfg.get('bgColor') is not None:
            self.page.setBackgroundColor(QtGui.QColor(*cfg['bgColor']))
        self.page.setAudioMuted(bool(cfg.get('muted', False)))
        script = QWebEngineScript()
        script.setName('psychopy')
        script.setInjectionPoint(
            QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(_BRIDGE_SCRIPT_)
        self.page.scripts().insert(script)

        self.page.loadStarted.connect(self._onLoadStarted)
        self.page.loadProgress.connect(
            lambda pct: self.send('loadProgress', pct=pct))
        self.page.loadFinished.connect(self._onLoadFinished)
        self.page.urlChanged.connect(
            lambda url: self.send('urlChanged', url=url.toString()))
        self.page.titleChanged.connect(
            lambda title: self.send('titleChanged', title=title))
        self.page.renderProcessTerminated.connect(self._onRenderGone)
        if hasattr(self.page, 'permissionRequested'):  # Qt 6.8+
            self.page.permissionRequested.connect(self._onPermission)
        else:
            self.page.featurePermissionRequested.connect(
                self._onFeaturePermission)

        self.view = QWebEngineView()
        self.view.setPage(self.page)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.view.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
        self.view.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.view.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.view.resize(int(cfg['w']), int(cfg['h']))
        self.view.setZoomFactor(float(cfg.get('zoom') or 1.0))
        self.view.installEventFilter(self)
        self.view.show()

        if cfg.get('html') is not None:
            self.setHtml(cfg['html'], cfg.get('baseUrl'))
        elif cfg.get('url'):
            self.navigate(cfg['url'])
        else:
            self.setHtml('<!doctype html><html><body></body></html>', None)

    def send(self, op, fds=None, **msg):
        self.server.conn.send(fds=fds, op=op, view=self.id, **msg)

    # ----------------------------------------------------------------------
    # page
    #

    def navigate(self, url):
        self.page.load(QtCore.QUrl.fromUserInput(url))

    def setHtml(self, html, baseUrl=None):
        base = QtCore.QUrl(baseUrl) if baseUrl else QtCore.QUrl('about:blank')
        if len(html.encode('utf-8')) < 1.9e6:
            self.page.setHtml(html, base)
            return
        # Qt refuses content over 2 MB given directly, so load it from a file
        # (relative links resolve against the file rather than `baseUrl`)
        path = self.server.tempHtmlFile(self.id)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        self.page.load(QtCore.QUrl.fromLocalFile(path))

    def history(self, action):
        actions = dict(
            back=QWebEnginePage.WebAction.Back,
            forward=QWebEnginePage.WebAction.Forward,
            reload=QWebEnginePage.WebAction.Reload,
            stop=QWebEnginePage.WebAction.Stop)
        self.page.triggerAction(actions[action])

    def runJavaScript(self, jsId, code):
        def done(value):
            try:
                _protocol.pack(value)
            except Exception:  # a type msgpack can't send
                value = repr(value)
            self.send('jsResult', id=jsId, ok=True, value=value)
        self.page.runJavaScript(code, done)

    def postMessage(self, data):
        self.page.runJavaScript(
            "window.dispatchEvent(new CustomEvent('psychopy:message', "
            "{detail: %s}));" % json.dumps(data))

    def acceptNavigation(self, url, isMainFrame):
        if not self.allowedUrls or not isMainFrame:
            return True
        if url.scheme() in ('data', 'about', 'file') and not url.host():
            return True  # content given with `setHtml`
        text = url.toString()
        if any(fnmatch.fnmatchcase(text, pattern)
               for pattern in self.allowedUrls):
            return True
        self.send('navBlocked', url=text)
        return False

    def createWindow(self, windowType):
        if self.newWindowPolicy == 'same':
            return self.page  # open the link here instead
        self.send('navBlocked', url='(new window)')
        return None

    def onConsole(self, level, message, line, source):
        if message.startswith(_protocol.MESSAGE_TAG):
            try:
                data = json.loads(message[len(_protocol.MESSAGE_TAG):])
            except ValueError:
                return
            self.send('pageMessage', data=data,
                      origin=self.page.url().toString())
            return
        self.send('console', level=level.name, msg=message, line=line,
                  src=source)

    def onDialog(self, kind, msg):
        self.send('dialog', kind=kind, msg=msg)

    def _onLoadStarted(self):
        self.send('loadStarted')
        self.hookProxy()

    def _onLoadFinished(self, ok):
        self.send('loadFinished', ok=bool(ok), url=self.page.url().toString())
        self.hookProxy()
        self.markDirty()

    def _onRenderGone(self, status, code):
        self.send('renderGone', status=status.name, code=code)
        QtCore.QTimer.singleShot(0, self.hookProxy)

    def _onPermission(self, permission):
        self.send('permissionDenied',
                  feature=permission.permissionType().name,
                  origin=permission.origin().toString())
        permission.deny()

    def _onFeaturePermission(self, origin, feature):
        self.send('permissionDenied', feature=feature.name,
                  origin=origin.toString())
        self.page.setFeaturePermission(
            origin, feature,
            QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)

    # ----------------------------------------------------------------------
    # frames
    #

    def eventFilter(self, obj, event):
        etype = event.type()
        if obj is self.view and etype in (QE.ChildAdded, QE.ChildPolished):
            QtCore.QTimer.singleShot(0, self.hookProxy)
        elif obj is self.proxy and etype == QE.CursorChange:
            shape = self.proxy.cursor().shape().name
            if shape != self.cursorShape:
                self.cursorShape = shape
                self.send('cursor', shape=shape)
        return False

    def addPopup(self, popup):
        """Draw a popup the page opened into its frames, and send it input
        over it."""
        if popup in self.popups:
            return
        self.popups.append(popup)
        popup.destroyed.connect(lambda *args: self.removePopup(popup))
        window = popup.quickWindow() if hasattr(popup, 'quickWindow') else None
        if window is not None:
            direct = Qt.ConnectionType.DirectConnection
            window.afterFrameEnd.connect(self.markDirty, direct)
            window.afterRendering.connect(self.markDirty, direct)
        if self.transport == 'gpu':
            self._capture(popup)
        self.markDirty()

    def removePopup(self, popup):
        capture = self.captures.pop(popup, None)
        if capture is not None:
            self._destroyCaptures([capture])
        if popup in self.popups:
            self.popups.remove(popup)
            self.markDirty()

    def openPopups(self):
        """Popups which are open, newest last."""
        self.popups = [p for p in self.popups if not sip.isdeleted(p)]
        return [p for p in self.popups if p.isVisible()]

    def popupRect(self, popup):
        """Where a popup is drawn on the page, in its pixels.

        Chromium places popups to fit the screen rather than the page, so they
        are moved to fit on it.
        """
        origin = self.proxy.mapToGlobal(QtCore.QPoint(0, 0))
        pos = popup.mapToGlobal(QtCore.QPoint(0, 0)) - origin
        size = self.view.size()
        x = max(0, min(pos.x(), size.width() - popup.width()))
        y = max(0, min(pos.y(), size.height() - popup.height()))
        return QtCore.QRect(x, y, popup.width(), popup.height())

    def hookProxy(self):
        """Watch the widget the page renders in for new frames.

        It is made once the page first loads, and is replaced if the page's
        render process does.
        """
        if self.closed:  # called later, e.g. from a timer
            return
        proxy = self.view.focusProxy()
        if proxy is None or proxy is self.proxy:
            return
        self.proxy = proxy
        proxy.installEventFilter(self)
        window = proxy.quickWindow() if hasattr(proxy, 'quickWindow') else None
        if window is not None:
            # direct, so emissions caused by grabbing are seen during it
            direct = Qt.ConnectionType.DirectConnection
            window.afterFrameEnd.connect(self.markDirty, direct)
            # the only one emitted when rendering in software
            window.afterRendering.connect(self.markDirty, direct)
            self.pollTimer.stop()
        else:
            self.pollTimer.start(int(1000 / (self.maxFps or 30)))
        if self.transport == 'gpu':
            self._capture(proxy)
        self.markDirty()

    def _poll(self):
        self.markDirty()

    def markDirty(self):
        """Note the page has rendered a frame which hasn't been grabbed."""
        if self.inGrab:  # grabbing renders a frame, which isn't a new one
            return
        self.dirty = True
        self.scheduleGrab()

    def scheduleGrab(self):
        if self.grabTimer.isActive():
            return
        delay = 0
        if self.maxFps > 0:
            wait = self.lastGrabTime + 1. / self.maxFps - time.perf_counter()
            delay = max(0, int(wait * 1000))
        self.grabTimer.start(delay)

    def grab(self):
        """Grab the page's latest frame and send it, if there is a new one and
        a free slot to put it in."""
        self.hookProxy()
        if not self.dirty or self.proxy is None:
            return
        if self.transport == 'gpu':
            try:
                self._grabGpu()
            except Exception as err:
                traceback.print_exc()
                self.gpuFailed("Drawing a frame on the GPU failed: {}".format(
                    err))
            return
        if self.ring is not None and not self.free:
            return  # sent when a slot is released
        self.dirty = False
        self.inGrab = True
        try:
            if hasattr(self.proxy, 'grabFramebuffer'):
                image = self.proxy.grabFramebuffer()
            else:
                image = self.view.grab().toImage()
            popups = self.openPopups()
            if popups and not image.isNull():
                self._drawPopups(image, popups)
        finally:
            self.inGrab = False
        if image.isNull():
            return

        fmt = _FORMATS_.get(image.format())
        if fmt is None:
            image = image.convertToFormat(
                QtGui.QImage.Format.Format_RGBA8888_Premultiplied)
            fmt = 'rgba_pm'
        width, height = image.width(), image.height()
        stride = image.bytesPerLine()
        ring = self.ring
        if (ring is None or (ring.width, ring.height, ring.stride, ring.fmt) !=
                (width, height, stride, fmt)):
            self._newRing(width, height, stride, fmt, image.devicePixelRatio())

        slot = min(self.free)
        self.free.discard(slot)
        bits = image.constBits()
        bits.setsize(image.sizeInBytes())
        self.ring.write(slot, bits)
        self.seq += 1
        self.lastGrabTime = time.perf_counter()
        self.send('frame', slot=slot, seq=self.seq, gen=self.gen,
                  t=self.lastGrabTime, **self._viewState())

    def _viewState(self):
        """Where the page was scrolled to, its zoom and the size of its
        document when a frame was grabbed, so positions in the window can be
        mapped onto the document as it was shown. Scroll position and size
        are in CSS pixels."""
        # Qt gives these in the view's pixels, so zoomed
        zoom = self.view.zoomFactor() or 1.0
        scroll = self.page.scrollPosition()
        size = self.page.contentsSize()
        return dict(scroll=(scroll.x() / zoom, scroll.y() / zoom),
                    zoom=zoom,
                    docSize=(size.width() / zoom, size.height() / zoom))

    def _drawPopups(self, image, popups):
        """Draw open popups on a frame of the page."""
        painter = QtGui.QPainter(image)
        try:
            for popup in popups:
                if hasattr(popup, 'grabFramebuffer'):
                    popupImage = popup.grabFramebuffer()
                else:
                    popupImage = popup.grab().toImage()
                rect = self.popupRect(popup)
                # the frame's device pixel ratio makes this page pixels
                painter.drawImage(QtCore.QPointF(rect.x(), rect.y()),
                                  popupImage)
        finally:
            painter.end()

    def _newRing(self, width, height, stride, fmt, dpr):
        """Start writing frames of a new size to a new segment.

        The old one is removed straight away, the stimulus can keep reading
        any slot it holds until it detaches.
        """
        if self.ring is not None:
            self.ring.close()
        self.gen += 1
        name = _protocol.shmName(os.getpid(), self.id, self.gen)
        self.ring = FrameRing.create(
            name, width, height, stride, fmt, _NUM_SLOTS, self.gen)
        self.free = set(range(_NUM_SLOTS))
        self.send('surface', shm=name, w=width, h=height, stride=stride,
                  fmt=fmt, slots=_NUM_SLOTS, gen=self.gen, dpr=dpr)

    def release(self, slot, gen):
        if self.gpuSurface is not None and gen == self.gpuSurface.gen:
            self.gpuSurface.release(slot)
        elif self.ring is not None and gen == self.gen:
            self.free.add(slot)
        else:
            return  # from slots that have gone
        if self.dirty:
            self.scheduleGrab()

    # frames on the GPU

    def _capture(self, widget):
        """Copy what a widget renders, to draw into frames on the GPU."""
        if widget not in self.captures and hasattr(widget, 'quickWindow'):
            self.captures[widget] = RetainedCapture(widget, self.gpuFailed)

    def _destroyCaptures(self, captures):
        compositor = self.server.compositor
        if compositor is None:
            return
        try:
            compositor.makeCurrent()
            for capture in captures:
                capture.destroy(compositor)
            compositor.doneCurrent()
        except Exception:
            traceback.print_exc()

    def _grabGpu(self):
        """Draw the latest renders into a free shared slot and send it."""
        capture = self.captures.get(self.proxy)
        if capture is None or capture.texture is None:
            return  # not rendered yet
        width, height = capture.size
        surface = self.gpuSurface
        if surface is None or (surface.width, surface.height) != (width,
                                                                  height):
            self._newGpuSurface(width, height)
            return  # frames start once the stimulus has checked the slots
        if not surface.checked or not surface.free:
            return  # sent when the check passes, or a slot is released
        self.dirty = False
        layers = [(capture, (0, 0, width, height))]
        scale = width / max(1, self.proxy.width())
        for popup in self.openPopups():
            popupCapture = self.captures.get(popup)
            if popupCapture is None or popupCapture.texture is None:
                continue
            rect = self.popupRect(popup)
            left = int(round(rect.x() * scale))
            right = int(round((rect.x() + rect.width()) * scale))
            top = int(round(rect.y() * scale))
            bottom = int(round((rect.y() + rect.height()) * scale))
            # OpenGL's y is up, the page's down
            layers.append((popupCapture,
                           (left, height - bottom, right, height - top)))
        slot = surface.compose(layers)
        self.seq += 1
        self.lastGrabTime = time.perf_counter()
        self.send('frame', slot=slot, seq=self.seq, gen=self.gen,
                  t=self.lastGrabTime, **self._viewState())

    def _newGpuSurface(self, width, height):
        """Allocate shared slots for frames of a new size, and send them to
        the stimulus to check."""
        old, self.gpuSurface = self.gpuSurface, None
        if old is not None:
            old.destroy()
        self.gen += 1
        try:
            surface = GpuSurface(self.server.compositor, self.gpuUuids, width,
                                 height, _NUM_SLOTS, self.gen)
        except GPUShareError as err:
            self.gpuFailed(str(err))
            return
        self.gpuSurface = surface
        fds, surface.stimulusFds = surface.stimulusFds, []
        self.send('surface', transport='gpu', w=width, h=height,
                  slots=_NUM_SLOTS, gen=self.gen, fmt='rgba_pm',
                  memSize=surface.memSize, bottomUp=True,
                  dpr=width / max(1, self.proxy.width()), fds=fds)

    def gpuStatus(self, gen, ok, reason=None):
        """The stimulus checked a set of shared slots."""
        surface = self.gpuSurface
        if surface is None or gen != surface.gen:
            return
        if ok:
            surface.checkPassed()
            self.markDirty()
        else:
            self.gpuFailed(reason or "The shared frames didn't check out",
                           notify=False)

    def gpuFailed(self, reason, notify=True):
        """Go back to frames in shared memory."""
        if self.transport != 'gpu':
            return
        print("Frames on the GPU stopped, using shared memory: {}".format(
            reason), file=sys.stderr)
        self.transport = 'shm'
        if notify:
            self.send('gpuFallback', reason=reason)
        surface, self.gpuSurface = self.gpuSurface, None
        if surface is not None:
            surface.destroy()
        captures, self.captures = list(self.captures.values()), {}
        self._destroyCaptures(captures)
        self.markDirty()

    def resize(self, width, height):
        self.view.resize(int(width), int(height))
        self.markDirty()

    def setMaxFps(self, fps):
        self.maxFps = float(fps or 0)

    # ----------------------------------------------------------------------
    # input
    #

    def input(self, msg):
        """Send input from the stimulus to the page."""
        self.hookProxy()
        target = self.proxy or self.view
        kind = msg['kind']
        popups = self.openPopups() if self.proxy is not None else []
        if popups and kind == 'key':
            target = popups[-1]  # the popup takes the keys, e.g. arrows
        mods = _flags(Qt.KeyboardModifier, _keymap.qtModifierNames(
            msg.get('mods', 0), _MAC))
        if kind in ('mouse', 'wheel'):
            pos = QtCore.QPointF(msg.get('x', 0.), msg.get('y', 0.))
            if popups:
                target, pos = self._popupTarget(popups, pos, msg)
                if target is None:
                    return
            globalPos = QtCore.QPointF(target.mapToGlobal(pos.toPoint()))
            buttons = _flags(Qt.MouseButton, [
                _keymap.qtButtonName(b) for b in msg.get('buttons', ())])
        if kind == 'mouse':
            action = msg['action']
            if action == 'leave':
                event = QtCore.QEvent(QE.Leave)
            else:
                etype = dict(
                    press=QE.MouseButtonPress, release=QE.MouseButtonRelease,
                    move=QE.MouseMove, dblclick=QE.MouseButtonDblClick)[action]
                button = Qt.MouseButton.NoButton
                if action != 'move':
                    button = getattr(Qt.MouseButton,
                                     _keymap.qtButtonName(msg.get('button')))
                event = QtGui.QMouseEvent(
                    etype, pos, pos, globalPos, button, buttons, mods)
        elif kind == 'wheel':
            angle = QtCore.QPoint(int(round(msg.get('dx', 0.) * 120)),
                                  int(round(msg.get('dy', 0.) * 120)))
            event = QtGui.QWheelEvent(
                pos, globalPos, QtCore.QPoint(0, 0), angle, buttons, mods,
                Qt.ScrollPhase.NoScrollPhase, False)
        elif kind == 'key':
            key = msg.get('key')
            text = msg.get('text') or _keymap.keyText(key)
            qtName = _keymap.qtKeyName(key, _MAC)
            if qtName is not None:
                code = getattr(Qt.Key, qtName)
            elif text:  # Qt's codes for printable keys are their characters
                code = ord(text.upper()[0])
            else:
                return
            if _keymap.isKeypad(key):
                mods |= Qt.KeyboardModifier.KeypadModifier
            etype = (QE.KeyPress if msg.get('action') == 'press'
                     else QE.KeyRelease)
            event = QtGui.QKeyEvent(etype, code, mods, text,
                                    bool(msg.get('repeat', False)))
        elif kind == 'ime':
            event = QtGui.QInputMethodEvent()
            event.setCommitString(msg.get('text', ''))
        elif kind == 'focus':
            event = QtGui.QFocusEvent(
                QE.FocusIn if msg.get('focused') else QE.FocusOut,
                Qt.FocusReason.MouseFocusReason)
        else:
            return
        QtWidgets.QApplication.sendEvent(target, event)

    def _popupTarget(self, popups, pos, msg):
        """Where mouse input at a position on the page goes while a popup is
        open: to the popup if over it, else a press closes the popup (and
        isn't passed on, as browsers do).

        Returns
        -------
        tuple
            `(widget, pos)`, the widget to send the event to and the position
            on it, or `(None, None)` to not send it.
        """
        for popup in reversed(popups):
            rect = self.popupRect(popup)
            if rect.contains(pos.toPoint()):
                return popup, pos - QtCore.QPointF(rect.topLeft())
        action = msg.get('action')
        if action == 'press':
            for popup in popups:
                popup.close()
            self.ignoreRelease = True
            self.markDirty()
            return None, None
        if action == 'release' and self.ignoreRelease:
            self.ignoreRelease = False
            return None, None
        return self.proxy, pos

    # ----------------------------------------------------------------------

    def close(self):
        self.closed = True
        self.grabTimer.stop()
        self.pollTimer.stop()
        self.view.removeEventFilter(self)
        if self.ring is not None:
            self.ring.close()
            self.ring = None
        captures, self.captures = list(self.captures.values()), {}
        self._destroyCaptures(captures)
        if self.gpuSurface is not None:
            self.gpuSurface.destroy()
            self.gpuSurface = None
        self.view.close()
        # pages have to go before the profile they use
        self.view.deleteLater()
        self.page.deleteLater()
        self.send('closed')


class BrowserServer(QtCore.QObject):
    """Runs the pages for the stimuli in the process that started the server.

    Parameters
    ----------
    conn : _server.Connection
        Connection to the stimulus' process.
    app : QApplication
        The application.

    """
    received = QtCore.pyqtSignal(object)

    def __init__(self, conn, app, gpu='off'):
        super().__init__()
        self.conn = conn
        self.app = app
        self.views = {}
        # whether frames may be shared on the GPU, and the compositor for
        # them once a page asks (or why there can't be one)
        self.gpu = gpu
        self.compositor = None
        self._compositorProblem = None
        self._tempDir = None
        # off the record (no storage name): nothing is kept after exiting
        self.profile = QWebEngineProfile()
        self.profile.downloadRequested.connect(lambda item: item.cancel())
        self.received.connect(self.handle, Qt.ConnectionType.QueuedConnection)
        self._closing = False
        app.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Give popups pages open (e.g. a <select>'s options) to their
        page."""
        if event.type() == QE.Show and isinstance(obj, QtWidgets.QWidget) \
                and obj.isWindow() and obj.windowType() == Qt.WindowType.Popup:
            owner = obj.parentWidget()
            for view in self.views.values():
                if view.view is owner:
                    view.addPopup(obj)
                    break
        return False

    def gpuCompositor(self):
        """Get the compositor for frames on the GPU, making it if needed.

        Returns
        -------
        tuple
            `(compositor, None)`, or `(None, reason)` if there can't be one.

        """
        if self.compositor is None and self._compositorProblem is None:
            if self.gpu != 'auto':
                self._compositorProblem = "turned off"
            else:
                try:
                    self.compositor = GpuCompositor()
                except Exception as err:
                    traceback.print_exc()
                    self._compositorProblem = str(err)
        return self.compositor, self._compositorProblem

    def readMessages(self):
        """Read messages until the connection closes (on its own thread)."""
        try:
            while True:
                data = self.conn.conn.recv_bytes()
                self.received.emit(_protocol.unpack(data))
        except (EOFError, OSError, RuntimeError):
            pass
        # the server may have shut down and been deleted already, as the
        # connection closes after (on Windows the pipe ends while this thread
        # is still running)
        try:
            self.received.emit({'op': 'eof'})
        except RuntimeError:
            pass

    def tempHtmlFile(self, viewId):
        import tempfile
        if self._tempDir is None:
            self._tempDir = tempfile.mkdtemp(prefix='psychopy-web-')
        return os.path.join(self._tempDir, 'page{}.html'.format(viewId))

    def handle(self, msg):
        op = msg.get('op')
        viewId = msg.get('view')
        try:
            if op == 'create':
                if viewId in self.views:
                    raise ValueError("Page {} already exists".format(viewId))
                self.views[viewId] = ViewHost(self, viewId, msg)
            elif op in ('shutdown', 'eof'):
                self.shutdown()
            elif op == 'ping':
                self.conn.send(op='pong', id=msg.get('id'))
            else:
                view = self.views.get(viewId)
                if view is None:
                    return  # closed already
                if op == 'release':
                    view.release(msg['slot'], msg['gen'])
                elif op == 'gpuStatus':
                    view.gpuStatus(msg['gen'], msg['ok'], msg.get('reason'))
                elif op == 'input':
                    view.input(msg)
                elif op == 'navigate':
                    view.navigate(msg['url'])
                elif op == 'setHtml':
                    view.setHtml(msg['html'], msg.get('baseUrl'))
                elif op == 'history':
                    view.history(msg['action'])
                elif op == 'js':
                    view.runJavaScript(msg['id'], msg['code'])
                elif op == 'message':
                    view.postMessage(msg.get('data'))
                elif op == 'resize':
                    view.resize(msg['w'], msg['h'])
                elif op == 'zoom':
                    view.view.setZoomFactor(float(msg['factor']))
                elif op == 'setMuted':
                    view.page.setAudioMuted(bool(msg['muted']))
                elif op == 'setMaxFps':
                    view.setMaxFps(msg['fps'])
                elif op == 'close':
                    self.views.pop(viewId).close()
        except Exception as err:
            traceback.print_exc()
            self.conn.send(op='error', view=viewId, msg='{}: {}'.format(
                type(err).__name__, err))

    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        for view in list(self.views.values()):
            view.close()
        self.views.clear()
        if self.compositor is not None and \
                self.compositor._allocator is not None:
            self.compositor._allocator.destroy()
        # delete the pages now, then the profile, which warns otherwise
        QtCore.QCoreApplication.sendPostedEvents(None, QE.DeferredDelete)
        self.profile.deleteLater()
        QtCore.QCoreApplication.sendPostedEvents(None, QE.DeferredDelete)
        if self._tempDir is not None:
            import shutil
            shutil.rmtree(self._tempDir, ignore_errors=True)
        self.conn.send(op='bye')
        self.app.quit()


def run(conn, platform, gpu='off'):
    """Run the server until it is told to stop or the connection closes.

    Parameters
    ----------
    conn : _server.Connection
        Connection to the stimulus' process.
    platform : str
        How Qt renders pages, see `_server.choosePlatform`.
    gpu : str
        `'auto'` to share frames on the GPU with stimuli which ask for it,
        `'off'` to only use shared memory.

    Returns
    -------
    int
        Exit code.

    """
    problem = checkVersions()
    if problem is not None:
        conn.send(op='fatal', error=problem)
        conn.close()
        return 1

    if gpu == 'auto':
        # so our context can share the pages' rendered textures, see `_qtgpu`
        QtCore.QCoreApplication.setAttribute(
            Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QtWidgets.QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    server = BrowserServer(conn, app, gpu)
    threading.Thread(target=server.readMessages, name='webServerReader',
                     daemon=True).start()
    conn.send(op='hello', protocol=_protocol.PROTOCOL_VERSION,
              pid=os.getpid(), versions=versions(), platform=platform,
              qpa=QtGui.QGuiApplication.platformName(), gpu=gpu)
    code = app.exec()
    conn.close()
    return code
