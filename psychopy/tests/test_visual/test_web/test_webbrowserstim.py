"""Tests for `WebBrowserStim` with real pages, which need Qt WebEngine. Pages
are local, so no internet access is needed."""
import time

import numpy as np
import pytest

from psychopy.tests import skip_under_vm
from psychopy.visual import web

pytestmark = [
    pytest.mark.needs_webengine,
    pytest.mark.slow,
    pytest.mark.skipif(not web.isAvailable(),
                       reason="needs Qt WebEngine (pip install psychopy[web])"),
    skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
]

PAGE = """<!doctype html><html><head><style>
body { margin: 0; background: rgb(255, 0, 0); font: 16px sans-serif; }
#txt { position: absolute; left: 10px; top: 10px; width: 200px; height: 24px; }
#btn { position: absolute; left: 10px; top: 60px; width: 100px; height: 30px; }
#tall { height: 3000px; }
</style></head><body>
<input id="txt">
<button id="btn" onclick="psychopy.send({clicked: true})">button</button>
<div id="tall"></div>
<script>psychopy.onMessage(function (data) { psychopy.send({echo: data}); });
</script>
</body></html>"""

# a different color each frame
ANIM = """<!doctype html><body style="margin: 0"><canvas id=c></canvas><script>
var c = document.getElementById('c'), g = c.getContext('2d'), n = 0;
c.width = innerWidth; c.height = innerHeight;
(function f() { g.fillStyle = 'hsl(' + (n++ * 7 % 360) + ',80%,50%)';
  g.fillRect(0, 0, c.width, c.height); requestAnimationFrame(f); })();
</script></body>"""


@pytest.fixture(scope='module')
def win():
    from psychopy import visual
    win = visual.Window((400, 300), winType='pyglet', units='pix',
                        color=(-1, -1, -1), allowGUI=False, autoLog=False)
    yield win
    win.close()


@pytest.fixture(scope='module')
def sites():
    """Pages served on two sites, ``localhost`` and ``127.0.0.1`` (which
    Chromium counts as different sites), as `(first, other, requests)`: their
    addresses, and a list of the `(method, path)` of each request made.

    The first has ``/start.html``, with ways of going to ``/anim.html``
    (`ANIM`) on the other: a link, a link which redirects there, and forms.
    Both have ``/script.js``, which sets `remoteScript`.
    """
    import http.server
    import threading

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = self.path.split('?')[0]
            requests.append((self.command, path))
            if path == '/redirect':
                self.send_response(302)
                self.send_header('Location', other + '/anim.html')
                self.end_headers()
                return
            if path not in pages:
                self.send_error(404)
                return
            contentType, body = pages[path]
            self.send_response(200)
            self.send_header('Content-Type', contentType)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.rfile.read(int(self.headers.get('Content-Length', 0)))
            self.do_GET()

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    port = server.server_address[1]
    first = 'http://localhost:{}'.format(port)
    other = 'http://127.0.0.1:{}'.format(port)
    start = """<!doctype html><body>
    <a id="link" href="{other}/anim.html">link</a>
    <a id="redirect" href="/redirect">redirect</a>
    <form id="formGet" method="get" action="{other}/anim.html">
      <input name="a" value="1"></form>
    <form id="formPost" method="post" action="{other}/anim.html">
      <input name="a" value="1"></form>
    </body>""".format(other=other)
    html = 'text/html; charset=utf-8'
    requests = []
    pages = {'/start.html': (html, start.encode()),
             '/anim.html': (html, ANIM.encode()),
             '/script.js': ('text/javascript', b'window.remoteScript = 1;')}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield first, other, requests
    server.shutdown()
    server.server_close()


def _gpuSupported(win):
    """Whether frames can be passed to `win` on the GPU here."""
    from psychopy.visual.web import _host, webbrowserstim
    host = _host.BrowserHost.get()
    return host.info.get('gpu') == 'auto' and \
        webbrowserstim._gpuSupportFor(win)[0] is not None


# each test using a page runs with frames in shared memory and on the GPU
# (which falls back to shared memory where it isn't supported)
@pytest.fixture(params=[False, True], ids=['shm', 'gpu'])
def stim(win, request):
    from psychopy import visual
    stim = visual.WebBrowserStim(win, html=PAGE, size=(320, 240),
                                 resolution=(320, 240), waitForLoad=True,
                                 gpuSharing=request.param)
    assert stim.isLoaded, stim.loadError
    # the first frames after loading can be of the page before it is painted
    # (blank white), so wait for its red background
    assert _flipUntil(stim, lambda: _drawnPixel(stim, (0, 50)) == (255, 0, 0))
    yield stim
    stim.close()


