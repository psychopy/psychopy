Presenting Stimuli
----------------------

.. note::
    
    Before you start, tell PsychoPy about your monitor(s) using the :ref:`monitorCenter`. That way you get to use units (like degrees of visual angle) that will transfer easily to other computers.
    
Stimulus objects
~~~~~~~~~~~~~~~~~~~~~~~~~~
Python is an 'object-oriented' programming language, meaning that Most stimuli in PsychoPy are represented by python objects, with various associated methods and information.

Typically you should create your stimulus once, at the beginning of the script, and then change it as you need to later using set____() commands. For instance, create your text and then change its color any time you like::

    from psychopy import visual, core
    win=visual.Window([400,400])
    message = visual.TextStim(win, text='hello')
    message.setAutoDraw(True)#automatically draw every frame
    win.flip()
    core.wait(2.0)
    message.setText('world')#change properties of existing stim
    win.flip()
    core.wait(2.0)

Timing
~~~~~~~~~~~
There are various ways to measure and control timing in PsychoPy:
    - using frame refresh periods (most accurate, least obvious)
    - checking the time on :class:`~core.Clock` objects
    - using :func:`core.wait()` commands (most obvious, least flexible/accurate)
    
Using core.wait(), as in the above example, is clear and intuitive in your script. But it can't be used while something is changing. For more flexible timing, you could use a :class:`~core.Clock()` object from the :mod:`core` module::

    from psychopy import visual, core
    
    #setup stimulus
    win=visual.Window([400,400])
    gabor = visual.PatchStim(win, tex='sin', mask='gauss',sf=5, name='gabor')
    gabor.setAutoDraw(True)#automatically draw every frame
    gabor.autoLog=False#or we'll get many messages about phase change
    
    clock = core.Clock()
    #let's draw a stimulus for 2s, drifting for middle 0.5s
    while clock.getTime()<2.0:#clock times are in seconds
        if 0.5<=clock.getTime()<1.0:
            gabor.setPhase(0.1, '+')#increment by 10th of cycle
        win.flip()

Clocks are accurate to around 1ms (better on some platforms), but using them to time stimuli is not very accurate because it fails to account for the fact that one frame on your monitor has a fixed frame rate. In the above, the stimulus does not actually get drawn for exactly 0.5s (500ms). If the screen is refreshing at 60Hz (16.7ms per frame) and the `getTime()` call reports that the time has reached 1.999s, then the stimulus will draw again for a frame, in accordance with the `while` loop statement and will ultimately be displayed for 2.0167s. Alternatively, if the time has reached 2.001s, there will not be an extra frame drawn. So using this method you get timing accurate to the nearest frame period but with little consistent precision. An error of 16.7ms might be acceptable to long-duration stimuli, but not to a brief presentation. It also might also give the false impression that a stimulus can be presented for any given period. At 60Hz refresh you can not present your stimulus for, say, 120ms; the frame period would limit you to a period of 116.7ms (7 frames) or 133.3ms (8 frames).

As a result, the most precise way to control stimulus timing is to present them for a specified number of frames. The frame rate is extremely precise, much better than ms-precision. Calls to `Window.flip()` will be synchronised to the frame refresh; the script will not continue until the flip has occured. As a result, on most cards, as long as frames are not being 'dropped' (see :ref:`detectDroppedFrames`) you can present stimuli for a fixed, reproducible period.

.. note::

    Some graphics cards, such as Intel GMA graphics chips under win32, don't support frame sync. Avoid integrated graphics for experiment computers wherever possible.
    
Using the concept of fixed frame periods and `flip()` calls that sync to those periods we can time stimulus presentation extremely precisely with the following::

    from psychopy import visual, core
    
    #setup stimulus
    win=visual.Window([400,400])
    gabor = visual.PatchStim(win, tex='sin', mask='gauss',sf=5, 
        name='gabor', autoLog=False)
    fixation = visual.PatchStim(win, tex=None, mask='gauss',sf=0, size=0.02,
        name='fixation', autoLog=False)
    
    clock = core.Clock()
    #let's draw a stimulus for 2s, drifting for middle 0.5s
    for frameN in range(200):#for exactly 200 frames
        if 10<=frameN<150:#present fixation for a subset of frames
            fixation.draw()
        if 50<=frameN<100:#present stim for a different subset
            gabor.setPhase(0.1, '+')#increment by 10th of cycle
            gabor.draw()
        win.flip()
        
Using autoDraw
~~~~~~~~~~~~~~~~~~~
Stimuli are typically drawn manually on every frame in which they are needed, using the `draw()` function. You can also set any stimulus to start drawing every frame using `setAutoDraw(True)` or `setAutoDraw(False)`. If you use these commands on stimuli that also have `autoLog=True`, then these functions will also generate a log message on the frame when the first drawing occurs and on the first frame when it is confirmed to have ended.
