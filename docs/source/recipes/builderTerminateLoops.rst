.. _feedback:

Builder - terminating a loop
=========================================

People often want to terminate their :ref:`loops` before they reach the designated number of trials based on subjects' responses. For example, you might want to use a Loop to repeat a sequence of images that you want to continue until a key is pressed, or use it to continue a training period, until a criterion performance is reached.

To do this you need a :ref:`code` inserted into your :ref:`routine`. All loops have an attribute called `finished` which is set to `True` or `False` (these in Python are really just other names for `1` and `0`). This `finished` property gets checked on each pass through the loop. So the key piece of code to end a loop called `trials` is simply::

	trials.finished=True #or trials.finished=1 if you prefer
	
Of course you need to check the condition for that with some form of `if` statement. 

Example 1: You have a change-blindness study in which a pair of images flashes on and off, with intervening blanks, in a loop called `presentationLoop`. You record the key press of the subject with a :ref:`keyboard` called `resp1`. Using the 'ForceEndTrial' parameter of `resp1` you can end the current cycle of the loop but to end the loop itself you would need a :ref:`code`. Insert the following two lines in the `End Routine` parameter for the Code Component, which will test whether more than zero keys have been pressed::

	if len(resp1.keys)>0:
		presentationLoop.finished=1

.. note:: 
	
	In Python there is no `end` to finish an `if` statement. The content of the `if` or of a for-loop is determined by the indentation of the lines. In the above example only onel line was indented so that one line will be executed if the statement evaluates to `True`.
