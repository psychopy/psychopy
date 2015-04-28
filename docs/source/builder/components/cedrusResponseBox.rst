.. _cedrusButtonBox:

Cedrus Button Box Component
---------------------------------

This component allows you to connect to a Cedrus Button Box to collect key presses.

*Note that there is a limitation currently that a button box can only be used in a single Routine. Otherwise PsychoPy tries to initialise it twice which raises an error.* As a workaround, you need to insert the start-routine and each-frame code from the button box into a code component for a second routine.

Properties
~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the button box is first read. See :ref:`startStop` for details.

Stop :
    Governs the duration for which the button box is first read. See :ref:`startStop` for details.

Force end of Routine : true/false
    If this is checked, the first response will end the routine.

Allowed keys : None, or an integer, list, or tuple of integers 0-7
    This field lets you specify which buttons (None, or some or all of 0 through 7) to listen to.

Store : (choice of: first, last, all, nothing)
    Which button events to save in the data file. Events and the response times are saved, with RT being recorded by the button box (not by PsychoPy).

Store correct : true/false
    If selected, a correctness value will be saved in the data file, based on a match with the given correct answer.

Correct answer: button
    The correct answer, used by Store correct.

Discard previous : true/false
    If selected, any previous responses will be ignored (typically this is what you want).

Advanced
+++++++++++++

Device number: integer
    This is only needed if you have multiple Cedrus devices connected and you need to specify which to use.

Use box timer : true/false
    Set this to True to use the button box timer for timing information (may give better time resolution)

.. seealso::

	API reference for :class:`~psychopy.hardware.iolab`
