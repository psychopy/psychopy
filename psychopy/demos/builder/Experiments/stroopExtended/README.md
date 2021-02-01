# Stroop Extended - a better implementation of the Stroop task

## The experiment:
The experiment is much like that in the Stroop demo (with some minor changes to the trial list file and to timing).
    
What differs is that there are now practice trials, with feedback provided. There is also a 'reverseStroop' version of the experiment, whereby subjects must report the colour spelled out by the word, instead of the letter colour used in the normal Stroop effect.

## Analysing your data:
Exactly as with the Stroop demo, except that, because there are two loops in the flow (for practice trials and main trials) there are now two worksheets in the Excel document.

## Notes: 
This version demonstrates more of the flexibility of PsychoPy. You can have multiple loops and they can span multiple Routines. A single Routine (e.g. trial) can be included in multiple places in the Flow, but beware that the trial list will need to have the same entries.

Also have a look at the `feedback` Routine. This is a little more involved than some other Routines because it does require a Code Component containing python scripting code. But the *good news* is that this Routine can be copied and pasted to other experiments (see the Experiment menu) and will work in most cases where the keyboard has been used with 'store correct answer' turned on.