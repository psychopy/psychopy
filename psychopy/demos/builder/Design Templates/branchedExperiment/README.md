# Branching in a PsychoPy Builder experiment

There are two ways to stop a set of trials from running: 
- The method used here is to set the `finished` attribute of a particular loop to be True. This allows you to abort a set of trials even during a run (e.g. based on the outcome of the previous trials).
- The second, simpler, method is to set the nReps of a loop to be zero. This is handy while testing your experiment to run only a subset of the trials (e.g. to skip the practice trials).