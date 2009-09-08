from psychopy import visual, misc
import numpy

nDots = 1000
angVelocity = 1 #deg rotation per frame

win = visual.Window((600,600))

class SphereDotStim(visual.DotStim):
    def _update_dotsXY(self):
        #override this so that the dots dont get updated 
        #(which they normally do during draw() for RDKs)
        pass
        
myStim = SphereDotStim(win, nDots=nDots)#most parameters aren't going to be used here

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
  