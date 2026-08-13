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
