"""measure your JND in orientation using a staircase method"""

from psychopy import core, visual, gui, data, misc, event
import time, numpy

try:#try to get a previous parameters file
    expInfo = misc.fromFile('lastParams.pickle')
except:#if not there then use a default set
    expInfo = {'observer':'jwp', 'refOrientation':0}
expInfo['dateStr']= time.strftime("%b_%d_%H%M", time.localtime())#add the current time
#present a dialogue to change params
dlg = gui.DlgFromDict(expInfo, title='simple JND Exp', fixed=['dateStr'])
if dlg.OK:
    misc.toFile('lastParams.pickle', expInfo)#save params to file for next time
else:
    core.quit()#the user hit cancel so exit

#make a text file to save data
fileName = expInfo['observer'] + dateStr
dataFile = open(fileName+'.csv', 'w')#a simple text file with 'comma-separated-values'
dataFile.write('targetSide,oriIncrement,correct\n')

#create the staircase handler
staircase = data.StairHandler(startVal = 20.0,
                          stepType = 'db', stepSizes=[8,4,4,2,2,1,1],
                          nUp=1, nDown=3,  #will home in on the 80% threshold
                          nTrials=50)
                          
#create window and stimuli
win = visual.Window([800,600],allowGUI=False, monitor='testMonitor', units='deg')
foil = visual.PatchStim(win, sf=1, size=4, mask='gauss', ori=expInfo['refOrientation'])
target = visual.PatchStim(win, sf=1,  size=4, mask='gauss', ori=expInfo['refOrientation'])
fixation = visual.PatchStim(win, rgb=-1, tex=None, mask='circle',size=0.2)
#and some handy clocks to keep track of time
globalClock = core.Clock()
trialClock = core.Clock()

#display instructions and wait
message1 = visual.TextStim(win, pos=[0,+3],text='Hit a key when ready.')
message2 = visual.TextStim(win, pos=[0,-3], 
    text="Then press left or right to identify the %.1fdeg probe." %expInfo['refOrientation'])
message1.draw()
message2.draw()
fixation.draw()
win.update()#to show our newly drawn 'stimuli'
#check for a keypress
event.waitKeys()

for thisIncrement in staircase: #will step through the staircase
    #set location of stimuli
    targetSide= round(numpy.random.random())*2-1 #will be either +1(right) or -1(left)
    foil.setPos([-5*targetSide, 0])
    target.setPos([5*targetSide, 0]) #in other location

    #set orientation of probe
    foil.setOri(expInfo['refOrientation'] + thisIncrement)

    #draw all stimuli
    foil.draw()
    target.draw()
    fixation.draw()
    win.update()

    core.wait(0.5)#wait 500ms (use a loop of x frames for more accurate timing)

    #blank screen
    fixation.draw()
    win.update()

    #get response
    thisResp=None
    while thisResp==None:
        allKeys=event.waitKeys()
        for thisKey in allKeys:
            if thisKey=='left':
                if targetSide==-1: thisResp = 1#correct
                else: thisResp = -1             #incorrect
            elif thisKey=='right':
                if targetSide== 1: thisResp = 1#correct
                else: thisResp = -1             #incorrect
            elif thisKey in ['q', 'escape']:
                core.quit()#abort experiment
        event.clearEvents() #must clear other (eg mouse) events - they clog the buffer

    #add the data to the staircase so it can calculate the next level
    staircase.addData(thisResp)
    dataFile.write('%i,%.3f,%i\n' %(targetSide, thisIncrement, thisResp))

#staircase has ended
dataFile.close()
staircase.saveAsPickle(fileName)#special python binary file to save all the info

#give some output to user
print 'reversals:'
print staircase.reversalIntensities
print 'mean of final 6 reversals = %.3f' %(numpy.average(staircase.reversalIntensities[-6:]))

win.close()
core.quit()
