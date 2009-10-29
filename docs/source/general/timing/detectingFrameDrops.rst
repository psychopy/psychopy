Detecting dropped frames
--------------------------

Occasionally you will drop frames if you
* try to do too much drawing
* do it in an innefficient manner (write poor code)
* have a poor computer/graphics card

Things to avoid:
* recreating textures for stimuli
* building new stimuli from scratch (create them once at the top of your script and then change them using :meth:`stim.setOri(ori)`,`stim.setPos([x,y]...)`

Turn on frame time recording
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The key sometimes is ''knowing'' if you are dropping frames. PsychoPy can help with that by keeping track of frame durations. By default, frame time tracking is turned off because many people don't need it, but it can be turned on any time after :class:`~psychopy.visual.Window` creation  :meth:`setRecordFrameIntervals(True)`, e.g.:

    from psychopy import visual
    win = visual.Window([800,600])
    win.setRecordFrameIntervals(True) 

Since there are often dropped frames just after the system is initialised, it makes sense to start off with a fixation period, or a ready message and don't start recording frame times until that has ended. Obviously if you aren't refreshing the window at some point (e.g. waiting for a key press with an unchanging screen) then you should turn off the recording of frame times or it will give spurious results.

Warn me if I drop a frame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to check if a frame has been dropped is to get PsychoPy to report a warning if it thinks a frame was dropped::

    from psychopy import visual, log
    win = visual.Window([800,600])
    win.setRecordFrameIntervals(True)
    win._refreshThreshold=1/85.0+0.004 #i've got 85Hz monitor and want to allow 4ms tolerance
    #set the log module to report warnings to the std output window (default is errors only)
    log.console.setLevel(log.ERROR)

The above code will spit a warning message only if the the current frame AND the average of current and the previous frames exceed self._refreshThreshold value (often a long frame is making up for an 'apparently' brief previous frame - see below).

Show me all the frame times that I recorded
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While recording frame times, these are simply appended, every frame to 
win.frameIntervals (a list). You can simply plot these at the end of your script using pylab::

    import pylab
    pylab.plot(win.frameIntervals)
    pylab.show()

Or you could save them to disk. A convenience function is provided for this::

    win.saveFrameIntervals(fileName=None, clear=True)

The above will save the currently stored frame intervals (using the default filename, 'lastFrameIntervals.log') and then clears the data. The saved file is a simple text file.

'Blocking' on the VBI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should see that most of your frame times are sitting roughly at the frame period for you monitor (with very little variability). At times you might see that frames are suddenly high, and these are most likely dropped frames. However, you might also be seeing bi-directional spikes where a very short frame is followed by a long one, with their average being the same as the nominal frame rate. This is caused by the fact that the graphics card will 'block' (wait for the frame to end before returning to the script) only if a frame is already waiting to pass through the pipeline [straw2008]_. 

.. [straw2008] Andrew Straw (2008) Vision egg: an open-source library for realtime visual stimulus generation. Front Neuroinformatics. 2008;2:4

So, when your graphics card is easily keeping up with drawing you see no spikes at all (it always has a spare frame queued-up so always 'blocks'. When the graphics card is ''just'' keeping up it doesn't always have the back-up frame ready, so doesn't block and the result is that the frame ''looks'' very brief (it was actually displayed at the same time), but is then followed by one that ''looks'' very long. I don't think these are a problem for most experiments - when they occur during the presentation of moving dots you don't see the characteristic judder of a dropped frame. When the drawing is falling so far behind that it fails to draw within the frame you get the simple skip of a frame, which you see as a single long frame, without the short one. This is a dropped frame and IS likely to be a problem for many experiments.
