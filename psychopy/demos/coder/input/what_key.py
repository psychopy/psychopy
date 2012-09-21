
from psychopy import visual, event

win = visual.Window([400,400])
msg = visual.TextStim(win, text='press a key\n<esc> to quit')
msg.draw()
win.flip()

k = ['']
count = 0
while k[0] not in ['escape', 'esc'] and count < 5:
    k = event.waitKeys()
    print k
    count += 1
