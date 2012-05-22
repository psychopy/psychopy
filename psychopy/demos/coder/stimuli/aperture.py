from psychopy import visual, core, event

win = visual.Window([400,400],allowStencil=True,units='norm')
gabor1 = visual.GratingStim(win, mask='circle', pos=[0.2, 0.2], 
    sf=4, size=.4,
    color=[0.5,-0.5,1])
gabor2 = visual.GratingStim(win, mask='circle', pos=[-0.2, -0.2], 
    sf=4, size=.4,
    color=[-0.5,-0.5,-1])

aperture = visual.Aperture(win, size=.5,pos=[0.16, 0.16],shape='square')
aperture.enable()#actually is enabled by default when created
gabor1.draw()
aperture.disable()#drawing from here ignores aperture
gabor2.draw()

win.flip()
event.waitKeys()