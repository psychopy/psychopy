
.. PEP 2014 slides file, created by
   hieroglyph-quickstart on Tue Mar  4 20:42:06 2014.

.. _lexical_decision:

How to make a Lexical Decision Task in PsychoPy
=====================================

What is a Lexical Decision Task?
----------------------------------------------

In it's most basic form, a  `Lexical Decision Task <https://en.wikipedia.org/wiki/Lexical_decision_task#:~:text=The%20lexical%20decision%20task%20(LDT,stimuli%20as%20words%20or%20nonwords.>`_ is a simple experiment where participants decide if a word is a "real" word or not.

Setting up our experiment 
----------------------------------------------

As always, we ask ourselves, "what makes the main stimuli in my trial". All we really need is - a word, and a keyboard response (and maybe a fixation cross to start of the trial!). 


Setting up our conditions file
----------------------------------------------

The first thing we need is our list of words and non-words, we want an equal proportion of words and non-words, so we ensure that half of our rows contain words and half non-words. 

+--------------+-------------+-------------+
| thisWord     | thisCond    | corrAns     |
+==============+=============+=============+
| CAT          | word        | left        |
+--------------+-------------+-------------+
| BAR          | word        | left        |
+--------------+-------------+-------------+
| TEA          | word        | left        |
+--------------+-------------+-------------+
| GHS          | nonword     | right       |
+--------------+-------------+-------------+
| JUL          | nonword     | right       |
+--------------+-------------+-------------+
| POK          | nonword     | right       |
+--------------+-------------+-------------+


Feeding trial info into PsychoPy
----------------------------------------------

Once we have our conditions file set up and **saved in the same location as our experiment** we need to give this info to our experiment. Add a loop around your trial routine and give the path to your conditions file in the Conditions field. We want to use the information from our conditions file to set the presented word (in the Text field of our word write :code:`$thisWord`).

Collecting responses
----------------------------------------------

In this experiment we want the participant to make a response on every trial, so we will leave the duration field of our keyboard component blank and make sure to check the `Force end of Routine` box (indicating that this routine will end and move on when a key press is made. We only want to watch the 'left' and 'right' keys, so make sure to only list those in the Allowed keys field. Finally, under the data tab in our keyboard component we then need to select the `Store correct` option and feed in our column header to the `Correct answer` field :code:`$corrAns`

Including a random Inter-Stimulus-Interval (ISI)
------------------------------------------------

To add a random ISI to our trials, we can add a routine before our word presentation and add a simple text component. Type '+' in the text field. Now, in the *duration* field type :code:`$random()`. This will produce a random number between 0 and 1, so if we want a random ISI between 0.5 and 1 seconds we can simple add this to 0.5 i.e. :code:`0.5 +random()`. Your text component should look like this. 

.. image:: /_images/tutorials/LDT/ISI.png
   :width: 100 %


.. note::
	Because :code:`random()` is actually imported from numpy in this case we will need to add a code snippet to the start of our experiment for this to work online. Add a code component, change type to JS and type :code:`random = Math.random` in the Begin Experiment tab.

Exercise
----------------------------------------------

You can use :code:`random()` to set most parameters, although we don't need it for this task, try to make your word appear at a random position along the x axis from -0.5 to 0.5
