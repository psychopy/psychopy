#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic ButtonBox class, and imports the `ioLab python library
    <http://github.com/ioLab/python-ioLabs>`_.
"""
#  This file can't be named ioLabs.py, otherwise "import ioLabs" doesn't work.
# And iolabs.py (lowercase) did not solve it either, something is case
# insensitive somewhere

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for ioLab Systems button boxes.

These are optional components that can be obtained by installing the
`psychopy-iolabs` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_iolabs import ButtonBox
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for ioLab Systems hardware is not available this session. "
        "Please install `psychopy-iolabs` and restart the session to enable "
        "support.")
finally:
    logging.warning(
        "Support for ioLabs Systems hardware has been discontinued and will "
        "likely break in the future."
    )

if __name__ == "__main__":
    pass
