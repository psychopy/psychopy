#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale().
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core
import random, os
import Image

# create a window before creating your rating scale:
myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor') 
    # the demo uses pix just to show that it does not have to be norm

# instructions for using a rating scale, from the subject's point of view:
instr = visual.TextStim(myWin,text="""This is a demo of visual.RatingScale(). There are two examples.

Example 1 uses the default configuration. You can use the mouse to indicate a rating: just click on the line (on the next screen). You can then select and drag the marker, or use the left and right arrow keys. Or you can type a number 1 to 7 to indicate your choice. To accept your rating, either press 'enter' or click the button.

Press any key to start Example 1.""")
event.clearEvents()
while len(event.getKeys()) == 0: # wait for any key...
    instr.draw()
    myWin.flip()

# Example 1 --------
myRatingScale = visual.RatingScale(myWin) # create a RatingScale object with default settings
myItem = visual.TextStim(myWin, text="How cool was that?", height=myRatingScale.textSize, units='norm')

event.clearEvents()
while myRatingScale.noResponse:
    myItem.draw()
    myRatingScale.draw()
    event.clearEvents()
    myWin.flip()
rating, ratingRT, scaleInfo = myRatingScale.getRating()

print 'Example 1:'
print rating, ratingRT, scaleInfo


# Example 2 --------
instr = visual.TextStim(myWin, text="""Example 2. This example uses non-default settings for the visual display, skipping a rating is not possible, and it uses a list of images to be rated. In addition, you will be asked to rate each image on two dimensions: valence and arousal.

Try this: Place a marker, then drag it along the line using the mouse. In this example, you cannot use 1 to 7 keys to respond because the scale is 0 to 10.

Press any key to start Example 2.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

# create a scale for Example 2, using quite a few non-default options:
myRatingScale = visual.RatingScale(myWin, low=0, high=10, precision=10, 
        markerStyle='glow', markerExpansion=10, showValue=False, allowSkip=False, lowLine=True)

# using a list is handy if you have a lot of items to rate on the same scale, eg personality adjectives or images:
imageList = [f for f in os.listdir('.') if len(f) > 4 and f[-4:] in ['.jpg','.png']] # all .png or .jpg images in the current directory
if len(imageList) > 2: 
    imageList = imageList[:2]

# optional: it can be useful to obtain ratings on several dimensions for each item, here two dimensions:
dimensions = ['0=very negative . . . 10=very positive', 
                        '0=boring . . . 10=extremely energizing']

# get a set of ratings for each image, different dimensions, all on the same scale
data = [ ]
for image in imageList: 
    img = Image.open(image) # check if its an image; its fast to open(), does not load it
    x,y = myRatingScale.win.size
    myItem = visual.SimpleImageStim(win=myWin, image=image, units='pix', pos=[0, y/7])
    # myItem = visual.TextStim(....) # can do text or PatchStime, too, of course
    # myItem = visual.PatchStim(win=self.win, tex=item, units='pix', size=img.size, pos=[0, y/5.5])
    
    #random.shuffle(dimensions) # could randomize which dimension comes first for each image
    for d in dimensions:
        myRatingScale.psyScaleDescription.setText(d)
        myRatingScale.reset() # needed for repeated use of the same rating scale
        event.clearEvents()
        while myRatingScale.noResponse:
            myItem.draw()
            myRatingScale.draw()
            event.clearEvents()
            myWin.flip()
        data.append([image, myRatingScale.getRating()]) # save for later

print 'Example 2:'
print "data =", data

core.quit()
