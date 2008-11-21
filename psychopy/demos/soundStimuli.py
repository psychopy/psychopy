#! /usr/local/bin/python2.5
import sys
from psychopy import sound,core, visual

highA = sound.Sound('A',octave=5, secs=0.01)
highA.setVolume(0.2)
tick = sound.Sound(700,secs=0.01)
tock = sound.Sound(600,secs=0.01)

core.wait(0.5)
highA.play()
core.wait(0.5) #to let the sound play
tick.play()
core.wait(0.5)
tock.play()
core.wait(0.5)
tick.play()
core.wait(0.5)

if sys.platform=='win32':
    ding = sound.Sound('ding')
    ding.play()

    core.wait(1)

    tada = sound.Sound('tada.wav')
    tada.play()

    core.wait(2)
print 'done'
core.quit()
