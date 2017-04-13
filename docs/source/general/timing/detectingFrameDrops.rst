.. _detectDroppedFrames:

Detecting dropped frames
------------------------

Occasionally you will drop frames if you:

* try to do too much drawing
* do it in an inefficient manner (write poor code)
* have a poor computer/graphics card

Things to avoid:

* recreating textures for stimuli
* building new stimuli from scratch (create them once at the top of your script
and then change them using :meth:`stim.setOri(ori)`, `stim.setPos([x,y]...)`

Turn on frame time recording
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The key sometimes is *knowing* if you are dropping frames. PsychoPy can help
with that by keeping track of frame durations. By default, frame time tracking
is turned off because many people don't need it, but it can be turned on any
time after :class:`~psychopy.visual.Window` creation::

    from psychopy import visual
    win = visual.Window([800,600])
    win.recordFrameIntervals = True

Since there are often dropped frames just after the system is initialised, it
makes sense to start off with a fixation period, or a ready message and don't
start recording frame times until that has ended. Obviously if you aren't
refreshing the window at some point (e.g. waiting for a key press with an
unchanging screen) then you should turn off the recording of frame times or it
will give spurious results.

Warn me if I drop a frame
~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to check if a frame has been dropped is to get PsychoPy to
report a warning if it thinks a frame was dropped::

    from __future__ import division, print_function

    from psychopy import visual, logging
    win = visual.Window([800,600])

    win.recordFrameIntervals = True

    # By default, the threshold is set to 120% of the estimated refresh
    # duration, but arbitrary values can be set.
    #
    # I've got 85Hz monitor and want to allow 4 ms tolerance; any refresh that
    # takes longer than the specified period will be considered a "dropped"
    # frame and increase the count of win.nDroppedFrames.
    win.refreshThreshold = 1/85 + 0.004

    # Set the log module to report warnings to the standard output window
    # (default is errors only).
    logging.console.setLevel(logging.WARNING)

    print('Overall, %i frames were dropped.' % win.nDroppedFrames)

Show me all the frame times that I recorded
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While recording frame times, these are simply appended, every frame to 
win.frameIntervals (a list). You can simply plot these at the end of your script
using matplotlib::

    import matplotlib.pyplot as plt
    plt.plot(win.frameIntervals)
    plt.show()

Or you could save them to disk. A convenience function is provided for this::

    win.saveFrameIntervals(fileName=None, clear=True)

The above will save the currently stored frame intervals (using the default
filename, 'lastFrameIntervals.log') and then clears the data. The saved file is
 a simple text file.

At any time you can also retrieve the time of the /last/ frame flip using
win.lastFrameT (the time is synchronised with logging.defaultClock so it will
match any logging commands that your script uses).

.. _blockingOnVBI:

'Blocking' on the VBI
~~~~~~~~~~~~~~~~~~~~~

As of version 1.62 PsychoPy 'blocks' on the vertical blank interval meaning
that, once Window.flip() has been called, no code will be executed until that
flip actually takes place. The timestamp for the above frame interval
measurements is taken immediately after the flip occurs. Run the timeByFrames
demo in Coder to see the precision of these measurements on your system. They
should be within 1ms of your mean frame interval.

Note that Intel integrated graphics chips (e.g. GMA 945) under win32 do not sync
to the screen at all and so blocking on those machines is not possible.
