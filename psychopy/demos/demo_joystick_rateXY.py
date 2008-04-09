from psychopy import *
import pygame

#create a window to draw in
myWin = visual.Window((800.0,800.0), allowGUI=False)

if event.joystick.get_count()>0:
    MyJoystick = pygame.Joystick(0)
    MyJoystick.init()
    print 'found ', MyJoystick.get_name(), ' with:'
    print '	', MyJoystick.get_numbuttons(), ' buttons'
    print '	', MyJoystick.get_numhats(), ' hats'
    print '	', MyJoystick.get_numaxes(), ' analogue axes'
else:
    print "You don't have a joystick connected!?"
    myWin.close()
    core.quit()
    
#INITIALISE SOME STIMULI
fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",pos=(0,0), size=(0.05,0.05),rgb=[-1.0,-1.0,-1.0])
grating = visual.PatchStim(myWin,pos=(0.5,0),
                    tex="sin",mask="gauss",
                    rgb=[1.0,0.5,-1.0],
                    size=(0.2,.2), sf=(2,0))
message = visual.TextStim(myWin,pos=(-0.95,-0.95),text='Hit Q to quit')

trialClock = Clock()
t = 0
while 1:#quits after 20 secs
    
    #handle events first
    pygame.event.pump()#refresh the event loop
    if MyJoystick.get_button(0):
        myWin.close()
        core.quit()

    #get joystick data
    xx = MyJoystick.get_axis(0)			*0.3#scale factors
    yy = MyJoystick.get_axis(1)			*0.3
    sf = MyJoystick.get_axis(2)			*(-5) + 5
    deltaOri = MyJoystick.get_axis(3)	*5
    if (xx**2+yy**2.0)**0.5 > 0.05:
        grating.set('pos',(xx*0.1, -yy*0.1),'+')
    if abs(deltaOri)>2:
        grating.set('ori',deltaOri,'+')
    grating.set('sf',sf)
    
    t=trialClock.getTime()
    
    fixSpot.draw()
    
    grating.set('phase',t*2)
    grating.draw()
    
    message.draw()
    
    event.clearEvents()#need to do this every frame
    myWin.update()#redraw the buffer

