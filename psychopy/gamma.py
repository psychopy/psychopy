#set the gamma LUT using platform-specific hardware calls
#this currently requires a pyglet window (to identify the current scr/display)

import numpy, sys, ctypes, ctypes.util

#import platform specific C++ libs for controlling gamma
if sys.platform=='win32':
    from ctypes import windll
elif sys.platform=='darwin':
    carbon = ctypes.CDLL('/System/Library/Carbon.framework/Carbon')
elif sys.platform.startswith('linux'):
    #we need XF86VidMode
    xf86vm=ctypes.CDLL(ctypes.util.find_library('Xxf86vm'))
    
def setGamma(pygletWindow=None, newGamma=1.0):
    #make sure gamma is 3x1 array
    if type(newGamma) in [float,int]:
        newGamma = numpy.tile(newGamma, [3,1])
    elif type(newGamma) in [list, tuple]:
        newGamma=numpy.array(newGamma)
        newGamma.shape=[3,1]
    elif type(newGamma) is numpy.ndarray:
        newGamma.shape=[3,1]
    #combine with the linear ramp    
    ramp = numpy.tile(numpy.arange(256, dtype=float)/255.0,(3,1))# (3x256) array
    newLUT = ramp**(1/numpy.array(newGamma))# correctly handles 1 or 3x1 gamma vals

    setGammaRamp(pygletWindow, newLUT)
    
def setGammaRamp(pygletWindow, newRamp):
    """Ramp should be provided as 3x256 array in range 0:1
    """
    if sys.platform=='win32':  
        newRamp= (255*newRamp).astype(numpy.uint16)
        newRamp.byteswap(True)#necessary, according to pyglet post from Martin Spacek
        success = windll.gdi32.SetDeviceGammaRamp(pygletWindow._dc, newRamp.ctypes)
        if not success: raise AssertionError, 'SetDeviceGammaRamp failed'
        
    if sys.platform=='darwin':  
        newRamp= (newRamp).astype(numpy.float32)
        error =carbon.CGSetDisplayTransferByTable(pygletWindow._screen.id, 256,
                   newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
        if error: raise AssertionError, 'CGSetDisplayTransferByTable failed'
        
    if sys.platform.startswith('linux'):
        newRamp= (65536*newRamp).astype(numpy.uint16)
        success = xf86vm.XF86VidModeSetGammaRamp(pygletWindow._x_display, pygletWindow._x_screen_id, 256,
                    newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
        if not success: raise AssertionError, 'XF86VidModeSetGammaRamp failed'
        
def getGammaRamp(pygletWindow):     
    """Ramp will be returned as 3x256 array in range 0:1
    """
    if sys.platform=='win32':  
        origramps = numpy.empty((3, 256), dtype=numpy.uint16) # init R, G, and B ramps
        success = windll.gdi32.GetDeviceGammaRamp(pygletWindow._dc, origramps.ctypes)
        if not success: raise AssertionError, 'SetDeviceGammaRamp failed'
        origramps.byteswap(True)
        origramps=origramps/255.0#rescale to 0:1
        
    if sys.platform=='darwin':          
        origramps = numpy.empty((3, 256), dtype=numpy.float32) # init R, G, and B ramps
        n = numpy.empty([1],dtype=numpy.int)
        error =carbon.CGGetDisplayTransferByTable(pygletWindow._screen.id, 256,
                   origramps[0,:].ctypes, origramps[1,:].ctypes, origramps[2,:].ctypes, n.ctypes);
        if error: raise AssertionError, 'CGSetDisplayTransferByTable failed'

    if sys.platform.startswith('linux'):
        origramps = numpy.empty((3, 256), dtype=numpy.uint16) 
        success = xf86vm.XF86VidModeGetGammaRamp(pygletWindow._x_display, pygletWindow._x_screen_id, 256,
                    origramps[0,:].ctypes, origramps[1,:].ctypes, origramps[2,:].ctypes)
        if not success: raise AssertionError, 'XF86VidModeGetGammaRamp failed'
        
    return origramps
