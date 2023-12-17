#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Audio capture and analysis using pyo.

These are optional components that can be obtained by installing the
`psychopy-legcay-mic` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_legacy_mic import (
        haveMic,
        FLAC_PATH,
        AudioCapture,
        AdvAudioCapture,
        getMarkerOnset,
        readWavFile,
        getDftBins,
        getDft,
        getRMSBins,
        getRMS,
        SoundFormatNotSupported,
        SoundFileError,
        MicrophoneError,
        Speech2Text,
        BatchSpeech2Text,
        flac2wav,
        wav2flac,
        switchOn,
        switchOff,
        _getFlacPath)
except (ModuleNotFoundError, ImportError, NameError):
    logging.error(
        "Support for `psychopy.microphone` hardware is not available this "
        "session. Please install `psychopy-legacy-mic` and restart the session "
        "to enable support.")
else:
    # if we successfully load the package, warn the user to use the newer stuff
    logging.warning(
        "Attempting to import `psychopy.microphone`. Note that this library is "
        "deprecated for the purpose of audio capture, but may still provide "
        "other useful functionality. Use `psychopy.sound.microphone` for audio "
        "capture instead."
    )

if __name__ == "__main__":
    pass
