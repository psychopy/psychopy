#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
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


class ConnectionError(Exception):
    pass


class NoGitError(DependencyError):
    pass
