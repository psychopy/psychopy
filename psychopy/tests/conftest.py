#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Configuration shared by the whole test suite."""

import functools

# reference to the unpatched `Window.__init__`, see `pytest_configure`
_origWindowInit = None


def pytest_configure(config):
    """Don't measure the frame rate of Windows opened by the test suite.

    Measuring costs additonal flips per `Window`, which dominates the runtime of 
    the visual tests on CI, and the result has no bearing on how stimuli are drawn.
    Tests which genuinely need a measured rate still call `getActualFrameRate()`
    themselves, and windows created with an explicit `checkTiming` value are
    left alone.

    This is done from `pytest_configure` rather than a fixture so that it also
    covers windows created while modules are imported, i.e. before any fixture
    has had a chance to run.

    """
    global _origWindowInit

    from psychopy.visual.window import Window

    _origWindowInit = Window.__init__

    # NB: `functools.wraps` is needed here, not just for tidiness -
    # `psychopy.tools.stimulustools.serialize` inspects the signature of
    # `Window.__init__` and refuses objects taking variable args, so the
    # wrapper has to report the signature of the function it wraps.
    @functools.wraps(_origWindowInit)
    def patchedInit(self, *args, **kwargs):
        kwargs.setdefault('checkTiming', False)
        return _origWindowInit(self, *args, **kwargs)

    Window.__init__ = patchedInit


def pytest_unconfigure(config):
    """Undo the patch applied by `pytest_configure`."""
    global _origWindowInit

    if _origWindowInit is None:
        return

    from psychopy.visual.window import Window

    Window.__init__ = _origWindowInit
    _origWindowInit = None
