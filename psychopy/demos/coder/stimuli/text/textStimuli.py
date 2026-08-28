#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo of text rendering in pyglet, including:
- how to specify fonts
- unicode
- rotating text
- mirror-image
- bidirectional and reshaped Arabic/Farsi text
"""

from psychopy import visual, core, event
from numpy import sin

# Create a window to draw in
win = visual.Window(units="height", size=(800, 800))
win.recordFrameIntervals = True

# Initialize some stimuli.
## Note that in Python 3 we no longer need to create special unicode strings
## with a u'' prefix, as all strings are unicode. For the time being, we 
## retain the prefix in this demo, for backwards compatibility for people 
## running PsychoPy under Python 2.7
fpsText = visual.TextBox2(win,
    text="fps",
    color="red", fillColor="black", 
    font="Share Tech Mono", letterHeight=0.04, 
    size=(0.2, 0.1), pos=(0, 0.1))
psychopyTxt = visual.TextBox2(win, 
    text=u"PsychoPy \u00A9Jon Peirce",
    color="white", 
    font="Indie Flower", letterHeight=0.05,
    size=(0.6, 0.2), pos=(0, 0))
unicodeStuff = visual.TextBox2(win,
    text = u"unicode (eg \u03A8 \u040A \u03A3)", # You can find the unicode character value by searching online
    color="black",
    font="EB Garamond", letterHeight=0.05,
    size=(0.5, 0.2), pos=(-0.5, -0.5), anchor="bottom-left")
longSentence = visual.TextBox2(win,
    text = u"Text wraps automatically! Just keep typing a long sentence that is very long and also it is entirely unnecessary how long the sentence is, it will wrap neatly.",
    color='DarkSlateBlue', borderColor="DarkSlateBlue", 
    font="Open Sans", letterHeight=0.025,
    size=(0.4, 0.3), pos=(0.45, -0.45), anchor='bottom-right')
mirror = visual.TextBox2(win, 
    text="mirror mirror",
    color='silver',
    font="Josefin Sans",  letterHeight=0.05,
    size=(0.2, 0.2), pos=(0, -0.1), 
    flipHoriz=True)
google = visual.TextBox2(win,
    text="Now supporting Google fonts!",
    color="blue",
    font="Josefin Sans", letterHeight=0.03,
    size=(0.4, 0.2), pos=(0.5, 0.5), anchor="top-right")
## By default, right-to-left languages like Hebrew are often shown in
## reversed order. Additionally, Arabic-based text by default is shown
## with characters in their isolated form, rather than flowing correctly
## into their neighbours. We can use the invisible \u200E left-to-right
## control character to resolve ambiguous transitions between text 
## directions (for example, to determine in which directional run a 
## punctuation character belongs).
## We correct these issues by setting setting the languageStyle to be
## 'bidirectional' (sufficient for Hebrew, for example) or 'Arabic'
## (which additionally does the reshaping of individual characters
## needed for languages based on the Arabic alphabet):
farsi = visual.TextBox2(win,
    text = u'Farsi text: \n \u200E خوش آمدید 1999',
    color = 'FireBrick',
    font="Cairo", letterHeight = 0.03, 
    size=(0.5, 0.1), pos = (-0.5, 0.4), anchor="top-left")
# Start a clock ticking
trialClock = core.Clock()
t = lastFPSupdate = 0
# Continues the loop until any key is pressed
while not event.getKeys():
    # Get current time from clock
    t = trialClock.getTime()
    # Draw stimuli
    mirror.draw()
    fpsText.draw()
    psychopyTxt.draw()
    unicodeStuff.draw()
    longSentence.draw()
    farsi.draw()
    google.draw()
    win.flip()
    # Update the fps text every second
    if t - lastFPSupdate > 1:
        fps = win.fps()
        fpsText.text = "%i fps" % fps
        lastFPSupdate += 1
        if fps > 50:
            fpsText.color = "green"
            print(fpsText.color)
        else:
            fpsText.color = "red"
    # Move PsychoPy text around
    psychopyTxt.pos = (sin(t)/2, sin(t)/2)
#
    
#
win.close()
core.quit()
#
# The contents of this file are in the public domain.
