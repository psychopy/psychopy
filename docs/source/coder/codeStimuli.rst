Presenting Stimuli
----------------------

.. note::

    Before you start, tell PsychoPy about your monitor(s) using the :ref:`monitorCenter`. That way you get to use units (like degrees of visual angle) that will transfer easily to other computers.

Stimulus objects
~~~~~~~~~~~~~~~~~~~~~~~~~~
Python is an 'object-oriented' programming language, meaning that most stimuli in PsychoPy are represented by python objects, with various associated methods and information.

Typically you should create your stimulus with the initial desired attributes once, at the beginning of the script, and then change select attributes later (see section below on setting stimulus attributes). For instance, create your text and then change its color any time you like::

    from psychopy import visual, core
    win = visual.Window([400,400])
    message = visual.TextStim(win, text='hello')
    message.autoDraw = True  # Automatically draw every frame
    win.flip()
    core.wait(2.0)
    message.text = 'world'  # Change properties of existing stim
    win.flip()
    core.wait(2.0)

Setting stimulus attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Stimulus attributes are typically set using either
         - a string, which is just some characters (as `message.text = 'world'` above)
         - a scalar (a number; see below)
         - an x,y-pair (two numbers; see below)

.. _attrib-xy:

**x,y-pair:**
    PsychoPy is very flexible in terms of input. You can specify the widely
    used x,y-pairs using these types:

        - A Tuple (x, y) with two elements
        - A List [x, y] with two elements
        - A numpy array([x, y]) with two elements

    However, PsychoPy always converts the x,y-pairs to numpy arrays internally.
    For example, all three assignments of pos are equivalent here::

        stim.pos = (0.5, -0.2)  # Right and a bit up from the center
        print stim.pos  # array([0.5, -0.2])

        stim.pos = [0.5, -0.2]
        print stim.pos  # array([0.5, -0.2])

        stim.pos = numpy.array([0.5, -0.2])
        print stim.pos  # array([0.5, -0.2])

    Choose your favorite :-) However, you can't assign elementwise::

        stim.pos[1] = 4  # has no effect

.. _attrib-scalar:

**Scalar:**
    Int or Float.

    Mostly, scalars are no-brainers to understand. E.g.::

        stim.ori = 90  # Rotate stimulus 90 degrees
        stim.opacity = 0.8  # Make the stimulus slightly transparent.

    However, scalars can also be used to assign x,y-pairs. In that case, both
    x and y get the value of the scalar. E.g.::

        stim.size = 0.5
        print stim.size  # array([0.5, 0.5])

.. _attrib-operations:

**Operations on attributes:**
    Operations during assignment of attributes are a handy way to smoothly
    alter the appearance of your stimuli in loops.

    Most scalars and x,y-pairs support the basic operations::

        stim.attribute += value  # addition
        stim.attribute -= value  # subtraction
        stim.attribute *= value  # multiplication
        stim.attribute /= value  # division
        stim.attribute %= value  # modulus
        stim.attribute **= value # power

    They are easy to use and understand on scalars::

        stim.ori = 5     # 5.0, set rotation
        stim.ori += 3.8  # 8.8, rotate clockwise
        stim.ori -= 0.8  # 8.0, rotate counterclockwise
        stim.ori /= 2    # 4.0, home in on zero
        stim.ori **= 3   # 64.0, exponential increase in rotation
        stim.ori %= 10   # 4.0, modulus 10

    However, they can also be used on x,y-pairs in very flexible ways. Here you
    can use both scalars and x,y-pairs as operators. In the latter case, the
    operations are element-wise::

        stim.size = 5           # array([5.0, 5.0]), set quadratic size
        stim.size +=2           # array([7.0, 7.0]), increase size
        stim.size /= 2          # array([3.5, 3.5]), downscale size
        stim.size += (0.5, 2.5) # array([4.0, 6.0]), a little wider and much taller
        stim.size *= (2, 0.25)  # array([8.0, 1.5]), upscale horizontal and downscale vertical

    Operations are not meaningful for strings.


