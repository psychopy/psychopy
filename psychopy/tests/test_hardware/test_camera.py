"""Tests for `psychopy.hardware.camera`.

These need a camera to actually be attached to the system, so they skip
wherever one isn't found rather than failing. Run them on a machine with a
webcam plugged in to exercise the capture path for real.

"""
import os
import shutil
from pathlib import Path

import numpy as np
import pytest

from psychopy import core, session, visual
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


# How long each recording below runs for, in seconds. Long enough to get a
# useful number of frames without making the suite drag.
RECORD_SECS = 2.0


class TestCameraRecording:
    """Record from a camera and write the result to disk."""
    def setup_method(self):
        self.win = visual.Window(
            size=(128, 128), units='pix', color='black', autoLog=False)
        # `mic=False` keeps this to the video track; a camera in video mode
        # otherwise picks up the first microphone going and takes the
        # audio/video merge path, which isn't what's under test here
        self.cam = Camera(
            device=0, win=self.win, usageMode='video', mic=False)

    def teardown_method(self):
        self.cam.close()
        self.win.close()

    def _recordFor(self, duration=RECORD_SECS):
        """Record from the open camera for `duration` seconds."""
        self.cam.record()
        startTime = core.getTime()
        while core.getTime() - startTime < duration:
            self.cam.update()
            self.win.flip()
        self.cam.stop()

    def test_recordAndSave(self, tmp_path):
        """A recording should be written to disk as a readable video."""
        cv2 = pytest.importorskip(
            "cv2", reason="need OpenCV to read the recording back")

        self.cam.open()
        frameWidth, frameHeight = self.cam.frameSize

        self._recordFor()

        # the camera should agree that it recorded for about as long as we
        # asked it to, before anything is written out
        assert self.cam.recordingTime == pytest.approx(RECORD_SECS, abs=0.5), (
            "Recorded for {}s having asked for {}s.".format(
                self.cam.recordingTime, RECORD_SECS))

        outFile = str(tmp_path / "recording.mp4")
        savedFile = self.cam.save(outFile)

        assert savedFile == outFile, (
            "`save()` reported writing to `{}` rather than `{}`.".format(
                savedFile, outFile))
        assert self.cam.lastClip == outFile, (
            "`lastClip` is `{}` after saving to `{}`.".format(
                self.cam.lastClip, outFile))
        assert os.path.isfile(outFile), (
            "`save()` returned without writing `{}`.".format(outFile))
        assert os.path.getsize(outFile) > 0, (
            "`save()` wrote an empty file to `{}`.".format(outFile))

        # the file should be a video we can read back, holding the footage the
        # camera said it captured
        recording = cv2.VideoCapture(outFile)
        try:
            assert recording.isOpened(), (
                "Saved file `{}` could not be opened as a video.".format(
                    outFile))

            savedWidth = int(recording.get(cv2.CAP_PROP_FRAME_WIDTH))
            savedHeight = int(recording.get(cv2.CAP_PROP_FRAME_HEIGHT))
            assert (savedWidth, savedHeight) == (frameWidth, frameHeight), (
                "Saved a {}x{} video from a camera capturing at {}x{}.".format(
                    savedWidth, savedHeight, frameWidth, frameHeight))

            # Frame count is left loose on purpose. How many frames a camera
            # actually delivers in a couple of seconds varies with the load on
            # the machine, so this is only asserting we got a recording of
            # roughly the right length rather than a handful of stray frames.
            savedFrames = int(recording.get(cv2.CAP_PROP_FRAME_COUNT))
            expectedFrames = self.cam.frameRate * RECORD_SECS
            assert 0.25 * expectedFrames <= savedFrames <= 2 * expectedFrames, (
                "Saved {} frames, expected roughly {} for {}s at {} "
                "fps.".format(
                    savedFrames, expectedFrames, RECORD_SECS,
                    self.cam.frameRate))

            readOK, frame = recording.read()
            assert readOK, (
                "Could not read the first frame back from `{}`.".format(
                    outFile))
            assert frame.shape == (frameHeight, frameWidth, 3), (
                "First frame read back as {}, expected {}.".format(
                    frame.shape, (frameHeight, frameWidth, 3)))
        finally:
            recording.release()

    def test_saveWithoutRecordingWritesNothing(self, tmp_path):
        """Saving with nothing recorded shouldn't leave a file behind."""
        self.cam.open()

        outFile = str(tmp_path / "empty.mp4")
        self.cam.save(outFile)

        assert not os.path.exists(outFile), (
            "`save()` wrote `{}` despite nothing having been "
            "recorded.".format(outFile))


