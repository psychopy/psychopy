#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for the movie tools in `psychopy.tools.movietools`.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import importlib
import os
import re
import shutil
import subprocess

import numpy as np
import pytest

from psychopy.tools.movietools import (
    FFPyPlayerMovieWriter,
    InvalidFrameSizeError,
    OpenCVMovieWriter,
    PyAVMovieWriter,
    addAudioToMovie,
    extractAudioFromMovie,
    _ffmpegOptsToArgs,
    _getFFMPEGExe)


# Frames are written at a size libx264 will accept as-is, i.e. both dimensions
# even, so that no writer has to pad or rescale them.
FRAME_SIZE = (64, 48)
FRAME_RATE = 30.0
N_FRAMES = 30  # a second of video, enough for the encoders to emit packets


def _libAvailable(libName):
    """Check whether an encoder library can be imported.

    Parameters
    ----------
    libName : str
        Name of the module to import, e.g. `'cv2'`.

    Returns
    -------
    bool
        `True` if importing the module worked.

    """
    try:
        importlib.import_module(libName)
    except Exception:
        return False

    return True


def _makeFrames(nFrames=N_FRAMES, frameSize=FRAME_SIZE, frameRate=FRAME_RATE):
    """Make frames to hand over to a writer.

    Each frame is a different picture, so that the encoders have something to
    encode rather than a run of identical frames which compress away to
    nothing.

    Parameters
    ----------
    nFrames : int
        Number of frames to make.
    frameSize : tuple
        Size `(w, h)` of the frames, in pixels.
    frameRate : float
        Rate the frames are spaced at, in frames per second.

    Returns
    -------
    list
        Frames as `(colorData, elapsed)` tuples, in the format a `MovieWriter`
        takes them, with `colorData` an RGB array.

    """
    frameWidth, frameHeight = frameSize

    frames = []
    for i in range(nFrames):
        colorData = np.empty((frameHeight, frameWidth, 3), dtype=np.uint8)
        colorData[:, :, 0] = np.linspace(
            0, 255, frameWidth, dtype=np.uint8)[np.newaxis, :]
        colorData[:, :, 1] = np.linspace(
            0, 255, frameHeight, dtype=np.uint8)[:, np.newaxis]
        colorData[:, :, 2] = (i * 255) // max(1, nFrames - 1)

        frames.append((colorData, i / frameRate))

    return frames


# Size in bytes a movie file must reach to count as holding encoded frames.
# A file which was opened and closed without a frame ever reaching it holds
# only the container's boxes, which comes to a few hundred bytes at most, while
# a single encoded frame of the size used here takes several thousand.
MIN_MOVIE_BYTES = 1024


def _assertIsMovieFile(filename):
    """Check that a file the writer produced looks like the movie it claims.

    Parameters
    ----------
    filename : str
        File the writer was pointed at.

    """
    assert os.path.isfile(filename), \
        "Writer did not create '{}'.".format(filename)

    fileSize = os.path.getsize(filename)
    assert fileSize > MIN_MOVIE_BYTES, \
        "'{}' is only {} bytes, too small to hold any encoded frames.".format(
            filename, fileSize)

    # every writer here muxes MP4, which starts with a file type box
    with open(filename, 'rb') as movieFile:
        header = movieFile.read(12)

    assert header[4:8] == b'ftyp', \
        "'{}' does not start with an MP4 file type box.".format(filename)


def _captureLog(monkeypatch, level):
    """Collect what the movietools module logs at one level rather than logging it.

    A test which provokes a message on purpose would otherwise leave it in the
    output of the whole run, where it reads as something having gone wrong.

    Parameters
    ----------
    monkeypatch : pytest.MonkeyPatch
        Patcher to make the replacement with, which undoes it after the test.
    level : str
        Name of the `psychopy.logging` function to collect from, e.g.
        `'warning'`.

    Returns
    -------
    list
        Messages logged at that level, appended to as the test runs.

    """
    import psychopy.tools.movietools as mt

    messages = []

    def collect(msg, *args, **kwargs):
        messages.append(msg)

    monkeypatch.setattr(mt.logging, level, collect)

    return messages


@pytest.fixture
def logErrors(monkeypatch):
    """Errors the movietools module logs while the test runs (`list`)."""
    return _captureLog(monkeypatch, 'error')


