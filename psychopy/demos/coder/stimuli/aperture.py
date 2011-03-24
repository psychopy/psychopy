from psychopy import visual, core, event

win = visual.Window([400,400],allowStencil=True)
gabor1 = visual.PatchStim(win, mask='circle', pos=[0.3, 0.3], 
    sf=4, size=1,
    color=[0.5,-0.5,1])
gabor2 = visual.PatchStim(win, mask='circle', pos=[-0.3, -0.3], 
    sf=4, size=1,
    color=[-0.5,-0.5,-1])
aperture = visual.Aperture(win, size=100,pos=[10,0])
aperture.enable()#actually is enabled by default when created
gabor1.draw()
aperture.disable()#drawing from here ignores aperture
gabor2.draw()

win.flip()
event.waitKeys()