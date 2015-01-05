#!/usr/bin/env python2
from random import random
from psychopy import data

#create your list of stimuli
#NB as of version 1.62 you could simply import an excel spreadsheet with this
#using data.importTrialTypes('someFile.xlsx')
stimList = []
for ori in range(90,180,30):
    for sf in [0.5, 1.0, 2.0]:
        stimList.append( 
            {'sf':sf, 'ori':ori} #this is a python 'dictionary'
            )

#organise them with the trial handler
trials = data.TrialHandler(stimList,10,extraInfo= {'participant':"Nobody",'session':1})
trials.data.addDataType('choice')#this will help store things with the stimuli
trials.data.addDataType('RT')#add as many types as you like

#run the experiment
nDone=0
for thisTrial in trials: #handler can act like a for loop
    #simulate some data
    thisReactionTime = random()+float(thisTrial['sf'])/2.0
    thisChoice = round(random())
    trials.data.add('RT', thisReactionTime) #add the data to our set
    trials.data.add('choice', thisChoice) 
    nDone += 1  #just for a quick reference
    
    print 'trial %i had position %s in the list (sf=%.1f)' \
          %(nDone, trials.thisIndex, thisTrial['sf'])
    
#after the experiment
print '\n'
trials.printAsText(stimOut=['sf','ori'], #write summary data to screen 
                  dataOut=['RT_mean','RT_std', 'choice_raw'])
trials.saveAsText(fileName='testData', # also write summary data to a text file
                  stimOut=['sf','ori'], 
                  dataOut=['RT_mean','RT_std', 'choice_raw'])
trials.saveAsExcel(fileName='testData', # ...or an xlsx file (which supports sheets)
                  sheetName = 'rawData',
                  stimOut=['sf','ori'], 
                  dataOut=['RT_mean','RT_std', 'choice_raw'])
trials.saveAsPickle(fileName = 'testData')#this saves a copy of the whole object 
df = trials.saveAsWideText("testDataWide.txt") #wide is useful for analysis with R or SPSS. Also returns dataframe df

    