def _flipUntil(stim, condition, timeout=5.):
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        stim.draw()
        stim.win.flip()
        if condition():
            return True
    return False


def _pixel(win, pos):
    import psychopy.tools.pygletgl as GL
    buf = (GL.GLubyte * 4)()
    x = int(pos[0] * win.pixScaleFactor + win.size[0] / 2)
    y = int(pos[1] * win.pixScaleFactor + win.size[1] / 2)
    GL.glReadPixels(x, y, 1, 1, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, buf)
    return tuple(buf)[:3]


def _drawnPixel(stim, pos):
    """Color at `pos` once the stimulus' latest frame is drawn."""
    stim.draw()
    return _pixel(stim.win, pos)


def _windowCoords(stim, pagePos):
    """Window coordinates (as the backend's events give them) of a position on
    the page."""
    from psychopy.visual.web._geometry import pageToWindowPix
    pix = pageToWindowPix(pagePos, stim.verticesPix, stim.resolution)
    return stim.win.backend._pixToWindowCoords(pix)


def test_draw(stim, win):
    stim.draw()
    assert _pixel(win, (0, 50)) == (255, 0, 0)
    assert _pixel(win, (0, 140)) == (0, 0, 0)  # outside it
    win.flip()


def test_messages(stim):
    stim.sendMessage({'x': [1, 2]})
    assert _flipUntil(stim, lambda: stim._messages)
    assert stim.getMessages() == [{'echo': {'x': [1, 2]}}]
    assert stim.getMessages() == []


def test_javascript(stim):
    assert stim.evaluateJavaScript('1 + 1') == 2
    assert stim.evaluateJavaScript('({a: [1, "b"]})') == {'a': [1, 'b']}
    # dialogs are dismissed rather than blocking the page
    assert stim.evaluateJavaScript('alert("hi"); confirm("ok?")') is False


def test_click(stim):
    """Clicking with the mouse (through the window's event handlers) reaches
    the page."""
    from pyglet.window import mouse
    x, y = _windowCoords(stim, (60, 75))
    handle = stim.win.winHandle
    handle.on_mouse_motion(x, y, 0, 0)
    handle.on_mouse_press(x, y, mouse.LEFT, 0)
    handle.on_mouse_release(x, y, mouse.LEFT, 0)
    assert _flipUntil(stim, lambda: stim._messages)
    assert stim.getMessages() == [{'clicked': True}]


def test_typing(stim):
    """Typing (through the window's event handlers) goes to the input the
    page focused when clicked."""
    from pyglet.window import key, mouse
    handle = stim.win.winHandle
    x, y = _windowCoords(stim, (100, 22))
    handle.on_mouse_press(x, y, mouse.LEFT, 0)
    handle.on_mouse_release(x, y, mouse.LEFT, 0)
    _flipUntil(stim, lambda: False, timeout=0.2)
    assert stim.evaluateJavaScript('document.activeElement.id') == 'txt'
    for char in 'Hey':
        symbol = getattr(key, char.upper())
        mods = key.MOD_SHIFT if char.isupper() else 0
        handle.on_key_press(symbol, mods)
        handle.on_text(char)
        handle.on_key_release(symbol, mods)
    handle.on_key_press(key.BACKSPACE, 0)
    handle.on_text_motion(key.MOTION_BACKSPACE)
    handle.on_key_release(key.BACKSPACE, 0)
    assert _flipUntil(stim, lambda: stim.evaluateJavaScript(
        "document.getElementById('txt').value") == 'He')

    stim.typeText('llo')
    assert _flipUntil(stim, lambda: stim.evaluateJavaScript(
        "document.getElementById('txt').value") == 'Hello')


def test_scroll(stim):
    x, y = _windowCoords(stim, (160, 200))
    handle = stim.win.winHandle
    handle.on_mouse_motion(x, y, 0, 0)
    handle.on_mouse_scroll(x, y, 0, -3)
    assert _flipUntil(stim, lambda: stim.evaluateJavaScript('scrollY') > 0)


