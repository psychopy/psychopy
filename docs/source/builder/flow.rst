.. _flow:

Flow
----------------

In the Flow panel a number of :doc:`Routines <builder/routines>` can be combined to form an experiment. For instance, your study may have a :doc:`Routine <builder/routines>` that presented initial instructions and waited for a key to be pressed, followed by a :doc:`Routine <builder/routines>` that presented one trial which should be repeated 5 times with various different parameters set. All of this is achieved in the Flow panel. You can adjust the display size of the Flow panel (see View menu).

Adding Routines
~~~~~~~~~~~~~~~~~

The :doc:`Routines <builder/routines>` that the Flow will use should be generated first (although their contents can be added or altered at any time). To insert a :doc:`Routine <builder/routines>` into the Flow click the appropriate button in the left of the Flow panel or use the Experiment menu. A dialog box will appear asking which of your :doc:`Routines <builder/routines>` you wish to add. To select the location move the mouse to the section of the flow where you wish to add it and click on the black disk.

.. _loops:

Loops
~~~~~~~~~~~~~~~
Loops control the repetition of :ref:`routines` and the choice of stimulus parameters for each. To insert a loop use the button on the left of the Flow panel, or the item in the Experiment menu of the Builder. The start and end of a loop is set in the same way as the location of a :doc:`Routine <builder/routines>` (see above). Loops can encompass one or more :doc:`Routines <builder/routines>` and other loops (i.e. they can be nested).

As with components in :ref:`routines`, the loop must be given a name, which must be unique and made up of only alpha-numeric characters (underscores are allowed). I would normally use a plural name, since the loop represents multiple repeats of something. For example, `trials`, `blocks` or `epochs` would be good names for your loops.

It is usually best to use trial information that is contained in an external file (.xlsx or .csv). When inserting a `loop` into the `flow` you can browse to find the file you wish to use for this. An example of this kind of file can be found in the Stroop demo (trialTypes.xlsx). The column names are turned into variables (in this case text, letterColor, corrAns and congruent), these can be used to define parameters in the loop by putting a $ sign before them e.g. `$text`.

As the column names from the input file are used in this way they must have legal variable names i.e. they must be unique, have no punctuation or spaces (underscores are ok) and must not start with a digit.

The parameter `Is trials` exists because some loops are not there to indicate trials *per se* but a set of stimuli within a trial, or a set of blocks. In these cases we don't want the data file to add an extra line with each pass around the loop. This parameter can be unchecked to improve (hopefully) your data file outputs. [Added in v1.81.00]

.. _trialTypes:

Loop types
^^^^^^^^^^^^^^^^^^^^^
You can use a number of different "Loop Types" in PsychoPy, this controls the way in which the trials you have fed into the "Conditions" field are presented. Imagine you have a conditions file that looks like this::

  letter
  a
  b
  c

After saving this as a spreadsheet (.xlsx or .csv), we could then add this to the "Conditions" field of our loop. Let's imagine we want to present each letter twice, so we set `nReps` to 2.  We could then use the following Loop Types:

*   **Random** - present a - b in a random order, because we have nReps at 2, this would be repeated twice e.g. :code:`[c, a, b, a, c, b]`
*   **Full Random** - present a - b in a random order but also take into account the number of nReps. Here, imagine that rather than having 3 items in the bag that we sample from, and repeat this twice, we instead have 6 items int he bag that are randomly sampled from. This would mean that with fullRandom, but not random, it would be possible to get the following order of trials e.g. :code:`[a, a, b, c, c, b]` - notice that a was sampled twice in the first 2 trials.
*   **sequential** - present the rows in the order they are set i nt he spreadsheet. Currently PsychoPy does not have inbuilt support for specific randomisation constraints, so if you need a specific pseudorandom order, preset this in your spreadsheet file and use a "sequential" loopType.
*   **staircase** - for use with adaptive procedures, create an output variable called :code:`level` that can then be used to set the parameter of a stimulus (e.g. it's opacity) in an adaptive fashion. This allows researchers to converge upon a participants threshold by adjusting the value of :code:`level` in accordance with performance.
*   **interleaved staircases** - for use with multiple staircases that are interleaved. This can also be used to implement other staircasing algorithms such as `QUEST (Watson and Pelli, 1983) <https://link.springer.com/content/pdf/10.3758/BF03202828.pdf>`_ via :class:`QuestHandler`.


Selecting a subset of conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the standard :ref:`trialTypes` you would use all the rows/conditions within your conditions file. However there are often times when you want to select a subset of your trials before randomising and repeating.

The parameter `Select rows` allows this. You can specify which rows you want to use by inserting values here:

*   `0,2,5` gives the 1st, 3rd and 6th entry of a list - Python starts with index zero)
*   `$random(4)*10` gives 4 indices from 0 to 9 (so selects 4 out of 10 conditions)
*   `5:10` selects the 6th to 10th rows
*   `$myIndices` uses a variable that you've already created

Note in the last case that `5:8` isn't valid syntax for a variable so you cannot do::

    myIndices = 5:8

but you can do::

    myIndices = slice(5,8) #python object to represent a slice
    myIndices = "5:8" #a string that PsychoPy can then parse as a slice later
    myIndices = "5:8:2" #as above but

Note that PsychoPy uses Python's built-in slicing syntax (where the first index is zero and the last entry of a slice doesn't get included). You might want to check the outputs of your selection in the Python shell (bottom of the Coder view) like this::

    >>> range(100)[5:8] #slice 5:8 of a standard set of indices
    [5, 6, 7]
    >>> range(100)[5:10:2] #slice 5:8 of a standard set of indices
    [5, 7, 9, 11, 13, 15, 17, 19]

Check that the conditions you wanted to select are the ones you intended!

.. _accessingParams:

Using loops to update stimuli trial-by-trial
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Once you have a loop arount the routine you want to repeat, you can use the variables created in your conditions file to update any parameter within your routine. For example, let's say that you have a conditions file that looks like this::

  letter
  a
  b
  c

You could then add a Text component and in the *text* field type :code:`$letter` and then set the corresponding dropsown box to "set every repeat". This indicates that you want the value of this parameter to change on each iteration of your loop, and the value of that parameter on each loop will correspond to the value of "letter" drawn on each trial.

.. note::
    You only need to use the $ sign if that field name does not already contain a $ sign! You also don't need several dollar signs in a field e.g. you wouldn't set the position of a stimulys on each repeat using :code:`($myX, $myY)` instead you would just use :code:`$(myX, myY)` - this is because the dollar sign indicates that this field will now accept python code, rather than that this value corresponds to a variable.
