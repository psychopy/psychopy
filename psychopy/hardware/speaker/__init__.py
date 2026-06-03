# -*- coding: utf-8 -*-

"""Classes and functions managing physical speaker devices for audio playback.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "SpeakerDevice",
]

from psychopy import logging
from psychopy import prefs

SpeakerDevice = None  # handle for the speaker device class

# select backend for speaker devices based on audio library preference
backend = 'default'
try:
    backend = prefs.hardware['audioLib']
    if isinstance(backend, (list, tuple)):
        backend = backend[0]
except (KeyError, IndexError, TypeError):
    # handle if we cannot read the preference for some reason
    logging.warn(
        "Cannot get audio library preference from preferences, using default."
    )

if backend == 'default':   # if default, select the best available backend
    backend = 'ptb'

# select the speaker device class based on the selected backend
if backend in ('sounddevice',):  # sounddevice backend
    from .speaker_sounddevice import SoundDeviceSpeakerDevice
    SpeakerDevice = SoundDeviceSpeakerDevice
elif backend in ('ptb', 'default'):  # psychtoolbox backend
    from .speaker_psychtoolbox import PsychtoolboxSpeakerDevice
    SpeakerDevice = PsychtoolboxSpeakerDevice
else:
    logging.error(
        f"Unsupported audio library '{backend}' specified in preferences. Using "
        f"'ptb' as fallback for sound output. Check the 'audioLib' preference "
        f"to ensure it is set to a valid audio library."
    )
    backend = 'ptb'  # fallback to ptb for sound output if unsupported library specified
    from .speaker_psychtoolbox import PsychtoolboxSpeakerDevice
    SpeakerDevice = PsychtoolboxSpeakerDevice

logging.info(f"Using '{backend}' backend for sound output devices.")

if __name__ == "__main__":
    pass
