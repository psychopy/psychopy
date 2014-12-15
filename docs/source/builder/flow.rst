.. _flow:

Flow
----------------

In the Flow panel a number of :doc:`Routines </builder/routines>` can be combined to form an experiment. For instance, your study may have a :doc:`Routine </builder/routines>` that presented initial instructions and waited for a key to be pressed, followed by a :doc:`Routine </builder/routines>` that presented one trial which should be repeated 5 times with various different parameters set. All of this is achieved in the Flow panel. You can adjust the display size of the Flow panel (see View menu).

Adding Routines
~~~~~~~~~~~~~~~~~

The :doc:`Routines </builder/routines>` that the Flow will use should be generated first (although their contents can be added or altered at any time). To insert a :doc:`Routine </builder/routines>` into the Flow click the appropriate button in the left of the Flow panel or use the Experiment menu. A dialog box will appear asking which of your :doc:`Routines </builder/routines>` you wish to add. To select the location move the mouse to the section of the flow where you wish to add it and click on the black disk.

.. _loops:

Loops
~~~~~~~~~~~~~~~
Loops control the repetition of :ref:`routines` and the choice of stimulus parameters for each. PsychoPy can generate the next trial based on the :term:`method of constants` or using an :term:`adaptive staircase`. To insert a loop use the button on the left of the Flow panel, or the item in the Experiment menu of the Builder. The start and end of a loop is set in the same way as the location of a :doc:`Routine </builder/routines>` (see above). Loops can encompass one or more :doc:`Routines </builder/routines>` and other loops (i.e. they can be nested).

As with components in :ref:`routines`, the loop must be given a name, which must be unique and made up of only alpha-numeric characters (underscores are allowed). I would normally use a plural name, since the loop represents multiple repeats of something. For example, `trials`, `blocks` or `epochs` would be good names for your loops.

It is usually best to use trial information that is contained in an external file (.xlsx or .csv). When inserting a `loop` into the `flow` you can browse to find the file you wish to use for this. An example of this kind of file can be found in the Stroop demo (trialTypes.xlsx). The column names are turned into variables (in this case text, letterColor, corrAns and congruent), these can be used to define parameters in the loop by putting a $ sign before them e.g. `$text`.

As the column names from the input file are used in this way they must have legal variable names i.e. they must be unique, have no punctuation or spaces (underscores are ok) and must not start with a digit.

The parameter `Is trials` exists because some loops are not there to indicate trials *per se* but a set of stimuli within a trial, or a set of blocks. In these cases we don't want the data file to add an extra line with each pass around the loop. This parameter can be unchecked to improve (hopefully) your data file outputs. [Added in v1.81.00]

.. _trialTypes:

Method of Constants
^^^^^^^^^^^^^^^^^^^^^
Selecting a loop type of `random`, `sequential`, or `fullRandom` will result in a :term:`method of constants` experiment, whereby the types of trials that can occur are predetermined. That is, the trials cannot vary depending on how the subject has responded on a previous trial. In this case, a file must be provided that describes the parameters for the repeats. This should be an Excel 2007 (:term:`xlsx`) file or a comma-separated-value (:term:`csv` ) file in which columns refer to parameters that are needed to describe stimuli etc. and rows one for each type of trial. These can easily be generated from a spreadsheet package like Excel. (Note that csv files can also be generated using most text editors, as long as they allow you to save the file as "plain text"; other output formats will *not* work, including "rich text".) The top row should be a row of headers: text labels describing the contents of the respective columns. (Headers must also not include spaces or other characters other than letters, numbers or underscores and must not be the same as any variable names used elsewhere in your experiment.) For example, a file containing the following table::

  ori	text	corrAns
  0	aaa	left
  90	aaa	left
  0	bbb	right
  90	bbb	right

would represent 4 different conditions (or trial types, one per line). The header line describes the parameters in the 3 columns: ori, text and corrAns. It's really useful to include a column called corrAns that shows what the correct key press is going to be for this trial (if there is one).

