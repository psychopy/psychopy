#! /usr/local/bin/python2.5
from psychopy import sound,wait
from sys import platform

sound.init(rate=22050, bits=16, stereo=True, buffer=1024)
#highA = sound.Sound('A',octave=6)
#highA.play()

highA = sound.Sound(440, secs=1,octave=6)
highA.play()
wait(1)

tick = sound.Sound(800,secs=0.01)
tick.setVolume(0.5)
tock = sound.Sound(400,secs=0.01)
tock.setVolume(0.5)
tick.play()
wait(0.5)
tock.play()

wait(1)

if platform=='win32':
    ding = sound.Sound('ding')
    ding.play()

    wait(1)

    tada = sound.Sound('tada.wav')
    tada.play()

    wait(2)
print 'done'