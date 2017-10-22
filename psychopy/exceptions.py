#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import
from __future__ import print_function


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
