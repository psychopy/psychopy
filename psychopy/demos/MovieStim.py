from psychopy import visual, core, event

win = visual.Window([800,600])
mov = visual.MovieStim(win, '47-APFB-2-RL.mov', size=[320,240],flipVert=False, flipHoriz=False)
print 'orig movie size=[%i,%i]' %(mov.format.width, mov.format.height)
print 'duration=%.2fs' %(mov.duration)
globalClock = core.Clock()

while globalClock.getTime()<(mov.duration+0.5):
    mov.draw()
    win.update()
    
core.quit()