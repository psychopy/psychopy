.. _microphonecomponent:

-------------------------------
Microphone Component
-------------------------------

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

Categories:
    Responses
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _microphonecomponent-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _microphonecomponent-startVal:
Start
    When the Microphone Component should start, see :ref:`startStop`.
    
.. _microphonecomponent-startEstim:
Expected start (s)
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _microphonecomponent-startType:
Start type
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _microphonecomponent-stopVal:
Stop
    When the Microphone Component should stop, see :ref:`startStop`.
    
.. _microphonecomponent-durationEstim:
Expected duration (s)
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _microphonecomponent-stopType:
Stop type
    The duration of the recording in seconds; blank = 0 sec
    
    Options:
    
    * duration (s)
    
Device
===============================

Information about the device associated with this Component. Keyboards, speakers, microphones, etc.


.. _microphonecomponent-deviceLabel:
Device label
    A label to refer to this Component's associated hardware device by. If using the same device for multiple components, be sure to use the same label here.
    
.. _microphonecomponent-device:
Device
    What microphone device would you like the use to record? This will only affect local experiments - online experiments ask the participant which mic to use.
    
.. _microphonecomponent-channels:
Channels
    Record two channels (stereo) or one (mono, smaller file). Select 'auto' to use as many channels as the selected device allows.
    
    Options:
    
    * Auto
    
    * Mono
    
    * Stereo
    
.. _microphonecomponent-sampleRate:
Sample rate (hz)
    How many samples per second (Hz) to record at
    
.. _microphonecomponent-exclusive:
Exclusive control
    Take exclusive control of the microphone, so other apps can't use it during your experiment.
    
.. _microphonecomponent-maxSize:
Max recording size (kb)
    To avoid excessively large output files, what is the biggest file size you are likely to expect?
    
Transcription
===============================




.. _microphonecomponent-transcribe:
Transcribe audio
    Whether to transcribe the audio recording and store the transcription
    
.. _microphonecomponent-transcribeBackend:
Transcription backend
    What transcription service to use to transcribe audio?
    
    Options:
    
    * `Google <https://cloud.google.com/speech-to-text>`_: Uses Google's cloud based speech-to-text engine, requiring a key from Google to use. We *highly* recommend taking a look at the documentation on :ref:`googleSpeech` to get started.

    * `Whisper (OpenAI) <https://openai.com/index/whisper/>`_: Uses an open-source speech recognition AI. Requires the `psychopy-whisper <https://github.com/psychopy/psychopy-whisper>`_ plugin to be installed, and will work better with a dedicated graphics card (as the model uses GPU to speed up processing)
    
.. _microphonecomponent-transcribeLang:
Transcription language
    What language you expect the recording to be spoken in, e.g. en-US for English
    
.. _microphonecomponent-transcribeWords:
Expected words
    Set list of words to listen for - if blank will listen for all words in chosen language. 

If using the built-in transcriber, you can set a minimum % confidence level using a colon after the word, e.g. 'red:100', 'green:80'. Otherwise, default confidence level is 80%.
    
.. _microphonecomponent-speakTimes:
Speaking start / stop times
    Tick this to save times when the participant starts and stops speaking
    
.. _microphonecomponent-transcribeWhisperModel:
Whisper model (*if :ref:`microphonecomponent-transcribeBackend` is "Whisper"*)
    Which model of Whisper AI should be used for transcription? Details of each model are available `here <https://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages>`_
    
    Options:
    
    * tiny
    
    * base
    
    * small
    
    * medium
    
    * large
    
    * tiny.en
    
    * base.en
    
    * small.en
    
    * medium.en
    
.. _microphonecomponent-transcribeWhisperDevice:
Whisper device (*if :ref:`microphonecomponent-transcribeBackend` is "Whisper"*)
    Which device to use for transcription?
    
    Options:
    
    * auto
    
    * gpu
    
    * cpu
    
Data
===============================

What information about this Component should be saved?


.. _microphonecomponent-saveStartStop:
Save onset/offset times
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _microphonecomponent-syncScreenRefresh:
Sync timing with screen refresh
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
.. _microphonecomponent-outputType:
Output file type
    What file type should output audio files be saved as?
    
    Options:
    
    * default
    
    * aiff
    
    * au
    
    * avr
    
    * caf
    
    * flac
    
    * htk
    
    * svx
    
    * mat4
    
    * mat5
    
    * mpc2k
    
    * mp3
    
    * ogg
    
    * paf
    
    * pvf
    
    * raw
    
    * rf64
    
    * sd2
    
    * sds
    
    * ircam
    
    * voc
    
    * w64
    
    * wav
    
    * nist
    
    * wavex
    
    * wve
    
    * xi
    
.. _microphonecomponent-policyWhenFull:
Full buffer policy
    What to do when we reach the max amount of audio data which can be safely stored in memory?
    
    Options:
    
    * Discard incoming data
    
    * Clear oldest data
    
    * Raise error
    
.. _microphonecomponent-trimSilent:
Trim silent
    Trim periods of silence from the output file
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _microphonecomponent-disabled:
Disable Component
    Disable this Component
    