#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Interfaces for `Brain Products GMBH <https://www.brainproducts.com>`_
hardware.

Here we have implemented support for the Remote Control Server application,
which allows you to control recordings, send annotations etc. all from Python.

"""

import psychopy.logging as logging
from psychopy.plugins import PluginStub


class RemoteControlServer(
    PluginStub,
    plugin="psychopy-brainproducts",
    docsHome="https://psychopy.github.io/psychopy-brainproducts"
):
    pass
