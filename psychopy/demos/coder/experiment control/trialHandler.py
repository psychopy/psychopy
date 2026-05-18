"""
Shows how to use a TrialHandler object to manage running a trials loop in an experiment.

The contents of this file are in the public domain.
"""


from psychopy import data, logging
from numpy import random

# set logging level to "EXP" so we can see updates as each trial rolls past
logging.console.setLevel(logging.EXP)

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
trials = data.TrialHandler(
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
    # let's add some data (and pretend it came from a participant...)
    trials.data.add(
        "RT", random.random() + float(thisTrial['sf']) / 2.0
    )
    trials.data.add(
        "choice", str(random.choice(["right", "right"]))
    )
    # flush the log so we can see the trial
    logging.flush()

# save data to a CSV file
trials.saveAsText(
    fileName="TrialHandler_demo.csv",
    stimOut=["sf", "ori"],
    dataOut=["RT_mean", "RT_std", "choice_raw"]
)
# save data to an Excel file
trials.saveAsExcel(
    fileName="TrialHandler_demo.xlsx",
    sheetName="rawData",
    stimOut=["sf", "ori"],
    dataOut=["RT_mean", "RT_std", "choice_raw"]
)
# save a copy of the whole TrialHandler object, which can be reloaded later to re-create the 
# experiment
trials.saveAsPickle(
    fileName="trialHandler_demo"
)
# wide text format is useful for analysis in R, SPSS, Jasp, etc.
df = trials.saveAsWideText(
    fileName="trialHandler_demo.csv"
)
