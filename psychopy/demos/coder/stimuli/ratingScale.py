#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo for the class psychopy.visual.RatingScale()

author: Jeremy Gray, Example 4 by Henrik Singmann
"""

from __future__ import division
from __future__ import print_function

from psychopy import visual, event, core, logging
import os

# create a window before creating your rating scale, whatever units you like:
win = visual.Window(fullscr=False, size=[1100, 800], units='pix', monitor='testMonitor')
instr = visual.TextStim(win, text="""This is a demo of visual.RatingScale(). There are four examples.

Example 1 is on the next screen. Use the mouse to indicate a rating: click somewhere on the line. You can also use the arrow keys to move left or right.

To accept your rating, either press 'enter' or click the glowing button. Pressing 'tab' will skip the rating.

Press any key to start Example 1 (or escape to quit).""")

event.clearEvents()
instr.draw()
win.flip()
if 'escape' in event.waitKeys():
    core.quit()

# Example 1 --------(basic choices)--------
# create a RatingScale object:
myRatingScale = visual.RatingScale(win, choices=['cold', 'cool', 'hot'])

# Or try this one:
# myRatingScale = visual.RatingScale(win, choices=map(str, range(1, 8)), marker='hover')

# the item to-be-rated or respond to:
myItem = visual.TextStim(win, text="How cool was that?", height=.12, units='norm')

# anything with a frame-by-frame .draw() method will work, e.g.:
# myItem = visual.MovieStim(win, 'jwpIntro.mov')

event.clearEvents()
while myRatingScale.noResponse:  # show & update until a response has been made
    myItem.draw()
    myRatingScale.draw()
    win.flip()
    if event.getKeys(['escape']):
        core.quit()

print('Example 1: rating =', myRatingScale.getRating())
print('history =', myRatingScale.getHistory())

# Example 2 --------(multiple items, multiple dimensions for each)--------
instr = visual.TextStim(win, text="""Example 2. This example uses non-default settings for the visual display, skipping a rating is not possible, and it uses a list of images (two) to be rated on several dimensions (valence and arousal).

Try this: Place a marker, then drag it along the line using the mouse. In this example, you cannot use numeric keys to respond because the scale is 0 to 50.

Press any key to start Example 2 (or escape to quit).""")

event.clearEvents()
instr.draw()
win.flip()
if 'escape' in event.waitKeys():
    core.quit()

# create a scale for Example 2, using quite a few non-default options:
myRatingScale = visual.RatingScale(win, low=0, high=50, precision=10, skipKeys=None,
        marker='glow', markerExpansion=10, showValue=False, pos=[0, -200], name='Example2')

# using a list is handy if you have a lot of items to rate on the same scale, eg personality adjectives or images:
imageList = ['beach.jpg', 'face.jpg']

data = []
for image in imageList:
    x, y = myRatingScale.win.size
    myItem = visual.SimpleImageStim(win=win, image=image, units='pix', pos=[0, y//7])

    # rate each image on two dimensions
    for dimension in ['0=very negative . . . 50=very positive',
                      '0=very boring . . . 50=very energizing']:
        myRatingScale.reset()  # reset between repeated uses of the same scale
        myRatingScale.setDescription(dimension)  # reset the instructions
        event.clearEvents()
        while myRatingScale.noResponse:
            myItem.draw()
            myRatingScale.draw()
            win.flip()
            if event.getKeys(['escape']):
                core.quit()
        data.append([image, myRatingScale.scaleDescription.text,
                     myRatingScale.getRating(), myRatingScale.getRT()])  # save for later

        # clear the screen & pause between ratings
        win.flip()
        core.wait(0.35)  # brief pause, slightly smoother for the subject

print('Example 2 (data from 2 images, each rated on 2 dimensions, reporting rating & RT):')
for d in data:
    print('  ', d)

# Example 3 --------(two simultaneous ratings)--------
instr = visual.TextStim(win, text="""Example 3. This example shows how one could obtain two ratings at the same time, e.g., to allow explicit comparison between images during ratings.

In such a situation, the subject will have to use the mouse (and not keyboard) to respond. The subject has to respond on both scales in order to go on to the next screen. Both of these considerations mean that it's best to disallow the subject to skip a rating.

Press any key to start Example 3 (or escape to quit).""")

event.clearEvents()
instr.draw()
win.flip()
if 'escape' in event.waitKeys():
    core.quit()

x, y = win.size  # for converting norm units to pix
leftward = -0.35 * x / 2  # use pix units, because the drawing window's units are pix
rightward = -1 * leftward
# for logging, its useful to give names, esp when there are 2 on-screen
myRatingScaleLeft = visual.RatingScale(win, mouseOnly=True, pos=(leftward, -y/6),
    marker='circle', size=0.85, name='left')
myRatingScaleRight = visual.RatingScale(win, mouseOnly=True, pos=(rightward, -y/6),
    markerColor='DarkGreen', size=0.85, name='right')

myItemLeft = visual.SimpleImageStim(win=win, image=imageList[0], pos=[leftward, y/6.])
myItemRight = visual.SimpleImageStim(win=win, image=imageList[1], pos=[rightward, y/6.])

event.clearEvents()
while myRatingScaleLeft.noResponse or myRatingScaleRight.noResponse:
    # you could hide the item if its been rated:
    # if myRatingScaleLeft.noResponse: myItemLeft.draw()
    # or easier: just initialize it with the disappear=True option
    # but lets just draw it every frame:
    myItemLeft.draw()
    myItemRight.draw()
    myRatingScaleLeft.draw()
    myRatingScaleRight.draw()
    win.flip()
    if event.getKeys(['escape']):
        core.quit()

# just for fun: briefly show the two scales with the markers in the 'down' position
myItemLeft.draw()
myItemRight.draw()
myRatingScaleLeft.draw()
myRatingScaleRight.draw()
win.flip()
core.wait(1)

print('Example 3:\n  rating left=', myRatingScaleLeft.getRating(), ' rt=%.3f' % myRatingScaleLeft.getRT())
print('  rating right=', myRatingScaleRight.getRating(), ' rt=%.3f' % myRatingScaleRight.getRT())

# Example 4 --------(using tickMarks argument)--------
instr = visual.TextStim(win, text="""Example 4.

In this example we will use acustim tick marks, a slider, and custom labels for a scale from 0 too 100.

Press any key to start Example 4 (or escape to quit).""")

event.clearEvents()
instr.draw()
win.flip()
if 'escape' in event.waitKeys():
    core.quit()

myRatingScale = visual.RatingScale(win, low=0, high=100, marker='slider',
    tickMarks=[0, 50, 82, 100], stretch=1.5, tickHeight=1.5,  # singleClick=True,
    labels=["0%", "half/half", "kinda", "100%"])
txt = "How probable is it that you will use this functionality in your next experiment?"
myItem = visual.TextStim(win, text=txt, height=.08, units='norm')

# show & update until a response has been made
while myRatingScale.noResponse:
    myItem.draw()
    myRatingScale.draw()
    win.flip()
    if event.getKeys(['escape']):
        core.quit()

print('Example 4: rating =', myRatingScale.getRating())

win.close()
core.quit()

# The contents of this file are in the public domain.
