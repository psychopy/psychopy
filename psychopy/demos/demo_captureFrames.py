from psychopy import visual

#copy pixels from the frame buffer
myWin = visual.Window([200,200])
myStim = visual.PatchStim(myWin, pos=[-0.5,-0.5],size=1, sf=5,rgb=[0,1,1],ori=30, mask='gauss')
n=10
for frameN in range(n): #for n frames
  myStim.setPhase(0.1, '+')
  myStim.draw()
  myWin.update()
  myWin.getMovieFrame()
#myWin.saveMovieFrames('frame.jpg')
#myWin.saveMovieFrames('myMovie.gif')
myWin.saveMovieFrames('myMovie.mpg')

myWin.close()
