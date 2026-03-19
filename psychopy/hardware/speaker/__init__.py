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

# select backend for speaker devices based on audio library preference
backend = 'default'
try:
    backend = prefs.hardware['audioDriver'][0]
except (KeyError, IndexError, TypeError):
    # handle if we cannot read the preference for some reason
    logging.warn(
        "Cannot get audio driver preference from preferences, using default."
    )

if backend == 'default':   # if default, select the best available backend
    backend = 'sounddevice'

SpeakerDevice = None  # handle for the speaker device class

# select the speaker device class based on the selected backend
if backend == 'sounddevice' or backend == 'portaudio':
    from .speaker_sounddevice import SoundDeviceSpeakerDevice
    SpeakerDevice = SoundDeviceSpeakerDevice
elif backend == 'ptb':
    from .speaker_psychtoolbox import PsychtoolboxSpeakerDevice
    SpeakerDevice = PsychtoolboxSpeakerDevice
else:
    raise ValueError((
        f"Invalid value '{backend}' for prefs.hardware['audioDriver'], "
        f"expected 'sounddevice', 'ptb', or 'default'"))

if __name__ == "__main__":
    pass
