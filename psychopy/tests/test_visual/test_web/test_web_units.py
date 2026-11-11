"""Tests for the parts of `psychopy.visual.web` which need neither Qt nor a
window: page geometry, key mapping, the protocol, shared memory and the
watchdog."""
import os
import sys

import numpy as np
import pytest

from psychopy.visual.web import (
    _geometry, _keymap, _protocol, _shm, _watchdog)


# --------------------------------------------------------------------------
# geometry
#

def _rectVertices(pos=(0, 0), size=(200, 100), ori=0., flipHoriz=False,
                  flipVert=False):
    """Corners of a page as `verticesPix` gives them: bottom-right,
    bottom-left, top-left, top-right, flipped, then rotated clockwise by `ori`
    degrees about `pos`, as PsychoPy rotates stimuli."""
    verts = np.array([[.5, -.5], [-.5, -.5], [-.5, .5], [.5, .5]])
    if flipHoriz:
        verts[:, 0] *= -1
    if flipVert:
        verts[:, 1] *= -1
    verts *= size
    rad = np.radians(ori)
    rot = np.array([[np.cos(rad), -np.sin(rad)], [np.sin(rad), np.cos(rad)]])
    return verts.dot(rot) + pos


@pytest.mark.parametrize('ori', [0., 90., 33.])
@pytest.mark.parametrize('flipHoriz', [False, True])
@pytest.mark.parametrize('flipVert', [False, True])
def test_geometryRoundTrip(ori, flipHoriz, flipVert):
    verts = _rectVertices((15, -20), (200, 100), ori, flipHoriz, flipVert)
    pageSize = (400, 200)
    for pagePos in [(0, 0), (400, 200), (100, 150), (399, 1)]:
        winPos = _geometry.pageToWindowPix(pagePos, verts, pageSize)
        x, y, inside = _geometry.windowPixToPage(winPos, verts, pageSize)
        assert np.allclose((x, y), pagePos)
        assert inside


def test_geometryCorners():
    """The page's top-left is at the top-left of an unrotated stimulus, and y
    increases downwards on the page."""
    verts = _rectVertices((10, 20), (200, 100))
    pageSize = (400, 200)
    for winPos, pagePos in [((-90, 70), (0, 0)), ((110, 70), (400, 0)),
                            ((-90, -30), (0, 200)), ((10, 20), (200, 100))]:
        x, y, inside = _geometry.windowPixToPage(winPos, verts, pageSize)
        assert np.allclose((x, y), pagePos)
    assert not _geometry.windowPixToPage((111, 20), verts, pageSize)[2]
    assert not _geometry.windowPixToPage((10, -31), verts, pageSize)[2]


def test_geometryFlip():
    """Flipping horizontally puts the page's left edge on the right."""
    verts = _rectVertices(size=(200, 100), flipHoriz=True)
    x, y, _ = _geometry.windowPixToPage((90, 40), verts, (200, 100))
    assert np.allclose((x, y), (10, 10))


def test_geometryNoArea():
    verts = _rectVertices(size=(0, 100))
    x, y, inside = _geometry.windowPixToPage((0, 0), verts, (200, 100))
    assert not inside and np.isnan(x)
    xy, inside = _geometry.windowPixToPageArray(
        [(0, 0), (1, 1)], verts, (200, 100))
    assert xy.shape == (2, 2) and np.isnan(xy).all() and not inside.any()


@pytest.mark.parametrize('ori', [0., 33.])
@pytest.mark.parametrize('flipVert', [False, True])
def test_geometryArray(ori, flipVert):
    """Many positions at once map as each does on its own, and `nan` positions
    are outside."""
    verts = _rectVertices((15, -20), (200, 100), ori, flipVert=flipVert)
    pageSize = (400, 200)
    rng = np.random.default_rng(0)
    winPos = rng.uniform(-150, 150, (50, 2))
    xy, inside = _geometry.windowPixToPageArray(winPos, verts, pageSize)
    assert xy.shape == (50, 2) and inside.shape == (50,)
    assert inside.any() and not inside.all()
    for pos, gotXY, gotInside in zip(winPos, xy, inside):
        x, y, ins = _geometry.windowPixToPage(pos, verts, pageSize)
        assert np.allclose(gotXY, (x, y)) and gotInside == ins
    xy, inside = _geometry.windowPixToPageArray(
        [(np.nan, 0.)], verts, pageSize)
    assert not inside[0]


# --------------------------------------------------------------------------
# key mapping
#

