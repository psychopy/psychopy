.. _variablecomponent:

-------------------------------
Variable Component
-------------------------------

A variable holds a value which you can refer to by name later in the experiment.

Categories:
    Custom
Works in:
    PsychoPy


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _variablecomponent-name:
Name 
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces). The name of the Component will be the name of the variable!
    
.. _variablecomponent-startVal:
Start 
    The time or condition from when you want your variable to be defined. The default value is None, and so will be defined at the beginning of the experiment, trial or frame., see :ref:`startStop`.
    
.. _variablecomponent-startEstim:
Expected start (s) 
    If you are using frames to control timing of your stimuli, you can add an expected start time to display the component timeline in the routine.
    
.. _variablecomponent-startType:
Start type 
    How do you want to define your start point?
    
    Options:
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _variablecomponent-stopVal:
Stop 
    The duration for which the variable is defined/updated, see :ref:`startStop`.
    
.. _variablecomponent-durationEstim:
Expected duration (s) 
    If you are using frames to control timing of your stimuli, you can add an expected duration to display the component timeline in the routine.
    
.. _variablecomponent-stopType:
Stop type 
    How do you want to define your end point?
    
    Options:
    
    * duration (s)
    
    * duration (frames)
    
    * time (s)
    
    * frame N
    
    * condition
    
.. _variablecomponent-startExpValue:
Experiment start value 
    The start value. A variable can be set to any value.
    
.. _variablecomponent-startRoutineValue:
Routine start value 
    Set the value for the beginning of each Routine.
    
.. _variablecomponent-startFrameValue:
Frame start value 
    Set the value for the beginning of every screen refresh.
    
Data
===============================

What information about this Component should be saved?


.. _variablecomponent-saveStartExp:
Save exp start value 
    Save the experiment start value in data file.
    
.. _variablecomponent-saveStartRoutine:
Save Routine start value 
    Choose whether or not to save the experiment start value to your data file.
    
.. _variablecomponent-saveFrameValue:
Save frame value 
    Frame values are contained within a list for each trial, and discarded at the end of each trial.
    Choose whether or not to take the first, last or average variable values from the frame container, and save to your data file.
    
    Options:
    
    * first
    
    * last
    
    * all
    
    * never
    
.. _variablecomponent-saveEndRoutine:
Save Routine end value 
    Choose whether or not to save the routine end value to your data file.
    
.. _variablecomponent-saveEndExp:
Save exp end value 
    Choose whether or not to save the experiment end value to your data file.
    
.. _variablecomponent-saveStartStop:
Save onset/offset times 
    Store the onset/offset times in the data file (as well as in the log file).
    
.. _variablecomponent-syncScreenRefresh:
Sync timing with screen refresh 
    Synchronize times with screen refresh (good for visual stimuli and responses based on them)
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _variablecomponent-disabled:
Disable Component 
    Disable this Component
    