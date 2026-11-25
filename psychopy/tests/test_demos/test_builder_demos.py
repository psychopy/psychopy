from pathlib import Path

import pytest

from psychopy.demos import builder
from psychopy import experiment
from psychopy.experiment.routines import Routine
from psychopy.experiment.components.unknown import UnknownComponent
from psychopy.experiment.routines.unknown import UnknownRoutine
from psychopy.tests.utils import checkSyntax

# root Builder demos folder
_demosDir = Path(builder.__file__).parent


def test_plugin_components_indicated():
    """
    Test that all components in Builder demos which come from plugins are marked as being from plugins.
    """
    # blank experiment for reading files
    exp = experiment.Experiment()
    # root Builder demos folder
    demosDir = Path(builder.__file__).parent
    # for all psyexp files in builder demos folder...
    for file in demosDir.glob("**/*.psyexp"):
        # load experiment
        exp.loadFromXML(str(file))
        # get all elements (Components and StandaloneRoutines) in the experiment
        emts = []
        for rt in exp.routines.values():
            if isinstance(rt, Routine):
                for comp in rt:
                    emts.append(comp)
            else:
                emts.append(rt)
        # check that each element is known
        for emt in emts:
            assert not isinstance(emt, (UnknownComponent, UnknownRoutine)), (
                f"Component/Routine `{emt.name}` ({type(emt).__name__}) from `{file.relative_to(demosDir)}` is "
                f"not known to PsychoPy and experiment file did not indicate that it's from a plugin."
            )


def test_pilot_mode():
    """
    Checks that all Builder demos are saved in Pilot mode.
    """
    # root Builder demos folder
    demosDir = Path(builder.__file__).parent
    # for all psyexp files in builder demos folder...
    for file in demosDir.glob("*/*/*.psyexp"):
        # load experiment
        exp = experiment.Experiment.fromFile(file)
        # check piloting mode param
        assert exp.settings.params['runMode'] == "0", (
            "Builder demos should be saved in Pilot mode, so that they start off piloting when "
            "users unpack them. Please change run mode on {}".format(file.name)
        )


def _checkLoaded(exp, file):
    """
    Check that a loaded experiment has a populated namespace with no collisions and writes valid
    Python syntax.
    """
    assert len(exp.namespace.user), f"No names in namespace after loading `{file}`"
    collisions = exp.namespace.getCollisions()
    assert not collisions, f"Namespace collisions after loading `{file}`: {collisions}"
    checkSyntax(exp, targets=("PsychoPy",))


@pytest.mark.parametrize(
    "file",
    sorted(_demosDir.glob("**/*.psyexp")),
    ids=lambda f: f.relative_to(_demosDir).as_posix(),
)
def test_load_save_compile(file, tmp_path):
    """
    Checks that a Builder demo loads with a valid namespace and writes valid Python syntax, and
    still does after being saved and reloaded.
    """
    # load experiment and check it
    exp = experiment.Experiment.fromFile(file)
    _checkLoaded(exp, file)
    # save it to a temp file
    resaved = tmp_path / file.name
    exp.saveToXML(str(resaved), makeLegacy=False)
    # reload and check again
    exp2 = experiment.Experiment.fromFile(resaved)
    _checkLoaded(exp2, resaved)
