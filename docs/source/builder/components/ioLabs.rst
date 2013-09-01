.. _iolabs:

ioLab Systems buttonbox Component
---------------------------------

A button box is a hardware device that is used to collect participant responses with high temporal precision, ideally with true ms accuracy.

Both the response (which button was pressed) and time taken to make it are returned. The time taken is determined by a clock on the device itself. This is what makes it capable (in theory) of high precision timing.

Check the log file to see how long it takes for PsychoPy to reset the button box's internal clock. If this takes a while, then the RT timing values are not likely to be high precision. It might be possible for you to obtain a correction factor for your computer + button box set up, if the timing delay is highly reliable.

The ioLabs button box also has a built-in voice-key, but PsychoPy does not have an interface for it. Use a microphone component instead.

Properties
~~~~~~~~~~~

name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

start :
    The time that the stimulus should first appear. See :ref:`startStop` for details.

stop :
    The duration for which the stimulus is presented. See :ref:`startStop` for details.

Force end of Routine : checkbox
    If this is checked, the first response will end the routine.

Active buttons : None, or an integer, list, or tuple of integers 0-7
    The ioLabs box lets you specify a set of active buttons. Responses on non-active buttons are ignored by the box, and never sent to PsychoPy.
    This field lets you specify which buttons (None, or some or all of 0 through 7).

Lights :
    If selected, the lights above the active buttons will be turned on.

    Using code components, it is possible to turn on and off specific lights within a trial. See the API for :class:`~psychopy.hardware.iolab`.

Store : (choice of: first, last, all, nothing)
    Which button events to save in the data file. Events and the response times are saved, with RT being recorded by the button box (not by PsychoPy).

Store correct : checkbox
    If selected, a correctness value will be saved in the data file, based on a match with the given correct answer.

Correct answer: button
    The correct answer, used by Store correct.

Discard previous : checkbox
    If selected, any previous responses will be ignored (typically this is what you want).

Lights off : checkbox
    If selected, all lights will be turned off at the end of each routine.

.. seealso::

	API reference for :class:`~psychopy.hardware.iolab`
