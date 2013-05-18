#!/usr/bin/env python

"""Demo to illustrate speech recognition using microphone.Speech2Text

Records 2s of speech, displays the word spoken, and sets a color.
Can be used to show subjects how loudly and clearly they need to talk.
Requires an internet connection, or get "<urlopen error [Errno 8...>"
"""
__author__ = 'Jeremy Gray'

import os
from psychopy import visual, core, event
from psychopy.microphone import switchOn, AudioCapture, Speech2Text

# Set up visual things:
win = visual.Window(color=-0.05)
quit_instr = visual.TextStim(win, text='say a color when you see the mic\n     green, hot pink, gold, fire brick, dark red, ...\npress q or say exit', height=0.08, pos=(0,-0.35), wrapWidth=1.4)
word = visual.TextStim(win, text='', height=0.2, opacity=0.8, pos=(0,.25))
icon = visual.ImageStim(win, image='mic.png', opacity=0.6)

# Set up microphone, must be 16000 or 8000 Hz for speech recognition
switchOn(sampleRate=16000)
mic = AudioCapture()

while not (event.getKeys(['escape', 'q']) or word.text in ['exit']):
    quit_instr.draw()
    word.draw()
    win.flip()
    core.wait(0.5)
    quit_instr.draw()
    word.draw()
    icon.draw()
    win.flip()

    # Record for 2 seconds, Speech2Text takes ~1s to return
    wavfile = mic.record(2)
    guess = Speech2Text(wavfile).getResponse()
    os.remove(wavfile)
    if guess.word:
        word.setText(guess.word)
    try:
        word.setColor(guess.word.replace(' ', ''))
    except:
        word.setColor(-0.7)
