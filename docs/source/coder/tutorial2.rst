Tutorial 2: Measuring a JND using a staircase procedure
========================================================================

This tutorial builds an experiment to test your just-noticeable-difference (JND) to orientation, that is it determines the smallest angular deviation that is needed for you to detect that a gabor stimulus isn't vertical (or at some other reference orientation). The method presents a pair of stimuli at once with the observer having to report with a key press whether the left or the right stimulus was at the reference orientation (e.g. vertical).

You can download the `full code here <https://raw.githubusercontent.com/psychopy/psychopy/master/docs/source/coder/tutorial2.py>`_.
Note that the entire experiment is constructed of less than 100 lines of code, including the initial presentation of a dialogue for parameters, generation and presentation of stimuli, running the trials, saving data and outputting a simple summary analysis for feedback. Not bad, eh?

There are a great many modifications that can be made to this code, however this example is designed to demonstrate how much can be achieved with very simple code. Modifying existing is an excellent way to begin writing your own scripts, for example you may want to try changing the appearance of the text or the stimuli.

Get info from the user
---------------------------------

The first lines of code import the necessary libraries. We need lots of the PsychoPy modules for a full experiment, as well as `numpy` (which handles various numerical/mathematical functions):

.. literalinclude:: tutorial2.py
    :linenos:
    :lineno-start: 1
    :lines: 1-4

Also note that there are two ways to insert comments in Python (and you should do this often!). Using triple quotes, as in `"""Here's my comment"""`, allows you to write a comment that can span several lines. Often you need that at the start of your script to leave yourself a note about the implementation and history of what you've written. For single-line comments, as you'll see below, you can use a simple `#` to indicate that the rest of the line is a comment.

The ``try:...except:...`` lines allow us to try and load a parameter file from a previous run of the experiment. If that fails (e.g. because the experiment has never been run) then create a default set of parameters. These are easy to store in a `python dictionary`_ that we'll call `expInfo`:

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 6
   :lines: 6-10

The last line adds the current date to to the information, whether we loaded from a previous run or created default values.

.. _python dictionary :  `http://docs.python.org/tut/node7.html#SECTION007500000000000000000`

So having loaded those parameters, let's allow the user to change them in a dialogue box (which we'll call ``dlg``). This is the simplest form of dialogue, created directly from the dictionary above. the dialogue will be presented immediately to the user and the script will wait until they hit *OK* or *Cancel*.

If they hit *OK* then dlg.OK=True, in which case we'll use the updated values and save them straight to a parameters file (the one we try to load above).

If they hit *Cancel* then we'll simply quit the script and not save the values.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 11
   :lines: 11-16

Setup the information for trials
---------------------------------

We'll create a file to which we can output some data as text during each trial (as well as :ref:`outputting a binary file <data-output>` at the end of the experiment). PsychoPy actually has supporting functions to do this automatically, but here we're showing you the manual way to do it.

We'll create a filename from the subject+date+".csv" (note how easy it is to concatenate strings in python just by 'adding' them). :term:`csv` files can be opened in most spreadsheet packages. Having opened a text file for writing, the last line shows how easy it is to send text to this target document.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 18
   :lines: 18-21

PsychoPy allows us to set up an object to handle the presentation of stimuli in a staircase procedure, the :class:`~psychopy.data.StairHandler`. This will define the increment of the orientation (i.e. how far it is from the reference orientation). The staircase can be configured in many ways, but we'll set it up to begin with an increment of 20deg (very detectable) and home in on the 80% threshold value. We'll step up our increment every time the subject gets a wrong answer and step down if they get three right answers in a row. The step size will also decrease after every 2 reversals, starting with an 8dB step (large) and going down to 1dB steps (smallish). We'll finish after 50 trials.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 23
   :lines: 23-27

Build your stimuli
---------------------------------

Now we need to create a window, some stimuli and timers. We need a `~psychopy.visual.Window` in which to draw our stimuli, a fixation point and two `~psychopy.visual.GratingStim` stimuli (one for the target probe and one as the foil). We can have as many timers as we like and reset them at any time during the experiment, but I generally use one to measure the time since the experiment started and another that I reset at the beginning of each trial.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 29
   :lines: 29-40

Once the stimuli are created we should give the subject a message asking if they're ready. The next two lines create a pair of messages, then draw them into the screen and then update the screen to show what we've drawn. Finally we issue the command event.waitKeys() which will wait for a keypress before continuing.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 42
   :lines: 42-51

Control the presentation of the stimuli
-------------------------------------------------------
OK, so we have everything that we need to run the experiment. The following uses a for-loop that will iterate over trials in the experiment. With each pass through the loop the :data:`staircase` object will provide the new value for the intensity (which we will call :data:`thisIncrement`). We will randomly choose a side to present the target stimulus using :func:`numpy.random.random()`, setting the position of the target to be there and the foil to be on the other side of the fixation point.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 53
   :lines: 53-57

Then set the orientation of the foil to be the reference orientation plus :data:`thisIncrement`, draw all the stimuli (including the fixation point) and update the window.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 59
   :lines: 59-66

Wait for presentation time of 500ms and then blank the screen (by updating the screen after drawing just the fixation point).

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 68
   :lines: 68-69

(This is not the most precise way to time your stimuli - you'll probably overshoot by one frame - but its easy to understand. PsychoPy allows you to present a stimulus for acertian number of screen refreshes instead which is better for short stimuli.)

Get input from the subject
---------------------------------
Still within the for-loop (note the level of indentation is the same) we need to get the response from the subject. The method works by starting off assuming that there hasn't yet been a response and then waiting for a key press. For each key pressed we check if the answer was correct or incorrect and assign the response appropriately, which ends the trial. We always have to clear the event buffer if we're checking for key presses like this

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 75
   :lines: 75-88

Now we must tell the staircase the result of this trial with its :meth:`.addData()` method. Then it can work out whether the next trial is an increment or decrement. Also, on each trial (so still within the for-loop) we may as well save the data as a line of text in that .csv file we created earlier.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 90
   :lines: 90-93

.. _data-output:

Output your data and clean up
-----------------------------

OK! We're basically done! We've reached the end of the for-loop (which occurred because the staircase terminated) which means the trials are over. The next step is to close the text data file and also save the staircase as a binary file (by 'pickling' the file in Python speak) which maintains a lot more info than we were saving in the text file.

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 95
   :lines: 95-97

While we're here, it's quite nice to give some immediate feedback to the user. Let's tell them the intensity values at the all the reversals and give them the mean of the last 6. This is an easy way to get an estimate of the threshold, but we might be able to do a better job by trying to reconstruct the psychometric function. To give that a try see the staircase analysis script of :doc:`Tutorial 3 <tutorial3>`.

Having saved the data you can give your participant some feedback and quit!

.. literalinclude:: tutorial2.py
   :linenos:
   :lineno-start: 99
   :lines: 99-116