@pytest.fixture
def logWarnings(monkeypatch):
    """Warnings the movietools module logs while the test runs (`list`)."""
    return _captureLog(monkeypatch, 'warning')


# Tests for using MovieWriters with camera frames

class _FakeCameraFrame:
    """Stand-in for a frame in a capture library's own wrapper.

    A writer cannot encode this as it stands, so it only reaches the file if
    the writer puts it through the `frameConverter` it was given, which is what
    happens when the capture library and the encoder library differ.

    """
    def __init__(self, colorData):
        self.colorData = colorData


class _MovieWriterTests:
    """Tests every `MovieWriter` subclass should pass.

    Subclasses set `writerClass` to the writer under test and are skipped if
    the library it encodes with is missing.

    """
    writerClass = None

    def _makeWriter(self, tmp_path, **kwargs):
        """Make a writer pointed at a file in the test's temporary directory.
        """
        kwargs.setdefault('filename', str(tmp_path / 'test_movie.mp4'))
        kwargs.setdefault('frameSize', FRAME_SIZE)
        kwargs.setdefault('frameRate', FRAME_RATE)

        return self.writerClass(**kwargs)

    def test_writeFrames(self, tmp_path):
        """Frames handed to an open writer reach the file."""
        writer = self._makeWriter(tmp_path)

        assert not writer.isOpen
        writer.open()
        assert writer.isOpen

        frames = _makeFrames()
        writer.write(frames)

        assert writer.framesWritten == len(frames)

        writer.close()
        assert not writer.isOpen

        # the last frame was placed where it was captured, not counted off
        assert writer.lastPTS == pytest.approx(
            frames[-1][1], abs=1.0 / FRAME_RATE)

        _assertIsMovieFile(writer.filename)

    def test_writeFramesOneAtATime(self, tmp_path):
        """Frames may be handed over singly rather than as a list."""
        writer = self._makeWriter(tmp_path)
        writer.open()

        for frame in _makeFrames():
            writer.write(frame)

        writer.close()

        assert writer.framesWritten == N_FRAMES
        _assertIsMovieFile(writer.filename)

    def test_noErrorsLogged(self, tmp_path, logErrors):
        """Frames are not dropped with an error logged in their place.

        `write()` logs the errors it catches rather than raising them, so a
        writer which failed on every frame would still look like it had
        written them.

        """
        writer = self._makeWriter(tmp_path)
        writer.open()
        writer.write(_makeFrames())
        writer.close()

        assert not logErrors, \
            "Writer logged error(s): {}".format(logErrors)

    def test_frameConverter(self, tmp_path):
        """Frames in another library's wrapper go through the converter."""
        converted = []

        def frameConverter(colorData):
            converted.append(colorData)
            return colorData.colorData

        writer = self._makeWriter(tmp_path, frameConverter=frameConverter)
        writer.open()
        writer.write(
            [(_FakeCameraFrame(colorData), elapsed)
             for colorData, elapsed in _makeFrames()])
        writer.close()

        assert len(converted) == N_FRAMES
        _assertIsMovieFile(writer.filename)

    def test_writeWhileClosed(self, tmp_path):
        """Frames handed to a writer which is not open are dropped."""
        writer = self._makeWriter(tmp_path)

        assert writer.write(_makeFrames()) == 0
        assert writer.framesWritten == 0
        assert not os.path.exists(writer.filename)

        # closing a writer which was never opened does nothing
        writer.close()
        assert not writer.isOpen

    def test_reopenResetsCounts(self, tmp_path):
        """Opening a writer again starts its counts from zero."""
        writer = self._makeWriter(tmp_path)

        writer.open()
        writer.write(_makeFrames())
        writer.close()
        assert writer.framesWritten == N_FRAMES

        writer.open()
        assert writer.framesWritten == 0
        assert writer.bytesWritten == 0
        assert writer.lastPTS == 0.0
        writer.close()

    def test_openTwiceIsHarmless(self, tmp_path):
        """Opening a writer which is already open does nothing."""
        writer = self._makeWriter(tmp_path)

        writer.open()
        writer.write(_makeFrames())
        writer.open()  # should not restart the file or clear the counts

        assert writer.framesWritten == N_FRAMES

        writer.close()
        _assertIsMovieFile(writer.filename)

    def test_noFrameSize(self, tmp_path):
        """A writer cannot be made without a frame size.

        The container's frame size is fixed when the file is opened, so there
        is nothing sensible to fall back to; the writer says so rather than
        guessing a size the frames will not match. A camera reports `None` for
        its frame size until its stream is open, so this is what a writer
        opened too early is handed.

        """
        with pytest.raises(InvalidFrameSizeError):
            self._makeWriter(tmp_path, frameSize=None)

    @pytest.mark.parametrize('frameSize', [
        (0, 48),  # no frames fit in it
        (64, -1),
        64,  # not a pair
        (64,),
        (64, 48, 3),
        '64x48',  # not numbers
        ('a', 'b'),
    ])
    def test_badFrameSize(self, tmp_path, frameSize):
        """A frame size the writer cannot use is rejected as such.

        The size is reported by whatever is being recorded, so a writer used
        for something other than a camera may be handed anything at all; it
        should say which argument was wrong rather than failing later on with
        whatever the encoder makes of it.

        """
        with pytest.raises(InvalidFrameSizeError):
            self._makeWriter(tmp_path, frameSize=frameSize)

    def test_noFrameRate(self, tmp_path, logWarnings):
        """A camera which reports no frame rate falls back to 30 fps."""
        writer = self._makeWriter(tmp_path, frameRate=None)

        assert writer.frameRate == 30.0
        assert any('frame rate' in msg for msg in logWarnings), \
            "Falling back to 30 fps was not reported: {}".format(logWarnings)
        assert writer.frameSize == FRAME_SIZE
        assert writer.encoderLib == self.writerClass._encoderLib


