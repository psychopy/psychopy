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
from numpy import sin, cos

# create a window to draw in
win = visual.Window(
    units="height", 
    size=(800, 800)
)

# PsychoPy has two text stimuli: TextStim and TextBox2
# think of these like Artistic Text and Text Box from most graphics programs (Affinity, Adobe, etc.):
# TextStim is some floating text centered on a point
# TextBox2 is a box with text fitted inside.
textStim = visual.TextStim(
    win,
    text="This is a TextStim, it isn't bounded by any box.",
    pos=(0, 0.2),
    height=0.03
)
textBox = visual.TextBox2(
    win,
    text="This is a TextBox2, it lives in a box. You can hide the box and it'll look like a TextStim, but text will still wrap!",
    pos=(0, 0),
    size=(0.5, 0.3),
    letterHeight=0.03,
    # set this to None and the box will be invisible
    borderColor="white"
)
# as of 2026.2.0, TextBox2 supports in-line formatting!
lionelHutz = visual.TextBox2(
    win,
    text=(
        "**Lionel Hutz Esq.**\n"
        "\n"
        "Works on contingency[color=red]?[/color]\n"
        "No[color=red],[/color] money down[color=red]![/color]\n"
    ),
    pos=(0, -0.3),
    size=(0.4, 0.2),
    fillColor="white",
    color="black"
)
# text stimuli can handle a variety of unicode characters, including emojis, so long as they are supported by the font you're using
# you can use any font installed on your machine, the following fonts also come packaged with PsychoPy:
# Noto Sans, JetBrains Mono, Indie Flower, Arvo, Deja Vu Serif
# you can also generally rely on the "web standard" fonts being available:
# https://www.w3schools.com/cssref/css_websafe_fonts.php
# if you can't see these emojis when you run, try installing Noto Emoji font:
# https://fonts.google.com/noto/specimen/Noto+Emoji
emojiText = visual.TextBox2(
    win,
    text="🤔💡🫣💯",
    font="Noto Emoji",
    letterHeight=0.03, 
    size=(0.3, 0.2), 
    pos=(0.3, 0.4)
)
# right-to-left languages are also supported, provided you have the correct font for them
# if you can't see the Farsi characters, try installing the Noto Sans Arabic font:
# https://fonts.google.com/noto/specimen/Noto+Sans+Arabic
farsiText = visual.TextBox2(
    win,
    text='Farsi text: \n \u200E خوش آمدید 1999',
    color="FireBrick",
    font="Noto Sans Arabic", 
    letterHeight=0.03, 
    size=(0.3, 0.2), 
    pos=(-0.3, 0.4)
)
# text can be updated each frame; useful for showing a live tracker!
clockText = visual.TextBox2(
    win,
    text="This will be updated...",
    # put the time small in the bottom left corner...
    anchor="bottom left",
    units="norm",
    pos=(-1, -1),
    size=(0.5, 0.2),
    letterHeight=0.1
)
win.recordFrameIntervals = True
fpsText = visual.TextBox2(
    win,
    text="This will be updated...",
    # put the frame rate small in the bottom right corner...
    anchor="bottom right",
    units="norm",
    pos=(1, -1),
    size=(0.5, 0.2),
    letterHeight=0.1
)

# you can update all sorts of attributes each frame, so let's make something wacky looking...
wackyText = visual.TextBox2(
    win,
    text="PsychoPy® by Open Science Tools Ltd.",
    letterHeight=0.05,
    # the wackiness will happen each frame, inside the frame loop lower down
    color=(1, 1, 1),
    colorSpace="rgb",
    ori=0,
    pos=(0, 0),
)

# let's put all the stimuli in a list for convenience
stimuli = [
    textStim, textBox, clockText, fpsText, lionelHutz, emojiText, farsiText, wackyText
]
# start a ticking clock
trialClock = core.Clock()
# now start the frame loop
while not event.getKeys():
    # get the time (useful for things which change over time)
    t = trialClock.getTime()
    # update the frame rate and time
    fpsText.text = "%i fps" % win.fps()
    clockText.text = "%.2f s" % t
    # apply the aforementioned wackiness
    wackyText.color = (sin(t), cos(t), t % 1 * 2 - 1 )
    wackyText.ori = t * -180
    wackyText.pos = (sin(t)/3, cos(t)/3)
    # draw all stimuli
    for stim in stimuli:
        stim.draw()
    # flip the window
    win.flip()


# # Initialize some stimuli.
# ## Note that in Python 3 we no longer need to create special unicode strings
# ## with a u'' prefix, as all strings are unicode. For the time being, we 
# ## retain the prefix in this demo, for backwards compatibility for people 
# ## running PsychoPy under Python 2.7
# fpsText = visual.TextBox2(win,
#     text="fps",
#     color="red", fillColor="black", 
#     font="Share Tech Mono", letterHeight=0.04, 
#     size=(0.2, 0.1), pos=(0, 0.1))
# psychopyTxt = visual.TextBox2(win, 
#     text=u"PsychoPy \u00A9Jon Peirce",
#     color="white", 
#     font="Indie Flower", letterHeight=0.05,
#     size=(0.6, 0.2), pos=(0, 0))
# unicodeStuff = visual.TextBox2(win,
#     text = u"unicode (eg \u03A8 \u040A \u03A3)", # You can find the unicode character value by searching online
#     color="black",
#     font="EB Garamond", letterHeight=0.05,
#     size=(0.5, 0.2), pos=(-0.5, -0.5), anchor="bottom-left")
# longSentence = visual.TextBox2(win,
#     text = u"Text wraps automatically! Just keep typing a long sentence that is very long and also it is entirely unnecessary how long the sentence is, it will wrap neatly.",
#     color='DarkSlateBlue', borderColor="DarkSlateBlue", 
#     font="Open Sans", letterHeight=0.025,
#     size=(0.4, 0.3), pos=(0.45, -0.45), anchor='bottom-right')
# mirror = visual.TextBox2(win, 
#     text="mirror mirror",
#     color='silver',
#     font="Josefin Sans",  letterHeight=0.05,
#     size=(0.2, 0.2), pos=(0, -0.1), 
#     flipHoriz=True)
# google = visual.TextBox2(win,
#     text="Now supporting Google fonts!",
#     color="blue",
#     font="Josefin Sans", letterHeight=0.03,
#     size=(0.4, 0.2), pos=(0.5, 0.5), anchor="top-right")
# ## By default, right-to-left languages like Hebrew are often shown in
# ## reversed order. Additionally, Arabic-based text by default is shown
# ## with characters in their isolated form, rather than flowing correctly
# ## into their neighbours. We can use the invisible \u200E left-to-right
# ## control character to resolve ambiguous transitions between text 
# ## directions (for example, to determine in which directional run a 
# ## punctuation character belongs).
# ## We correct these issues by setting setting the languageStyle to be
# ## 'bidirectional' (sufficient for Hebrew, for example) or 'Arabic'
# ## (which additionally does the reshaping of individual characters
# ## needed for languages based on the Arabic alphabet):
# farsi = visual.TextBox2(win,
#     text = u'Farsi text: \n \u200E خوش آمدید 1999',
#     color = 'FireBrick',
#     font="Cairo", letterHeight = 0.03, 
#     size=(0.5, 0.1), pos = (-0.5, 0.4), anchor="top-left")
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
