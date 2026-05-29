"""
One easy way to handle stimuli that are drawn repeatedly is to
setAutoDraw(True) for that stimulus. It will continue to be drawn until
stim.setAutoDraw(False) is called. By default a logging message of
level EXP will be created when the setAutoDraw is called.

This can be turned off for each call with stim.setAutoDraw(True, autoLog=False).

The contents of this file are in the public domain.
"""

from psychopy import visual, core

# create a window
win = visual.Window(
    size=[800, 800],
    units="height"
)

# create some stimuli
stim1 = visual.GratingStim(
    win,
    pos=[-0.25, 0], 
    size=[0.3, 0.3],
    name='stim1'
)
stim2 = visual.TextBox2(
    win, 
    "Stim 2",
    pos=[0.25, 0],
    size=[0.3, 0.3],
    name='textStim'
)

# create a fixation point
fixation = visual.GratingStim(
    win, 
    mask='gauss', 
    tex=None, 
    size=0.02,
    name='fixation', 
    # we don't need to log info about the fixation point, so use autoLog=False
    autoLog=False
)

# set everything to autodraw
fixation.setAutoDraw(True)
stim1.setAutoDraw(True)
stim2.setAutoDraw(True)
# run 20 frames like this
for frameN in range(20):
    win.flip()

# only draw stim1 and the fixation point
stim2.setAutoDraw(False)
# run 20 frames like this
for frameN in range(20):
    win.flip()

# only draw stim2 and the fixation point 
stim1.setAutoDraw(False)
stim2.setAutoDraw(True)
# run 20 frames like this
for frameN in range(20):
    win.flip()

# set everything to not autodraw
fixation.setAutoDraw(False)
stim1.setAutoDraw(False)
stim2.setAutoDraw(False)
# the first flip with autodraw off for a stimulus will cause the 'off' log messages to be sent
win.flip()  

# exit
win.close()
core.quit()