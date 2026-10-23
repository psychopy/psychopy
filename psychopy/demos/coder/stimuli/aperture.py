"""
Demo for the class psychopy.visual.Aperture().

Draw two gabor circles, one with an irregular aperture and one with no aperture.

The contents of this file are in the public domain
"""

from psychopy import visual, event

# create a window
win = visual.Window(
    [400, 400],
    units="norm",
    # need allowStencil=True for Aperture to work
    allowStencil=True
)
# create some instructions
instr = visual.TextBox2(
    win, 
    text="Any key to quit", 
    pos=(0, -.7)
)
# make a grating stim, this will be outside the aperture
gabor1 = visual.GratingStim(
    win, 
    mask="circle", 
    sf=4, 
    size=1.2, 
    color="lightpurple"
)
# make a different grating stim, this will be inside the aperture
gabor2 = visual.GratingStim(
    win, 
    mask='circle', 
    sf=4, 
    size=1.2, 
    color="darkbrown"
)
# make an aperture (given it a funky shape here so it's easy to tell what it is)
aperture = visual.Aperture(
    win, 
    size=(0.9, 0.9), 
    shape=[
        (-0.02, -0.0), 
        (-.8, .2), 
        (0, .6), 
        (.1, 0.06), 
        (.8, .3), 
        (.6, -.4)
    ]
) 

# start a frame loop...
while not event.getKeys():
    # start off with the aperture disabled (so everything is drawn)
    aperture.enabled = False
    # draw the instructions and first gabor
    instr.draw()
    gabor1.draw()
    # enable the aperture
    aperture.enabled = True
    # with aperture enabled, draw the other gabor (so it's hidden outside the aperture's edge)
    gabor2.draw()
    # disable aperture again when done
    aperture.enabled = False
    # flip the window
    win.flip()
