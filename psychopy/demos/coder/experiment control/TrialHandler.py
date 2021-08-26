#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of TrialHandler

The contents of this file are in the public domain.

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
        stimList.append({'sf': sf, 'ori': ori})

# organize them with the trial handler
trials = data.TrialHandler(stimList, 10,
                           extraInfo={'participant': "Nobody", 'session':'001'})

# run the experiment
nDone = 0
for thisTrial in trials:  # handler can act like a for loop
    # simulate some data
    thisReactionTime = random() + float(thisTrial['sf']) / 2.0
    thisChoice = round(random())
    trials.data.add('RT', thisReactionTime)  # add the data to our set
    trials.data.add('choice', thisChoice)
    nDone += 1  # just for a quick reference

    msg = 'trial %i had position %s in the list (sf=%.1f)'
    print(msg % (nDone, trials.thisIndex, thisTrial['sf']))

# After the experiment, print a new line
print('\n')

# Write summary data to screen
trials.printAsText(stimOut=['sf', 'ori'],
                   dataOut=['RT_mean', 'RT_std', 'choice_raw'])

# Write summary data to a text file ...
trials.saveAsText(fileName='testData',
                  stimOut=['sf', 'ori'],
                  dataOut=['RT_mean', 'RT_std', 'choice_raw'])

# ... or an xlsx file (which supports sheets)
trials.saveAsExcel(fileName='testData',
                   sheetName='rawData',
                   stimOut=['sf', 'ori'],
                   dataOut=['RT_mean', 'RT_std', 'choice_raw'])

# Save a copy of the whole TrialHandler object, which can be reloaded later to
# re-create the experiment.
trials.saveAsPickle(fileName='testData')

# Wide format is useful for analysis with R or SPSS.
df = trials.saveAsWideText('testDataWide.txt')
