import pytest

from psychopy import experiment
from psychopy.experiment.components.movie import MovieComponent


def _compileMovieExperiment(updates='constant', **params):
    """Compile an experiment with one Routine holding one Movie Component,
    made with the params given and its movie file set to update as given, to
    a Python script."""
    exp = experiment.Experiment()
    exp.name = "TestMovieComponentExp"
    rt = exp.addRoutine(routineName='trial')
    exp.flow.addRoutine(rt, 0)
    comp = MovieComponent(
        exp=exp, parentName='trial', name='movie', movie='movie.mp4',
        **params)
    comp.params['movie'].updates = updates
    rt.append(comp)

    return comp, exp.writeScript(target="PsychoPy")


class TestMovieComponent:

    def test_defaultBackendIsPyAV(self):
        """New Movie Components play their movie with PyAV, the one decoder
        library sure to be installed (`ffpyplayer` has no wheels for newer
        Python versions)."""
        comp, script = _compileMovieExperiment()

        assert comp.params['backend'].val == 'pyav'
        assert 'pyav' in comp.params['backend'].allowedVals
        assert "movieLib='pyav'" in script

    @pytest.mark.parametrize('updates', ['constant', 'set every repeat'])
    @pytest.mark.parametrize('backend', ['pyav', 'opencv'])
    def test_backendCompilesToMovieStim(self, backend, updates):
        """Each backend `MovieStim` supports compiles to a `MovieStim` using
        it, rather than to one of the movie classes which have since moved
        out to the `psychopy-legacy` plugin, or to one using another
        backend."""
        _, script = _compileMovieExperiment(updates=updates, backend=backend)

        assert "MovieStim2" not in script
        assert "MovieStim3" not in script
        assert "movie = visual.MovieStim(" in script
        assert "movieLib='{}'".format(backend) in script
        if updates == 'set every repeat':
            # one stimulus, given the movie for each repeat as it starts
            assert script.count("visual.MovieStim(") == 1
            assert "movie.setMovie(" in script
