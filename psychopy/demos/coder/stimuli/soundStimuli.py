#!/usr/bin/env python2

"""
Sound stimuli are currently an area of development in PsychoPy

Previously we used pygame. Now the pyo library is also supported.
On OSX this is an improvement (using coreaudio rather than SDL). 
On windows this should help on systems with good sound cards, 
but this is yet to be confirmed. 
See the demo hardware>testSoundLatency too

"""
import sys
from psychopy import logging, prefs
logging.console.setLevel(logging.DEBUG)#get messages about the sound lib as it loads

from psychopy import sound,core, visual
if prefs.general['audioLib'][0] == 'pyo':
    #if pyo is the first lib in the list of preferred libs then we could use small buffer
    #pygame sound is very bad with a small buffer though
    sound.init(48000,buffer=128)
print 'Using %s(with %s) for sounds' %(sound.audioLib, sound.audioDriver)

highA = sound.Sound('A',octave=3, sampleRate=44100, secs=0.8, bits=8)
highA.setVolume(0.8)
tick = sound.Sound(800,secs=0.01,sampleRate=44100, bits=8)#sample rate ignored because already set
tock = sound.Sound('600',secs=0.01, sampleRate=44100)

highA.play()
core.wait(0.8)
tick.play()
core.wait(0.4)
tock.play()
core.wait(0.6)

if sys.platform=='win32':
    ding = sound.Sound('ding')
    ding.play()

    core.wait(1)

    tada = sound.Sound('tada.wav')
    tada.play()

    core.wait(2)
print 'done'
core.quit()
