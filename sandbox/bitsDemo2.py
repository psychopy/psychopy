from psychopy import visual, core, event
import numpy

#create a window with bitsMode='fast' (why would you ever use 'slow'!?)
win = visual.Window([800,800], bitsMode='fast')

grating = visual.PatchStim(win,mask = 'gauss',sf=2)


#---using bits++ with one stimulus
globalClock = core.Clock()
while True:
    #get new contrast
    t=globalClock.getTime()
    newContr = numpy.sin(t*numpy.pi*2)#sinusoidally modulate contrast
    
    #set whole screen to this contrast
    win.bits.setContrast(newContr)# see http://www.psychopy.org/reference/
    #draw gratings and update screen
    grating.draw()
    win.update()
    
    #check for a keypress
    if event.getKeys():
        break
    event.clearEvents()

grating1 = visual.PatchStim(win,mask = 'circle', pos=[0.5,0.0],sf=2,
    contrast=0.25, rgbPedestal=[0.5, 0.5, 0.5])
grating2 = visual.PatchStim(win,mask = 'circle', pos=[-0.5,0.0],sf=2,
    contrast=0.25, rgbPedestal=[-0.5, -0.5, -0.5])
while True:
    t=globalClock.getTime()
    newContr = numpy.sin(t*numpy.pi*2)#sinusoidally modulate contrast
    
    win.bits.setContrast(newContr, LUTrange=[0.25,0.4999])#grating 1
    win.bits.setContrast(newContr/3.0, LUTrange=[0.5,0.75])#grating 2
    #draw gratings and update screen
    grating1.draw()
    grating2.draw()
    win.update()
    
    #check for a keypress
    if event.getKeys():
        break
    event.clearEvents()
    
#reset the bits++ (and update the window so that this is done properly)
win.bits.setContrast(1)
win.update()
core.quit()