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

MicrophoneDevice = None  # handle for the microphone device class

# set the audio backend from preferences
try:
    backend = prefs.hardware['audioLib']
    if isinstance(backend, (list, tuple)):
        backend = backend[0]
except (KeyError, IndexError):
    logging.warning(
        "Audio library preference not found or empty, defaulting to 'ptb' for "
        "audio capture. Check the 'audioLib' preference to ensure it is set to a "
        "valid audio library."
    )
    backend = 'ptb'

# select backend microphone device class based on audio library preference
if backend in ('sounddevice',):  # sounddevice backend
    from .microphone_soundevice import SoundDeviceMicrophoneDevice
    MicrophoneDevice = SoundDeviceMicrophoneDevice
elif backend in ('ptb', 'default'):  # psychtoolbox backend
    from .microphone_psychtoolbox import PsychtoolboxMicrophoneDevice
    MicrophoneDevice = PsychtoolboxMicrophoneDevice
else:
    logging.error(
        f"Unsupported audio library '{backend}' specified in preferences. Using "
        f"'ptb' as fallback for audio capture. Check the 'audioLib' preference "
        f"to ensure it is set to a valid audio library."
    )
    backend = 'ptb'  # fallback to ptb for audio capture if unsupported library specified
    from .microphone_psychtoolbox import PsychtoolboxMicrophoneDevice
    MicrophoneDevice = PsychtoolboxMicrophoneDevice

logging.info(f"Using '{backend}' backend for audio capture devices.")

if __name__ == "__main__":
    pass
