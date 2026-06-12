# -*- coding: utf-8 -*-

"""Classes and functions managing physical speaker devices for audio playback.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "SpeakerDevice",
]

import importlib.metadata


class SpeakerDevice:

    # selected backend
    backend = "sounddevice"
    # known backends
    backends = {
        'ptb': importlib.metadata.EntryPoint(
            name="ptb", 
            value="psychopy.hardware.speaker.speaker_psychtoolbox:PsychtoolboxSpeakerDevice", 
            group="psychopy.hardware.speaker.backends"
        ),
        'sounddevice': importlib.metadata.EntryPoint(
            name="sounddevice", 
            value="psychopy.hardware.speaker.speaker_sounddevice:SoundDeviceSpeakerDevice", 
            group="psychopy.hardware.speaker.backends"
        )
    }
    # alias backend names
    backends['psychtoolbox'] = backends['ptb']
    backends['sd'] = backends['sounddevice']

    def __new__(cls, *args, **kwargs):
        # handle list
        if isinstance(cls.backend, (list, tuple)):
            try:
                # try to get the first valid backend
                cls.backend = [
                    val for val in cls.backend if val in cls.backends
                ][0]
            except:
                # otherwise get the first backend
                cls.backend = cls.backend[0]
        # if not present, error
        if cls.backend not in cls.backends:
            raise ModuleNotFoundError(
                f"Invalid value '{cls.backend}' for {cls.__name__}.backend, known backends are: {list(cls.backends)}"
            )
        # import backend
        backend = cls.backends[cls.backend].load()

        return backend(*args, **kwargs)

# get sound backends from plugins
for ep in importlib.metadata.entry_points(group="psychopy.hardware.speaker.backends"):
    SpeakerDevice.backends[ep.name] = ep
