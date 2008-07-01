#! /usr/local/bin/python2.5
from psychopy import *

#create a window to draw in
myWin = visual.Window((600.0,600.0), allowGUI=True)

#INITIALISE SOME STIMULI
fixSpot = visual.PatchStim(myWin,tex="none", mask="gauss",pos=(0,0), size=(0.05,0.05),rgb=[-1.0,-1.0,-1.0])
grating = visual.PatchStim(myWin,pos=(0.5,0),
                           tex="sin",mask="gauss",
                           rgb=[1.0,0.5,-1.0],
                           size=(1.0,1.0), sf=(3,0))

message = visual.TextStim(myWin,pos=(-0.95,-0.95),text='Hit Q to quit, fps=N/A')

while True: #continue until keypress
    #handle key presses each frame
    for key in event.getKeys():
        if key in ['escape','q']:
            core.quit()
            
    #get mouse events
    mouse_dX,mouse_dY = event.mouse.get_rel()
    mouse1, mouse2, mouse3 = event.mouse.get_pressed()
    if (mouse1):
        grating.setSF(mouse_dX/200.0, '+')
    elif (mouse3):
        grating.setPos([mouse_dX/400.0, -mouse_dY/400.0], '+')
        
    event.clearEvents()#get rid of other, unprocessed events

    #do the drawing
    fixSpot.draw()
    grating.setPhase(0.05, '+')#advance 0.1cycles per frame
    grating.draw()
    myWin.flip()#redraw the buffer

