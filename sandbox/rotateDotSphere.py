from psychopy import visual, misc
import numpy

nDots = 1000
angVelocity = 1 #deg rotation per frame

win = visual.Window((600,600))

#Ideally, we should subclass DotStim and override the _updateDots method to 
#what we want with the spherical rotation. But we'll just set speed and dotLife
#so that they won't update (?)
myStim = visual.DotStim(win, nDots=nDots,
    speed=0, fieldSize=[500,500], dotLife=-1)#this is a hack

#starting spherical coordinates for our dots
azims = numpy.random.random(nDots)*360
elevs = numpy.random.random(nDots)*180-90
radii = 0.5 

win.setRecordFrameIntervals()
for frameN in range(1000):
    
    azims += angVelocity #add angVel to the azimuth of the dots
    x,y,z = misc.sph2cart(elevs, azims, radii)
    
    myStim._dotsXY[:,0] = x
    myStim._dotsXY[:,1] = z #?!
    myStim._calcDotsXYRendered()
    myStim.draw()
    
    win.flip()
    
   
print win.fps()  
  