#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).


class DependencyError(Exception):
    """The user requested something that won't be possible because
    of a dependency error (e.g. audiolib that isn't available)
    """
    pass


class SoundFormatError(Exception):
    """The user tried to create two streams (diff sample rates) on a machine
    that won't allow that
    """
    pass


class NoUserError(Exception):
    pass


class NoGitError(DependencyError):
    pass


class RepositoryError(Exception):
    pass


class ConditionsImportError(Exception):
    """
    Exception class to handle errors arising when attempting to import conditions
    from a file. Includes attribute "reason" so that the source of the error can
    be identified without parsing the error message, as this method falls down
    when the error message is translated.

    Parameters
    ==========
    msg : str
        The error message to be displayed, same as any other Exception
    reason : str
        Language-agnostic label for the error.
    """

    def __init__(self, msg, reason=""):
        # Initialise exception with message
        Exception.__init__(self, msg)
        # Add reason
        self.reason = reason


class MissingFontError(Exception):
    pass
