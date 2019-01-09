.. _microphoneComponent:

Microphone Component
-------------------------------

Please note: This is a new component, and is subject to change.

The microphone component provides a way to record sound during an experiment. To do so, specify the
starting time relative to the start of the routine (see `start` below) and a stop time (= duration in seconds).
A blank duration evaluates to recording for 0.000s.

The resulting sound files
are saved in .wav format (at 48000 Hz, 16 bit), one file per recording. The files appear in a new folder within the data
directory (the subdirectory name ends in `_wav`). The file names include the unix (epoch) time
of the onset of the recording with milliseconds, e.g., `mic-1346437545.759.wav`.

It is possible to stop a recording that is in progress by using a code component. Every frame,
check for a condition (such as key 'q', or a mouse click), and call the `.stop()` method
of the microphone component. The recording will end at that point and be saved.
For example, if `mic` is the name of your microphone component, then in the code component, do this on **Each frame**::
    
    if event.getKeys(['q']):
        mic.stop()

Parameters
~~~~~~~~~~~~

`name` : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
`start` : float or integer
    The time that the stimulus should first play. See :ref:`startStop` for details.

`stop (duration)`: 
    The length of time (sec) to record for. An `expected duration` can be given for 
    visualisation purposes. See :ref:`startStop` for details; note that only seconds are allowed.

.. seealso::
	
	API reference for :class:`~psychopy.microphone.AdvAudioCapture`
