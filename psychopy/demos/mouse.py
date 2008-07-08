#! /usr/local/bin/python2.5
from psychopy import *
"""
Handling of the mouse has changed under pyglet - you should now
use a mouse object (from the event sub-module) to query the current
mouse position etc.

You can also check the position of the wheel now too.
"""
#create a window to draw in
myWin = visual.Window((600.0,600.0), allowGUI=True)

#INITIALISE SOME STIMULI
fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",pos=(0,0), size=(0.05,0.05),rgb=[-1.0,-1.0,-1.0])
grating = visual.PatchStim(myWin,pos=(0.5,0),
                           tex="sin",mask="gauss",
                           rgb=[1.0,0.5,-1.0],
                           size=(1.0,1.0), sf=(3,0))
myMouse = event.Mouse(win=myWin)
message = visual.TextStim(myWin,pos=(-0.95,-0.9),alignHoriz='left',height=0.08,
    text='left-drag=SF, right-drag=pos, scroll=ori')

while True: #continue until keypress
    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            core.quit()
            
    #get mouse events
    mouse_dX,mouse_dY = myMouse.getRel()
    mouse1, mouse2, mouse3 = myMouse.getPressed()
    if (mouse1):
        grating.setSF(mouse_dX/200.0, '+')
    elif (mouse3):
        grating.setPos([mouse_dX/400.0, -mouse_dY/400.0], '+')
        
    #Handle the wheel(s):
    # Y is the normal mouse wheel, but some (e.g. mighty mouse) have an x as well
    wheel_dX, wheel_dY = myMouse.getWheelRel()
    grating.setOri(wheel_dY*5, '+')
    
    event.clearEvents()#get rid of other, unprocessed events
    
    #do the drawing
    fixSpot.draw()
    grating.setPhase(0.05, '+')#advance 0.05cycles per frame
    grating.draw()
    message.draw()
    myWin.flip()#redraw the buffer

