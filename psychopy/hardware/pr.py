#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Photo Research Inc. spectroradiometers.

These are optional components that can be obtained by installing the
`psychopy-photoresearch` extension into the current environment.

"""

from psychopy.plugins import PluginStub


class PR650(
    PluginStub, 
    plugin="psychopy-photoresearch", 
    docsHome="https://psychopy.github.io/psychopy-photoresearch",
    docsRef="/coder/PR650"
):
    pass


class PR655(
    PluginStub, 
    plugin="psychopy-photoresearch", 
    docsHome="https://psychopy.github.io/psychopy-photoresearch",
    docsRef="/coder/PR655"
):
    pass
