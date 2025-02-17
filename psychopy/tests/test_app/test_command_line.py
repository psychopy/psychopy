"""
Test that PsychoPy can be initialised from the command line with all API options
"""
import sys
import time
from pathlib import Path
from psychopy import core
from psychopy.tests import utils
        

def test_version_query():
    """
    Check that we can call the PsychoPy app with -v to get the version
    """
    from psychopy import __version__ as ppyVersion
    cases = [
        "-v",
        "--version",
    ]
    for case in cases:
        stderr = core.shellCall(
            [sys.executable, "-m", "psychopy.app", case],
            stderr=True
        )
        assert ppyVersion in "\n".join(stderr)


def test_help_query():
    """
    Check that we can call the PsychoPy app with -h to get the help text
    """
    cases = [
        "-h",
        "--help",
    ]
    for case in cases:
        stderr = core.shellCall(
            [sys.executable, "-m", "psychopy.app", case],
            stderr=True
        )
        assert "PsychoPy" in "\n".join(stderr)


def test_direct_run():
    """
    Check that we can directly run files by invoking psychopy.app with -x
    """
    cases = [
        {'tag': "-x", 'files': [str(Path(utils.TESTS_DATA_PATH) / "ghost_stroop.psyexp")]},
        {'tag': "-x", 'files': [str(Path(utils.TESTS_DATA_PATH) / "test_basic_run.py")]},
        {'tag': "-x", 'files': [
            str(Path(utils.TESTS_DATA_PATH) / "ghost_stroop.psyexp"),
            str(Path(utils.TESTS_DATA_PATH) / "test_basic_run.py")
        ]},
    ]
    # include --direct too
    for case in cases.copy():
        case['tag'] = "--direct"
        cases.append(case)
    # run all cases
    for case in cases:
        stderr = core.shellCall(
            [sys.executable, "-m", "psychopy.app", case['tag']] + case['files'],
            stderr=True
        )