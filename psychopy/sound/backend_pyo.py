#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio playback backend using Pyo.

These are optional components that can be obtained by installing the
`psychopy-pyo` extension into the current environment.

"""


from psychopy.plugins import PluginStub


class SoundPyo(
    PluginStub,
    plugin="psychopy-pyo",
    docsHome="https://github.com/psychopy/psychopy-pyo",
):
    pass


class init(
    PluginStub,
    plugin="psychopy-pyo",
    docsHome="https://github.com/psychopy/psychopy-pyo",
):
    pass


class get_devices_infos(
    PluginStub,
    plugin="psychopy-pyo",
    docsHome="https://github.com/psychopy/psychopy-pyo",
):
    pass


class get_input_devices(
    PluginStub,
    plugin="psychopy-pyo",
    docsHome="https://github.com/psychopy/psychopy-pyo",
):
    pass


class get_output_devices(
    PluginStub,
    plugin="psychopy-pyo",
    docsHome="https://github.com/psychopy/psychopy-pyo",
):
    pass


class getDevices(
    PluginStub,
    plugin="psychopy-pyo",
    docsHome="https://github.com/psychopy/psychopy-pyo",
):
    pass


pyoSndServer: SoundPyo
audioDriver: str