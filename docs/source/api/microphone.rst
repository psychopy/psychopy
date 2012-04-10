:mod:`psychopy.microphone` - Capture and analyze sound
======================================================

Overview
--------
**AudioCapture()** allows easy audio recording and saving of arbitrary sounds to a file (wav format).

**Speech2Text()** provides speech recognition (courtesy of google), with about 1-2 seconds latency for a
2 sec voice recording. Note that the sound files are sent to google over the internet.
Files are sent over https, but no attempt is made to validate the server's certificate. 
Intended for within-experiment processing (near real-time, 1-2s delayed), in which
its often more important to skip a slow response.

**BatchSpeech2Text()** takes a list of files, or a directory name, and processes them
all (up to 5 concurrent threads). Returns a list of (file, response) tuples. Intended for
post-experiment processing of multiple files, in which waiting for a slow response
is not a problem (better to get the data).

Eventually, other features will be available, including: **loudness** and
**voice onset detection** (to automatically estimate vocal response time for a
given speech sample). And **interactive visual inspection** of a waveform, with
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
