.. _staircases:

Using a Staircase
=================================================
Using a staircase procedure to control your loop allows the implementation of adaptive methods. That is, aspects of a trial can depend on (or “adapt to”) how a subject has responded earlier in the study. This could be, for example, simple up-down staircases where an intensity value is varied trial-by-trial according to certain parameters, or a stop-signal paradigm to assess impulsivity. 

To use a staircase, you'll need to set a 'correct' and an 'incorrect' response to the stimuli in your experiment. This is because the estimate produced by staircases is dependent on your participant's responses; the value will decrease when a participant is 'correct' and increase when the participant is 'incorrect'.

There are currently three types of staircase in PsychoPy:

* Simple
* QUEST
* QUEST Plus

You can add just one of these staircases, or you can choose to interleave two or more. 

Only QUEST is currently supported for online use.

.. _simple_staircase:

Using a simple staircase 
-------------------------------------------------------------
A simple staircase allows you to input the step sizes that you want the staircase to take when a user gets an answer correct or incorrect. 

** To add one simple staircase**

* To add just one simple staircase, you'll firstly need to add a loop around the routines you want to repeat. Then, from the loop type drop-down list select "staircase":

.. figure:: /images/simplestair_loop.png

* You'll now see a list of parameters:

    * nReps: The minimum number of trials in the staircase. If the staircase has not reached the required number of reversals then it will continue.
    * start value: The initial value for the staircase.
    * max value: The largest legal value for the staircase, which can be used to prevent it reaching impossible contrast values, for instance.
    * min value: The smallest legal value for the staircase.
    * step sizes: The size of steps as a single value or a list. For a single value the step size is fixed. For a list the step size will progress to the next value at each reversal.
    * step type: The type of steps that should be taken each time:
            * 'lin' - This will simply add or subtract that amount at each step. 
            * 'log' - This will add or subtract a certain number of log units at each step (note that this will prevent your value ever reaching zero or less).
            * 'db' - This will add or subtract a certain number of decibels at each step (note that this will prevent your value ever reaching zero or less).
    * N up: The number of 'incorrect' (or 0) responses before the staircase level increases.
    * N down: The number of 'correct' (or 1) responses before the staircase level decreases.
    * nReversals: The minimum number of reversals (i.e., times that the staircase changes direction when an answer is correct/incorrect) that must occur before the staircase ends.

* Complete these fields as required for your experiment and click OK to save the loop.
* Now that you have your conditions set up, you will need to *use* the estimates that are being produced by the staircase to control the particular aspect of the stimulus that you're investigating (contrast, or opacity for example). To do this, simply use the variable `$level` as the value for that parameter and set every repeat!

** To add more than one simple staircase**

* To add more than one staircase, add a loop in the same way as above but select "Interleaved staircases" from the loop type drop-down list, then "simple" from the stair type drop-down:

.. figure:: /images/interleaved_simple.png


* Set nReps to the minimum number of trials to run.
* Next, use the switch method drop-down list to select whether you want to switch between your staircases sequentially or randomly. Let's imagine that you have four staircases that you want to interleave. Choosing sequential would mean that on the first trial staircase one is used, on the next trial staircase two is used, then staircase three followed by staircase four. Then we go back to staircase one on the fifth trial. Choosing random would randomly choose from one of the four staircases to use on each trial. 

* Now, you'll need to create a conditions file that contains the following column headers:

    * label: So that you can distinguish between the different staircases in your data output, add a `label` column containing a name for each of your staircases.
    * nReps: The minimum number of trials in the staircase. If the staircase has not reached the required number of reversals then it will continue.
    * startVal: The initial value for the staircase.
    * maxVal: The largest legal value for the staircase, which can be used to prevent it reaching impossible contrast values, for instance.
    * minVal: The smallest legal value for the staircase.
    * stepSizes: The size of steps as a single value or a list. For a single value the step size is fixed. For a list the step size will progress to the next value at each reversal.
    * stepType: The type of steps that should be taken each time:
            * 'lin' - This will simply add or subtract that amount at each step. 
            * 'log' - This will add or subtract a certain number of log units at each step (note that this will prevent your value ever reaching zero or less).
            * 'db' - This will add or subtract a certain number of decibels at each step (note that this will prevent your value ever reaching zero or less).
    * nUp: The number of 'incorrect' (or 0) responses before the staircase level increases.
    * nDown: The number of 'correct' (or 1) responses before the staircase level decreases.
    * nReversals: The minimum number of reversals (i.e., times that the staircase changes direction when an answer is correct/incorrect) that must occur before the staircase ends.

 * You'll then need to input values for each of your staircases. For example:

