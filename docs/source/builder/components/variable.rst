.. _vairableComponent:

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

Start : int, float or bool
    The time or condition from when you want your variable to be defined. The default value is None, and so will be defined at the beginning of the experiment, trial or frame.
    See :ref:`startStop` for details.

Stop : int, float or bool
    The duration for which the variable is defined/updated. See :ref:`startStop` for details.

Experiment start value: any
    The variable can take any value at the beginning of the experiment, so long as you define you variables using literals or existing variables.

Routine start value : any
    The variable can take any value at the beginning of a routine/trial, and can remain a constant, or be defined/updated on every routine.

Frame start value : any
    The variable can take any value at the beginning of a frame, or during a condition bases on Start and/or Stop.

Save exp start value : bool
    Choose whether or not to save the experiment start value to your data file.

Save routine start value : bool
    Choose whether or not to save the routine start value to your data file.

Save frame value : bool and drop=down menu
    Frame values are contained within a list for each trial, and discarded at the end of each trial.
    Choose whether or not to take the first, last or average variable values from the frame container, and save to your data file.

Save routine start value : bool
    Choose whether or not to save the routine end value to your data file.

Save exp start value : bool
    Choose whether or not to save the experiment end value to your data file.
