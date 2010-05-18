#!/usr/bin/env python

""" demo for the class psychopy.visual.RatingScale(). in the code, look for "myVRS", lines 24 & 30, and 57 & 59
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core
import random, os

myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor')
instr = visual.TextStim(myWin,text="""This is a demo of visual.RatingScale(). There are two examples.

To rate an item, use the mouse to indicate your rating by clicking somewhere on the line (on the next screen). You can then select and drag the marker, or use the left and right arrow keys. Or type a number 1 to 7 to indicate your choice. In this example, responses are rounded to the nearest tick-mark. Then either press enter, or click the button to accept it. 

Press any key to start Example 1, which has two displays, both using the default settings.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

"""Example 1 uses the default configuration, which will probably suffice for most ratings (or be quite close). 
The scale uses a 'triangle' marker style, color DarkBlue, range 1 to 7, for "not at all" to "extremely"."""
# create an RatingScale object with display parameters--here using default settings for everything:
myVRS = visual.RatingScale(myWin)  # try: visual.RatingScale(myWin, markerStyle='circle')
# you do not need to use a list with a RatingScale object; its handy if you have a lot of items to rate on the same scale:
itemList = ["How cool was that?", "How WARM was that?"]
data = []
for item in itemList: 
    rating, ratingRT, scaleInfo = myVRS.rate(item) # get the rating info for each item
    data.append([rating, ratingRT, scaleInfo])
    myWin.flip()
    core.wait(0.5) # subjects can feel rushed if the next question pops up too quickly

# pick one of the items, just to show that all the data are stored, including the item text information (which might be an image file name):
sample = data[random.choice([0,1])] 
instr = visual.TextStim(myWin,text="""Your rating for '%s' was: %d on a scale of %d to %d.""" % (
                sample[2][3], sample[0], sample[2][0],sample[2][1]))
instr.draw()
myWin.flip()
core.wait(4)

"""Example 2 uses markerStyle='glow'. The default color for 'glow' is white, but we'll use markerColor='DarkRed' instead, 
and we'll accept quasi-continuous ratings (precision=100) but not reveal them to the subject (showValue=False) to 
reduce people obsessing over exact values. The marker will become larger when placed further to the right (markerExpansion=10). 
low=0 and  high=100 will be added to the instructions."""

instr = visual.TextStim(myWin,text="""
Example 2. This example uses non-default settings for the visual display, and automatically detects that the text is a filename. Try this: Place a marker, then drag it along the line using the mouse.

Press any key to start Example 2.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

myVRS = visual.RatingScale(myWin, low=0, high=100, precision=100, scale="0=don't like at all . . . 100=breath-taking",
        markerStyle='glow', markerColor='DarkRed', markerExpansion=10, showValue=False, lowLine=True)
imageList = [f for f in os.listdir('.') if f.find('.png') > -1 or f.find('.jpg') > -1] # gets a list of all likely png or jpg images in current directory
random.shuffle(imageList)
for image in imageList:
    print myVRS.rate(image) 

