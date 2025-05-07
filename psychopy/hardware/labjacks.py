#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This provides a basic LabJack U3 class that can write a full byte of data, by
extending the labjack python library u3.U3 class.

These are optional components that can be obtained by installing the
`psychopy-labjack` extension into the current environment.

"""


from psychopy.plugins import PluginStub


class U3(
    PluginStub,
    plugin="psychopy-labjack",
    docsHome="http://psychopy.github.io/psychopy-labjack",
    docsRef="/labjacks.html#psychopy_labjack.labjacks.U3"
):
    pass
