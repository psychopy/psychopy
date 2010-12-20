#copy pixels from the frame buffer
from psychopy import *

myWin = visual.Window([800,600])

myStim = visual.PatchStim(myWin, pos=[-0.5,-0.5],size=1, sf=9,rgb=[0,1,1],ori=30, mask='gauss')
for frameN in range(10):
  myStim.setPhase(0.2, '+')
  myStim.draw()
  myWin.update()
  myWin.getMovieFrame()
  
#myWin.saveMovieFrames('frame.jpg')
myWin.saveMovieFrames('myMovie.mpg',  mpgCodec='mpeg1video')