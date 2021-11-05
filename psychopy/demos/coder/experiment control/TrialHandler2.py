#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of TrialHandler
"""

from random import random
from psychopy import data

# create your list of stimuli
# NB as of version 1.62 you could simply import an excel spreadsheet with this
# using data.importConditions('someFile.xlsx')
stimList = []
for ori in range(90, 180, 30):
    for sf in [0.5, 1.0, 2.0]:
        # append a python 'dictionary' to the list
        stimList.append({'sf':sf, 'ori':ori})

# organize them with the trial handler
trials = data.TrialHandler2(stimList, 10,
                            extraInfo= {'participant':"Nobody", 'session':'001'})

# run the experiment
nDone = 0
for thisTrial in trials:  # handler can act like a for loop
    # simulate some data
    thisReactionTime = random() + float(thisTrial['sf']) / 2.0
    thisChoice = round(random())
    trials.addData('RT', thisReactionTime)  # add the data to our set
    trials.addData('choice', thisChoice)
    nDone += 1  # just for a quick reference

    msg = 'trial %i had position %s in the list (sf=%.1f)'
    print(msg % (nDone, trials.thisIndex, thisTrial['sf']))

# after the experiment
print('\n')
trials.saveAsPickle(fileName = 'testData')  # this saves a copy of the whole object
df = trials.saveAsWideText("testDataWide.csv")  # wide is useful for analysis with R or SPSS. Also returns dataframe df

# The contents of this file are in the public domain.
