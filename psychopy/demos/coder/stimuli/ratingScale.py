#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale()
author: Jeremy Gray, modified by Henrik Singmann
"""

from psychopy import visual, event, core, logging
import os

# create a window before creating your rating scale, whatever units you like:
myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor')

# instructions from the subject's point of view:
instr = visual.TextStim(myWin,text="""This is a demo of visual.RatingScale(). There are three examples.

Example 1 is close to the default configuration. You can use keys or the mouse to indicate a rating: just click on the line (on the next screen). You can then select and drag the marker, or use the left and right arrow keys.
To accept your rating, either press 'enter' or click the glowing button.

Press any key to start Example 1 (or escape to quit).""")
event.clearEvents()
instr.draw()
myWin.flip()
if 'escape' in event.waitKeys():
    core.quit()

# Example 1 --------(almost as simple as possible)--------
# create a default RatingScale object, plus choices[]:
#myRatingScale = visual.RatingScale(myWin) # = almost as simple as possible: defaults to 1-7 scale, not at all to extremely
myRatingScale = visual.RatingScale(myWin, choices=['cold', 'cool', 'tepid', 'warm', 'hot'])

# item to-be-rated:
question = "How cool was that?"
myItem = visual.TextStim(myWin, text=question, height=.12, units='norm')

# note that anything with a frame-by-frame method for being drawn in a visual.Window() should work:
#myItem = visual.MovieStim(myWin, 'jwpIntro.mov', pos=(0,120))

event.clearEvents()
while myRatingScale.noResponse: # show & update until a response has been made
    myItem.draw()
    myRatingScale.draw()
    myWin.flip()

rating = myRatingScale.getRating() # get the value indicated by the subject, 'None' if skipped 
print 'Example 1: rating =', rating

# Example 2 --------(multiple items, multiple dimensions for each)--------
instr = visual.TextStim(myWin, text="""Example 2. This example uses non-default settings for the visual display, skipping a rating is not possible, and it uses a list of images (two) to be rated on several dimensions (valence and arousal).

Try this: Place a marker, then drag it along the line using the mouse. In this example, you cannot use numeric keys to respond because the scale is 0 to 50.

Press any key to start Example 2 (or escape to quit).""")
instr.draw()
myWin.flip()
if 'escape' in event.waitKeys():
    core.quit()

# create a scale for Example 2, using quite a few non-default options:
myRatingScale = visual.RatingScale(myWin, low=0, high=50, precision=10, 
        markerStyle='glow', markerExpansion=10, showValue=False, allowSkip=False, pos=[0,-300], name='Example2')

# using a list is handy if you have a lot of items to rate on the same scale, eg personality adjectives or images:
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']] # find all .png or .jpg images in the directory
imageList = imageList[:2] # ...but lets just use the first two

data = []
for image in imageList: 
    x,y = myRatingScale.win.size
    myItem = visual.SimpleImageStim(win=myWin, image=image, units='pix', pos=[0, y//7])
    
    # rate each image on two dimensions
    for dimension in ['0=very negative . . . 50=very positive', '0=very boring . . . 50=very energizing']:
        myRatingScale.reset() # needed between repeated uses of the same rating scale
        myRatingScale.setDescription(dimension) # reset the instructions for this rating
        event.clearEvents()
        while myRatingScale.noResponse:
            myItem.draw()
            myRatingScale.draw()
            myWin.flip()
        data.append([image, myRatingScale.scaleDescription.text, myRatingScale.getRating(), myRatingScale.getRT()]) # save for later
        
        # clear the screen & pause between ratings
        myWin.flip()
        core.wait(0.35) # brief pause, slightly smoother for the subject

print 'Example 2 (data from 2 images, each rated on 2 dimensions, reporting rating & RT):'
for d in data:
    print '  ',d

# Example 3 --------(two simultaneous ratings)--------
instr = visual.TextStim(myWin, text="""Example 3. This example shows how one could obtain two ratings at the same time, e.g., to allow explicit comparison between images during ratings.

In such a situation, the subject will have to use the mouse (and not keyboard) to respond. The subject has to respond on both scales in order to go on to the next screen. Both of these considerations mean that its best to disallow the subject to skip a rating.

Press any key to start Example 3 (or escape to quit).""")
instr.draw()
myWin.flip()
if 'escape' in event.waitKeys():
    core.quit()

x,y = myRatingScale.win.size # for converting norm units to pix
leftward = -0.35 * x / 2 # use pix units, because the drawing window's units are pix
rightward = -1 * leftward
myRatingScaleLeft = visual.RatingScale(myWin, mouseOnly=True, pos=(leftward,-y/6),
    markerStyle='circle', displaySizeFactor=0.85,name='left')
myRatingScaleRight = visual.RatingScale(myWin, mouseOnly=True, pos=(rightward,-y/6),
    markerColor='DarkGreen', displaySizeFactor=0.85,name='right') # for logging, its useful to give names, esp when there are 2 on-screen

myItemLeft = visual.SimpleImageStim(win=myWin, image=imageList[0], pos=[leftward, y/6.])
myItemRight = visual.SimpleImageStim(win=myWin, image=imageList[1], pos=[rightward, y/6.])

event.clearEvents()
while myRatingScaleLeft.noResponse or myRatingScaleRight.noResponse:
    # you could hide the item if its been rated:
    #if myRatingScaleLeft.noResponse: myItemLeft.draw() 
    # or easier: just initialize it with the disappear=True option
    # but lets just draw it every frame:
    myItemLeft.draw()
    myItemRight.draw()
    myRatingScaleLeft.draw()
    myRatingScaleRight.draw()
    myWin.flip()

# just for fun: briefly show the two scales with the markers in the 'down' position
myItemLeft.draw()
myItemRight.draw()
myRatingScaleLeft.draw()
myRatingScaleRight.draw()
myWin.flip()
core.wait(1)

print 'Example 3:\n  rating left=', myRatingScaleLeft.getRating(), ' rt=%.3f' % myRatingScaleLeft.getRT()
print '  rating right=', myRatingScaleRight.getRating(), ' rt=%.3f' % myRatingScaleRight.getRT()


# Example 4 --------(using tickMarks argument)--------
instr = visual.TextStim(myWin,text="""Example 4. 

In this example we will use acustim tick marks and custom labels for a scale from 0 too 100.

Press any key to start Example 4 (or escape to quit).""")
event.clearEvents()
instr.draw()
myWin.flip()
if 'escape' in event.waitKeys():
    core.quit()


# create a default RatingScale object, plus choices[]:
#myRatingScale = visual.RatingScale(myWin) # = as simple as possible: defaults to 1-7 scale, not at all to extremely
myRatingScale = visual.RatingScale(myWin, low = 0, high = 100, tickMarks = [0, 25, 50, 80, 100], labels = ["0%", "1/4", "half/half", "kinda", "100%"])

# item to-be-rated:
question = "How probable is it that you will use this functionality in your next experiment?"
myItem = visual.TextStim(myWin, text=question, height=.08, units='norm')

# note that anything with a frame-by-frame method for being drawn in a visual.Window() should work:
#myItem = visual.MovieStim(myWin, 'jwpIntro.mov', pos=(0,120))

event.clearEvents()
while myRatingScale.noResponse: # show & update until a response has been made
    myItem.draw()
    myRatingScale.draw()
    myWin.flip()

rating = myRatingScale.getRating() # get the value indicated by the subject, 'None' if skipped 
print 'Example 4: rating =', rating

core.quit()