#import pygame
#from pygame import mixer

#mixer.init(22050,-16,2)
#print mixer.get_init()

from psychopy import core, sound
import numpy

clock = core.Clock()
#default sound rate: 22050Hz

mySound = sound.Sound('pinknoiseburst.wav')
print clock.getTime()
mySound.play()
print clock.getTime()

core.wait(2) #give the sound long enough to playq