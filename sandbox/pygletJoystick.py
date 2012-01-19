from psychopy import visual, core
from psychopy.hardware.joystick import pyglet_input
import pygame

win = visual.Window([400,400], winType='pygame')

pygame.joystick.init()#initialise the module
myJoystick = pygame.joystick.Joystick(0)
myJoystick.init()#initialise the device
print 'found ', myJoystick.get_name(), ' with:'
print '...', myJoystick.get_numbuttons(), ' buttons'
print '...', myJoystick.get_numhats(), ' hats'
print '...', myJoystick.get_numaxes(), ' analogue axes'

for n in range(1000):
    for axis in range(myJoystick.get_numaxes()):
        print myJoystick.get_axis(axis),
    print ' '
    win.flip()
    core.wait(0.5)
    
