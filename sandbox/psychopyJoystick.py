from psychopy import visual, core
from psychopy.hardware import joystick
joystick.backend='pyglet'

win = visual.Window([400,400], winType='pyglet')

print 'Found %i joysticks' %joystick.getNumJoysticks()
joy = joystick.Joystick(0)
print 'testing joystick named:', joy.name
print '...', joy.getNumButtons(), ' buttons'
print '...', joy.getNumHats(), ' hats'
print '...', len(joy.getAllAxes()), ' analogue axes'

print joy.getAllAxes()
print dir(joy.getAllAxes()[0])
for n in range(1000):
    print joy.getAllAxes()
    print joy.getX(), joy.getY(), joy.getZ()
    win.flip()
    core.wait(0.5)
    
