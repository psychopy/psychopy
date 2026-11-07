"""Tests for PsychoPy's OpenGL loader, `psychopy.tools.opengl`.
"""
import ctypes
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

import psychopy
import psychopy.tools.opengl as GL
from psychopy.tests import skip_under_vm
from psychopy.tools.opengl import _lib

# the generator is only in the repository, not installed packages
_GENERATOR = Path(psychopy.__file__).parents[1] / 'building' / \
    'generateGLBindings.py'
needsGenerator = pytest.mark.skipif(
    not _GENERATOR.is_file(), reason="needs the PsychoPy repository")


@pytest.fixture(scope='module')
def generator():
    return runpy.run_path(str(_GENERATOR))


def _ctypeName(ctype):
    """Comparable description of a `ctypes` type, since equivalent types from
    different modules are different objects."""
    if ctype is None:
        return 'void'
    if issubclass(ctype, ctypes._Pointer):
        return f'POINTER({_ctypeName(ctype._type_)})'
    if issubclass(ctype, ctypes._CFuncPtr):
        argtypes = ', '.join(_ctypeName(t) for t in ctype._argtypes_)
        return f'FUNCTYPE({_ctypeName(ctype._restype_)}, {argtypes})'
    if issubclass(ctype, ctypes.Structure):
        return 'Structure'

    return ctype.__name__


@needsGenerator
def test_usedNamesBound(generator):
    """Every OpenGL name PsychoPy uses is bound."""
    used = generator['findUsedNames'](Path(psychopy.__file__).parent)
    assert used  # the search works
    assert not {name for name in used if not hasattr(GL, name)}


@needsGenerator
def test_bindingsUpToDate(generator):
    """The bindings are what the generator creates from the registry."""
    commit = generator['COMMIT'].read_text().strip()
    bindings, groups, _ = generator['generate'](generator['REGISTRY'], commit)
    package = Path(GL.__file__).parent
    assert bindings == (package / '_bindings.py').read_text(encoding='utf-8')
    assert groups == (package / '_enumgroups.py').read_text(encoding='utf-8')


def test_pygletParity():
    """Everything in `pyglet.gl` is bound, with the same types and values, so
    either can be used with the other's values."""
    pytest.importorskip('pyglet', minversion='2.0')
    import psychopy.tools.pygletgl  # creates pyglet's (legacy) shadow window
    from pyglet.gl import gl as pygletGL, gl_compat as pygletCompat

    missing, different = [], []
    for module in (pygletGL, pygletCompat):
        for name, pygletValue in vars(module).items():
            if not name.startswith(('gl', 'GL_')):
                continue
            if not hasattr(GL, name):
                missing.append(name)
                continue
            value = getattr(GL, name)
            if name.startswith('GL_'):
                if value != pygletValue:
                    different.append(name)
            elif hasattr(pygletValue, 'argtypes'):
                # (`argtypes` are a tuple once functions are linked)
                ours = [_ctypeName(t) for t in
                        [value.restype, *value.argtypes]]
                theirs = [_ctypeName(t) for t in
                          [pygletValue.restype, *pygletValue.argtypes]]
                if ours != theirs:
                    different.append(name)

    assert not missing
    assert not different


def test_noContext():
    """Without a context, `gl_info` reports nothing (in a new process, since
    other tests leave pyglet's shadow window current)."""
    script = (
        "import psychopy.tools.opengl as GL\n"
        "assert not GL.gl_info.have_context()\n"
        "assert GL.gl_info.get_version() == (0, 0)\n"
        "assert GL.gl_info.get_extensions() == set()\n")
    subprocess.run([sys.executable, '-c', script], check=True)


@pytest.mark.parametrize('winType', [
    'pyglet',
    pytest.param('glfw', marks=skip_under_vm(
        reason="GLFW doesn't work on (macOS) virtual machine")),
])
def test_drawWithWindow(winType):
    """Functions work with contexts made by each backend."""
    from psychopy import visual
    win = visual.Window(
        (64, 64), winType=winType, allowGUI=False, autoLog=False)
    try:
        assert GL.gl_info.have_context()
        assert GL.gl_info.have_version(2, 1)
        assert GL.gl_info.get_renderer()

        GL.glClearColor(0., 1., 0., 1.)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        pixel = (GL.GLubyte * 4)()
        GL.glReadPixels(0, 0, 1, 1, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pixel)
        assert list(pixel) == [0, 255, 0, 255]

        # linked functions replace their placeholders
        assert not isinstance(GL.glClearColor, _lib.GLFunction)

        # concave, so needs the GLU tessellator
        shape = visual.ShapeStim(
            win, vertices=[(-.5, -.5), (0, .5), (.5, -.5), (0, 0)],
            fillColor='red', autoLog=False)
        shape.draw()
        win.flip()
    finally:
        win.close()


@pytest.mark.skipif(
    not sys.platform.startswith('linux'), reason="EGL is only used on Linux")
