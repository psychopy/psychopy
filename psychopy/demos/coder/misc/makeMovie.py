from psychopy import visual, core, prefs
from pathlib import Path
from math import sin, pi, cos

win = visual.Window(size=(128,128), units='pix')

resourcesFolder = Path(prefs.paths['resources'])
psychopyIcon = resourcesFolder / "psychopy.png"
img = visual.ImageStim(win, psychopyIcon)
img.autoDraw = True

# grow and spin
for frameN in range(200):
    if frameN < 50:
        h = frameN*2
    img.size = (cos(frameN/50*pi)*h, h)
    win.flip()
    win.getMovieFrame()

# fade to grey
for frameN in range(5):
    img.contrast -= 0.2
    win.flip()
    win.getMovieFrame()
    
win.saveMovieFrames('myMov.mp4', fps=30, codec='libx264', clearFrames=False)
#win.saveMovieFrames('myMov.png')
#win.saveMovieFrames('myMov.gif')