#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from packaging.version import Version
import psychopy.data

######### Begin Compatibility Class Definitions #########


class _oldStyleBaseTrialHandler():
    """Please excuse these ugly kluges, but in order to unpickle
        psydat pickled trial handlers that were created using the old-style
        (pre python 2.2) class, original classes have to be defined.
    """
    pass


class _oldStyleBaseStairHandler():
    """Stubbed compapatibility class for StairHandler"""
    pass


class _oldStyleTrialHandler():
    """Stubbed compapatibility class for TrialHandler"""
    pass


class _oldStyleStairHandler():
    """Stubbed compapatibility class for StairHandler"""
    pass


class _oldStyleMultiStairHandler():
    """Stubbed compapatibility class for MultiStairHandler"""
    pass
######### End Compatibility Class Definitions #########


def _convertToNewStyle(newClass, oldInstance):
    """Converts un-pickled old-style compatibility classes to new-style ones
       by initializing a new-style class and copying the old compatibility
       instance's attributes.
    """
    # if the oldInstance was an ExperimentHandler it wouldn't throw an error
    # related to itself, but to the underlying loops within it. So check if we
    # have that and then do imports on each loop
    if oldInstance.__class__.__name__ == 'ExperimentHandler':
        newHandler = psychopy.data.ExperimentHandler()
        # newClass()  # Init a new new-style object
    else:
        newHandler = newClass([], 0)  # Init a new new-style object
    for thisAttrib in dir(oldInstance):
        # can handle each attribute differently
        if 'instancemethod' in str(type(getattr(oldInstance, thisAttrib))):
            # this is a method
            continue
        elif thisAttrib == '__weakref__':
            continue
        else:
            value = getattr(oldInstance, thisAttrib)
            setattr(newHandler, thisAttrib, value)
    return newHandler


def checkCompatibility(old, new, prefs=None, fix=True):
    """Check for known compatibility issue between a pair of versions and fix
    automatically if possible. (This facility, and storing the most recently
    run version of the app, was added in version 1.74.00)

    usage::

        ok, msg =  checkCompatibility(old, new, prefs, fix=True)

    prefs is a standard psychopy preferences object. It isn't needed by all
    checks but may be useful.
    This function can be used simply to check for issues by setting fix=False
    """
    if old == new:
        return 1, ""  # no action needed
    if old > new:  # switch them over
        old, new = new, old

    msg = "From %s to %s:" % (old, new)
    warning = False
    if old[0:4] < '1.74':
        msg += ("\n\nThere were many changes in version 1.74.00 that will "
                "break\ncompatibility with older versions. Make sure you read"
                " the changelog carefully\nbefore using this version. Do not "
                "upgrade to this version halfway through an experiment.\n")
        if fix and 'PatchComponent' not in prefs.builder['hiddenComponents']:
            prefs.builder['hiddenComponents'].append('PatchComponent')
        warning = True
    if not warning:
        msg += "\nNo known compatibility issues"

    return (not warning), msg


def checkUpdatesInfo(old, new):
    """
    Checks whether we need to display information from a new update, e.g. introducing a new feature.

    Parameters
    ----------
    old : str or packaging.version.Version
        Last version which was opened
    new : str or packaging.version.Version
        Current version
    prefs : psychopy.preferences.Preferences
        Preferences for the app

    Returns
    -------
    list[str]
        List of strings with markdown content for relevant updates
    """
    from psychopy.preferences import prefs
    # make sure both versions are Version objects
    if isinstance(old, str):
        old = Version(old)
    if isinstance(new, str):
        new = Version(new)
    # start off with no messages
    messages = []
    # if not a new version, no action needed
    if old >= new:
        return messages
    # find changes folder
    changesDir = Path(prefs.paths['psychopy']) / "changes"
    # if it is a new version, check for updates
    for file in changesDir.glob("*.md"):
        # try to Version-ise target
        try:
            target = Version(file.stem)
        except (TypeError, ValueError):
            # skip if it fails
            continue
        # have we just crossed the target version?
        if old < target < new:
            # load the markdown file
            msg = file.read_text(encoding="utf-8")
            # add its contents to messages array
            messages.append(msg)
    # reverse messages so they go from most-to-least recent
    messages.reverse()

    return messages
