#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load and play sounds

We have used a number of different Python libraries ("backends") for generating
sounds in PsychoPy. We started with `Pygame`, then tried `pyo` and `sounddevice`
but we now strongly recommend you use the PTB setting. That uses the
`PsychPortAudio`_ engine, written by Mario Kleiner for `Psychophysics Toolbox`_.

With the PTB backend you get some options about how aggressively you want to try
for low latency, and there is also an option to pre-schedule a sound to play at
a given time in the future.

The built-in backends are 'ptb' (alias 'psychtoolbox') and 'sounddevice'
(alias 'sd'). Plugins may register additional backends. The backend is
chosen from the list in preferences > hardware > audioLib (default:
['ptb', 'sounddevice', 'pyo', 'pygame']), and the first entry that names a
known backend is used. Entries for removed backends, such as 'pyo' and
'pygame', are skipped. To override the preference in a script, set
`psychopy.sound.Sound.backend` to a backend name before creating any sounds.

The backend is not imported until it is first needed, which is usually when
the first `Sound` is created. With the PTB backend you can also choose the
underlying sound driver (e.g. ASIO, CoreAudio etc) in
preferences > hardware > audioDriver.

The sound lib and driver being used can be queried as::
    `psychopy.sound.audioLib`
    `psychopy.sound.audioDriver`

These are resolved lazily on first access, so the audio backend is not
imported until it is needed. Accessing `audioDriver` will import the backend.

.. PTB

.. _PsychPortAudio: http://psychtoolbox.org/docs/PsychPortAudio-Open
.. _Psychophysics Toolbox: http://psychtoolbox.org
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
from .audiodevice import *
from .audioclip import *  # import objects related to AudioClip
from . import microphone, sound
from .sound import Sound

__all__ = [
    "microphone",
    "Sound"
]


# used to check if we are on 64-bit Python
bits32 = sys.maxsize == 2 ** 32


def __getattr__(name):
    """Provide legacy module-level attributes, resolved lazily.

    Previously the audio backend was loaded when `psychopy.sound` was
    imported, and `audioLib`, `audioDriver`, `backend` and `pyoSndServer`
    were set as module globals. The backend is now only loaded when needed,
    so these are computed on access to keep existing code working.
    """
    if name == "audioLib":
        # name of the selected backend (e.g. 'ptb'), without importing it
        return Sound.resolveBackendName()
    if name == "audioDriver":
        # driver used by the backend, if it defines one
        return getattr(Sound.resolveBackend(), "audioDriver", None)
    if name == "backend":
        # the backend module itself
        return Sound.resolveBackend()
    if name == "pyoSndServer":
        # the pyo backend has been removed, so there is never a pyo server
        return None

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

