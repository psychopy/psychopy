Builder concepts
--------------------

Routines and Flow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Builder view of the PsychoPy application is designed to allow the rapid development of a wide range of experiments for experimental psychology and cognitive neuroscience experiments.

The Builder view comprises two main panels for viewing the experiment's :doc:`routines` (upper left) and another for viewing the :doc:`flow` (lower part of the window). 

An experiment can have any number of routines, describing the timing of stimuli, instructions and responses. These are portrayed in a simple track-based view, similar to that of video-editing software, which allows stimuli to come on go off repeatedly and to overlap with each other.

The way in which these routines are combined and/or repeated is controlled by the flow panel. All experiments have exactly one flow. This takes the form of a standard flowchart allowing a sequence of routines to occur one after another, and for loops to be inserted around one or more of the routines. The loop also controls variables that change between repetitions, such as stimulus attributes.

Example 1 - a reaction time experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For a simple reaction time experiment there might be 3 routines, one that presents instructions and waits for a keypress, one that controls the trial timing, and one that thanks the participant at the end. These could then be combined in the flow so that the instructions come first, followed by trial, followed by the thanks routine, and a loop could be inserted so that the trial routine repeated 4 times for each of 6 stimulus intensities.

Example 2 - an fMRI block design
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Many fMRI experiments present a sequence of stimuli in a `block`. For this there are multiple ways to create the experiment. 
* We could create a single routine that contained a number of stimuli and presented them sequentially, followed by a long blank period to give the inter-epoch interval, and surround this single routine by a loop to control the blocks.
* Alternatively we could create a pair of routines to allow presentation of a) a single stimulus (for 1 sec) and b) a blank screen, for the prolonged period. With these routines we could insert  pair of loops, one to repeat the stimulus routine with different images, followed by the blank routine, and another to surround this whole set and control the blocks.
