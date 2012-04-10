:mod:`psychopy.microphone` - Capture and analyze sound
======================================================

Overview
--------
**AudioCapture()** allows easy audio recording and saving of arbitrary sounds to a file (wav format).

**Speech2Text()** provides speech recognition (courtesy of google), with about 1-2 seconds latency for a
2 sec voice recording. Note that the sound files are sent to google over the internet.
Files are sent over https, but no attempt is made to validate the server's certificate.
(Its possible to do so, but more involved; seems low priority as a feature.)

Eventually, other features will be available, including: **loudness** and
**voice onset detection** (to automatically estimate vocal response time for a
given speech sample). It would be handy to have **multiple-file speech-to-text**
conversion, e.g., to process all wav files in a directory. And **visual inspection** of a
waveform, with playback and manual voice onset determination (= the "gold standard" for RT).

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
.. autoclass:: psychopy.microphone.Speech2Text
    :members:
    :undoc-members:
    :inherited-members:
