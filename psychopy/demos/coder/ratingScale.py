#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale(). in the code, look for "myVRS", lines 25 & 26, and 44 & 60
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
rating, ratingRT, scaleInfo = myVRS.rate("How cool was that?") # get a rating, decision time, scale info

# Example 2 --------
instr = visual.TextStim(myWin,text="""The code to produce Example 1 was just two lines:
  myVRS = visual.RatingScale(myWin) # create a scale
  myVRS.rate("How cool was that?") # get a rating

Example 2. This example uses non-default settings for the visual display, automatically detects that images are requested, and uses a list of images to be rated. In addition, you will be asked to rate each image on two dimensions: valence and arousal.

Try this: Place a marker, then drag it along the line using the mouse. In this example, you cannot use 1 to 7 keys to respond because the scale is 0 to 10.

Press any key to start Example 2.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

# create a scale for Example 2, using quite a few non-default options:
myVRS = visual.RatingScale(myWin, low=0, high=10, precision=10, 
        markerStyle='glow', markerExpansion=10, showValue=False, lowLine=True)

# using a list is handy if you have a lot of items to rate on the same scale, eg personality adjectives or images:
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']] # all .png or .jpg images in the current directory
if len(imageList) > 2: 
    imageList = imageList[:2]
if len(imageList) == 0: # just in case; text will work because images are auto-detected from filenames
    imageList = ['puppy in the daisies', 'war hatchet']

# optional: it can be useful to obtain ratings on several dimensions for each item:
dimensions = ['0=very negative . . . 10=very positive', '0=boring . . . 10=extremely energizing']
data = []
for image in imageList: # get a set of ratings for each image, different dimensions, all on the same scale
    random.shuffle(dimensions) # optional: randomize which dimension will get rated first
    ratings = myVRS.rateDimensions(image, dimensions) # typically use rate() for just a single dimension
    data.append(ratings) # save for later

# pick an image, just to show that all the data are stored, including the item text information (which might be an image file name):
sample = data[random.choice(range(len(data)))] # 'sample' holds a list of tuples, one tuple per dimension
print sample
core.quit()
