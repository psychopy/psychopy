from importlib import import_module

from ._base import BaseStandaloneRoutine, Routine
from .unknown import UnknownRoutine
from pathlib import Path


def getAllStandaloneRoutines(fetchIcons=True):
    # Safe import all modules within this folder (apart from protected ones with a _)
    for loc in Path(__file__).parent.glob("*"):
        if loc.is_dir() and not loc.name.startswith("_"):
            import_module("." + loc.name, package="psychopy.experiment.routines")
    # Get list of subclasses of BaseStandalone
    classList = BaseStandaloneRoutine.__subclasses__()
    # Remove unknown
    #if UnknownRoutine in classList:
    #    classList.remove(UnknownRoutine)
    # Get list indexed by class name with Routine removed
    classDict = {c.__name__: c for c in classList}

    return classDict