Timing
~~~~~~~~~~~
There are various ways to measure and control timing in PsychoPy:
    - using frame refresh periods (most accurate, least obvious)
    - checking the time on :class:`~core.Clock` objects
    - using :func:`core.wait()` commands (most obvious, least flexible/accurate)

Using core.wait(), as in the above example, is clear and intuitive in your script. But it can't be used while something is changing. For more flexible timing, you could use a :class:`~core.Clock()` object from the :mod:`core` module::

    from psychopy import visual, core

    # Setup stimulus
    win = visual.Window([400, 400])
    gabor = visual.GratingStim(win, tex='sin', mask='gauss', sf=5, name='gabor')
    gabor.autoDraw = True  # Automatically draw every frame
    gabor.autoLog = False  # Or we'll get many messages about phase change

    # Let's draw a stimulus for 2s, drifting for middle 0.5s
    clock = core.Clock()
    while clock.getTime() < 2.0:  # Clock times are in seconds
        if 0.5 <= clock.getTime() < 1.0:
            gabor.phase += 0.1  # Increment by 10th of cycle
        win.flip()

Clocks are accurate to around 1ms (better on some platforms), but using them to time stimuli is not very accurate because it fails to account for the fact that one frame on your monitor has a fixed frame rate. In the above, the stimulus does not actually get drawn for exactly 0.5s (500ms). If the screen is refreshing at 60Hz (16.7ms per frame) and the `getTime()` call reports that the time has reached 1.999s, then the stimulus will draw again for a frame, in accordance with the `while` loop statement and will ultimately be displayed for 2.0167s. Alternatively, if the time has reached 2.001s, there will not be an extra frame drawn. So using this method you get timing accurate to the nearest frame period but with little consistent precision. An error of 16.7ms might be acceptable to long-duration stimuli, but not to a brief presentation. It also might also give the false impression that a stimulus can be presented for any given period. At 60Hz refresh you can not present your stimulus for, say, 120ms; the frame period would limit you to a period of 116.7ms (7 frames) or 133.3ms (8 frames).

As a result, the most precise way to control stimulus timing is to present them for a specified number of frames. The frame rate is extremely precise, much better than ms-precision. Calls to `Window.flip()` will be synchronised to the frame refresh; the script will not continue until the flip has occurred. As a result, on most cards, as long as frames are not being 'dropped' (see :ref:`detectDroppedFrames`) you can present stimuli for a fixed, reproducible period.

.. note::

    Some graphics cards, such as Intel GMA graphics chips under win32, don't support frame sync. Avoid integrated graphics for experiment computers wherever possible.

Using the concept of fixed frame periods and `flip()` calls that sync to those periods we can time stimulus presentation extremely precisely with the following::

    from psychopy import visual, core

    # Setup stimulus
    win = visual.Window([400, 400])
    gabor = visual.GratingStim(win, tex='sin', mask='gauss', sf=5,
        name='gabor', autoLog=False)
    fixation = visual.GratingStim(win, tex=None, mask='gauss', sf=0, size=0.02,
        name='fixation', autoLog=False)

    # Let's draw a stimulus for 200 frames, drifting for frames 50:100
    for frameN in range(200):   # For exactly 200 frames
        if 10 <= frameN < 150:  # Present fixation for a subset of frames
            fixation.draw()
        if 50 <= frameN < 100:  # Present stim for a different subset
            gabor.phase += 0.1  # Increment by 10th of cycle
            gabor.draw()
        win.flip()

Using autoDraw
~~~~~~~~~~~~~~~~~~~
Stimuli are typically drawn manually on every frame in which they are needed, using the `draw()` function. You can also set any stimulus to start drawing every frame using `stim.autoDraw = True` or `stim.autoDraw = False`. If you use these commands on stimuli that also have `autoLog=True`, then these functions will also generate a log message on the frame when the first drawing occurs and on the first frame when it is confirmed to have ended.
