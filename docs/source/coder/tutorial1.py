from psychopy import visual, core, event #import some libraries from PsychoPy
from psychopy.hardware import keyboard

#create a window
mywin = visual.Window([800,600],monitor="testMonitor", units="deg")

#create some stimuli
grating = visual.GratingStim(win=mywin, mask='circle', size=3, pos=[-4,0], sf=3)
fixation = visual.GratingStim(win=mywin, size=0.2, pos=[0,0], sf=0, rgb=-1)

#create a keyboard component
kb = keyboard.Keyboard()

#draw the stimuli and update the window
while True: #this creates a never-ending loop
    grating.setPhase(0.05, '+')#advance phase by 0.05 of a cycle
    grating.draw()
    fixation.draw()
    mywin.flip()

    if len(kb.getKeys()) > 0:
        break
    event.clearEvents()

#cleanup
mywin.close()
core.quit()