# Offset used for the scheduled start/stop tests, in seconds. Long enough to
# tell a deferred recording apart from an immediate one without the tests
# becoming sensitive to a frame or two of jitter.
SCHEDULE_DELAY = 1.0


class TestCameraScheduledRecording:
    """Schedule the start and stop of a recording with `when`.

    Note that `when` is an offset from the moment of the call, not an absolute
    clock time: both `record()` and `stop()` compute their target as
    `when + self._getTime()`. The docstrings on both describe it as an absolute
    time, which is not what either does.

    """
    def setup_method(self):
        self.win = visual.Window(
            size=(128, 128), units='pix', color='black', autoLog=False)
        self.cam = Camera(
            device=0, win=self.win, usageMode='video', mic=False)

    def teardown_method(self):
        self.cam.close()
        self.win.close()

    def _pumpFor(self, duration):
        """Poll the camera and flip the window for `duration` seconds."""
        startTime = core.getTime()
        while core.getTime() - startTime < duration:
            self.cam.update()
            self.win.flip()

    def test_recordWhenDefersStart(self, tmp_path):
        """`record(when=...)` should hold the recording off until then.

        Frames arriving before the requested start time belong to the stream
        but not to the recording, so they should be left out of the frame
        count, out of the recording clock, and out of the saved file.

        """
        cv2 = pytest.importorskip(
            "cv2", reason="need OpenCV to read the recording back")

        self.cam.open()

        self.cam.record(when=SCHEDULE_DELAY)

        # halfway to the requested start nothing should have been recorded yet
        self._pumpFor(SCHEDULE_DELAY * 0.5)
        assert self.cam.frameCount == 0, (
            "Recorded {} frames {}s into a recording deferred by {}s.".format(
                self.cam.frameCount, SCHEDULE_DELAY * 0.5, SCHEDULE_DELAY))

        # let it run past the requested start and capture for a known window
        captureSecs = 1.0
        self._pumpFor(SCHEDULE_DELAY * 0.5 + captureSecs)

        assert self.cam.frameCount > 0, (
            "Recorded nothing after passing a start deferred by {}s.".format(
                SCHEDULE_DELAY))

        # the recording clock should run from the deferred start, not from the
        # `record()` call, so it should read about `captureSecs` rather than
        # `SCHEDULE_DELAY + captureSecs`
        assert self.cam.recordingTime == pytest.approx(captureSecs, abs=0.5), (
            "Recording clock reads {}s, expected about {}s measured from the "
            "deferred start rather than from the `record()` call.".format(
                self.cam.recordingTime, captureSecs))

        self.cam.stop()

        outFile = str(tmp_path / "deferred.mp4")
        self.cam.save(outFile)

        # the file should hold only the footage from the deferred start
        # onwards, not the whole span since `record()` was called
        recording = cv2.VideoCapture(outFile)
        try:
            savedFrames = int(recording.get(cv2.CAP_PROP_FRAME_COUNT))
        finally:
            recording.release()

        expectedFrames = self.cam.frameRate * captureSecs
        assert savedFrames <= 2 * expectedFrames, (
            "Saved {} frames, about what {}s would give. A recording deferred "
            "by {}s should only hold the {}s after the start.".format(
                savedFrames, SCHEDULE_DELAY + captureSecs, SCHEDULE_DELAY,
                captureSecs))
        assert savedFrames >= 0.25 * expectedFrames, (
            "Saved only {} frames, expected roughly {} for the {}s captured "
            "after the deferred start.".format(
                savedFrames, expectedFrames, captureSecs))

    def test_stopWhenDefersStop(self, tmp_path):
        """`stop(when=...)` should keep recording until the scheduled time.

        The video track has to run on past the `stop()` call so that it ends
        alongside the audio track, which gets the same scheduled time as its
        `stopTime`.

        """
        cv2 = pytest.importorskip(
            "cv2", reason="need OpenCV to read the recording back")

        self.cam.open()

        self.cam.record()
        self._pumpFor(0.5)

        framesAtStopCall = self.cam.frameCount
        assert framesAtStopCall > 0, (
            "Recorded nothing before the scheduled stop was requested.")
        assert not self.cam.isStopping, (
            "Reported a pending stop before one was scheduled.")

        self.cam.stop(when=SCHEDULE_DELAY)

        # the recording carries on, but now with an end in sight
        assert self.cam.isStopping, (
            "No pending stop reported after `stop(when={})`.".format(
                SCHEDULE_DELAY))
        assert self.cam.isRecording, (
            "Recording ended when `stop(when={})` was called rather than at "
            "the scheduled time.".format(SCHEDULE_DELAY))

        # keep polling past the scheduled stop
        self._pumpFor(SCHEDULE_DELAY + 0.3)

        assert not self.cam.isStopping, (
            "Still reporting a pending stop after the scheduled time passed.")

        # the extra footage between the call and the scheduled stop should have
        # gone into the recording
        framesAfterStop = self.cam.frameCount - framesAtStopCall
        expectedExtra = self.cam.frameRate * SCHEDULE_DELAY
        assert framesAfterStop == pytest.approx(expectedExtra, rel=0.5), (
            "Recorded {} more frames after a stop deferred by {}s, expected "
            "roughly {}.".format(
                framesAfterStop, SCHEDULE_DELAY, expectedExtra))

        # and the recording should have closed itself off at the scheduled
        # time rather than run on
        assert not self.cam.isRecording, (
            "Still recording {}s after a stop deferred by {}s.".format(
                0.3, SCHEDULE_DELAY))

        framesAtDeadline = self.cam.frameCount
        self._pumpFor(0.3)
        assert self.cam.frameCount == framesAtDeadline, (
            "Frame count moved from {} to {} after the scheduled stop "
            "passed.".format(framesAtDeadline, self.cam.frameCount))

        outFile = str(tmp_path / "scheduled_stop.mp4")
        self.cam.save(outFile)

        assert os.path.isfile(outFile) and os.path.getsize(outFile) > 0, (
            "Nothing saved to `{}` after a scheduled stop.".format(outFile))

        # the saved file should hold the deferred footage too, not just what
        # had been captured when `stop()` was called
        recording = cv2.VideoCapture(outFile)
        try:
            savedFrames = int(recording.get(cv2.CAP_PROP_FRAME_COUNT))
        finally:
            recording.release()

        assert savedFrames > framesAtStopCall, (
            "Saved {} frames, no more than the {} captured by the time "
            "`stop()` was called; the deferred footage was dropped.".format(
                savedFrames, framesAtStopCall))

    def test_stopWithoutWhenStopsImmediately(self):
        """`stop()` with no `when` should end the recording there and then."""
        self.cam.open()

        self.cam.record()
        self._pumpFor(0.5)

        self.cam.stop()
        framesAtStopCall = self.cam.frameCount

        assert not self.cam.isRecording, (
            "Still recording after an immediate `stop()`.")
        # an immediate stop takes effect as it is called, so it never shows up
        # as pending
        assert not self.cam.isStopping, (
            "Reported a pending stop after an immediate `stop()`.")

        self._pumpFor(0.5)

        assert self.cam.frameCount == framesAtStopCall, (
            "Frame count moved from {} to {} after an immediate "
            "`stop()`.".format(framesAtStopCall, self.cam.frameCount))

    def test_scheduledStopClosesWithoutPolling(self):
        """A scheduled stop should still complete if frames stop arriving.

        The recording normally ends on the frame which crosses the stop time,
        so a camera nobody is polling would otherwise stay recording for ever.

        """
        self.cam.open()

        self.cam.record()
        self._pumpFor(0.5)

        self.cam.stop(when=SCHEDULE_DELAY)

        # let the scheduled time pass without polling the camera at all
        core.wait(SCHEDULE_DELAY + 0.2)
        self.cam.update()

        assert not self.cam.isRecording, (
            "Still recording after the scheduled stop passed unpolled.")


