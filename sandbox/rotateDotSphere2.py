from psychopy import visual, misc
import numpy

nDots = 1000
angVelocity = 1 #deg rotation per frame

win = visual.Window((600,600))
myStim = visual.ElementArrayStim(win,  elementTex=None, elementMask='circle', texRes=64,
        nElements=nDots, sizes=0.01)

#starting spherical coordinates for our dots
azims = numpy.random.random(nDots)*360
elevs = numpy.random.random(nDots)*180-90
radii = 0.5 

for frameN in range(1000):
    
    azims += angVelocity #add angVel to the azimuth of the dots
    x,y,z = misc.sph2cart(elevs, azims, radii)
    
    xy = numpy.transpose(numpy.vstack([x,z]))
    myStim.setXYs(xy)
    myStim.draw()
    
    win.flip()
    
   
  
  