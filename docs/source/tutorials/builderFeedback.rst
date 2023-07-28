.. _feedback:

Builder - providing feedback
================================

If you're using the Builder then the way to provide feedback is with a :ref:`code` to generate an appropriate message (and then a :ref:`text` to present that message). PsychoPy will be keeping track of various aspects of the stimuli and responses for you throughout the experiment and the key is knowing where to find those.

The following examples assume you have a :ref:`Loop <loops>` called `trials`, containing a :ref:`Routine <routines>` with a :ref:`keyboard` called `key_resp`. Obviously these need to be adapted in the code below to fit your experiment.

.. note::

    The following generate strings use python 'formatted strings'. These are very powerful and flexible but a little strange when you aren't used to them (they contain odd characters like %.2f). See :ref:`formattedStrings` for more info.

Feedback after a trial
-----------------------

This is actually demonstrated in the demo, `ExtendedStroop` (in the Builder>demos menu, unpack the demos and then look in the menu again. tada!)

If you have a Keyboard Component called `key_resp` then, after every trial you will have the following variables::

    key_resp.keys # A python list of keys pressed
    key_resp.rt # The time to the first key press
    key_resp.corr # None, 0 or 1, if you are using 'store correct'

To create your `msg`, insert the following into the 'start experiment` section of the :ref:`code`::

    msg='doh!'# If this comes up we forgot to update the msg!
    
and then insert the following into the `Begin Routine` section (this will get run every repeat of the routine)::
    
    if not key_resp.keys :
        msg = "Failed to respond"
    elif key_resp.corr: # Stored on last run routine
        msg = "Correct! RT=%.3f" %(key_resp.rt)
    else:
        msg="Oops! That was wrong"
  
Feedback after a block
---------------------------

In this case the feedback routine would need to come after the loop (the block of trials) and the message needs to use the stored data from the loop rather than the `key_resp` directly. Accessing the data from a loop is not well documented but totally possible.

In this case, to get all the keys pressed in a `numpy <http://www.numpy.org>`_ array::

    trials.data['key_resp.keys'] # numpy array with size=[ntrials,ntypes]

If you used the 'Store Correct' feature of the Keyboard Component (and told psychopy what the correct answer was) you will also have a variable::

    # numpy array storing whether each response was correct (1) or not (0)
    trials.data['key_resp.corr'] 
    
So, to create your `msg`, insert the following into the 'start experiment` section of the :ref:`code`::

    msg='doh!'# If this comes up we forgot to update the msg!
    
and then insert the following into the `Begin Routine` section (this will get run every repeat of the routine)::

    nCorr = trials.data['key_resp.corr'].sum() # .std(), .mean() also available
    meanRt = trials.data['key_resp.rt'].mean()
    msg = "You got %i trials correct (rt=%.2f)" %(nCorr,meanRt)

Draw your message to the screen
-------------------------------------

Using one of the above methods to generate your `msg` in a :ref:`code`, you then need to present it to the participant by adding a :ref:`text` to your `feedback` Routine and setting its text to `$msg`.

.. warning::

    The Text Component needs to be below the Code Component in the Routine (because it needs to be updated after the code has been run) and it needs to `set every repeat`.

Youtube tutorial
----------------
- `Trial by trial accuracy feedback <https://www.youtube.com/watch?v=o6gG1LRngmU>`_
- `Trial by trial reaction time feedback  <https://www.youtube.com/watch?v=bfbtqGCKf-A>`_
- `Feedback for typed responses  <https://www.youtube.com/watch?v=-Fto45M7bS0>`_