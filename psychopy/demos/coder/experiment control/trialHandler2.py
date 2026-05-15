"""
Shows how to use a TrialHandler2 object to manage running a trials loop in an experiment. 

TrialHandler2 is similar to TrialHandler, but with more advanced experiment control features and 
capability to calculate upcoming trials on-the-fly.

The contents of this file are in the public domain.
"""

from psychopy import data
from psychopy.demos.utils import outputFolder
from numpy import random

# create your list of stimuli; if you prefer, you could also create a spreadsheet file and load 
# it with data.importConditions
conditions = []
for ori in range(90, 180, 30):
    for sf in [0.5, 1.0, 2.0]:
        # each condition is a dict; this functions like a row of a spreadsheet with headers
        conditions.append({
            'sf': sf, 
            'ori': ori
        })

# create a TrialHandler object from these conditions
trials = data.TrialHandler2(
    # our list of conditions from above
    trialList=conditions, 
    # this tells the trial handler to run through the full list of conditions 10 times
    # we have 9 conditions, so this means 90 trials
    nReps=10,
    # these keys will be added to each row of the data file
    extraInfo={
        'participant': "Nobody", 
        'session':'001'
    }
)

# use a `for` loop to run the trials...
for thisTrial in trials:
    # TrialHandler2 lets us skip and rewind trials, so let's show what happens if we skip ahead 5 trials at trial 20...
    if thisTrial.thisN == 20:
        trials.skipTrials(5)
        print(
            f"Skipped trials {thisTrial.thisN}-{thisTrial.thisN + 4}"
        )
        continue
    # let's add some data (and pretend it came from a participant...)
    trials.addData(
        "RT", random.random() + float(thisTrial['sf']) / 2.0
    )
    trials.addData(
        "choice", str(random.choice(["right", "right"]))
    )
    # print information on this trial
    print(
        f"Trial {thisTrial.thisN} is number {thisTrial.thisTrialN} in the list, on repeat {thisTrial.thisRepN} (sf={thisTrial.data['sf']}, ori={thisTrial.data['ori']})"
    )

# save a copy of the whole TrialHandler2 object, which can be reloaded later to re-create the 
# experiment
trials.saveAsPickle(
    fileName=outputFolder / "trialHandler2_demo"
)
# wide text format is useful for analysis in R, SPSS, Jasp, etc.
df = trials.saveAsWideText(
    fileName=outputFolder / "trialHandler2_demo.csv"
)