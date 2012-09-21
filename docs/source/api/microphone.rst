.. _microphone:

:mod:`psychopy.microphone` - Capture and analyze sound
======================================================

(Available as of version 1.74.00)

Overview
--------
**AudioCapture()** allows easy audio recording and saving of arbitrary sounds to a file (wav format).

**Speech2Text()** provides speech recognition (courtesy of google), with about 1-2 seconds latency for a
2 sec voice recording. Note that the sound files are sent to google over the internet.
Intended for within-experiment processing (near real-time, 1-2s delayed), in which
priority is given to keeping an experiment session moving along, even if that means
skipping a slow response once in a while.

**BatchSpeech2Text()** takes a list of files, or a directory name, and processes all files
using Speech2Text with up to 5 concurrent threads. Returns a list of (file, response) tuples.
Batch processing is intended to facillitate post-experiment processing.

Eventually, other features are planned, including: **loudness** and
**voice onset detection** (to automatically estimate vocal RT for a
given speech sample), and **interactive visual inspection** of sound waveform, with
playback and manual onset determination (= the "gold standard" for RT).

Audio Capture
-------------
.. autofunction:: psychopy.microphone.switchOn
.. autofunction:: psychopy.microphone.switchOff 

.. autoclass:: psychopy.microphone.AudioCapture
    :members:
    :undoc-members:
    :inherited-members:

Speech recognition
------------------
.. autoclass:: psychopy.microphone.BatchSpeech2Text
    :members:
    :undoc-members:
    
.. autoclass:: psychopy.microphone.Speech2Text
    :members:
    :undoc-members:
    :inherited-members:
