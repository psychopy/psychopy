#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale()
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core
import os

# create a window before creating your rating scale, whatever units you like:
myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor')

# display instructions for using a rating scale, from the subject's point of view:
instr = visual.TextStim(myWin,text="""This is a demo of visual.RatingScale(). There are two examples.

Example 1 is as simple as possible, relying on the default configuration. You can use keys or the mouse to indicate a rating: just click on the line (on the next screen). You can then select and drag the marker, or use the left and right arrow keys. Or you can type a number 1 to 7 to indicate your choice. 

To accept your rating, either press 'enter' or click the button.

Press any key to start Example 1 (or escape to quit).""")
event.clearEvents()
instr.draw()
myWin.flip()
if 'escape' in event.waitKeys():
    core.quit()

# Example 1 --------(as simple as possible)--------
myRatingScale = visual.RatingScale(myWin) # create a RatingScale object
question = "How cool was that?"
myItem = visual.TextStim(myWin, text=question, height=.12, units='norm') # item to-be-rated

# anything with a frame-by-frame method for being drawn in a visual.Window() should work just fine, eg a movie:
#myItem = visual.MovieStim(myWin, 'jwpIntro.mov', pos=(0,120))

event.clearEvents()
while myRatingScale.noResponse: # show & update until a response has been made
    myItem.draw()
    myRatingScale.draw()
    myWin.flip()

rating = myRatingScale.getRating() # get the value indicated by the subject, 'None' if skipped (esc)
print 'Example 1: rating =', rating

# Example 2 --------(multiple items, multiple dimensions for each)--------
instr = visual.TextStim(myWin, text="""Example 2. This example uses non-default settings for the visual display, skipping a rating is not possible, and it uses a list of images to be rated. In addition, you will be asked to rate each image on two dimensions: valence and arousal.

Try this: Place a marker, then drag it along the line using the mouse. In this example, you cannot use 1 to 7 keys to respond because the scale is 0 to 10.

Press any key to start Example 2 (or escape to quit).""")
instr.draw()
myWin.flip()
if 'escape' in event.waitKeys():
    core.quit()

# create a scale for Example 2, using quite a few non-default options:
myRatingScale = visual.RatingScale(myWin, low=0, high=50, precision=10, 
        markerStyle='glow', markerExpansion=10, showValue=False, allowSkip=False, offsetVert=-0.6)

# using a list is handy if you have a lot of items to rate on the same scale, eg personality adjectives or images:
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']] # find all .png or .jpg images in the directory
imageList = imageList[:2] # ...but lets just use the first two

data = []
for image in imageList: 
    x,y = myRatingScale.win.size
    myItem = visual.SimpleImageStim(win=myWin, image=image, units='pix', pos=[0, y/7])
    
    # rate each image on two dimensions
    for dimension in ['0=very negative . . . 50=very positive', '0=very boring . . . 50=very energizing']:
        myRatingScale.scaleDescription.setText(dimension)
        myRatingScale.reset() # needed between repeated uses of the same rating scale
        event.clearEvents()
        while myRatingScale.noResponse:
            myItem.draw()
            myRatingScale.draw()
            myWin.flip()
        data.append([image, dimension, myRatingScale.getRating(), myRatingScale.getRT()]) # save for later
        
        # clear the screen & pause between ratings
        myWin.flip()
        core.wait(0.35) # brief pause, slightly smoother for the subject

print 'Example 2 (data from 2 images, each rated on 2 dimensions, reporting rating & RT):'
for d in data:
    print d