def test_eglContext():
    """Functions work with EGL contexts, as GLFW creates under Wayland (in a
    new process, since a GLX context can't be current on the same thread as an
    EGL one, and other tests leave pyglet's current)."""
    pytest.importorskip('glfw')
    script = (
        "import sys\n"
        "import glfw\n"
        "import psychopy.tools.opengl as GL\n"
        "from psychopy.tools.opengl import _platform\n"
        "if not glfw.init():\n"
        "    sys.exit(77)\n"
        # also EGL under X11, so this runs without Wayland
        "glfw.window_hint(glfw.CONTEXT_CREATION_API, glfw.EGL_CONTEXT_API)\n"
        "win = glfw.create_window(16, 16, 'EGL', None, None)\n"
        "if not win:\n"
        "    sys.exit(77)\n"
        "glfw.make_context_current(win)\n"
        "assert _platform._getCurrentEGLContext()\n"
        "assert GL.gl_info.have_version(2, 1)\n"
        "GL.glClearColor(0., 1., 0., 1.)\n"
        "GL.glClear(GL.GL_COLOR_BUFFER_BIT)\n"
        "pixel = (GL.GLubyte * 4)()\n"
        "GL.glReadPixels(0, 0, 1, 1, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pixel)\n"
        "assert list(pixel) == [0, 255, 0, 255], list(pixel)\n"
        # not exported by libOpenGL, so found with `eglGetProcAddress()`
        "program = GL.glCreateProgramObjectARB()\n"
        "assert program\n"
        "GL.glDeleteObjectARB(program)\n"
        "glfw.terminate()\n")
    result = subprocess.run([sys.executable, '-c', script])
    if result.returncode == 77:
        pytest.skip("can't create an EGL context")
    assert result.returncode == 0


@pytest.fixture
def win():
    from psychopy import visual
    win = visual.Window((64, 64), allowGUI=False, autoLog=False)
    yield win
    win.close()


@pytest.fixture
def errorChecking():
    """Check for errors after every call, during a test."""
    GL.setErrorChecking(True)
    yield
    GL.setErrorChecking(False)


def test_errorChecking(win, errorChecking):
    """With error checking on, the call causing an OpenGL error raises a
    `GLError` describing it, except between `glBegin()` and `glEnd()` where
    checking is an error itself."""
    assert GL.getErrorChecking()
    with pytest.raises(GL.GLError) as excinfo:
        GL.glEnable(0xDEAD)
    error = excinfo.value
    assert error.errors == [GL.GL_INVALID_ENUM]
    assert error.errorNames == ['GL_INVALID_ENUM']
    assert error.function == 'glEnable'
    assert error.arguments == (0xDEAD,)
    assert 'after calling `glEnable(0xDEAD)`' in str(error)
    assert "isn't one of the EnableCap values" in str(error)

    GL.glBegin(GL.GL_TRIANGLES)
    for vertex in [(0., 0.), (1., 0.), (0., 1.)]:
        GL.glVertex2f(*vertex)
    GL.glEnd()

    # and is turned off for functions linked while it was on
    GL.setErrorChecking(False)
    GL.glEnable(0xDEAD)
    assert GL.getErrors() == [GL.GL_INVALID_ENUM]
    assert GL.getErrors() == []  # cleared


def test_checkErrors(win):
    """`checkErrors()` raises a `GLError` for errors reported since the last
    check, saying how to find the call that caused them."""
    GL.checkErrors()  # none
    GL.glEnable(0xDEAD)
    GL.glClear(0x8)  # not a buffer bit
    with pytest.raises(GL.GLError) as excinfo:
        GL.checkErrors('in this test')
    error = excinfo.value
    # many drivers only keep the first error until it's read
    assert error.errors[0] == GL.GL_INVALID_ENUM
    assert set(error.errors) <= {GL.GL_INVALID_ENUM, GL.GL_INVALID_VALUE}
    assert error.function is None
    assert 'in this test' in str(error)
    assert 'PSYCHOPY_DEBUG_GL' in str(error)
    GL.checkErrors()  # cleared


def test_flipRaisesErrors(win):
    """`Window.flip()` raises errors from drawing the frame."""
    win.flip()
    GL.glEnable(0xDEAD)
    with pytest.raises(GL.GLError, match='during the last frame'):
        win.flip()
    win.flip()  # cleared


def _placeholder(name):
    """The `GLFunction` placeholder of an OpenGL function."""
    return next(f for f in _lib._functions if f.__name__ == name)


@pytest.mark.parametrize('name, arguments, expected', [
    ('glClear', (GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT,),
     'glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)'),  # in bit order
    ('glDrawArrays', (GL.GL_TRIANGLES, 0, 3), 'glDrawArrays(GL_TRIANGLES, 0, 3)'),
    ('glBlendFunc', (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA),
     'glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)'),
    ('glTexImage2D',
     (GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 4, 4, 0, GL.GL_RGBA,
      GL.GL_UNSIGNED_BYTE, None),
     'glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 4, 4, 0, GL_RGBA, '
     'GL_UNSIGNED_BYTE, None)'),
    ('glColor4f', (1., .5, 0., 1.), 'glColor4f(1, 0.5, 0, 1)'),
    ('glGenTextures', (1, ctypes.byref(GL.GLuint())),
     'glGenTextures(1, byref(c_uint(0)))'),
    ('glLoadMatrixf', ((GL.GLfloat * 16)(),), 'glLoadMatrixf(c_float[16])'),
])
def test_errorMessages(name, arguments, expected):
    """Error messages describe the call, naming enumerants and bit flags."""
    error = GL.GLError(
        [GL.GL_INVALID_OPERATION], _placeholder(name), arguments)
    assert f'after calling `{expected}`' in str(error)
    assert 'GL_INVALID_OPERATION (0x0502)' in str(error)


def test_errorMessageMultiple():
    """All errors reported are described."""
    error = GL.GLError([GL.GL_INVALID_ENUM, GL.GL_OUT_OF_MEMORY])
    message = str(error)
    assert message.startswith('OpenGL errors since errors were last checked')
    assert 'GL_INVALID_ENUM (0x0500)' in message
    assert 'GL_OUT_OF_MEMORY (0x0505)' in message


def test_missingFunction():
    """Calling a function the driver doesn't have raises `GLException`."""
    # not starting with 'gl', since on Linux `glXGetProcAddressARB()` returns
    # a dispatch stub for any name that does
    func = _lib.link('psychopyNotAFunction', None, [], 'OpenGL 9.9')
    with pytest.raises(GL.GLException, match='psychopyNotAFunction'):
        func()
