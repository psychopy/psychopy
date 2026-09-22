"""Tests for `psychopy.hardware.camera`.

These need a camera to actually be attached to the system, so they skip
wherever one isn't found rather than failing. Run them on a machine with a
webcam plugged in to exercise the capture path for real.

"""
import numpy as np
import pytest

from psychopy import visual
from psychopy.hardware.camera import Camera, getCameras
from psychopy.tests.utils import RUNNING_IN_VM


def _getAttachedCameras():
    """Get the cameras attached to this system, if any.

    Enumeration reaches out to the OS and can raise if the capture backend
    isn't usable here, which for our purposes is the same as having no camera.

    Returns
    -------
    dict
        Mapping of camera name to the formats it supports, empty if none were
        found or if the system couldn't be queried.

    """
    try:
        return getCameras()
    except Exception:
        return {}


# Skip unless there's a camera to talk to. Checked at import time so collection
# reports this as skipped rather than opening a window and then bailing out.
_attachedCameras = _getAttachedCameras()

pytestmark = [
    pytest.mark.needs_camera,
    pytest.mark.skipif(
        RUNNING_IN_VM, reason="no camera hardware available in a VM/CI"),
    pytest.mark.skipif(
        not _attachedCameras, reason="no camera attached to this system"),
]


class TestCameraStream:
    """Present a live camera stream in an `ImageStim`."""
    def setup_method(self):
        self.win = visual.Window(
            size=(128, 128), units='pix', color='black', autoLog=False)
        self.cam = Camera(device=0, win=self.win, usageMode='cv')

    def teardown_method(self):
        # `close()` is a no-op on a camera which never opened, so this is safe
        # however far through `setup_method` and the test we got
        self.cam.close()
        self.win.close()

    def test_streamToImageStim(self):
        """A camera opened as an `ImageStim` image should deliver frames.

        Covers the path the `camera.py` demo takes: enumerate a camera, open
        it, hand it to an `ImageStim` and draw that every frame.

        """
        self.cam.open()

        # the camera should describe itself sensibly once open
        frameWidth, frameHeight = self.cam.frameSize
        assert frameWidth > 0 and frameHeight > 0, (
            "Camera reported a degenerate frame size {}.".format(
                self.cam.frameSize))
        assert self.cam.frameRate > 0, (
            "Camera reported a frame rate of {}.".format(self.cam.frameRate))

        camView = visual.ImageStim(
            self.win, image=self.cam, size=self.cam.frameSize, units='pix',
            autoLog=False)

        # draw the stream for a while, collecting whatever frames arrive
        grabbedFrames = []
        for _ in range(60):
            camView.draw()
            self.win.flip()
            grabbedFrames.extend(self.cam.getVideoFrames())

        assert grabbedFrames, (
            "Camera delivered no frames over 60 window flips.")

        # every frame should match the size the camera said it would give us
        for frame in grabbedFrames:
            assert frame.get_size() == (frameWidth, frameHeight), (
                "Got a {} frame from a camera reporting {}.".format(
                    frame.get_size(), self.cam.frameSize))

        # frames should carry a full plane of image data, not a short or empty
        # buffer
        lastFrame = np.frombuffer(
            bytes(grabbedFrames[-1].to_bytearray()[0]), dtype=np.uint8)
        assert lastFrame.size >= frameWidth * frameHeight * 3, (
            "Frame buffer holds {} bytes, too short for a {}x{} RGB "
            "image.".format(lastFrame.size, frameWidth, frameHeight))
