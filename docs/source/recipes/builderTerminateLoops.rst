.. _feedback:

Builder - terminating a loop
=========================================

People often want to terminate their :ref:`loops` before they reach the designated number of trials based on subjects' responses. For example, you might want to use a Loop to repeat a sequence of images that you want to continue until a key is pressed, or use it to continue a training period, until a criterion performance is reached.

To do this you need a :ref:`code` inserted into your :ref:`routine <routines>`. All loops have an attribute called `finished` which is set to `True` or `False` (in Python these are really just other names for `1` and `0`). This `finished` property gets checked on each pass through the loop. So the key piece of code to end a loop called `trials` is simply::

	trials.finished=True #or trials.finished=1 if you prefer
	
Of course you need to check the condition for that with some form of `if` statement. 

**Example 1**: You have a change-blindness study in which a pair of images flashes on and off, with intervening blanks, in a loop called `presentationLoop`. You record the key press of the subject with a :ref:`keyboard` called `resp1`. Using the 'ForceEndTrial' parameter of `resp1` you can end the current cycle of the loop but to end the loop itself you would need a :ref:`code`. Insert the following two lines in the `End Routine` parameter for the Code Component, which will test whether more than zero keys have been pressed::

	if resp1.keys is not None and len(resp1.keys)>0 :
    		trials.finished=1
		
or::	

	if resp1.keys :
		presentationLoop.finished=1
		

**Example 2**: Sometimes you may have more possible trials than you can actually display. By default, a loop will present all possible trials (nReps * length-of-list). If you only want to present the first 10 of all possible trials, you can use a code component to count how many have been shown, and then finish the loop after doing 10.

This example assumes that your loop is named 'trials'. You need to add two things, the first to initialize the count, and the second to update and check it.

`Begin Experiment`::

    myCount = 0

`Begin Routine`::

    myCount = myCount + 1
    if myCount > 10:
        trials.finished = True

.. note:: 
	
	In Python there is no `end` to finish an `if` statement. The content of the `if` or of a for-loop is determined by the indentation of the lines. In the above example only one line was indented so that one line will be executed if the statement evaluates to `True`.
