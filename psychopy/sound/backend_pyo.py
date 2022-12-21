#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Audio playback backend using Pyo.

These are optional components that can be obtained by installing the
`psychopy-pyo` extension into the current environment.

"""

import psychopy.logging as logging
from .exceptions import DependencyError

try:
    from psychopy_pyo import (
        init,
        get_devices_infos,
        get_input_devices,
        get_output_devices,
        getDevices,
        SoundPyo)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for the `pyo` audio backend is not available this session. "
        "Please install `psychopy-pyo` and restart the session to enable "
        "support.")
except (NameError, DependencyError):
    logging.error(
        "Error encountered while loading `psychopy-pyo`. Check logs for more "
        "information.")

if __name__ == "__main__":
    pass