class TestSharedCameraDevice:
    """Two `Camera` objects streaming from the same physical device.

    A `Camera` is a client of a capture device rather than the device itself,
    so asking for the same camera twice gets two objects sharing one stream
    instead of two streams (which the hardware would refuse). Each client
    records and saves on its own schedule.

    """
    def setup_method(self):
        self.win = visual.Window(
            size=(128, 128), units='pix', color='black', autoLog=False)
        self.camA = Camera(
            device=0, win=self.win, usageMode='video', mic=False,
            name='sharedCamA')
        self.camB = Camera(
            device=0, win=self.win, usageMode='video', mic=False,
            name='sharedCamB')

    def teardown_method(self):
        # closing one client leaves the stream up for the other, so the order
        # here doesn't matter
        self.camA.close()
        self.camB.close()
        self.win.close()

    def _pumpFor(self, duration):
        """Poll both cameras and flip the window for `duration` seconds."""
        startTime = core.getTime()
        while core.getTime() - startTime < duration:
            self.camA.update()
            self.camB.update()
            self.win.flip()

    def test_sharesOneCaptureDevice(self):
        """Both cameras should be clients of a single capture device."""
        assert self.camA is not self.camB, (
            "Asking for the same camera twice gave back one object; this test "
            "needs two separate clients.")
        assert self.camA._capture is self.camB._capture, (
            "The two cameras hold different capture devices ({!r} and {!r}); "
            "they should share one.".format(
                self.camA._capture, self.camB._capture))

        self.camA.open()
        self.camB.open()

        # both should be registered to receive frames from the one device
        boundClients = self.camA._capture._cameraClients
        assert self.camA in boundClients and self.camB in boundClients, (
            "Both cameras should be bound to the shared device, got "
            "{}.".format(boundClients))

        # sharing a stream means sharing its format
        assert self.camA.frameSize == self.camB.frameSize, (
            "Cameras on one device report different frame sizes, {} and "
            "{}.".format(self.camA.frameSize, self.camB.frameSize))
        assert self.camA.frameRate == self.camB.frameRate, (
            "Cameras on one device report different frame rates, {} and "
            "{}.".format(self.camA.frameRate, self.camB.frameRate))

        # The real test of sharing: the same captured frames reach both. Frames
        # only reach a camera in video mode while it is recording, hence the
        # `record()` calls, and they are identified by capture time.
        self.camA.record()
        self.camB.record()

        seenByA, seenByB = set(), set()
        startTime = core.getTime()
        while core.getTime() - startTime < 1.0:
            self.camA.update()
            self.camB.update()
            self.win.flip()
            if self.camA.lastFrame is not None:
                seenByA.add(self.camA.lastFrame.absTime)
            if self.camB.lastFrame is not None:
                seenByB.add(self.camB.lastFrame.absTime)

        self.camA.stop()
        self.camB.stop()

        assert seenByA, "Neither camera saw any frames."
        assert seenByA == seenByB, (
            "The cameras saw different frames; {} of {} capture times were "
            "common to both. Frames from a shared device should reach every "
            "client.".format(
                len(seenByA & seenByB), len(seenByA | seenByB)))

    def test_overlappingRecordings(self, tmp_path):
        """Each client should record and save over its own window.

        The two recordings overlap: the second starts while the first is still
        running, and outlives it.

        """
        cv2 = pytest.importorskip(
            "cv2", reason="need OpenCV to read the recordings back")

        self.camA.open()
        self.camB.open()

        leadIn = 0.5      # A recording alone
        overlap = 0.7     # both recording
        tailOut = 0.5     # B recording alone

        self.camA.record()
        self._pumpFor(leadIn)

        # B joins while A is still going
        self.camB.record()
        self._pumpFor(overlap)

        assert self.camA.isRecording and self.camB.isRecording, (
            "Expected both cameras to be recording during the overlap, got "
            "A={} B={}.".format(self.camA.isRecording, self.camB.isRecording))
        assert self.camA.frameCount > 0 and self.camB.frameCount > 0, (
            "Expected both cameras to have frames during the overlap, got "
            "A={} B={}.".format(self.camA.frameCount, self.camB.frameCount))

        # A finishes first; B should carry on regardless
        self.camA.stop()
        framesWhenAStopped = self.camB.frameCount

        assert not self.camA.isRecording, "A still recording after `stop()`."
        assert self.camB.isRecording, (
            "B stopped recording when A did; clients of a shared device "
            "should record independently.")

        self._pumpFor(tailOut)
        self.camB.stop()

        assert self.camB.frameCount > framesWhenAStopped, (
            "B captured nothing after A stopped, frame count stuck at "
            "{}.".format(framesWhenAStopped))

        # each client writes its own file
        fileA = str(tmp_path / "clientA.mp4")
        fileB = str(tmp_path / "clientB.mp4")
        self.camA.save(fileA)
        self.camB.save(fileB)

        for label, path, recordedSecs in (
                ('A', fileA, leadIn + overlap),
                ('B', fileB, overlap + tailOut)):
            assert os.path.isfile(path) and os.path.getsize(path) > 0, (
                "Client {} saved nothing to `{}`.".format(label, path))

            recording = cv2.VideoCapture(path)
            try:
                assert recording.isOpened(), (
                    "Client {}'s recording `{}` could not be opened as a "
                    "video.".format(label, path))

                savedFrames = int(recording.get(cv2.CAP_PROP_FRAME_COUNT))
                savedSize = (int(recording.get(cv2.CAP_PROP_FRAME_WIDTH)),
                             int(recording.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            finally:
                recording.release()

            assert savedSize == tuple(self.camA.frameSize), (
                "Client {} saved a {} video from a {} stream.".format(
                    label, savedSize, self.camA.frameSize))

            # each file should cover that client's own recording window, not
            # the whole span the pair were running over
            expectedFrames = self.camA.frameRate * recordedSecs
            assert savedFrames == pytest.approx(expectedFrames, rel=0.5), (
                "Client {} saved {} frames, expected roughly {} for its {}s "
                "recording.".format(
                    label, savedFrames, expectedFrames, recordedSecs))


# Folder holding the Builder experiments run by the tests below
BUILDER_DIR = Path(__file__).parent / "builder"


class TestBuilderCamLiveView:
    """Compile and run a Builder experiment with a live camera view.

    `builderCamLiveViewTest.psyexp` has a single Routine which draws a Camera
    Component into an Image Component for 10s, recording from the camera
    between 1s and 9s. Running it through a `Session` takes the same path as
    running it from Builder: the experiment is compiled to a script, which is
    imported and has its `run()` called.

    """
    # when the Camera Component starts and how long it runs for, in seconds, as
    # set in the experiment
    CAM_START = 1.0
    CAM_DURATION = 8.0

    def setup_method(self):
        # the experiment asks for a full screen window, so give the `Session`
        # a small one of its own to run in instead
        self.win = visual.Window(
            [128, 128], pos=[50, 50], allowGUI=False, autoLog=False)

    def teardown_method(self):
        self.win.close()

    def test_compileAndRun(self, tmp_path):
        """The experiment should compile, run, and save a camera recording."""
        cv2 = pytest.importorskip(
            "cv2", reason="need OpenCV to read the recording back")

        # Work from a copy, so the compiled script and the data and recordings
        # the experiment writes all land in the temp folder rather than in the
        # source tree.
        expFile = tmp_path / "builderCamLiveViewTest.psyexp"
        shutil.copy(str(BUILDER_DIR / expFile.name), str(expFile))

        sess = session.Session(root=tmp_path, win=self.win)
        sess.addExperiment(expFile.name, key="camLiveView")

        scriptFile = expFile.with_suffix(".py")
        assert scriptFile.is_file(), (
            "Adding `{}` to a Session didn't compile it to `{}`.".format(
                expFile.name, scriptFile.name))

        # the Session takes expInfo straight from the experiment, so this runs
        # without showing the info dialog
        sess.runExperiment("camLiveView")

        # the Camera Component should have started and stopped when the
        # experiment says it should
        thisExp = sess.runs[-1]
        trialData = thisExp.entries[0]
        assert trialData['cam.started'] == pytest.approx(
            self.CAM_START, abs=0.1), (
            "Camera started at {}s, expected {}s.".format(
                trialData['cam.started'], self.CAM_START))
        camRanFor = trialData['cam.stopped'] - trialData['cam.started']
        assert camRanFor == pytest.approx(self.CAM_DURATION, abs=0.1), (
            "Camera ran for {}s, expected {}s.".format(
                camRanFor, self.CAM_DURATION))

        # the recording should have been saved to the file the data points to,
        # in the folder the experiment keeps recordings from `cam` in
        clipFile = Path(trialData['cam.clip'])
        camRecFolder = Path(thisExp.dataFileName + '_cam_recorded')
        assert clipFile.parent == camRecFolder, (
            "Recording saved to `{}`, expected it in `{}`.".format(
                clipFile, camRecFolder))
        assert clipFile.is_file() and clipFile.stat().st_size > 0, (
            "No recording saved to `{}`.".format(clipFile))

        # and it should be a video we can read back, running for about as long
        # as the Camera Component did
        recording = cv2.VideoCapture(str(clipFile))
        try:
            assert recording.isOpened(), (
                "Recording `{}` could not be opened as a video.".format(
                    clipFile))
            savedFrames = int(recording.get(cv2.CAP_PROP_FRAME_COUNT))
            savedFPS = recording.get(cv2.CAP_PROP_FPS)
            readOK, _ = recording.read()
        finally:
            recording.release()

        assert readOK, (
            "Could not read the first frame back from `{}`.".format(clipFile))

        # Loose for the same reason as in `test_recordAndSave`: how many frames
        # arrive over the recording varies with the load on the machine.
        assert savedFPS > 0, (
            "Recording `{}` reports a frame rate of {}.".format(
                clipFile, savedFPS))
        savedSecs = savedFrames / savedFPS
        assert 0.25 * self.CAM_DURATION <= savedSecs <= 2 * self.CAM_DURATION, (
            "Recording holds {}s of video ({} frames at {} fps), expected "
            "roughly {}s.".format(
                savedSecs, savedFrames, savedFPS, self.CAM_DURATION))
