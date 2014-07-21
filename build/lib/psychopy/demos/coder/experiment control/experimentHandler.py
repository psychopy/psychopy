from psychopy import data, logging
from numpy import random
logging.console.setLevel(logging.DEBUG)

exp = data.ExperimentHandler(name='testExp',
                version='0.1',
                extraInfo={'participant':'jwp','ori':45},
                runtimeInfo=None,
                originPath=None,
                savePickle=True,
                saveWideText=True,
                dataFileName='testExp')

#a first loop (like training?)
conds = data.createFactorialTrialList({'faceExpression':['happy','sad'],'presTime':[0.2,0.3]})
training=data.TrialHandler(trialList=conds, nReps=3,name='train',
                 method='random',
                 seed=100)#this will set the global seed - so fixed for whole exp
exp.addLoop(training)
#run those trials
for trial in training:
    training.addData('training.rt',random.random()*0.5+0.5)
    if random.random()>0.5:
        training.addData('training.key','left')
    else:
        training.addData('training.key','right')
    exp.nextEntry()

#then run 3 repeats of a staircase
outerLoop=data.TrialHandler(trialList=[], nReps=3,name='stairBlock',
                 method='random')
exp.addLoop(outerLoop)
for thisRep in outerLoop:#the outer loop doesn't save any data
    staircase=data.StairHandler(startVal=10, name='staircase', nTrials=5)
    exp.addLoop(staircase)
    for thisTrial in staircase:
        id=random.random()
        if random.random()>0.5:
            staircase.addData(1)
        else:
            staircase.addData(0)
        exp.addData('id',id)
        exp.nextEntry()
#exp should then automatically save the pickle and csv data files when it gets deleted (end of script)
for e in exp.entries:
    print e
print 'done'
