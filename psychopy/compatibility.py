#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

# from future import standard_library
# standard_library.install_aliases()
from builtins import str
from builtins import object
import codecs
import pickle
import psychopy.data

######### Begin Compatibility Class Definitions #########


class _oldStyleBaseTrialHandler(object):
    """Please excuse these ugly kluges, but in order to unpickle
        psydat pickled trial handlers that were created using the old-style
        (pre python 2.2) class, original classes have to be defined.
    """
    pass


class _oldStyleBaseStairHandler(object):
    """Stubbed compapatibility class for StairHandler"""
    pass


class _oldStyleTrialHandler(object):
    """Stubbed compapatibility class for TrialHandler"""
    pass


class _oldStyleStairHandler(object):
    """Stubbed compapatibility class for StairHandler"""
    pass


class _oldStyleMultiStairHandler(object):
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


def fromFile(filename):
    """In order to switch experiment handler to the new-style
    (post-python 2.2, circa 2001) classes, this is a proof-of-concept loader
    based on tools.filetools.fromFile that will load psydat files created
    with either new or old style TrialHandlers or StairHandlers.

    Since this is really just an example, it probably [hopefully] won't be
    incorporated into upstream code, but it will work.

    The method will try to load the file using a normal new-style Pickle
    loader; however, if a type error occurs it will temporarily replace the
    new-style class with a stubbed version of the old-style class and will
    then instantiate a fresh new-style class with the original attributes.
    """
    with codecs.open(filename, 'rb') as f:
        try:
            # Try to load the psydat file into the new-style class.
            contents = pickle.load(f)
        except TypeError as e:
            f.seek(0)
            # check er as string for one of our handlers
            errStr = "{}".format(e)
            name = ''
            for thisHandler in ['TrialHandler','StairHandler','MultiStairHandler']:
                if thisHandler in errStr:
                    name = thisHandler
            # if error is from something else try to deduce the class
            if not name:
                name = e.args[1].__name__
            # then process accordingly
            if name == 'TrialHandler':
                currentHandler = psychopy.data.TrialHandler
                # Temporarily replace new-style class
                psychopy.data.TrialHandler = _oldStyleTrialHandler
                oldContents = pickle.load(f)
                psychopy.data.TrialHandler = currentHandler
                contents = _convertToNewStyle(psychopy.data.TrialHandler,
                                              oldContents)
            elif name == 'StairHandler':
                currentHandler = psychopy.data.StairHandler
                # Temporarily replace new-style class
                psychopy.data.StairHandler = _oldStyleStairHandler
                oldContents = pickle.load(f)
                psychopy.data.StairHandler = currentHandler
                contents = _convertToNewStyle(
                    psychopy.data.StairHandler, oldContents)
            elif name == '':
                newStair = psychopy.data.StairHandler
                newMulti = psychopy.data.MultiStairHandler
                # Temporarily replace new-style class
                psychopy.data.StairHandler = _oldStyleStairHandler
                # Temporarily replace new-style class
                psychopy.data.MultiStairHandler = _oldStyleMultiStairHandler
                oldContents = pickle.load(f)
                psychopy.data.MultiStairHandler = newMulti
                # Temporarily replace new-style class:
                psychopy.data.StairHandler = newStair
                contents = _convertToNewStyle(
                    psychopy.data.MultiStairHandler, oldContents)
            else:
                raise TypeError("Didn't recognize %s" % name)
    return contents


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
