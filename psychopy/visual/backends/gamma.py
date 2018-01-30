#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# set the gamma LUT using platform-specific hardware calls
# this currently requires a pyglet window (to identify the current scr/display)

from __future__ import absolute_import, division, print_function

from builtins import map
from builtins import range
import numpy
import sys
import platform
import ctypes
import ctypes.util
import pyglet
from psychopy import logging
import os

# import platform specific C++ libs for controlling gamma
if sys.platform == 'win32':
    from ctypes import windll
elif sys.platform == 'darwin':
    try:
        carbon = ctypes.CDLL(
            '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    except OSError:
        try:
            carbon = ctypes.CDLL(
                '/System/Library/Frameworks/Carbon.framework/Carbon')
        except OSError:
            carbon = ctypes.CDLL('/System/Library/Carbon.framework/Carbon')
elif sys.platform.startswith('linux'):
    # we need XF86VidMode
    xf86vm = ctypes.CDLL(ctypes.util.find_library('Xxf86vm'))

_TravisTesting = os.environ.get('TRAVIS') == 'true'  # in Travis-CI testing


def setGamma(screenID=None, newGamma=1.0, rampType=None, xDisplay=None):
    # make sure gamma is 3x1 array
    if type(newGamma) in [float, int]:
        newGamma = numpy.tile(newGamma, [3, 1])
    elif type(newGamma) in [list, tuple]:
        newGamma = numpy.array(newGamma)
        newGamma.shape = [3, 1]
    elif type(newGamma) is numpy.ndarray:
        newGamma.shape = [3, 1]
    # create LUT from gamma values
    newLUT = numpy.tile(createLinearRamp(
        screenID, rampType, xDisplay), (3, 1))  # linear ramp
    if numpy.all(newGamma == 1.0) == False:
        # correctly handles 1 or 3x1 gamma vals
        newLUT = newLUT**(1.0/numpy.array(newGamma))
    setGammaRamp(screenID, newLUT, xDisplay=xDisplay)


def setGammaRamp(screenID, newRamp, nAttempts=3, xDisplay=None):
    """Sets the hardware look-up table, using platform-specific functions.
    For use with pyglet windows only (pygame has its own routines for this).
    Ramp should be provided as 3x256 or 3x1024 array in range 0:1.0

    On windows the first attempt to set the ramp doesn't always work. The
    parameter nAttemps allows the user to determine how many attempts should
    be made before failing
    """

    LUTlength = newRamp.shape[1]

    if newRamp.shape[0] != 3 and newRamp.shape[1] == 3:
        newRamp = numpy.ascontiguousarray(newRamp.transpose())
    if sys.platform == 'win32':
        newRamp = (255.0 * newRamp).astype(numpy.uint16)
        # necessary, according to pyglet post from Martin Spacek
        newRamp.byteswap(True)
        for n in range(nAttempts):
            success = windll.gdi32.SetDeviceGammaRamp(
                0xFFFFFFFF & screenID, newRamp.ctypes)  # FB 504
            if success:
                break
        assert success, 'SetDeviceGammaRamp failed'

    if sys.platform == 'darwin':
        newRamp = (newRamp).astype(numpy.float32)
        error = carbon.CGSetDisplayTransferByTable(
            screenID, LUTlength,
            newRamp[0, :].ctypes,
            newRamp[1, :].ctypes,
            newRamp[2, :].ctypes)
        assert not error, 'CGSetDisplayTransferByTable failed'

    if sys.platform.startswith('linux') and not _TravisTesting:
        newRamp = (65535 * newRamp).astype(numpy.uint16)
        success = xf86vm.XF86VidModeSetGammaRamp(
            xDisplay, screenID, LUTlength,
            newRamp[0, :].ctypes,
            newRamp[1, :].ctypes,
            newRamp[2, :].ctypes)
        assert success, 'XF86VidModeSetGammaRamp failed'

    elif _TravisTesting:
        logging.warn("It looks like we're running in the Travis-CI testing "
                     "environment. Hardware gamma table cannot be set")


def getGammaRamp(screenID, xDisplay=None):
    """Ramp will be returned as 3xN array in range 0:1
    """

    rampSize = getGammaRampSize(screenID, xDisplay=xDisplay)

    if sys.platform == 'win32':
        # init R, G, and B ramps
        origramps = numpy.empty((3, rampSize), dtype=numpy.uint16)
        success = windll.gdi32.GetDeviceGammaRamp(
            0xFFFFFFFF & screenID, origramps.ctypes)  # FB 504
        if not success:
            raise AssertionError('GetDeviceGammaRamp failed')
        origramps = origramps/65535.0  # rescale to 0:1

    if sys.platform == 'darwin':
        # init R, G, and B ramps
        origramps = numpy.empty((3, rampSize), dtype=numpy.float32)
        n = numpy.empty([1], dtype=numpy.int)
        error = carbon.CGGetDisplayTransferByTable(
            screenID, rampSize,
            origramps[0, :].ctypes,
            origramps[1, :].ctypes,
            origramps[2, :].ctypes, n.ctypes)
        if error:
            raise AssertionError('CGSetDisplayTransferByTable failed')

    if sys.platform.startswith('linux') and not _TravisTesting:
        origramps = numpy.empty((3, rampSize), dtype=numpy.uint16)
        success = xf86vm.XF86VidModeGetGammaRamp(
            xDisplay, screenID, rampSize,
            origramps[0, :].ctypes,
            origramps[1, :].ctypes,
            origramps[2, :].ctypes)
        if not success:
            raise AssertionError('XF86VidModeGetGammaRamp failed')
        origramps = origramps/65535.0  # rescale to 0:1

    elif _TravisTesting:
        logging.warn("It looks like we're running in the Travis-CI testing "
                     "environment. Hardware gamma table cannot be retrieved")
        origramps = None

    return origramps


def createLinearRamp(screenID, rampType=None, xDisplay=None):
    """Generate the Nx3 values for a linear gamma ramp on the current platform.
    This uses heuristics about known graphics cards to guess the 'rampType' if
    none is explicitly given.

    Much of this work is ported from LoadIdentityClut.m, by Mario Kleiner
    for the psychtoolbox

    rampType 0 : an 8-bit CLUT ranging 0:1
        This is seems correct for most windows machines and older macOS systems
        Known to be used by:
            OSX 10.4.9 PPC with GeForceFX-5200

    rampType 1 : an 8-bit CLUT ranging (1/256.0):1
        For some reason a number of macs then had a CLUT that (erroneously?)
        started with 1/256 rather than 0. Known to be used by:
            OSX 10.4.9 with ATI Mobility Radeon X1600
            OSX 10.5.8 with ATI Radeon HD-2600
            maybe all ATI cards?

    rampType 2 : a 10-bit CLUT ranging 0:(1023/1024)
        A slightly odd 10-bit CLUT that doesn't quite finish on 1.0!
        Known to be used by:
            OSX 10.5.8 with Geforce-9200M (MacMini)
            OSX 10.5.8 with Geforce-8800

    rampType 3 : a nasty, bug-fixing 10bit CLUT for crumby macOS drivers
        Craziest of them all for Snow leopard. Like rampType 2, except that
        the upper half of the table has 1/256.0 removed?!!
        Known to be used by:
            OSX 10.6.0 with NVidia Geforce-9200M
    """
    def _versionTuple(v):
        # for proper sorting: _versionTuple('10.8') < _versionTuple('10.10')
        return tuple(map(int, v.split('.')))
    if rampType is None:
        # try to determine rampType from heuristics including sys info
        driver = pyglet.gl.gl_info.get_renderer()
        osxVer = platform.mac_ver()[0]  # '' on non-Mac

        # try to deduce ramp type
        if osxVer:
            osxVerTuple = _versionTuple(osxVer)
            if 'NVIDIA' in driver:
                # leopard nVidia cards don't finish at 1.0!
                if _versionTuple("10.5") < osxVerTuple < _versionTuple("10.6"):
                    rampType = 2
                # snow leopard cards are plain crazy!
                elif _versionTuple("10.6") < osxVerTuple:
                    rampType = 3
                else:
                    rampType = 1
            else:  # is ATI or unkown manufacturer, default to (1:256)/256
                # this is certainly correct for radeon2600 on 10.5.8 and
                # radeonX1600 on 10.4.9
                rampType = 1
        else:  # for win32 and linux this is sensible, not clear about Vista and Windows7
            rampType = 0

    rampSize = getGammaRampSize(screenID, xDisplay)

    if rampType == 0:
        ramp = numpy.linspace(0.0, 1.0, num=rampSize)
    elif rampType == 1:
        assert rampSize == 256
        ramp = numpy.linspace(1/256.0, 1.0, num=256)
    elif rampType == 2:
        assert rampSize == 1024
        ramp = numpy.linspace(0, 1023.0/1024, num=1024)
    elif rampType == 3:
        assert rampSize == 1024
        ramp = numpy.linspace(0, 1023.0/1024, num=1024)
        ramp[512:] = ramp[512:] - 1/256.0
    logging.info('Using gamma ramp type: %i' % rampType)
    return ramp


def getGammaRampSize(screenID, xDisplay=None):
    """Returns the size of each channel of the gamma ramp."""

    if sys.platform == 'win32':

        # windows documentation (for SetDeviceGammaRamp) seems to indicate that
        # the LUT size is always 256
        rampSize = 256

    elif sys.platform == 'darwin':

        rampSize = carbon.CGDisplayGammaTableCapacity(screenID)

    elif sys.platform.startswith('linux') and not _TravisTesting:

        rampSize = ctypes.c_int()

        success = xf86vm.XF86VidModeGetGammaRampSize(
            xDisplay,
            screenID,
            ctypes.byref(rampSize)
        )

        assert success, 'XF86VidModeGetGammaRampSize failed'

        rampSize = rampSize.value

    else:

        assert _TravisTesting

        rampSize = 256

    if rampSize == 0:
        raise RuntimeError("Gamma ramp size is reported as 0.")

    return rampSize
