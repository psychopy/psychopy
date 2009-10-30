from psychopy import visual

def testMany():
    win = visual.Window([600,600])
    text = visual.TextStim(win, text='hello', pos=[-0.9, -0.9])
    gabor = visual.PatchStim(win, mask='gauss', pos=[0.9, -0.9])
    shape = visual.ShapeStim(win, lineRGB=[1, 1, 1], lineWidth=1.0, 
        fillRGB=[0.80000000000000004, 0.80000000000000004, 0.80000000000000004], 
        vertices=[[-0.5, 0],[0, 0.5],[0.5, 0]], 
        closeShape=True, pos=[0, 0], ori=0.0, opacity=1.0, depth=0, interpolate=True)
    mov = visual.MovieStim(win, 'testMovie.mp4')
    for frameN in range(10):
        shape.draw()
        text.draw()
        gabor.draw()
        mov.draw()
        win.flip()
    win.close()
   