from psychopy import visual, core, event

win = visual.Window([800,600])

#mov = visual.MovieStim(win, 'testmovie.mpg', flipVert=True)
mov2 = visual.MovieStim(win, 'myMovie.mpg', flipVert=False)

for frameN in range (2000):
    #mov.draw()
    mov2.draw()
    win.update() 
    