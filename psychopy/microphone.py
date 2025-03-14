#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Audio capture and analysis using pyo.

These are optional components that can be obtained by installing the
`psychopy-legcay-mic` extension into the current environment.

"""


from psychopy.plugins import PluginStub


class AudioCapture(
    PluginStub,
    plugin="psychopy-legacy-mic",
    docsHome="https://github.com/psychopy/psychopy-legacy-mic",
):
    pass


if __name__ == "__main__":
    pass
