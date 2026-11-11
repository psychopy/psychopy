"""Tests for `WebBrowserStim` and the web browser server process, using a fake
server (`fakeserver.py`) so they don't need Qt WebEngine."""
import os
import subprocess
import sys
import textwrap
import time

import numpy as np
import pytest

from psychopy.tests import skip_under_vm
from psychopy.visual.web import _host
from ..test_glThread import glDeletes  # noqa: F401 (fixture)

FAKE_SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'fakeserver.py')


@pytest.fixture
def fakeServer(monkeypatch):
    """Use the fake server, in a host of its own."""
    _host._shutdownHost()
    monkeypatch.setenv('PSYCHOPY_WEB_SERVER_CMD', '"{}" "{}"'.format(
        sys.executable, FAKE_SERVER))
    yield
    _host._shutdownHost()


@pytest.fixture(scope='module')
def win():
    from psychopy import visual
    win = visual.Window((128, 128), winType='pyglet', units='pix',
                        color=(-1, -1, -1), allowGUI=False, autoLog=False)
    yield win
    win.close()


def _pixel(win, pos):
    """Color of the back buffer at `pos` ('pix' from the center)."""
    import psychopy.tools.pygletgl as GL
    buf = (GL.GLubyte * 4)()
    x = int(pos[0] * win.pixScaleFactor + win.size[0] / 2)
    y = int(pos[1] * win.pixScaleFactor + win.size[1] / 2)
    GL.glReadPixels(x, y, 1, 1, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, buf)
    return tuple(buf)[:3]


def _waitFor(stim, condition, timeout=5.):
    """Flip until `condition()` is true, returning whether it became so."""
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        stim.draw()
        stim.win.flip()
        if condition():
            return True
    return False


def _inputs(stim):
    """Input that reached the fake page, which it sends back."""
    return [m for m in stim.getMessages() if m.get('op') == 'input']


