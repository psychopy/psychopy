"""Tests for OpenGL state set by `psychopy.tools.gltools` and the window.
"""
import ctypes

import pytest

from psychopy import visual
import psychopy.tools.gltools as gt
import psychopy.tools.opengl as GL


@pytest.fixture(scope='module')
def win():
    win = visual.Window((128, 128), allowGUI=False, autoLog=False)
    yield win
    win.close()


def _getInteger(name):
    value = GL.GLint()
    GL.glGetIntegerv(name, ctypes.byref(value))
    return value.value


def _boundVAO():
    # same value as `GL_VERTEX_ARRAY_BINDING_APPLE`
    return _getInteger(GL.GL_VERTEX_ARRAY_BINDING)


@pytest.fixture
def vao(win):
    vertices = gt.createVBO([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    vao = gt.createVAO({GL.GL_VERTEX_ARRAY: vertices}, legacy=True)
    yield vao
    gt.deleteVAO(vao)
    gt.deleteVBO(vertices)


def test_useProgram(win):
    prog = win._shaders['stim3d_phong'][(0, False)]
    gt.useProgram(prog)
    assert _getInteger(GL.GL_CURRENT_PROGRAM) == prog
    gt.useProgram(None)
    assert _getInteger(GL.GL_CURRENT_PROGRAM) == 0


def test_drawVAO_unbind(win, vao):
    gt.drawVAO(vao, GL.GL_TRIANGLES)
    assert _boundVAO() == 0

    # left bound for drawing another VAO
    gt.drawVAO(vao, GL.GL_TRIANGLES, unbind=False)
    assert _boundVAO() == vao.name
    gt.drawVAO(vao, GL.GL_TRIANGLES)
    assert _boundVAO() == 0


@pytest.mark.parametrize('name, value', [
    ('never', GL.GL_NEVER), ('less', GL.GL_LESS), ('equal', GL.GL_EQUAL),
    ('lequal', GL.GL_LEQUAL), ('greater', GL.GL_GREATER),
    ('notequal', GL.GL_NOTEQUAL), ('gequal', GL.GL_GEQUAL),
    ('always', GL.GL_ALWAYS),
])
def test_depthFunc(win, name, value):
    old = win.depthFunc
    try:
        win.depthFunc = name
        assert win.depthFunc == name
        assert _getInteger(GL.GL_DEPTH_FUNC) == value
    finally:
        win.depthFunc = old


def test_depthFunc_invalid(win):
    with pytest.raises(KeyError):
        win.depthFunc = 'sometimes'
