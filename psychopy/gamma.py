#set the gamma LUT using platform-specific hardware calls
#this currently requires a pyglet window (to identify the current scr/display)

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy, sys, platform, ctypes, ctypes.util
import pyglet
from psychopy import logging
import os

#import platform specific C++ libs for controlling gamma
if sys.platform=='win32':
    from ctypes import windll
elif sys.platform=='darwin':
    carbon = ctypes.CDLL('/System/Library/Carbon.framework/Carbon')
elif sys.platform.startswith('linux'):
    #we need XF86VidMode
    xf86vm=ctypes.CDLL(ctypes.util.find_library('Xxf86vm'))

_TravisTesting = os.environ.get('TRAVIS')=='true' #in Travis-CI testing

def setGamma(pygletWindow=None, newGamma=1.0, rampType=None):
    #make sure gamma is 3x1 array
    if type(newGamma) in [float,int]:
        newGamma = numpy.tile(newGamma, [3,1])
    elif type(newGamma) in [list, tuple]:
        newGamma=numpy.array(newGamma)
        newGamma.shape=[3,1]
    elif type(newGamma) is numpy.ndarray:
        newGamma.shape=[3,1]
    #create LUT from gamma values
    newLUT = numpy.tile(createLinearRamp(pygletWindow, rampType), (3,1))#linear ramp
    if numpy.all(newGamma==1.0)==False:
        newLUT = newLUT**(1/numpy.array(newGamma))# correctly handles 1 or 3x1 gamma vals
    setGammaRamp(pygletWindow, newLUT)

