#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
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
    from a file. Includes attribute "translated" as these error messages are used
    by Builder to set a label in the loop dialog so need to be available both as
    a fixed value which can be queried and as a variable value which can change
    according to locale.

    Parameters
    ==========
    msg : str
        The error message to be displayed, same as any other Exception.
    translated : str
        The error message translated according to user's locale.
    """

    def __init__(self, msg, translated=None):
        # Initialise exception with message
        Exception.__init__(self, msg)
        # Add reason
        self.translated = translated or msg


class MissingFontError(Exception):
    pass
