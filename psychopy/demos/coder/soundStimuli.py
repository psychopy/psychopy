#!/usr/bin/env python

"""
For sound use, I really recommend installing pygame (v1.8 or later). 
For users of the intel-Mac app bundle you already have it. Pyglet will
play sounds, but I find them unpredictable in timing and (sometimes they
don't seem to play at all. :-(

PsychoPy sound handling with pygame is not ideal, with a latency of 20-30ms, but at least with pygame it is robust - 
all sounds play consistently. I hope one day to write a better, low-level handler for playing sounds directly from the
drivers (e.g. CoreAudio, DirectSound, ASIO), but for now, pygame will have to do.

"""
import sys
from psychopy import sound,core, visual

highA = sound.Sound('A',octave=3, sampleRate=22050, secs=0.8, bits=8)
highA.setVolume(0.8)
tick = sound.Sound(800,secs=0.01,sampleRate=44100, bits=8)
tock = sound.Sound(600,secs=0.01)

highA.play()
core.wait(0.8)
tick.play()
core.wait(0.4)
tock.play()
core.wait(0.2)

if sys.platform=='win32':
    ding = sound.Sound('ding')
    ding.play()

    core.wait(1)

    tada = sound.Sound('tada.wav')
    tada.play()

    core.wait(2)
print 'done'
core.quit()
