#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio playback backend using SoundDevice.

These are optional components that can be obtained by installing the
`psychopy-sounddevice` extension into the current environment.

"""


from psychopy.plugins import PluginStub


class SoundDeviceSound(
    PluginStub,
    plugin="psychopy-sounddevice",
    docsHome="https://github.com/psychopy/psychopy-sounddevice",
):
    pass


class init(
    PluginStub,
    plugin="psychopy-sounddevice",
    docsHome="https://github.com/psychopy/psychopy-sounddevice",
):
    pass


class getDevices(
    PluginStub,
    plugin="psychopy-sounddevice",
    docsHome="https://github.com/psychopy/psychopy-sounddevice",
):
    pass


class getStreamLabel(
    PluginStub,
    plugin="psychopy-sounddevice",
    docsHome="https://github.com/psychopy/psychopy-sounddevice",
):
    pass