@pytest.mark.parametrize('zoom', [1., 2.])
def test_windowToDocument(win, zoom):
    """Positions in the window map onto the document as Chromium lays it out,
    once scrolled and zoomed."""
    from psychopy import visual
    from psychopy.visual.web._geometry import pageToWindowPix
    page = """<!doctype html><html><body style="margin: 0">
    <div style="height: 3000px; width: 1000px"></div>
    <div id="mark" style="position: absolute; left: 100px; top: 500px;
        width: 40px; height: 40px; background: blue"></div>
    </body></html>"""
    stim = visual.WebBrowserStim(win, html=page, size=(320, 240),
                                 resolution=(320, 240), zoom=zoom,
                                 waitForLoad=True)
    try:
        assert stim.isLoaded, stim.loadError
        stim.runJavaScript('scrollTo(30, 450)')
        assert _flipUntil(stim, lambda: stim.scrollPosition == (30., 450.))
        assert stim.evaluateJavaScript('[scrollX, scrollY]') == [30, 450]
        docW, docH = stim.documentSize
        assert docW >= 1000 and docH >= 3000
        # center of the mark, (120, 520) on the document
        pagePos = ((120 - 30) * zoom, (520 - 450) * zoom)
        winPos = pageToWindowPix(pagePos, stim.verticesPix, stim.resolution)
        docPos = stim.windowToDocument(winPos, units='pix')
        assert np.allclose(docPos, (120, 520), atol=0.5)
        assert stim.evaluateJavaScript(
            'document.elementFromPoint({} - scrollX, {} - scrollY).id'.format(
                *docPos)) == 'mark'
    finally:
        stim.close()


def test_allowedUrls(win):
    from psychopy import visual
    stim = visual.WebBrowserStim(
        win, html=PAGE, size=(64, 48), allowedUrls=['https://example.org/*'],
        waitForLoad=True)
    try:
        url = stim.url
        stim.url = 'https://blocked.invalid/'
        _flipUntil(stim, lambda: False, timeout=0.5)
        assert stim.url == url
        assert stim.evaluateJavaScript("typeof psychopy") == 'object'
    finally:
        stim.close()


def test_largeHtml(win):
    """Pages too big for Qt to take directly (over 2 MB) are shown."""
    from psychopy import visual
    filler = '<p>' + 'x' * 1000 + '</p>'
    html = '<html><body>{}<div id="end">end</div></body></html>'.format(
        filler * 2500)
    stim = visual.WebBrowserStim(win, html=html, size=(64, 48),
                                 waitForLoad=True, timeout=20)
    try:
        assert stim.isLoaded, stim.loadError
        assert stim.evaluateJavaScript(
            "document.getElementById('end').textContent") == 'end'
    finally:
        stim.close()


def test_setHtmlBaseUrl(win, sites):
    """HTML given with a base address has relative links resolve against it,
    is read as UTF-8, can load scripts from the web and is given that
    address."""
    from psychopy import visual
    first, other, requests = sites
    html = """<!doctype html><html lang="en"><head><title>t</title>
    <script src="{}/script.js"></script></head>
    <body><a id="a" href="sub/page.html">é✓</a></body></html>""".format(
        other)
    stim = visual.WebBrowserStim(win, html=html, baseUrl=first + '/dir/',
                                 size=(64, 48), waitForLoad=True)
    try:
        assert stim.isLoaded, stim.loadError
        assert stim.url == first + '/dir/'
        href = stim.evaluateJavaScript("document.getElementById('a').href")
        assert href == first + '/dir/sub/page.html'
        assert stim.evaluateJavaScript(
            "document.getElementById('a').textContent") == 'é✓'
        assert stim.evaluateJavaScript("window.remoteScript") == 1
        assert stim.evaluateJavaScript("document.documentElement.lang") == 'en'
        stim.setHtml('<p>no base</p>')
        assert _flipUntil(stim, lambda: stim.url == 'about:blank')
    finally:
        stim.close()


def _assertAnimated(stim, duration=1.):
    """Check `ANIM` is shown changing, rather than stuck on one frame."""
    colors = set()
    seq = stim.frameSeq
    _flipUntil(stim, lambda: colors.add(_drawnPixel(stim, (0, 0))),
               timeout=duration)
    assert len(colors) > 5, "showed {} in {} frames of {}".format(
        colors, stim.frameSeq - seq, stim.url)


def test_frameTiming(stim):
    """An animated page is shown at (close to) its own frame rate, without
    the window missing flips."""
    stim.setHtml(ANIM)
    assert stim.waitForLoad()
    _flipUntil(stim, lambda: False, timeout=0.5)
    seq = stim.frameSeq
    t0 = time.perf_counter()
    _flipUntil(stim, lambda: False, timeout=2.)
    fps = (stim.frameSeq - seq) / (time.perf_counter() - t0)
    assert fps > 20
    # and once given other HTML, which Qt WebEngine doesn't show when given
    # as a `data:` URL
    stim.setHtml(ANIM.replace('* 7', '* 11'))
    assert stim.waitForLoad()
    _assertAnimated(stim)


