from psychopy import visual, core, event

win = visual.Window([800,600])
mov = visual.MovieStim(win, 'testmovie.mpg', flipVert=False, flipHoriz=False)

for frameN in range (2000):
    mov.draw()
    win.update()
    
core.quit()