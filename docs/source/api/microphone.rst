.. _microphone:

:mod:`psychopy.microphone` - Capture and analyze sound
======================================================

(Available as of version 1.74.00; Advanced features available as of 1.77.00)

Overview
--------
**AudioCapture()** allows easy audio recording and saving of arbitrary sounds to a file (wav format).
AudioCapture will likely be replaced entirely by AdvAudioCapture in the near future.

**AdvAudioCapture()** can do everything AudioCapture does, and also allows onset-marker sound
insertion and detection, loudness computation (RMS audio "power"), and lossless file compression (flac).
The Builder microphone component now uses AdvAudioCapture by default.

Audio Capture
-------------
.. autofunction:: psychopy.microphone.switchOn

.. autoclass:: psychopy.microphone.AdvAudioCapture
    :members:
    :undoc-members:
    :inherited-members:

Speech recognition
------------------

Google's speech to text API is no longer available. AT&T, IBM, and wit.ai have
a similar (paid) service.

Misc
----

Functions for file-oriented Discrete Fourier Transform and RMS computation are also provided.

.. autofunction:: psychopy.microphone.wav2flac

.. autofunction:: psychopy.microphone.flac2wav

.. autofunction:: psychopy.microphone.getDft

.. autofunction:: psychopy.microphone.getRMS
