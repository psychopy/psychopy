#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `psychopy.visual.MovieStim` video decoding and playback.

These tests run against every decoder backend which is importable in the
current environment, so that the backends stay behaviourally interchangeable.

Audio is disabled throughout. These tests cover the video side of `MovieStim`,
and extracting an audio track needs a working output device which test machines
often lack.

"""
import math
import threading
import time
import weakref
from pathlib import Path
from contextlib import contextmanager

import numpy as np
import pytest

from psychopy import visual, prefs, core, logging
import psychopy.visual.movies as movies
from psychopy.visual.movies import MovieFileReader, _frameSampleOffset
from .. import utils


# --------------------------------------------------------------------------
# Test fixtures and helpers
#

MOVIE_PATH = Path(utils.TESTS_DATA_PATH) / 'testMovie.mp4'


def _readMovieProperties(filename):
    """Read the properties of a movie file using `PyAV`.

    Reading these from the file rather than hard-coding them keeps the
    expectations below correct if the test movie is ever replaced, and means
    the values each decoder backend reports are checked against something
    derived independently of `MovieStim`.

    Parameters
    ----------
    filename : str or Path
        Movie file to inspect.

    Returns
    -------
    tuple
        Frame size as `(w, h)` in pixels, frame rate in frames per second, and
        duration in seconds.

    """
    import av

    with av.open(str(filename)) as container:
        videoStream = container.streams.video[0]

        width = videoStream.codec_context.width
        height = videoStream.codec_context.height

        # `average_rate` is a `Fraction`, and some containers don't carry one
        frameRate = float(videoStream.average_rate or videoStream.guessed_rate)
        duration = float(videoStream.duration * videoStream.time_base)

    return (width, height), frameRate, duration


try:
    MOVIE_SIZE, MOVIE_FPS, MOVIE_DURATION = _readMovieProperties(MOVIE_PATH)
except Exception as err:
    # Placeholders so the module can still be imported, letting the tests skip
    # with a reason instead of failing to collect. `PyAV` is a hard dependency
    # of PsychoPy, so in practice this only happens if the movie is missing.
    MOVIE_SIZE, MOVIE_FPS, MOVIE_DURATION = (0, 0), 1.0, 0.0
    MOVIE_PROPERTIES_ERROR = '{}: {}'.format(type(err).__name__, err)
else:
    MOVIE_PROPERTIES_ERROR = None

MOVIE_FRAME_INTERVAL = 1.0 / MOVIE_FPS
MOVIE_FRAME_COUNT = int(MOVIE_DURATION * MOVIE_FPS)

# Backends disagree about duration by around a frame: `opencv` derives it from
# the frame count and frame rate, where the others read it from the container.
DURATION_TOL = 2.0 * MOVIE_FRAME_INTERVAL

# Two sample points used for frame comparisons, a third and two thirds of the
# way through and aligned to the start of a frame. `MovieStim` advances its
# clock by the elapsed wall time on every update, so a seek lands slightly past
# the timestamp asked for. Starting at a frame boundary leaves a whole frame
# interval of headroom for that drift, which keeps the comparisons below
# reproducible on a loaded machine.
SAMPLE_EARLY = (MOVIE_FRAME_COUNT // 3) * MOVIE_FRAME_INTERVAL
SAMPLE_LATE = (2 * MOVIE_FRAME_COUNT // 3) * MOVIE_FRAME_INTERVAL


# A second, different movie used to check that two can play at once. It is
# shipped with PsychoPy rather than living in the test data folder.
SECOND_MOVIE_PATH = Path(prefs.paths['assets']) / 'default.mp4'

needsSecondMovie = pytest.mark.skipif(
    not SECOND_MOVIE_PATH.is_file(),
    reason='second movie not found at {}'.format(SECOND_MOVIE_PATH))


def _availableBackends():
    """Get the decoder backends which can actually be used here.

    Returns
    -------
    list
        Names of backends whose underlying library is importable.

    """
    found = []
    for movieLib, moduleName in (
            # ('ffpyplayer', 'ffpyplayer'),
            # ('vlc', 'vlc'),
            ('pyav', 'av'),
            ('opencv', 'cv2')):
        try:
            __import__(moduleName)
        except Exception:
            # Raises rather than failing to import when it cannot
            # find a library to bind to, so this cannot just catch
            # `ImportError`
            continue
        found.append(movieLib)

    return found


BACKENDS = _availableBackends()

# run every test in this module once per available backend
pytestmark = [
    pytest.mark.skipif(not BACKENDS, reason='no movie decoder libraries found'),
    pytest.mark.skipif(
        MOVIE_PROPERTIES_ERROR is not None,
        reason='could not read properties of {} ({})'.format(
            MOVIE_PATH, MOVIE_PROPERTIES_ERROR)),
    pytest.mark.parametrize('movieLib', BACKENDS)]


@pytest.fixture(scope='module')
def win():
    """Window shared by all tests in this module."""
    thisWin = visual.Window(
        [128, 128], winType='pyglet', allowGUI=False, autoLog=False)
    yield thisWin
    thisWin.close()


@contextmanager
def movieStim(win, movieLib, filename=MOVIE_PATH, **kwargs):
    """Create a `MovieStim` and guarantee it is unloaded afterwards.

    Unloading matters here since a loaded movie holds an open file handle (and,
    for `ffpyplayer`, a decoding thread) which would otherwise leak between
    tests.

    """
    kwargs.setdefault('noAudio', True)
    kwargs.setdefault('autoStart', False)
    kwargs.setdefault('size', (128, 128))

    mov = visual.MovieStim(win, str(filename), movieLib=movieLib, **kwargs)
    try:
        yield mov
    finally:
        mov.unload()


def _frameBytesExpected(mov):
    """Bytes of pixel data `mov._recentFrame` should hold at least: the whole
    RGBA frame, or the luma plane of a frame uploaded as YUV."""
    width, height = mov._recentFrameSize
    if isinstance(mov._recentFrameImage, movies._YUVFrameAdapter):
        return width * height

    return width * height * 4


def _drawFrames(win, mov, count=3, interval=0.0):
    """Draw the movie `count` times, flipping the window between each."""
    for _ in range(count):
        mov.draw()
        win.flip()
        if interval:
            time.sleep(interval)


def _drawUntilSeekResolves(win, mov, maxFrames=200):
    """Draw until the movie has caught up with an outstanding seek.

    This is how a drawing loop is expected to use `isSeeking`: keep drawing,
    and the movie catches up over the next few frames rather than the seek
    stalling the loop. How many frames that takes is backend dependent, so
    tests poll rather than assuming a particular number.

    Returns
    -------
    int
        Number of frames drawn before the seek resolved.

    """
    drawn = 0
    while mov.isSeeking and drawn < maxFrames:
        mov.draw()
        win.flip()
        drawn += 1

    return drawn


def _frameAt(mov, timestamp):
    """Seek to `timestamp` and return the frame decoded there as an array.

    `seek()` refreshes the video frame itself, so nothing is drawn here. Drawing
    in between would advance the movie clock by the elapsed wall time and make
    which frame gets decoded depend on timing. The movie is deliberately left
    playing: pausing would stop the `ffpyplayer` decoder, which then returns no
    new frames at all.

    """
    mov.seek(timestamp)

    return np.asarray(mov._recentFrame).copy()


def _captureBackBuffer(win):
    """Grab the window's back buffer as an RGB array."""
    frame = np.asarray(win.getMovieFrame(buffer='back')).astype(int)
    win.movieFrames = []  # don't let captured frames pile up on the window

    return frame


def _drawToBackBuffer(win, *stims):
    """Draw stimuli onto a freshly cleared window and capture the result.

    Returns
    -------
    tuple
        The captured frame, and the background it was drawn over.

    """
    win.flip()  # clear the back buffer, leaving only the background
    background = _captureBackBuffer(win)

    for stim in stims:
        stim.draw()

    drawn = _captureBackBuffer(win)
    win.flip()

    return drawn, background


def _drawnRegion(win, *stims, **kwargs):
    """Draw stimuli and work out which pixels of the window they changed.

    Comparing against the cleared window, rather than looking for pixels of a
    particular colour, keeps this independent of both the window background and
    whatever the movie happens to contain.

    Parameters
    ----------
    win : `~psychopy.visual.Window`
        Window to draw to.
    stims
        Stimuli to draw, in the order they should be drawn.
    threshold : int
        How far a pixel must move, summed across RGB, to count as covered.

    Returns
    -------
    tuple
        Boolean mask of the pixels the stimuli changed, and the mean absolute
        difference from the background over the whole window.

    """
    threshold = kwargs.pop('threshold', 12)

    drawn, background = _drawToBackBuffer(win, *stims)
    difference = np.abs(drawn - background)

    return difference.sum(axis=2) > threshold, difference.mean()


def _boundingBox(mask):
    """Get the bounding box `(x, y, w, h)` of the set pixels in a mask.

    Returns `None` if nothing is set.

    """
    if not mask.any():
        return None

    rows = np.where(np.any(mask, axis=1))[0]
    cols = np.where(np.any(mask, axis=0))[0]

    return (int(cols[0]), int(rows[0]),
            int(cols[-1] - cols[0] + 1), int(rows[-1] - rows[0] + 1))


def _crop(frame, box):
    """Cut the region `(x, y, w, h)` out of a captured frame."""
    x, y, width, height = box

    return frame[y:y + height, x:x + width]


def _drawnSize(win, mov):
    """Get the on-screen size `(w, h)` in pixels of the drawn movie."""
    box = _boundingBox(_drawnRegion(win, mov)[0])

    return (0, 0) if box is None else (box[2], box[3])


# --------------------------------------------------------------------------
# Decoding
#

