import os
import pytest
from psychopy import visual
from psychopy.tests import utils


def test_moviestim_stop_and_unload():
    """Test that MovieStim.stop() and unload() cleanly manage player resources without AttributeError (#7793)."""
    movie_path = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
    if not os.path.exists(movie_path):
        pytest.skip(f"Test movie {movie_path} not found")

    win = visual.Window([128, 128], pos=[50, 50], allowGUI=False, autoLog=False)
    try:
        stim = visual.MovieStim(win, movie_path, noAudio=True)
        assert stim._isLoaded
        stim.play()
        assert stim.isPlaying

        # stop() reloads the movie after fully unloading the player
        stim.stop()
        assert stim._isLoaded
        assert not stim.isPlaying

        # unload() explicitly tears down the player and texture buffers
        stim.unload()
        assert not stim._isLoaded
    finally:
        win.close()


def test_moviestim_decoder_returns_no_frame():
    """Test that MovieStim keeps the last frame instead of raising when the
    decoder doesn't return a frame in time, which FFPyPlayer does near the end
    of a stream before reporting 'eof' (#7835)."""
    movie_path = os.path.join(utils.TESTS_DATA_PATH, 'testMovie.mp4')
    if not os.path.exists(movie_path):
        pytest.skip(f"Test movie {movie_path} not found")

    class _StalledPlayer:
        """Stands in for an FFPyPlayer `MediaPlayer` that has no frame ready."""
        def get_frame(self, *args, **kwargs):
            return None, 0.0

    win = visual.Window([128, 128], pos=[50, 50], allowGUI=False, autoLog=False)
    try:
        stim = visual.MovieStim(win, movie_path, noAudio=True)
        reader = stim._player
        realPlayer = reader._player
        reader._player = _StalledPlayer()
        try:
            # request a frame past the last one in the store
            assert reader.getFrame(stim.duration) is None
        finally:
            reader._player = realPlayer
    finally:
        win.close()
