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

**Speech2Text()** provides speech recognition (courtesy of google), with about 1-2 seconds latency for a
2 sec voice recording. Note that the sound files are sent to google over the internet.
Intended for within-experiment processing (near real-time, 1-2s delayed), in which
priority is given to keeping an experiment session moving along, even if that means
skipping a slow response once in a while. See coder demo > input > `speech_recognition.py`.

Eventually, other features are planned, including: **speech onset detection** (to automatically estimate vocal RT for a
given speech sample), and **interactive visual inspection** of sound waveform, with
playback and manual onset determination (= the "gold standard" for RT).

Audio Capture
-------------
.. autofunction:: psychopy.microphone.switchOn

.. autoclass:: psychopy.microphone.AdvAudioCapture
    :members:
    :undoc-members:
    :inherited-members:

Speech recognition
------------------

.. autoclass:: psychopy.microphone.Speech2Text
    :members:
    :undoc-members:
    :inherited-members:

.. autoclass:: psychopy.microphone.BatchSpeech2Text
    :members:
    :undoc-members:

Misc
----
PsychoPy provides lossless compression using FLAC codec. (This requires that `flac`
is installed on your computer. It is not included with PsychoPy by default,
but you can download for free from http://xiph.org/flac/ ).
Functions for file-oriented Discrete Fourier Transform and RMS computation are also provided.

.. autofunction:: psychopy.microphone.wav2flac

.. autofunction:: psychopy.microphone.flac2wav

.. autofunction:: psychopy.microphone.getDft

.. autofunction:: psychopy.microphone.getRMS
