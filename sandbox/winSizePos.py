#test screen size

from psychopy import visual, core

win = visual.Window([1280*2,1024], allowGUI=False, pos=[0,0])
fixationL = visual.PatchStim(win, size=[20,20],pos=[-640,0],units='pix',
    tex=None, mask='gauss')   
fixationR = visual.PatchStim(win, size=[20,20],pos=[+640,0],units='pix',
    tex=None, mask='gauss')   
fixationL.draw()
fixationR.draw()
win.update()
core.wait(2)