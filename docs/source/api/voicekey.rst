.. _voicekey:

:mod:`psychopy.voicekey` - Real-time sound processing
======================================================

(Available as of version 1.83.00)

Overview
--------
Hardware voice-keys are used to detect and signal acoustic properties in real
time, e.g., the onset of a spoken word in word-naming studies. PsychoPy
provides two virtual voice-keys, one for detecting vocal onsets and one for vocal
offsets.

All PsychoPy voice-keys can take their input from a file or from a microphone.
Event detection is typically quite similar is both cases.

The base class is very general, and is best thought of as providing a toolkit
for developing a wide range of custom voice-keys. It would be possible to develop
a set of voice-keys, each optimized for detecting different initial phonemes.
Band-pass filtered data and zero-crossing counts are computed in real-time
every 2ms.

Voice-Keys
-------------

.. autoclass:: psychopy.voicekey.OnsetVoiceKey
    :members:
    :exclude-members: trip
    :inherited-members:

.. autoclass:: psychopy.voicekey.OffsetVoiceKey

Signal-processing functions
----------------------------

Several utility functions are available for real-time sound analysis.

.. autofunction:: psychopy.voicekey.smooth

.. autofunction:: psychopy.voicekey.bandpass

.. autofunction:: psychopy.voicekey.rms

.. autofunction:: psychopy.voicekey.std

.. autofunction:: psychopy.voicekey.zero_crossings

.. autofunction:: psychopy.voicekey.tone

.. autofunction:: psychopy.voicekey.apodize

Sound file I/O
---------------
Several helper functions are available for converting and saving sound data
from several data formats (numpy arrays, pyo tables) and file formats. All file formats that
`pyo` supports are available, including `wav`, `flac` for lossless compression. `mp3` format is not
supported (but you can convert to .wav using another utility).

.. autofunction:: psychopy.voicekey.samples_from_table

.. autofunction:: psychopy.voicekey.table_from_samples

.. autofunction:: psychopy.voicekey.table_from_file

.. autofunction:: psychopy.voicekey.samples_from_file

.. autofunction:: psychopy.voicekey.samples_to_file

.. autofunction:: psychopy.voicekey.table_to_file
