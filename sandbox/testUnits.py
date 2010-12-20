from psychopy import visual, event

win = visual.Window([400,400], units='pix')
stim = visual.PatchStim(win, tex='sin', size=200, units=None)
stim.draw()
win.update()

event.waitKeys()