from psychopy import visual, core
from psychopy.hardware.joystick import pyglet_input

win = visual.Window([400,400])

joy = pyglet_input.get_joysticks()[0]
joy.open()
print dir(joy.device)
print joy.device.get_controls()
print joy.device.name
throttle=joy.device.get_controls()[-3]
print 'throttle', dir(throttle)
for n in range(1000):
    #joy.device.dispatch_events()
#    print joy.x, joy.y,joy.z,  joy.rx, joy.ry, joy.rz, throttle.value
    print joy.getAllAxes()
    #win.flip()
    core.wait(0.5)
    