.. figure:: /images/simplestair_conds.png

    This example has two staircases, one that will start with a high spatial frequency and one that will start with a low spatial frequency.

* Use the variable `$level` in exactly the same way as you would with one staircase - this will update on every repeat automatically.



.. _quest_staircase:

Using a QUEST staircase 
-------------------------------------------------------------
Rather than setting the step sizes manually, as with a simple staircase, the QUEST staircase procedure produces estimates that are based on the stimuli and the observer’s responses in the preceding trials. Watson and Pelli (1983) reported QUEST which uses a Bayesian method to estimate the position of the psychometric function. For full information please see `their paper <https://link.springer.com/content/pdf/10.3758/BF03202828.pdf>`_ in the first instance. 


* To add a QUEST staircase, you'll firstly need to add a loop around the routines you want to repeat. Then, from the loop type drop-down list select "Interleaved staircases" and "QUEST" from the stair type drop-down:

.. figure:: /images/quest_loop.png

* Set nReps to the minimum number of trials to run.
* If you're using more than one staircase, use the switch method drop-down list to select whether you want to switch between your staircases sequentially or randomly. If you're only using one staircase you can just leave this set to the default value. 
* Now, you'll need to create a conditions file that contains the following column headers/variables:

    * label: The label given to the staircase.
    * startVal: The initial value for the staircase.
    * startValSd: Standard deviation of your starting guess threshold. Be generous with the SD as QUEST will have trouble finding the true threshold if it’s more than one SD from your initial guess.
    * pThreshold: Your threshold criterion expressed as probability of response==1. Typical values for pThreshold are: 0.82 which is equivalent to a 3 up 1 down standard staircase; 0.63 which is equivalent to a 1 up 1 down standard staircase; 0.5 in a yes-no task and 0.75 in a 2-AFC task
    * method: The method used to determine the next threshold estimate to test. Choose from 'mean', 'mode' or 'quantile'. The default value is quantile.
    * beta: This controls the steepness of the psychometric function (or slope).
    * delta: This is the lapse rate - the fraction of trials that the participant lapses attention and guesses blindly. The default value is 0.01.
    * gamma: The value that is scored while the participant is guessing. Watson and Pelli (1983) state that "The parameter gamma specifies the probability of a success at zero intensity: for two-alternative forced choice it is 0.5, for n-alternative forced choice it is n to the -1 ; for yes-no, it is the false alarm rate."
    * grain: Grain: This is the quantization (step size) of the internal table, e.g., 0.01.
    * minVal **Use this along with maxVal when running the staircase locally (i.e., not online)**: The minimum value that the staircase will return (good for preventing impossible contrast values, for instance). 
    * maxVal **Use this along with minVal when running the staircase locally (i.e., not online)**: The maximum value that the staircase will return (good for preventing impossible contrast values, for instance).
    * range **Use this when running the staircase online)**: This is the intensity difference between the largest and smallest value, centered on startVal. Be generous with the range so that you don't exclude possible values for the threshold estimate.

* Complete these fields as required for your experiment and click OK to save the loop.
* Add as many staircases as you need to the conditions file.
* Now that you have your conditions set up, you will need to *use* the estimates that are being produced by the staircase to control the particular aspect of the stimulus that you're investigating (contrast, or opacity for example). To do this, simply use the variable `$level` as the value for that parameter and set every repeat!


.. _questPlus_staircase:

Using a QUEST Plus staircase 
-------------------------------------------------------------
QUEST Plus is an extension of the original QUEST procedure set out by Watson and Pelli (1983), by Watson (2017). Read the paper `here <https://jov.arvojournals.org/article.aspx?articleid=2611972>`_ for a complete explanation of the QUEST Plus procedure.


