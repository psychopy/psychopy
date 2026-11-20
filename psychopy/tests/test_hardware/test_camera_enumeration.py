#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Tests for finding cameras with PyAV when `ffpyplayer` isn't installed.

On Windows, FFmpeg only reports cameras and their formats in its log, so these
check that log is read correctly. None of them need a camera: the log text is
given to the parser directly, or the functions which capture it are swapped
for fakes.

"""

import builtins
import platform

import pytest

from psychopy.hardware import camera
from psychopy.hardware.camera import (
    CAMERA_LIB_PYAV, CAMERA_LIB_FFPYPLAYER, CAMERA_LIB_OPENCV,
    CAMERA_NULL_VALUE, CAMERA_UNKNOWN_VALUE)

# Option listing as FFmpeg 7 logs it for a webcam, with each mode repeated
# for the colour spaces it supports
OPTIONS_LOG = (
    'DirectShow video device options (from video devices)\n'
    ' Pin "Capture" (alternative pin name "0")\n'
    '  vcodec=mjpeg  min s=1920x1080 fps=30 max s=1920x1080 fps=30\n'
    '  vcodec=mjpeg  min s=1920x1080 fps=30 max s=1920x1080 fps=30 '
    '(pc, bt470bg/bt709/unknown, center)\n'
    '  vcodec=mjpeg  min s=640x480 fps=30 max s=640x480 fps=30\n'
    '  pixel_format=yuyv422  min s=1920x1080 fps=5 max s=1920x1080 fps=5\n'
    '  pixel_format=yuyv422  min s=640x480 fps=5 max s=640x480 fps=29.97\n'
)


class TestParseDShowModes:
    """Formats are read out of FFmpeg's DirectShow option listing."""

    def test_readsEachModeOnce(self):
        """Each mode is given once, at its largest size and frame rate, with
        the codec or pixel format it's opened with."""
        assert camera._parseDShowModes(OPTIONS_LOG) == [
            (CAMERA_NULL_VALUE, 'mjpeg', (1920, 1080), 30),
            (CAMERA_NULL_VALUE, 'mjpeg', (640, 480), 30),
            ('yuyv422', CAMERA_NULL_VALUE, (1920, 1080), 5),
            ('yuyv422', CAMERA_NULL_VALUE, (640, 480), 29.97),
        ]

    def test_wholeFrameRatesAreInts(self):
        """Whole frame rates are given as `int`, as Builder's frame rate
        param is an integer."""
        rates = [mode[3] for mode in camera._parseDShowModes(OPTIONS_LOG)]

        assert [type(rate) for rate in rates] == [int, int, int, float]

    def test_noModes(self):
        """Nothing is read from a log which lists no modes, e.g. when the
        camera couldn't be opened."""
        assert camera._parseDShowModes(
            'Could not enumerate video devices (or none found).\n') == []


@pytest.mark.skipif(
    platform.system() != 'Windows', reason="DirectShow is Windows only")
class TestWindowsCamerasWithoutFFPyPlayer:
    """Without `ffpyplayer`, PyAV finds cameras and their formats itself."""

    @pytest.fixture(autouse=True)
    def noFFPyPlayer(self, monkeypatch):
        """Make `ffpyplayer` look like it isn't installed, and give PyAV one
        camera to find."""
        realImport = builtins.__import__

        def fakeImport(name, *args, **kwargs):
            if name.startswith('ffpyplayer'):
                raise ImportError("No module named 'ffpyplayer'")
            return realImport(name, *args, **kwargs)

        monkeypatch.setattr(builtins, '__import__', fakeImport)
        monkeypatch.setattr(
            camera, '_getDShowDevicesPyAV', lambda: ["Fake Cam"])

    @pytest.mark.parametrize("cameraLib", [CAMERA_LIB_PYAV, CAMERA_LIB_OPENCV])
    def test_listsFormats(self, monkeypatch, cameraLib):
        """Each camera is listed with the formats FFmpeg reports for it, for
        any library other than `ffpyplayer` itself."""
        monkeypatch.setattr(
            camera, '_getDShowFormatsPyAV',
            lambda name: camera._parseDShowModes(OPTIONS_LOG))

        cameras = camera._getCameraInfoWindows(cameraLib)

        assert list(cameras) == ["Fake Cam"]
        assert [(cam.frameSize, cam.frameRate) for cam in cameras["Fake Cam"]] \
            == [((1920, 1080), 30), ((640, 480), 30), ((1920, 1080), 5),
                ((640, 480), 29.97)]
        assert all(cam.cameraLib == cameraLib for cam in cameras["Fake Cam"])

    def test_listsCameraWithoutFormats(self, monkeypatch):
        """A camera whose formats can't be found is still listed, leaving
        the format for FFmpeg to pick."""
        monkeypatch.setattr(camera, '_getDShowFormatsPyAV', lambda name: [])

        cameras = camera._getCameraInfoWindows(CAMERA_LIB_PYAV)

        assert len(cameras["Fake Cam"]) == 1
        assert cameras["Fake Cam"][0].codecFormat == CAMERA_UNKNOWN_VALUE

    def test_ffpyplayerStillRequiredForItsOwnLibrary(self):
        """Reading cameras with `ffpyplayer` still needs it installed."""
        with pytest.raises(ImportError):
            camera._getCameraInfoWindows(CAMERA_LIB_FFPYPLAYER)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
