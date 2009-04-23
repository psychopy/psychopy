#! /usr/local/bin/python2.5
from psychopy import visual

#copy pixels from the frame buffer
myWin = visual.Window([200,200])
myStim = visual.PatchStim(myWin, pos=[-0.5,-0.5],size=1, sf=5,rgb=[0,1,1],ori=30, mask='gauss')
n=10
for frameN in range(n): #for n frames
  myStim.setPhase(0.1, '+')
  myStim.draw()
  #you can either read from the back buffer BEFORE win.flip() or 
  #from the front buffer just AFTER the flip. The former has the
  #advantage that it won't be affected by other windows whereas
  #latter can be.
  myWin.getMovieFrame(buffer='back')
  myWin.flip()
#save the movie in the format of your choice
myWin.saveMovieFrames('frame.jpg')
#myWin.saveMovieFrames('myMovie.gif')
#myWin.saveMovieFrames('myMovie.mpg')

myWin.close()
