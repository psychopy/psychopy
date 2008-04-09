from psychopy import visual, event, makeMovies, misc
import numpy

nDots = 500
maxSpeed = 0.02
dotSize = .0075

dotsTheta=numpy.random.rand(nDots)*360
dotsRadius=(numpy.random.rand(nDots)**0.5)*2
speed=numpy.random.rand(nDots)*maxSpeed

win = visual.Window([800,600],rgb=-1)
dot = visual.PatchStim(win, rgb=1, tex=None, mask='circle', size=dotSize)

for frameN in range(400):
    
    #update radius
    dotsRadius = (dotsRadius+speed)
    #random radius where radius too large
    outFieldDots = (dotsRadius>=2.0)
    dotsRadius[outFieldDots] = numpy.random.rand(sum(outFieldDots))*2.0
    
    dotsX, dotsY = misc.pol2cart(dotsTheta,dotsRadius)
    dotsX *= 0.75 #to account for wider aspect ratio
    for dotN in range(nDots):
        dot.setPos( (dotsX[dotN], dotsY[dotN]) )
        dot.draw()
    
    win.update()
    win.getMovieFrame()
    
win.saveMovieFrames('starfield.mpg')    