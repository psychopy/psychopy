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
