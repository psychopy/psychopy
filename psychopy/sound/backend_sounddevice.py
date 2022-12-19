#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio playback backend using SoundDevice.

These are optional components that can be obtained by installing the
`psychopy-sounddevice` extension into the current environment.

"""

import psychopy.logging as logging
from .exceptions import DependencyError

try:
    from psychopy_sounddevice import (
        SoundDeviceSound,
        init,
        getDevices,
        getStreamLabel
    )
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for the `sounddevice` audio backend is not available this "
        "session. Please install `psychopy-sounddevice` and restart the "
        "session to enable support.")
except (NameError, DependencyError):
    logging.error(
        "Error encountered while loading `psychopy-sounddevice`. Check logs "
        "for more information.")

if __name__ == "__main__":
    pass
