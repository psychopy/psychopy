.. _code:

Code Component
-------------------------------

.. only:: html

    .. image:: /images/code_component.gif
       :alt: A code component in action

This Component can be used to insert short pieces of python code into your experiments. This might
be
create
 a variable that you want for another :ref:`Component <components>`, to manipulate images before
displaying them, to interact with hardware for which there isn't yet a pre-packaged component in |PsychoPy| (e.g. writing code to interact with the serial/parallel ports). See `code uses`_ below.

Be aware that the code for each of the components in your :ref:`Routine <routines>` are executed in the order they appear on the :ref:`Routine <routines>` display (from top to bottom). If you want your `Code Component` to alter a variable to be used by another component immediately, then it needs to be above that component in the view. You may want the code not to take effect until next frame however, in which case put it at the bottom of the :ref:`Routine <routines>`. You can move `Components` up and down the :ref:`Routine <routines>` by right-clicking on their icons.

Within your code you can use other variables and modules from the script. For example, all routines have a stopwatch-style :class:`~psychopy.core.Clock` associated with them, which gets reset at the beginning of that repeat of the routine. So if you have a :ref:`Routine <routines>` called trial, there will be a :class:`~psychopy.core.Clock` called trialClock and so you can get the time (in sec) from the beginning of the trial by using::

    currentT = trialClock.getTime()

To see what other variables you might want to use, and also what terms you need to avoid in your chunks of code, :ref:`compile your script <compileScript>` before inserting the code object and take a look at the contents of that script.

Note that this page is concerned with `Code Components` specifically, and not all cases in which you might use python syntax within the Builder. It is also possible to put code into a non-code input field (such as the duration or text of a `Text Component`). The syntax there is slightly different (requiring a `$` to trigger the special handling, or `\\$` to avoid triggering special handling). The syntax to use within a Code Component is always regular python syntax.

Parameters
~~~~~~~~~~~~~~

Code type:
    What type of code will you write?

    *   *Py* - Python code only (for local use)
    *   *JS* - Javascript only (for online use)
    *   *Auto -> JS* - Write in python code on the left and this will be auto translated to Javascript on the right.
    *   *Both* - write both Python and Javascript, but independently of one another (Python will be executed when you run the task locally, JS will be executed when you run the task online)

Within a `Code Component` you can write code to be executed at 6 different points within the experiment. You can use as many or as few of these as you need for any `Code Component`:

Before Experiment:
    Things that need to be done just once, like importing a supporting module, which do not need the experiment window to exist yet.

Begin Experiment:
    Things that need to be done just once, like initialising a variable for later use, which may need to refer to the experiment window.

Begin Routine:
    Certain things might need to be done at the start of a :ref:`Routine <routines>` e.g. at the beginning of each trial you might decide which side a stimulus will appear.

Each Frame:
    Things that need to updated constantly, throughout the experiment. Note that these will be executed exactly once per video frame (on the order of every 10ms), to give dynamic displays. Static displays do not need to be updated every frame.

End Routine:
    At the end of the :ref:`Routine <routines>` (e.g. the trial) you may need to do additional things, like checking if the participant got the right answer

End Experiment:
    Use this for things like saving data to disk, presenting a graph(?), or resetting hardware to its original state.

.. _code uses:

Example code uses
~~~~~~~~~~~~~~~~~~~~~~~

1. Set a random location for your target stimulus
====================================================

There are many ways to do this, but you could add the following to the `Begin Routine` section of a `Code Component` at the top of your :ref:`Routine <routines>`. Then set your stimulus position to be `$(targetX, 0)` and set the correct answer field of a :ref:`keyboard` to be `$corrAns` (set both of these to update on every repeat of the Routine).::
    
    if random()>0.5:
        targetX=-0.5 #on the left
        corrAns='left'
    else:
        targetX=0.5#on the right
        corrAns='right'

2. Create a patch of noise 
====================================================

As with the above there are many different ways to create noise, but a simple method would be to add the following to the `Begin Routine` section of a `Code Component` at the top of your :ref:`Routine <routines>`. Then set the image as `$noiseTexture`.::

    noiseTexture = random.rand((128,128)) * 2.0 - 1

