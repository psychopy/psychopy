# -*- coding: utf-8 -*-

"""Classes and functions managing audio capture devices
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    "MicrophoneDevice",
]

import importlib.metadata
from psychopy.preferences import prefs
from psychopy import logging


class MicrophoneDevice:
    # selected backend
    backend = None
    # known backends
    backends = {
        'ptb': importlib.metadata.EntryPoint(
            name="ptb", 
            value="psychopy.hardware.microphone.microphone_psychtoolbox:PsychtoolboxMicrophoneDevice", 
            group="psychopy.hardware.microphone.backends"
        ),
        'sounddevice': importlib.metadata.EntryPoint(
            name="sounddevice", 
            value="psychopy.hardware.microphone.microphone_soundevice:SoundDeviceMicrophoneDevice", 
            group="psychopy.hardware.microphone.backends"
        )
    }
    # alias backend names
    backends['psychtoolbox'] = backends['ptb']
    backends['sd'] = backends['sounddevice']

    def __new__(cls, *args, **kwargs):
        backend = cls.resolveBackend()

        return backend(*args, **kwargs)

    @classmethod
    def resolveBackend(cls):
        backend = cls.backend
        # if backend is None, get from prefs
        if backend is None:
            backend = prefs.hardware['audioLib']
        # handle list
        if isinstance(backend, (list, tuple)):
            try:
                # try to get the first valid backend
                backend = [
                    val for val in backend if val in cls.backends
                ][0]
            except:
                # otherwise get the first backend
                backend = backend[0]
        # if not present, error
        if backend not in cls.backends:
            raise ModuleNotFoundError(
                f"Invalid value '{backend}' for {cls.__name__}.backend, known backends are: {list(cls.backends)}"
            )

        # import backend
        try:
            return cls.backends[backend].load()
        except:
            # if backend fails to import, remove it from .backends
            del cls.backends[backend]
            # if there's no backends left, error
            if not len(cls.backends):
                raise ImportError(
                    "All audio backends failed to load."
                )
            # try next option
            cls.backend = list(cls.backends)[0]
            # log
            logging.error(
                f"Failed to load {backend} backend, trying {cls.backend}..."
            )

            return cls.resolveBackend()

    @staticmethod
    def getAvailableDevices():
        return MicrophoneDevice.resolveBackend().getAvailableDevices()
    
    @classmethod
    def getBackends(cls):
        """
        Get all available Sound backends (by name)

        Returns
        -------
        dict[str:importlib.metadata.EntryPoint]
            Dict mapping backend names to backend entry points - call `.load` on an entry point to 
            import the relevant module.
        """
        
        return cls.backends


# get sound backends from plugins
for ep in importlib.metadata.entry_points(group="psychopy.hardware.microphone.backends"):
    MicrophoneDevice.backends[ep.name] = ep
