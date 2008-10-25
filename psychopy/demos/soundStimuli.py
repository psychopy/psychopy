#! /usr/local/bin/python2.5
import sys
from psychopy import sound,core

highA = sound.Sound('A',octave=5, secs=0.4)
tick = sound.Sound(700,secs=0.02)
tock = sound.Sound(600,secs=0.02)

highA.play()
core.wait(1.0) #to let the sound play
tick.play()
core.wait(0.5) #to let the sound play
tock.play()

core.wait(1)

if sys.platform=='win32':
    ding = sound.Sound('ding')
    ding.play()

    core.wait(1)

    tada = sound.Sound('tada.wav')
    tada.play()

    core.wait(2)
print 'done'
core.quit()
