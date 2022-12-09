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
        switchOff)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Konica Minolta hardware is not available this session. "
        "Please install `psychopy-minolta` and restart the session to enable "
        "support.")

if __name__ == "__main__":
    pass