class TestMovieStimDecoding:
    """Tests for opening movie files and decoding frames from them."""

    def test_readerClassForBackend(self, movieLib):
        """Creating a `MovieFileReader` gives the reader of the backend asked
        for, whose own class can't be asked for another."""
        reader = MovieFileReader(str(MOVIE_PATH), decoderLib=movieLib)
        readerClass = type(reader)
        assert readerClass is not MovieFileReader
        assert isinstance(reader, MovieFileReader)
        assert reader.decoderLib == movieLib

        assert type(readerClass(str(MOVIE_PATH))) is readerClass

        otherLib = next(
            lib for lib in movies.SUPPORTED_VIDEO_LIBS if lib != movieLib)
        with pytest.raises(ValueError):
            readerClass(str(MOVIE_PATH), decoderLib=otherLib)

        with pytest.raises(ValueError):
            MovieFileReader(str(MOVIE_PATH), decoderLib='nonsense')

    def test_metadata(self, win, movieLib):
        """Movie metadata is reported correctly and agrees across backends."""
        with movieStim(win, movieLib) as mov:
            assert mov.frameSize == MOVIE_SIZE
            assert mov.videoSize == MOVIE_SIZE
            assert mov.fps == pytest.approx(MOVIE_FPS, abs=0.01)
            assert mov.getFPS() == pytest.approx(MOVIE_FPS, abs=0.01)
            assert mov.duration == pytest.approx(
                MOVIE_DURATION, abs=DURATION_TOL)

    def test_filename(self, win, movieLib):
        """The loaded movie reports the file it was created from."""
        with movieStim(win, movieLib) as mov:
            assert Path(mov.filename) == MOVIE_PATH

    def test_decodesFrameOnLoad(self, win, movieLib):
        """A frame is decoded when the movie is loaded, before playback."""
        with movieStim(win, movieLib) as mov:
            frame = np.asarray(mov._recentFrame)
            # four bytes per pixel for RGBA, or the luma plane of YUV, at the
            # size the frame came out at (see `TestMovieStimDownscaling`)
            assert frame.size >= _frameBytesExpected(mov)
            assert frame.dtype == np.uint8
            # a real frame, not a blank buffer
            assert frame.std() > 1.0

    def test_decodesDifferentFramesOverTime(self, win, movieLib):
        """Distinct positions in the movie decode to distinct frames."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            early = _frameAt(mov, SAMPLE_EARLY)
            late = _frameAt(mov, SAMPLE_LATE)

            assert early.std() > 1.0
            assert late.std() > 1.0
            assert not np.array_equal(early, late)

    def test_decodingIsDeterministic(self, win, movieLib):
        """Seeking back to a timestamp decodes the same frame again."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            first = _frameAt(mov, SAMPLE_EARLY)
            _frameAt(mov, SAMPLE_LATE)  # move away
            second = _frameAt(mov, SAMPLE_EARLY)  # and back again

            assert np.array_equal(first, second)

    def test_drawRendersToWindow(self, win, movieLib):
        """Drawing the movie puts image data into the window's back buffer."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.seek(2.0)
            _drawFrames(win, mov)

            mov.draw()  # capture the back buffer before it is cleared by flip
            rendered = np.asarray(win.getMovieFrame(buffer='back'))
            win.movieFrames = []  # don't accumulate frames on the window
            win.flip()

            assert rendered.std() > 1.0  # something other than a blank window

    def test_drawScalesToRequestedSize(self, win, movieLib):
        """The movie covers the area on-screen that `size` asks for."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.seek(SAMPLE_EARLY)

            # sizes are kept well inside the window so nothing is clipped
            for size in ((40, 24), (80, 48), (100, 60)):
                mov.size = size

                assert _drawnSize(win, mov) == pytest.approx(size, abs=1)

    def test_drawRotates(self, win, movieLib):
        """Rotating the movie rotates the region it covers on-screen."""
        width, height = 80, 40

        with movieStim(win, movieLib, size=(width, height)) as mov:
            mov.play()
            mov.seek(SAMPLE_EARLY)

            mov.ori = 0
            assert _drawnSize(win, mov) == pytest.approx((width, height), abs=1)

            mov.ori = 90  # a quarter turn swaps the extents
            assert _drawnSize(win, mov) == pytest.approx((height, width), abs=1)

            mov.ori = 180  # a half turn is the same way round again
            assert _drawnSize(win, mov) == pytest.approx((width, height), abs=1)

            # part way round, both extents grow to the rotated diagonal. This
            # separates a real rotation from merely swapping width and height.
            mov.ori = 45
            diagonal = (width + height) / np.sqrt(2.0)
            assert _drawnSize(win, mov) == pytest.approx(
                (diagonal, diagonal), abs=2)

    def test_drawAppliesOpacity(self, win, movieLib):
        """Lowering opacity blends the movie further into the background."""
        with movieStim(win, movieLib, size=(80, 40)) as mov:
            mov.play()
            mov.seek(SAMPLE_EARLY)

            differences = []
            for opacity in (1.0, 0.75, 0.5, 0.25):
                mov.opacity = opacity
                _, difference = _drawnRegion(win, mov)
                differences.append(difference)

            # every step towards transparent leaves the window closer to the
            # way it looked before the movie was drawn over it
            assert all(
                nearer > further
                for nearer, further in zip(differences, differences[1:]))

            mov.opacity = 0.0  # fully transparent draws nothing at all
            mask, difference = _drawnRegion(win, mov)

            assert not mask.any()
            assert difference == pytest.approx(0.0, abs=1e-6)

    @needsSecondMovie
    def test_twoMoviesPlaySideBySide(self, win, movieLib):
        """Two different movies play at once, side by side on one window."""
        size, offset = (50, 38), 30

        with movieStim(win, movieLib, size=size, pos=(-offset, 0)) as left, \
                movieStim(win, movieLib, filename=SECOND_MOVIE_PATH,
                          size=size, pos=(offset, 0)) as right:
            left.play()
            right.play()

            assert left.isPlaying
            assert right.isPlaying

            leftMask, _ = _drawnRegion(win, left)
            rightMask, _ = _drawnRegion(win, right)
            leftBox, rightBox = _boundingBox(leftMask), _boundingBox(rightMask)

            # each is drawn at its own size, in its own half of the window,
            # without straying into the other's
            assert leftBox[2:] == pytest.approx(size, abs=1)
            assert rightBox[2:] == pytest.approx(size, abs=1)
            assert leftBox[0] < rightBox[0]
            assert not (leftMask & rightMask).any()

            # drawing both covers the span of the two together
            bothMask, _ = _drawnRegion(win, left, right)
            bothBox = _boundingBox(bothMask)
            assert bothBox[0] == pytest.approx(leftBox[0], abs=1)
            assert bothBox[0] + bothBox[2] == pytest.approx(
                rightBox[0] + rightBox[2], abs=1)

            # both keep decoding new frames while sharing the window
            before, _ = _drawToBackBuffer(win, left, right)
            startLeft, startRight = left.movieTime, right.movieTime

            deadline = time.time() + 0.4
            while time.time() < deadline:
                left.draw()
                right.draw()
                win.flip()

            after, _ = _drawToBackBuffer(win, left, right)

            assert left.movieTime > startLeft
            assert right.movieTime > startRight
            assert not np.array_equal(
                _crop(before, leftBox), _crop(after, leftBox))
            assert not np.array_equal(
                _crop(before, rightBox), _crop(after, rightBox))

    @needsSecondMovie
    def test_twoMoviesOverlayAtHalfOpacity(self, win, movieLib):
        """Two half-opacity movies drawn over each other both show through."""
        size = (80, 60)

        with movieStim(win, movieLib, size=size, pos=(0, 0)) as under, \
                movieStim(win, movieLib, filename=SECOND_MOVIE_PATH,
                          size=size, pos=(0, 0)) as over:
            under.play()
            over.play()
            under.seek(SAMPLE_EARLY)
            over.seek(SAMPLE_EARLY)

            # Freeze both on the frame they are showing. The three captures
            # below have to be of the same two frames to be comparable: left
            # playing, they would decode different frames between captures and
            # the comparisons would pass on that difference alone, whether or
            # not the movies were actually blended.
            under.pause()
            over.pause()

            under.opacity = over.opacity = 0.5

            # drawn at the same size and position, so they cover the same area
            assert _drawnSize(win, under) == pytest.approx(size, abs=1)
            assert _drawnSize(win, over) == pytest.approx(size, abs=1)

            underOnly, background = _drawToBackBuffer(win, under)
            overOnly, _ = _drawToBackBuffer(win, over)
            composite, _ = _drawToBackBuffer(win, under, over)

            assert np.abs(composite - background).mean() > 1.0  # drew something

            # The movie underneath still shows through the one on top, and the
            # one on top has changed what was underneath, so neither is simply
            # painting over the other. Drawn opaque, the top movie would cover
            # the lower one exactly and the first of these would be zero.
            assert np.abs(composite - overOnly).mean() > 1.0
            assert np.abs(composite - underOnly).mean() > 1.0

    def test_loadMovieReplacesCurrentMovie(self, win, movieLib):
        """A new movie can be loaded into an existing stimulus."""
        with movieStim(win, movieLib) as mov:
            mov.loadMovie(str(MOVIE_PATH))

            assert Path(mov.filename) == MOVIE_PATH
            assert mov.duration == pytest.approx(
                MOVIE_DURATION, abs=DURATION_TOL)
            assert mov.isNotStarted

    def test_unloadReleasesMovie(self, win, movieLib):
        """Unloading a movie stops playback and can be called safely twice."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            _drawFrames(win, mov)
            mov.unload()

            assert not mov._isLoaded

            mov.unload()  # unloading again must not raise


# --------------------------------------------------------------------------
# Playback
#

class TestMovieStimPlayback:
    """Tests for playback control and transport functions."""

    def test_initialStatus(self, win, movieLib):
        """A movie with `autoStart=False` waits for `play()`."""
        with movieStim(win, movieLib) as mov:
            assert mov.isNotStarted
            assert not mov.isPlaying
            assert not mov.isPaused
            assert not mov.isFinished
            assert mov.movieTime == pytest.approx(0.0, abs=1e-6)

    def test_playPauseResume(self, win, movieLib):
        """Playback status follows `play()` and `pause()` calls."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            assert mov.isPlaying
            assert not mov.isNotStarted

            mov.pause()
            assert mov.isPaused
            assert not mov.isPlaying

            mov.play()
            assert mov.isPlaying
            assert not mov.isPaused

    def test_toggleSwitchesPlayState(self, win, movieLib):
        """`toggle()` flips between playing and paused."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.toggle()
            assert mov.isPaused

            mov.toggle()
            assert mov.isPlaying

    def test_autoStartBeginsPlaybackOnDraw(self, win, movieLib):
        """With `autoStart=True` the movie starts when first drawn."""
        with movieStim(win, movieLib, autoStart=True) as mov:
            assert mov.isNotStarted

            _drawFrames(win, mov, count=1)

            assert mov.isPlaying

    def test_movieTimeAdvancesWhilePlaying(self, win, movieLib):
        """The movie clock advances as frames are drawn."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            _drawFrames(win, mov, count=1)
            start = mov.movieTime

            _drawFrames(win, mov, count=5, interval=0.02)

            assert mov.movieTime > start

    def test_movieTimeHeldWhilePaused(self, win, movieLib):
        """The movie clock does not advance while paused."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            _drawFrames(win, mov, count=3, interval=0.01)
            mov.pause()

            paused = mov.movieTime
            _drawFrames(win, mov, count=5, interval=0.02)

            assert mov.movieTime == pytest.approx(paused, abs=1e-6)

    def test_stopResetsToStart(self, win, movieLib):
        """`stop()` rewinds the movie and leaves it ready to play again."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.seek(3.0)
            _drawFrames(win, mov)

            mov.stop()

            # `stop()` reloads the movie, so it reports as not started rather
            # than stopped, and can be replayed from the beginning
            assert mov.isNotStarted
            assert mov.movieTime == pytest.approx(0.0, abs=1e-6)

            mov.play()
            assert mov.isPlaying

    def test_seek(self, win, movieLib):
        """`seek()` moves playback to an arbitrary timestamp."""
        with movieStim(win, movieLib) as mov:
            mov.play()

            for timestamp in (5.0, 1.0, 3.5):  # includes seeking backwards
                mov.seek(timestamp)
                assert mov.movieTime == pytest.approx(timestamp, abs=0.05)

    def test_rewindAndFastForward(self, win, movieLib):
        """`rewind()` and `fastForward()` move by a relative offset."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.seek(4.0)

            mov.rewind(1.0)
            assert mov.movieTime == pytest.approx(3.0, abs=0.05)

            mov.fastForward(2.0)
            assert mov.movieTime == pytest.approx(5.0, abs=0.05)

    def test_replayRestartsFromBeginning(self, win, movieLib):
        """`replay()` returns to the start and resumes playing."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.seek(5.0)
            _drawFrames(win, mov)

            mov.replay()

            assert mov.movieTime == pytest.approx(0.0, abs=0.05)
            assert mov.isPlaying

    def test_percentageComplete(self, win, movieLib):
        """Progress through the movie is reported as a percentage."""
        with movieStim(win, movieLib) as mov:
            mov.play()

            mov.seek(0.0)
            assert mov.getPercentageComplete() == pytest.approx(0.0, abs=1.0)

            mov.seek(mov.duration / 2.0)
            assert mov.getPercentageComplete() == pytest.approx(50.0, abs=1.0)

    def test_finishesWhenNotLooping(self, win, movieLib):
        """A non-looping movie reports `isFinished` once it runs out."""
        with movieStim(win, movieLib, loop=False) as mov:
            mov.play()
            mov.seek(mov.duration - 0.05)

            for _ in range(200):
                _drawFrames(win, mov, count=1)
                if mov.isFinished:
                    break

            assert mov.isFinished
            assert not mov.isPlaying

    def test_loopsWhenLoopingEnabled(self, win, movieLib):
        """A looping movie wraps back to the start instead of finishing."""
        with movieStim(win, movieLib, loop=True) as mov:
            assert mov.loop
            mov.play()
            mov.seek(mov.duration - 0.05)

            for _ in range(200):
                _drawFrames(win, mov, count=1)
                if mov.loopCount > 0:
                    break

            assert mov.loopCount > 0
            assert not mov.isFinished
            assert mov.movieTime < mov.duration

    def test_isSeekingFalseWhenIdle(self, win, movieLib):
        """`isSeeking` is clear whenever no seek is outstanding."""
        with movieStim(win, movieLib) as mov:
            assert not mov.isSeeking  # freshly loaded

            mov.play()
            _drawFrames(win, mov)
            assert not mov.isSeeking  # just playing along

            # `seek()` resolves the seek itself, so it is done by the time it
            # returns for media the decoder can keep up with
            mov.seek(SAMPLE_LATE)
            assert not mov.isSeeking

            mov.unload()
            assert not mov.isSeeking  # nothing loaded to be seeking in

    def test_isSeekingSetUntilFrameArrives(self, win, movieLib):
        """The reader reports a seek as outstanding until a frame arrives.

        This goes through `MovieFileReader` because `MovieStim.seek()` fetches
        the frame itself, which resolves the seek before it returns.

        """
        reader = MovieFileReader(str(MOVIE_PATH), decoderLib=movieLib)
        reader.open()
        try:
            # `ffpyplayer` leaves the decoder paused after opening, and needs a
            # moment before it will hand over frames
            reader.pause(False)
            time.sleep(0.2)

            assert not reader.isSeeking

            # asked for part way into a frame rather than exactly on its
            # boundary, where `pyav` can need a second call to hand one over
            target = SAMPLE_LATE + MOVIE_FRAME_INTERVAL / 2.0

            reader.seek(target)
            assert reader.isSeeking  # asked for, but no frame for it yet

            assert reader.getFrame(target) is not None
            assert not reader.isSeeking  # cleared by the frame arriving
        finally:
            reader.close()

        assert not reader.isSeeking  # and by closing the reader

    def test_isSeekingLeavesPlaybackStatusAlone(self, win, movieLib):
        """An outstanding seek does not change whether the movie is playing.

        Reporting seeking through the playback status instead would make
        `isPlaying` go false mid-seek, breaking the usual `while mov.isPlaying`
        style of loop.

        """
        with movieStim(win, movieLib) as mov:
            mov.play()
            _drawFrames(win, mov)

            # Seek the reader without letting `MovieStim` refresh its frame,
            # so the seek is still outstanding when we look. Going through
            # `MovieStim.seek()` would resolve it before returning.
            target = SAMPLE_LATE + MOVIE_FRAME_INTERVAL / 2.0
            mov._player.seek(target)

            assert mov.isSeeking
            assert mov.isPlaying  # still counts as playing
            assert not mov.isPaused
            assert not mov.isFinished
            assert not mov.isNotStarted

            # the frame the seek was waiting on, fetched at the position the
            # reader was sent to
            assert mov._player.getFrame(target) is not None

            assert not mov.isSeeking
            assert mov.isPlaying  # and still playing afterwards

    def test_seekBlockingControlsWhenTheFrameArrives(self, win, movieLib):
        """`blocking` decides whether `seek()` waits for the new frame."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            _drawFrames(win, mov)

            # the default fetches the frame for the new position before
            # returning, so there is nothing left outstanding
            mov.seek(SAMPLE_EARLY)
            assert not mov.isSeeking
            assert mov.movieTime == pytest.approx(SAMPLE_EARLY, abs=0.05)

            # asking not to block returns with the seek still in flight, which
            # is what makes `isSeeking` worth polling from a drawing loop
            mov.seek(SAMPLE_LATE, blocking=False)
            assert mov.isSeeking
            assert mov.isPlaying  # playback status is untouched either way
            assert mov.movieTime == pytest.approx(SAMPLE_LATE, abs=0.05)

            # the movie catches up over the next frame or two of drawing
            assert _drawUntilSeekResolves(win, mov) > 0
            assert not mov.isSeeking

    def test_transportControlsTakeBlocking(self, win, movieLib):
        """The transport controls can leave the seek for the next draw.

        `rewind()`, `fastForward()`, `replay()` and `reset()` all move the
        movie by seeking, so each takes the same `blocking` argument.

        """
        moves = (
            ('rewind',
             lambda mov, blocking: mov.rewind(0.5, blocking=blocking)),
            ('fastForward',
             lambda mov, blocking: mov.fastForward(1.0, blocking=blocking)),
            ('replay',
             lambda mov, blocking: mov.replay(blocking=blocking)),
            ('reset',
             lambda mov, blocking: mov.reset(blocking=blocking)))

        with movieStim(win, movieLib) as mov:
            for name, move in moves:
                # somewhere to move away from, with nothing outstanding
                mov.play()
                mov.seek(SAMPLE_LATE)

                move(mov, True)  # the default waits for the new frame
                assert not mov.isSeeking, name

                mov.play()
                mov.seek(SAMPLE_LATE)

                move(mov, False)  # ... this one hands it to the next draw
                assert mov.isSeeking, name

                _drawUntilSeekResolves(win, mov)
                assert not mov.isSeeking, name

    def test_isSeekingClearsAtEndOfMovie(self, win, movieLib):
        """A seek which runs off the end of the movie does not stay set."""
        with movieStim(win, movieLib) as mov:
            mov.play()
            mov.seek(mov.duration + 5.0)

            assert not mov.isSeeking

    def test_volumeControlsDoNotRaise(self, win, movieLib):
        """Volume and mute are usable regardless of the backend in use.

        `MovieStim` routes these to different places depending on whether the
        decoder plays its own audio, so exercise them for every backend.

        """
        with movieStim(win, movieLib) as mov:
            assert 0.0 <= mov.volume <= 1.0

            mov.volume = 0.5
            mov.volumeUp(0.1)
            mov.volumeDown(0.2)
            assert 0.0 <= mov.volume <= 1.0

            # Muting only has something to act on when the decoder plays audio
            # itself (`ffpyplayer`, via SDL2) or when an audio track has been
            # extracted for separate playback. With `noAudio=True` the other
            # backends have neither, so muting is a no-op for them.
            hasAudio = mov._audioLib == 'sdl2' or mov._audioTrack is not None

            mov.muted = True
            if hasAudio:
                assert mov.muted

            mov.muted = False
            assert not mov.muted


# --------------------------------------------------------------------------
# Scheduling
#

# How far ahead playback is scheduled to start. Long enough to draw a few
# frames before it, short enough not to slow the suite down.
SCHEDULE_DELAY = 0.25

# The movie clock is worked out from the time of the flip each frame is drawn
# for, so it should match the time between flips to well within a frame. This
# is a frame of slack for a loaded machine.
SCHEDULE_TOL = MOVIE_FRAME_INTERVAL


def _absTime(t):
    """Convert a `core.getTime()` time to the absolute time on the clock
    `psychopy.clock.getTime()` reads, which `when` is given in (as for
    `Sound.play()`)."""
    return t + core.monotonicClock.getLastResetTime()


def _nextFlip(win):
    """Time of the window's next flip on the clock `core.getTime()` reads,
    which is the time the movie clock is read at when the movie is drawn."""
    return win.getFutureFlipTime(clock=core.monotonicClock)


def _drawUntil(win, mov, t):
    """Draw the movie until `core.getTime()` reaches `t`.

    Returns
    -------
    float
        The time of the flip the movie was last drawn for, on the clock
        `core.getTime()` reads.

    """
    while core.getTime() < t:
        mov.draw()
        win.flip()

    tFlip = _nextFlip(win)
    mov.draw()  # once more at or after `t`
    win.flip()

    return tFlip


class _AudioTrackStandIn:
    """Stands in for the `Sound` holding a movie's audio track.

    Audio is disabled in these tests, so this records what `MovieStim` asks of
    its audio track instead of playing anything.

    """
    def __init__(self):
        self.volume = 1.0
        self.playedWhen = []  # `when` passed to each call to `play()`
        self.calls = []  # `('play', when)` and `('seek', t)`, in call order

    def play(self, when=None, **kwargs):
        self.playedWhen.append(when)
        self.calls.append(('play', when))

    def pause(self, **kwargs):
        pass

    def stop(self, **kwargs):
        pass

    def seek(self, t):
        self.calls.append(('seek', t))


class TestMovieStimScheduling:
    """Tests for scheduling the start of playback with `play(when=...)`."""

    def test_playWhenHoldsUntilStartTime(self, win, movieLib):
        """Playback scheduled for a time to come holds the movie at its
        position until then, and the movie clock runs from that time."""
        with movieStim(win, movieLib) as mov:
            tStart = core.getTime() + SCHEDULE_DELAY
            mov.play(when=_absTime(tStart))

            # scheduled playback counts as playing, so that a
            # `while mov.isPlaying` loop keeps drawing until it starts
            assert mov.isPlaying

            drawn = 0
            while core.getTime() < tStart - MOVIE_FRAME_INTERVAL:
                _drawFrames(win, mov, count=1)
                drawn += 1
                assert mov.movieTime == pytest.approx(0.0, abs=1e-6)
            assert drawn > 0  # the hold was actually exercised

            tDrawn = _drawUntil(win, mov, tStart + SCHEDULE_DELAY)
            assert mov.movieTime == pytest.approx(
                tDrawn - tStart, abs=SCHEDULE_TOL)

    def test_playWhenWindowStartsOnNextFlip(self, win, movieLib):
        """Passing a window starts playback on its next flip."""
        with movieStim(win, movieLib) as mov:
            win.flip()  # so the next flip is a frame away

            mov.play(when=win)

            # drawn ahead of the flip it was scheduled for, so still held
            mov.draw()
            assert mov.movieTime == pytest.approx(0.0, abs=1e-6)

            tFlip = win.flip()
            tDrawn = _drawUntil(win, mov, tFlip + SCHEDULE_DELAY)
            assert mov.movieTime == pytest.approx(
                tDrawn - tFlip, abs=SCHEDULE_TOL)

    def test_playWhenAbsoluteFlipTime(self, win, movieLib):
        """The next flip as an absolute time, as it would be passed to
        `Sound.play()`, schedules playback for that flip too."""
        with movieStim(win, movieLib) as mov:
            win.flip()  # so the next flip is a frame away

            mov.play(when=win.getFutureFlipTime(clock='ptb'))

            mov.draw()
            assert mov.movieTime == pytest.approx(0.0, abs=1e-6)

            tFlip = win.flip()
            tDrawn = _drawUntil(win, mov, tFlip + SCHEDULE_DELAY)
            assert mov.movieTime == pytest.approx(
                tDrawn - tFlip, abs=SCHEDULE_TOL)

    def test_playWhenInThePastStartsNow(self, win, movieLib):
        """A start time which has already gone by starts playback straight
        away (from the next flip), rather than jumping ahead to where the movie
        would be by now."""
        with movieStim(win, movieLib) as mov:
            tPlay = _nextFlip(win)
            mov.play(when=_absTime(core.getTime() - 10.0))

            tDrawn = _drawUntil(win, mov, tPlay + SCHEDULE_DELAY)
            assert mov.movieTime == pytest.approx(
                tDrawn - tPlay, abs=SCHEDULE_TOL)

    def test_pauseCancelsScheduledStart(self, win, movieLib):
        """Pausing before a scheduled start cancels it, and playing again
        starts from the same position straight away."""
        with movieStim(win, movieLib) as mov:
            mov.play(when=_absTime(core.getTime() + 60.0))
            _drawFrames(win, mov)
            mov.pause()

            assert mov.isPaused
            _drawFrames(win, mov)
            assert mov.movieTime == pytest.approx(0.0, abs=1e-6)

            tPlay = _nextFlip(win)
            mov.play()
            tDrawn = _drawUntil(win, mov, tPlay + SCHEDULE_DELAY)
            assert mov.movieTime == pytest.approx(
                tDrawn - tPlay, abs=SCHEDULE_TOL)

    def test_seekBeforePlayIsKept(self, win, movieLib):
        """A seek before playback starts is where playback starts from, both
        while waiting for a scheduled start and after it."""
        with movieStim(win, movieLib) as mov:
            mov.seek(SAMPLE_EARLY)

            # drawing a movie which hasn't started must not undo the seek
            _drawFrames(win, mov)
            assert mov.movieTime == pytest.approx(SAMPLE_EARLY, abs=1e-6)

            tStart = core.getTime() + SCHEDULE_DELAY
            mov.play(when=_absTime(tStart))
            _drawFrames(win, mov)
            assert mov.movieTime == pytest.approx(SAMPLE_EARLY, abs=1e-6)

            tDrawn = _drawUntil(win, mov, tStart + SCHEDULE_DELAY)
            assert mov.movieTime == pytest.approx(
                SAMPLE_EARLY + tDrawn - tStart, abs=SCHEDULE_TOL)

    def test_playStartsAudioTrackFromMovieTime(self, win, movieLib):
        """Playing seeks the audio track to wherever the video is first, so
        that resuming doesn't rely on the track carrying on from the right
        place by itself (the `sounddevice` backend reads ahead of playback,
        so would resume from a little past where it was paused)."""
        with movieStim(win, movieLib) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            track = _AudioTrackStandIn()
            mov._noAudio = False
            mov._audioTrack = track

            mov.play()
            _drawFrames(win, mov, count=5, interval=0.01)
            mov.pause()
            paused = mov.movieTime
            assert paused > 0.0

            del track.calls[:]
            mov.play()
            (seek, tSeek), (play, _) = track.calls
            assert (seek, play) == ('seek', 'play')
            assert tSeek == pytest.approx(paused, abs=1e-6)

            # and from a position seeked to while paused
            mov.pause()
            mov.seek(SAMPLE_EARLY)
            del track.calls[:]
            mov.play()
            assert track.calls[0][0] == 'seek'
            assert track.calls[0][1] == pytest.approx(SAMPLE_EARLY, abs=1e-6)
            assert track.calls[-1][0] == 'play'

    def test_playWhenSchedulesAudioTrack(self, win, movieLib):
        """The audio track is scheduled to start at the same time as the
        video, in a form each `Sound` backend can convert to its own clock.

        The `Sound` backends ask a window passed as `when` for its next flip
        time, either on PsychoPy's clock, as an absolute time, or relative to
        now, so `when` must answer for the start time in each of those.

        """
        with movieStim(win, movieLib) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            track = _AudioTrackStandIn()
            mov._noAudio = False
            mov._audioTrack = track

            # without `when`, the track is started straight away
            mov.play()
            assert track.playedWhen[-1] is None
            mov.pause()

            tStart = core.getTime() + 1.0
            mov.play(when=_absTime(tStart))
            when = track.playedWhen[-1]

            assert when.getFutureFlipTime(clock='ptb') == pytest.approx(
                _absTime(tStart))
            assert when.getFutureFlipTime(clock=None) == pytest.approx(
                _absTime(tStart) - logging.defaultClock.getLastResetTime())
            assert when.getFutureFlipTime(clock='now') == pytest.approx(
                tStart - core.getTime(), abs=0.01)
            mov.pause()

            # a window is resolved to its next flip, the same time the video
            # is held until
            win.flip()
            mov.play(when=win)
            tFlip = track.playedWhen[-1].getFutureFlipTime(clock=None)
            assert tFlip == pytest.approx(
                win.getFutureFlipTime(clock=None), abs=1e-3)
            assert tFlip > core.getTime()


# --------------------------------------------------------------------------
# Frame timing
#

# backends which decode frames ahead of playback on a thread of their own
DECODE_AHEAD_BACKENDS = ('pyav', 'opencv')


def _queuedFrameCount(reader):
    """Number of frames the decode thread has decoded ahead."""
    with reader._decoderCondition:
        return reader._queuedFrameCount()


def _waitForQueuedFrames(reader, count, timeout=5.0):
    """Wait for the decode thread to have `count` frames decoded ahead,
    returning how many it has when done waiting."""
    deadline = time.time() + timeout
    while _queuedFrameCount(reader) != count and time.time() < deadline:
        time.sleep(0.01)

    return _queuedFrameCount(reader)


class TestMovieStimFrameTiming:
    """Tests for which frame is shown on which flip, and for keeping the work
    of decoding out of the way of drawing."""

    @pytest.mark.parametrize('framePeriod, frameInterval, expected', [
        (1 / 60, 1 / 60, 1 / 120),  # same rate, half a frame
        (1 / 60, 1 / 30, 1 / 120),  # 2 refreshes a frame, a quarter frame
        (1 / 60, 1 / 24, 1 / 240),  # 2.5 refreshes a frame, a tenth
        (1 / 60, 1 / 120, 1 / 240),  # 2 frames a refresh, half a frame
        (1 / 60, 1.0, 1 / 120),  # never more than half a refresh
        (1 / 59.96, 1 / 60, 1 / 120),  # measured rates count as 60 Hz
        (0.0, 1 / 60, 0.0),  # unknown refresh rate
        (None, 1 / 60, 0.0),
        (1 / 60, -1.0, 0.0)])  # unknown frame rate
    def test_frameSampleOffset(self, win, movieLib, framePeriod,
                               frameInterval, expected):
        """Frames are chosen from as far past the movie clock as keeps it
        clear of frame boundaries, given how flips line up with frames."""
        assert _frameSampleOffset(framePeriod, frameInterval) == \
            pytest.approx(expected)

    def test_playShowsFirstFrameOnNextFlip(self, win, movieLib):
        """The movie clock starts from the next flip, so the first frame is
        the one shown on it, and the clock reads the time between flips."""
        with movieStim(win, movieLib) as mov:
            win.flip()
            tStart = _nextFlip(win)

            mov.play()
            mov.draw()
            assert mov.movieTime == pytest.approx(0.0, abs=1e-6)
            assert mov.pts == pytest.approx(0.0, abs=1e-6)

            win.flip()
            tNext = _nextFlip(win)
            mov.draw()
            assert mov.movieTime == pytest.approx(tNext - tStart, abs=1e-3)

    def test_framesAdvanceOncePerRefresh(self, win, movieLib, monkeypatch):
        """With the display refreshing once per movie frame, each refresh
        shows the next frame even when the flips jitter a little.

        Playback starting on a flip puts every later flip right at the start
        of a frame here, where the movie used to judder, repeating one frame
        and skipping the next as the jitter tipped it either way.

        """
        rng = np.random.default_rng(0)
        tFlip = [core.getTime() + 10.0]  # flips stood in for, see below

        # a display refreshing at the movie frame rate, with ~1 ms of jitter
        monkeypatch.setattr(win, 'monitorFramePeriod', MOVIE_FRAME_INTERVAL)
        monkeypatch.setattr(
            win, 'getFutureFlipTime',
            lambda targetTime=0, clock=None: tFlip[0])

        with movieStim(win, movieLib) as mov:
            mov.play()

            shown = []
            for _ in range(60):
                assert mov.updateVideoFrame()
                shown.append(int(round(mov.pts / MOVIE_FRAME_INTERVAL)))
                tFlip[0] = tFlip[0] + MOVIE_FRAME_INTERVAL + \
                    rng.uniform(-1e-3, 1e-3)

        assert shown[0] == 0
        assert np.all(np.diff(shown) == 1), shown

    def test_deferredDecodingWaitsForDecodeAhead(self, win, movieLib):
        """`getFrame(deferDecoding=True)` leaves the decode thread be until
        `decodeAhead()`, so that it can't compete with copying the frame to
        the GPU. Otherwise it replaces the frames taken straight away."""
        if movieLib not in DECODE_AHEAD_BACKENDS:
            pytest.skip('{} does not decode ahead'.format(movieLib))

        reader = MovieFileReader(str(MOVIE_PATH), decoderLib=movieLib)
        reader.open()
        try:
            full = reader._decodeQueueDepth
            assert _waitForQueuedFrames(reader, full) == full

            assert reader.getFrame(
                3.5 * MOVIE_FRAME_INTERVAL, deferDecoding=True) is not None
            left = _queuedFrameCount(reader)
            assert left < full

            time.sleep(0.2)
            assert _queuedFrameCount(reader) == left  # left be

            reader.decodeAhead()
            assert _waitForQueuedFrames(reader, full) == full

            assert reader.getFrame(6.5 * MOVIE_FRAME_INTERVAL) is not None
            assert _waitForQueuedFrames(reader, full) == full
        finally:
            reader.close()

    def test_decodedOffDrawingThread(self, win, movieLib, monkeypatch):
        """Frames are decoded (and converted) on the decode thread as the
        movie plays, never on the thread drawing it, where it would hold up
        the drawing."""
        if movieLib not in DECODE_AHEAD_BACKENDS:
            pytest.skip('{} does not decode ahead'.format(movieLib))

        decodedOn = set()
        readerClass = movies.readers._base._MOVIE_READER_CLASSES[movieLib]
        decodeNextFrame = readerClass._decodeNextFrame

        def recording(reader):
            decodedOn.add(threading.current_thread())
            return decodeNextFrame(reader)

        monkeypatch.setattr(readerClass, '_decodeNextFrame', recording)

        with movieStim(win, movieLib) as mov:
            mov.play()
            _drawFrames(win, mov, count=20, interval=0.01)
            mov.seek(SAMPLE_LATE)
            _drawFrames(win, mov, count=5, interval=0.01)

        assert decodedOn
        assert threading.main_thread() not in decodedOn

    def test_framesFreedOffDrawingThread(self, win, movieLib):
        """Frames are freed by the decode thread rather than the one drawing
        them, where freeing a large frame can take long enough to miss a
        flip."""
        if movieLib not in DECODE_AHEAD_BACKENDS:
            pytest.skip('{} does not decode ahead'.format(movieLib))

        freedOn = []

        def watch(frameImage):
            # the samples, which the frame is the last thing holding on to
            samples = frameImage.planes[0][0] if isinstance(
                frameImage, movies._YUVFrameAdapter) else frameImage.memview
            weakref.finalize(
                samples,
                lambda: freedOn.append(threading.current_thread()))

        with movieStim(win, movieLib) as mov:
            mov.play()

            lastPts = None
            for _ in range(40):
                _drawFrames(win, mov, count=1, interval=0.02)
                if mov.pts != lastPts:
                    lastPts = mov.pts
                    watch(mov._recentFrameImage)

            # let the decode thread get round to the last frames handed to it
            _drawFrames(win, mov, count=3, interval=0.05)

            assert freedOn
            assert threading.main_thread() not in freedOn


# --------------------------------------------------------------------------
# Audio track
#

def _readAudioTrackProperties(filename):
    """Sample rate and duration in seconds of the first audio track in a movie,
    or `None` if it has none."""
    import av

    with av.open(str(filename)) as container:
        audioStream = next(
            (s for s in container.streams if s.type == 'audio'), None)
        if audioStream is None:
            return None

        return (audioStream.codec_context.sample_rate,
                float(audioStream.duration * audioStream.time_base))


MOVIE_AUDIO = _readAudioTrackProperties(MOVIE_PATH)

# as defined, rather than as any test has patched it
_decodeAudioTrack = movies.MovieStim._decodeAudioTrack

needsMovieAudio = pytest.mark.skipif(
    MOVIE_AUDIO is None, reason='test movie has no audio track')


class _SoundStandIn(_AudioTrackStandIn):
    """Stands in for `psychopy.sound.Sound`, as made for a movie's audio
    track, on a stereo speaker playing at `SPEAKER_RATE`.

    This records what the track is loaded with instead of opening an audio
    device, which test machines often lack.

    """
    SPEAKER_RATE = 48000

    made = []  # every one made, in order

    def __init__(self, value, **kwargs):
        super().__init__()
        self.speaker = type(
            'Speaker', (), {'sampleRateHz': self.SPEAKER_RATE, 'channels': 2})
        self.sampleRate = self.SPEAKER_RATE
        self.sndArr = np.asarray(value)
        self.writes = 0  # calls to `_writeSamples`
        _SoundStandIn.made.append(self)

    @property
    def loaded(self):
        """Samples the track is loaded with."""
        return self.sndArr

    def setSound(self, value, log=True):
        self.sndArr = np.asarray(value)

    def _allocateSamples(self, nSamples, channels):
        self.sndArr = np.zeros((nSamples, channels), np.float32)

    def _writeSamples(self, start, samples):
        nWritten = max(0, min(len(samples), len(self.sndArr) - start))
        self.sndArr[start:start + nWritten] = samples[:nWritten]
        self.writes += 1
        return nWritten

    def _trimSamples(self, nSamples):
        self.sndArr = self.sndArr[:nSamples]

    def stop(self, **kwargs):
        self.calls.append(('stop', None))


@pytest.fixture
def soundStandIn(monkeypatch):
    """Make `MovieStim` load audio tracks into `_SoundStandIn`s."""
    import psychopy.sound

    _SoundStandIn.made = []
    monkeypatch.setattr(psychopy.sound, 'Sound', _SoundStandIn)

    return _SoundStandIn


@pytest.fixture
def gatedAudioDecode(monkeypatch):
    """Hold up `MovieStim` decoding audio tracks in the background until the
    event returned is set (or decoding is cancelled)."""
    release = threading.Event()

    def gated(container, audioStream, sampleRate, layout=None, onBlock=None,
              cancel=None):
        while not release.is_set() and not cancel.is_set():
            time.sleep(0.005)
        return _decodeAudioTrack(
            container, audioStream, sampleRate, layout=layout,
            onBlock=onBlock, cancel=cancel)

    monkeypatch.setattr(
        movies.MovieStim, '_decodeAudioTrack', staticmethod(gated))

    return release


def _decodeMovieAudio(sampleRate, layout='stereo'):
    """The test movie's audio track, decoded in one go."""
    import av

    with av.open(str(MOVIE_PATH)) as container:
        return _decodeAudioTrack(
            container, container.streams.audio[0], sampleRate, layout=layout)