@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
class TestWebBrowserStim:

    def test_host(self, fakeServer):
        host = _host.BrowserHost.get()
        assert host.info['versions'] == {'fake': True}
        assert host.ping()
        assert _host.BrowserHost.get() is host

    def test_draw(self, win, fakeServer):
        from psychopy import visual
        stim = visual.WebBrowserStim(win, html='color:0,255,0', size=(64, 32),
                                     waitForLoad=True)
        try:
            assert stim.resolution == (64 * win.pixScaleFactor,
                                       32 * win.pixScaleFactor)
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            stim.draw()
            assert _pixel(win, (0, 0)) == (0, 255, 0)
            assert _pixel(win, (0, 25)) == (0, 0, 0)  # outside it
            win.flip()
        finally:
            stim.close()

    def test_opacity(self, win, fakeServer):
        from psychopy import visual
        stim = visual.WebBrowserStim(win, html='color:255,255,255',
                                     size=(64, 32), opacity=0.5)
        try:
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            stim.draw()
            assert np.allclose(_pixel(win, (0, 0)), 128, atol=2)
            win.flip()
        finally:
            stim.close()

    def test_mouse(self, win, fakeServer):
        """Mouse input over the stimulus reaches the page, at the position on
        the page."""
        from psychopy import visual
        from pyglet.window import mouse
        stim = visual.WebBrowserStim(win, html='color:0,0,255', pos=(10, 0),
                                     size=(64, 32), resolution=(640, 320))
        try:
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            handle = win.winHandle
            # top-left quarter of the stimulus
            x, y = win.backend._pixToWindowCoords((10 - 16, 8))
            handle.on_mouse_motion(x, y, 0, 0)
            handle.on_mouse_press(x, y, mouse.LEFT, 0)
            handle.on_mouse_release(x, y, mouse.LEFT, 0)
            handle.on_mouse_scroll(x, y, 0, 2)
            # outside it
            x, y = win.backend._pixToWindowCoords((-60, 0))
            handle.on_mouse_press(x, y, mouse.LEFT, 0)
            handle.on_mouse_release(x, y, mouse.LEFT, 0)
            got = []
            _waitFor(stim, lambda: got.extend(_inputs(stim)) or len(got) >= 5)
            actions = [(m['kind'], m.get('action')) for m in got]
            assert actions[:5] == [
                ('focus', None), ('mouse', 'move'), ('mouse', 'press'),
                ('mouse', 'release'), ('wheel', None)] or actions[:5] == [
                ('mouse', 'move'), ('focus', None), ('mouse', 'press'),
                ('mouse', 'release'), ('wheel', None)]
            press = [m for m in got if m.get('action') == 'press'][0]
            assert np.allclose((press['x'], press['y']), (160, 80), atol=1)
            assert press['button'] == 'left' and press['buttons'] == ['left']
            assert [m for m in got if m['kind'] == 'wheel'][0]['dy'] == 2
            assert stim.hasFocus
            # the press outside didn't reach the page
            assert len([m for m in got if m.get('action') == 'press']) == 1
        finally:
            stim.close()

    def test_keys(self, win, fakeServer):
        """Keys are passed on with the text they type while it has focus, and
        shortcuts straight away."""
        from psychopy import visual
        from pyglet.window import key
        stim = visual.WebBrowserStim(win, html='color:0,0,255', size=(64, 32))
        try:
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            stim.focus()
            handle = win.winHandle
            handle.on_key_press(key.A, key.MOD_SHIFT)
            handle.on_text('A')
            handle.on_key_release(key.A, key.MOD_SHIFT)
            handle.on_key_press(key.C, key.MOD_CTRL)
            handle.on_key_release(key.C, key.MOD_CTRL)
            handle.on_key_press(key.RETURN, 0)
            handle.on_text('\r')
            handle.on_key_release(key.RETURN, 0)
            got = []
            _waitFor(stim, lambda: got.extend(_inputs(stim)) or len(
                [m for m in got if m['kind'] == 'key']) >= 6)
            keys = [(m['action'], m['key'], m['text'])
                    for m in got if m['kind'] == 'key']
            assert keys == [
                ('press', 'a', 'A'), ('release', 'a', ''),
                ('press', 'c', ''), ('release', 'c', ''),
                ('press', 'return', ''), ('release', 'return', '')]

            # not passed on without focus
            stim.interactive = False
            handle.on_key_press(key.B, 0)
            handle.on_text('b')
            _waitFor(stim, lambda: False, timeout=0.2)
            assert not [m for m in _inputs(stim) if m['kind'] == 'key']
        finally:
            stim.close()

    def test_resize(self, win, fakeServer):
        """Frames of the new size are drawn after the stimulus is resized."""
        from psychopy import visual
        stim = visual.WebBrowserStim(win, html='color:255,0,0', size=(64, 32))
        try:
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            stim.size = (32, 64)
            expected = (32 * win.pixScaleFactor, 64 * win.pixScaleFactor)
            assert stim.resolution == expected
            assert _waitFor(
                stim, lambda: stim._ring is not None and
                (stim._ring.width, stim._ring.height) == expected)
            stim.draw()
            assert _pixel(win, (0, 30)) == (255, 0, 0)
            win.flip()
        finally:
            stim.close()

    def test_windowToDocument(self, win, fakeServer):
        """Positions in the window map onto the document as the page was
        drawn: zoomed and scrolled, in any units."""
        from psychopy import layout, visual
        stim = visual.WebBrowserStim(
            win, html='color:0,0,255;scroll:100,500', pos=(10, 0),
            size=(64, 32), resolution=(640, 320), zoom=2.)
        try:
            # nothing scrolled before the first frame
            assert stim.scrollPosition == (0., 0.)
            assert stim.documentSize is None
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            assert stim.scrollPosition == (100., 500.)
            assert stim.documentSize == (2000., 3000.)
            # the page is 320 x 160 CSS pixels, from (100, 500) on the document
            for winPos, docPos in [((-22, 16), (100, 500)),
                                   ((10, 0), (260, 580)),
                                   ((42, -16), (420, 660))]:
                assert np.allclose(stim.windowToDocument(winPos), docPos)
            assert np.isnan(stim.windowToDocument((60, 0))).all()  # off it
            # many at once, with tracking lost for one
            got = stim.windowToDocument(
                [(10, 0), (np.nan, np.nan), (-60, 0), (-22, 16)])
            assert got.shape == (4, 2)
            assert np.allclose(got[[0, 3]], [(260, 580), (100, 500)])
            assert np.isnan(got[[1, 2]]).all()
            # other units
            norm = layout.Position((10, 0), 'pix', win).norm
            assert np.allclose(
                stim.windowToDocument(norm, units='norm'), (260, 580))
            stim.units = 'norm'
            assert np.allclose(stim.windowToDocument(norm), (260, 580))
        finally:
            stim.close()

    def test_javascript(self, win, fakeServer):
        from psychopy import visual
        stim = visual.WebBrowserStim(win, html='color:0,0,0', size=(16, 16))
        try:
            assert stim.evaluateJavaScript('1 + 2') == 5  # fake gives length
            results = []
            stim.runJavaScript('abc', results.append)
            assert _waitFor(stim, lambda: results == [3])
            with pytest.raises(TimeoutError):
                stim.evaluateJavaScript('ignore', timeout=0.3)
        finally:
            stim.close()

    def test_serverCrash(self, win, fakeServer):
        """The stimulus keeps drawing its last frame if the server stops, and
        a new server is started for the next one."""
        from psychopy import visual
        stim = visual.WebBrowserStim(win, html='color:0,255,0', size=(64, 32))
        try:
            assert _waitFor(stim, lambda: stim.frameSeq > 0)
            stim.runJavaScript('crash')
            assert _waitFor(stim, lambda: stim.loadError is not None)
            stim.draw()
            assert _pixel(win, (0, 0)) == (0, 255, 0)
            win.flip()
            with pytest.raises(TimeoutError):
                stim.evaluateJavaScript('1', timeout=0.2)
        finally:
            stim.close()
        stim = visual.WebBrowserStim(win, html='color:0,0,0', size=(16, 16))
        try:
            assert stim.waitForLoad()
        finally:
            stim.close()

    def test_windowClose(self, fakeServer):
        """Closing the window closes its pages."""
        from psychopy import visual
        win = visual.Window((64, 64), winType='pyglet', allowGUI=False,
                            autoLog=False)
        stim = visual.WebBrowserStim(win, html='color:0,0,0', size=(16, 16),
                                     units='pix', autoDraw=True)
        win.flip()
        channel = stim._channel
        win.close()
        assert channel.closed
        assert stim._channel is None


