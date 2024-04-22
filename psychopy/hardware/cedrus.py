#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Cedrus Corporation devices such as button boxes.

These are optional components that can be obtained by installing the
`psychopy-cedrus` extension into the current environment.

DEPRECATED:
This sub-package is out of date. Please use the cedrus-written `pyxid2` package
instead (bundled with Standalone PsychoPy)::

    import pyxid2

"""

import psychopy.logging as logging
from psychopy.tools.pkgtools import PluginStub


class RB730(
    PluginStub, 
    plugin="psychopy-cedrus", 
    doclink="https://psychopy.github.io/psychopy-cedrus/coder/RB730"
):
    pass



if __name__ == "__main__":
    pass