def _waitForAudio(mov, timeout=10.0):
    """Wait for a movie's audio track to finish loading in the background."""
    deadline = time.time() + timeout
    while not mov.isAudioReady and time.time() < deadline:
        time.sleep(0.005)

    assert mov.isAudioReady


@needsMovieAudio
class TestMovieStimAudioTrack:
    """Tests for decoding a movie's audio track for playback alongside it."""

    @pytest.mark.parametrize('sampleRate', [None, 48000, 22050])
    def test_decodeAudioTrack(self, win, movieLib, sampleRate):
        """The track decodes to the rate asked for, matching what resampling
        it a decoded frame at a time gives."""
        import av
        from av.audio.resampler import AudioResampler

        sourceRate, duration = MOVIE_AUDIO
        sampleRate = sampleRate or sourceRate

        with av.open(str(MOVIE_PATH)) as container:
            audioStream = container.streams.audio[0]
            samples = visual.MovieStim._decodeAudioTrack(
                container, audioStream, sampleRate)

        with av.open(str(MOVIE_PATH)) as container:
            audioStream = container.streams.audio[0]
            resampler = AudioResampler(
                format='flt', layout=audioStream.layout.name, rate=sampleRate)
            expected = [
                resampled.to_ndarray()
                for frame in container.decode(audioStream)
                for resampled in resampler.resample(frame)]
            expected += [r.to_ndarray() for r in resampler.resample(None)]
            expected = np.concatenate(expected, axis=1).reshape(
                -1, len(audioStream.layout.channels))

        assert samples.dtype == np.float32
        assert samples.shape == expected.shape
        assert len(samples) / sampleRate == pytest.approx(duration, abs=0.05)
        np.testing.assert_allclose(samples, expected, atol=1e-6)

    def test_decodeAudioTrackConvertsSampleFormat(self, win, movieLib,
                                                  tmp_path):
        """Tracks decoded to something other than 32-bit float planar, here
        16-bit mono, are converted on the way."""
        import av
        import soundfile
        from av.audio.resampler import AudioResampler

        sourceRate, sampleRate = 32000, 44100
        t = np.arange(2 * sourceRate) / sourceRate
        tone = (0.5 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)
        trackPath = tmp_path / 'tone.wav'
        soundfile.write(str(trackPath), tone, sourceRate, subtype='PCM_16')

        with av.open(str(trackPath)) as container:
            audioStream = container.streams.audio[0]
            samples = visual.MovieStim._decodeAudioTrack(
                container, audioStream, sampleRate)

        with av.open(str(trackPath)) as container:
            resampler = AudioResampler(format='flt', layout='mono',
                                       rate=sampleRate)
            expected = [
                resampled.to_ndarray()
                for frame in container.decode(audio=0)
                for resampled in resampler.resample(frame)]
            expected += [r.to_ndarray() for r in resampler.resample(None)]
            expected = np.concatenate(expected, axis=1).reshape(-1, 1)

        assert samples.shape == expected.shape
        assert len(samples) == pytest.approx(2 * sampleRate, abs=64)
        np.testing.assert_allclose(samples, expected, atol=1e-4)

    def test_audioTrackDecodedAtSpeakerRate(self, win, movieLib,
                                            soundStandIn):
        """The track is loaded at the rate its speaker plays at, rather than
        one it would have to be resampled from again to be played."""
        with movieStim(win, movieLib, noAudio=False) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            _waitForAudio(mov)
            track = mov._audioTrack
            assert soundStandIn.made == [track]
            assert track.sampleRate == soundStandIn.SPEAKER_RATE

            samples = track.loaded
            assert samples.dtype == np.float32
            assert samples.shape[1] == 2
            assert len(samples) / soundStandIn.SPEAKER_RATE == \
                pytest.approx(MOVIE_AUDIO[1], abs=0.05)

            # written a block at a time as it decoded, to the same result as
            # decoding it in one go
            assert track.writes > 0
            np.testing.assert_array_equal(
                samples, _decodeMovieAudio(soundStandIn.SPEAKER_RATE))

    def test_stopKeepsAudioTrack(self, win, movieLib, soundStandIn):
        """`stop()` reloads the movie, but keeps its audio track (back at the
        start) rather than decoding it all over again."""
        with movieStim(win, movieLib, noAudio=False) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            track = mov._audioTrack
            mov.play()
            _drawFrames(win, mov)

            del track.calls[:]
            mov.stop()

            assert mov._audioTrack is track
            assert soundStandIn.made == [track]
            assert track.calls[0] == ('stop', None)
            assert ('seek', 0.0) in track.calls

    def test_audioTrackReloadedWhenMovieChanges(self, win, movieLib,
                                                soundStandIn, tmp_path):
        """A track is only kept for the file it came from, as it is on disk.
        Changing the file, or loading another, decodes the track again."""
        import os
        import shutil

        moviePath = tmp_path / MOVIE_PATH.name
        shutil.copyfile(MOVIE_PATH, moviePath)

        with movieStim(win, movieLib, filename=moviePath, noAudio=False) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            first = mov._audioTrack

            # the file is replaced on disk with a newer version
            stat = os.stat(moviePath)
            os.utime(moviePath, ns=(stat.st_atime_ns,
                                    stat.st_mtime_ns + 1_000_000_000))
            mov.stop()

            second = mov._audioTrack
            assert second is not first
            assert soundStandIn.made == [first, second]
            assert ('stop', None) in first.calls

            # and another movie altogether
            mov.loadMovie(str(MOVIE_PATH))
            assert mov._audioTrack is not second
            assert len(soundStandIn.made) == 3

    def test_loadingDoesNotWaitForAudioTrack(self, win, movieLib,
                                             soundStandIn, gatedAudioDecode):
        """Loading a movie returns while its audio track is still decoding in
        the background, and `play()` waits for it to finish."""
        with movieStim(win, movieLib, noAudio=False,
                       loadAudioInBackground=True) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            assert not mov.isAudioReady
            mov.volume = 0.25  # applies to the track while it loads

            threading.Timer(0.2, gatedAudioDecode.set).start()
            mov.play()

            assert mov.isAudioReady
            assert mov.isPlaying
            track = mov._audioTrack
            assert track.volume == pytest.approx(0.25)
            assert track.calls[-1][0] == 'play'
            np.testing.assert_array_equal(
                track.loaded, _decodeMovieAudio(soundStandIn.SPEAKER_RATE))

    def test_unloadStopsAudioTrackDecoding(self, win, movieLib, soundStandIn,
                                           gatedAudioDecode):
        """Unloading a movie while its audio track is decoding stops it, and
        nothing more is written to the track afterwards."""
        with movieStim(win, movieLib, noAudio=False,
                       loadAudioInBackground=True) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            loader = mov._audioLoader
            track = mov._audioTrack
            mov.unload()

            assert loader.isDone
            assert loader.error is None
            assert loader.nSamples == 0
            assert track.writes == 0
            assert mov._audioTrack is None
            assert loader not in movies._audioTrackLoaders

    def test_stopKeepsAudioTrackDecoding(self, win, movieLib, soundStandIn,
                                         gatedAudioDecode):
        """`stop()` while the audio track is still decoding carries on with it,
        rather than starting it over."""
        with movieStim(win, movieLib, noAudio=False,
                       loadAudioInBackground=True) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            loader = mov._audioLoader
            mov.stop()
            assert mov._audioLoader is loader
            assert not loader.isDone

            gatedAudioDecode.set()
            mov.play()

            assert soundStandIn.made == [mov._audioTrack]
            np.testing.assert_array_equal(
                mov._audioTrack.loaded,
                _decodeMovieAudio(soundStandIn.SPEAKER_RATE))

    def test_loadingWaitsForAudioTrackByDefault(self, win, movieLib,
                                                soundStandIn):
        """Unless asked to load it in the background, the audio track has
        loaded by the time loading the movie returns."""
        with movieStim(win, movieLib, noAudio=False) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            assert mov._audioLoader is None
            assert mov.isAudioReady
            np.testing.assert_array_equal(
                mov._audioTrack.loaded,
                _decodeMovieAudio(soundStandIn.SPEAKER_RATE))

    @pytest.mark.parametrize('inBackground', [False, True])
    def test_audioTrackErrorRaised(self, win, movieLib, soundStandIn,
                                   monkeypatch, inBackground):
        """An error decoding the audio track is raised by loading the movie,
        or by `play()` if loading it in the background, after which the movie
        plays without it."""
        def broken(*args, **kwargs):
            raise RuntimeError('broken audio track')

        monkeypatch.setattr(
            movies.MovieStim, '_decodeAudioTrack', staticmethod(broken))

        if not inBackground:
            with pytest.raises(RuntimeError, match='broken audio track'):
                with movieStim(win, movieLib, noAudio=False):
                    pass
            return

        with movieStim(win, movieLib, noAudio=False,
                       loadAudioInBackground=True) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            with pytest.raises(RuntimeError, match='broken audio track'):
                mov.play()
            assert mov._audioTrack is None

            mov.play()
            assert mov.isPlaying

    @pytest.mark.parametrize('inBackground', [False, True])
    @pytest.mark.parametrize('duration', [0.25, None])
    def test_audioTrackLongerThanAllocated(self, win, movieLib, soundStandIn,
                                           monkeypatch, duration, inBackground):
        """A track which decodes longer than the movie file says, or whose
        length it doesn't say, is still loaded whole."""
        monkeypatch.setattr(
            movies.MovieStim, '_getAudioDuration',
            staticmethod(lambda container, audioStream: duration))

        with movieStim(win, movieLib, noAudio=False,
                       loadAudioInBackground=inBackground) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            _waitForAudio(mov)
            np.testing.assert_array_equal(
                mov._audioTrack.loaded,
                _decodeMovieAudio(soundStandIn.SPEAKER_RATE))

    def test_audioTrackAtRequestedRate(self, win, movieLib, soundStandIn):
        """`audioConfig['fps']` decodes the track at that rate instead of the
        speaker's, leaving the `Sound` to resample it."""
        with movieStim(win, movieLib, noAudio=False,
                       audioConfig={'fps': 22050}) as mov:
            if mov._decoderPlaysAudio:
                pytest.skip('{} plays the audio itself'.format(movieLib))

            _waitForAudio(mov)
            track = mov._audioTrack
            assert track.sampleRate == 22050
            np.testing.assert_array_equal(
                track.loaded, _decodeMovieAudio(22050))


