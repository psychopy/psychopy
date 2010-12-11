from psychopy import visual, core

win = visual.Window([600,600])

dot1 = visual.PatchStim(win, size=0.5, mask='gauss', pos=[-0.5, 0], sf=2, ori=90)
bigStim = visual.PatchStim(win, size=1.5, mask=None, pos=[0, 0], sf=2)
dot2 = visual.PatchStim(win, size=0.5, mask='gauss', pos=[0.5, 0], sf=2, ori=90)

if False:#drawing not in same order as creation (above)
    dot2.draw()
    bigStim.draw()
    dot1.draw()
else:
    bigStim.draw()
    dot1.draw()
    dot2.draw()
    
win.update()

core.wait(2)
win.close()