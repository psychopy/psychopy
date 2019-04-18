from psychopy import visual, event, core
from psychopy.hardware import keyboard

showAll = True  # if False then only show codes that are 'wrong'

print("Keyboards:")
for kb in keyboard.getKeyboards():
    print("{}: {}".format(kb['index'], kb['product']))

kb = keyboard.Keyboard()
win = visual.Window()
msg = visual.TextStim(win, 'press a key')
msg.draw()
win.flip()
keyNames = {}
while True:
    txt = ''
    pygKey = event.waitKeys()[0]
    # wait for the key to be raised
    keys = kb.getKeys(waitRelease=False)
    for key in keys:
        keyCode = key.code
        txt += "{}: {} guess:{}\n".format(keyCode, pygKey, key.name)
        keyNames[keyCode]=pygKey
    msg.text = txt
    msg.draw()
    win.flip()
    if pygKey=='escape':
        break

print(keyNames)
#keyboard = 
#
#while True:
#    