def setGammaRamp(pygletWindow, newRamp, nAttempts=3):
    """Sets the hardware look-up table, using platform-specific ctypes functions.
    For use with pyglet windows only (pygame has its ow routines for this).
    Ramp should be provided as 3x256 or 3x1024 array in range 0:1.0

    On windows the first attempt to set the ramp doesn't always work. The parameter nAttemps
    allows the user to determine how many attempts should be made before failing
    """
    if newRamp.shape[0]!=3 and newRamp.shape[1]==3:
        newRamp= numpy.ascontiguousarray(newRamp.transpose())
    if sys.platform=='win32':
        newRamp= (255.0*newRamp).astype(numpy.uint16)
        newRamp.byteswap(True)#necessary, according to pyglet post from Martin Spacek
        for n in range(nAttempts):
            success = windll.gdi32.SetDeviceGammaRamp(0xFFFFFFFF & pygletWindow._dc, newRamp.ctypes) # FB 504
            if success:
                break
        assert success, 'SetDeviceGammaRamp failed'

    if sys.platform=='darwin':
        newRamp= (newRamp).astype(numpy.float32)
        LUTlength=newRamp.shape[1]
        error =carbon.CGSetDisplayTransferByTable(pygletWindow._screen.id, LUTlength,
                   newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
        assert not error, 'CGSetDisplayTransferByTable failed'

    if sys.platform.startswith('linux') and not _TravisTesting:
        newRamp= (65535*newRamp).astype(numpy.uint16)
        success = xf86vm.XF86VidModeSetGammaRamp(pygletWindow._x_display, pygletWindow._x_screen_id, 256,
                    newRamp[0,:].ctypes, newRamp[1,:].ctypes, newRamp[2,:].ctypes)
        assert success, 'XF86VidModeSetGammaRamp failed'

    elif _TravisTesting:
        logging.warn("It looks like we're running in the Travis-CI testing environment. Hardware gamma table cannot be set")

def getGammaRamp(pygletWindow):
    """Ramp will be returned as 3x256 array in range 0:1
    """
    if sys.platform=='win32':
        origramps = numpy.empty((3, 256), dtype=numpy.uint16) # init R, G, and B ramps
        success = windll.gdi32.GetDeviceGammaRamp(0xFFFFFFFF & pygletWindow._dc, origramps.ctypes) # FB 504
        if not success:
            raise AssertionError, 'GetDeviceGammaRamp failed'
        origramps=origramps/65535.0#rescale to 0:1

    if sys.platform=='darwin':
        origramps = numpy.empty((3, 256), dtype=numpy.float32) # init R, G, and B ramps
        n = numpy.empty([1],dtype=numpy.int)
        error =carbon.CGGetDisplayTransferByTable(pygletWindow._screen.id, 256,
                   origramps[0,:].ctypes, origramps[1,:].ctypes, origramps[2,:].ctypes, n.ctypes);
        if error:
            raise AssertionError, 'CGSetDisplayTransferByTable failed'

    if sys.platform.startswith('linux'):
        origramps = numpy.empty((3, 256), dtype=numpy.uint16)
        success = xf86vm.XF86VidModeGetGammaRamp(pygletWindow._x_display, pygletWindow._x_screen_id, 256,
                    origramps[0,:].ctypes, origramps[1,:].ctypes, origramps[2,:].ctypes)
        if not success:
            raise AssertionError, 'XF86VidModeGetGammaRamp failed'
        origramps=origramps/65535.0#rescale to 0:1

    return origramps

def createLinearRamp(win, rampType=None):
    """Generate the Nx3 values for a linear gamma ramp on the current platform.
    This uses heuristics about known graphics cards to guess the 'rampType' if
    none is exlicitly given.

    Much of this work is ported from LoadIdentityClut.m, written by Mario Kleiner
    for the psychtoolbox

    rampType 0 : an 8-bit CLUT ranging 0:1
        This is seems correct for most windows machines and older OS X systems
        Known to be used by:
            OSX 10.4.9 PPC with GeForceFX-5200

    rampType 1 : an 8-bit CLUT ranging (1/256.0):1
        For some reason a number of macs then had a CLUT that (erroneously?) started with 1/256 rather than 0
        Known to be used by:
            OSX 10.4.9 with ATI Mobility Radeon X1600
            OSX 10.5.8 with ATI Radeon HD-2600
            maybe all ATI cards?

    rampType 2 : a 10-bit CLUT ranging 0:(1023/1024)
        A slightly odd 10-bit CLUT that doesn't quite finish on 1.0!
        Known to be used by:
            OSX 10.5.8 with Geforce-9200M (MacMini)
            OSX 10.5.8 with Geforce-8800

    rampType 3 : a nasty, bug-fixing 10bit CLUT for crumby OS X drivers
        Craziest of them all for Snow leopard. Like rampType 2, except that the upper half of the table has 1/256.0 removed?!!
        Known to be used by:
            OSX 10.6.0 with NVidia Geforce-9200M
    """
    if rampType is None:
        #try to determine rampType from heuristics
        #get sys info
        driver = pyglet.gl.gl_info.get_renderer()
        if sys.platform=='darwin':
            isOSX=True
            osxVer=platform.mac_ver()[0]
        else:
            isOSX=False
            osxVer=None

        #try to deduce ramp type
        if isOSX:
            if 'NVIDIA' in driver:
                if ("10.5"<osxVer<"10.6"):#leopard nVidia cards don't finish at 1.0!
                    rampType=2
                if ("10.6"<osxVer):#snow leopard cards are plain crazy!
                    rampType=3
            else: #is ATI or unkown manufacturer, default to (1:256)/256
                #this is certainly correct for radeon2600 on 10.5.8 and radeonX1600 on 10.4.9
                rampType=1
        else:#for win32 and linux this is sensible, not clear about Vista and Windows7
            rampType=0

    if rampType==0:
        ramp = numpy.linspace(0.0, 1.0, num=256)
    elif rampType==1:
        ramp = numpy.linspace(1/256.0,1.0,num=256)
    elif rampType==2:
        ramp = numpy.linspace(0, 1023.0/1024,num=1024)
    elif rampType==3:
        ramp = numpy.linspace(0, 1023.0/1024,num=1024)
        ramp[512:] = ramp[512:]-1/256.0
    logging.info('Using gamma ramp type: %i' %rampType)
    return ramp


