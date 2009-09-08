import numpy, pylab
from numpy import pi, cos

def radians(degs):
    return degs*pi/180.0

def makeMask(inVals, centre, platWidth, rampWidth):
    inVals = ((inVals-centre)+180)%(360) - 180#make 180 the centre of the vals
    rampInner = platWidth/2.0
    rampOuter = platWidth/2.0+rampWidth
    
    mask=inVals.copy()
    mask[ abs(inVals)<=rampInner ] = 1#this is the plateau
    mask[ abs(inVals)>=rampOuter ] = 0#this is the base
    rampUpIndices = (inVals<rampOuter)*(inVals>rampInner)
    rampDownIndices = (inVals>-rampOuter)*(inVals<-rampInner)
    #for each ramp side, set the ramp values to run 0-90 and then take cos**2
    mask[rampUpIndices] = cos(radians((inVals[rampUpIndices]-rampInner)*90.0/rampWidth))**2
    mask[rampDownIndices] = cos(radians((inVals[rampDownIndices]+rampInner)*90.0/rampWidth))**2
    
    return mask
    
xVals = numpy.arange(360.0)
exp1=False
if exp1:
    for centre in [45,135,225,315]:
        mask = makeMask(xVals, centre, 80, 10)
        pylab.plot(xVals, mask, 'k-')
else:
    for centre in range(0,360,45):
        mask = makeMask(xVals, centre, 35, 10)
        pylab.plot(xVals, mask, 'k-')
    
pylab.ylim([-0.1, 1.1])
pylab.xlim([-1, 361])
pylab.show()
