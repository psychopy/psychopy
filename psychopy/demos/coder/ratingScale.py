#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale().
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core
import random, os, Image # used in the example, not necessary for a rating scale

# create a window before creating your rating scale, norm or pix is fine:
myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor')

# instructions for using a rating scale, from the subject's point of view:
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
myRatingScale = visual.RatingScale(myWin) # create a default RatingScale object
question = "How cool was that?"
myItem = visual.TextStim(myWin, text=question, height=.12, units='norm') # item to-be-rated
# anything with a frame-by-frame method for display should work just fine, eg a movie:
#myItem = visual.MovieStim(myWin, 'jwpIntro.mov', size=[320,240], flipVert=False, flipHoriz=False, pos=(0,120))

event.clearEvents()
while myRatingScale.noResponse: # show & update until a response has been made
    myItem.draw()
    myRatingScale.draw()
    myWin.flip()

rating = myRatingScale.getRating() # get the value indicated
print 'Example 1: rating =', rating

# Example 2 --------(complex)--------
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

# it can be useful to obtain ratings on several dimensions for each item, here two dimensions:
dimensions = ['0=very negative . . . 50=very positive', 
                        '0=very boring . . . 50=very energizing']

data = []
for image in imageList: 
    img = Image.open(image) # check if its an image; open() is fast, does not load but allows access to size info
    x,y = myRatingScale.win.size
    myItem = visual.SimpleImageStim(win=myWin, image=image, units='pix', pos=[0, y/7])
    for d in dimensions:
        myRatingScale.scaleDescription.setText(d)
        myRatingScale.reset() # needed between repeated uses of the same rating scale
        event.clearEvents()
        while myRatingScale.noResponse:
            myItem.draw()
            myRatingScale.draw()
            myWin.flip()
        data.append([image, myRatingScale.getRating(detailed=True)]) # save for later, 3-tuple, with RT
        myWin.flip()
        core.wait(0.35) # brief pause, slightly smoother for the subject

print 'Example 2 data (detailed):\n', data
