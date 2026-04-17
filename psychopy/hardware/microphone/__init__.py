# -*- coding: utf-8 -*-

"""Classes and functions managing audio capture devices
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "MicrophoneDevice",
]

from psychopy import logging
from psychopy import prefs

MicrophoneDevice = None  # handle for the speaker device class

# set the audio backend from preferences
try:
    backend = prefs.hardware['audioDriver'][0]
except (KeyError, IndexError):
    logging.warning(
        "Audio library preference not found or empty, defaulting to 'sounddevice' for "
        "audio capture. Check the 'audioDriver' preference to ensure it is set to a "
        "valid audio library."
    )
    backend = 'sounddevice'


# select backend microphone device class based on audio library preference
if backend in ('sounddevice', 'default'):  # sounddevice backend
    from .microphone_soundevice import SoundDeviceMicrophoneDevice
    MicrophoneDevice = SoundDeviceMicrophoneDevice
elif backend in ('ptb', 'portaudio'):  # psychtoolbox backend
    from .microphone_psychtoolbox import PsychtoolboxMicrophoneDevice
    MicrophoneDevice = PsychtoolboxMicrophoneDevice
else:
    raise NotImplementedError(
        f"MicrophoneDevice is not implemented for audio library {backend}."
    )


if __name__ == "__main__":
    pass
