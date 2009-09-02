import numpy, pylab
from numpy import pi, cos

def radians(degs):
    return degs*pi/180.0

def makeMask(inVals, centre, platWidth, rampWidth):
    inVals = ((inVals-centre)+pi)%(2*pi) - pi#make 0 the centre of the 
    rampInner = platWidth/2.0
    rampOuter = platWidth/2.0+rampWidth
    
    mask=inVals.copy()
    mask[ abs(inVals)<rampInner ] = 1#this is the plateau
    mask[ abs(inVals)>rampOuter ] = 0#this is the base area
    rampUpIndices = (inVals<rampOuter)*(inVals>rampInner)
    rampDownIndices = (inVals>-rampOuter)*(inVals<-rampInner)
    mask[rampUpIndices] = numpy.cos((inVals[rampUpIndices]-rampInner)/rampWidth*pi/2)**2
    mask[rampDownIndices] = numpy.cos((inVals[rampDownIndices]+rampInner)/rampWidth*pi/2)**2
    
    return mask
   
masktheta = numpy.arange(0,2*pi, 0.01)
mask1 = makeMask(masktheta, centre=0.39, platWidth=1.48, rampWidth=0.17)
mask2 = makeMask(masktheta, centre=1.96, platWidth=1.48, rampWidth=0.17)
mask3 = makeMask(masktheta, centre=3.53, platWidth=1.48, rampWidth=0.17)
mask4 = makeMask(masktheta, centre=5.10, platWidth=1.48, rampWidth=0.17)

pylab.plot(masktheta, mask1, 'k-')
pylab.plot(masktheta, mask2, 'k-')
pylab.plot(masktheta, mask3, 'r-')
pylab.plot(masktheta, mask4, 'k-')
pylab.ylim([-0.1, 1.1])
pylab.xlim([-0.1,6.5])
pylab.show()