@pytest.mark.skipif(
    not _libAvailable('ffpyplayer'), reason="`ffpyplayer` is not installed")
class TestFFPyPlayerMovieWriter(_MovieWriterTests):
    """Tests for the writer which encodes with FFPyPlayer."""
    writerClass = FFPyPlayerMovieWriter

    def test_timestampsIncrease(self, tmp_path):
        """Frames captured too close together still get their own timestamp.

        FFPyPlayer counts timestamps in ticks of the frame interval, and the
        muxer rejects two frames sharing one, so frames which land on the same
        tick are pushed onto the next.

        """
        writer = self._makeWriter(tmp_path)
        writer.open()

        # all captured within a single frame interval
        frames = [(colorData, 0.001 * i)
                  for i, (colorData, _) in enumerate(_makeFrames(10))]

        seenPTS = []
        for frame in frames:
            writer.write(frame)
            seenPTS.append(writer.lastPTS)

        writer.close()

        assert seenPTS == sorted(set(seenPTS)), \
            "Timestamps were not strictly increasing: {}".format(seenPTS)
        _assertIsMovieFile(writer.filename)

    def test_encoderOpts(self, tmp_path):
        """Encoder options are passed on to FFmpeg."""
        writer = self._makeWriter(
            tmp_path, encoderOpts={'crf': '30', 'preset': 'ultrafast'})

        assert writer.encoderOpts == {'crf': '30', 'preset': 'ultrafast'}

        writer.open()
        writer.write(_makeFrames())
        writer.close()

        _assertIsMovieFile(writer.filename)


@pytest.mark.skipif(
    not _libAvailable('av'), reason="`av` (PyAV) is not installed")
class TestPyAVMovieWriter(_MovieWriterTests):
    """Tests for the writer which encodes with PyAV."""
    writerClass = PyAVMovieWriter

    def test_bytesWritten(self, tmp_path):
        """PyAV reports how much of the file the encoder has produced.

        The encoder is tuned for zero latency here so that it emits a packet
        for every frame it is given. Left to itself it holds frames back for
        its lookahead, and a recording this short would reach the file only
        when the encoder is flushed on close, which is after the last byte
        count was taken.

        """
        writer = self._makeWriter(
            tmp_path,
            encoderOpts={'preset': 'ultrafast', 'tune': 'zerolatency'})
        writer.open()

        bytesOut = 0
        for frame in _makeFrames():
            bytesOut += writer.write(frame)

        writer.close()

        assert bytesOut > 0
        assert writer.bytesWritten == bytesOut
        # the file holds the container's boxes on top of the encoded frames
        assert writer.bytesWritten <= os.path.getsize(writer.filename)
        _assertIsMovieFile(writer.filename)

    def test_encoderOpts(self, tmp_path):
        """Encoder options are passed on to the stream."""
        writer = self._makeWriter(
            tmp_path, encoderOpts={'crf': 30, 'preset': 'ultrafast'})

        writer.open()
        # options reach the stream as strings, which is what FFmpeg wants
        assert writer._stream.options == {'crf': '30', 'preset': 'ultrafast'}
        writer.write(_makeFrames())
        writer.close()

        _assertIsMovieFile(writer.filename)


