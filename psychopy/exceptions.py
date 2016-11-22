# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

class DependencyError(Exception):
    """The user requested something that won't be possible because
    of a dependency error (e.g. audiolib that isn't available)
    """
    pass