.. note::

    Don't expect all code components to work online. Remember that code components using specific python libraries such as numpy won't smoothly translate. You might want to view the `PsychoPy to Javascript crib sheet <https://discourse.psychopy.org/t/psychopy-python-to-javascript-crib-sheet/14601>`_ for useful info on using code components for online experiments.

3. Send a feedback message at the end of the experiment
=================================================================

Make a new routine, and place it at the end of the flow (i.e., the end of the experiment).
Create a `Code Component` with this in the `Begin Experiment` field::

    expClock = core.Clock()

and put this in the `Begin routine` field::

    msg = "Thanks for participating - that took' + str(expClock.getTime()/60.0)) + 'minutes in total'

Next, add a `Text Component` to the routine, and set the text to `$msg`. Be sure that the text field's updating is set to "Set every repeat" (and not "Constant").

4. End a loop early.
====================================================

Code components can also be used to control the end of a loop. For example imagine you want to end when a key response has been made 5 times::

    if key_resp.keys: # if a key response has been made
        if len(key_resp.keys) ==5: # if 5 key presses have been made
            continueRoutine = False # end the current routine
            trials.finished = True # exit the current loop (if your loop is called "trials"

What variables are available to use?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most complete way to find this out for your particular script is to :ref:`compile it <compileScript>` and take a look at what's in there. Below are some options that appear in nearly all scripts. Remember that those variables are Python objects and can have attributes of their own. You can find out about those attributes using::
    
    dir(myObject)

Common |PsychoPy| variables:

- expInfo: This is a Python Dictionary containing the information from the starting dialog box. e.g. That generally includes the 'participant' identifier. You can access that in your experiment using `exp['participant']`
- t: the current time (in seconds) measured from the start of this Routine
- frameN: the number of /completed/ frames since the start of the Routine (=0 in the first frame)
- win: the :class:`~psychopy.visual.Window` that the experiment is using

Your own variables:

- anything you've created in a Code Component is available for the rest of the script. (Sometimes you might need to define it at the beginning of the experiment, so that it will be available throughout.)
- the name of any other stimulus or the parameters from your file also exist as variables.
- most Components have a `status` attribute, which is useful to determine whether a stimulus has `NOT_STARTED`, `STARTED` or `FINISHED`. For example, to play a tone at the end of a Movie Component (of unknown duration) you could set start of your tone to have the 'condition' ::

    myMovieName.status==FINISHED

Selected contents of `the numpy library and numpy.random <http://docs.scipy.org/doc/numpy/reference/index.html>`_ are imported by default. The entire numpy library is imported as `np`, so you can use a several hundred maths functions by prepending things with 'np.':

- `random() <http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.rand.html>`_ , `randint() <http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.randint.html>`_ , `normal() <http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.normal.html>`_ , `shuffle() <http://docs.scipy.org/doc/numpy/reference/generated/numpy.random.shuffle.html>`_ options for creating arrays of random numbers.

- `sin()`, `cos()`, `tan()`, and `pi`: For geometry and trig. By default angles are in radians, if you want the cosine of an angle specified in degrees use `cos(angle*180/pi)`, or use numpy's conversion functions, `rad2deg(angle)` and `deg2rad(angle)`.

- `linspace() <http://docs.scipy.org/doc/numpy/reference/generated/numpy.linspace.html>`_: Create an array of linearly spaced values.

- `log()`, `log10()`: The natural and base-10 log functions, respectively. (It is a lowercase-L in log).

- `sum()`, `len()`: For the sum and length of a list or array. To find an average, it is better to use `average()` (due to the potential for integer division issues with `sum()/len()` ).

- `average()`, `sqrt()`, `std()`: For average (mean), square root, and standard deviation, respectively. **Note:** Be sure that the numpy standard deviation formula is the one you want!

- np.______: Many math-related features are available through the complete numpy libraries, which are available within psychopy builder scripts as 'np.'. For example, you could use `np.hanning(3)` or `np.random.poisson(10, 10)` in a code component.
