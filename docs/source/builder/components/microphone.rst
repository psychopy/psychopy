.. _microphoneComponent:

Microphone Component
-------------------------------

*Enabled for online use in version 2021.2 onwards*

The microphone component provides a way to record sound during an experiment. You can even transcribe the recording to text! Take a look at the documentation on :ref:`googleSpeech` to get started with that. 

When using a mic recording, specify the
starting time relative to the start of the routine (see `start` below) and a stop time (= duration in seconds).
A blank duration evaluates to recording for 0.000s.

The resulting sound files
are saved in .wav format (at the specified sampling frequency), one file per recording. The files appear in a new folder within the data
directory (the subdirectory name ends in `_wav`). The file names include the unix (epoch) time
of the onset of the recording with milliseconds, e.g., `mic-1346437545.759.wav`.

It is possible to stop a recording that is in progress by using a code component. Every frame,
check for a condition (such as key 'q', or a mouse click), and call the `mic.stop()` method
of the microphone component. The recording will end at that point and be saved.

Parameters
~~~~~~~~~~~~

Basic
====================

name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start : float or integer
    The time that the stimulus should first play. See :ref:`startStop` for details.

stop (duration):
    The length of time (sec) to record for. An `expected duration` can be given for
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.

Device:
    Which microphone device to use

Transcription
====================

Transcribe Audio: bool
    Whether to transcribe audio recordings and store the data

Online Transcription Backend:
    What transcription service to use to transcribe audio `Google <https://cloud.google.com/speech-to-text>`_ or built in. Note that in our experience Google has better transcription results, though we *highly* recommend taking a look at the documentation on :ref:`googleSpeech` to get started.

Transcription Language: string
    The language code for your chosen transcription language e.g. English (United States) is "en-US" see `list of codes here <https://cloud.google.com/speech-to-text/docs/languages>`_

Expected Words: list of strings
    A list of key words that you want to listen for e.g. `["Hello", "World"]` if blank all words will be listened for.

Data
====================

Save onset/offset times: bool
    Whether to save the onset and offset times of the component.

Sync timing with screen refresh: bool
    Whether to sync the start time of the component with the window refresh.

Output File Type:
    File type to save audio as (default is wav).

Speaking Start/Stop Times: bool
    Save onset/offset of speech.

Trim Silent: bool
    Trim periods of silent from the output file.

Hardware
====================

Channels:
    Record 1 (mono) or 2 (stereo) channels (auto will save as many as the recording device allows).

Sample Rate (Hz):
    Sampling rate of recorded audio.

Max Recording Size (kb):
    Max recording size to avoid excessively large output files.

.. seealso::
    API reference for :class:`~psychopy.microphone.AdvAudioCapture`
    API reference for :class:`~psychopy.sound.transcribe`
