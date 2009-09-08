import pyglet.window
import numpy, sys, time

#import platform specific C++ libs for controlling gamma
if sys.platform=='win32':
    from ctypes import windll 
elif sys.platform=='darwin':
    carbon = pyglet.lib.load_library(framework='/System/Library/Frameworks/Carbon.framework')
elif sys.platform=='linux':
    import xf86vmode #or is it in xlib?

class Window(pyglet.window.Window):
    def __init__(self):
        pyglet.window.Window.__init__(self)
    def setGamma(self, newGamma):
        #make sure gamma is 3x1 array
        if type(newGamma) in [float,int]:
            newGamma = numpy.tile(newGamma, [3,1])
        elif type(newGamma) is numpy.ndarray:
            newGamma.shape=[3,1]
        #combine with the linear ramp    
        ramp = numpy.tile(numpy.arange(256)/256.0,(3,1))# (3x256) array
        newLUT = ramp**(1/numpy.array(newGamma))# correctly handles 1 or 3x1 gamma vals
        self.setHardwareGammaRamp(newLUT)
        
    def setGammaRamp(self, newRamp):
        """Ramp should be provided as 3x256 array in range 0:1
        """
        if sys.platform=='win32':  
            newRamp= (255*newRamp).astype(numpy.uint16)
            newRamp.byteswap(True)#necessary, according to pyglet post from Martin Spacek
            success = windll.gdi32.SetDeviceGammaRamp(self._dc, newRamp.ctypes)
            if not success: raise AssertionError, 'SetDeviceGammaRamp failed'
            
        if sys.platform=='darwin':  
            newRamp= (newRamp).astype(numpy.float32)
            error =carbon.CGSetDisplayTransferByTable(self._screen.id, 256,
                       newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
            if error: raise AssertionError, 'CGSetDisplayTransferByTable failed'
            
        #if sys.platform=='linux':    
            #newRamp= (256*newRamp).astype(numpy.uint16)      
            #error = xf86vmode.XF86VidModeSetGammaRamp(display??, screenID??, 256,
                        #newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
            #if error: raise AssertionError, 'XF86VidModeSetGammaRamp failed'
            
    def getGammaRamp(self):     
        """Ramp will be returned as 3x256 array in range 0:1
        """
        if sys.platform=='win32':  
            origramps = numpy.empty((3, 256), dtype=numpy.uint16) # init R, G, and B ramps
            success = windll.gdi32.GetDeviceGammaRamp(self._dc, origramps.ctypes)
            if not success: raise AssertionError, 'SetDeviceGammaRamp failed'
            origramps.byteswap(True)
            origramps=origramps/255.0#rescale to 0:1
            
        if sys.platform=='darwin':          
            origramps = numpy.empty((3, 256), dtype=numpy.float32) # init R, G, and B ramps
            n = numpy.empty([1],dtype=numpy.int)
            error =carbon.CGGetDisplayTransferByTable(self._screen.id, 256,
                       origramps[0,:].ctypes, origramps[1,:].ctypes, origramps[2,:].ctypes, n.ctypes);
            if error: raise AssertionError, 'CGSetDisplayTransferByTable failed'

        #if sys.platform=='linux':           
            #error = xf86vmode.XF86VidModeGetGammaRamp(Xdisplay??, screenID??, 256,
                        #newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
            #if error: raise AssertionError, 'XF86VidModeSetGammaRamp failed'
            
        return origramps
    
myWin = Window()
orig = myWin.getHardwareGammaRamp()
myWin.setHardwareGamma(4.0)#will make things visibly brighter
time.sleep(2)
myWin.setHardwareGammaRamp(orig)