# how pages go to another site themselves
_GO = {
    'link': "document.getElementById('link').click()",
    'script': "location.href = '{other}/anim.html'",
    'redirect': "document.getElementById('redirect').click()",
    'formGet': "document.getElementById('formGet').submit()",
    'formPost': "document.getElementById('formPost').submit()",
    'url': None,  # set by the stimulus
}


@pytest.mark.parametrize('gpuSharing', [False, True], ids=['shm', 'gpu'])
@pytest.mark.parametrize('how', list(_GO))
def test_crossSiteNavigation(win, sites, how, gpuSharing):
    """Pages are shown after going to another site, which Qt WebEngine (6.12
    on Windows, at least) doesn't always do unless they're loaded again once
    there."""
    from psychopy import visual
    first, other, requests = sites
    del requests[:]
    stim = visual.WebBrowserStim(win, url=first + '/start.html',
                                 size=(320, 240), resolution=(320, 240),
                                 waitForLoad=True, gpuSharing=gpuSharing)
    try:
        assert stim.isLoaded, stim.loadError
        if how == 'url':
            stim.url = other + '/anim.html'
        else:
            stim.runJavaScript(_GO[how].format(other=other))
        assert _flipUntil(stim, lambda: stim.url.startswith(
            other + '/anim.html') and stim.isLoaded, timeout=10)
        _assertAnimated(stim)
        # pages on the first site load once, those on the other twice
        assert requests.count(('GET', '/start.html')) == 1
        assert len([r for r in requests if r[1] == '/anim.html']) == 2
    finally:
        stim.close()


@pytest.mark.parametrize('gpuSharing', [False, True], ids=['shm', 'gpu'])
def test_selectPopup(win, gpuSharing):
    """A <select>'s options, which open in a popup window of their own, are
    drawn on the page and take keys and clicks."""
    from psychopy import visual
    from pyglet.window import key, mouse
    options = ''.join('<option>option {}</option>'.format(i) for i in range(6))
    stim = visual.WebBrowserStim(
        win, size=(320, 240), resolution=(320, 240), waitForLoad=True,
        gpuSharing=gpuSharing,
        html="<body style='margin:0; background: #fff'>"
             "<select id='s' style='position: absolute; left: 10px; "
             "top: 10px; font: 16px sans-serif'>{}</select></body>".format(
                 options))
    try:
        _flipUntil(stim, lambda: stim.frameSeq > 1)
        handle = win.winHandle

        def frame():
            stim.draw()
            image = np.array(win._getFrame(buffer='back'))
            win.flip()
            return image

        closed = frame()
        x, y = _windowCoords(stim, (30, 20))
        handle.on_mouse_motion(x, y, 0, 0)
        handle.on_mouse_press(x, y, mouse.LEFT, 0)
        handle.on_mouse_release(x, y, mouse.LEFT, 0)
        _flipUntil(stim, lambda: False, timeout=0.5)
        opened = frame()
        # the options are drawn below the select
        assert np.abs(opened.astype(int) - closed).sum() > 1000

        for symbol in (key.DOWN, key.DOWN, key.RETURN):
            handle.on_key_press(symbol, 0)
            handle.on_key_release(symbol, 0)
        assert _flipUntil(stim, lambda: stim.evaluateJavaScript(
            "document.getElementById('s').selectedIndex") == 2)
    finally:
        stim.close()


# --------------------------------------------------------------------------
# frames on the GPU
#

def test_gpuTransport(win):
    """Frames come on the GPU where it is supported, drawn the right way up,
    and in shared memory when it is turned off."""
    from psychopy import visual
    if not _gpuSupported(win):
        pytest.skip("frames can't be passed on the GPU here")
    page = ("<body style='margin: 0'><div style='height: 50vh; background: "
            "#f00'></div><div style='height: 50vh; background: #0f0'></div>"
            "</body>")
    for gpuSharing, transport in ((True, 'gpu'), (False, 'shm')):
        stim = visual.WebBrowserStim(win, html=page, size=(320, 240),
                                     gpuSharing=gpuSharing, waitForLoad=True)
        try:
            # the first frames can be of the page before it is painted
            assert _flipUntil(
                stim, lambda: _drawnPixel(stim, (0, 60)) == (255, 0, 0))
            assert stim.frameTransport == transport
            stim.draw()
            assert _pixel(win, (0, -60)) == (0, 255, 0)
            win.flip()
        finally:
            stim.close()