@skip_under_vm(reason="Pyglet doesn't work on (macOS) virtual machine")
def test_freedOnGLThread(win, fakeServer, glDeletes):  # noqa: F811
    """A stimulus freed by the garbage collector on another thread leaves its
    texture for the window to delete at its next flip, and closes its page."""
    import threading
    from psychopy import visual
    from ..test_glThread import collectorOnOtherThread, _letGo, _textureExists
    with collectorOnOtherThread():
        stim = visual.WebBrowserStim(win, html='color:0,0,0', size=(16, 16))
        for _ in range(300):
            stim.draw()
            win.flip()
            if stim._texture is not None:
                break
        textureId = stim._texture.textureId.value
        channel = stim._channel
        _letGo(stim)
        del stim

    assert 'Collector' not in glDeletes
    assert _textureExists(textureId)
    assert channel.closed

    win.flip()
    assert set(glDeletes) == {threading.main_thread().name}
    assert not _textureExists(textureId)


ORPHAN_SCRIPT = textwrap.dedent("""
    import sys, time
    from psychopy.visual.web import _host
    host = _host.BrowserHost.get()
    print('serverPid', host.info['pid'], flush=True)
    time.sleep(60)
""")


@pytest.mark.skipif(sys.platform == 'win32', reason="uses POSIX signals")
@pytest.mark.parametrize('server', ['fake', 'real'])
def test_orphanedServerExits(tmp_path, server):
    """The server (and the page processes the real one starts) exits by itself
    when the process that started it is killed, without a chance to clean up,
    and removes its shared memory."""
    import psutil
    import signal
    from psychopy.visual import web
    env = dict(os.environ)
    env.pop('PSYCHOPY_WEB_SERVER_CMD', None)
    script = ORPHAN_SCRIPT
    if server == 'fake':
        env['PSYCHOPY_WEB_SERVER_CMD'] = '"{}" "{}"'.format(
            sys.executable, FAKE_SERVER)
    elif not web.isAvailable():
        pytest.skip("needs Qt WebEngine")
    else:
        # open a page, so there are page processes and shared memory
        script = script.replace(
            "host = _host.BrowserHost.get()",
            "host = _host.BrowserHost.get()\n"
            "channel = host.openChannel()\n"
            "channel.send('create', w=64, h=64, html='<p>hi</p>')\n"
            "time.sleep(3)")
    scriptPath = tmp_path / 'parent.py'
    scriptPath.write_text(script)
    shmBefore = set(os.listdir('/dev/shm')) if os.path.isdir('/dev/shm') \
        else set()
    parent = subprocess.Popen([sys.executable, str(scriptPath)], env=env,
                              stdout=subprocess.PIPE, text=True)
    try:
        # other output (e.g. pygame's banner) may come first
        for line in parent.stdout:
            if line.startswith('serverPid'):
                serverPid = int(line.split()[1])
                break
        server = psutil.Process(serverPid)
        procs = [server] + server.children(recursive=True)
        os.kill(parent.pid, signal.SIGKILL)
        parent.wait(5)
        gone, alive = psutil.wait_procs(procs, timeout=8)
        assert not alive, alive
        if os.path.isdir('/dev/shm'):
            ours = {name for name in set(os.listdir('/dev/shm')) - shmBefore
                    if name.startswith('pw{:x}_'.format(serverPid))}
            assert not ours
    finally:
        if parent.poll() is None:
            parent.kill()
