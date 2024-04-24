#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for Minolta light-measuring devices.

These are optional components that can be obtained by installing the
`psychopy-minolta` extension into the current environment.

"""

from psychopy.tools.pkgtools import PluginStub


class CS100A(PluginStub, plugin="psychopy-minolta", doclink="https://psychopy.github.io/psychopy-minolta/coder/CS100A"):
    pass


class LS100(PluginStub, plugin="psychopy-minolta", doclink="https://psychopy.github.io/psychopy-minolta/coder/LS100"):
    pass
