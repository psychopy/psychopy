#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Cedrus Corporation devices such as button boxes.

These are optional components that can be obtained by installing the
`psychopy-cedrus` extension into the current environment.
"""


from psychopy.plugins import PluginStub


class RB730(
    PluginStub, 
    plugin="psychopy-cedrus", 
    docsHome="https://psychopy.github.io/psychopy-cedrus",
    docsRef="/coder/RB730"
):
    pass
