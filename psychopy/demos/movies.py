from psychopy import visual, core, event

win = visual.Window([800,600])

mov = visual.MovieStim(win, 'testmovie.mpg', flipVert=False)

for frameN in range (4000):
    mov.draw()
    win.update() 
    