"""
Show a very basic program: hello world.

The contents of this file are in the public domain.
"""

# import key parts of the PsychoPy library:
from psychopy import visual, core

# create a visual window:
win = visual.Window(
    size=[800, 800],
    units="height"
)

# create (but not yet display) some text:
msg1 = visual.TextBox2(win, 
    text="Hello world!", 
    letterHeight=0.08,
    # position this one slightly above the middle of the screen
    pos=(0, 0.2)
) 
msg2 = visual.TextBox2(win, 
    text="¡Hola mundo!", 
    letterHeight=0.08,
    # position this one slightly below the middle of the screen
    pos=(0, -0.2)
)

# draw the text to the hidden visual buffer:
msg1.draw()
msg2.draw()

# show the hidden buffer - everything that has been drawn since the last win.flip():
win.flip()

# wait 3 seconds so people can see the message
core.wait(3)

# exit gracefully
win.close()
core.quit()
