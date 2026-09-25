import importlib
import weakref
from copy import copy
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from psychopy import visual, colors, core
from psychopy.tests import utils
from psychopy.tests.test_visual.test_basevisual import _TestColorMixin
from psychopy.tools.stimulustools import serialize
from psychopy import colors

from psychopy.visual.window import OpenWinList


# Colours the captured triangle cycles through. Any two of them differ by at
# least half the range in some channel, so a frame which came back out of
# order, duplicated or missing is unmistakable even after a lossy codec.
CAPTURE_COLORS = ('red', 'green', 'blue', 'yellow', 'magenta', 'cyan')

# How far a decoded pixel may sit from the colour that was drawn. Encoding to
# H.264 moves a solid patch by a value or two, so this is loose enough for the
# codec while staying far tighter than the gap between any two of the colours
# above.
COLOR_TOL = 16


def _decodeMovieFrames(filename):
    """Decode every frame of a movie file.

    Read with PyAV directly rather than through `MovieStim`, so that what
    reached the file is established independently of the playback path which
    the same test goes on to exercise.

    Parameters
    ----------
    filename : str or Path
        Movie file to read.

    Returns
    -------
    list
        One 8-bit `(height, width, 3)` RGB array per frame, in the order they
        are played back in.

    """
    import av

    frames = []
    with av.open(str(filename)) as container:
        for frame in container.decode(video=0):
            frames.append(frame.to_ndarray(format='rgb24'))

    return frames


def _assertCenterColor(frame, colorName, context):
    """Check the middle of a captured frame is the colour drawn there.

    The triangle is centred on the window and covers the middle pixel, so that
    pixel says which of `CAPTURE_COLORS` the frame was drawn in.

    Parameters
    ----------
    frame : numpy.ndarray
        Frame as an 8-bit `(height, width, 3)` RGB array.
    colorName : str
        Name of the colour the triangle was drawn in.
    context : str
        Included in the failure message to say which frame is at fault.

    """
    height, width = frame.shape[:2]
    center = frame[height // 2, width // 2].astype(int)
    expected = np.asarray(
        colors.Color(colorName, 'named').rgb255, dtype=int)

    assert np.abs(center - expected).max() <= COLOR_TOL, (
        "{}: expected a {} triangle (RGB {}) but the middle of the frame is "
        "RGB {}".format(
            context, colorName,
            tuple(int(val) for val in expected),
            tuple(int(val) for val in center)))


class _DummyWin:
    """Stand-in for a Window, so these tests need no GL context."""


class TestOpenWinList:
    def test_append(self):
        winList = OpenWinList()
        win = _DummyWin()
        winList.append(win)
        # the window is stored as a weak reference, not by value
        assert isinstance(winList[0], weakref.ref)
        assert winList[0]() is win

    def test_append_keeps_order(self):
        """Consumers treat `openWindows[0]` as the primary window."""
        winList = OpenWinList()
        wins = [_DummyWin() for _ in range(3)]
        for win in wins:
            winList.append(win)
        assert [ref() for ref in winList] == wins

    def test_append_does_not_keep_win_alive(self):
        """The whole point of the weak references: appending must not pin
        the window in memory.

        """
        winList = OpenWinList()
        win = _DummyWin()
        finalized = []
        weakref.finalize(win, finalized.append, True)
        winList.append(win)
        del win  # list holds the only remaining reference
        assert finalized == [True]
        assert winList[0]() is None

    def test_remove(self):
        winList = OpenWinList()
        first, second = _DummyWin(), _DummyWin()
        winList.append(first)
        winList.append(second)
        winList.remove(first)
        # only `first` should be gone
        assert [ref() for ref in winList] == [second]

    def test_remove_after_dead_ref(self):
        """A dead reference earlier in the list must not mask the removal."""
        winList = OpenWinList()
        dead, target = _DummyWin(), _DummyWin()
        winList.append(dead)
        winList.append(target)
        del dead  # first entry is now a dead weakref
        winList.remove(target)
        # the dead ref is purged and the target is deregistered
        assert list(winList) == []

    def test_remove_purges_dead_refs(self):
        winList = OpenWinList()
        deadFirst, deadSecond, keep = _DummyWin(), _DummyWin(), _DummyWin()
        for win in (deadFirst, deadSecond, keep):
            winList.append(win)
        del deadFirst, deadSecond
        # removing a window which was never added still purges dead refs
        winList.remove(_DummyWin())
        assert [ref() for ref in winList] == [keep]


class TestWindow:
    def test_serialization(self):
        # make window
        win = visual.Window()
        try:
            # serialize window
            params = serialize(win, includeClass=True)
            # get class
            mod = importlib.import_module(params.pop('__module__'))
            cls = getattr(mod, params.pop('__class__'))
            # check class is Window
            assert isinstance(win, cls)
            # recreate win from params
            dupe = cls(**params)
            # delete duplicate
            dupe.close()
        finally:
            win.close()

    def test_background_image_fit(self):
        _baseCases = [
            # no fitting
            {"fit": None, "image": "default.png",
             "sizes": {'wide': 256, 'tall': 256, 'large': 256, 'small': 256}},
            # cover
            {"fit": "cover", "image": "default.png",
             "sizes": {'wide': 500, 'tall': 500, 'large': 500, 'small': 200}},
            # contain
            {"fit": "contain", "image": "default.png",
             "sizes": {'wide': 200, 'tall': 200, 'large': 500, 'small': 200}},
            # fill
            {"fit": "fill", "image": "default.png",
             "sizes": {'wide': "fill", 'tall': "fill", 'large': 500, 'small': 200}},
            # scaleDown
            {"fit": "scaleDown", "image": "default.png",
             "sizes": {'wide': 200, 'tall': 200, 'large': 256, 'small': 200}},

        ]
        cases = []
        # Create version of each case with different units
        for units in ["pix", "height", "norm"]:
            theseCases = copy(_baseCases)
            for case in theseCases:
                case['units'] = units
                cases.append(case)
        # Additional level of variation: window sizes
        sizes = {
            "wide": (500, 200),
            "tall": (200, 500),
            "large": (500, 500),
            "small": (200, 200),
        }

        for sizeTag, size in sizes.items():
            win = visual.Window(size=size)
            try:
                for case in cases:
                    # Set image and fit
                    win.backgroundFit = case['fit']
                    win.backgroundImage = case['image']
                    win.flip()
                    # Compare
                    imgName = Path(case['image']).stem
                    filename = f"test_win_bg_{sizeTag}_{case['sizes'][sizeTag]}_{imgName}.png"
                    # win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                    try:
                        utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, win, crit=7)
                    except AssertionError as err:
                        raise AssertionError(f"Window did not look as expected when:\n"
                                             f"backgroundImage={case['image']},\n"
                                             f"backgroundFit={case['fit']},\n"
                                             f"size={sizeTag},\n"
                                             f"units={case['units']}\n"
                                             f"\n"
                                             f"Original error:"
                                             f"{err}")
            finally:
                # Close
                win.close()

    def test_win_color_with_image(self):
        """
        Test that the window color is still visible under the background image
        """
        cases = [
            "red",
            "blue",
            "green",
        ]

        win = visual.Window(size=(200, 200), backgroundImage="default.png", backgroundFit="contain")
        try:
            for case in cases:
                # Set window color
                win.color = case
                # Draw with background
                win.flip()
                # Check
                filename = f"test_win_bgcolor_{case}.png"
                # win.getMovieFrame(buffer='back').save(Path(utils.TESTS_DATA_PATH) / filename)
                utils.compareScreenshot(Path(utils.TESTS_DATA_PATH) / filename, win, crit=10)
        finally:
            win.close()

    def test_window_colors(self):
        win = visual.Window(size=(200, 200))

        try:
            for case in _TestColorMixin.colorTykes + _TestColorMixin.colorExemplars:
                # Go through all TestColorMixin cases
                for colorSpace, color in case.items():
                    # Make color to compare against
                    target = colors.Color(color, colorSpace)
                    # Set each colorspace/color combo
                    win.colorSpace = colorSpace
                    win.color = color
                    win.flip()
                    # Check that the middle pixel is this color
                    utils.comparePixelColor(
                        win, target,
                        coord=(0, 0),
                        context=f"win_{color}_{colorSpace}")
        finally:
            win.close()


