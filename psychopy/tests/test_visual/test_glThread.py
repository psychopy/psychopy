#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests that stimuli free their OpenGL objects on the thread with the window's
OpenGL context, whichever thread the garbage collector frees them on.

The collector runs on whichever thread happens to be allocating when it's due,
which can be one of PsychoPy's own, such as a movie's decode thread. OpenGL
calls made there crash on macOS, and do nothing or the wrong thing elsewhere.

"""
import gc
import threading
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

import psychopy.tools.pygletgl as GL
from psychopy import visual
from .. import utils


@pytest.fixture(scope='module')
def win():
    """Window shared by all tests in this module."""
    thisWin = visual.Window(
        [128, 128], winType='pyglet', allowGUI=False, allowStencil=True,
        autoLog=False)
    yield thisWin
    thisWin.close()


@pytest.fixture
def glDeletes(monkeypatch):
    """Names of the threads each OpenGL object deletion is made on."""
    threads = []
    for name in ('glDeleteTextures', 'glDeleteLists', 'glDeleteBuffers',
                 'glDeleteFramebuffers'):
        def recording(*args, _delete=getattr(GL, name)):
            threads.append(threading.current_thread().name)
            return _delete(*args)

        monkeypatch.setattr(GL, name, recording)

    return threads


@contextmanager
def collectorOnOtherThread():
    """Hold the garbage collector back until the end of the block, and then
    run it on a thread of its own, as when it runs on a movie's decode thread.

    Anything let go of in the block is in a reference cycle with itself, so
    that only the collector frees it.

    """
    gc.collect()  # so there's nothing else for it to free there
    gc.disable()
    try:
        yield
        collector = threading.Thread(target=gc.collect, name='Collector')
        collector.start()
        collector.join()
    finally:
        gc.enable()


def _letGo(stim):
    """Leave `stim` for the garbage collector to free, once the caller has let
    go of it too."""
    stim._selfReference = stim


def _textureExists(textureId):
    return bool(GL.glIsTexture(textureId))


class TestWindowCallOnGLThread:
    """Tests for `Window._callOnGLThread`."""

    def test_calledStraightAwayOnGLThread(self, win):
        """On the window's own thread, the call is made straight away."""
        calls = []
        win._callOnGLThread(calls.append, 'now')

        assert calls == ['now']

    def test_otherThreadsWaitForFlip(self, win):
        """From any other thread, the call is made on the window's thread at
        the end of its next flip, once."""
        calls = []

        def call():
            calls.append(threading.current_thread().name)

        caller = threading.Thread(
            target=win._callOnGLThread, args=(call,), name='Caller')
        caller.start()
        caller.join()
        assert calls == []

        win.flip()
        assert calls == [threading.main_thread().name]

        win.flip()
        assert len(calls) == 1

    def test_closingMakesWaitingCalls(self):
        """Closing the window makes the calls still waiting, and any made
        from other threads after that are dropped, the context having gone."""
        thisWin = visual.Window(
            [64, 64], winType='pyglet', allowGUI=False, autoLog=False)
        calls = []

        for name in ('BeforeClose', 'AfterClose'):
            caller = threading.Thread(
                target=thisWin._callOnGLThread, args=(calls.append, name),
                name=name)
            caller.start()
            caller.join()
            if name == 'BeforeClose':
                thisWin.close()

        assert calls == ['BeforeClose']
        assert len(thisWin._glThreadCalls) == 0


class TestStimuliFreedOnGLThread:
    """Tests that stimuli freed by the garbage collector on another thread
    leave their OpenGL objects for the window to free at its next flip."""

    @pytest.mark.parametrize('makeStim', [
        lambda win: visual.GratingStim(win, tex='sin', mask='gauss'),
        lambda win: visual.ImageStim(
            win, image=np.random.default_rng(0).uniform(-1, 1, (16, 16))),
        lambda win: visual.ElementArrayStim(
            win, nElements=4, elementTex='sin', elementMask='gauss'),
    ], ids=['GratingStim', 'ImageStim', 'ElementArrayStim'])
    def test_texturesFreedOnFlip(self, win, glDeletes, makeStim):
        """Textures are deleted at the next flip, on the window's thread."""
        with collectorOnOtherThread():
            stim = makeStim(win)
            stim.draw()
            textureIds = [stim._texID.value, stim._maskID.value]
            _letGo(stim)
            del stim

        # freed on the collector's thread, but its textures left alone there
        assert 'Collector' not in glDeletes
        assert all(_textureExists(i) for i in textureIds)

        win.flip()
        assert set(glDeletes) == {threading.main_thread().name}
        assert not any(_textureExists(i) for i in textureIds)

    def test_apertureDisabledOnFlip(self, win):
        """An aperture freed on another thread turns the window's stencil test
        off at the next flip, on the window's thread, rather than there."""
        with collectorOnOtherThread():
            aperture = visual.Aperture(win, size=0.5)
            assert win.stencilTest
            _letGo(aperture)
            del aperture

        assert win.stencilTest
        assert GL.glIsEnabled(GL.GL_STENCIL_TEST)

        win.flip()
        assert not win.stencilTest
        assert not GL.glIsEnabled(GL.GL_STENCIL_TEST)

    def test_movieUnloadedOnFlip(self, win, glDeletes):
        """A movie freed on another thread is unloaded at the next flip, on the
        window's thread: its textures deleted, and its reader closed."""
        pytest.importorskip('av')
        moviePath = Path(utils.TESTS_DATA_PATH) / 'testMovie.mp4'

        with collectorOnOtherThread():
            mov = visual.MovieStim(
                win, str(moviePath), movieLib='pyav', noAudio=True,
                autoStart=False, size=(64, 64))
            mov.play()
            mov.draw()
            reader = mov._player
            textureIds = [mov._textureId.value] + list(
                mov._planeTextureIds or [])
            _letGo(mov)
            del mov

        assert 'Collector' not in glDeletes
        assert all(_textureExists(i) for i in textureIds)
        assert reader._decoderThread is not None  # still decoding

        win.flip()
        assert set(glDeletes) == {threading.main_thread().name}
        assert not any(_textureExists(i) for i in textureIds)
        assert reader._decoderThread is None  # stopped, and the reader closed
