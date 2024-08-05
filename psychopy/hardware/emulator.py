#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Software fMRI machine emulator.

Idea: Run or debug an experiment script using exactly the same code, i.e., for
both testing and online data acquisition. To debug timing, you can emulate sync
pulses and user responses.

Limitations: pyglet only; keyboard events only.

These are optional components that can be obtained by installing the
`psychopy-mri-emulator` extension into the current environment.

"""


from psychopy.tools.pkgtools import PluginStub


class SyncGenerator(
    PluginStub,
    plugin="psychopy-mri-emulator"
):
    pass


class ResponseEmulator(
    PluginStub,
    plugin="psychopy-mri-emulator"
):
    pass


class launchScan(
    PluginStub,
    plugin="psychopy-mri-emulator"
):
    pass


if __name__ == "__main__":
    pass
