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

    def test_hardwareDecodingOffByDefault(self):
        """Movies are decoded in software unless asked otherwise, and scripts
        are then written as they were before the option existed."""
        comp, script = _compileMovieExperiment()

        assert comp.params['hardwareDecoding'].val is False
        assert 'hardwareDecoding' not in script

    @pytest.mark.parametrize('value', [True, 'True'])
    def test_hardwareDecodingCompiles(self, value):
        """Asking for hardware decoding (as set in Builder, or loaded from an
        experiment file as text) is passed on to `MovieStim`, in a script
        which compiles."""
        _, script = _compileMovieExperiment(hardwareDecoding=value)

        assert "hardwareDecoding=True" in script
        compile(script, 'TestMovieComponentExp.py', 'exec')

    @pytest.mark.parametrize('value', [False, 'False'])
    def test_hardwareDecodingOff(self, value):
        """Hardware decoding turned off, including as text from an experiment
        file, leaves it out."""
        _, script = _compileMovieExperiment(hardwareDecoding=value)

        assert 'hardwareDecoding' not in script

    def test_hardwareDecodingOnlyWithPyAV(self):
        """Hardware decoding is only shown for, and passed on with, the PyAV
        backend, the only one which does it."""
        comp, script = _compileMovieExperiment(
            backend='opencv', hardwareDecoding=True)

        assert 'hardwareDecoding' not in script
        assert {"dependsOn": "backend", "condition": "in ['pyav']",
                "param": "hardwareDecoding", "true": "show",
                "false": "hide"} in comp.depends

    def test_hardwareDecodingBackendsMatchReaders(self):
        """The backends the option is shown for are those whose readers
        decode with hardware (which the component doesn't import, see
        `HARDWARE_DECODING_BACKENDS`)."""
        from psychopy.experiment.components import movie
        from psychopy.visual import movies

        assert list(movie.HARDWARE_DECODING_BACKENDS) == \
            movies.hardwareDecodingBackends()

    def test_hardwareDecodingSavedAndLoaded(self, tmp_path):
        """The setting is kept in the experiment file, and experiments saved
        before it existed load with it off."""
        comp, _ = _compileMovieExperiment(hardwareDecoding=True)
        path = tmp_path / 'withSetting.psyexp'
        comp.exp.saveToXML(str(path))

        exp = experiment.Experiment()
        exp.loadFromXML(str(path))
        loaded = exp.routines['trial'].getComponentFromName('movie')
        assert loaded.params['hardwareDecoding']
        assert "hardwareDecoding=True" in exp.writeScript(target="PsychoPy")

        # as written before the setting existed
        text = path.read_text(encoding='utf-8')
        at = text.index('name="hardwareDecoding"')
        start = text.rindex('<Param', 0, at)
        end = text.index('/>', at) + 2
        path.write_text(text[:start] + text[end:], encoding='utf-8')
        assert 'hardwareDecoding' not in path.read_text(encoding='utf-8')
        exp = experiment.Experiment()
        exp.loadFromXML(str(path))
        loaded = exp.routines['trial'].getComponentFromName('movie')
        assert not loaded.params['hardwareDecoding']
        assert 'hardwareDecoding' not in exp.writeScript(target="PsychoPy")
