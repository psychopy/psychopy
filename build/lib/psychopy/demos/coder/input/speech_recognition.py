#!/usr/bin/env python2

"""Demo to illustrate speech recognition using microphone.Speech2Text

Requires flac, which does not come with PsychoPy. You can get it free,
download & install from https://xiph.org/flac/download.html

Records 2.5s of speech, displays the word(s) spoken, and sets a color.
Can be used to show subjects how loudly and clearly they need to talk.
"""
__author__ = 'Jeremy Gray'

import os
from psychopy import visual, core, event, colors, web
from psychopy.microphone import switchOn, AudioCapture, Speech2Text

web.requireInternetAccess()  # needed to access google's speech API

def display(*args):
    [item.draw() for item in args]
    win.flip()

# PsychoPy only knows English color names; 'en-UK' might work better here for some speakers:
options = {'lang': 'en-US'}

# Set up visual things:
win = visual.Window(color=-0.05)
instr = visual.TextStim(win, text='say a color name when you see the microphone icon\n     green, hot pink, gold, fire brick, dark red, ...\n\npress q or say exit to quit;   expects "%s" input' % options['lang'], height=0.08, pos=(0,-0.4), wrapWidth=1.4)
word = visual.TextStim(win, text='', height=0.2, opacity=0.8, pos=(0,.25))
icon = visual.ImageStim(win, image='mic.png', opacity=0.6)
anykey = visual.TextStim(win, text='Press any key to start', pos=instr.pos-[0,.3], color='darkblue')

display(instr, anykey)
if 'escape' in event.waitKeys(): core.quit()
win.flip()

# Set up microphone, must be 16000 or 8000 Hz for speech recognition
switchOn(sampleRate=16000)
mic = AudioCapture()

while not (event.getKeys(['escape', 'q']) or word.text in ['exit']):
    display(instr, word)
    core.wait(1.5)
    display(instr, word, icon)

    # Record for 2.5 seconds, get the "best word" guess:
    wavfile = mic.record(2.5)
    display(instr, word)
    guess = Speech2Text(wavfile, **options).getResponse()
    os.remove(wavfile)

    if guess.word:
        word.setText(guess.word)
    color = guess.word.replace(' ', '').lower()  # Green -> green
    if not color in colors.colors:
        color = 'black'
    word.setColor(color)

win.flip()
