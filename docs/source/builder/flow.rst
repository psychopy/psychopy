.. _flow:

Flow
----------------

In the Flow panel a number of :doc:`Routines </builder/routines>` can be combined to form an experiment. For instance, your study may have a :doc:`Routine </builder/routines>` that presented initial instructions and waited for a key to be pressed, followed by a :doc:`Routine </builder/routines>` that presented one trial which should be repeated 5 times with various different parameters set. All of this is achieved in the Flow panel.

Adding Routines
~~~~~~~~~~~~~~~~~

The :doc:`Routines </builder/routines>` that the Flow will use should be generated first (although their contents can be added or altered at any time). To insert a :doc:`Routine </builder/routines>` into the Flow click the appropriate button in the left of the Flow panel or use the Experiment menu. A dialog box will appear asking which of your :doc:`Routines </builder/routines>` you wish to add and where to add it. To select the location choose the number (being shown in small black disks on the timeline) that corresponds to the location for your :doc:`Routine </builder/routines>`. Note that the numbers do not represent physical units of time (e.g. seconds), merely an ordering.

.. _loops:

Loops
~~~~~~~~~~~~~~~
Loops control the repetition of :ref:`routines` and the choice of stimulus parameters for each. PsychoPy can generate the next trial based on the :term:`method of constants` or using an :term:`adaptive staircase`. To insert a loop use the button on the left of the Flow panel, or the item in the Experiment menu of the Builder. The start and end of a loop is set in the same way as the location of a :doc:`Routine </builder/routines>` (see above) using numbers to indicate the entry points on the time line. Loops can encompass one or more :doc:`Routines </builder/routines>` and other loops (i.e. they can be nested).

As with components in :ref:`routines`, the loop must be given a name, which must be unique and made up of only alpha-numeric characters (underscores are allowed). I would normally use a plural name, since the loop represents multiple repeats of something. For example, `trials`, `blocks` or `epochs` would be good names for your loops.

.. _trialTypes:

Method of Constants
^^^^^^^^^^^^^^^^^^^^^
Selecting a loop type of `random` or `sequential` will result in a :term:`method of constants` experiment, whereby the types of trials that can occur are predetermined. In this case, a file must be provided that describes the parameters for the repeats. This should be an Excel 2007 (:term:`xlsx`) file or a comma-separated-value (:term:`csv`) file in which columns refer to parameters that are needed to describe stimuli etc and rows one for each type of trial. These can easily be generated from a spreadsheet package like excel. The top row should give headers; text labels describing the contents of that column (which must also not include spaces or other characters other than letters, numbers or underscores). For example, a file containing the following table::

  ori	text	corrAns
  0	aaa	left
  90	aaa	left
  0	bbb	right
  90	bbb	right

would represent 4 different conditions (trial types) with parameters ori, text and corrAns. It's really useful to include a column called corrAns that shows what the correct key press is going to be for this trial (if there is one).

If the loop type is `sequential` then, on each iteration of the :ref:`routines`, the next row will be selected in order, whereas under the `random` type the next row will be selected randomly. `nReps` determines how many repeats will be performed (for all conditions). All conditions will be presented once before the second repeat etc.

Staircase methods
^^^^^^^^^^^^^^^^^^^
The loop type `staircase` allows the implementation of simple up-down staircases where an intensity value is varied trial-by-trial according to certain parameters. For this type of loop a 'correct answer' must be provided from something like a :doc:`components/keyboard`. Various parameters for the staircase can be set to govern how many trials will be conducted and how many correct or incorrect answers make the staircase go up or down.

.. _accessingParams:

Accessing loop parameters from components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The parameters from your loops are accessible to any component enclosed within that loop. The simplest (and default) way to address these variables is simply to call them by the name of the parameter, prepended with `$` to indicate that this is the name of a variable. For example, if your Flow contains a loop with the above table as its input trial types file then you could give one of your stimuli an orientation `$ori` which would depend on the current trial type being presented. Example scenarios:

#. You want to loop randomly over some conditions in a loop called `trials`. Your conditions are stored in a csv file with headings 'ori', 'text', 'corrAns' which you provide to this loop. You can then access these values from any component using `$ori`, `$text`, and `$corrAns`
#. You create a random loop called `blocks` and give it an excel file with a single column called `movieName` listing filenames to be played. On each repeat you can access this with `$movieName`
#. You create a staircase loop called `stairs`. On each trial you can access the current value in the staircase with `$thisStair`

.. note::
    When you set a component to use a parameter that will change (e.g on each repeat through the loop) you should **remember to change the component parameter from `constant` to `set every repeat` or `set every frame`** or it won't have any effect!

Reducing namespace clutter (advanced)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The downside of the above approach is that the names of trial parameters must be different between every loop, as well as not matching any of the predefined names in python, numpy and PsychoPy. For example, the stimulus called `movie` cannot use a parameter also called `movie` (so you need to call it `movieName`). An alternative method can be used without these restrictions. If you set the Builder preference `unclutteredNamespace` to True you can then access the variables by referring to parameter as an attribute of the singular name of the loop prepended with `this`. For example, if you have a loop called `trials` which has the above file attached to it, then you can access the stimulus ori with `$thisTrial.ori`. If you have a loop called `blocks` you could use `$thisBlock.corrAns`.

Now, although the name of the loop must still be valid and unique, the names of the parameters of the file do not have the same requirements (they must still not contain spaces or punctuation characters).
