#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `psychopy.visual.MovieStim` video decoding and playback.

These tests run against every decoder backend which is importable in the
current environment, so that the backends stay behaviourally interchangeable.

Audio is disabled throughout. These tests cover the video side of `MovieStim`,
and extracting an audio track needs a working output device which test machines
often lack.

"""
import time
from pathlib import Path
from contextlib import contextmanager

import numpy as np
import pytest

from psychopy import visual, prefs
from psychopy.visual.movies import MovieFileReader
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
            ('ffpyplayer', 'ffpyplayer'),
            ('pyav', 'av'),
            ('opencv', 'cv2')):
        try:
            __import__(moduleName)
        except ImportError:
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
            # three bytes per pixel, RGB24
            assert frame.size == MOVIE_SIZE[0] * MOVIE_SIZE[1] * 3
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
