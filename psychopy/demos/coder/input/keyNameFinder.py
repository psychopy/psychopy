from psychopy import visual
from psychopy.hardware import keyboard

# Make window
win = visual.Window(units="height")

# To have keyboard.Keyboard() use iohub backend, start the iohub server
# prior to creating a Keyboard() instance.
# from psychopy.iohub import launchHubServer
# launchHubServer(window=win)

# Make instructions textbox
instr = visual.TextBox2(win,
    text="Press any key...",
    font="Open Sans", letterHeight=0.1,
    pos=(0, 0.2))
# Make key name textbox
output = visual.TextBox2(win,
    text="No key pressed yet",
    font="Open Sans", letterHeight=0.1,
    pos=(0, -0.2))
# Make keyboard object
kb = keyboard.Keyboard()
# Listen for keypresses until escape is pressed
keys = kb.getKeys()
while 'escape' not in keys:
    # Draw stimuli
    instr.draw()
    output.draw()
    win.flip()
    # Check keypresses
    keys = kb.getKeys()
    if keys:
        # If a key was pressed, display it
        output.text = f"That key was `{keys[-1].name}`. Press another key."
        for k in keys:
            print(k.name, k.code, k.tDown, k.rt, k.duration)
# End the demo
win.close()