def test_keymapQtNamesExist():
    """Every Qt name the key map gives is a member of Qt's enums (PyQt6 is a
    dependency, Qt WebEngine isn't needed)."""
    QtCore = pytest.importorskip('PyQt6.QtCore')
    Qt = QtCore.Qt
    for mac in (False, True):
        names = set(_keymap._KEYS_.values()) | set(_keymap._MAC_KEYS_.values())
        for name in names:
            assert hasattr(Qt.Key, name), name
        for mods in range(256):
            for name in _keymap.qtModifierNames(mods, mac):
                assert hasattr(Qt.KeyboardModifier, name), name
    for button in ('left', 'middle', 'right', 'back', 'forward', None):
        assert hasattr(Qt.MouseButton, _keymap.qtButtonName(button))


def test_keymapPygletNames():
    """Keys named as pyglet window listeners name them are known."""
    pytest.importorskip('pyglet')
    from pyglet.window import key
    from psychopy.visual.backends._events import pygletKeyName
    for symbol in [key.A, key.Z, key._0, key._9, key.RETURN, key.ESCAPE,
                   key.TAB, key.BACKSPACE, key.DELETE, key.LEFT, key.PAGEUP,
                   key.PAGEDOWN, key.HOME, key.END, key.F1, key.F12, key.SPACE,
                   key.LSHIFT, key.LCTRL, key.MINUS, key.GRAVE, key.NUM_1,
                   key.NUM_ENTER, key.NUM_ADD]:
        name = pygletKeyName(symbol)
        assert _keymap.qtKeyName(name) is not None, name


def test_keymapMacModifiers():
    """Qt calls command "Control" and control "Meta" on macOS."""
    assert _keymap.qtModifierNames(_keymap.MOD_CTRL, mac=False) == [
        'ControlModifier']
    assert _keymap.qtModifierNames(_keymap.MOD_CTRL, mac=True) == [
        'MetaModifier']
    assert _keymap.qtModifierNames(_keymap.MOD_COMMAND, mac=True) == [
        'ControlModifier']
    assert _keymap.qtKeyName('lcommand', mac=True) == 'Key_Control'
    assert _keymap.qtKeyName('lctrl', mac=False) == 'Key_Control'


def test_keymapText():
    assert _keymap.keyText('return') == '\r'
    assert _keymap.keyText('backspace') == '\x08'
    assert _keymap.keyText('a') == ''
    assert _keymap.isKeypad('num_1') and not _keymap.isKeypad('numlock')


# --------------------------------------------------------------------------
# protocol and shared memory
#

def test_packUnpack():
    msg = {'op': 'input', 'view': 3, 'kind': 'key', 'text': 'é',
           'buttons': ['left'], 'x': 1.5}
    assert _protocol.unpack(_protocol.pack(msg)) == msg


def test_shmNameLength():
    """Names fit macOS's 31 character limit (with Python's leading slash)."""
    name = _protocol.shmName(4194304, 2 ** 31, 2 ** 31)
    assert len(name) <= 30


@pytest.fixture
def ring():
    ring = _shm.FrameRing.create(
        _protocol.shmName(os.getpid(), 999, 1), 5, 3, 24, 'bgra_pm', 3, 1)
    yield ring
    ring.close()


def test_frameRing(ring):
    """Frames written by the owner are read by another attachment, at the
    address given."""
    import ctypes
    reader = _shm.FrameRing.attach(ring.name, 5, 3, 24, 'bgra_pm', 3, 1)
    try:
        assert reader.slotSize % 64 == 0
        frame = bytes(range(72))
        ring.write(2, frame)
        view = reader.view(2)
        assert bytes(view) == frame
        del view
        assert ctypes.string_at(reader.address(2), 72) == frame
        with pytest.raises(IndexError):
            reader.address(3)
        with pytest.raises(ValueError):
            ring.write(0, b'short')
    finally:
        reader.close()
    # the owner still has it after another process detaches
    ring.write(0, bytes(72))


def test_frameRingMismatch(ring):
    """Attaching checks the segment holds what the server said."""
    with pytest.raises(ValueError):
        _shm.FrameRing.attach(ring.name, 5, 3, 24, 'bgra_pm', 3, 2)
    with pytest.raises(ValueError):
        _shm.FrameRing.attach(ring.name, 6, 3, 24, 'bgra_pm', 3, 1)


@pytest.mark.skipif(not os.path.isdir('/dev/shm'), reason="needs /dev/shm")
def test_frameRingRemoved():
    """The owner removes the segment, an attachment doesn't."""
    name = _protocol.shmName(os.getpid(), 998, 1)
    ring = _shm.FrameRing.create(name, 4, 4, 16, 'rgba_pm', 3, 1)
    reader = _shm.FrameRing.attach(name, 4, 4, 16, 'rgba_pm', 3, 1)
    reader.address(0)  # holds a view of it, which closing must drop
    reader.close()
    assert os.path.exists('/dev/shm/' + name)
    _shm.closeOwnedRings()
    assert not os.path.exists('/dev/shm/' + name)
    ring.close()  # already closed


