from psychopy import visual, core, data, event
from numpy.random import shuffle
import copy, time #from the std python libs

#create some info to store with the data
info={}
info['startPoints']=[1.5,3,6]
info['nTrials']=10
info['observer']='jwp'

win=visual.Window([400,400])
#---------------------
#create the stimuli
#---------------------

#create staircases
stairs=[]
for thisStart in info['startPoints']:
    #we need a COPY of the info for each staircase 
    #(or the changes here will be made to all the other staircases)
    thisInfo = copy.copy(info)
    #now add any specific info for this staircase
    thisInfo['thisStart']=thisStart #we might want to keep track of this
    thisStair = data.StairHandler(startVal=thisStart, 
        extraInfo=thisInfo,
        nTrials=50, nUp=1, nDown=3,
        minVal = 0.5, maxVal=8, 
        stepSizes=[4,4,2,2,1,1])
    stairs.append(thisStair)
    
for trialN in range(info['nTrials']):
    shuffle(stairs) #this shuffles 'in place' (ie stairs itself is changed, nothing returned)
    #then loop through our randomised order of staircases for this repeat
    for thisStair in stairs:
        thisIntensity = next(thisStair)
        print('start=%.2f, current=%.4f' %(thisStair.extraInfo['thisStart'], thisIntensity))
        
        #---------------------
        #run your trial and get an input
        #---------------------
        keys = event.waitKeys() #(we can simulate by pushing left for 'correct')
        if 'left' in keys: wasCorrect=True
        else: wasCorrect = False
        
        thisStair.addData(wasCorrect) #so that the staircase adjusts itself
        
    #this trial (of all staircases) has finished
#all trials finished
        
#save data (separate pickle and txt files for each staircase)
dateStr = time.strftime("%b_%d_%H%M", time.localtime())#add the current time
for thisStair in stairs:
    #create a filename based on the subject and start value
    filename = "%s start%.2f %s" %(thisStair.extraInfo['observer'], thisStair.extraInfo['thisStart'], dateStr)
    thisStair.saveAsPickle(filename)
    thisStair.saveAsText(filename)   