@pytest.mark.skipif(
    not _libAvailable('cv2'), reason="`cv2` (OpenCV) is not installed")
class TestOpenCVMovieWriter(_MovieWriterTests):
    """Tests for the writer which encodes with OpenCV."""
    writerClass = OpenCVMovieWriter

    def test_framesEncoded(self, tmp_path):
        """Every frame handed over reaches the file when the encoder keeps up.
        """
        writer = self._makeWriter(tmp_path)
        writer.open()
        writer.write(_makeFrames())
        writer.close()

        assert writer.framesEncoded == N_FRAMES
        assert writer.framesDropped == 0
        _assertIsMovieFile(writer.filename)

    def test_gapIsPadded(self, tmp_path):
        """A gap left by a camera running slow is filled by repeating frames.

        OpenCV writes frames at a fixed rate, so a recording only lines up with
        the time it was captured over if the gap is padded out.

        """
        writer = self._makeWriter(tmp_path)
        writer.open()

        # half a second of frames, then a half second gap, then more
        frames = _makeFrames(10)
        frames += [(colorData, elapsed + 0.5)
                   for colorData, elapsed in _makeFrames(10)]
        writer.write(frames)
        writer.close()

        assert writer.framesWritten == len(frames)
        # the gap covers the frame intervals which no frame was captured in
        assert writer.framesEncoded > len(frames)
        assert writer.framesEncoded == pytest.approx(
            int(round(frames[-1][1] * FRAME_RATE)) + 1, abs=1)
        _assertIsMovieFile(writer.filename)

    def test_framesTooCloseAreDropped(self, tmp_path):
        """Frames arriving faster than the file's rate can hold are dropped."""
        writer = self._makeWriter(tmp_path)
        writer.open()

        # ten frames captured within a single frame interval, which a file
        # written at a fixed rate has only one slot for
        writer.write(
            [(colorData, 0.001 * i)
             for i, (colorData, _) in enumerate(_makeFrames(10))])
        writer.close()

        assert writer.framesWritten == 10
        assert writer.framesEncoded == 1
        assert writer.framesDropped == 9
        _assertIsMovieFile(writer.filename)

    def test_unknownEncoderOpts(self, tmp_path, logWarnings):
        """Options OpenCV cannot express are ignored with a warning."""
        writer = self._makeWriter(
            tmp_path, encoderOpts={'fourcc': 'mp4v', 'crf': '30'})

        # the option OpenCV has no way to express is named in the warning
        assert len(logWarnings) == 1, \
            "Expected one warning, got: {}".format(logWarnings)
        assert "'crf'" in logWarnings[0]
        # the one it does understand is used rather than warned about
        assert 'fourcc' not in logWarnings[0]
        assert writer._fourcc == 'mp4v'

        writer.open()
        writer.write(_makeFrames())
        writer.close()

        _assertIsMovieFile(writer.filename)

    def test_frameSizeMismatchIsRescaled(self, tmp_path):
        """Frames which do not match the file's frame size are rescaled."""
        writer = self._makeWriter(tmp_path)
        writer.open()

        frameWidth, frameHeight = FRAME_SIZE
        writer.write(_makeFrames(frameSize=(frameWidth * 2, frameHeight * 2)))
        writer.close()

        assert writer.framesEncoded == N_FRAMES
        assert writer.framesDropped == 0
        _assertIsMovieFile(writer.filename)


# Tests for the audio/video functions which shell out to FFMPEG

def _ffmpegAvailable():
    """Check whether an FFMPEG executable can be found.

    Returns
    -------
    bool
        `True` if `movietools` can find something to run.

    """
    try:
        _getFFMPEGExe()
    except Exception:
        return False

    return True


FFMPEG_AVAILABLE = _ffmpegAvailable()

# Media the tests are run against, short enough to encode in a moment but long
# enough that every stream holds more than a single packet.
MEDIA_DURATION = 1.0  # seconds
MEDIA_SIZE = (64, 48)
MEDIA_RATE = 30

# Size in bytes an output file must reach to count as holding encoded data,
# for the same reason as `MIN_MOVIE_BYTES` above.
MIN_MEDIA_BYTES = 1024


