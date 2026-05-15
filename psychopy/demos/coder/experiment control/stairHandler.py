"""
Shows how to use a StairHandler object to manage running a staircase loop in an experiment. 

The contents of this file are in the public domain.
"""

from psychopy import data
from psychopy.demos.utils import outputFolder
from numpy import random

staircase = data.StairHandler(
    # value to start the staircase at
    startVal=10, 
    # the number of "incorrect" responses before the staircase increases
    nUp=1,
    # the number of "correct" responses before the staircase decreases
    nDown=1,
    # how to step up and down; "lin" (linear) for a simple addition/subtraction, "log" to 
    # increase/decrease in log units
    stepType="lin",
    # how much to increase/decrease by - as this is a list, it will start with the first value and move on each reversal
    stepSizes=[8, 4, 2, 1],
    # minimum number of trials; the staircase can't finish until at least this many trials have run
    nTrials=5,
    # the smallest and largest values allowed; it cannot increase/decrease beyond these
    minVal=0, 
    maxVal=90
)

# use a `for` loop to run the staircase...
for value in staircase:
    # define a correct answer - in your actual experiment, this is up to you
    corr = str(random.choice(["left", "right"]))
    staircase.addData("corr", corr)
    # pretent we got a response from the participant...
    resp = str(random.choice(["left", "right"]))
    staircase.addData("resp", resp)
    # store correct (1) or incorrect (0) for this trial
    staircase.addResponse(resp == corr)
    # print whether the participant was correct, and how this changed the value
    print(
        f"Correct: {resp == corr}, increment: {value}"
    )

# save a copy of the whole StairHandler object, which can be reloaded later to re-create the 
# experiment
df = staircase.saveAsPickle(
    fileName=str(outputFolder / "stairHandler_demo")
)
# save data as a CSV file
df = staircase.saveAsText(
    fileName=outputFolder / "stairHandler_demo.csv"
)

