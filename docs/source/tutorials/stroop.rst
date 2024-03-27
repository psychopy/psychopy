
.. PEP 2014 slides file, created by
   hieroglyph-quickstart on Tue Mar  4 20:42:06 2014.

.. _stroop:

How to make a Stroop task in PsychoPy
=====================================

A great starter experiment
----------------------------------------------

The Stroop task is a great starting point for learning to use PsychoPy, it is why we use it in `the textbook <https://us.sagepub.com/en-us/nam/building-experiments-in-psychopy/book253480>`_! So let's talk through the basics of making a Stroop in PsychoPy.

Setting up our experiment 
----------------------------------------------

OK step 1 of any experiment is to consider "what makes the main stimuli in my trial". In the Stroop task, this is simple - a word, and a keyboard response (and maybe a fixation cross to start of the trial!). 

.. image:: /_images/tutorials/stroop/basic_flow.png
   :width: 100 %


Setting up our conditions file
----------------------------------------------

The next thing to do is to think about what information changes trial-by-trial. In a Stroop task the written word can either represent the same color, or a different color to the ink it is written in. Here we have made 2 basic "congruent" and 2 "incongruent" trials. We have also added a column to code the correct answer, in this case we want participants to press the left key if the word says red, and press the right key if the word says blue. 

+--------------+-------------+-------------+-------------+
| thisWord     | thisColor   | condition   | corrAns     |
+==============+=============+=============+=============+
| red          | red         | congruent   |    left     |
+--------------+-------------+-------------+-------------+
| blue         | blue        | congruent   |    right    |
+--------------+-------------+-------------+-------------+
| red          | blue        | incongruent |    left     |
+--------------+-------------+-------------+-------------+
| blue         | red         | incongruent |    right    |
+--------------+-------------+-------------+-------------+

.. note::
    We aren't going to use the column with the header "conditions" in our experiment. But this info will be saved to our data file, so in general it is good to be kind to future us, and think about what data you might want later when it comes to analysis. 

Feeding trial info into PsychoPy
----------------------------------------------

Once we have our conditions file set up and **saved in the same location as our experiment** we need to give this info to our experiment. Add a loop around your trial routine and give the path to your conditions file in the Conditions field. We want to use the information from our conditions file to set a) the presented word (in the Text field of our word write :code:`$thisWord`) and b) the color of that word (in the Appearance tab of our word component write :code:`$thisColor` in the Foreground Color field) - in both of these fields make sure to **set every repeat** this is because these are parameters that are going to change on each iteration of our trials loop. 

Collecting responses
----------------------------------------------

In this experiment we want the participant to make a response on every trial, so we will leave the duration field of our keyboard component blank and make sure to check the `Force end of Routine` box (indicating that this routine will end and move on when a key press is made. We only want to watch the 'left' and 'right' keys, so make sure to only list those in the Allowed keys field. Finally, under the data tab in our keyboard component we then need to select the `Store correct` option and feed in our column header to the `Correct answer` field :code:`$corrAns`

And there you have it! a very simple stroop task!


Exercise (15 mins)
----------------------------------------------

1. Add some instructions and a thanks message. 
2. Add more colors combinations to the task
3. add a neutral condition. 
4. Add a routine for participants to practice *Hint: you can use the same routine several times in an experiment, which can really save work in the long run!*

Youtube tutorial
----------------
`Building a Stroop Task <https://www.youtube.com/watch?v=VV6qhuQgsiI>`_

