#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale(). in the code, look for "myVRS", lines 25 & 26, and 42 & 49
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core
import random, os

# create a window before creating your rating scale:
myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor')

# instructions for using a rating scale, from the subject's point of view:
instr = visual.TextStim(myWin,text="""This is a demo of visual.RatingScale(). There are two examples.

Example 1 uses the default configuration. You can use the mouse to indicate a rating: just click on the line (on the next screen). You can then select and drag the marker, or use the left and right arrow keys. Or you can type a number 1 to 7 to indicate your choice. To accept your rating, either press 'enter' or click the button.

Press any key to start Example 1.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

# Example 1 --------
myVRS = visual.RatingScale(myWin) # create a RatingScale object with default settings
myVRS.rate("How cool was that?")     # get a rating (but here, ignore the returned data; see Example 2 for saving data)

# Example 2 --------
instr = visual.TextStim(myWin,text="""The code to produce Example 1 was just two lines:
  myVRS = visual.RatingScale(myWin) # create a scale
  myVRS.rate("How cool was that?") # get a rating

Example 2. This example uses non-default settings for the visual display, automatically detects that images are requested, and uses a list of items to be rated. Try this: Place a marker, then drag it along the line using the mouse. In this example, you cannot use 1 to 7 keys to respond because the scale is 0 to 100.

Press any key to start Example 2.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

# create a scale for Example 2, using quite a few non-default options:
myVRS = visual.RatingScale(myWin, low=0, high=100, precision=100, scale="0=don't like at all . . . 100=breath-taking",
        markerStyle='glow', markerExpansion=10, showValue=False, lowLine=True)

# using a list is handy if you have a lot of items to rate on the same scale, eg personality adjectives or images:
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']] # all .png or .jpg images in the current directory
data = []
for image in imageList:
    rating, ratingRT, scaleInfo = myVRS.rate(image) # get a rating for each image, all on the same scale; rate() auto-detects that its an image
    data.append([rating, ratingRT, scaleInfo]) # save for later

# pick an image, just to show that all the data are stored, including the item text information (which might be an image file name):
sample = data[random.choice([0,1])] 
print """
Your rating for '%s' was:
    %d  (on a scale of %d to %d), made in %.3f sec
""" % (sample[2][3], sample[0], sample[2][0],sample[2][1], sample[1]) # typically you'll want the rating = sample[0], and maybe the decision time sample[1]