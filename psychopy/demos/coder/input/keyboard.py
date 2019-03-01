from psychopy import visual, event, core
from psychopy.hardware import keyboard

print(keyboard.hid)
print("Keyboards:")
for kb in keyboard.getKeyboards():
    print(kb)
for n in range(256):
    if n not in keyboard.keyNames:
        print(n)
kb = keyboard.Keyboard()
print(kb._ids)
print(kb._devs)
win = visual.Window()
msg = visual.TextStim(win, 'press a key')
msg.draw()
win.flip()

continuing = True
while continuing:
    txt = ''
    pygKey = event.waitKeys()[0]
    # wait for the key to be raised
    keyEvents = kb.getKeys(includeDuration=False)
    for key in keyEvents:
        txt = "{}".format(key.name)

        if key.name == 'n/a':
            keyboard.keyNames[key.code] = pygKey
            txt = "setting {} to {}".format(key.code, pygKey)
            print(txt)

        if key == 'escape':
            continuing = False

    print(txt, repr(keyEvents))
    msg.text = txt
    #        if evt['down']:
    #            keyCode = evt['keycode']
    #            msg.text = "{}: {}".format(keyCode, pygKey)
    #            keyboard.keyNames[keyCode]=pygKey
    msg.draw()
    win.flip()
#    if pygKey=='escape':
#        break

print(keyboard.keyNames)
# keyboard =
#
# while True:
#