def test_gpuResize(win):
    """Frames keep coming on the GPU, at the new size, when the page is
    resized."""
    from psychopy import visual
    if not _gpuSupported(win):
        pytest.skip("frames can't be passed on the GPU here")
    stim = visual.WebBrowserStim(win, html=PAGE, size=(160, 120),
                                 gpuSharing=True, waitForLoad=True)
    try:
        assert _flipUntil(stim, lambda: stim.frameTransport == 'gpu')
        stim.size = (240, 160)
        expected = (int(240 * win.pixScaleFactor),
                    int(160 * win.pixScaleFactor))
        assert _flipUntil(
            stim, lambda: stim._shown[1] is not None and
            (stim._shown[1].width, stim._shown[1].height) == expected)
        assert _flipUntil(
            stim, lambda: _drawnPixel(stim, (0, 70)) == (255, 0, 0))
        assert stim.frameTransport == 'gpu'
        win.flip()
    finally:
        stim.close()


def test_gpuCheckFailureFallsBack(win, monkeypatch):
    """If the frames the server shares read back wrong, frames come in shared
    memory instead, with a warning, and later pages don't try again."""
    import weakref
    from psychopy import visual
    from psychopy.visual.web import _gpushare, webbrowserstim
    if not _gpuSupported(win):
        pytest.skip("frames can't be passed on the GPU here")
    monkeypatch.setattr(webbrowserstim, '_gpuSupport',
                        weakref.WeakKeyDictionary())
    monkeypatch.setattr(_gpushare, 'checkColor', lambda slot: (1, 2, 3, 4))
    stim = visual.WebBrowserStim(win, html=PAGE, size=(160, 120),
                                 gpuSharing=True, waitForLoad=True)
    try:
        assert _flipUntil(stim, lambda: stim.frameTransport == 'shm' and
                          _drawnPixel(stim, (0, 0)) == (255, 0, 0))
        win.flip()
        assert stim._gpuSlots is None
        assert webbrowserstim._gpuSupport[win][0] is None
    finally:
        stim.close()


@pytest.fixture
def freshServer():
    """A web browser server started for the test, and another after it."""
    from psychopy.visual.web import _host
    _host._shutdownHost()
    yield
    _host._shutdownHost()


def test_gpuTurnedOffByEnvironment(win, monkeypatch, freshServer):
    """`PSYCHOPY_WEB_GPU_SHARING=0` keeps frames in shared memory, and the
    server doesn't set up for sharing them."""
    import weakref
    from psychopy import visual
    from psychopy.visual.web import _host, webbrowserstim
    monkeypatch.setenv(_host.ENV_GPU_SHARING, '0')
    monkeypatch.setattr(webbrowserstim, '_gpuSupport',
                        weakref.WeakKeyDictionary())
    stim = visual.WebBrowserStim(win, html=PAGE, size=(160, 120),
                                 gpuSharing=True, waitForLoad=True)
    try:
        assert _host.BrowserHost.current().info['gpu'] == 'off'
        assert _flipUntil(stim, lambda: stim.frameSeq > 1)
        assert stim.frameTransport == 'shm'
    finally:
        stim.close()


def test_gpuSlotsFreedOnGLThread(win, monkeypatch):
    """A page drawn from GPU slots, freed by the garbage collector on another
    thread, leaves deleting them to the window's thread."""
    import threading
    from psychopy import visual
    from psychopy.visual.web import _gpushare
    from ..test_glThread import collectorOnOtherThread, _letGo
    if not _gpuSupported(win):
        pytest.skip("frames can't be passed on the GPU here")
    deletes = []
    realDelete = _gpushare.GLSlots.delete

    def recordingDelete(self):
        deletes.append(threading.current_thread().name)
        realDelete(self)

    monkeypatch.setattr(_gpushare.GLSlots, 'delete', recordingDelete)
    with collectorOnOtherThread():
        stim = visual.WebBrowserStim(win, html=PAGE, size=(160, 120),
                                     gpuSharing=True, waitForLoad=True)
        assert _flipUntil(stim, lambda: stim.frameTransport == 'gpu')
        _letGo(stim)
        del stim

    assert not deletes  # left for the window
    win.flip()
    assert deletes == [threading.main_thread().name]