# --------------------------------------------------------------------------
# Scaling frames down as they're decoded
#

def _drawUntilFrameSize(win, mov, size, timeout=3.0, interval=1 / 60.):
    """Play the movie until it shows a frame of `size`, returning whether it
    got to one within `timeout` seconds (frames decoded ahead before a size
    change keep the old size).

    This waits on time rather than a number of flips, since the frames decoded
    ahead take up to `DECODE_AHEAD_MAX_FRAMES` frames' worth of playback to get
    through, and `flip()` doesn't wait for a refresh without vsync (as under
    Xvfb), so a fixed number of flips can be over before the movie gets there.

    """
    mov.play()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        mov.draw()
        win.flip()
        if tuple(mov._recentFrameSize) == tuple(size):
            return True
        time.sleep(interval)

    return False


# backends which scale frames down as they decode them
SCALING_BACKENDS = ('pyav', 'opencv')


class TestMovieStimDownscaling:
    """Tests for decoding frames at the size the movie is drawn at."""

    def test_framesDecodedAtDrawnSize(self, win, movieLib):
        """Frames come out at the size the movie is drawn at, from the very
        first, and the texture they're uploaded to is that size too."""
        if movieLib not in SCALING_BACKENDS:
            pytest.skip('{} does not scale frames'.format(movieLib))

        drawnSize = (MOVIE_SIZE[0] // 4, MOVIE_SIZE[1] // 4)
        with movieStim(win, movieLib, size=drawnSize, units='pix') as mov:
            assert mov._player.outputFrameSize == drawnSize
            assert tuple(mov._recentFrameSize) == drawnSize
            assert (mov._vidWidth, mov._vidHeight) == drawnSize
            assert mov._recentFrame.size >= _frameBytesExpected(mov)

            # and still draws to the size asked for
            assert _drawnSize(win, mov) == pytest.approx(drawnSize, abs=1)

    def test_downscaleFramesOff(self, win, movieLib):
        """`downscaleFrames=False` keeps frames at the movie's own size."""
        with movieStim(win, movieLib, size=(32, 32), units='pix',
                       downscaleFrames=False) as mov:
            assert mov._player.outputFrameSize is None
            assert tuple(mov._recentFrameSize) == MOVIE_SIZE
            assert (mov._vidWidth, mov._vidHeight) == MOVIE_SIZE

    def test_framesNeverScaledUp(self, win, movieLib):
        """A movie drawn larger than its own size is decoded at its own size
        (in each dimension), rather than scaled up for nothing."""
        with movieStim(win, movieLib, units='pix',
                       size=(MOVIE_SIZE[0] * 2, MOVIE_SIZE[1] // 2)) as mov:
            expected = MOVIE_SIZE if movieLib not in SCALING_BACKENDS else \
                (MOVIE_SIZE[0], MOVIE_SIZE[1] // 2)
            assert tuple(mov._recentFrameSize) == expected

    def test_sizeChangeFollowedByFrames(self, win, movieLib):
        """Changing the size the movie is drawn at changes the size frames are
        decoded at, and the texture follows them."""
        if movieLib not in SCALING_BACKENDS:
            pytest.skip('{} does not scale frames'.format(movieLib))

        with movieStim(win, movieLib, size=(64, 64), units='pix') as mov:
            mov.size = (40, 30)
            assert mov._player.outputFrameSize == (40, 30)

            assert _drawUntilFrameSize(win, mov, (40, 30))
            assert (mov._vidWidth, mov._vidHeight) == (40, 30)

    def test_sizeFromMovieAspect(self, win, movieLib):
        """With one dimension left to the movie's aspect ratio, frames come
        out at the size that works out to once the movie is open."""
        if movieLib not in SCALING_BACKENDS:
            pytest.skip('{} does not scale frames'.format(movieLib))

        width = MOVIE_SIZE[0] // 2
        height = int(math.ceil(width * MOVIE_SIZE[1] / MOVIE_SIZE[0]))
        with movieStim(win, movieLib, size=(width, None), units='pix') as mov:
            assert mov._player.outputFrameSize == (width, height)
            assert _drawUntilFrameSize(win, mov, (width, height))

    def test_interpolateChoosesFilter(self, win, movieLib):
        """Frames are scaled down with a box filter, or nearest neighbour when
        not interpolating, as the GPU would."""
        with movieStim(win, movieLib, size=(64, 64), units='pix') as mov:
            assert mov._player._outputFrameFormat[1] == 'AREA'

            mov.interpolate = False
            assert mov._player._outputFrameFormat[1] == 'POINT'

    def test_readerOutputFrameSize(self, win, movieLib):
        """`MovieFileReader.setOutputFrameSize` sets the size frames are
        decoded at from then on, never larger than their own, and makes room
        to decode more of them ahead."""
        if movieLib not in SCALING_BACKENDS:
            pytest.skip('{} does not scale frames'.format(movieLib))

        reader = MovieFileReader(str(MOVIE_PATH), decoderLib=movieLib)
        reader.setOutputFrameSize((50.2, 40.0))
        reader.open()
        try:
            assert reader.outputFrameSize == (51, 40)  # whole pixels, rounded up
            first = reader._getFrameFromStore(0.0)[0]
            assert first.size == (51, 40)

            reader.setOutputFrameSize((MOVIE_SIZE[0] * 2, 10))
            reader.seek(SAMPLE_EARLY)
            img = reader.getFrame(SAMPLE_EARLY)[0]
            assert img.size == (MOVIE_SIZE[0], 10)
            assert reader._decodeQueueDepth == \
                movies.readers._base.DECODE_AHEAD_MAX_FRAMES
        finally:
            reader.close()

    @pytest.mark.parametrize('size', [
        (64, 48),  # divides exactly, done in one go
        (100, 77),  # doesn't, so halved first
        (351, 288),  # by less than half
        (1, 1)])
    def test_resizeFrameOpenCV(self, win, movieLib, size):
        """OpenCV frames are box filtered down to the size asked for, coming
        out close to doing it in one go (which is slow for large reductions),
        or nearest neighbour for `'POINT'`."""
        cv2 = pytest.importorskip('cv2')
        if movieLib != 'opencv':
            pytest.skip('only needs to run the once')

        frame = np.random.default_rng(0).integers(
            0, 256, (288, 352, 3), dtype=np.uint8)
        frame = cv2.GaussianBlur(frame, (0, 0), 3)  # some structure to keep

        scaled = movies.readers.opencv_reader._resizeFrameOpenCV(frame, size)
        assert (scaled.shape[1], scaled.shape[0]) == size
        oneGo = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
        assert np.abs(scaled.astype(int) - oneGo).mean() < 2.0

        nearest = movies.readers.opencv_reader._resizeFrameOpenCV(
            frame, size, 'POINT')
        np.testing.assert_array_equal(
            nearest, cv2.resize(frame, size, interpolation=cv2.INTER_NEAREST))


# --------------------------------------------------------------------------
# Converting frames to RGB on the GPU
#

def _writeTaggedMovie(path, pixelFormat='yuv444p', colorspace=1, colorRange=1,
                      size=(64, 48), nFrames=5):
    """Write a short lossless (FFV1) movie of smooth random colour, tagged
    with the colour matrix (`AVColorSpace` value) and range given, returning
    its first frame's planes."""
    import av
    import cv2

    rng = np.random.default_rng(0)
    width, height = size
    first = None
    with av.open(str(path), 'w') as container:
        stream = container.add_stream('ffv1', rate=30)
        stream.width, stream.height, stream.pix_fmt = width, height, pixelFormat
        stream.codec_context.colorspace = colorspace
        stream.codec_context.color_range = colorRange
        for _ in range(nFrames):
            # smooth, so that interpolating chroma makes little difference
            rgb = cv2.GaussianBlur(
                rng.integers(0, 256, (height, width, 3), dtype=np.uint8),
                (0, 0), 4)
            rgb = cv2.normalize(rgb, None, 20, 235, cv2.NORM_MINMAX)
            frame = av.VideoFrame.from_ndarray(rgb, format='rgb24').reformat(
                format=pixelFormat)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)

    return path


def _movieRegion(win, size, inset=2):
    """Index of the part of a captured window a movie of `size` drawn in the
    middle of it covers, `inset` pixels in from its edges."""
    x0 = (win.size[0] - size[0]) // 2
    y0 = (win.size[1] - size[1]) // 2

    return np.s_[y0 + inset:y0 + size[1] - inset,
                 x0 + inset:x0 + size[0] - inset]


def _readTexture(textureId, width, height):
    """Read an RGBA texture back from the GPU, its first row first."""
    import psychopy.tools.pygletgl as GL

    data = (GL.GLubyte * (width * height * 4))()
    GL.glBindTexture(GL.GL_TEXTURE_2D, textureId)
    GL.glGetTexImage(
        GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, data)
    GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    return np.frombuffer(data, np.uint8).reshape(height, width, 4).copy()


def _glState():
    """The parts of the GL state converting a frame on the GPU changes."""
    import ctypes
    import psychopy.tools.pygletgl as GL

    state = {}
    for name in ('GL_FRAMEBUFFER_BINDING', 'GL_CURRENT_PROGRAM',
                 'GL_ACTIVE_TEXTURE', 'GL_CLIENT_ACTIVE_TEXTURE',
                 'GL_MATRIX_MODE', 'GL_TEXTURE_BINDING_2D',
                 'GL_PIXEL_UNPACK_BUFFER_BINDING', 'GL_UNPACK_ALIGNMENT',
                 'GL_UNPACK_ROW_LENGTH', 'GL_BLEND_SRC', 'GL_BLEND_DST'):
        value = GL.GLint()
        GL.glGetIntegerv(getattr(GL, name), ctypes.byref(value))
        state[name] = value.value
    viewport = (GL.GLint * 4)()
    GL.glGetIntegerv(GL.GL_VIEWPORT, viewport)
    state['GL_VIEWPORT'] = tuple(viewport)
    for name in ('GL_BLEND', 'GL_SCISSOR_TEST', 'GL_DEPTH_TEST',
                 'GL_STENCIL_TEST', 'GL_TEXTURE_2D'):
        state[name] = bool(GL.glIsEnabled(getattr(GL, name)))
    for name in ('GL_PROJECTION_MATRIX', 'GL_MODELVIEW_MATRIX'):
        matrix = (GL.GLfloat * 16)()
        GL.glGetFloatv(getattr(GL, name), matrix)
        state[name] = tuple(matrix)

    return state


class _TaggedFrame:
    """Just what `_frameColorMatrix` looks at of a frame."""
    def __init__(self, colorspace, width, height):
        self.colorspace, self.width, self.height = colorspace, width, height


class TestMovieStimGPUColorConversion:
    """Tests for uploading frames as YUV and converting them in a shader."""

    @pytest.mark.parametrize('colorspace, size, expected', [
        (1, (320, 240), 'ITU709'),  # tagged, whatever the size
        (6, (3840, 2160), 'ITU601'),
        (5, (640, 480), 'ITU601'),
        (9, (3840, 2160), 'BT2020'),
        (2, (1920, 1080), 'ITU709'),  # untagged HD is taken to be BT.709
        (2, (1280, 720), 'ITU709'),
        (2, (720, 576), 'ITU601'),  # and SD BT.601
        (8, (640, 480), 'ITU601')])  # YCgCo has no matrix to use
    def test_frameColorMatrix(self, win, movieLib, colorspace, size,
                              expected):
        """Frames are converted with the colour matrix they're tagged with,
        or the one video players take untagged frames of their size to be."""
        frame = _TaggedFrame(colorspace, *size)
        assert movies.frame._frameColorMatrix(frame) == expected

    @pytest.mark.parametrize('fullRange', [False, True])
    @pytest.mark.parametrize('colorMatrix', sorted(movies._COLOR_MATRIX_KR_KB))
    def test_yuvToRGBMatchesSwscale(self, win, movieLib, colorMatrix,
                                    fullRange):
        """What the shader converts YUV to RGB with matches `swscale`."""
        import av
        from av.video.reformatter import Colorspace

        rng = np.random.default_rng(1)
        planes = rng.integers(16, 236, (3, 32, 32), dtype=np.uint8)
        frame = av.VideoFrame.from_ndarray(planes, format='yuv444p')
        if colorMatrix in Colorspace.__members__:
            expected = frame.to_ndarray(
                format='rgb24', src_colorspace=colorMatrix,
                src_color_range='JPEG' if fullRange else 'MPEG')
        else:
            # PyAV before 18 has no name for BT.2020, but goes by a frame
            # tagged with it
            frame.colorspace = movies.frame._SWSCALE_TO_AVCOL_SPC[colorMatrix]
            frame.color_range = 2 if fullRange else 1  # JPEG or MPEG
            expected = frame.to_ndarray(format='rgb24')

        matrix, offset = movies._yuvToRGBUniforms(colorMatrix, fullRange)
        yuv = np.moveaxis(planes, 0, -1) / 255.0
        rgb = (yuv - np.array(offset)) @ np.array(matrix).reshape(3, 3).T
        rgb = np.round(np.clip(rgb, 0.0, 1.0) * 255.0)

        assert np.abs(rgb - expected).max() <= 1

    @pytest.mark.parametrize('colorRange', [1, 2])  # MPEG, JPEG
    @pytest.mark.parametrize('colorspace', [9, 10])  # BT2020_NCL, BT2020_CL
    def test_BT2020FramesConvertedToRGB(self, win, movieLib, colorspace,
                                        colorRange):
        """Frames tagged BT.2020 which are converted to RGB as they're decoded
        (as 10-bit ones are) are converted with BT.2020, whichever PyAV
        version names it or not."""
        if movieLib != 'pyav':
            pytest.skip('only pyav converts frames with their colour matrix')

        import av

        rng = np.random.default_rng(1)
        planes = rng.integers(16, 236, (3, 32, 32), dtype=np.uint8)

        def taggedFrame(tag):
            frame = av.VideoFrame.from_ndarray(planes, format='yuv444p')
            frame.colorspace, frame.color_range = tag, colorRange
            return frame

        # what `swscale` converts BT2020_NCL to, which BT2020_CL is too
        expected = taggedFrame(9).to_ndarray(format='rgba')

        reader = MovieFileReader(str(MOVIE_PATH), decoderLib=movieLib)
        reader.setOutputPixelFormat('rgba')
        reader.open()
        try:
            converted = reader._convertFrameToRGB(taggedFrame(colorspace))
            assert np.array_equal(converted.memview, expected)
        finally:
            reader.close()

    def test_framesUploadedAsYUV(self, win, movieLib):
        """With `pyav`, frames are kept as YUV and drawn from one texture per
        plane, unless turned off with `gpuColorConversion=False`."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')

        with movieStim(win, movieLib) as mov:
            assert mov._player.outputPixelFormat == 'yuv'
            assert isinstance(mov._recentFrameImage, movies._YUVFrameAdapter)
            assert mov._textureLayout[0] == 'yuv'
            assert len(mov._planeTextureIds) == 3

        with movieStim(win, movieLib, gpuColorConversion=False) as mov:
            assert mov._player.outputPixelFormat == 'rgba'
            assert isinstance(
                mov._recentFrameImage, movies.frame._RGBFrameAdapter)
            assert mov._planeTextureIds is None

    @pytest.mark.parametrize('colorspace, colorRange', [
        (1, 1),  # BT.709, limited range
        (6, 2)])  # BT.601, full range
    def test_gpuConversionMatchesCPU(self, win, movieLib, tmp_path,
                                     colorspace, colorRange):
        """Frames drawn through the shader look the same as frames converted
        as they're decoded, using the colour matrix and range the movie is
        tagged with. (Without chroma subsampling, which the two upsample
        differently, see `test_gpuConversionUpsamplesChroma`.)"""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')

        size = (64, 48)
        path = _writeTaggedMovie(
            tmp_path / 'tagged.mkv', 'yuv444p', colorspace, colorRange, size)

        drawn = {}
        for gpu in (True, False):
            with movieStim(win, movieLib, filename=path, units='pix',
                           size=size, gpuColorConversion=gpu) as mov:
                drawn[gpu], _ = _drawToBackBuffer(win, mov)

        region = _movieRegion(win, size)
        difference = np.abs(drawn[True][region] - drawn[False][region])
        assert difference.mean() < 1.0
        assert difference.max() <= 3

    def test_gpuConversionUpsamplesChroma(self, win, movieLib, tmp_path):
        """Subsampled chroma is interpolated up to the size of the luma as
        it's drawn, centred on each pair of pixels."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')
        import av
        import cv2

        size = (64, 48)
        path = _writeTaggedMovie(
            tmp_path / 'tagged.mkv', 'yuv420p', colorspace=1, colorRange=1,
            size=size)

        # what the shader should come out with, from the decoded planes
        with av.open(str(path)) as container:
            frame = next(container.decode(video=0))
            planes = [
                np.frombuffer(plane, np.uint8).reshape(
                    plane.height, plane.line_size)[:, :plane.width]
                for plane in frame.planes]
        upsampled = [planes[0]] + [
            cv2.resize(plane, size, interpolation=cv2.INTER_LINEAR)
            for plane in planes[1:]]
        matrix, offset = movies._yuvToRGBUniforms('ITU709', False)
        yuv = np.stack(upsampled, axis=-1) / 255.0
        expected = np.clip(
            (yuv - np.array(offset)) @ np.array(matrix).reshape(3, 3).T,
            0.0, 1.0) * 255.0

        with movieStim(win, movieLib, filename=path, units='pix',
                       size=size) as mov:
            drawn, _ = _drawToBackBuffer(win, mov)

        region = _movieRegion(win, size)
        difference = np.abs(drawn[region] - expected[2:-2, 2:-2])
        assert difference.mean() < 1.0
        assert difference.max() <= 3

    def test_rgbaConversionUsesFrameMatrix(self, win, movieLib, tmp_path):
        """Frames converted as they're decoded use the colour matrix the movie
        is tagged with, or for an untagged HD movie, BT.709 (where PyAV would
        take it to be BT.601)."""
        if movieLib != 'pyav':
            pytest.skip('only pyav reads the colour matrix')
        import av

        cases = (
            ('untagged HD', 2, (1280, 720), 'ITU709'),
            ('tagged BT.601', 6, (1280, 720), 'ITU601'))
        for name, colorspace, size, colorMatrix in cases:
            path = _writeTaggedMovie(
                tmp_path / '{}.mkv'.format(colorspace), colorspace=colorspace,
                size=size, nFrames=2)
            with av.open(str(path)) as container:
                frame = next(container.decode(video=0))
                expected = frame.to_ndarray(
                    format='rgba', src_colorspace=colorMatrix)

            reader = MovieFileReader(str(path), decoderLib=movieLib)
            reader.open()
            try:
                image = reader._getFrameFromStore(0.0)[0]
                np.testing.assert_array_equal(image.memview, expected, name)
            finally:
                reader.close()

    def test_yuvFramesScaledDown(self, win, movieLib):
        """Frames kept as YUV are still scaled down to the size they're drawn
        at, each plane by as much."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')

        drawnSize = (MOVIE_SIZE[0] // 4, MOVIE_SIZE[1] // 4)
        with movieStim(win, movieLib, size=drawnSize, units='pix') as mov:
            image = mov._recentFrameImage
            assert image.size == drawnSize
            lumaSize = image.planes[0][1:3]
            chromaSize = image.planes[1][1:3]
            assert tuple(lumaSize) == drawnSize
            assert tuple(chromaSize) == tuple(
                (val + 1) // 2 for val in drawnSize)  # the movie is 4:2:0

    def test_otherFormatsConvertedAsDecoded(self, win, movieLib, tmp_path):
        """Frames in a format the shader doesn't take (here greyscale) are
        converted to RGBA as they're decoded instead."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')

        path = _writeTaggedMovie(tmp_path / 'grey.mkv', pixelFormat='gray')
        with movieStim(win, movieLib, filename=path) as mov:
            assert mov._player.outputPixelFormat == 'yuv'
            assert isinstance(
                mov._recentFrameImage, movies.frame._RGBFrameAdapter)
            assert mov._planeTextureIds is None
            mov.draw()

    def test_noShaderConvertsAsDecoded(self, win, movieLib, monkeypatch):
        """Without the shader (where it can't be made), frames are converted
        to RGBA as they're decoded instead."""
        monkeypatch.setattr(movies, '_getYUVToRGBProgram', lambda win: None)

        with movieStim(win, movieLib) as mov:
            assert mov._player.outputPixelFormat == 'rgba'
            assert not isinstance(
                mov._recentFrameImage, movies._YUVFrameAdapter)
            mov.draw()

    @pytest.mark.parametrize('gpu', [True, False])
    def test_frameTextureHoldsRGBAFrame(self, win, movieLib, tmp_path, gpu):
        """`frameTexture` holds the frame as RGBA however frames are converted
        to RGB, top row first, as frames decoded as RGBA always have been."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')
        import av

        size = (64, 48)
        path = _writeTaggedMovie(tmp_path / 'tagged.mkv', size=size)
        with av.open(str(path)) as container:
            frame = next(container.decode(video=0))
            expected = frame.to_ndarray(format='rgba', src_colorspace='ITU709')

        with movieStim(win, movieLib, filename=path, units='pix', size=size,
                       gpuColorConversion=gpu) as mov:
            assert (mov._planeTextureIds is not None) == gpu
            texture = _readTexture(mov.frameTexture, *size)

        difference = np.abs(texture.astype(int) - expected)
        assert difference[..., :3].max() <= 3
        assert np.all(texture[..., 3] == 255)

    def test_frameTextureKeptAsFramesChange(self, win, movieLib):
        """The texture `frameTexture` gives stays the same as the movie plays,
        with each frame converted into it, so that it can be held on to."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')

        with movieStim(win, movieLib, size=(64, 64), units='pix') as mov:
            textureId = mov.frameTexture.value
            first = _readTexture(mov.frameTexture, 64, 64)

            mov.play()
            _drawFrames(win, mov, count=10, interval=0.02)

            assert mov.frameTexture.value == textureId
            assert np.any(_readTexture(mov.frameTexture, 64, 64) != first)

    @pytest.mark.parametrize('useFBO', [False, True])
    def test_conversionLeavesGLStateAlone(self, movieLib, useFBO):
        """Converting a frame into `frameTexture` puts back everything about
        the GL state it changes, including the framebuffer bound, which with
        `useFBO=True` is the window's own."""
        if movieLib != 'pyav':
            pytest.skip('only pyav keeps frames as YUV')

        fboWin = visual.Window(
            [128, 128], winType='pyglet', allowGUI=False, autoLog=False,
            useFBO=useFBO)
        try:
            with movieStim(fboWin, movieLib) as mov:
                assert mov._planeTextureIds is not None
                before = _glState()
                mov._pixelTransfer(forceRefresh=True)  # converts it again
                assert _glState() == before
                if useFBO:
                    assert before['GL_FRAMEBUFFER_BINDING'] != 0

                # and draws the same as converting it as it's decoded
                drawnGPU, _ = _drawToBackBuffer(fboWin, mov)
            with movieStim(fboWin, movieLib, gpuColorConversion=False) as mov:
                drawnCPU, _ = _drawToBackBuffer(fboWin, mov)
        finally:
            fboWin.close()

        assert np.abs(drawnGPU - drawnCPU).mean() < 3.0


class TestMovieStimFrameTexture:
    """Tests for keeping `frameTexture` up to date."""

    @staticmethod
    def _frameTexture(mov):
        return _readTexture(mov.frameTexture, mov._vidWidth, mov._vidHeight)

    def test_updateVideoFrameUpdatesFrameTexture(self, win, movieLib):
        """`updateVideoFrame()` keeps `frameTexture` up to date without the
        movie being drawn."""
        with movieStim(win, movieLib) as mov:
            first = self._frameTexture(mov)
            mov.play()

            for _ in range(15):
                win.flip()  # without drawing the movie
                time.sleep(0.02)
                assert mov.updateVideoFrame()

            assert mov.pts > 0.0
            assert np.any(self._frameTexture(mov) != first)

    @pytest.mark.parametrize('started', [False, True])
    def test_seekWhilePausedUpdatesFrameTexture(self, win, movieLib, started):
        """Seeking while paused (or before playing) shows the frame sought to,
        and puts it in `frameTexture`, rather than waiting for playback to
        start."""
        with movieStim(win, movieLib) as mov:
            if started:
                mov.play()
                _drawFrames(win, mov)
                mov.pause()

            before = self._frameTexture(mov)
            mov.seek(SAMPLE_LATE)
            after = self._frameTexture(mov)
            assert np.any(after != before)

            # drawn as it is, and staying put while paused
            _drawFrames(win, mov, count=3, interval=0.02)
            np.testing.assert_array_equal(self._frameTexture(mov), after)