* To add a QUEST Plus staircase, you'll firstly need to add a loop around the routines you want to repeat. Then, from the loop type drop-down list select "Interleaved staircases" and "QUEST Plus" from the stair type drop-down:

.. figure:: /images/questplus_loop.png

* Now, you'll need to create a conditions file that contains the following column headers/variables:

    * label: The label given to the staircase.
    * nTrials: The number of trials to run.
    * intensityVals: The complete set of stimulus levels. These do not have to just be intensity, they can be contrasts, durations or weights etc.
    * thresholdVals: The complete set of possible threshold values.
    * slopeVals: The complete set of possible slope values.
    * lowerAsymptoteVals: The complete set of possible values of the lower asymptote. This corresponds to false-alarm rates in yes-no tasks, and to the guessing rate in n-AFC tasks. Therefore, when performing an n-AFC experiment, the collection should consist of a single value only (e.g., `[0.5]` for 2-AFC, `[0.33]` for 3-AFC, `[0.25]` for 4-AFC, etc.).
    * lapseRateVals: The complete set of possible lapse rate values. The lapse rate defines the upper asymptote of the psychometric function, which will be at `1 - lapse rate`.
    * responseVals: The complete set of possible response outcomes. Currently, only two outcomes are supported: the first element must correspond to a successful response/stimulus detection, and the second one to an unsuccessful or incorrect response. For example, in a yes-no task, you would use `['Yes', 'No']`, and in an n-AFC task,`['Correct', 'Incorrect']`; or, alternatively, you could use `[1, 0]` in both cases.
    * prior: The prior probabilities to assign to the parameter values.
    * startIntensity: The very first intensity (or stimulus level) to present.
    * stimScale: The scale on which the stimulus intensities (or stimulus levels) are provided. Currently supported are the log scale, `log10`; decibels, `dB`; and a linear scale, `linear`.
    * stimSelectionMethod: How to select the next stimulus. `minEntropy` will select the stimulus that will minimize the expected entropy. `minNEntropy` will randomly pick pick a stimulus from the set of stimuli that will produce the smallest, 2nd-smallest, ..., N-smallest entropy. This can be used to ensure some variation in the stimulus selection (and subsequent presentation) procedure. The number `N` will then have to be specified via the `stimSelectionOption` parameter.
    * stimSelectionOptions: This parameter further controls how to select the next stimulus in case `stimSelectionMethod=minNEntropy`. The dictionary supports two keys:`N` and `maxConsecutiveReps`. `N` defines the number of "best" stimuli (i.e., those which produce the smallest `N` expected entropies) from which to randomly select a stimulus for presentation in the next trial. `maxConsecutiveReps` defines how many times the exact same stimulus can be presented on consecutive trials. For example, to randomly pick a stimulus from those which will produce the 4 smallest expected entropies, and to allow the same stimulus to be presented on two consecutive trials max, use `stimSelectionOptions=dict(N=4, maxConsecutiveReps=2)`. To achieve reproducible results, you may pass a seed to the random number generator via the `randomSeed` key.
    * paramEstimationMethod: How to calculate the final parameter estimate. `mean` returns the mean of each parameter, weighted by their respective posterior probabilities. `mode` returns the the parameters at the peak of the posterior distribution.

* Complete these fields as required for your experiment and click OK to save the loop.
* Add as many staircases as you need to the conditions file.
* Now that you have your conditions set up, you will need to *use* the estimates that are being produced by the staircase to control the particular aspect of the stimulus that you're investigating (contrast, or opacity for example). To do this, simply use the variable `$level` as the value for that parameter and set every repeat!

If there is a problem - We want to know!
-------------------------------------------------------------
If you have followed the steps above and are having an issue, please post details of this on the `PsychoPy Forum <https://discourse.psychopy.org/>`_.

We are constantly looking to update our documentation so that it's easy for you to use PsychoPy in the way that you want to. Posting in our forum allows us to see what issues users are having, offer solutions, and to update our documentation to hopefully prevent those issues from occurring again!