from psychopy import visual

def testMovie():
    win = visual.Window([600,600])
    mov = visual.MovieStim(win, 'testMovie.mp4')
    for frameN in range(10):
        mov.draw()
        win.flip()
    win.close()