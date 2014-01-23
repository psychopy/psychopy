#!/usr/bin/env python2
from psychopy import visual

#copy pixels from the frame buffer
myWin = visual.Window([200,200])
myStim = visual.PatchStim(myWin, pos=[-0.5,-0.5],
    size=1, sf=5,color=[0,1,1],ori=30, mask='gauss',
    autoLog=False)#this stim changes too much for autologging to be useful
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
myWin.saveMovieFrames('frame.png')
#myWin.saveMovieFrames('frame.tif') #much like png files (but used more on win32)
#myWin.saveMovieFrames('frame.jpg') #lossy, but highly compressed images
#myWin.saveMovieFrames('myMovie.gif')# for better results, make your gif in gimp
#myWin.saveMovieFrames('myMovie.mpg')#only on win32 so far (requires pymedia)

myWin.close()
