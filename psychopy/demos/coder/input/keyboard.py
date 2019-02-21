from psychopy import visual, event, core
from psychopy.hardware import keyboard

print("Keyboards:")
for kb in keyboard.getKeyboards():
    print(kb)

kb = keyboard.Keyboard()
print(kb.evtBuffer._ids)
print(kb.evtBuffer._devs[0])
win = visual.Window()
msg = visual.TextStim(win, 'press a key')
msg.draw()
win.flip()

while True:
    txt = ''
    pygKey = event.waitKeys()[0]
    # wait for the key to be raised
    keyEvents = kb.getKeys(includeDuration=False)
    for key in keyEvents:
        txt += "{}: {}\n".format(key.name, pygKey)
    msg.text = txt
#        if evt['down']:
#            keyCode = evt['keycode']
#            msg.text = "{}: {}".format(keyCode, pygKey)
#            keyboard.keyNames[keyCode]=pygKey
    msg.draw()
    win.flip()
    if pygKey=='escape':
        break

print(keyboard.keyNames)
#keyboard = 
#
#while True:
#    