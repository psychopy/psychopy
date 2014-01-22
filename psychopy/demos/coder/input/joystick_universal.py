#!/usr/bin/env python2
from psychopy import visual, core, event
from psychopy.hardware import joystick

"""There are two ways to retrieve info from the first 3 joystick axes. You can use::
    joy.getAxis(0)
    joy.getX()
Beyond those 3 axes you need to use the getAxis(id) form.
Although it may be that these don't always align fully. This demo should help you
to find out which physical axis maps to which number for your device.

Known issue: Pygame 1.91 unfortunately spits out a debug message every time the 
joystick is accessed and there doesn't seem to be a way to get rid of those messages.
"""

joystick.backend='pyglet'
#create a window to draw in
myWin = visual.Window((800.0,800.0), allowGUI=False, 
    winType=joystick.backend)#as of v1.72.00 you need the winType and joystick.backend to match

nJoysticks=joystick.getNumJoysticks()

if nJoysticks>0:
    joy = joystick.Joystick(0)
    print 'found ', joy.getName(), ' with:'
    print '...', joy.getNumButtons(), ' buttons'
    print '...', joy.getNumHats(), ' hats'
    print '...', joy.getNumAxes(), ' analogue axes'
else:
    print "You don't have a joystick connected!?"
    myWin.close()
    core.quit()
nAxes=joy.getNumAxes()
#INITIALISE SOME STIMULI
fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",pos=(0,0), size=(0.05,0.05),color='black')
grating = visual.PatchStim(myWin,pos=(0.5,0),
                    tex="sin",mask="gauss",
                    color=[1.0,0.5,-1.0],
                    size=(0.2,.2), sf=(2,0))
message = visual.TextStim(myWin,pos=(0,-0.95),text='Hit "q" to quit')

trialClock = core.Clock()
t = 0
while 1:#quits after 20 secs
    #update stim from joystick
    xx = joy.getX()
    yy = joy.getY()
    grating.setPos((xx, -yy))
    #change SF
    if nAxes>3: 
        sf = (joy.getZ()+1)*2.0#so should be in the range 0:4?
        grating.setSF(sf)
    #change ori
    if nAxes>6: 
        ori = joy.getAxis(5)*90
        grating.setOri(ori)
    #if any button is pressed then make the stimulus coloured
    if sum(joy.getAllButtons()):
        grating.setColor('red')
    else:
        grating.setColor('white')
        
    #drift the grating
    t=trialClock.getTime()
    grating.setPhase(t*2)
    grating.draw()
    
    fixSpot.draw()
    message.draw()
    print joy.getAllAxes()#to see what your axes are doing!
    
    if 'q' in event.getKeys():
        core.quit()
        
    event.clearEvents()#do this each frame to avoid getting clogged with mouse events
    myWin.flip()#redraw the buffer