If the loop type is `sequential` then, on each iteration through the :ref:`routines`, the next row will be selected in the order listed in the file. Under a `random` order, the next row will be selected at random (without replacement); it can only be selected again after all the other rows have also been selected. `nReps` determines how many repeats will be performed (for all conditions). The total number of trials will be the number of conditions (= number of rows in the file, not counting the header row) times the number of repetitions, `nReps`. With the `fullRandom` option, the entire list of trials including repetitions is used in random order, allowing the same item to appear potentially many times in a row, and to repeat without necessarily having done all of the other trials. For example, with 3 repetitions, a file of trial types like this::

  letter
  a
  b
  c

could result in the following possible sequences. `sequential` could only ever give one sequence with this order: [a b c a b c a b c]. `random` will give one of 216 different orders (= 3! * 3! * 3! = nReps * (nTrials!) ), for example: [b a c a b c c a b]. Here the letters are effectively in sets of (abc) (abc) (abc), and randomization is only done within each set, ensuring (for example) that there are at least two a's before the subject sees a 3rd b. Finally, `fullRandom` will return one of 362,880 different orders (= 9! = (nReps * nTrials)! ), such as [b b c a a c c a b], which `random` never would. There are no longer mini-blocks or "sets of trials" within the longer run. This means that, by chance, it would also be possible to get a very un-random-looking sequence like [a a a b b b c c c].

It is possible to achieve any sequence you like, subject to any constraints that are logically possible. To do so, in the file you specify every trial in the desired order, and the for the loop select `sequential` order and nReps=1.

Selecting a subset of conditions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the standard :ref:`trialTypes` you would use all the rows/conditions within your conditions file. However there are often times when you want to select a subset of your trials before randomising and repeating.

The parameter `Select rows` allows this. You can specify which rows you want to use by inserting values here:

    - `0,2,5` gives the 1st, 3rd and 5th entry of a list - Python starts with index zero)
    - `random(4)*10` gives 4 indices from 0 to 10 (so selects 4 out of 11 conditions)
    - `5:10` selects the 6th to 9th rows
    - `$myIndices` uses a variable that you've already created

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

.. _staircaseMethods:

Staircase methods
^^^^^^^^^^^^^^^^^^^
The loop type `staircase` allows the implementation of adaptive methods. That is, aspects of a trial can depend on (or "adapt to") how a subject has responded earlier in the study. This could be, for example, simple up-down staircases where an intensity value is varied trial-by-trial according to certain parameters, or a stop-signal paradigm to assess impulsivity. For this type of loop a 'correct answer' must be provided from something like a :doc:`components/keyboard`. Various parameters for the staircase can be set to govern how many trials will be conducted and how many correct or incorrect answers make the staircase go up or down.

.. _accessingParams:

Accessing loop parameters from components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The parameters from your loops are accessible to any component enclosed within that loop. The simplest (and default) way to address these variables is simply to call them by the name of the parameter, prepended with `$` to indicate that this is the name of a variable. For example, if your Flow contains a loop with the above table as its input trial types file then you could give one of your stimuli an orientation `$ori` which would depend on the current trial type being presented. Example scenarios:

#. You want to loop randomly over some conditions in a loop called `trials`. Your conditions are stored in a csv file with headings 'ori', 'text', 'corrAns' which you provide to this loop. You can then access these values from any component using `$ori`, `$text`, and `$corrAns`
#. You create a random loop called `blocks` and give it an Excel file with a single column called `movieName` listing filenames to be played. On each repeat you can access this with `$movieName`
#. You create a staircase loop called `stairs`. On each trial you can access the current value in the staircase with `$thisStair`

.. note::
    When you set a component to use a parameter that will change (e.g on each repeat through the loop) you should **remember to change the component parameter from `constant` to `set every repeat` or `set every frame`** or it won't have any effect!

Reducing namespace clutter (advanced)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The downside of the above approach is that the names of trial parameters must be different between every loop, as well as not matching any of the predefined names in python, numpy and PsychoPy. For example, the stimulus called `movie` cannot use a parameter also called `movie` (so you need to call it `movieName`). An alternative method can be used without these restrictions. If you set the Builder preference `unclutteredNamespace` to True you can then access the variables by referring to parameter as an attribute of the singular name of the loop prepended with `this`. For example, if you have a loop called `trials` which has the above file attached to it, then you can access the stimulus ori with `$thisTrial.ori`. If you have a loop called `blocks` you could use `$thisBlock.corrAns`.

Now, although the name of the loop must still be valid and unique, the names of the parameters of the file do not have the same requirements (they must still not contain spaces or punctuation characters).
