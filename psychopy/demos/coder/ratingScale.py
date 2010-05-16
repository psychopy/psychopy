#!/usr/bin/env python

""" demo for psychopy.visual.getRatingScale()
"""

__author__ = 'Jeremy Gray'

from psychopy import visual, event
import random

myWin = visual.Window(fullscr=True, units='pix', monitor='testMonitor') 
instr = visual.TextStim(myWin,text="""This is a demo of visual.getRatingScale(). The first example shows how easy it can be. The second example illustrates what you can do with some of the non-default settings. (JRG note: the demo looks horrible for me when I lack OpenGL extensions on linux.)

Example 1. On the next screen, you will see the default configuration, which will probably suffice for most ratings or be pretty close. It uses a 'triangle' marker style, color blue, range 1 to 7 (not at all to extremely).

By relying on the defaults, the entire next screen requires nothing more than this code in your script:

    visual.getRatingScale(myWin, "How cool was that?")

To respond, use the mouse to indicate a rating by clicking somewhere on the line (on the next screen). You can then select and drag the marker, or use the left and right arrow keys. Or type a number 1 to 7 to indicate your choice. In this example, responses are rounded to the nearest tick-mark. Then either press enter, or click the button to accept it. 

Press any key to start Example 1.""")
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

# the next line of code makes Example 1 happen:
rating, ratingRT, scaleInfo = visual.getRatingScale(myWin, "How cool was that?")
print rating, ratingRT, scaleInfo
instr = visual.TextStim(myWin,text="""Your rating was: %d on a scale of %d to %d. (These three numbers were all returned by the function. The question text is also returned.) If you want a 1 to 5 scale instead of 1 to 7, just add 'high=5' to the argument list.

Example 2. This example shows how you might present a scale akin to Lang's "Self-Assessment Manikin" for emotion ratings. First, we'll use markerStyle='glow'. The default color for 'glow' is white, but we'll use markerColor='DarkRed' instead, and we'll accept quasi-continuous ratings (precision=100) but not reveal them to the subject (showValue=False) to reduce people obsessing over exact values.

visual.getRatingScale(myWin, "How hot was that?", low=0, high=100, precision=100, markerStyle='glow', markerColor='DarkRed', markerExpansion=10, showValue=False)

The marker will become larger when placed further to the right (markerExpansion=10). low=0 and  high=100 will be added to the instructions.

Press any key to start Example 2.""" % (rating, scaleInfo[0],scaleInfo[1]))
event.clearEvents()
while len(event.getKeys()) == 0:
    instr.draw()
    myWin.flip()

# the next line of code makes Example 2 happen:
rating, ratingRT, scaleInfo = visual.getRatingScale(myWin, "How hot was that?", low=0, high=100, precision=100,
        markerStyle='glow', markerColor='DarkRed', markerExpansion=10, showValue=False)
print rating, ratingRT, scaleInfo