class TestWindowMovieFrames:
    """Grabbing frames from a window and writing them to disk.

    A triangle is redrawn in a different colour on every frame, so that the
    frames which reach the file can be told apart and put in order. That is
    what makes it possible to say whether every captured frame was written,
    rather than only whether the file has some frames in it.

    """
    WIN_SIZE = (128, 128)
    N_FRAMES = 12
    FPS = 30

    @pytest.fixture(scope='class')
    def captureWin(self):
        """Window the image tests capture from.

        Shared rather than opened per test, both because opening a window is
        slow and because the tests which use it only need somewhere to draw;
        each clears the captured frames as it starts, so they stay independent
        of one another. The movie test opens its own, since it has to close the
        window it captured from.

        """
        win = visual.Window(
            size=self.WIN_SIZE, allowGUI=False, autoLog=False, color='black')
        yield win
        win.close()

    def _captureColorCycle(self, win, nFrames):
        """Draw a triangle in a new colour each frame, capturing every one.

        Parameters
        ----------
        win : psychopy.visual.Window
            Window to draw into and capture from.
        nFrames : int
            Number of frames to draw and capture.

        Returns
        -------
        list
            Name of the colour drawn on each frame, in the order drawn.

        """
        triangle = visual.Polygon(win, edges=3, radius=0.7, autoLog=False)

        win.movieFrames = []  # anything a previous test left behind

        drawn = []
        for n in range(nFrames):
            color = CAPTURE_COLORS[n % len(CAPTURE_COLORS)]
            triangle.fillColor = color
            triangle.draw()
            # Captured before the flip, which is where the frame just drawn
            # still is. Flipping first would leave the back buffer cleared and
            # every captured frame identical.
            win.getMovieFrame(buffer='back')
            drawn.append(color)
            win.flip()

        return drawn

    def test_saveSingleFrameAsImage(self, captureWin, tmp_path):
        """A single captured frame is written as one image file.

        `saveMovieFrames()` only writes one file when one frame was captured;
        with more on the stack it numbers them instead, which
        `test_saveFramesAsImageSequence` covers.

        """
        imageFile = tmp_path / 'frame.png'

        drawn = self._captureColorCycle(captureWin, 1)
        assert len(captureWin.movieFrames) == 1

        captureWin.saveMovieFrames(str(imageFile))

        # the stack is emptied once the frames have been written
        assert captureWin.movieFrames == []

        assert imageFile.is_file(), "no image was written to {}".format(
            imageFile)

        with Image.open(imageFile) as image:
            assert image.size == self.WIN_SIZE
            frame = np.asarray(image.convert('RGB'))

        _assertCenterColor(frame, drawn[0], 'the saved image')

    def test_saveFramesAsImageSequence(self, captureWin, tmp_path):
        """Several captured frames are written as numbered image files."""
        drawn = self._captureColorCycle(captureWin, self.N_FRAMES)
        captureWin.saveMovieFrames(str(tmp_path / 'frame.png'))

        written = sorted(tmp_path.glob('frame*.png'))
        assert len(written) == self.N_FRAMES, (
            "captured {} frames but {} image(s) were written".format(
                self.N_FRAMES, len(written)))

        # the numbering runs in the order the frames were captured
        for frameN, (imageFile, color) in enumerate(zip(written, drawn)):
            with Image.open(imageFile) as image:
                assert image.size == self.WIN_SIZE
                frame = np.asarray(image.convert('RGB'))

            _assertCenterColor(frame, color, 'image {}'.format(imageFile.name))

    def test_saveFramesAsMovieAndPlayBack(self, tmp_path):
        """Captured frames are written as a movie which plays back from disk.

        Every frame captured must reach the file: a writer which dropped or
        repeated frames would still produce a playable movie, so the frames are
        counted and their colours checked against the order they were drawn in.
        The movie is then played back with a `MovieStim`, with the window which
        recorded it closed, so that what is on screen can only have come off
        the disk.

        """
        movieFile = tmp_path / 'movie.mp4'

        # The playback window is opened first so that the capture window can be
        # closed before playback begins. Only the capture window has to be gone
        # for the movie to be coming off the disk, and opening a window once
        # every window has been closed tears down and rebuilds the GL context,
        # which is fragile across backends.
        playbackWin = visual.Window(
            size=self.WIN_SIZE, allowGUI=False, autoLog=False)
        try:
            captureWin = visual.Window(
                size=self.WIN_SIZE, allowGUI=False, autoLog=False,
                color='black')
            try:
                drawn = self._captureColorCycle(captureWin, self.N_FRAMES)
                assert len(captureWin.movieFrames) == self.N_FRAMES

                captureWin.saveMovieFrames(str(movieFile), fps=self.FPS)
            finally:
                captureWin.close()

            assert movieFile.is_file(), "no movie was written to {}".format(
                movieFile)

            # --- what actually reached the file ---
            frames = _decodeMovieFrames(movieFile)

            assert len(frames) == self.N_FRAMES, (
                "captured {} frames but the movie holds {}".format(
                    self.N_FRAMES, len(frames)))

            for frameN, (frame, color) in enumerate(zip(frames, drawn)):
                assert frame.shape[:2] == self.WIN_SIZE[::-1], (
                    "frame {} is {} rather than the window's {}".format(
                        frameN, frame.shape[:2], self.WIN_SIZE[::-1]))
                _assertCenterColor(
                    frame, color, 'frame {} of the movie'.format(frameN))

            # --- playing it back ---
            movie = visual.MovieStim(
                playbackWin, str(movieFile), noAudio=True, autoStart=False,
                loop=False, size=self.WIN_SIZE, autoLog=False)
            try:
                assert tuple(movie.frameSize) == self.WIN_SIZE
                assert movie.duration == pytest.approx(
                    self.N_FRAMES / self.FPS, abs=1.0 / self.FPS)

                movie.play()

                # Drawn until the movie runs out rather than a fixed number of
                # times. Playback advances with wall-clock time, not with
                # flips, and without vsync (e.g. under Xvfb) flips return
                # immediately, so any fixed number of them can be over before
                # the movie is. The loop is bounded by time instead, with some
                # slack for the decoder starting up on a slow machine.
                deadline = core.getTime() + movie.duration + 5.0
                while not movie.isFinished and core.getTime() < deadline:
                    movie.draw()
                    playbackWin.flip()

                assert movie.isFinished, (
                    "the movie did not play through to the end")
            finally:
                movie.unload()
        finally:
            playbackWin.close()

