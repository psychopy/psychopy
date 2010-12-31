from psychopy import visual
import os, nose

def testMovie():
    win = visual.Window([600,600])
    
    movFile = os.path.abspath('testMovie.mp4')
    nose.tools.assert_true(os.path.exists(movFile),
            msg = "File not found: %s" %(movFile))
            
    mov = visual.MovieStim(win, movFile)
    for frameN in range(10):
        mov.draw()
        win.flip()
    win.close()