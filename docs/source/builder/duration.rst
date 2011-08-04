.. _duration:

Duration
------------------

As of version 1.65.02 the duration of stimuli can be defined in several ways.

Start and stop times can be entered in terms of seconds (`time(s)`), by frame number (`frameN`) or in relation to another stimulus (`condition`). `Condition` would be used to make :ref:`components` start or stop depending on the status of something else, for example when a sound has finished. Duration can also be varied using a code component.

Expected start/duration allows components with variable durations to be drawn in the routine window. If you do not enter the approximate duration it will not be drawn correctly, this will not however effect experimental performance or the compiled script. 

Measuring duration is seconds is not very accurate because it doesn't take into account the fact that your monitor has a fixed frame rate. For example if the screen has a refresh rate of 60Hz you cannot present your stimulus for 120ms; the frame rate would limit you to 116.7ms (7 frames) or 133.3ms (8 frames).

If you need more precision that this it is best to control your duration by specifying the number of frames the stimulus will be presented for. 

The duration of a frame can be calculated by 1/(refresh rate in Hz).

For more details of how to achieve good temporal precision see :ref:`timing`

Examples
~~~~~~~~~~~~

*	Use `time(s)` or `frameN` and simply enter numeric values into the start and duration boxes.
*	Use `time(s)` or `frameN` and enter a numeric value into the start time and set the duration to a variable name by preceeding it with a $ as described :ref:`here <accessingParams>`. Then set `expected time` to see an approximation in your :ref:`routine <routines>`
*	Use condition to cause the stimulus to start immediately after a movie component called myMovie, by entering `$myMovie.status==FINISHED` into the `start` time.