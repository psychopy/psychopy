.. _text:

Variable Component
-------------------------------

A variable can hold quantities or values in memory that can be referenced using a variable name.
You can store values in a variable to use in your experiments.

Parameters
~~~~~~~~~~~~

Name : string
    Everything in a PsychoPy experiment needs a unique name.
    The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    The variable name references the value stored in memory, so that your stored values can be used in your experiments.

Start : int or float
    The time you want your variable to be defined. The default value is None, and so will be defined at the beginning of the experiment, trial or frame.
    See :ref:`startStop` for details.

Stop : int or float
    The duration for which the variable is defined/updated. See :ref:`startStop` for details.

Initial value : any
    The variable can take any value at the beginning of the experiment, so long as you define you variables using literals or existing variables.

Routine start value : any
    The variable can take any value at the beginning of a routine/trial, and can remain a constant, or be defined/updated on every routine.

Frame start value : any
    The variable can take any value at the beginning of a frame, and can remain a constant, or be defined/updated on every routine/trial, or every frame.

Save variable : final, routine, frame, never
    There are several options for saving your variable. 'Final' provides the option to save the value stored in the variable at the end of each trial.
    'Routine' saves the variable at the end of each routine.
    'Frame' saves the variable at the end of each frame.