def _runFFMPEG(args):
    """Run an FFMPEG command to make media for a test to work on.

    Parameters
    ----------
    args : list
        Arguments to pass to FFMPEG, after the ones which quiet it down.

    """
    cmd = [_getFFMPEGExe(), '-loglevel', 'error', '-nostdin', '-y'] + args

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        universal_newlines=True)

    assert proc.returncode == 0, \
        "Could not make test media with '{}':\n{}".format(
            ' '.join(cmd), proc.stderr)


# picks the stream type and codec out of a line FFMPEG prints about a file,
# e.g. "Stream #0:1[0x2](und): Audio: aac (LC) (mp4a / 0x6134706D), 44100 Hz"
_STREAM_LINE = re.compile(r'Stream #\d+:\d+.*?: (Video|Audio): (\w+)')


def _mediaStreams(filename):
    """Find what streams a media file holds, and what they are encoded with.

    FFMPEG itself is used to read the file rather than FFPROBE, since the copy
    of FFMPEG bundled with `imageio-ffmpeg` comes without it. Asked to read a
    file without being given anywhere to write one, FFMPEG describes the input
    and exits with an error, which is what is picked apart here.

    Parameters
    ----------
    filename : str
        File to look at.

    Returns
    -------
    dict
        Name of the codec each stream is encoded with, keyed by the type of
        the stream, i.e. `'video'` and/or `'audio'`.

    """
    assert os.path.isfile(filename), \
        "'{}' was not created.".format(filename)

    fileSize = os.path.getsize(filename)
    assert fileSize > MIN_MEDIA_BYTES, \
        "'{}' is only {} bytes, too small to hold any encoded data.".format(
            filename, fileSize)

    proc = subprocess.run(
        [_getFFMPEGExe(), '-hide_banner', '-nostdin', '-i', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
        universal_newlines=True)

    streams = {}
    for line in proc.stderr.splitlines():
        found = _STREAM_LINE.search(line)
        if found is not None:
            streamType, codecName = found.groups()
            streams.setdefault(streamType.lower(), codecName)

    assert streams, \
        "FFMPEG found no streams at all in '{}':\n{}".format(
            filename, proc.stderr)

    return streams


@pytest.fixture(scope='session')
def sourceMedia(tmp_path_factory):
    """Media the muxing tests work on, made once for the whole run (`dict`).

    Only the video stream is encoded with `mpeg4` and the audio with `aac`,
    both of which FFMPEG can encode without any external library, so the tests
    do not turn on how the copy of FFMPEG on this machine was built.

    """
    if not FFMPEG_AVAILABLE:
        pytest.skip("no FFMPEG executable found")

    mediaDir = tmp_path_factory.mktemp('movietools_media')

    videoSize = '{}x{}'.format(*MEDIA_SIZE)
    videoSource = 'testsrc=size={}:rate={}:duration={}'.format(
        videoSize, MEDIA_RATE, MEDIA_DURATION)
    audioSource = 'sine=frequency=440:duration={}'.format(MEDIA_DURATION)

    # a video with no audio track at all
    silentVideo = mediaDir / 'silent.mp4'
    _runFFMPEG(
        ['-f', 'lavfi', '-i', videoSource,
         '-c:v', 'mpeg4', '-pix_fmt', 'yuv420p', str(silentVideo)])

    # an audio file on its own
    audio = mediaDir / 'audio.wav'
    _runFFMPEG(['-f', 'lavfi', '-i', audioSource, str(audio)])

    # a video which already has an audio track
    soundVideo = mediaDir / 'sound.mp4'
    _runFFMPEG(
        ['-f', 'lavfi', '-i', videoSource, '-f', 'lavfi', '-i', audioSource,
         '-c:v', 'mpeg4', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-shortest',
         str(soundVideo)])

    return {
        'silentVideo': str(silentVideo),
        'soundVideo': str(soundVideo),
        'audio': str(audio)}


@pytest.fixture
def media(sourceMedia, tmp_path):
    """Copies of the source media for one test to work on (`dict`).

    A test may delete or overwrite what it is given, so each gets its own copy
    rather than the files every other test is run against.

    """
    copies = {}
    for name, filename in sourceMedia.items():
        copy = tmp_path / os.path.basename(filename)
        shutil.copyfile(filename, str(copy))
        copies[name] = str(copy)

    return copies


@pytest.fixture
def movieThreads(monkeypatch):
    """Threads `movietools` starts while the test runs (`list`).

    The functions which do their work in a thread do not hand it back, so it
    is caught here instead, letting a test wait for the work to finish rather
    than guessing how long it takes.

    """
    import psychopy.tools.movietools as mt

    threads = []
    makeThread = mt.threading.Thread

    def catchThread(*args, **kwargs):
        thread = makeThread(*args, **kwargs)
        threads.append(thread)
        return thread

    monkeypatch.setattr(mt.threading, 'Thread', catchThread)

    return threads


def _joinMovieThreads(movieThreads, timeout=60.0):
    """Wait for the threads a test caught to finish their work."""
    assert movieThreads, "No thread was started."

    for thread in movieThreads:
        thread.join(timeout)
        assert not thread.is_alive(), \
            "Thread did not finish within {} s.".format(timeout)


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="no FFMPEG executable found")
class TestExtractAudioFromMovie:
    """Tests for pulling the audio track out of a movie file."""

    def test_extractAudio(self, media, tmp_path):
        """The audio track of a movie is written out on its own."""
        audioFile = str(tmp_path / 'extracted.wav')

        extractAudioFromMovie(media['soundVideo'], audioFile)

        streams = _mediaStreams(audioFile)
        assert 'audio' in streams
        # the video stream is left behind rather than carried along
        assert 'video' not in streams
        # the movie it came from is untouched
        assert os.path.exists(media['soundVideo'])

    def test_extractAudioDropsVideoStream(self, media, tmp_path):
        """The video stream is left out even where it could be carried.

        A container which holds nothing but audio, such as WAV, drops the
        video whatever the command says, so a Matroska file is asked for here
        instead; it would hold both tracks if the video were not dropped on
        purpose.

        """
        audioFile = str(tmp_path / 'extracted.mkv')

        extractAudioFromMovie(media['soundVideo'], audioFile)

        assert 'video' not in _mediaStreams(audioFile)

    @pytest.mark.parametrize('extension, codecName', [
        ('.wav', 'pcm_s16le'),
        ('.aac', 'aac'),
    ])
    def test_extractAudioFormatFollowsExtension(
            self, media, tmp_path, extension, codecName):
        """The audio is encoded with whatever the output extension asks for.

        The track is transcoded rather than copied, so the caller picks the
        format by naming the file, which is how the function behaved when it
        was written with MoviePy.

        """
        audioFile = str(tmp_path / ('extracted' + extension))

        extractAudioFromMovie(media['soundVideo'], audioFile)

        assert _mediaStreams(audioFile)['audio'] == codecName

    def test_extractAudioOverwrites(self, media, tmp_path):
        """An audio file already at the output path is replaced."""
        audioFile = tmp_path / 'extracted.wav'
        audioFile.write_text('not an audio file')

        extractAudioFromMovie(media['soundVideo'], str(audioFile))

        assert _mediaStreams(str(audioFile))['audio'] == 'pcm_s16le'

    def test_extractAudioMissingVideo(self, tmp_path):
        """A movie file which is not there is reported as such.

        The file is checked here rather than left to FFMPEG so that the caller
        gets the usual error for a missing file instead of having to read it
        out of what FFMPEG printed.

        """
        with pytest.raises(FileNotFoundError):
            extractAudioFromMovie(
                str(tmp_path / 'no_such_movie.mp4'),
                str(tmp_path / 'extracted.wav'))

    def test_extractAudioNoAudioTrack(self, media, tmp_path):
        """A movie with no audio to extract fails rather than writing nothing.
        """
        with pytest.raises(RuntimeError):
            extractAudioFromMovie(
                media['silentVideo'], str(tmp_path / 'extracted.wav'))

    def test_extractAudioRemoveFiles(self, media, tmp_path):
        """The movie is deleted once its audio has been extracted."""
        audioFile = str(tmp_path / 'extracted.wav')

        extractAudioFromMovie(
            media['soundVideo'], audioFile, removeFiles=True)

        assert not os.path.exists(media['soundVideo'])
        assert 'audio' in _mediaStreams(audioFile)

    def test_extractAudioKeepsFilesWhenItFails(self, media, tmp_path):
        """A movie is not deleted when the audio could not be extracted.

        Deleting it would leave the recording with neither the audio nor the
        movie it was meant to come from.

        """
        with pytest.raises(RuntimeError):
            extractAudioFromMovie(
                media['silentVideo'],
                str(tmp_path / 'extracted.wav'),
                removeFiles=True)

        assert os.path.exists(media['silentVideo'])


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="no FFMPEG executable found")
class TestAddAudioToMovie:
    """Tests for muxing an audio track into a movie file."""

    def test_addAudio(self, media, tmp_path):
        """A movie and an audio file are merged into one movie."""
        outputFile = str(tmp_path / 'merged.mp4')

        addAudioToMovie(
            outputFile, media['silentVideo'], media['audio'],
            useThreads=False)

        streams = _mediaStreams(outputFile)
        assert 'video' in streams
        assert streams['audio'] == 'aac'
        # the files it was merged from are untouched
        assert os.path.exists(media['silentVideo'])
        assert os.path.exists(media['audio'])

    def test_addAudioThreaded(self, media, tmp_path, movieThreads):
        """The merge may be left to run in the background."""
        outputFile = str(tmp_path / 'merged.mp4')

        addAudioToMovie(
            outputFile, media['silentVideo'], media['audio'],
            useThreads=True)

        _joinMovieThreads(movieThreads)

        streams = _mediaStreams(outputFile)
        assert 'video' in streams
        assert streams['audio'] == 'aac'

    def test_addAudioCopiesVideoStream(self, media, tmp_path):
        """The video is carried over as it is rather than encoded again.

        Re-encoding it to attach an audio track would cost time and a
        generation of picture quality for nothing, so the stream is copied.

        """
        outputFile = str(tmp_path / 'merged.mp4')

        addAudioToMovie(
            outputFile, media['silentVideo'], media['audio'],
            useThreads=False)

        assert _mediaStreams(outputFile)['video'] == \
            _mediaStreams(media['silentVideo'])['video']

    def test_addAudioReplacesExistingTrack(self, media, tmp_path):
        """The audio given replaces the one the movie already had."""
        outputFile = str(tmp_path / 'merged.mkv')

        # FLAC is nothing like the AAC track the movie arrived with, so the
        # output can only hold it if the original track was dropped
        addAudioToMovie(
            outputFile, media['soundVideo'], media['audio'],
            useThreads=False, writerOpts={'c:a': 'flac'})

        assert _mediaStreams(outputFile)['audio'] == 'flac'

    def test_addAudioWriterOpts(self, media, tmp_path):
        """Options given by the caller are passed on to FFMPEG."""
        outputFile = str(tmp_path / 'merged.mkv')

        addAudioToMovie(
            outputFile, media['silentVideo'], media['audio'],
            useThreads=False, writerOpts={'c:a': 'flac'})

        # the default codec was overridden rather than added to
        assert _mediaStreams(outputFile)['audio'] == 'flac'

    def test_addAudioNoAudioFile(self, media, tmp_path):
        """Handing over no audio strips the track the movie had."""
        outputFile = str(tmp_path / 'silenced.mp4')

        addAudioToMovie(
            outputFile, media['soundVideo'], None, useThreads=False)

        streams = _mediaStreams(outputFile)
        assert 'video' in streams
        assert 'audio' not in streams

    def test_addAudioOverwrites(self, media, tmp_path):
        """A file already at the output path is replaced."""
        outputFile = tmp_path / 'merged.mp4'
        outputFile.write_text('not a movie file')

        addAudioToMovie(
            str(outputFile), media['silentVideo'], media['audio'],
            useThreads=False)

        assert 'audio' in _mediaStreams(str(outputFile))

    @pytest.mark.parametrize('missing', ['video', 'audio'])
    @pytest.mark.parametrize('useThreads', [True, False])
    def test_addAudioMissingInput(
            self, media, tmp_path, missing, useThreads):
        """An input file which is not there is reported as such.

        The inputs are checked before any thread is started, so the caller is
        told about a missing file whether the merge was to be threaded or not.

        """
        videoFile = media['silentVideo']
        audioFile = media['audio']

        if missing == 'video':
            videoFile = str(tmp_path / 'no_such_movie.mp4')
        else:
            audioFile = str(tmp_path / 'no_such_audio.wav')

        with pytest.raises(FileNotFoundError):
            addAudioToMovie(
                str(tmp_path / 'merged.mp4'), videoFile, audioFile,
                useThreads=useThreads)

    def test_addAudioFailureRaises(self, media, tmp_path):
        """A merge which FFMPEG could not do is raised to the caller."""
        with pytest.raises(RuntimeError):
            addAudioToMovie(
                str(tmp_path / 'merged.mp4'),
                media['silentVideo'],
                media['audio'],
                useThreads=False,
                writerOpts={'c:a': 'not_a_real_codec'})

    def test_addAudioFailureIsLoggedWhenThreaded(
            self, media, tmp_path, movieThreads, logErrors):
        """A threaded merge which failed logs an error rather than raising.

        Nothing is waiting on the thread for an exception to reach, so the
        only way the failure can be reported is through the log.

        """
        addAudioToMovie(
            str(tmp_path / 'merged.mp4'),
            media['silentVideo'],
            media['audio'],
            useThreads=True,
            writerOpts={'c:a': 'not_a_real_codec'})

        _joinMovieThreads(movieThreads)

        assert logErrors, "The failed merge was not reported anywhere."

    def test_addAudioRemoveFiles(self, media, tmp_path):
        """Both inputs are deleted once they have been merged."""
        outputFile = str(tmp_path / 'merged.mp4')

        addAudioToMovie(
            outputFile, media['silentVideo'], media['audio'],
            useThreads=False, removeFiles=True)

        assert not os.path.exists(media['silentVideo'])
        assert not os.path.exists(media['audio'])
        assert 'audio' in _mediaStreams(outputFile)

    def test_addAudioKeepsFilesWhenItFails(self, media, tmp_path):
        """Neither input is deleted when the merge failed.

        The merged file is all the recording would have left, so the tracks it
        was to be made from are kept when it was not.

        """
        with pytest.raises(RuntimeError):
            addAudioToMovie(
                str(tmp_path / 'merged.mp4'),
                media['silentVideo'],
                media['audio'],
                useThreads=False,
                removeFiles=True,
                writerOpts={'c:a': 'not_a_real_codec'})

        assert os.path.exists(media['silentVideo'])
        assert os.path.exists(media['audio'])


