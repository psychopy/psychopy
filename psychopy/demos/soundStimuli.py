#! /usr/local/bin/python2.5
import sys
print 'started'; sys.stdout.flush()
from psychopy import sound,core

#sound.init(rate=22050, bits=16, stereo=True, buffer=1024)
#highA = sound.Sound('A',octave=6)
#highA.play()

#highA = sound.Sound(440, secs=1)
#highA.play()
#wait(1)
print 'imported'; sys.stdout.flush()
tick = sound.Sound(800,secs=0.5)
tick.setVolume(1.0)
tock = sound.Sound(900,secs=0.1)
tock.setVolume(1.0)
tick.play()
core.wait(0.3)
tock.play()

core.wait(1)

if sys.platform=='win32':
    ding = sound.Sound('ding')
    ding.setVolume(2.0)
    ding.play()

    core.wait(1)

    tada = sound.Sound('tada.wav')
#    tada.play()

    core.wait(2)
print 'done'
core.quit()