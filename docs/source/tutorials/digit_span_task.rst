
.. PEP 2014 slides file, created by
   hieroglyph-quickstart on Tue Mar  4 20:42:06 2014.

.. _digit_span:

How to make a Digit Span Task in PsychoPy
=====================================

What is a Digit Span Task?
----------------------------------------------

A digit span task is a basic test of working memory. Participants are presented a set of numbers and then asked to recall as many digits as they can. In this task we will use the `TextBox <https://www.psychopy.org/api/visual/textbox.html>`_ component to present text stimuli and to gather typed responses.

Setting up our experiment 
----------------------------------------------

As always, we ask ourselves, "what makes the main stimuli in my trial". For this experiment we will need a series of numbers that will be presented one after the other, followed by a text box where participants can type the numbers that they recall. 


Setting up our conditions file
----------------------------------------------

In this experiment, we are actually going to use code rather than a conditions file to generate the numbers to be presented on each trial, but we do need a conditions file to determine the length of each digit series to be presented. 

+--------------+
| seriesLen    |
+==============+
| 1            |
+--------------+
| 2            |
+--------------+
| 3            |
+--------------+
| 4            |
+--------------+
| 5            |
+--------------+
| 6            |
+--------------+

.. note::
	Technically we could also specify the possible length of each digit series in code too, e.g. by having a code component and using :code:`seriesLength = [1, 2, 3,4, 5] in our Begin Experiment tab, but this would then require us to index this list later on, so let's make use of a conditions file for ease. 

Feeding trial info into PsychoPy
----------------------------------------------

Once we have our conditions file set up and **saved in the same location as our experiment** we need to give this info to our experiment. This time, we are not going to use the variable in our conditions file as in a component parameter (e.g. :code:`$seriesLen`). Instead, we are going to use this parameter to set the number of times a number will be presented, we are going to use the variable :code:`seriesLen` in the :code:`nReps` field of a loop. 

First we need to add a routine that contains a simple text component, this will present our digit. The text field of that component type :code:`$randint()` and make sure to **set every repeat**. This will generate you a random integer value.

.. note::
	Because :code:`randint()` is actually imported from :code:`numpy.random`. This might not work online, instead what we could do is use :code:`int(random()*10)` which is easier to translate into Javascript. All we would need is to add a code component, change type to JS and type :code:`random = Math.random` in the Begin Experiment tab.

OK now we want to wrap **two** loops around this routine. The inner loop, we will name "stimuli" the outerloop we will name "trials", this is because our outer loop represents each trial and the inner loop represents the series of digits presented within a trial. 

We load our conditions spreadsheet into the Conditions field of our outerloop, in our inner loop we use the variable :code:`seriesLen` in the nReps field (note that we do not need to start this field with a "$" because the field already contains one in the name). 

Collecting responses
----------------------------------------------

In this experiment, we are going to allow participants to type responses. Add a routine called "recall" and inside this routine add a textBox component. Make sure to have the "Editable" field selected. This indicates that participants can edit the content of the textbox. Let's allow 5 seconds for recall by setting the duration of this component to 5 seconds.

Your entire experiment should now look like this:

.. image:: /_images/tutorials/digit_span/full_flow.png
   :width: 100 %


Exercise
----------------------------------------------

1. Add a routine to the start of your experiment and ask participants to type their name and occupation. 
2. Turn this digit span task into a letter span task using code. Hint: you can `generate a random letter in python <https://www.kite.com/python/answers/how-to-generate-a-random-letter-in-python>`_ or use a random integer to index a letter from a list e.g. :code:`myList[randint()]`
