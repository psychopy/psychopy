#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for ioLab Systems button boxes.

These are optional components that can be obtained by installing the
`psychopy-iolabs` extension into the current environment.

"""

from psychopy.plugins import PluginStub


class ButtonBox(
    PluginStub,
    plugin="psychopy-iolabs",
    docsHome="http://psychopy.github.io/psychopy-iolabs",
    docsRef="/coder/ButtonBox/"
):
    pass