# --------------------------------------------------------------------------
# watchdog
#

def test_parseServerCmdline():
    assert _watchdog.parseServerCmdline(
        [sys.executable, '/x/_server.py', '--address', 'a', '--parent-pid',
         '123']) == 123
    assert _watchdog.parseServerCmdline(
        [sys.executable, '/x/other.py', '--parent-pid', '123']) is None
    assert _watchdog.parseServerCmdline(
        [sys.executable, '/x/_server.py', '--parent-pid']) is None
    assert _watchdog.parseServerCmdline(None) is None


def test_isProcessGone():
    import psutil
    assert not _watchdog.isProcessGone(os.getpid())
    # created after the time given, so a different process with that ID
    created = psutil.Process().create_time()
    assert _watchdog.isProcessGone(os.getpid(), createdBefore=created - 10)
    assert not _watchdog.isProcessGone(os.getpid(), createdBefore=created)


# --------------------------------------------------------------------------
# frames on the GPU: passing file descriptors, OpenGL and Vulkan functions
#

@pytest.mark.skipif(os.name != 'posix', reason="passes POSIX file descriptors")
def test_fdPassingWithDefaultTimeout(tmp_path):
    """File descriptors pass on a connection and leave it blocking, even with
    a socket default timeout set (as `psychopy.web` sets one), which would
    otherwise make later reads fail with BlockingIOError."""
    import socket
    from multiprocessing import Pipe
    path = tmp_path / 'shared.txt'
    path.write_text('shared file')
    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(5)
    sender, receiver = Pipe()
    try:
        fd = os.open(str(path), os.O_RDONLY)
        sender.send_bytes(_protocol.pack({'op': 'surface', 'nfds': 1}))
        _protocol.sendFds(sender, [fd])
        os.close(fd)
        sender.send_bytes(_protocol.pack({'op': 'frame'}))

        assert _protocol.unpack(receiver.recv_bytes())['nfds'] == 1
        fds = _protocol.recvFds(receiver, 1)
        assert os.get_blocking(receiver.fileno())
        assert _protocol.unpack(receiver.recv_bytes()) == {'op': 'frame'}
        with os.fdopen(fds[0]) as f:
            assert f.read() == 'shared file'
    finally:
        socket.setdefaulttimeout(previous)
        sender.close()
        receiver.close()


@pytest.mark.skipif(os.name != 'posix', reason="POSIX sockets")
def test_makeBlocking():
    from multiprocessing import Pipe
    a, b = Pipe()
    try:
        os.set_blocking(a.fileno(), False)
        _protocol.makeBlocking(a)
        assert os.get_blocking(a.fileno())
    finally:
        a.close()
        b.close()


def test_glFunctionsUnknown():
    """Names which aren't among the OpenGL functions used raise
    AttributeError, rather than being looked up."""
    from psychopy.visual.web import _glext
    gl = _glext.GLFunctions(lambda name: 0)
    with pytest.raises(AttributeError):
        gl.notAFunction


def test_vulkanAllocator():
    """Memory and semaphores are allocated on a device found by its UUIDs and
    exported as file descriptors; an unknown device is refused."""
    from psychopy.visual.web import _vkshare
    try:
        devices = _vkshare.listDevices()
    except _vkshare.VulkanError as err:
        pytest.skip("no Vulkan: {}".format(err))
    if not devices:
        pytest.skip("no Vulkan devices")
    name, deviceUUID, driverUUID = devices[0]
    try:
        allocator = _vkshare.VulkanAllocator(deviceUUID, driverUUID)
    except _vkshare.VulkanError as err:
        pytest.skip("{} can't export memory: {}".format(name, err))
    try:
        image = allocator.allocateImage(64, 32)
        semaphore = allocator.createSemaphore()
        assert image.size >= 64 * 32 * 4
        fds = [image.exportFd(), image.exportFd(), semaphore.exportFd()]
        assert len(set(fds)) == 3 and all(fd >= 0 for fd in fds)
        for fd in fds:
            os.close(fd)
        image.destroy()
        semaphore.destroy()
    finally:
        allocator.destroy()
    with pytest.raises(_vkshare.VulkanError, match="No Vulkan device"):
        _vkshare.VulkanAllocator('00' * 16, '00' * 16)