class TestFFMPEGOpts:
    """Tests for turning a mapping of options into FFMPEG arguments."""

    def test_valuesFollowTheirOption(self):
        """An option is named with a dash and followed by its value."""
        assert _ffmpegOptsToArgs({'c:v': 'copy', 'b:a': '192k'}) == \
            ['-c:v', 'copy', '-b:a', '192k']

    def test_numbersAreStrings(self):
        """Numbers are handed over as text, which is all argv can carry."""
        assert _ffmpegOptsToArgs({'crf': 23, 'filter_complex_threads': 1.0}) \
            == ['-crf', '23', '-filter_complex_threads', '1.0']

    def test_trueIsABareFlag(self):
        """An option which takes no value is given as `True`."""
        assert _ffmpegOptsToArgs({'shortest': True, 'an': True}) == \
            ['-shortest', '-an']

    @pytest.mark.parametrize('value', [False, None])
    def test_falseDropsTheOption(self, value):
        """An option switched off is left out rather than passed as a flag.

        This is how a caller turns off one of the defaults the muxing
        functions would otherwise pass.

        """
        assert _ffmpegOptsToArgs({'c:v': 'copy', 'shortest': value}) == \
            ['-c:v', 'copy']

    def test_noOpts(self):
        """Nothing to pass on gives nothing to splice into the command."""
        assert _ffmpegOptsToArgs({}) == []


@pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="no FFMPEG executable found")
class TestGetFFMPEGExe:
    """Tests for finding the FFMPEG executable to run."""

    def test_executableRuns(self):
        """What was found is something which can actually be run."""
        proc = subprocess.run(
            [_getFFMPEGExe(), '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            universal_newlines=True)

        assert proc.returncode == 0
        assert 'ffmpeg version' in proc.stdout

    def test_lookupIsCached(self, monkeypatch):
        """The executable is looked for once rather than on every call.

        Finding it means going out to the file system, which the functions
        calling it should not have to pay for each time they run a command.

        """
        import psychopy.tools.movietools as mt

        found = _getFFMPEGExe()

        def doNotLookAgain(name):
            raise AssertionError(
                "Looked for '{}' again after it had been found.".format(name))

        monkeypatch.setattr(shutil, 'which', doNotLookAgain)

        assert _getFFMPEGExe() == found
        assert mt._ffmpegExe == found
