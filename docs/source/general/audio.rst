.. _audioStimuli:

Presenting audio stimuli
====================================

Presenting audio stimuli with low latency is more difficult than you might think! PsychoPy has historically used a range of audio libraries
to try and solve this issue. In PsychoPy 3.2 we added the option of using Psych

Choice of audio library
---------------------------

If low-latency audio is important to you then **we strongly recommend
you use the `ptb` library** which is a Python version of the PsychoPhysics
Toolbox audio engine (PsychPortAudio_).

Other options:

- `pyo` can be fast with the right hardware/OS, but not on such a range of hardware as the PTB option.
- `sounddevice` is the next best option if `pyo` isn't working for you
- `pygame` we really don't recommend

PsychoPy and the PTB audio engine
-------------------------------------

The PsychPortAudio_ engine from `Psychophysics Toolbox`_ is considerably faster
than any of our previous audio library options. On most hardware it should result
in sub-ms precision in audio latencies.

This is achieved by a number of means, including fine-grained control of
audio driver settings and by pre-scheduling of sounds for playback.





.. _PsychPortAudio: http://psychtoolbox.org/docs/PsychPortAudio-Open
.. _Psychophysics Toolbox: http://psychtoolbox.org
