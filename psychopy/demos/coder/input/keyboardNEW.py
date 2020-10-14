from psychopy import visual, event, core
from psychopy.hardware import keyboard


kb = keyboard.Keyboard()

win = visual.Window()
msg = visual.TextStim(win, 'Using WaitKeys()\n\nPress a key!', wrapWidth=1.5)
msg.setAutoDraw(True)
instruct = visual.TextStim(win, pos=(0,-0.8),
    text='Press Esc to move on (to test getKeys)', wrapWidth=1.5)
instruct.setAutoDraw(True)
win.flip()

timer = core.Clock()

continuing = True
while continuing:
    timer.reset()
    kb.clock.reset()
    
    pygKey = event.waitKeys()[0]
    pygRT = timer.getTime()
    core.wait(0.001)  # make sure event was processed by ptb too
    ptbKey = kb.getKeys(waitRelease=False)[0]
    
    txt = 'got key:\n\n'
    txt += ('waitKeys: {},\n    RT={}\n\n'
            .format(pygKey, pygRT))
    txt += ('new(PTB): {} ({})\n    RT={}\n\n'
            .format(ptbKey.name, ptbKey.code, ptbKey.rt))
    txt += ('new was {:.3f}ms faster'
            .format((pygRT-ptbKey.rt)*1000))
    msg.text = txt

    if pygKey == 'escape':
        continuing = False

    win.flip()

msg.text = 'Using getKeys (worse timing)\n\nPress a key!'
instruct.text='Press Esc to finish'
continuing = True
timer.reset()
kb.clock.reset()
while continuing:
    
    pygKey = event.getKeys()
    pygRT = timer.getTime()
    if pygKey:
        pygKey = pygKey[0] # key not a list of them
        core.wait(0.001)  # make sure event was processed by ptb too
        # wait for the key to be raised
        ptbKey = kb.getKeys(waitRelease=False)[0]
        
        txt = 'got key:\n\n'
        txt += ('waitKeys: {},\n    RT={}\n\n'
                .format(pygKey, pygRT))
        txt += ('new(PTB): {} ({})\n    RT={}\n\n'
                .format(ptbKey.name, ptbKey.code, ptbKey.rt))
        txt += ('new was {:.3f}ms faster'
                .format((pygRT-ptbKey.rt)*1000))
        msg.text = txt

        if pygKey == 'escape':
            continuing = False
        #after this key press reset for next one
        win.callOnFlip(timer.reset)
        win.callOnFlip(kb.clock.reset)

    win.flip()