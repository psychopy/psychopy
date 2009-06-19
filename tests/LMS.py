
import numpy
from numpy import linalg
from psychopy.misc import sph2cart
 
def dkl2rgb(dkl_Nx3, conversionMatrix=None):
    #Convert from DKL color space (cone-opponent space from Derrington,
    #Krauskopf & Lennie) to RGB. 

    #Requires a conversion matrix, which will be generated from generic
    #Sony Trinitron phosphors if not supplied (note that this will not be
    #an accurate representation of the color space unless you supply a 
    #conversion matrix
    #
    #usage:
        #rgb(Nx3) = dkl2rgb(dkl_Nx3(el,az,radius), conversionMatrix)
    
    dkl_3xN = numpy.transpose(dkl_Nx3)#its easier to use in the other orientation!
    if numpy.size(dkl_3xN)==3:
        RG, BY, LUM = sph2cart(dkl_3xN[0],dkl_3xN[1],dkl_3xN[2])
    else:
        RG, BY, LUM = sph2cart(dkl_3xN[0,:],dkl_3xN[1,:],dkl_3xN[2,:])
    dkl_cartesian = numpy.asarray([LUM, RG, BY])

    if conversionMatrix==None:
        conversionMatrix = numpy.asarray([ \
            #LUMIN	%L-M	%L+M-S  (note that dkl has to be in cartesian coords first!)
            [1.0000, 1.0000, -0.1462],	#R
            [1.0000, -0.3900, 0.2094],	#G
            [1.0000, 0.0180, -1.0000]])	#B
    
    #rgb = numpy.dot(dkl_cartesian,numpy.transpose(conversionMatrix))
    rgb = numpy.dot(conversionMatrix, dkl_cartesian)
    return numpy.transpose(rgb)#return in the shape we received it
"""    
def lms2rgb(lms_Nx3, conversionMatrix=None):
    #Convert from cone space (Long, Medium, Short) to RGB. 
    
    #Requires a conversion matrix, which will be generated from generic
    #Sony Trinitron phosphors if not supplied (note that this will not be
    #an accurate representation of the color space unless you supply a 
    #conversion matrix
    #
    #usage:
        #rgb(Nx3) = dkl2rgb(dkl_Nx3(el,az,radius), conversionMatrix)
    
    lms_3xN = numpy.transpose(lms_Nx3)#its easier to use in the other orientation!
        
    if conversionMatrix==None:
        cones_to_rgb = numpy.asarray([ \
            #L		M		S
            [1.0000,    -1.0000,    0.1462],#R
            [-0.1829,    0.5205,   -0.2094],#G
            [-0.0080,   -0.0344,    1.0000]])#B
    else: cones_to_rgb=conversionMatrix
    
    rgb_to_cones = linalg.pinv(cones_to_rgb)#get inverse
    whiteLMS = numpy.dot(rgb_to_cones, numpy.ones(3))
    cones_to_rgb[:,0]*=whiteLMS[0]
    cones_to_rgb[:,1]*=whiteLMS[1]
    cones_to_rgb[:,2]*=whiteLMS[2]
    print cones_to_rgb
    
##    scaledLMS = lms_3xN*whiteLMS
    
    #rgb = numpy.dot(dkl_cartesian,numpy.transpose(conversionMatrix))
##    rgb = numpy.dot(cones_to_rgb, scaledLMS)
    rgb = numpy.dot(cones_to_rgb, lms_3xN)
    return numpy.transpose(rgb)#return in the shape we received it
"""
from psychopy import *
lms2rgb = misc.lms2rgb
myWin = visual.Window((600,600), monitor='laptop')
gabs = []
#dkl cardinals
##gabs.append( visual.PatchStim(myWin, mask='gauss',dkl=(90,0,1), pos=[-0.5,0.5],sf=2) )#achrom
##gabs.append( visual.PatchStim(myWin, mask='gauss',dkl=(0,0,1), pos=[-0.5,0],sf=2))# L-M
##gabs.append( visual.PatchStim(myWin, mask='gauss',dkl=(0,90,0.9), pos=[0,-0.5],sf=2))# S
#lms using rgb
gabs.append( visual.PatchStim(myWin, mask='gauss',rgb=lms2rgb([0.2,0,0]), pos=[-0.5,0.5],sf=2) )#achrom
gabs.append( visual.PatchStim(myWin, mask='gauss',rgb=lms2rgb([0,0.2,0]), pos=[-0.5,0],sf=2))# L-M
gabs.append( visual.PatchStim(myWin, mask='gauss',rgb=lms2rgb([0,0,0.5]), pos=[-0.5,-0.5],sf=2))# L-M
gabs.append( visual.PatchStim(myWin, mask='gauss',dkl=(+8,+8,0.9), pos=[0,0.5],sf=2) )#L
gabs.append( visual.PatchStim(myWin, mask='gauss',dkl=(+4,+184,0.9), pos=[0,0],sf=2))# L-M
#~ gabs.append( visual.PatchStim(myWin, mask='gauss',dkl=(0,90,1), pos=[-0.5,-0.5],sf=2))# S
#~ gabs.append( visual.PatchStim(myWin, mask='gauss',lms=(0.2,0,0), pos=[0.5,0.5],sf=2))
#~ gabs.append( visual.PatchStim(myWin, mask='gauss',lms=(0,0.2,0), pos=[0.5,0],sf=2))
#~ gabs.append( visual.PatchStim(myWin, mask='gauss',lms=(0,0,0.5), pos=[0.5,-0.5],sf=2))
myClock = core.Clock()

while True:#myClock.getTime()<10:
    for thisGab in gabs:
        thisGab.draw()
    myWin.update()

    #handle key presses each frame
    for keys in event.getKeys():
        if keys in ['escape','q']:
            core.quit()
    event.clearEvents()