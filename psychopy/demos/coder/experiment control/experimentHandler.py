"""
Shows how to use an ExperimentHandler object to manage running an experiment.

The contents of this file are in the public domain.
"""

from psychopy import data, logging
from psychopy.demos.utils import outputFolder
from numpy import random
logging.console.setLevel(logging.DEBUG)

# create an object which manages the whole experiment
exp = data.ExperimentHandler(
    name="testExp",
    version="0.1",
    extraInfo={
        'participant': "jwp", 
        'ori': 45
    },
    runtimeInfo=None,
    originPath=None,
    savePickle=True,
    saveWideText=True,
    dataFileName=outputFolder / "testExp"
)

# this is an easy way to make conditions with every combination of multiple factors
# if you prefer, you could also create a spreadsheet file and load it with data.importConditions
conds = data.createFactorialTrialList({
    'faceExpression': ['happy', 'sad'], 
    'presTime': [0.2, 0.3]
})

# create our first loop - a training step
training = data.TrialHandler(
    trialList=conds, 
    nReps=3, 
    name='train',
    method='random',
    # beware: this sets the global seed for all random functions
    seed=100
)
exp.addLoop(training)

# run those trials...
for trial in training:
    # let's add some data (and pretend it came from a participant...)
    training.addData('training.rt', random.random() * 0.5 + 0.5)
    if random.random() > 0.5:
        training.addData('training.key', 'left')
    else:
        training.addData('training.key', 'right')
    # this tells the ExperimentHandler to move on to the next row in your output data
    exp.nextEntry()

# this loop handles repeating the blocks inside it
outerLoop = data.TrialHandler(
    trialList=[], 
    nReps=3, 
    name='stairBlock',
    method='random'
)
exp.addLoop(outerLoop)
# run the outer loop...
for thisRep in outerLoop:
    # each repetition, create a staircase
    staircase = data.StairHandler(
        startVal=10, 
        name='staircase', 
        nTrials=5
    )
    exp.addLoop(staircase)
    # run the staircase...
    for thisTrial in staircase:
        # create a random id for this trial
        id = random.random()
        exp.addData('id', id)
        # more "participant data"
        if random.random() > 0.5:
            staircase.addData(1)
        else:
            staircase.addData(0)
        # next row
        exp.nextEntry()

# now that the experiment is finished, show the results
for e in exp.entries:
    print(e)
print("Done. 'exp' experimentHandler will now (end of script) save data to testExp.csv")
print(" and also to testExp.psydat, which is a pickled version of `exp`")
