#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Acknowledgements:
#    This code was initially written by Jon Peirce.
#    with substantial additions by Andrew Schofield
#    CRS Ltd provided support as needed.
#    Shader code for mono++ and color++ modes was based on code in Psychtoolbox
#    (Kleiner) but does not actually use that code directly

import os
import sys
import time
import glob
import weakref
import serial
import numpy as np
from copy import copy, deepcopy
from time import sleep
import time

# Python 3.8 removed time.clock()
if sys.version_info < (3, 8):
    clock = time.clock
else:
    clock = time.perf_counter

from . import shaders
from psychopy import logging, core
from .. import serialdevice
import threading
try:
    import Queue
except Exception:
    import queue as Queue


__docformat__ = "restructuredtext en"

DEBUG = True

plotResults = False
if plotResults:
    from matplotlib import pyplot

try:
    from psychopy.ext import _bits
    haveBitsDLL = True
except Exception:
    haveBitsDLL = False

if DEBUG:  # we don't want error skipping in debug mode!
    from . import shaders
    haveShaders = True
else:
    try:
        from . import shaders
        haveShaders = True
    except Exception:
        haveShaders = False

try:
    import configparser
except Exception:
    import ConfigParser as configparser

# Bits++ modes
bits8BITPALETTEMODE = 0x00000001  # /* normal vsg mode */
NOGAMMACORRECT = 0x00004000  # /* Gamma correction mode */
GAMMACORRECT = 0x00008000  # /* Gamma correction mode */
VIDEOENCODEDCOMMS = 0x00080000  # must set so that LUT is read from screen


class button(dict):
    """clever dict like object or object like dict 
    for button presses
    """

    def __init__(self, direction='None', button=0, t=0):
        self['dir']=direction
        self['button']=button
        self['time']=t

    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError as k: 
            return None
        
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k: 
            raise AttributeError(k)
    
    def __repr__(self):     
        return '<button ' + dict.__repr__(self) + '>'
    
    def __getstate__(self): 
        return dict(self)
    
    def __setstate__(self,value):
        for k,v in value.items(): self[k]=v

class status(dict):
    """clever dict like object or object like dict
    for Bits# status messages
    """
    def __init__(self, sample=0, 
                         t=0, 
                         trigIn=0, 
                         bitsvals=0, 
                         IR=0, 
                         ADCs=0.0):
        self['sample']=sample
        self['time']=t
        self['trigIn']=trigIn
        self['DIN']=[bitsvals]*10
        self['DWORD']=bitsvals
        self['IR']=[IR]*6
        self['ADC']=[ADCs]*6 
 

    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError as k: 
            return None
        
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k: 
            raise AttributeError(k)
    
    def __repr__(self):     
        return '<sample ' + dict.__repr__(self) + '>'
    
    def __getstate__(self): 
        return dict(self)
    
    def __setstate__(self,value):
        for k,v in value.items(): self[k]=v
        
class event(dict):
    """clever dict like object or object like dict 
    for Bits# status events
    """
    def __init__(self, source='None', 
                         t=0, 
                         input=0, 
                         direction='None'):
        self['dir']=direction
        self['source']=source
        self['time']=t
        self['input']=input
 

    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError as k: 
            return None
        
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k: 
            raise AttributeError(k)
    
    def __repr__(self):     
        return '<event ' + dict.__repr__(self) + '>'
    
    def __getstate__(self): 
        return dict(self)
    
    def __setstate__(self,value):
        for k,v in value.items(): self[k]=v
        
class touch(dict):
    """clever dict like object or object like dict 
    for touch screen presses
    """
    def __init__(self, t=0, x=0, y=0, direction='down'):
        self['time']=t
        self['x']=x
        self['y']=y
        self['dir']=direction

    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError as k: 
            return None
        
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k: 
            raise AttributeError(k)
    
    def __repr__(self):     
        return '<touch ' + dict.__repr__(self) + '>'
    
    def __getstate__(self): 
        return dict(self)
    
    def __setstate__(self,value):
        for k,v in value.items(): self[k]=v


class BitsPlusPlus:
    """The main class to control a Bits++ box.
    This is usually a class added within the window object and is
    typically accessed from there. e.g.::

        from psychopy import visual
        from psychopy.hardware import crs
        win = visual.Window([800,600])
        bits = crs.BitsPlusPlus(win, mode='bits++')
        # use bits++ to reduce the whole screen contrast by 50%:
        bits.setContrast(0.5)
    """

    def __init__(self,
                 win,
                 contrast=1.0,
                 gamma=None,
                 nEntries=256,
                 mode='bits++',
                 rampType='configFile',
                 frameRate=None):
        """
        Parameters
        -----------

        contrast :
            The contrast to be applied to the LUT.
            See :func:`BitsPlusPlus.setLUT` and
            :func:`BitsPlusPlus.setContrast` for flexibility on setting
            just a section of the LUT to a different value
        gamma :
            The value used to correct the gamma in the LUT
        nEntries : 256
            [DEPRECATED feature]
        mode : 'bits++' (or 'mono++' or 'color++')
            Note that, unlike the Bits#, this only affects the way the
            window is rendered, it does not switch the state of the Bits++
            device itself (because unlike the Bits# have no way to
            communicate with it).
            The mono++ and color++ are only supported in PsychoPy 1.82.00
            onwards. Even then they suffer from not having gamma
            correction applied on Bits++ (unlike Bits# which can apply
            a gamma table in the device hardware).
        rampType : 'configFile', None or an integer
            if 'configFile' then we'll look for a valid config in the
            userPrefs folder if an integer then this will be used during
            win.setGamma(rampType=rampType):
        frameRate : an estimate the frameRate of the monitor. If None frame rate
            will be calculated.

        """
        self.win = win
        self.contrast = contrast
        self.nEntries = nEntries
        self.mode = mode
        # Frame rate isused to calculate trigger packets but for some reason
        # Bits++ needs it to be faked
        if frameRate == None:
            frameRate = self.win.getActualFrameRate()
        self.frameRate=frameRate*0.9
        # used to allow setting via USB which was 'slow':
        self.method = 'fast'
        # Bits++ doesn't do its own correction so we need to:
        self.gammaCorrect = 'software'

        # import pyglet.GL late so that we can import bits.py without it
        # initially
        global GL, visual
        from psychopy import visual
        import pyglet.gl as GL

        if self.gammaCorrect == 'software':
            if gamma is None:
                # inherit from window:
                self.gamma = win.gamma
            elif len(gamma) > 2:
                # [Lum,R,G,B] or [R,G,B]
                self.gamma = gamma[-3:]
            else:
                self.gamma = [gamma, gamma, gamma]
        if init():
            setVideoMode(NOGAMMACORRECT | VIDEOENCODEDCOMMS)
            self.initialised = True
            logging.debug('Found and initialised Bits++')
        else:
            self.initialised = False
            logging.warning("Couldn't initialise Bits++")

        # do the processing
        
        self._setHeaders(self.frameRate)

        self.setLUT()  # this will set self.LUT and update self._LUTandHEAD
        self._setupShaders()

        # replace window methods with our custom ones
        self.win._prepareFBOrender = self._prepareFBOrender
        self.win._finishFBOrender = self._finishFBOrender
        self.win._afterFBOrender = self._afterFBOrender
        # set gamma of the window to the identity LUT
        if rampType == 'configFile':
            # now check that we have a valid configuration of the box
            self.config = Config(self)
            # check we matche the prev config for our graphics card etc
            ok = False  # until we find otherwise
            ok = self.config.quickCheck()
            if ok:
                self.win.gammaRamp = self.config.identityLUT
            else:
                rampType = None
        if not rampType == 'configFile':
            # 'this must NOT be an `else` from the above `if` because can be
            # overridden possibly we were given a numerical rampType (as in
            # the :func:`psychopy.gamma.setGamma()`)
            self.win.winHandle.setGamma(self.win.winHandle._dc, rampType=rampType)
          
    #==================================#
    # Helper function for __init__     #
    #==================================#
    
    def _setHeaders(self, frameRate):
        """ Sets up the TLock header codes and some flags that are
            common to operating all CRS devices
        """
        # TLock for setting LUTs in the CRS device
        self._HEADandLUT = np.zeros((524, 1, 3), np.uint8)
        # R
        valsR = (36, 63, 8, 211, 3, 112, 56, 34, 0, 0, 0, 0)
        self._HEADandLUT[:12, :, 0] = np.asarray(valsR).reshape([12, 1])
        # G
        valsG = (106, 136, 19, 25, 115, 68, 41, 159, 0, 0, 0, 0)
        self._HEADandLUT[:12, :, 1] = np.asarray(valsG).reshape([12, 1])
        # B
        valsB = (133, 163, 138, 46, 164, 9, 49, 208, 0, 0, 0, 0)
        self._HEADandLUT[:12, :, 2] = np.asarray(valsB).reshape([12, 1])
        self.LUT = np.zeros((256, 3), 'd')  # just a place holder

        #TLock Header for everything else
        self._NumberPackets = int(round(1+10000/frameRate,0))

        # R:
        TLockR = (69, 40, 19, 119, 52, 233, 41, 183, 
                    0, 1, 0, 2, 0, 3, 0, 6, 0, 7, 0)        
        # G:
        TLockG = (33, 230, 190, 84, 12, 108,201, 124, 
                    0, 0, 0, 0, 0, 0, 0, 0, 0, 255, 0)
        # B:
        TLockB = (56, 208, 102, 207, 192, 172,80, 221, 
                    self._NumberPackets-1, 0, 0, 0, 0, 0, 0, 2, 0, 255, 0)

        # The following is used to reset the Bits# clock
        self._HEADandClock = np.zeros(((self._NumberPackets*2)+19,1,3),
                                            np.uint8)
        self._HEADandClock[:19,:,0] = np.asarray(TLockR).reshape([19,1])#R
        self._HEADandClock[:19,:,1] = np.asarray(TLockG).reshape([19,1])#G
        self._HEADandClock[:19,:,2] = np.asarray(TLockB).reshape([19,1])#B
        self._HEADandClock[15,:,1] = 12 # Pixel 15 green = 12 to reset clock.
        
        self._HEADandClockstr = self._HEADandClock.tostring()
            
        # The following are used to send triggers and control FE1 goggles
        # via the digital output  lines.
        self._HEADandTrig = np.zeros(((self._NumberPackets*2)+19,1,3),
                                        np.uint8)
        self._HEADandGogLeftOpen = np.zeros(((self._NumberPackets*2)+19,1,3),
                                                np.uint8)
        self._HEADandGogRightOpen = np.zeros(((self._NumberPackets*2)+19,1,3),
                                                np.uint8)
        self._HEADandGogBothOpen = np.zeros(((self._NumberPackets*2)+19,1,3),
                                                np.uint8)
        self._HEADandGogBothClosed = np.zeros(((self._NumberPackets*2)+19,1,3)
                                        , np.uint8)
        self._HEADandTrig[:19,:,0] = np.asarray(TLockR).reshape([19,1])#R
        self._HEADandTrig[:19,:,1] = np.asarray(TLockG).reshape([19,1])#G
        self._HEADandTrig[:19,:,2] = np.asarray(TLockB).reshape([19,1])#B

        self._HEADandGogLeftOpen[:19,:,0] = (
                                        np.asarray(TLockR).reshape([19,1]))
        self._HEADandGogLeftOpen[:19,:,1] = (
                                        np.asarray(TLockG).reshape([19,1]))
        self._HEADandGogLeftOpen[:19,:,2] = (
                                        np.asarray(TLockB).reshape([19,1]))
        self._HEADandGogRightOpen[:19,:,0] = (
                                        np.asarray(TLockR).reshape([19,1]))
        self._HEADandGogRightOpen[:19,:,1] = (
                                        np.asarray(TLockG).reshape([19,1]))
        self._HEADandGogRightOpen[:19,:,2] = (
                                        np.asarray(TLockB).reshape([19,1]))
        self._HEADandGogBothOpen[:19,:,0] = (
                                        np.asarray(TLockR).reshape([19,1]))
        self._HEADandGogBothOpen[:19,:,1] = (
                                        np.asarray(TLockG).reshape([19,1]))
        self._HEADandGogBothOpen[:19,:,2] = (
                                        np.asarray(TLockB).reshape([19,1]))
        self._HEADandGogBothClosed[:19,:,0] = (
                                        np.asarray(TLockR).reshape([19,1]))
        self._HEADandGogBothClosed[:19,:,1] = (
                                        np.asarray(TLockG).reshape([19,1]))
        self._HEADandGogBothClosed[:19,:,2] = (
                                        np.asarray(TLockB).reshape([19,1]))

        
        # flags for controlling triggers, goggles and analog outputs
        self.trigger=False
        self.clockReset=False
        self.clockReset=False
        self.gogglesGo=False
        self.gogglesLeft = 0
        self.gogglesRight = 1
        # Set up some blank triggers
        self.setTrigger()
        self.triggerProtected = False

    #==========================================#
    # Lut Functions                            #
    #==========================================#

    def setLUT(self, newLUT=None, gammaCorrect=True, LUTrange=1.0):
        """Sets the LUT to a specific range of values in 'bits++' mode only
        Note that, if you leave gammaCorrect=True then any LUT values you
        supply will automatically be gamma corrected.
        The LUT will take effect on the next `Window.flip()`

        **Examples**:

            - `bitsBox.setLUT()` to build a LUT using bitsBox.contrast and bitsBox.gamma
            - `bitsBox.setLUT(newLUT=some256x1array)` (NB array should be float 0.0:1.0)
              Builds a luminance LUT using newLUT for each gun
              (actually array can be 256x1 or 1x256)
            - `bitsBox.setLUT(newLUT=some256x3array)`
              (NB array should be float 0.0:1.0)
              Allows you to use a different LUT on each gun

        (NB by using BitsBox.setContr() and BitsBox.setGamma() users may not
        need this function)
        """

        # choose endpoints
        LUTrange = np.asarray(LUTrange)
        if LUTrange.size == 1:
            startII = int(round((0.5 - LUTrange/2.0) * 255.0))
            # +1 because python ranges exclude last value:
            endII = int(round((0.5 + LUTrange/2.0) * 255.0)) + 1
        elif LUTrange.size == 2:
            multiplier = 1.0
            if LUTrange[1] <= 1:
                multiplier = 255.0
            startII = int(round(LUTrange[0] * multiplier))
            # +1 because python ranges exclude last value:
            endII = int(round(LUTrange[1] * multiplier)) + 1
        stepLength = 2.0/(endII - startII - 1)

        if newLUT is None:
            # create a LUT from scratch (based on contrast and gamma)
            # rampStep = 2.0/(self.nEntries-1)
            ramp = np.arange(-1.0, 1.0 + stepLength, stepLength)
            ramp = (ramp * self.contrast + 1.0)/2.0
            # self.LUT will be stored as 0.0:1.0 (gamma-corrected)
            self.LUT[startII:endII, 0] = copy(ramp)
            self.LUT[startII:endII, 1] = copy(ramp)
            self.LUT[startII:endII, 2] = copy(ramp)
        elif type(newLUT) in [float, int] or (newLUT.shape == ()):
            self.LUT[startII:endII, 0] = newLUT
            self.LUT[startII:endII, 1] = newLUT
            self.LUT[startII:endII, 2] = newLUT
        elif len(newLUT.shape) == 1:
            # one dimensional LUT
            # replicate LUT to other channels, check range is 0:1
            if newLUT > 1.0:
                logging.warning('newLUT should be float in range 0.0:1.0')
            self.LUT[startII:endII, 0] = copy(newLUT.flat)
            self.LUT[startII:endII, 1] = copy(newLUT.flat)
            self.LUT[startII:endII, 2] = copy(newLUT.flat)

        elif len(newLUT.shape) == 2:
            # one dimensional LUT
            # use LUT as is, check range is 0:1
            if max(max(newLUT)) > 1.0:
                raise AttributeError('newLUT should be float in range 0.0:1.0')
            self.LUT[startII:endII, :] = newLUT

        else:
            logging.warning('newLUT can be None, nx1 or nx3')

        # do gamma correction if necessary
        if self.gammaCorrect == 'software':
            gamma = self.gamma

            try:
                lin = self.win.monitor.linearizeLums
                self.LUT[startII:endII, :] = lin(self.LUT[startII:endII, :],
                                                 overrideGamma=gamma)
            except AttributeError:
                try:
                    lin = self.win.monitor.lineariseLums
                    self.LUT[startII:endII, :] = lin(self.LUT[startII:endII, :],
                                                     overrideGamma=gamma)
                except AttributeError:
                    pass

        # update the bits++ box with new LUT
        # get bits into correct order, shape and add to header
        # go from ubyte to uint16
        ramp16 = (self.LUT * (2**16 - 1)).astype(np.uint16)
        ramp16 = np.reshape(ramp16, (256, 1, 3))
        # set most significant bits
        self._HEADandLUT[12::2, :, :] = (ramp16[:, :, :] >> 8).astype(np.uint8)
        # set least significant bits
        self._HEADandLUT[13::2, :, :] = (
            ramp16[:, :, :] & 255).astype(np.uint8)
        self._HEADandLUTstr = self._HEADandLUT.tostring()

    def setContrast(self, contrast, LUTrange=1.0, gammaCorrect=None):
        """Set the contrast of the LUT for 'bits++' mode only
        :Parameters:

            contrast : float in the range 0:1
                The contrast for the range being set

            LUTrange : float or array
                If a float is given then this is the fraction of the LUT
                to be used. If an array of floats is given, these will
                specify the start / stop points as fractions of the LUT.
                If an array of ints (0-255) is given these determine the
                start stop *indices* of the LUT

        Examples:
            - `setContrast(1.0,0.5)` to set the central 50% of the LUT so that a stimulus with
                contr=0.5 will actually be drawn with contrast 1.0
            - `setContrast(1.0,[0.25,0.5])`
            - or `setContrast(1.0,[63,127])` to set the lower-middle quarter of the LUT
                (which might be useful in LUT animation paradigms)
        """
        self.contrast = contrast
        if gammaCorrect is None:
            if gammaCorrect not in [False, "hardware"]:
                gammaCorrect = False
            else:
                gammaCorrect = True
        # setLUT uses contrast automatically
        self.setLUT(newLUT=None, gammaCorrect=gammaCorrect, LUTrange=LUTrange)

    def setGamma(self, newGamma):
        """Set the LUT to have the requested gamma value
        Currently also resets the LUT to be a linear contrast
        ramp spanning its full range. May change this to read
        the current LUT, undo previous gamma and then apply
        new one?"""
        self.gamma = newGamma
        self.setLUT()  # easiest way to update

    #=================================================#
    # Bits Clock Functions                            #
    #=================================================#

    def resetClock(self):
        """Issues a clock reset code using 1 screen flip
        if the next frame(s) is dropped the reset will be 
        re-issued thus keeping timing good.
        
        Resets continue to be issued on each video frame until
        the next win.flip so you need to have regular win.flips for
        this function to work properly.
        
        Example:
            bits.resetClock()
            drawImage()
            bits.win.flip()
            
            
        Will issue clock resets while the image is being drawn then
        display the image and allow the clock to continue from the
        same frame.
        
        Example:
            bits.resetClock()
            bits.RTBoxWait()
            bits.win.flip()
            
        Will issue clock resets until a button is pressed.
        
        """
        self.clockReset=True
        self.win.flip() # Send reset signal this frame, reset will happen next frame. 
                         # If next winflip is late the reset flag should latch thus 
                         # resetting clock until the next winflip


    def primeClock(self):
        """Primes the clock to reset at the next screen 
        flip - note only 1 clock reset signal will be issued
        but if the frame(s) after the reset frame is 
        dropped the reset will be re-issued thus keeping timing good.
        
        Resets continute to be issued on each video frame until
        the next win.flip so you need to have regular win.flips for
        this function to work properly.
        
        Example::

            bits.primeClock()
            drawImage
            while not response
                #do some processing
                bits.win.flip()
        
        Will get a clock reset signal ready but won't issue it until the first win.flip in the loop.
        
        """
        self.clockReset=True
    
    def syncClocks(self,t):
        """Synchronise the Bits/RTBox Clock with the host clock 
        Given by t.
        """
        self.clockReset=True
        self.win.flip()
        self.clockReset=False
        self.win.flip()
        t.reset()

    #=================================================#
    # Bits Trigger and Stereo Goggle Functions        #
    #=================================================#

    def getPackets(self):
        """Returns the number of packets available for trigger pulses.
        """
        return self._NumberPackets

    def setTrigger(self, triggers=0, onTime=0, 
                   duration=0, mask=0xFFFF):
        """ Quick way to set up triggers.
            
            Triggers is a binary word that determines which 
            triggers will be turned on.
            
            onTime specifies the start time of the trigger within
            the frame (in S with 100uS resolution)
            
            Duration specifies how long the trigger will last.
            (in S with 100uS resolution).
            
            Note that mask only protects the digital output lines
            set by other activities in the Bits. Not other triggers.
            
            Example::
                bits.setTrigger(0b0000000010, 2.0, 4.0, 0b0111111111)
                bits.startTrigger()


            Will issue a 4ms long high-going pulse, 2ms after the start 
            of each frame on DOUT1 while protecting the value of DOUT 9.
        """
        # Convert on time and duration into device units.
        sOnTime = int(round(onTime*10000.0, 0))
        sDuration = int(round(duration*10000.0, 0))
        # preallocate an empty data packet
        packet = [0]*self._NumberPackets
        # Set some elements of the packet equal to the desired trigger pattern.
        for index in range(sOnTime, int(sOnTime + sDuration) ):
            packet[index] = triggers
        # Set up the actual trigger headers.
        self.setTriggerList(triggerList=packet, mask=mask)

    def setTriggerList(self, triggerList=None, mask=0xFFFF):
        """ Sets up Trigger pulses in Bits++ using the fine grained
            method that can control every trigger line at 100uS
            intervals.
           
            TriggerList should contain 1 entry for every 100uS 
            packet (see getPackets) the binary word in each entry 
            specifies which trigger line will be active during that
            time slot.
        
            Note that mask only protects the digital output lines
            set by other activities in the Bits. Not other triggers.
            
            Example::

                packet = [0]*self._NumberPackets
                packet[0] = 0b0000000010
                bits.setTriggerList(packet)
            
            Will sens a 100us pulse on DOUT1 at the start of the frame.
            
             Example 2::

                packet = [0]*self._NumberPackets
                packet[10] = 0b0000000010
                packet[20] = 0b0000000001
                bits.setTriggerList(packet)
                bits.startTrigger()
            
            Will sens a 100us pulse on DOUT1 1000us after the start of the 
            frame and a second 100us pusle on DOUT0 2000us after the start of
            the frame.
            
            Triggers will continue until stopTrigger is called.
            
        """
                                                                               
        if len(triggerList) < self._NumberPackets:
            warning = ("setTriggerList: TriggerList does not "
                       "contain enough data")
            raise AssertionError(warning)
        
        # Constants for FE1 via D25 connector goggle settings.
        bothOpen = 16
        leftOpen = 0
        rightOpen = 32
        bothClosed = 48

        if self.gogglesGo: # Force mask to include goggles
            mask = (mask & 0b1111111111001111) +48
        # For every item in data packet representing trigger values.
        for index in range(0,self._NumberPackets):
            # Select the item
            trig=triggerList[index]
            # Mask out the original tirggers and add in the four possible
            # goggle states.
            trigBothOpen = (trig & 0b1111111111001111) + bothOpen
            trigLeftOpen = (trig & 0b1111111111001111) + leftOpen
            trigRightOpen = (trig & 0b1111111111001111) + rightOpen
            trigBothClosed = (trig & 0b1111111111001111) + bothClosed
            # Set up the TLock Memory address indexes for the trigger alone
            # and the trigger with all possible goggle states.
            self._HEADandTrig[19+index*2,:,0] = 8 + index
            self._HEADandGogLeftOpen[19+index*2,:,0] = 8 + index
            self._HEADandGogRightOpen[19+index*2,:,0] = 8 + index
            self._HEADandGogBothOpen[19+index*2,:,0] = 8 + index
            self._HEADandGogBothClosed[19+index*2,:,0] = 8 + index
            # Set the data payload within the TLock for the trigger alone.
            self._HEADandTrig[19+index*2,:,1] = int(np.floor(trig / 256))
            self._HEADandTrig[19+index*2,:,2] = int(np.remainder(trig,256))
            # Set the data payloads for the triggers with all possible goggle states.
            self._HEADandGogLeftOpen[19+index*2,:,1] = int(
                                            np.floor(trigLeftOpen / 256))
            self._HEADandGogLeftOpen[19+index*2,:,2] = int(
                                            np.remainder(trigLeftOpen, 256))
            self._HEADandGogRightOpen[19+index*2,:,1] = int(
                                            np.floor(trigRightOpen / 256))
            self._HEADandGogRightOpen[19+index*2,:,2] = int(
                                            np.remainder(trigRightOpen, 256))
            self._HEADandGogBothOpen[19+index*2,:,1] = int(
                                            np.floor(trigBothOpen / 256))
            self._HEADandGogBothOpen[19+index*2,:,2] = int(
                                            np.remainder(trigBothOpen, 256))
            self._HEADandGogBothClosed[19+index*2,:,1] = int(
                                            np.floor(trigBothClosed / 256))
            self._HEADandGogBothClosed[19+index*2,:,2] = int(
                                            np.remainder(trigBothClosed, 256))
        # Set the hardware mask in each TLock.                            
        self._HEADandTrig[17,:,1]=int(np.floor(mask/256))
        self._HEADandTrig[17,:,2]=int(np.remainder(mask,256))
        self._HEADandGogLeftOpen[17,:,1]=int(np.floor(mask/256))
        self._HEADandGogLeftOpen[17,:,2]=int(np.remainder(mask,256))
        self._HEADandGogRightOpen[17,:,1]=int(np.floor(mask/256))
        self._HEADandGogRightOpen[17,:,2]=int(np.remainder(mask,256))
        self._HEADandGogBothOpen[17,:,1]=int(np.floor(mask/256))
        self._HEADandGogBothOpen[17,:,2]=int(np.remainder(mask,256))
        self._HEADandGogBothClosed[17,:,1]=int(np.floor(mask/256))
        self._HEADandGogBothClosed[17,:,2]=int(np.remainder(mask,256))
        
        # Turn the trigger only payload into a string 
        # The goggles payloads are dealt with elsewhere.
        self._HEADandTrigStr = self._HEADandTrig.tostring()
        
        # Any attempt to set the triggers should un-protect them
        # since by definition the protected values are no longer valid.
        self.triggerProtected = False

    def sendTrigger(self, triggers=0, onTime=0, duration=0,
                      mask=65535):
        """ Sends a single trigger using up 1 win.flip.
            The trigger will be sent on the following frame.
        
            The triggers will continue until after the next win.flip.
            
            Actions are always 1 frame after the request.
        
            May do odd things if Goggles and Analog are also
            in use.
            
            Example::

                bits.sendTrigger(0b0000000010, 2.0, 4.0)
                bits.win.flip()
            
            Will send a 4ms puilse on DOUT1 2ms after the start of the frame.
            Due to the following win.flip() the pulse should last for 1 frame only.
            
            Triggers will continue until stopTrigger is called.
        """
        self.setTrigger(triggers,onTime,duration,mask)
        self.trigger=True
        self.win.flip() # Send the trigger but trigger not acted on until the next frame. 
        #If next winflip is late the trigger will be repeated until it is cleared by the next winflip
        self.trigger=False
        
    def startTrigger(self):
        """ Start sending triggers on the next win flip 
            and continue until stopped by stopTrigger
            Triggers start 1 frame after the frame on which 
            the first trigger is sent.
            
            Example::

                bits.setTrigger(0b0000000010, 2.0, 4.0, 0b0111111111)
                bits.startTrigger()
                while imageOn:
                    #do some processing
                    continue
                bits.stopTrigger()
                bits.win.flip()
        """
        # If triggers have been protected from another TLock action
        # we will need to restore them first.
        if self.triggerProtected:
            self._restoreTrigger()
            self.triggerProtected = False
        self.trigger=True
        
    def stopTrigger(self):
        """ Stop sending triggers at the next win flip
        
        Example:

        .. code-block:: python

                bits.setTrigger(0b0000000010, 2.0, 4.0, 0b0111111111)
                bits.startTrigger()
                while imageOn:
                    #do some processing
                    continue
                bits.stopTrigger()
                bits.win.flip()

        """
        # This is a hack to get triggers to stop on the one
        # Bits++ box tested.

        self.trigger=False # Needed before protecting triggers.
        # Protect existing triggers. Also sets triggers to zero.
        self._protectTrigger() 
        self.trigger=True # Needed to send the zero trigger.
        self.win.flip() # Make sure zero trigger is sent.
        self.trigger=False # Now turn off triggers.
        self._restoreTrigger() # Recover old triggers for
                               # Future use


    def startGoggles(self, left = 0, right = 1):
        """Starts CRS stereo goggles. Note if you are
        using FE-1 goggles you should start this before
        connecting the goggles.

        Left is the state of the left shutter on the
        first frame to be presented 0, False or
        'closed'=closed; 1, True or 'open' = open,

        right is the state of the right shutter on the
        first frame to be presented 0, False or
        'closed'=closed; 1, True or 'open' = open
        
        Note you can set the goggles to be both open 
        or both closed on the same frame.
        
        The system will always toggle the state of 
        each lens so as to not damage FE-1 goggles.
        
        Example::

            bits.startGoggles(0,1)
            bits.win.flip()
            while not response
                bits.win.flip()
                #do some processing
            bits.stopGoggles()
            bits.win.flip()
            
        Starts toggling the goggles with the right eye open in sync with the
        first win.flip() within the loop. The open eye will alternate.
            
        Example::

            bits.startGoggles(1,1)
            bits.win.flip()
            while not response:
                bits.win.flip()
                #do some processing
            bits.stopGoggles()
            bits.win.flip()
            
        Starts toggling the goggle with both eyes open in sync with the first
        win.flip() within the loop. Eyes will alternate between both open and both closed.
        
        Note it is safe to leave the goggles toggling forever, ie to never call stopGoggles().
        """
        # Protect any existing trigger settings if required.
        self._protectTrigger() # Also sets triggers to zero.
        if left in ('closed','Closed'):
           self.gogglesLeft = 0
        elif left in ('open','Open'):
            self.gogglesLeft = 1
        else:
            self.gogglesLeft = int(left)
        if right in ('closed','Closed'):
            self.gogglesRight = 0
        elif right in ('open','Open'):
            self.gogglesRight = 1
        else:
            self.gogglesRight = int(right)
        self.gogglesGo = True
            
    def stopGoggles(self):
        """ Stop the stereo goggles from toggling 
        
        Example::

            bits.startGoggles(0,1)
            bits.win.flip()
            while not response:
                bits.win.flip()
                #do some processing
            bits.stopGoggles()
            bits.win.flip()
            
        Starts toggling the goggles with the right eye open in sync with the
        first win.flip(0) within the loop. The open eye will alternate.

        Note it is safer to leave the goggles toggling forever, ie to never call stopGoggles().
        """
        # Restore old triggers if goggles used without other triggers.
        self._restoreTrigger()
        self.stopTrigger() #A hack for Bits++
        self.gogglesGo = False


    def reset(self):
        """Deprecated: This was used on the old Bits++
        to power-cycle the box.
        It required the compiled dll, which only worked 
        on windows and doesn't work with Bits# or Display++.
        """
        reset()

    #==========================================#
    # Helper functions for LUTs and Triggers   #
    # Should not be needed by user             #
    #==========================================#

    def _protectTrigger(self):
        """ If Goggles (or analog) outputs are used when the
        digital triggers are off we need to make a set of blank 
        triggers first. But the user might have set up triggers
        in waiting for a later time. So this will protect them.
        """
        # No need to do this if triggers are active anyway.
        # or if they are already being protected.
        if not self.trigger and not self.triggerProtected:
            self._keepTrig = deepcopy(self._HEADandTrig)
            self._keepGogLeftOpen = deepcopy(self._HEADandGogLeftOpen)
            self._keepGogRightOpen = deepcopy(self._HEADandGogRightOpen)
            self._keepGogBothOpen = deepcopy(self._HEADandGogBothOpen)
            self._keepGogBothClosed = deepcopy(self._HEADandGogBothClosed)
            self.setTrigger()
            # Set flag to tell trigger start that it has to recover its 
            # trigger headers.
            self.triggerProtected = True
        
    def _restoreTrigger(self):
        """ Restores the triggers to previous settings
        """
        # No need to do this if triggers are running as will have been
        # recovered already if required.
        if not self.trigger:
            self._HEADandTrig = deepcopy(self._keepTrig)
            self._HEADandTrigStr = self._HEADandTrig.tostring()
            self._HEADandGogLeftOpen = deepcopy(self._keepGogLeftOpen)
            self._HEADandGogRightOpen = deepcopy(self._keepGogRightOpen)
            self._HEADandGogBothOpen = deepcopy(self._keepGogBothOpen)
            self._HEADandGogBothClosed = deepcopy(self._keepGogBothClosed)
            # Set flag to tell trigger start that it has no need to recover its 
            # trigger headers.
            self.triggerProtected = False

    def _drawLUTtoScreen(self):
        """(private) Used to set the LUT in 'bits++' mode.
        Should not be needed by user if attached to a
        :class:`~psychopy.visual.Window` since this will automatically
        draw the LUT as part of the screen refresh.
        """
        # push the projection matrix and set to orthographic
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        # this also sets the 0,0 to be top-left
        GL.glOrtho(0, self.win.size[0], self.win.size[1], 0, 0, 1)
        # but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        # draw the pixels
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        GL.glRasterPos2i(0, 1)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glDrawPixels(len(self._HEADandLUT), 1,
                        GL.GL_RGB, GL.GL_UNSIGNED_BYTE,
                        self._HEADandLUTstr)
        # GL.glDrawPixels(524,1, GL.GL_RGB,GL.GL_UNSIGNED_BYTE,
        #    self._HEADandLUTstr)
        # return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        
    def _ResetClock(self):
        """(private) Used to reset Bits hardware clock.
        Should not be needed by user if attached to a 
        :class:`~psychopy.visual.Window`
        since this will automatically draw the 
        reset code as part of the screen refresh.
        """
        #push the projection matrix and set to orthographic
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho( 0, self.win.size[0],self.win.size[1], 0, 0, 1 )    #this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        # unload texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        # unload mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        # draw the pixels
        GL.glRasterPos2i(0,2)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glDrawPixels(len(self._HEADandClock),1,
            GL.GL_RGB,GL.GL_UNSIGNED_BYTE,
            self._HEADandClockstr)
        #return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode( GL.GL_PROJECTION )
        GL.glPopMatrix()
        GL.glMatrixMode( GL.GL_MODELVIEW )
        # ensures that only 1 clock reset pulse will be issed at a time
        self.clockReset=False 

    def _drawTrigtoScreen(self, sendStr=None):
        """(private) Used to send a trigger pulse.
        Should not be needed by user if attached to a 
        :class:`~psychopy.visual.Window`
        since this will automatically draw the trigger code as 
        part of the screen refresh.
        """
        if sendStr == None:
            sendStr = self._HEADandTrigStr
        
        #push the projection matrix and set to orthographic
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho( 0, self.win.size[0],self.win.size[1], 0, 0, 1 )    #this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        #draw the pixels
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glRasterPos2i(0,3)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glDrawPixels(len(self._HEADandTrig),1,
            GL.GL_RGB,GL.GL_UNSIGNED_BYTE,
            sendStr)
        GL.glMatrixMode( GL.GL_PROJECTION )
        GL.glPopMatrix()
        GL.glMatrixMode( GL.GL_MODELVIEW )

    def _Goggles(self):
        """(private) Used to set control the goggles.
        Should not be needed by user if attached to a 
        :class:`~psychopy.visual.Window`
        """
        # Work out current goggles state value.
        gogglesState = self.gogglesRight*2+self.gogglesLeft

        # Toggle the goggle states ready for the next win flip
        self.gogglesLeft = 1 - self.gogglesLeft
        self.gogglesRight = 1- self.gogglesRight
 
        # Use gogleState to load the desired goggle trigger pattern into.
        # the TLock and draw this trigger.
        if gogglesState == 0:
            self._drawTrigtoScreen(self._HEADandGogBothOpen.tostring())
        if gogglesState == 1:
            self._drawTrigtoScreen(self._HEADandGogLeftOpen.tostring())
        if gogglesState == 2:
            self._drawTrigtoScreen(self._HEADandGogRightOpen.tostring())
        if gogglesState == 3:
            self._drawTrigtoScreen(self._HEADandGogBothClosed.tostring())

    def _setupShaders(self):
        """creates and stores the shader programs needed for mono++ and
        color++ modes
        """
        if not haveShaders:
            return
        self._shaders = {}
        shCompile = shaders.compileProgram
        self._shaders['mono++'] = shCompile(shaders.vertSimple,
                                            shaders.bitsMonoModeFrag)
        self._shaders['color++'] = shCompile(shaders.vertSimple,
                                             shaders.bitsColorModeFrag)

    def _prepareFBOrender(self):
        if self.mode == 'mono++':
            GL.glUseProgram(self._shaders['mono++'])
        elif self.mode == 'color++':
            GL.glUseProgram(self._shaders['color++'])
        else:
            GL.glUseProgram(self.win._progFBOtoFrame)

    def _finishFBOrender(self):
        GL.glUseProgram(0)

    def _afterFBOrender(self):
        GL.glDisable(GL.GL_BLEND)
        if self.mode.startswith('bits'):
            self._drawLUTtoScreen()
        if self.gogglesGo: # Will also send triggers if started
            self._Goggles()
        elif self.trigger:
            self._drawTrigtoScreen()
        if self.clockReset:
            self._ResetClock()
        GL.glEnable(GL.GL_BLEND)


class BitsSharp(BitsPlusPlus, serialdevice.SerialDevice):
    """A class to support functions of the Bits# (and most Display++ functions
    This device uses the CDC (serial port) connection to the Bits box.
    To use it you must have followed the instructions from CRS Ltd. to get
    your box into the CDC communication mode.
    Typical usage (also see demo in Coder view demos>hardware>BitsBox ):

    .. code-block:: python

        from psychopy import visual
        from psychopy.hardware import crs
        # we need to be rendering to framebuffer
        win = visual.Window([1024,768], useFBO=True)
        bits = crs.BitsSharp(win, mode = 'mono++')
        # You can continue using your window as normal and OpenGL shaders
        # will convert the output as needed
        print(bits.info)
        if not bits.OK:
            print('failed to connect to Bits box')
            core.quit()
        core.wait(0.1)
        # now, you can change modes using
        bits.mode = 'mono++' # 'color++', 'mono++', 'bits++', 'status'

    Note that the firmware in Bits# boxes varies over time and some features of
    this class may not work for all firmware versions. Also Bits# boxes can be
    configured in various ways via their config.xml file so this class makes certain
    assumptions about the configuration. In particular it is assumed that all
    digital inputs, triggers and analog inputs are reported as part of status
    updates. If some of these report are disabled in your config.xml file 
    then 'status' and 'event' commands in this class may not work.
    
    RTBox commands that reset the key mapping have been found not to work
    one some firmware
    """
    name = b'CRS Bits#'

    def __init__(self, win=None,
                         portName=None,
                         mode='', 
                         checkConfigLevel=1,
                         gammaCorrect='hardware',
                         gamma=None,
                         noComms=False):
        """
        Parameters
        ----------

        win : a PsychoPy :class:`~psychopy.visual.Window` object, required

        portName : str or int
            the (virtual) serial port to which the device is
            connected. If None then PsychoPy will search available
            serial ports and test communication (on OSX, the first
            match of `/dev/tty.usbmodemfa*` will be used and on
            linux `/dev/ttyS0` will be used

        mode : 'bits++', 'color++', 'mono++', 'status'

        checkConfigLevel : int

            Allows you to specify how much checking of the device is
            done to ensure a valid identity look-up table. If you specify
            one level and it fails then the check will be escalated to
            the next level (e.g. if we check level 1 and find that it
            fails we try to find a new LUT):

                - 0 don't check at all
                - 1 check that the graphics driver and OS version haven't
                    changed since last LUT calibration
                - 2 check that the current LUT calibration still provides
                    identity (requires switch to status mode)
                - 3 search for a new identity look-up table (requires
                    switch to status mode)

        gammaCorrect : string

            G overning how gamma correction is performed:
            - 'hardware': use the gamma correction file stored on the
              hardware
            - 'FBO': gamma correct using shaders when rendering the FBO
              to back buffer
            - 'bitsMode': in bits++ mode there is a user-controlled LUT
              that we can use for gamma correction

        noComms : bool
            If True then don't try to communicate with the device at all
            (passive mode). This can be useful if you want to debug the
            system without actually having a Bits# connected.
        """

        # import pyglet.GL late so that we can import bits.py without it
        # initially
        global GL, visual
        from psychopy import visual
        import pyglet.gl as GL

        if noComms:
            self.noComms = True
            self.OK = True
            self.sendMessage = self._nullSendMessage
            self.getResponse = self._nullGetResponse
        else:
            self.noComms = False
            # look for device on valid serial ports
            # parity="N",  # 'N'one, 'E'ven, 'O'dd, 'M'ask,
            serialdevice.SerialDevice.__init__(self, port=portName,
                                               baudrate=19200,
                                               byteSize=8, stopBits=1,
                                               parity="N",
                                               eol='\n',
                                               maxAttempts=1,
                                               pauseDuration=0.1,
                                               checkAwake=True)
        if not self.OK:
            return
        self.win = win
        if self.noComms:
            self.frameRate = self.win.getActualFrameRate()
        else:
            msg='a'
            while msg:
                msg=self.read(timeout=0.1)
            self.sendMessage('$VideoFrameRate\r')
            self.pause()
            msg=self.read(timeout=0.1)
            msg2 = msg.split(b';')
            self.frameRate = float(msg2[1])
        
        self._setHeaders(self.frameRate)
        # flag for controlling analog outputs
        self.analog = False
        
        # replace window methods with our custom ones
        self.win._prepareFBOrender = self._prepareFBOrender
        self.win._finishFBOrender = self._finishFBOrender
        self.win._afterFBOrender = self._afterFBOrender

        # Bits++ doesn't do its own correction so we need to
        self.gammaCorrect = gammaCorrect
        self.gamma = gamma
        # we have a confirmed connection. Now check details about device and
        # system
        if not hasattr(self, 'info'):
            self.info = self.getInfo()
        self.config = None
        self.mode = mode
        if self.win is not None:
            if not hasattr(self.win, '_prepareFBOrender'):
                logging.error("BitsSharp was given an object as win "
                              "argument but this is not a visual.Window")
            self.win._prepareFBOrender = self._prepareFBOrender
            self.win._finishFBOrender = self._finishFBOrender
            self._setupShaders()
            # now check that we have a valid configuration of the box
            if checkConfigLevel:
                ok = self.checkConfig(level=checkConfigLevel)
            else:
                self.win.gammaRamp = self.config.identityLUT
        else:
            self.config = None  # makes no sense if we have a window?
            logging.warning("%s was not given any PsychoPy win" % (self))
  
        # members for controlling the RTBox functionality
        self.RTBoxMode = ['CB6','down','trigger']
        self.RTBoxEnabled = False
        
        # Make sure that RTBox event logging is off
        self.RTBoxDisable()
        
        # members for storing RTBox button presses
        self.RTButtons=[] # list of button presses
        self.nRTPresses = 0 # number of button presses recorded

        # members for controlling the statusBox functionality
        self.statusBoxMode = ['CB6','down','trigger','analog']
        self.statusBoxEnabled = False
        self.statusButtonMap = [99]*23
        self.statusBoxThreshold = 9999.99

        # members for storing statusBox presses
        self.statusButtons=[] # list of button presses
        self.nStatusPresses = 0 # number of button presses recorded
        
        # members for controlling status logging and reporting
        self.statusDINBase = 0b1111111111   #initial values for ditgial ins
        self.statusIRBase = 0b111111        #initial values for CB6 IR box
        self.statusTrigInBase = 0           #initial values for TrigIn
        self.statusADCBase = 0              #initial value for ADCs
        self.statusThreshold = 9999.99      #threshold for ADC change
        self.statusMode = ['up','down']     #Direction of events to be reported
        self.statusEnabled = False
        self._statusSize = 111
        
        # members for storing status logs and reports
        self.statusQ=Queue.Queue(70000) # sets up a queue in which to store bits status events
        self.statusValues=[] # full list of values recorded while logging the Bits# status
        self.status_nValues = 0 #number of status values recorded
        self.statusEvents=[] # list of meaningful events extracted from log
        self.status_nEvents = 0 #number of events recorded

    #==============================================#
    # Some overloads as Bits++ and Bits# appear to #
    # function slightly differently when it comes  #
    # to triggers                                  #
    #==============================================#
    
    def stopTrigger(self):
        """Stop sending triggers at the next win flip.
        
        Example::

            bits.setTrigger(0b0000000010, 2.0, 4.0, 0b0111111111)
            bits.startTrigger()
            while imageOn:
                #do some processing
                continue
            bits.stopTrigger()
            bits.win.flip()

        """
        # Simply stops sending TLock triggers as the next win flip.
        self.trigger=False

    def stopGoggles(self):
        """ Stop the stereo goggles from toggling 
        
        Example::

            bits.startGoggles(0,1)
            bits.win.flip()
            while not response
                bits.win.flip()
                #do some processing
            bits.stopGoggles()
            bits.win.flip()

        Starts toggling the goggles with the right eye open in sync with the
        first win.flip(0) within the loop. The open eye will alternate.

        Note it is safer to leave the goggles toggling forever, ie to never call stopGoggles().
        """
        # Restore any protected triggers if required and stop sending.
        # TLock for goggles at next win flip.
        self._restoreTrigger()
        self.gogglesGo = False

    #===================================================#
    # Some empty methods that we can use to replace     #
    # serial methods if noComms                         #
    #===================================================#
    
    def _nullSendMessage(self, message, autoLog=True):
        pass

    def _nullGetResponse(self, length=1, timeout=0.1):
        pass

    #================================#
    # Basic functionality            #
    #================================#

    def __del__(self):
        """If the user discards this object then close the serial port
        so it is released.
        """
        try:
            self.com.close()
        except AttributeError:
            pass

    def isAwake(self):
        """Test whether we have an active connection on the virtual serial
        port
        """
        self.info = self.getInfo()
        # if we got a productType then this is a bits device
        return len(self.info['ProductType']) > 0

    def getInfo(self):
        """ Returns a python dictionary of info about the Bits Sharp box
        
            Example::
                info=bits.getInfo
                print(info['ProductType'])
            
        
        """
        if self.noComms:
            return {'ProductType': 'Bits#',
                    'SerialNumber': 'n/a',
                    'FirmwareDate': 'n/a'}
        self.sendMessage(b'$Stop\r')
        self.read(timeout=0.5)  # clear input buffer
        
        
        info = {}
        # get product ('Bits_Sharp'?)
        self.sendMessage(b'$ProductType\r')
        time.sleep(0.1)
        info['ProductType'] = self.read().replace(b'#ProductType;', b'')
        info['ProductType'] = info['ProductType'].replace(b';\n\r', b'')
        # get serial number
        self.sendMessage(b'$SerialNumber\r')
        time.sleep(0.1)
        info['SerialNumber'] = self.read().replace(b'#SerialNumber;', b'')
        info['SerialNumber'] = info['SerialNumber'].replace(b'\x00\n\r', b'')
        # get firmware date
        self.sendMessage(b'$FirmwareDate\r')
        time.sleep(0.1)
        info['FirmwareDate'] = self.read().replace(b'#FirmwareDate;', b'')
        info['FirmwareDate'] = info['FirmwareDate'].replace(b';\n\r', b'')
        return info

    @property
    def mode(self):
        """Get/set the mode of the BitsSharp to one of:
            "bits++"
            "mono++" 
            "color++" 
            "status"
            "storage"
            "auto"
        """
        return self.__dict__['mode']

    @mode.setter
    def mode(self, value):
        requiresFBO = 'mode requires a PsychoPy Window with useFBO=True'
        if value in [None, '']:
            self.__dict__['mode'] = ''
            return
        elif ('mode' in self.__dict__) and value == self.mode:
            return  # nothing to do here. Move along please
        elif value == 'status':
            self.sendMessage(b'$statusScreen\r')
            self.__dict__['mode'] = 'status'
            return
        elif 'storage' in value.lower():
            self.sendMessage(b'$USB_massStorage\r')
            self.__dict__['mode'] = 'massStorage'
        elif value.startswith('bits'):
            self.sendMessage(b'$BitsPlusPlus\r')
            self.__dict__['mode'] = 'bits++'
            self.setLUT()
        elif value.startswith('mono'):
            if not self.win.useFBO:
                raise Exception("Mono++ " + requiresFBO)
            self.sendMessage(b'$monoPlusPlus\r')
            self.__dict__['mode'] = 'mono++'
        elif value.startswith('colo'):
            if not self.win.useFBO:
                raise Exception("Color++ " + requiresFBO)
            self.sendMessage(b'$colorPlusPlus\r')
            self.__dict__['mode'] = 'color++'
        elif value.startswith('auto'):
            if not self.win.useFBO:
                raise Exception("Auto++ " + requiresFBO)
            self.sendMessage(b'$autoPlusPlus\r')
            self.__dict__['mode'] = 'auto++'
        else:
            msg = ("Bits# doesn't know how to use mode "
                   "%r. Should be 'mono++', 'color++' etc")
            raise AttributeError(msg % value)
        logging.info('Switched %s to %s mode' % (self.info['ProductType'],
                                                 self.__dict__['mode']))

    def setLUT(self, newLUT=None, gammaCorrect=False, LUTrange=1.0,
               contrast=None):
        """SetLUT is only really needed for bits++ mode of bits# to set the
        look-up table (256 values with 14bits each).
        For the BitsPlusPlus device the default is to perform gamma
        correction here but on the BitsSharp it seems better to have the
        device perform that itself as the last step so gamma correction is
        off here by default.
        If no contrast has yet been set (it isn't needed for other modes)
        then it will be set to 1 here.
        """
        if contrast is not None:
            # we were given a new contrast value so use it:
            self.contrast = contrast
        elif not hasattr(self, 'contrast'):
            # we don't have one yet so create a default
            self.contrast = 1.0
        BitsPlusPlus.setLUT(self, newLUT, gammaCorrect, LUTrange)

    @property
    def temporalDithering(self):
        """Temporal dithering can be set to True or False
        """
        return self.__dict__['temporalDithering']

    @temporalDithering.setter
    def temporalDithering(self, value):
        if value:
            self.sendMessage(b'$TemporalDithering=[ON]\r')
        else:
            self.sendMessage(b'$TemporalDithering=[OFF]\r')
        self.__dict__['temporalDithering'] = value

    @property
    def gammaCorrectFile(self):
        """Get / set the gamma correction file to be used
        (as stored on the device)
        """
        return self.__dict__['gammaCorrectFile']

    @gammaCorrectFile.setter
    def gammaCorrectFile(self, value):
        self.sendMessage(b'$enableGammaCorrection=[%s]\r' % (value))
        self.__dict__['gammaCorrectFile'] = value

    @property
    def monitorEDID(self):
        """Get / set the EDID file for the monitor.
        The edid files will be located in the EDID subdirectory of the
        flash disk. The file `automatic.edid` will be the file read from
        the connected monitor.
        """
        return self.__dict__['monitorEDID']

    @monitorEDID.setter
    def monitorEDID(self, value):
        self.sendMessage(b'$setMonitorType=[%s]\r' % (value))
        self.__dict__['monitorEDID'] = value

    def beep(self, freq=800, dur=1):
        """Make a beep of a given frequency and duration
        """
        self.sendMessage(b'$Beep=[%i, %.4f]\r' % (freq, dur))

    def getVideoLine(self, lineN, nPixels, timeout=10.0, nAttempts=10):
        """Return the r,g,b values for a number of pixels on a particular
        video line

        :param lineN: the line number you want to read
        :param nPixels: the number of pixels you want to read
        :param nAttempts: the first time you call this function it has
            to get to status mode. In this case it sometimes takes a few
            attempts to make the call work

        :return: an Nx3 numpy array of uint8 values
        """
        # define sub-function oneAttempt
        def oneAttempt():
            self.com.flushInput()
            self.sendMessage(b'$GetVideoLine=[%i, %i]\r' % (lineN, nPixels))
            # the box implicitly ends up in status mode
            self.__dict__['mode'] = 'status'
            # prepare to read
            t0 = time.time()
            raw = ""
            vals = []
            while len(vals) < (nPixels * 3):
                raw += self.read(timeout=0.001).decode("utf-8")
                vals = raw.split(';')[1:-1]
                if time.time() - t0 > timeout:
                    msg = ("getVideoLine() timed out: only found %i pixels"
                           " in %.2f s")
                    logging.warn(msg % (len(vals), timeout))
                    return []
            return np.array(vals, dtype=int).reshape([-1, 3])

        # call oneAttempt a few times
        for attempt in range(nAttempts):
            vals = oneAttempt()
            if len(vals):
                return vals
        return None
        
    #==============================================================#
    # Bits# and Display++ comms functions                          #
    #==============================================================#

    def read(self, timeout=0.1):
        """Get the current waiting characters from the serial port
        if there are any.
        
        Mostly used internally but may be needed by user. Note the
        return message depends on what state the device is in and will
        need to be decoded. See the Bits# manual but also the other functions
        herein that do the decoding for you.
        
        Example:
            message = bits.read()
        """
        if self.noComms:
            return
        self.com.timeout = timeout
        nChars = self._inWaiting()
        raw = self.com.read(nChars)
        if raw:
            # don't bother if we found nothing on input
            logging.debug("Got BitsSharp reply: %s" % (repr(raw)))
        return raw
        
    def flush(self):
        """ Flushes the serial input buffer
        Its good to do this before and after data collection,
        And generally quite often.
        """
        
        while self._inWaiting()>0:
            msg=self.read(0.001)

    #=============================================================#
    # Helper functions for comms                                  #
    #=============================================================#

    def _inWaiting(self):
        """Helper function to determine how many bytes are waiting on
        the serial port.
        """
        if self.noComms:
            return 0
        else:
            return self.com.inWaiting()
    
    #=============================================================#
    # overload of _afterFBOrender for Bits# and Display++         #
    #=============================================================#
    
    def _afterFBOrender(self):
        GL.glDisable(GL.GL_BLEND)
        if self.mode.startswith('bits'):
            self._drawLUTtoScreen()
        if self.gogglesGo: # Will also send triggers if requested
            self._Goggles()
        elif self.analog or self.trigger:
            self._drawTrigtoScreen()
        if self.clockReset:
            self._ResetClock()
        GL.glEnable(GL.GL_BLEND)


    #====================================================#
    # Analog functions send voltages via the DAC outputs #
    # But we also need to overload the setTrigger        #
    # functions to protect the analog settings.          #
    #====================================================#
    
    def setTrigger(self, triggers=0, onTime=0, duration=0,
                     mask=0xFFFF):
        """ Quick way to set up triggers.
            
            Triggers is a binary word that determines which 
            triggers will be turned on.
            
            onTime specifies the start time of the trigger within
            the frame (in S with 100uS resolution)
            
            Duration specifies how long the trigger will last.
            (in S with 100uS resolution).
            
            Note that mask only protects the digital output lines
            set by other activities in the Bits. Not other triggers.
            
            Example:

            ```
            bits.setTrigger(0b0000000010, 2.0, 4.0, 0b0111111111)
            bits.startTrigger()
            ```

            Will issue a 4ms long high-going pulse, 2ms after the start 
            of each frame on DOUT1 while protecting the value of DOUT 9.
        """
        
        # Protect the analog output settings. 
        self._protectAnalog()

        super(BitsSharp, self).setTrigger(triggers, 
                                            onTime, 
                                            duration, 
                                            mask)
        
        # Restore the analog output settings.
        self._restoreAnalog
        
    def setTriggerList(self, triggerList=None, mask=0xFFFF):
        """Overaload of Bits# and Display++ 
            Sets up Trigger pulses via the list method 
            while preserving the analog output settings.
        
            Sets up Trigger pulses in Bist++ using the fine grained
            method that can control every trigger line at 100uS
            intervals.
           
            TriggerList should contain 1 entry for every 100uS 
            packet (see getPackets) the binary word in each entry 
            specifies which trigger line will be active during that
            time slot.
        
            Note that mask only protects the digital output lines
            set by other activities in the Bits. Not other triggers.
            
            Example:
                packet = [0]*self._NumberPackets
                packet[0] = 0b0000000010
                bits.setTriggerList(packet)
            
            Will sens a 100us pulse on DOUT1 at the start of the frame.
            
             Example 2:
                packet = [0]*self._NumberPackets
                packet[10] = 0b0000000010
                packet[20] = 0b0000000001
                bits.setTriggerList(packet)
                bits.statrtTrigger()
            
            Will sens a 100us pulse on DOUT1 1000us after the start of the 
            frame and a second 100us pusle on DOUT0 2000us after the start of
            the frame.
            
            Triggers will continue until stopTrigger is called.

        """
        
        # Protect the analog output settings.
        self._protectAnalog()

        super(BitsSharp, self).setTriggerList(triggerList, 
                                            mask)
        
        # Restore the analog output settings
        self._restoreAnalog
    
    def setAnalog(self,AOUT1=0, AOUT2=0):
        """Sets up Analog outputs in Bits# 
        AOUT1 and AOUT2 are the two analog values required in volts.
        Analog commands are issued at the next win.flip() and
        actioned 1 video frame later.
        
        Example:
            bits.set Analog(4.5,-2.2)
            bits.startAnalog()
            bits.win.flip()
            
        
        """
        # Convert AOUT1 from volts to device units.
        AOUT1 = int(np.round(32767.0*AOUT1/5.0,0))
        if AOUT1 < 0:
            AOUT1 = 65535 + AOUT1
        # Add analog values to the Tlock payloads
        self._HEADandTrig[11,:,1] = int(np.floor(AOUT1 / 256))
        self._HEADandTrig[11,:,2] = np.remainder(AOUT1, 256)
        self._HEADandGogLeftOpen[11,:,1] = int(np.floor(AOUT1 / 256))
        self._HEADandGogLeftOpen[11,:,2] = np.remainder(AOUT1, 256)
        self._HEADandGogRightOpen[11,:,1] = int(np.floor(AOUT1 / 256))
        self._HEADandGogRightOpen[11,:,2] = np.remainder(AOUT1, 256)
        self._HEADandGogBothOpen[11,:,1] = int(np.floor(AOUT1 / 256))
        self._HEADandGogBothOpen[11,:,2] = np.remainder(AOUT1, 256)
        self._HEADandGogBothClosed[11,:,1] = int(np.floor(AOUT1 / 256))
        self._HEADandGogBothClosed[11,:,2] = np.remainder(AOUT1, 256)
        
        # Convert AOUT2 from volts to device units.
        AOUT2 = int(np.round(32767.0*AOUT2 / 5.0, 0))
        if AOUT2 < 0:
            AOUT2 = 65535 + AOUT2
        # Add analog values to the Tlock payloads
        self._HEADandTrig[13,:,1] = int(np.floor(AOUT2 / 256))
        self._HEADandTrig[13,:,2] = np.remainder(AOUT2, 256)
        self._HEADandGogLeftOpen[13,:,1] = int(np.floor(AOUT2 / 256))
        self._HEADandGogLeftOpen[13,:,2] = np.remainder(AOUT2, 256)
        self._HEADandGogRightOpen[13,:,1] = int(np.floor(AOUT2 / 256))
        self._HEADandGogRightOpen[13,:,2] = np.remainder(AOUT2, 256)
        self._HEADandGogBothOpen[13,:,1] = int(np.floor(AOUT2 / 256))
        self._HEADandGogBothOpen[13,:,2] = np.remainder(AOUT2,256)
        self._HEADandGogBothClosed[13,:,1] = int(np.floor(AOUT2 / 256))
        self._HEADandGogBothClosed[13,:,2] = np.remainder(AOUT2, 256)

        # Convert the trigger only payload to a string.
        # goggle payloads are dealt with later.
        self._HEADandTrigStr = self._HEADandTrig.tostring()
        
    def sendAnalog(self,AOUT1 = 0, AOUT2 = 0):
        """sends a single analog output pulse uses up 1 win flip.
        pulse will continue until next win flip called.
        Actions are always 1 frame behind the request.
        
        May conflict with trigger and goggle settings.
        
        Example:
            bits.sendAnalog(4.5,-2.0)
            bits.win.flip()
        """
        if not self.trigger:    # If digital triggers are not on.
            self._protectTrigger() # Protect any trigger settings.
            # and set up a blank trigger
        # Goggle setting always preserved.
        self.setAnalog(AOUT1 = AOUT1, AOUT2 = AOUT2)
        self.analog=True
        self.win.flip() # Send the pulse but not acted on until the next frame. 
                         # If next winflip is late the trigger will be repeated until
                         # it is cleared by the next winflip
        self.analog=False # Cancel and future analogf outs.
        self._restoreTrigger() # Restore the old digital triggers.

    def startAnalog(self):
        """will start sending analog signals on the
        next win flip and continue until stopped.
        
        Example:
            bits.set Analog(4.5,-2.2)
            bits.startAnalog()
            bits.win.flip()
        
        """
        if not self.trigger: # If digital triggers are not on.
            self._protectTrigger() # Protect any trigger settings.
            # and set up a blank trigger
        # Goggle setting always preserved.
        self.analog=True
        
    def stopAnalog(self):
        """will stop sending analogs signals at the next win flip.

        Example::

            bits.set Analog(4.5,-2.2)
            bits.startAnalog()
            bits.win.flip()
            while not response:
                #do some processing.
                bits.win.flip()
            bits.stopAnalog()
            bits.win.flip()

        """
        # Restore any protected triggers if required and stop sending.
        # TLock for analog at next win flip.
        self._restoreTrigger()
        self.analog=False
        
    #============================================================#
    # Helper functions for protecting the analog settings from   #
    # bits++ trigger functions                                   #
    #============================================================#
    
    def _protectAnalog(self):
        self.keepA1MS = self._HEADandTrig[11,:,1]
        self.keepA1LS = self._HEADandTrig[11,:,2]
        self.keepA2MS = self._HEADandTrig[13,:,1]
        self.keepA2LS = self._HEADandTrig[13,:,2]
    
    def _restoreAnalog(self):
        self._HEADandGogLeftOpen[11,:,1] = self.keepA1MS
        self._HEADandGogLeftOpen[11,:,2] = self.keepA1LS
        self._HEADandGogLeftOpen[13,:,1] = self.keepA2MS
        self._HEADandGogLeftOpen[13,:,2] = self.keepA2LS
        
        self._HEADandGogRightOpen[11,:,1] = self.keepA1MS
        self._HEADandGogRightOpen[11,:,2] = self.keepA1LS
        self._HEADandGogRightOpen[13,:,1] = self.keepA2MS
        self._HEADandGogRightOpen[13,:,2] = self.keepA2LS
        
        self._HEADandGogBothOpen[11,:,1] = self.keepA1MS
        self._HEADandGogBothOpen[11,:,2] = self.keepA1LS
        self._HEADandGogBothOpen[13,:,1] = self.keepA2MS
        self._HEADandGogBothOpen[13,:,2] = self.keepA2LS
        
        self._HEADandGogBothClosed[11,:,1] = self.keepA1MS
        self._HEADandGogBothClosed[11,:,2] = self.keepA1LS
        self._HEADandGogBothClosed[13,:,1] = self.keepA2MS
        self._HEADandGogBothClosed[13,:,2] = self.keepA2LS
        
        self._HEADandTrig[11,:,1] = self.keepA1MS
        self._HEADandTrig[11,:,2] = self.keepA1LS
        self._HEADandTrig[13,:,1] = self.keepA2MS
        self._HEADandTrig[13,:,2] = self.keepA2LS
        
        self._HEADandTrigStr = self._HEADandTrig.tostring()

    #============================================================#
    #    RTBox. Bits# and Display++ can mimic a RT Box physical  #
    #    Reaction time response box                              #
    #    see https://lobes.osu.edu/rt-box.php                    #
    #    These RTBox functions use the RTBox comms format to     #
    #    read button press and trigger events                    #
    #============================================================#

    def RTBoxClear(self):
        """ Flushes the serial input buffer.
        Its good to do this before and after data collection.
        This just calls flush() so is a wrapper for RTBox.
        """
        
        self.flush()

    def setRTBoxMode(self, mode=['CB6','Down','Trigger']):
        """ Sets the RTBox mode data member - does not
        actually set the RTBox into this mode.
        
        Example:
            bits.setRTBoxMode(['CB6','Down']) # set the mode
            bits.RTBoxEnable() # Enable RTBox emulation with
            # the preset mode.
        
        sets the RTBox mode settings for a CRS CB6 button box.
        and for detection of 'Down' events only.
        
        """
        self.RTBoxMode = mode


    def RTBoxEnable(self, mode=None, map=None):
        """ Sets up the RTBox with preset or bespoke mappings 
        and enables event detection.
        
        RTBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, tigers and
        CB6 IR input channels.
        
        Mode is a list of strings.
        Preset mappings  provided via mode:

        * `CB6` for the CRS CB6 IR response box.
        * `IO` for a three button box connected to Din0-2
        * `IO6` for a six button box connected to Din0-5
            
        If mode = None or is not set then the value of self.RTBoxMode is used.

        Bespoke Mappings over write preset ones.
        
        The format for map is a list of tuples with each tuple 
        containing the name of the 
        RT Box button to be mapped and its source 
        eg ('btn1','Din0') maps physical input Din0 to 
        logical button btn1. 
        
        Note the lowest number button event is Btn1
        
        RTBox has four logical buttons (btn1-4) and 
        three auxiliary events (light, pulse and trigger)
        Buttons/events can be mapped to multiple physical
        inputs and stay mapped until reset.
        
        Mode is a list of string or list of strings that contains 
        keywords to determine present mappings and modes for RTBox.
        
        * If mode includes 'Down' button events will be detected when pressed.
        * If mode includes 'Up' button events will be detected when released.

        You can detect both types of event but note that pulse, light and trigger events
        don't have an 'Up' mode.
        
        If Trigger is included in mode the trigger event will be mapped to the trigIn connector.

        Example:
        .. code-block:: python

            bits.RTBoxEnable(mode = ['Down']), map = [('btn1','Din0'), ('btn2','Din1')]
            
        enables the RTBox emulation to detect Down events on buttons 1 and 2 where they are
        mapped to DIN0 and DIN1.

        Example:
        .. code-block:: python

            bits.RTBoxEnable(mode = ['Down','CB6'])
        
        enables the RTBox emulation to detect Down events on the standard CB6 IR response box keys.
        
        If no key direction has been set (mode does not contain 'Up' or 'Down') the default is 'Down'.

        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        
        The ability to reset keys mappings has been found not to work
        on some Bits# firmware.
        """
        if self.noComms:
            return

        if self.statusEnabled:
            warning = ("Cannot use RTBox status logging "
                       " is on")
            raise AssertionError(warning)
        
        if self.statusBoxEnabled:
            warning = ("Cannot use RTBox when statusBox is on ")
            raise AssertionError(warning)

        # If mode is not None then use the supplied Mode otherwise use the preset mode.
        if mode != None:
            self.RTBoxMode = mode
        # If self.RTBoxMode has still not be set to something set it to the default: 'down','CB6','trigger'
        if self.RTBoxMode == None:
            self.setRTBoxMode
        # If 'Up' is not in mode adds a 'Down' just in case no direction has been set at all.
        if (('Up' not in self.RTBoxMode)  
                and ('up' not in self.RTBoxMode)):
            self.RTBoxMode.append('Down')
        self.RTBoxResetKeys() # reset all the button - input mappings.
        # If map is not None the mapping provided will over ride any presets given
        # by mode, otherwise use the present mappings below.
        if map is None:
            if 'CB6' in self.RTBoxMode:
                self.sendMessage(b'$btn1 =[IRButtonA]\r')
                self.sendMessage(b'$btn2 =[IRButtonB]\r')
                self.sendMessage(b'$btn3 =[IRButtonC]\r')
                self.sendMessage(b'$btn4 =[IRButtonD]\r')
                self.sendMessage(b'$light =[IRButtonE]\r')
                self.sendMessage(b'$pulse =[IRButtonF]\r')
                # will now add pulse and light to mode
                # as required to read more than 4 inputs.
                self.RTBoxMode.append('Pulse') 
                self.RTBoxMode.append('Light')
            # For a 3 or 6 button box wired to the DINs
            if 'IO' in self.RTBoxMode: 
                self.sendMessage(b'$btn1 =[Din0]\r')
                self.sendMessage(b'$btn2 =[Din1]\r')
                self.sendMessage(b'$btn3 =[Din2]\r')
            # Add 3 more buttons wired to the DINs
            if 'IO6' in self.RTBoxMode:
                self.sendMessage(b'$btn4 =[Din3]\r')
                self.sendMessage(b'$light =[Din4]\r')
                self.sendMessage(b'$pulse =[Din5]\r')
                # will now add pulse and light to mode.
                # as required to read more than 4 inputs.
                self.RTBoxMode.append('Pulse') 
                self.RTBoxMode.append('Light')
            # Add the TrigIn input as a possible event.
            if (('Trigger' in self.RTBoxMode)
                 or ('trigger' in self.RTBoxMode)):
                self.sendMessage(b'$trigger =[TrigIn]\r')
        else:
            self.RTBoxSetKeys(map) # Set up a bespoke mapping
            
        self.sendMessage('X') # Advanced mode turns timestamping on
        time.sleep(0.1)
        msg=self.read(0.1)
        # Assumes that BitsSharp and Display++ return BOX as part of
        # their ID in respect of RTBox style commands.
        if b'BOX' in msg: 
            smsg=msg.split(b',')
            self.RTBoxTimeBase = float(smsg[1]) # Get the timebase for timestamps
            logging.debug("Put RTBox into advanced mode: box ID = %s" %(msg))
        else:
            raise Exception("Cannot get RTBox into "
                             "advanced mode - this is needed for timestamping")
        if (('Down' in self.RTBoxMode)
                 or ('down' in self.RTBoxMode)):
            self.sendMessage('D')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'D':
                logging.debug("Put RTBox into key down mode")
            else:
                raise Exception("Cannot get RTBox into key down mode")
        if (('Up' in self.RTBoxMode)
                 or ('up' in self.RTBoxMode)):
            self.sendMessage('U')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'U':
                logging.debug("Put RTBox into key up mode")
            else:
                raise Exception("Cannot get RTBox into key up mode")
        if (('Trigger' in self.RTBoxMode)
                 or ('trigger' in self.RTBoxMode)):
            self.sendMessage('F')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'F':
                logging.debug("Put RTBox into TR mode")
            else:
                raise Exception("Cannot get RTBox into TR mode")
        if (('Light' in self.RTBoxMode)
                 or ('light' in self.RTBoxMode)):
            self.sendMessage('O')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'O':
                logging.debug("Put RTBox into Light mode")
            else:
                raise Exception("Cannot get RTBox into Light mode")
        if (('Pulse' in self.RTBoxMode)
                 or ('pulse' in self.RTBoxMode)):
            self.sendMessage('P')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'P':
                logging.debug("Put RTBox into Pulse mode")
            else:
                raise Exception("Cannot get RTBox into Pulse mode")
        self.RTBoxEnabled = True
        logging.debug("RTBox emulation enabled")
        self.RTBoxClear()

    def RTBoxDisable(self):
        """ Disables the detection of RTBox events.
        This is useful to stop the Bits# from reporting key presses
        When you no longer need them. Nad must be done before using any
        other data logging methods.
        
        It undoes any button - input mappings.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        
        The ability to reset keys mappings has been found not to work
        on some Bits# firmware.
        """
        if self.noComms:
            self.RTBoxEnabled = False
            return
        self.flush()
        if (('Down' in self.RTBoxMode)
                 or ('down' in self.RTBoxMode)):
            self.sendMessage('d')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'd':
                logging.debug("Take RTBox out of key down mode")
            else:
                raise Exception("Cannot take RTBox out of key down mode")
        if (('Up' in self.RTBoxMode)
                 or ('up' in self.RTBoxMode)):
            self.sendMessage('u')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'u':
                logging.debug("Take RTBox out of key up mode")
            else:
                raise Exception("Cannot take RTBox out of key up mode")
        if (('Trigger' in self.RTBoxMode)
                 or ('trigger' in self.RTBoxMode)):
            self.sendMessage('f')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'f':
                logging.debug("Take RTBox out of TR mode")
            else:
                raise Exception("Cannot take RTBox out of TR mode")
        if (('Light' in self.RTBoxMode)
                 or ('light' in self.RTBoxMode)):
            self.sendMessage('o')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'o':
                logging.debug("Take RTBox out of Light mode")
            else:
                raise Exception("Cannot take RTBox out of Light mode")
        if (('Pulse' in self.RTBoxMode)
                 or ('pulse' in self.RTBoxMode)):
            self.sendMessage('p')
            time.sleep(0.1)
            msg = self.read(0.1)
            if msg == b'p':
                logging.debug("Take RTBox out of Pulse mode")
            else:
                raise Exception("Cannot take RTBox out of Pulse mode")
            self.RTBoxClear()
        #Reset the button mappings
        self.RTBoxResetKeys()
        self.RTBoxClear()
        self.RTBoxEnabled = False
        logging.debug("RTBox emulation disabled")

    def RTBoxResetKeys(self):
        """ Resets the key mappings to no mapping.
        Has the effect of disabling RTBox input.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        
        The ability to reset keys mappings has been found not to work
        on some Bits# firmware.
        """
        if self.noComms:
            return
        self.sendMessage(b'$btn1 =[null]\r')
        self.sendMessage(b'$btn2 =[null]\r')
        self.sendMessage(b'$btn3 =[null]\r')
        self.sendMessage(b'$btn4 =[null]\r')
        self.sendMessage(b'$light =[null]\r')
        self.sendMessage(b'$pulse =[null]\r')
        self.sendMessage(b'$trigger =[null]\r')
        logging.debug("All RTBOX buttons disconnected")
        
    def RTBoxSetKeys(self,map):
        """ Set key mappings: first resets existing then adds new ones.
        Does not reset any event that is not in the new list.
        RTBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, triggers and CB6 IR input channels.
        The format for map is a list of tuples with each tuple containing the name of the 
        RTBox button to be mapped and its source eg ('btn1','Din1') maps physical input Din1 to 
        logical button btn1.
        
        RTBox has four logical buttons (btn1-4) and three auxiliary events (light, pulse and trigger)
        Buttons/events can be mapped to multiple physical inputs and stay mapped until reset.
        
        Example:
            bits.RTBoxSetKeys([('btn1','Din0),('light','Din9')])
            
        Will link Din0 to button 1 and Din9 to the the light input emulation.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        
        """
        if self.noComms:
            return
        for mapping in map:
            # reset the mapping.
            str = '$'+mapping[0]+'=[null]\r'
            self.sendMessage(str)
            # Construct and send new mapping string
            str = '$'+mapping[0]+'=['+mapping[1]+']\r'
            self.sendMessage(str)
            
    def RTBoxAddKeys(self,map):
        """ Add key mappings to an existing map.
        RTBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, triggers and CB6 IR input channels.
        The format for map is a list of tuples with each tuple containing the name of the 
        RTBox button to be mapped and its source eg ('btn1','Din1') maps physical input Din1 to 
        logical button btn1.
        RTBox has four logical buttons (btn1-4) and three auxiliary events (light, pulse and trigger)
        Buttons/events can be mapped to multiple physical inputs and stay mapped until reset.
        
        
        Example::

            bits.RTBoxSetKeys([('btn1','Din0),('btn2','Din1')])
            bits.RTBoxAddKeys([('btn1','IRButtonA'),(('btn2','IRButtonB')])
            
        Will link Din0 to button 1 and Din1 to button 2.
        Then adds IRButtonA and IRButtonB alongside the original mappings.
        
        Now both hard wired and IR inputs will - emulating the same logical button press.

        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        
        """
        if self.noComms:
            return
        for mapping in map:
            # Construct and send new mapping string
            str = '$'+mapping[0]+'=['+mapping[1]+']\r'
            self.sendMessage(str)

    def RTBoxCalibrate(self,N=1):
        """ Used to assess error between host clock and Bits# 
        button press time stamps.
        
        Prints each sample provided and returns the mean error.
        
        The clock willnever be completely in sync but the aim is that there
        should be that the difference between them should not grow over
        a serise of button presses.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.

        """
        
        print("Calibrating Bits Button box: Press button %d times" %(N))
        drift=0;
        HostClock=core.Clock()
        # Sync the 2 clocks as best they can be by resetting them both.
        self.syncClocks(HostClock)
        # Measure the difference between the stime stamps provided by N
        # Button presses and the host clock equivalents.
        for sample in range(0, N):
            msg = self.RTBoxWait()
            if msg:
                tH = HostClock.getTime()
                tB = msg.time
                drift = drift+tH-tB
                print (sample, tB, tH, tH-tB)
            else:
                drift = 0
        return drift/N


    def getRTBoxResponses(self, N=1):
        """ checks for (at least) an appropriate number of 
        RTBox style key presses on the input buffer then reads them.
        Returns a list of dict like objects with three members 
        'button', 'dir' and 'time'
        
        'button' is a number from 1 to 9 to indicate the event that 
        was detected.
        1-4 are the 'btn1-btn4' events, 5 and 6 are the 
        'light' and 'pulse' events,
        7 is the 'trigger' event, 
        9 is a requested timestamp event (see Clock()).
        
        'dir' is the direction of the event eg 'up' or 'down', 
        trigger is described as 'on' when low.
        
        'dir' is set to 'time' if a requested 
        timestamp event has been detected.
        
        'time' is the timestamp associated with the event.
        
        Values can be read as a list of structures eg::

            res = getRTBoxResponses(3)
            res[0].dir, res[0].button, res[0].time

        or dictionaries::

            res[0]['dir'], res[0]['button'], res[0]['time']
            
        Note even if only 1 key press was requested 
        a list of dict / objects is returned.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        
        """
        if self.noComms:
            return
        if  self._inWaiting() > (N*7-1):
            msg = self.read()
            return self._RTBoxDecodeResponse(msg,N)
        else:
            return

    def getRTBoxResponse(self):
        """ checks for one RTBox style key presses on the input 
        buffer then reads it.
        Returns a dict like object with three members 
        'button', 'dir' and 'time'
        
        'button' is a number from 1 to 9 to indicate the event that 
        was detected.
        1-4 are the 'btn1-btn4' events, 5 and 6 are the 
        'light' and 'pulse' events,
        7 is the 'trigger' event, 
        9 is a requested timestamp event (see Clock()).
        
        'dir' is the direction of the event eg 'up' or 'down', 
        trigger is described as 'on' when low.
        
        'dir' is set to 'time' if a requested 
        timestamp event has been detected.
        
        'time' is the timestamp associated with the event.
        
        Value can be read as a structure, eg:
            res= getRTBoxResponse()
            res.dir, res.button, res.time
        or dictionary
            res['dir'], res['button'], res['time']
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        """    

        self.getRTBoxResponses(1)
        if self.nRTPresses>0:
            op=self.RTButtons[0]
            return op
        else:
            return 

    def getAllRTBoxResponses(self):
        """ Read all of the RTBox style key presses on the 
        input buffer.
        Returns a list of dict like objects with three members 
        'button', 'dir' and 'time'
        
        'button' is a number from 1 to 9 to indicate the event that 
        was detected.
        1-4 are the 'btn1-btn4' events, 5 and 6 are the 
        'light' and 'pulse' events,
        7 is the 'trigger' event, 
        9 is a requested timestamp event (see Clock()).
        
        'dir' is the direction of the event eg 'up' or 'down', 
        trigger is described as 'on' when low.
        
        'dir' is set to 'time' if a requested 
        timestamp event has been detected.
        
        'time' is the timestamp associated with the event.
        
        Values can be read as a structure eg::

            res = getAllRTBoxResponses()
            res[0].dir, res[0].button, res[0].time

        or dictionary::

            res[0]['dir'], res[0]['button'], res[0]['time']
            
        Note even if only 1 key press was found 
        a list of dict / objects is returned
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        """
        
        N=int(self._inWaiting()/7)
        return self.getRTBoxResponses(N)
    
    def RTBoxKeysPressed(self,N=1):
        """Check to see if (at least) the appropriate number 
        of RTBox style key presses have been made.
        
        Example:
            bits.RTBoxKeysPressed(5)
            
        will return false until 5 button presses have been recorded.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        """
        #7 is number of bytes for one press
        if self._inWaiting() > 7*N - 1: 
            return True
        else:
            return False
    
    def RTBoxWaitN(self, N=1):
        """Waits until (at least) the appropriate number 
        of RTBox style key presses have been made 
        Pauses program execution in mean time.
        
        Example:
            res = bits.RTBoxWaitN(5) 
            
        will suspend all other activity until 5 button presses have been
        recorded and will then return a list of Dicts containing the 5 results.
        
        Results can be accessed as follows:
            
        structure
            res[0].dir, res[0].button, res[0].time
        or dictionary
            res[0]['dir'], res[0]['button'], res[0]['time']

        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        """
        if self.noComms:
            return
        while self._inWaiting() < 7*N:
            continue # ie loop
        return self.getRTBoxResponses(N)

    def RTBoxWait(self):
        """Waits until (at least) one 
        of RTBox style key presses have been made 
        Pauses program execution in mean time.
        
        Example:
            res = bits.RTBoxWait() 
            
        will suspend all other activity until 1 button press has been
        recorded and will then return a dict / structure containing results.
        
        Results can be accessed as follows:
            
        structure
            res.dir, res.button, res.time
        or dictionary
            res['dir'], res['button'], res['time']
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. Such variations may affect key mappings for RTBox
        commands.
        """
        if self.noComms:
            return
        while self._inWaiting() < 7:
            continue # ie loop
        return self.getRTBoxResponse()

    def clock(self):
        """ Reads the internal clock of the Bits box via the RTBox
        fortmat but note there will be a delay in reading the value 
        back. The fortmat for the return values is the same as for
        button box presses. The return value for button will be 9 and
        the return value for event will be time. The return value for
        time will be the time of the clock at the moment of the request.
        
        Example:
            res = bits.clock()
            print(res.time)
            print(res['time'])
        
        """
        self.RTBoxClear()
        self.sendMessage('Y')
        return self.RTBoxWait()

    # Helper function for RTBox commands #
    def _RTBoxDecodeResponse(self,msg,N=1):
        """ Helper function for decoding key presses in the 
        RT response box format.
        
        Not normally needed by user
        """
        
        self.RTButtons = [button() for i in range(N)]
        self.nRTPresses = N
        EV=0
        for index in range(0,N):
            t=0
            # The RTBox serial input format is quite primitive
            # This is a hack to make work in different versions of Python 
            # There may be a better way!
            if sys.version_info[0] == 3: 
                for i in range(index*7 + 1,index*7 + 7):
                    # i is ofset by index*7 so this is subtracted from 7 in line
                    # below and then reinstated by adding index*7 back in.
                    t = t+ord(chr(msg[i])) * 256**(7-i + index*7 -1)
                t = t / self.RTBoxTimeBase 
                if chr(msg[0]) == 'Y':
                    event = 9
                else:
                    event = ord(chr(msg[index*7]))
            else:
                raise AssertionError("Bits# RTBox Only tested for PY3")
            Direction = 'None'
            EV=99
            # Decode event bytes into a button number and a direction.
            # Calls to read the clock are a special case.
            if event == 9:
                Direction = 'time'
                EV = 9
            # Odd numbered events 49 - 55 are the down events for the 4 btn inputs
            # Decoded to button = 1 -4 and direction = down.
            if event == 49:
                Direction = 'down'
                EV = 1
            if event == 51:
                Direction = 'down'
                EV = 2
            if event == 53:
                Direction = 'down'
                EV = 3
            if event == 55:
                Direction = 'down'
                EV = 4
            # Even numbered events 50 - 56 are the down events for the 4 btn inputs
            # Decoded to button = 1 -4 and direction = up.
            if event == 50:
                Direction = 'up'
                EV = 1
            if event == 52 :
                Direction = 'up'
                EV = 2
            if event == 54:
                Direction = 'up'
                EV= 3
            if event == 56:
                Direction = 'up'
                EV = 4
            # Event 48 is the pulse event - down only
            # Decoded to button = 5, direction = down
            if event == 48:
                Direction = 'down'
                EV = 5
            # Event 57 is the light event - down only
            # Decoded to button = 6, direction = down
            if event == 57:
                Direction = 'down'
                EV= 6
            # Event 97 is the Trigger event
            # Decoded to button = 7, direction = on
            if event == 97:
                Direction = 'on'
                EV = 7
            self.RTButtons[index].dir = Direction
            self.RTButtons[index].button = EV
            self.RTButtons[index].time = t
        return self.RTButtons

    #====================================================================#
    #   'statusBox' functions use BitsSharp status reporting to          #
    #   emulate a button box.                                            #
    #====================================================================#

    def setStatusBoxMode(self, mode=['CB6','Down','Trigger','Analog']):
        """ Sets the statusBox mode data member - does not
        actually set the statusBox into this mode.
        
        Example:
            bits.setStatusBoxMode(['CB6','Down']) # set the mode
            bits.statusBoxEnable() # Enable status Box emulation with
            # the preset mode.
        
        sets the statusBox mode settings for a CRS CB6 button box.
        and for detection of 'Down' events only.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        self.statusBoxMode = mode
        
    def setStatusBoxThreshold(self, threshold=None):
        """ Sets the threshold by which analog inputs must change to trigger a button 
        press event. If None the threshold will be set very high so that no such events are
        triggered.
        
        Can be used to change the threshold for analog events without having to re enable the
        status box system as a whole.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        if threshold != None:
            self.statusBoxThreshold = threshold
        else:
            self.statusBoxThreshold = 9999.99  # set impossibly high to block events.

    def statusBoxEnable(self, mode=None, map=None, threshold=None):
        """ Sets up the stautsBox with preset or bespoke mappings 
        and enables event detection.
        
        stautsBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, tigers and
        CB6 IR input channels.
        
        mode is a list of strings.
        Preset mappings provided via mode:

            - CB6 for the CRS CB6 IR response box connected mapped to btn1-6
            - IO for a three button box connected to Din0-2 mapped to btn1-3
            - IO6 for a six button box connected to Din0-5 mapped to btn1-6
            - IO10 for a ten button box connected to Din0-9 mapped to btn1-10
            - Trigger maps the trigIn to btn17
            - Analog maps the 6 analog inputs on a Bits# to btn18-23
            
        If CB6 and IOx are used together the Dins are mapped from btn7 onwards.
            
        If mode = None or is not set then the value of self.statusBoxMode is used.

        Bespoke Mappings overwrite preset ones.
        
        The format for map is a list of tuples with each tuple 
        containing the name of the 
        button to be mapped and its source 
        eg ('btn1','Din0') maps physical input Din0 to 
        logical button btn1. 
        
        Note the lowest number button event is Btn1
        
        statusBox has 23 logical buttons (btn1-123).
        Buttons/events can be mapped to multiple physical
        inputs and stay mapped until reset.
        
        mode is a string or list of strings that contains 
        keywords to determine present mappings and modes for statusBox.
        
        If mode includes 'Down' button events will be 
        detected when pressed.
        If mode includes 'Up' button events will be 
        detected when released.
        You can detect both types of event noting that the event detector
        will look for transitions and ignorewhat it sees as the starting state.
        
        To match with the CRS hardware description inputs are labelled as follows.
        
        TrigIn, Din0 ... Din9, IRButtonA ... IRButtonF, AnalogIn1 ... AnalogIn6
        
        Logical buttons are numbered from 1 to 23.
        
        threshold sets the threshold by which analog inputs must change to trigger a button 
        press event. If None the threshold will be set very high so that no such events are
        triggered. Analog inputs must cycle up and down by threshold to be detected as separate
        events. So if only 'Up' events are detected the input must go up by threshold, then come
        down again and then go back up to register 2 up events.
            
        Example::

            bits.statusBoxEnable(mode = 'Down'), map = [('btn1','Din0'), ('btn2','Din1')]
            
        enables the stautsBox to detect Down events on buttons 1 and 2 where they are
        mapped to DIN0 and DIN1.
        
        Example::

            bits.statusBoxEnable(mode = ['Down','CB6'])
        
        enables the status Box emulation to detect Down events on the standard CB6 IR response box keys.
        
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        if self.noComms:
            return

        if self.statusEnabled:
            warning = ("Cannot use statusBox when status logging "
                       " is on")
            raise AssertionError(warning)
            
        if self.RTBoxEnabled:
            warning = ("Cannot use statusBox when RTBox is on ")
            raise AssertionError(warning)
            
        # If threshold is not None use the supplied value as the threshold for analog events.
        if threshold != None:
            self.statusBoxThreshold = threshold
        else:
            self.statusBoxThreshold = 9999.99  # set impossibly high to block events.

        # If mode is not None then use the supplied Mode otherwise use the preset or default mode.
        if mode != None:
            self.statusBoxMode = mode
        self.statusBoxResetKeys() # reset all the button - input mappings.

        # If map is not None the mapping provided will over ride any presets given
        # by mode, otherwise use the present mappings below.
        
        self.statusButtonMap = [99]*23
        
        if map == None:
            DinBaseButton = 1
            if 'CB6' in self.statusBoxMode:
                # position in status line = logical button number
                self.statusButtonMap[11] = 1
                self.statusButtonMap[12] = 2
                self.statusButtonMap[13] = 3
                self.statusButtonMap[14] = 4
                self.statusButtonMap[15] = 5
                self.statusButtonMap[16] = 6
                DinBaseButton = 7
            # For a 3 button box wired to the DINs
            if 'IO' in self.statusBoxMode:
                self.statusButtonMap[1] = 0+DinBaseButton
                self.statusButtonMap[2] = 1+DinBaseButton
                self.statusButtonMap[3] = 2+DinBaseButton
            # Add 3 more buttons wired to the DINs
            if 'IO6' in self.statusBoxMode:
                self.statusButtonMap[4] = 3+DinBaseButton
                self.statusButtonMap[5] = 4+DinBaseButton
                self.statusButtonMap[6] = 5+DinBaseButton
            # Add all the Dins to the button list
            if 'IO10' in self.statusBoxMode:
                self.statusButtonMap[7] = 6+DinBaseButton
                self.statusButtonMap[8] = 7+DinBaseButton
                self.statusButtonMap[9] = 8+DinBaseButton
                self.statusButtonMap[10] = 9+DinBaseButton
            if (('Trigger' in self.statusBoxMode)
                 or ('trigger' in self.statusBoxMode)):
                self.statusButtonMap[0] = 17
            if (('Analog' in self.statusBoxMode)
                 or ('analog' in self.statusBoxMode)):
                self.statusButtonMap[17] = 18
                self.statusButtonMap[18] = 19
                self.statusButtonMap[19] = 20
                self.statusButtonMap[20] = 21
                self.statusButtonMap[21] = 22
                self.statusButtonMap[22] = 23
        else:
            self.statusBoxSetKeys(map) # Set up a bespoke mapping
        self.statusBoxEnabled = True
        logging.debug("statusBox emulation enabled")
        self.flush()
        
        #time = 60
        
        # Enable status reading 
        self.statusThread=threading.Thread(target=self._statusBox)
        self.statusBoxEnd = False
        self._statusEnable()
        self.statusThread.start()

    def statusBoxDisable(self):
        """ Disables the detection of statusBox events.
        This is useful to stop the Bits# from reporting key presses
        When you no longer need them. And must be done before using any
        other data logging methods.
        
        It undoes any button - input mappings
        """
        if self.noComms:
            self.statusBoxEnabled = False
            return
        
        # disable code here
        self.statusBoxEnd = True # This semaphore will tell the status logging thread to stop.
        self.statusThread.join() # Join the thread and wait for it to finish.
        del self.statusThread
        
        self.flush()
        self.statusBoxResetKeys()
        self.statusBoxEnabled = False
        logging.debug("statusBox emulation disabled")
        
    def statusBoxResetKeys(self):
        self.statusButtons = [99]*23
        
    def statusBoxSetKeys(self,map):
        """ Set key mappings: first resets existing then adds new ones.
        Does not reset any event that is not in the new list.
        statusBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, triggers and CB6 IR input channels.
        The format for map is a list of tuples with each tuple containing the name of the 
        RTBox button to be mapped and its source eg ('btn1','Din1') maps physical input Din1 to 
        logical button btn1.
        
        statusBox has 17 logical buttons (btn1-17) 
        Buttons/events can be mapped to multiple physical inputs and stay mapped until reset.
        
        Example:
            bits.RTBoxSetKeys([('btn1','Din0),('btn2','IRButtonA')])
            
        Will link physical Din0 to logical button 1 and IRButtonA to button 2.
        
        To match with the CRS hardware description inputs are labelled as follows.
        
        TrigIn, Din0 ... Din9, IRButtonA ... IRButtonF, AnalogIn1 ... AnalogIn6
        
        Logical buttons are numbered from 1 to 23.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        
        self.statusBoxResetKeys()
        self.statusBoxAddKeys(map)
    
        
    def statusBoxAddKeys(self,map):
        """ Add key mappings to an existing map.
        statusBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, triggers and CB6 IR input channels.
        The format for map is a list of tuples with each tuple containing the name of the 
        RTBox button to be mapped and its source eg ('btn1','Din1') maps physical input Din1 to 
        logical button btn1.
        statusBox has 23 logical buttons (btn1-23).
        Unlike RTBox buttons/events can only be partially mapped to multiple physical inputs.
        That is a logical button can be mapped to more than 1 physical input but a physical input
        can onloy be mapped to 1 logical button.
        So, this function over write any existing mappings if the physical input is the
        same.
        
        
        Example::
        
            bits.RTBoxSetKeys([('btn1','Din0),('btn2','Din1')])
            bits.RTBoxAddKeys([('btn1','IRButtonA'),(('btn2','IRButtonB')])
            
        Will link Din0 to button 1 and Din1 to button 2.
        Then adds IRButtonA and IRButtonB alongside the original mappings.
        
        Now both hard wired and IR inputs will emulate the same logical button press.
        
        To match with the CRS hardware description inputs are labelled as follows.
        
        TrigIn, Din0 ... Din9, IRButtonA ... IRButtonF, AnalogIn1 ... AnalogIn6
        
        Logical buttons are numbered from 1 to 23.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """        # reset the mapping
        for mapping in map:
            btn = int(mapping[0][3])
            if mapping[1][0] == 'I':  # IR input
                # A = 65 so ord(chr)-65+11 is the 11th status input etc
                # status inputs will be adjusted later to match true position.
                sourse = ord(mapping[1][-1])-65+11
            if mapping[1][0] == 'D': # Digital input
                source = int(mapping[1][-1])+1
            if mapping[1][0] == 'T': # Trigger input
                source = 0
            if mapping[1][0] == 'A': # Analog input
                source = int(mapping[1][-1])+16
            self.statusButtonMap[sourse] = btn

    def getStatusBoxResponses(self, N=1):
        """ checks for (at least) an appropriate number of 
        RTBox style key presses on the input buffer then reads them.
        Returns a list of dict like objects with three members 
        'button', 'dir' and 'time'
        
        'button' is a number from 1 to 9 to indicate the event that 
        was detected.
        1-4 are the 'btn1-btn4' events, 5 and 6 are the 
        'light' and 'pulse' events,
        7 is the 'trigger' event, 
        9 is a requested timestamp event (see Clock()).
        
        'dir' is the direction of the event eg 'up' or 'down', 
        trigger is described as 'on' when low.
        
        'dir' is set to 'time' if a requested 
        timestamp event has been detected.
        
        'time' is the timestamp associated with the event.
        
        Values can be read as a list of structures eg::

            res = getRTBoxResponses(3)
            print(res[0].dir, res[0].button, res[0].time)

        or dictionaries::

            print(res[0]['dir'], res[0]['button'], res[0]['time'])
            
        Note even if only 1 key press was requested 
        a list of dict / objects is returned.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        
        if self.noComms: # If we have no commes there will nothing to read
            return
        if  self.statusQ.qsize() > N - 1:
            res = [button() for  i in range(N)] 
            # get the required number of button presses off the queue
            for i in range(N):
                res[i] = self.statusQ.get()
            # empty the queue of everything else
            while not self.statusQ.empty():
                dummy = self.statusQ.get()
            self.nStatusPresses = N
            self.statusButtons = res
            return res
        else:
            return

    def getStatusBoxResponse(self):
        """ checks for one statusBox style key presses on the input 
        buffer then reads it.
        Returns a dict like object with three members 
        'button', 'dir' and 'time'
        
        'button' is a number from 1 to 9 to indicate the event that 
        was detected.
        1-17 are the 'btn1-btn17' events.
        
        'dir' is the direction of the event eg 'up' or 'down', 
        trigger is described as 'on' when low.
        
        'dir' is set to 'time' if a requested 
        timestamp event has been detected.
        
        'time' is the timestamp associated with the event.
        
        Value can be read as a structure, eg:
            res= getRTBoxResponse()
            res.dir, res.button, res.time
        or dictionary
            res['dir'], res['button'], res['time']
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """    

        self.getStatusBoxResponses(1)
        if self.nStatusPresses>0:
            op=self.statusButtons[0]
            return op
        else:
            return 

    def getAllStatusBoxResponses(self):
        """ Read all of the statusBox style key presses on the 
        input buffer.
        Returns a list of dict like objects with three members 
        'button', 'dir' and 'time'
        
        'button' is a number from 1 to 9 to indicate the event that 
        was detected.
        1-17 are the 'btn1-btn17' events.
        
        'dir' is the direction of the event eg 'up' or 'down', 
        trigger is described as 'on' when low.
        
        'dir' is set to 'time' if a requested 
        timestamp event has been detected.
        
        'time' is the timestamp associated with the event.
        
        Values can be read as a structure eg::

            res= getAllStatusBoxResponses()
            res[0].dir, res[0].button, res[0].time

        or dictionary::

            res[0]['dir'], res[0]['button'], res[0]['time']
            
        Note even if only 1 key press was found 
        a list of dict / objects is returned.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        
        N=self.statusQ.qsize()
        return self.getStatusBoxResponses(N)
    
    def statusBoxKeysPressed(self,N=1):
        """Check to see if (at least) the appropriate number 
        of RTBox style key presses have been made.
        
        Example:
            bits.statusBoxKeysPressed(5)
            
        will return false until 5 button presses have been recorded.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        #7 is number of bytes for one press
        if self.statusQ.qsize() > N - 1: 
            return True
        else:
            return False
    
    def statusBoxWaitN(self, N=1):
        """Waits until (at least) the appropriate number 
        of RTBox style key presses have been made 
        Pauses program execution in mean time.
        
        Example:
            res = bits.statusBoxWaitN(5) 
            
        will suspend all other activity until 5 button presses have been
        recorded and will then return a list of Dicts containing the 5 results.
        
        Results can be accessed as follows:
            
        structure::

            res[0].dir, res[0].button, res[0].time

        or dictionary::

            res[0]['dir'], res[0]['button'], res[0]['time']
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        if self.noComms:
            return
        while self.statusQ.qsize() < N:
            continue # ie loop
        return self.getStatusBoxResponses(N)

    def statusBoxWait(self):
        """Waits until (at least) one 
        of RTBox style key presses have been made 
        Pauses program execution in mean time.
        
        Example:
            res = bits.statusBoxWait() 
            
        will suspend all other activity until 1 button press has been
        recorded and will then return a dict / structure containing results.
        
        Results can be accessed as follows:
            
        structure
            res.dir, res.button, res.time
        or dictionary
            res['dir'], res['button'], res['time']
            
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also DBits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        if self.noComms:
            return
        while self.statusQ.empty():
            continue # ie loop
        return self.getStatusBoxResponse()

    #====================================================================#
    #   Helper function to run in its own thread detecting statusBox     #
    #   events and putting them in a queue                               #
    #====================================================================#

    def _statusBox(self):
        """ Should not normally be called by user
        Called in its own thread via self.statusBoxEnable()
        Reads the status reports from the Bits# for default 60 seconds or
        until self.statusBoxDisable() is called.
 
        Note any non status reports are found on the buffer will 
        cause an error.
        
        args specifies the time over which to record status events.
        The minimum time is 10ms, less than this results in recording stopping after 
        about 1 status report has been read.
        
        Puts its results into a Queue.
        
        This function is normally run in its own thread so actions can be asynchronous.
        

        """


        # Continue reading data until sample time is up or status.End is set
        # Note when used in thread statusEnd can be set from outside this function.
        firstIn = True # we do something different for the very first status entry
        while (self.statusBoxEnd == False): 
            self.com.timeout = 0.01
            raw=""
            nChars = self._inWaiting()
            if nChars >= self._statusSize:  # we many have a status report
                # use self.com.read() to get exact number of chars
                raw = self.com.read(nChars) 
                msg=raw.decode("utf-8")
                # just in case split message into status lines marked by CR
                lines = msg.split('\r') 
                N = len(lines) 
                values = [button() for  i in range(N)] 
                for i in range(N-1): # for each status line
                    # split line into component parts marked by ;
                    v=lines[i].split(';') 
                    if v[0] == '#sample': # Check we have read a status line
                        if not firstIn: # Not first status entry
                            # Check digital inputs
                            for sourse in range(17):
                                # if input has changed and input is mapped
                                if (v[3+sourse] != log[3+sourse] 
                                    and self.statusButtonMap[sourse] < 24): 
                                    if ('Down' in self.statusBoxMode
                                            or 'down'  in self.statusBoxMode):
                                        if int(v[3+sourse]) == 0:
                                            values[i].button = (
                                                    self.statusButtonMap[sourse])
                                            values[i].time = float(v[2])
                                            values[i].dir = 'down'
                                            self.statusQ.put(values[i])
                                    if ('Up' in self.statusBoxMode
                                            or 'up'  in self.statusBoxMode):
                                        if int(v[3+sourse]) == 1:
                                            values[i].button = (
                                                    self.statusButtonMap[sourse])
                                            values[i].time = float(v[2])
                                            values[i].dir = 'up'
                                            self.statusQ.put(values[i])
                                    # save new state of sourse
                                    log[3+sourse] = v[3+sourse] 
                            # Check analog inputs
                            for analog in range(6):
                                sourse = analog + 17
                                fLog = float(log[3+sourse])
                                fVal = float(v[3+sourse])
                                # if input has changed enough and input is mapped
                                if (abs(fVal - fLog)
                                    > self.statusBoxThreshold
                                    and self.statusButtonMap[sourse] < 24): 
                                    if ('Down' in self.statusBoxMode
                                            or 'down'  in self.statusBoxMode):
                                        # Is change of input in downward direction
                                        if fLog > fVal:
                                            values[i].button = (
                                                    self.statusButtonMap[sourse])
                                            values[i].time = float(v[2])
                                            values[i].dir = 'down'
                                            self.statusQ.put(values[i])

                                    if ('Up' in self.statusBoxMode
                                            or 'up'  in self.statusBoxMode):
                                        # Is change of input in upward direction
                                        if fVal > fLog:
                                            values[i].button = (
                                                    self.statusButtonMap[sourse])
                                            values[i].time = float(v[2])
                                            values[i].dir = 'up'
                                            self.statusQ.put(values[i])
                                    # save new state of sourse
                                    log[3+sourse] = v[3+sourse] 
                        else: # this is the first entry
                            log = deepcopy(v) # make a copy of status entry
                            firstIn = False
                    elif v[0] == '$touch': # We've read a screen touch event by mistake.
                        warning = ("_statusBox found touch" 
                                " data on input so skipping that")
                        logging.warning(warning)
                    else: # We've read something we can't interpret.
                        warning = ("_statusBox found unknown data"
                                " on input so skipping that")
                        logging.warning(warning)
                        
        # clearn up when stop is called.
        # Send stop signal to CRS device to shut it up.
        self._statusDisable() # Send stop signal to CRS device to shut it up.
        self.statusBoxEnd = True # Confirm that data logging has ended.
        self.flush()

    #====================================================================#
    #    'status' functions use BitsSharp status reporting to read the   #
    #    digital IO, IR channels                                         #
    #    and analog inputs via a separate thread                          #
    #====================================================================#

    def setStatusEventParams(self, DINBase=0b1111111111, 
                                      IRBase=0b111111, 
                                      TrigInBase=0,
                                      ADCBase=0,
                                      threshold=9999.99,
                                      mode=['up','down']):
        """ Sets the parameters used to determine if a status value represents
        a reportable event.
        
        DIN_base = a 10 bit binary word specifying the expected starting 
        values of the 10 digital input lines
        
        IR_base = a 6 bit binary word specifying the expected starting 
        values of the 6 CB6 IR buttons
        
        Trig_base = the starting value of the Trigger input
        
        mode = a list of event types to monitor can be 'up' or  'down' 
        typically 'down' corresponds to a button press or when the input
        is being pulled down to zero volts.
        
        Example::

            bits.setStatusEventParams(DINBase=0b1111111111, 
                                      IRBase=0b111111, 
                                      TrigInBase=0, 
                                      ADCBase=0,
                                      threshold = 3.4,
                                      mode = ['down'])
            bits.startStatusLog()
            while not event
                #do some processing
                continue
            bits.stopStatusLog()
            res=getAllStatusEvents(0)
            print(bits.res.time)
            
        This ill start the event extraction process as if DINs and IRs are all '1', Trigger is '0'
        ADCs = 0 with an ADC threshold for change of 3.4 volts,
        and will only register 'down' events. Here we display the time stamp of the first event.
        
        Note that the firmware in Display++ units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Display++ units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        self.statusDINBase = DINBase   # Initial values for ditgial ins
        self.statusIRBase = IRBase        # Initial values for CB6 IR box
        self.statusTrigInBase = TrigInBase           # Initial values for TrigIn
        self.statusADCBase = ADCBase           # Initial value for all ADCs
        self.statusThreshold = threshold   # Threshold for ADC events
        self.statusMode = mode     # Direction of events to be reported

    def pollStatus(self, t=0.0001):
        """ Reads the status reports from the Bits# for the specified 
        usually short time period t. The script will wait for this time
        to lapse so not ideal for  time critical applications.
        
        If t is less than 0.01 polling will continue until at least 1
        data entry has been recorded.
        
        If you don't want to wait while this does its job 
        use startStatusLog and stopStatusLog instead.
        
        Fills the statusValues list with all the status values
        read during the time period.
        
        Fills the statusEvents list with just those status values
        that are likely to be meaningful events.
        
        the members statusValues and statusEvents will end up containing 
        dict like objects of the following style:
        sample, time, trigIn, DIN[10], DWORD, IR[6], ADC[6]
        
        They can be accessed as statusValues[i]['sample'] or 
        stautsValues[i].sample, statusValues[x].ADC[j].
        
        Example::

            bits.pollStatus()
            print(bits.statusValues[0].IR[0])
            
        will display the value of the IR InputA in the first sample recorded.

        Note: Starts and stops logging for itself.
        
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        
        self.startStatusLog(t)
        self.statusThread.join()
        self._statusDisable()
        self._getStatusLog()
        self._extractStatusEvents()
        self.flush()
        del self.statusThread

    def startStatusLog(self, t=60):
        """ Start logging data from the Bits#
        
            Starts data logging in its own thread.
            
            Will run for t seconds, defrault 60 or until 
            stopStatusLog() is called.
            
            Example::

                bits.startStatusLog()
                while not event
                    #do some processing
                    continue
                bits.stopStatusLog()
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        
        if self.statusBoxEnabled:
            warning = ("Cannot use status log when statusBox is on ")
            raise AssertionError(warning)
        if self.RTBoxEnabled:
            warning = ("Cannot use status log when RTBox is on ")
            raise AssertionError(warning)
        
        # Try both Py2 and Py3 safe versions
        # The two Python versions seem to want to pass args to threads in different ways.
        try: 
            self.statusThread=threading.Thread(target=self._statusLog,args=(t,))
        except Exception:
            self.statusThread=threading.Thread(target=self._statusLog,args=(t))
        self.statusEnd = False
        self._statusEnable()
        self.statusThread.start()

    def stopStatusLog(self):
        """ Stop logging data from the Bits#
            and extracts the raw status values and significant events and puts them
            in statusValues and statusEvents.
            
            statusValues will end up containing 
            dict like objects of the following style: `sample, time, trigIn, DIN[10], DWORD, IR[6], ADC[6]`
        
            They can be accessed as statusValues[i]['sample'] or 
            statusValues[i].sample, statusValues[x].ADC[j].
            
            StatusEvents will end up containing dict like objects of
            the following style: `source, input, direction, time`
                
            The data can be accessed as statusEvents[i]['time'] or statusEvents[i].time
            
            Waits for _statusLog to finish properly 
            so can introduce a timing delay.
                        
        Example::

            bits.startStatusLog()
            while not event
                #do some processing
                continue
            bits.stopStatusLog()
            print(bits.statusValues[0].time)
            print(bits.statusEvents[0].time)
            
        Will display the time stamps of the first starus value recorded and the first
        meaningful event.


        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        """
        
        self.statusEnd=True # This semaphore will tell the status logging thread to stop.
        self.statusThread.join() # Join the thread and wait for it to finish.
        # Get the stausts values and events form the queue.
        self._getStatusLog()
        self._extractStatusEvents()
        del self.statusThread

    def getAllStatusEvents(self):
        """Returns the whole status event list
        
        Returns a list of dictionary like objects with the following entries
        source, input, direction, time.
        
        source = the general source of the event - e.g. 
        DIN for Digital input, 
        IR for CB6 IR response box events
        
        input = the individual input in the source.
        direction = 'up' or 'down'
        time = time stamp.
        
        All sourses are numbered from zero.
        Din 0 ... 9
        IR 0 ... 5
        ADC 0 ... 5
        
        mode specifies which directions of events are captured. 
        e.g 'up' will only report up events.
        
        The data can be accessed as value[i]['time'] or value[i].time
        
        Example::

            bits.startStatusLog()
            while not event
                #do some processing
                continue
            bits.stopStatusLog()
            res=getAllStatusEvents()
            print(bits.res[0].time)
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        return self.statusEvents

    def getStatusEvent(self, N=0): 
        """ pulls out the Nth event from the status event list
        
        Returns a dictionary like object with the following entries
        source, input, direction, time.
        
        source = the general source of the event - e.g. 
        DIN for Digital input, 
        IR for IT response box.
        
        input = the individual input in the source.
        direction = 'up' or 'down'
        time = time stamp.
        
        All sourses are numbered from zero.
        Din 0 ... 9
        IR 0 ... 5
        ADC 0 ... 5
        
        mode specifies which directions of events are captured, 
        e.g 'up' will only report up events.
        
        The data can be accessed as value['time'] or value.time
        
        Example::

            bits.startStatusLog()
            while not event
                #do some processing
                continue
            bits.stopStatusLog()
            res=getAllStatusEvents(20)
            print(bits.res.time)
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """

        if N < self.status_nEvents:
            op = self.statusEvents[N]
            return op
        else:
            return 

    def getAllStatusValues(self):
        """Returns the whole status values list.
        
        Returns a list of dict like objects with the following entries
        sample, time, trigIn, DIN[10], DWORD, IR[6], ADC[6]
        sample is the sample ID number.
        time is the time stamp.
        trigIn is the value of the trigger input.
        DIN is a list of 10 digital input values.
        DWORD represents the digital inputs as a single decimal value.
        IR is a list of 10 infra-red (IR) input values.
        ADC is a list of 6 analog input values.
        These can be accessed as value[i]['sample'] 
        or value[i].sample, values[i].ADC[j].
        
        All sourses are numbered from zero.
        Din 0 ... 9
        IR 0 ... 5
        ADC 0 ... 5
        
        Example::

            bits.startStatusLog()
            while not event
                #do some processing
                continue
            bits.stopStatusLog()
            res=getAllStatusValues()
            print(bits.res[0].time)
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        return self.statusValues

    def getStatus(self,N=0):
        """Pulls out the Nth entry in the statusValues list.
        
        Returns a dict like object with the following entries
        sample, time, trigIn, DIN[10], DWORD, IR[6], ADC[6]
        
        sample is the sample ID number.
        time is the time stamp.
        trigIn is the value of the trigger input.
        DIN is a list of 10 digital input values.
        DWORD represents the digital inputs as a single decimal value.
        IR is a list of 10 infra-red (IR) input values.
        ADC is a list of 6 analog input values.
        These can be accessed as value['sample'] 
        or value.sample, values.ADC[j].
        
        All sourses are numbered from zero.
        Din 0 ... 9
        IR 0 ... 5
        ADC 0 ... 5

        Example::

            bits.startStatusLog()
            while not event
                #do some processing
                continue
            bits.stopStatusLog()
            res=getStatus(20)
            print(bits.res.time)
            
            
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
 
        """

        if N < self.status_nValues:
            value=self.statusValues[N]
            return value
        else:
            return 


    def getAnalog(self,N=0):
        """Pulls out the values of the analog inputs for 
        the Nth status entry.
        
        Returns a dictionary with a list of 6 floats (ADC) and a time stamp (time).
        
        All sourses are numbered from zero.
        ADC 0 ... 5
        
        Example:
            bits.pollStatus()
            res=bits.getAnalog()
            print(res['ADC'])
            
        will poll the status display the values of the  ADC inputs 
        in the first status entry returned.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        
        value=self.getStatus(N)
        if value:
            return {'ADC':value.ADC,'time':value.time}
        
    def getDigital(self,N=0):
        """ Pulls out the values of the digital inputs for
        the Nth status entry.
        
        Returns a dictionary with a list of 10 ints that 
        are 1 or 0 (DIN) and a time stamp (time)
        
        ll sourses are numbered from zero.
        Din 0 ... 9

        
        Example:
            bits.pollStatus()
            res=bits.getAnalog()
            print(res['DIN'])
            
        will poll the status display the value of the  digital inputs 
        in the first status entry returned.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also DBits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        
        value=self.getStatus(N)
        if value:
            return {'DIN':value.DIN,'time':value.time}
        
    def getDigitalWord(self,N=0):
        """ Pulls out the values of the digital inputs for 
        the Nth status entry.
        
        Returns a dictionary with a 10 bit word representing the binary
        values of those inputs (DWORD) and a time stamp (time).
        
        Example:
            bits.pollStatus()
            res=bits.getAnalog()
            print(res['DWORD'])
            
        will poll the status display the value of the digital inputs 
        as a decimal number.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        
        value=self.getStatus(N)
        if value:
            return {'DWORD':value.DWORD,'time':value.time}
        
    def getTrigIn(self,N=0):
        """Pulls out the values of the trigger input for the 
        Nth status entry.
        
        Returns dictionary with a 0 or 1 (trigIn) and a time stamp (time)
        
        Example:
            bits.pollStatus()
            res=bits.getAnalog()
            print(res['trigIn'])
            
        will poll the status display the value of the trigger input.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        
        value=self.getStatus(N)
        if value:
            return {'trigIn':value.trigIn,'time':value.time}
        
    def getIRBox(self,N=0):
        """Pulls out the values of the CB6 IR response box inputs for
        the Nth status entry.
        
        Returns a dictionary with a list of 6 ints that are
        1 or 0 (IRBox) and a time stamp (time).
        
        ll sourses are numbered from zero.
        IR 0 ... 5
        
        
        Example:
            bits.pollStatus()
            res=bits.getAnalog()
            print(res.['IRBox'])
            
        will poll the status display the values of the  IR box buttons 
        in the first status entry returned.
        
        Note that the firmware in Bits# units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Bits# units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        value=self.getStatus(N)
        if value:
            return {'IRBox':value.IR,'time':value.time}

    #=============================================================#
    #    Helper functions for the main status functions.          #
    #    Not normally needed by the user.                         #
    #=============================================================#

    def _statusEnable(self):
        """Sets the Bits# to continuously send back its status until stopped.
        You get a lot a data by leaving this going.
        
        Not normally needed by user
        """

        if self.RTBoxEnabled:
            warning = ("Cannot use status log when RTBox is on ")
            raise AssertionError(warning)
        # send start message to CRS device
        self.sendMessage(b'$Start\r')
        self.statusEnabled = True

    def _statusDisable(self):
        """Stop Bits# from recording data - and clears the buffer
        
        Not normally needed by user
        """
        # send stop message to CRS device
        self.sendMessage(b'$Stop\r')
        self.statusEnabled = False
        self.flush()

    def _statusLog(self,args=60):
        """ Should not normally be called by user
        Called in its own thread via self.startStatusLog()
        Reads the status reports from the Bits# for default 60 seconds or
        until self.stopStatusLog() is called.
        Ignores the last line as this is can be bogus. 
        Note any non status reports are found on the buffer will 
        cause an error.
        
        args specifies the time over which to record status events.
        The minimum time is 10ms, less than this results in recording stopping after 
        about 1 status report has been read.
        
        Puts its results into a Queue.
        
        This function is normally run in its own thread so actions can be asynchronous.
        """

        t = args   # Get the time to run for
        if t < 0.01: # But if very short treat as a 1-shot read.
            oneshot = True
            t = 0.01
        else:
            oneshot = False
        sT=clock() # start time
        msg=""
        # Continue reading data until sample time is up or status.End is set
        # Note when used in thread statusEnd can be set from outside this function.
        while (clock() - sT < t) and (self.statusEnd == False):
            smsg=self.read(timeout=0.1)
            # Compile message strings
            if smsg:
                msg=msg + smsg.decode("utf-8")
            # Stop if we have 1 whole status string in one shot mode
            if len(msg) > self._statusSize and oneshot:
                self.statusEnd = True
        # Send stop signal to CRS device to shut it up.
        self._statusDisable() # Send stop signal to CRS device to shut it up.
        self.statusEnd = True # Confirm that data logging has ended.
        if msg: # If we actually have a message
            lines = msg.split('\r') # Split message into status lines marked by CR
            N = len(lines) 
            values = [status() for  i in range(N-1)] # ignore last line as likely to be error
            for i in range(N-1): # for each status line
                v=lines[i].split(';') # split line into component parts marked by ;
                if v[0] == '#sample': # Check we have read a status line
                    # Now strip out status values into a structure.
                    values[i].sample = int(float(v[1]))
                    values[i].time = float(v[2])
                    values[i].trigIn = int(float(v[3]))
                    dword = 0;
                    for j in range(10): #10 digital inputs
                        values[i].DIN[j] = int(float(v[4+j]))
                        dword=dword + (2**j) * values[i].DIN[j]
                    values[i].DWORD = dword
                    for j in range(6): # 6 IR buttons
                        values[i].IR[j] = int(float(v[14+j]))
                    for j in range(6): # 6 Analog inputs
                        values[i].ADC[j] = float(v[20+j])
                    # Put the structure onto the cue.
                    self.statusQ.put(values[i])
                elif v[0] == '$touch': # We've read a screen touch event by mistake.
                    warning = ("_statusLog found touch" 
                            " data on input so skipping that")
                    logging.warning(warning)
                else: # We've read something we can't interpret.
                    warning = ("_statusLog found unknown data"
                            " on input so skipping that")



    def _getStatusLog(self):
        """ Read the log Queue
        
        Should not be needed by user if start/stopStatusLog or pollStatus 
        are used.
        
        fills statusValues with a list of dictionary like objects with the following 
        entries:
        sample, time, trigIn, DIN[10], DWORD, IR[6], ADC[6]
        
        They can be accessed as statusValues[i]['sample'] 
        or statusValues[i].sample, statusValues[i].ADC[j]
        
        Also sets status_nValues to the number of values recorded.
        """

        if not(self.statusQ.empty()):
            # emply statusValues of correct size
            self.statusValues = [
                        status() for  i in range(self.statusQ.qsize())]
            # Take the status values off the queue
            for index in range(0,self.statusQ.qsize()):
                self.statusValues[index] = self.statusQ.get()
            self.status_nValues = len(self.statusValues)
        else:
            self.status_nValues = 0

    def _extractStatusEvents(self): 
        """ Interprets values from status log to pullout any events.
        
        Should not be needed by user if start/stopStatusLog or 
        pollStatus are used
        
        Fills statusEvents with a list of dictionary like objects with the following entries
        source, input, direction, time.
        
        source = the general source of the event - e.g. DIN for 
        Digital input, IR for IT response box
        
        input = the individual input in the source.
        direction = 'up' or 'down'
        time = time stamp.
        
        Events are recorded relative to the four event flags
            statusDINBase, initial values for ditgial ins.
            statusIRBase, initial values for CB6 IR box.
            statusTrigInBase, initial values for TrigIn.
            statusMode, direction(s) of events to be reported.
        
        The data can be accessed as statusEvents[i]['time'] or statusEvents[i].time
        
        Also set status._nEvents to the number of events recorded
        
        """
        
        DIN_baseAll = [0]*10
        IR_baseAll = [0]*6
        ADC_baseAll = [self.statusADCBase]*6
        # Interpret statusDINBase and statusIRBase statusADCBase into lists.
        for i in range(10):
            mask = 2**i
            if mask & self.statusDINBase:
                DIN_baseAll[i] = 1
        for i in range(6):
            mask = 2**i
            if mask & self.statusIRBase:
                IR_baseAll[i] = 1
       
        Trig_base = self.statusTrigInBase
        N = len(self.statusValues)

        self.statusEvents = []
        nEvents = 0
        for i in range(N):
            DIN = self.statusValues[i].DIN 
            IR = self.statusValues[i].IR
            Trig = self.statusValues[i].trigIn
            ADC = self.statusValues[i].ADC
            # For 10 digital inputs
            for j in range(10):
                # Has input changed high to low and is that direction being recorded?
                if (DIN[j] == 0) and (DIN_baseAll[j] == 1): 
                    if ('down' in self.statusMode
                        or 'Down' in self.statusMode):
                        self.statusEvents.append(event())
                        self.statusEvents[nEvents].source = 'DIN'
                        self.statusEvents[nEvents].input = j
                        self.statusEvents[nEvents].dir = 'down'
                        self.statusEvents[nEvents].time = self.statusValues[i].time
                        nEvents = nEvents + 1
                    DIN_baseAll[j] = 0  # Set to the current input state
                # Has input changed low to high and is that direction being recorded?
                if (DIN[j] == 1) and (DIN_baseAll[j] == 0):
                    if ('up' in self.statusMode
                        or 'Up' in self.statusMode):
                        self.statusEvents.append(event())
                        self.statusEvents[nEvents].source = 'DIN'
                        self.statusEvents[nEvents].input = j
                        self.statusEvents[nEvents].dir = 'up'
                        self.statusEvents[nEvents].time = self.statusValues[i].time
                        nEvents = nEvents + 1
                    DIN_baseAll[j] = 1 # Set to the current input state
                    
            # For 6 IR buttons
            for j in range(6):
                # Has button changed high to low and is that direction being recorded?
                if (IR[j] == 0) and (IR_baseAll[j] == 1):
                    if ('down' in self.statusMode
                        or 'Down' in self.statusMode):
                        self.statusEvents.append(event())
                        self.statusEvents[nEvents].source = 'IR'
                        self.statusEvents[nEvents].input = j
                        self.statusEvents[nEvents].dir = 'down'
                        self.statusEvents[nEvents].time = self.statusValues[i].time
                        nEvents = nEvents + 1
                    IR_baseAll[j] = 0 # Set to the current input state
                    
                # Has button changed low to high and is that direction being recorded?
                if (IR[j] == 1) and (IR_baseAll[j]==0):
                    if ('up' in self.statusMode
                        or 'Up' in self.statusMode):
                        self.statusEvents.append(event())
                        self.statusEvents[nEvents].source = 'IR'
                        self.statusEvents[nEvents].input = j
                        self.statusEvents[nEvents].dir = 'up'
                        self.statusEvents[nEvents].time = self.statusValues[i].time
                        nEvents = nEvents + 1
                    IR_baseAll[j] = 1 # Set to the current input state
            for j in range(6):
                # Has analog input changed high to low and is that direction being recorded?
                if ADC_baseAll[j] - ADC[j] > self.statusThreshold:
                    if ('down' in self.statusMode
                        or 'Down' in self.statusMode):
                        self.statusEvents.append(event())
                        self.statusEvents[nEvents].source = 'ADC'
                        self.statusEvents[nEvents].input = j
                        self.statusEvents[nEvents].dir = 'down'
                        self.statusEvents[nEvents].time = self.statusValues[i].time
                        nEvents = nEvents + 1
                    ADC_baseAll[j] = ADC[j]
                    
                # Has analog input changed low to high and is that direction being recorded?
                if ADC[j] - ADC_baseAll[j]  > self.statusThreshold:
                    if ('up' in self.statusMode
                        or 'Up' in self.statusMode):
                        self.statusEvents.append(event())
                        self.statusEvents[nEvents].source = 'ADC'
                        self.statusEvents[nEvents].input = j
                        self.statusEvents[nEvents].dir = 'up'
                        self.statusEvents[nEvents].time = self.statusValues[i].time
                        nEvents = nEvents + 1
                    ADC_baseAll[j] = ADC[j]
                    
            # Has trigger changed high to low and is that direction being recorded?
            if Trig == 0 and Trig_base == 1:
                if ('down' in self.statusMode
                    or 'Down' in self.statusMode):
                    self.statusEvents.append(event())
                    self.statusEvents[nEvents].source='Trigger'
                    self.statusEvents[nEvents].input=0
                    self.statusEvents[nEvents].dir='down'
                    self.statusEvents[nEvents].time=self.statusValues[i].time
                    nEvents=nEvents+1
                Trig_base = 0 # Set to the current input state
                
            # Has trigger changed low to high and is that direction being recorded?
            if Trig == 1 and Trig_base == 0:
                if ('up' in self.statusMode
                    or 'Up' in self.statusMode):
                    self.statusEvents.append(event())
                    self.statusEvents[nEvents].source = 'Trigger'
                    self.statusEvents[nEvents].input = 0
                    self.statusEvents[nEvents].dir = 'up'
                    self.statusEvents[nEvents].time = self.statusValues[i].time
                    nEvents = nEvents + 1
                Trig_base = 1 # Set to the current input state
                
        self.status_nEvents=nEvents



    #=======================#
    #   Other functions     #
    #=======================#

    # TO DO: The following are either not yet implemented (or not tested)
    def start(self):
        """[Not currently implemented] Used to begin event collection by
        the device.
        
        Not really needed as other members now do this.
        
        """
        raise NotImplementedError

    def stop(self):
        """[Not currently implemented] Used to stop event collection by
        the device.
        
        Not really needed as other members now do this.
        
        """
        raise NotImplementedError

    def checkConfig(self, level=1, demoMode=False, logFile=''):
        """Checks whether there is a configuration for this device and
        whether it's correct

        Parameters
        ----------

        level: integer

            - 0: do nothing
            - 1: check that we have a config file and that the graphics
                card and operating system match that specified in the
                file. Then assume identity LUT is correct
            - 2: switch the box to status mode and check that the
                identity LUT is currently working
            - 3: force a fresh search for the identity LUT
        """
        
        if self.noComms:
            demoMode = True
        prevMode = self.mode
        # if we haven't fetched a config yet then do so
        if not self.config:
            self.config = Config(self)
        # check that this matches the prev config for our graphics card etc
        ok = False  # until we find otherwise
        if level == 1:
            ok = self.config.quickCheck()
            if not ok:
                # didn't match our graphics card or OS
                level = 2
                self._warnTesting()
            else:
                self.mode = prevMode
                self.win.gammaRamp = self.config.identityLUT
                msg = "Bits# config matches current system: %s on %s"
                logging.info(msg % (self.config.gfxCard, self.config.os))
                return 1
        # it didn't so switch to doing the test
        if level == 2:
            errs = self.config.testLUT(demoMode=demoMode)
            if demoMode:
                return 1
            if (errs**2).sum() != 0:
                level = 3
                logging.info("The current LUT didn't work as identity. "
                             "We'll try to find a working one.")
            else:
                self.config.identityLUT = self.win.backend.getGammaRamp().transpose()
                self.config.save()
                self.mode = prevMode
                logging.info("We found a LUT and it worked as identity")
                return 1
        if level == 3:
            ok = self.config.findIdentityLUT(demoMode=demoMode,
                                             logFile=logFile)
        self.mode = prevMode
        return ok

    def _warnTesting(self):
        msg = ("We need to run some tests on your graphics card (hopefully "
               "just once).\nThe BitsSharp will go into status mode while "
               "this is done.\nIt can take a minute or two...")
        print(msg)
        sys.stdout.flush()
        msgOnScreen = visual.TextStim(self.win, msg)
        msgOnScreen.draw()
        self.win.flip()
        core.wait(1.0)
        self.win.flip()

    # properties that need a weak ref to avoid circular references
    @property
    def win(self):
        """The window that this box is attached to
        """
        
        if self.__dict__.get('win') is None:
            return None
        else:
            return self.__dict__.get('win')()

    @win.setter
    def win(self, win):
        self.__dict__['win'] = weakref.ref(win)

class DisplayPlusPlus(BitsSharp):
    """A Display++ is Bits# box inside and LCD monitor so this class
       is just a wrapper that reminds people with a Display++ that
       they are using it. However unlike the Bits# you may not 
       have any analog connections on a Display++ unless you 
       purchased that option.
       
       Everything in the Bits# class should work but any 
       analog values sent or read will be spurious unless you
       have the analog hardware installed.
       
        Note that the firmware in Display++ units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Display++ units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particualar it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        RTBox commands that reset the key mapping have been found not to work
        one some firmware.
    """
       
    name = b'CRS Display++'
    def __init__(self, win=None, 
                         portName=None, 
                         mode='', 
                         checkConfigLevel=1,
                         gammaCorrect = 'hardware',
                         gamma = None,
                         noComms=False):
        super(DisplayPlusPlus,self).__init__(win, portName, mode, checkConfigLevel,
                 gammaCorrect, gamma,
                 noComms)

    def __del__(self):
        super(DisplayPlusPlus,self).__del__()



class DisplayPlusPlusTouch(DisplayPlusPlus):
    """A Display++ is Bits# box inside and LCD monitor but its 
       also possible to add a touch screen option to Display++ 
       and this class will give access to that.
       
       Otherwise this class is just a wrapper to the Bits# class.
       However unlike the Bits# you may not have any analog
       connections on a Display++ unless you purchased that option.
       
       Everything in the Bits# class should work but any 
       analog values sent or read will be spurious unless you
       have the analog hardware installed.
       
        Note that the firmware in Display++ units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Display++ units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        RTBox commands that reset the key mapping have been found not to work
        one some firmware.
    """
    
    name = b'CRS Display++Touch'
    def __init__(self, win=None, 
                         portName=None, 
                         mode='', 
                         checkConfigLevel = 1,
                         gammaCorrect = 'hardware',
                         gamma = None,
                         noComms=False):
        super(DisplayPlusPlusTouch,self).__init__(win, portName, mode, 
                                                checkConfigLevel,
                                                gammaCorrect, gamma,
                                                noComms)
       
       # Members for controlling touch screen
        self.touchEnabled = False   # Used to keep track of touch screen enables
        self.touchLogEnd = False    # used to kill the touch logging thread.
        self.lastTouch = 'released' # Used to detect a possible error 
                                        # in the touch screen hardware.
        self.touchFirstTime = True  # Used to detect a possible error 
                                        #in the touch screen hardware.
        self.touchDistance = 10     # Used to screen out events that are 
                                        #too close together.
        self.touchTime = 0.1        # Used to screen out events that are 
                                        #too close in time.
        self.touchType = ['touched', 'released'] # Used to screen in events
                                        #in forming the touch event list.
        self.checkTime = 0.25       # Used to screen out an error 
                                        #in the touch screen hardware
                                        
        self._touchSize = 31        # Number of bytes returned by touch 
                                        # screen when pressed.
        
       # Data members for touch screen
        self.touch_nValues=0
        self.touch_nEvents=0
        self.touchValues=[] 
        self.touchEvents=[]
        # Set up a queue in which to store touch screen events.
        self.touchQ = Queue.Queue(70000) 

    def __del__(self):
        super(DisplayPlusPlusTouch,self).__del__()


    def RTBoxEnable(self, mode=('CB6','Down','Trigger'), map=None):
        """ Overaload RTBoxEnable for Display++ with touch screen.
        Sets up the RTBox with preset or bespoke mappings 
        and enables event detection.
        
        RTBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, tigers and
        CB6 IR input channels.
        
        Mode is a list of strings.
        Preset mappings  provided via mode:
            CB6 for the CRS CB6 IR response box.
            IO for a three button box connected to Din0-2
            IO6 for a six button box connected to Din0-5
            
        If mode = None or is not set then the value of self.RTBoxMode is used.

        Bespoke Mappings over write preset ones.
        
        The format for map is a list of tuples with each tuple 
        containing the name of the 
        RT Box button to be mapped and its source 
        eg ('btn1','Din0') maps physical input Din0 to 
        logical button btn1. 
        
        Note the lowest number button event is Btn1
        
        RTBox has four logical buttons (btn1-4) and 
        three auxiliary events (light, pulse and trigger)
        Buttons/events can be mapped to multiple physical
        inputs and stay mapped until reset.
        
        Mode is a list of string or list of strings that contains 
        keywords to determine present mappings and modes for RTBox.
        
        If mode includes 'Down' button events will be 
        detected when pressed.
        If mode includes 'Up' button events will be 
        detected when released.
        You can detect both types of event but note 
        that pulse, light and trigger events
        dont have an 'Up' mode.
        
        If Trigger is included in mode the trigger 
            event will be mapped to the trigIn connector.
            
        Example: 
            bits.RTBoxEnable(mode = 'Down'), map = [('btn1','Din0'), ('btn2','Din1')]
            
        enable the RTBox emulation to detect Down events on buttons 1 and 2 where they are
        mapped to DIN0 and DIN1.
        
        Example: 
            bits.RTBoxEnable(mode = ['Down','CB6'])
        
        enable the RTBox emulation to detect Down events on the standard CB6 IR response box keys.

        """
        if self.touchEnabled:
            warning = ("Cannot use RTBox when touch screen is on")
            raise AssertionError(warning)
        else:
            if type(mode) is tuple:
                mode = list(mode)
            super(DisplayPlusPlusTouch, self).RTBoxEnable(mode = mode, map = map)
    
    def statusBoxEnable(self, mode=None, map=None, threshold = None):
        """ Sets up the statusBox with preset or bespoke mappings 
        and enables event detection.
        
        stautsBox events can be mapped to a number of physical events on Bits#
        They can be mapped to digital input lines, tigers and
        CB6 IR input channels.
        
        Mode is a list of strings.
        Preset mappings  provided via mode:
            CB6 for the CRS CB6 IR response box connected mapped to btn1-6
            IO for a three button box connected to Din0-2 mapped to btn1-3
            IO6 for a six button box connected to Din0-5 mapped to btn1-6
            IO10 for a ten button box connected to Din0-9 mapped to btn1-10
            Trigger maps the trigIn to btn17
            
            if CB6 and IOx are used the Dins are mapped from btn7 onwards.
            
        If mode = None or is not set then the value of self.statusBoxMode is used.

        Bespoke Mappings over write preset ones.
        
        The format for map is a list of tuples with each tuple 
        containing the name of the 
         button to be mapped and its source 
        eg ('btn1','Din0') maps physical input Din0 to 
        logical button btn1. 
        
        Note the lowest number button event is Btn1
        
        statusBox has 17 logical buttons (btn1-17).
        Buttons/events can be mapped to multiple physical
        inputs and stay mapped until reset.
        
        Mode is a string or list of strings that contains 
        keywords to determine present mappings and modes for statusBox.
        
        If mode includes 'Down' button events will be 
        detected when pressed.
        If mode includes 'Up' button events will be 
        detected when released.
        You can detect both types of event noting that the event detector
        will look for transitions and ignorewhat it sees as the starting state.
        

            
        Example: 
            bits.statusBoxEnable(mode = 'Down'), map = [('btn1','Din0'), ('btn2','Din1')]
            
        enable the stautsBox to detect Down events on buttons 1 and 2 where they are
        mapped to DIN0 and DIN1.
        
        Example: 
            bits.statusBoxEnable(mode = ['Down','CB6'])
        
        enable the statusBox emulation to detect Down events on the standard CB6 IR response box keys.
        
        Note that the firmware in Display++ units varies over time and some 
        features of this class may not work for all firmware versions. 
        Also Display++ units can be configured in various ways via their 
        config.xml file so this class makes certain assumptions about the
        configuration. In particular it is assumed that all digital inputs,
        triggers and analog inputs are reported as part of status
        updates. If some of these report are disabled in your config.xml file 
        then 'status' and 'event' commands in this class may not work.
        
        """
        if self.touchEnabled:
            warning = ("Cannot use status Box when touch screen is on")
            raise AssertionError(warning)
        else:
            super(DisplayPlusPlusTouch, self).statusBoxEnable(mode = mode, map = map, threshold = threshold)
    
    def _statusEnable(self):
        """ Overaload _statusEnable for Display++ with touch screen
        
        Sets the Bits# to continuously send back its status until stopped.
        You get a lot a data by leaving this going.
        
        Not normally needed by user
        """
        if self.touchEnabled:
            warning = ("Cannot use status log when touch screen is on")
            raise AssertionError(warning)
        else:
            super(DisplayPlusPlusTouch, self)._statusEnable()
        
        
    #===================================================================#
    #    The getTouch, touchWait, and touchPressed commands work        #
    #    a bit like equivalent RTBox commands.                          #
    #                                                                   #
    #    They do use touch logging in a thread but only do anything if  #
    #    there is something useful on the serial buffer so you need     #
    #    to call touchEnable before and touchDisable after any call     # 
    #    to these functions                                             #
    #===================================================================#
    
        
    def touchEnable(self):
        """ Turns on the touch screen. Any presses will now be reported
        
        Example:
            bits.touchEnable()
            res = bits.touchWait()
            bits.touchDisable()
            print(res.time)
            
        Enables touch screen, waits for a touch, disables touch screen 
        and displays the timestamp of the touch.
        
        """
        if self.RTBoxEnabled:
            warning = ("Cannot use touch screen when RTBox is on")
            raise AssertionError(warning)
        if self.statusBoxEnabled:
            warning = ("Cannot use touch screen when status Box is on")
            raise AssertionError(warning)
        if self.statusEnabled:
            warning = ("Cannot use touch screen when status logging is on")
            raise AssertionError(warning)
        if self.noComms:
            return
        # Send message to Display++ to turn on touch screen
        self.sendMessage(b'$EnableTouchScreen=[ON]\r')
        msg=self.read(timeout=0.1)
        msg=msg.decode("utf-8")
        # Check the reply message
        if 'ON' in msg:
            self.touchEnabled = True
        else:
            raise AssertionError("Cannot enable touch screen")
        self.flush()

        
    def touchDisable(self):
        """ Turns off the touch screen.
                
        Example:
            bits.touchEnable()
            res = bits.touchWait()
            bits.touchDisable()
            print(res.time)
            
        Enables touch screen, waits for a touch, disables touch screen 
        and displays the timestamp of the touch.
        """
        if self.noComms:
            return
        # Send message to Display++ to turn off the touch screen.
        self.sendMessage(b'$EnableTouchScreen=[OFF]\r')
        msg=self.read(timeout=0.1)
        msg=msg.decode("utf-8")
        # Check the reply message
        if 'OFF' in msg:
            self.touchEnabled = False
        else:
            raise AssertionError("Cannot disable touch screen")
        self.flush()
        
        
    def getTouchResponses(self,N=1):
        """ checks for (at least) an appropriate number of touch screen
        presses on the input buffer then reads them.
        Returns a list of dict like objects with four members
        'x','y','dir' and 'time'
        'x and y' are the x and y coordinates pressed.
        'dir' is the direction of the event
                    eg 'touched' for presses and 'released' for releases.
        'time' is the timestamp associated with the event.
        these values can be read as a structure:
            res=getTouchResponses(3)
            res[0].dir, res[0].x, res[0].time
        or dictionary
            res[0]['dir'], res[0]['x'], res[0]['time']
        
        Note even if only 1 response is requested the result is
            a 1 item long list of dict like objects.
        
        Note in theory this could be used to get multiple responses
            but in practice the touch screen reports every slight
            movements so the Logging methods, getTouchResponse 
            or getAllTouchResponses are better.
        
        Note this function does not start touch screen
            recording so should only be called
            when there appears to be data waiting.
            So you need to call touchEnable() before and 
            touchDisable after this function.
            
        Example:
            bits.touchEnable()
            while not event:
                # do some processing
                continue
            bits.touchDisable()
            res=getTouchResponses(3)
            print(res[0].time)
        
        Will put the touch screen into continuous reading while doing some task
        and at the end get the first 3 tocuhes are display the timestamp of the first one.
        """
        if self.noComms or N == 0:
            return
        if  self._inWaiting() > (N*self._touchSize - 1):  
            # Works by calling the startTouchLog() after the event.
            # Will wait 0.01 seconds per response requested
            self.startTouchLog(N*0.01) 
            # Join the touch log thread and wait for it to finish.
            self.touchThread.join()
            del self.touchThread
            values = self.getTouchLog()
            self.flush()
            return values[0:N]
        else:
            return 
            
    def getAllTouchResponses(self):
        """ get all the touch screen presses from the
        events on the input buffer then reads them.
        Returns a list of dict like objects with four members
        'x','y','dir' and 'time'
        'x and y' are the x and y coordinates pressed.
        'dir' is the direction of the event
                    eg 'touched' for presses and 'relased' for releases.
        'time' is the timestamp associated with the event.
        these values can be read as a structure:
            res=getAllTouchResponses()
            res[0].dir, res[0].x, rest[0].time
        or dirctionary
            res[0]['dir'], res[0]['x'], res[0]['time']
        
        Note even if only 1 response is requested the result is
            a 1 item long list of dict like objects.
        
        Note in theory this could be used to get multiple responses
            but in practice the touch screen reports every slight
            movement so the Logging methods are better.
        
        Note this function does not start touch screen
            recording so should only be called
            when there appears to be data waiting.
            So you need to call touchEnable() before and 
            touchDisable after this function

        Example:
            bits.touchEnable()
            while not event:
                # do some processing
                continue
            bits.touchDisable()
            res=getAllTouchResponses(3)
            print(res[0].time)
        
        Will put the touch screen into continuous reading while doing some task
        and at the end get all the tocuhes are display the timestamp of the first one.
        """
        N = int(np.floor(self._inWaiting() / self._touchSize))
        return self.getTouchResponses(N)
        
            
    def getTouchResponse(self):
        """ checks for (at least) one touch screen
        press on the input buffer then reads it.
        Returns a dict like object with four members
        'x','y','dir' and 'time'
        'x and y' are the x and y coordinates pressed.
        'dir' is the direction of the event
                    eg 'touched' for presses and 'relased' for releases.
        'time' is the timestamp associated with the event.
        these values can be read as a structure:
            res=getTouchGetResponse()
            res.dir, res.x, rest.time
        or dirctionary
            res['dir'], res['x'], res['time']
        
        Note this function does not start touch screen
            recording so should only be called
            when there appears to be data waiting.
            So you need to call touchEnable() before and 
            touchDisable after this function.
            
        Example:
            bits.touchEnable()
            while not event:
                # do some processing
                continue
            bits.touchDisable()
            res=getTouchResponse()
            print(res.time)
        
        Will put the touch screen into continuous reading while doing some task
        and at the end get all the tocuhes are display the timestamp of the first one.
        """
        
        res=self.getTouchResponses(1)
        value=res[0]
        return value
    
    def touchPressed(self,N=1):
        """Check to see if (at least) the appropriate number of 
        touch screen events have been made
        
        Not accurate due to touch jitter creating extra events
        but can be used to detect first press.
        
        Example:
            bits.touchEnable()
            while not bits.touchPressed(5):
                # do some processing
                continue
            bits.touchDisable()
        
        Will do some processing until 5 screen couches are recorded.
        """
        if self.noComms:
            return
        if self._inWaiting()<self._touchSize*N:
            return False
        else:
            return True
    
    # touchWaitN is depreciated due to touch jitter creating false events
    def touchWaitN(self, N=1):
        """Waits until (at least) the appropriate number of 
        touch screen events have been made 
        then reports the responses.
        Pauses program execution in mean time.
        
        Not every accurate due to touch jitter creating extra events.
        
        Example:
            bits.touchEnable()
            bits.touchWaitN(5):
            bits.touchDisable()
            
        Will pause until 5 screen touches are recorded.
        
        """
        if self.noComms:
            return
        while self._inWaiting()<self._touchSize*N:
            continue # ie loop
        return self.getTouchResponses(N)
    
        
    def touchWait(self):
        """Waits until (at least) one 
        touch screen event have been made.
        Then reports the response.
        Pauses programe execution in mean time.
        
        Example:
            bits.touchEnable()
            bits.touchWait():
            bits.touchDisable()
            
        Will pause until 1 screen touch  recorded.
        
        """
        if self.noComms:
            return
        while self._inWaiting()<self._touchSize:
            continue # ie loop
        return self.getTouchResponse()
        
    #================================================================#
    #    Touch logging commands work a bit more like the status log  #
    #    commands.
    #    You turn logging on, do other stuff, then later collect the #
    #    log results with getTouchLog                                #
    #================================================================#
    

    def startTouchLog(self,t=60):
        """ Start logging data from the touch screen.
        Turns on the touch screen.
        
        Example:
            bits.startTouchLog()
            while not event:
                #do some processing
                continue
            bits.stopTouchLog()
            res=bits.getTouchLog()
        
        """
        if not(self.touchEnabled):
            self.touchEnable()

        #Try both Python 2 and 3 versions for initialising a thread
        try: 
            self.touchThread=threading.Thread(target=self._touchLog,args=(t,))
        except Exception:
            self.touchThread=threading.Thread(target=self._touchLog,args=(t))

        self.touchLogEnd=False
        self.touchThread.start()

    def stopTouchLog(self):
        """ Stop logging data from the Bits#
        Waits for _getLog to finish properly so can 
        introduce a timing delay.
        
        Does not automatically extract the touch log.
        
        Example:
            bits.startTouchLog()
            while not event:
                #do some processing
                continue
            bits.stopTouchLog()
            res=bits.getTouchLog()
        
        """
        self.touchLogEnd=True
        self.touchThread.join()
        del self.touchThread
        self.flush()
        if self.touchEnabled:
            self.touchDisable()

    def getTouchLog(self, caution=True, checkTime=None):
        """ Reads out the touch screen cue and checks for a known error
        Returns a list of dict like objects with four members
        'x','y','dir' and 'time'
        'x and y' are the x and y coordinates pressed.
        'dir' is the direction of the event
                    eg 'touched' for presses and 'released' for releases.
        'time' is the timestamp associated with the event.
        these values can be read as a structure:
            res=getTouchResponses(3)
            res[0].dir, res[0].x, res[0].time
        or dictionary
            res[0]['dir'], res[0]['x'], res[0]['time']
        
        Note even if only 1 response is requested the result is
            a 1 item long list of dict like objects.
        
        Note in theory this could be used to get multiple responses
            but in practice the touch screen reports every slight
            movements so the Logging methods, getTouchResponse 
            or getAllTouchResponses are better.
        
        Note this function does not start touch screen
            recording so should only be called
            when there appears to be data waiting.
            So you need to call touchEnable() before and 
            touchDisable after this function.
 
        checkTime specifies a time between the first and second touches
        after which a warning of a possible error will be issued and
        the error may be corrected.
        
        caution: If True tell the function to check for a known Display++ error
        if you don't have that error or you don't care about it you should set 
        this to False.
        
        Example:
            bits.startTouchLog()
            while not event:
                #do some processing
                continue
            bits.stopTouchLog()
            res=bits.getTouchLog(caution = False)
        
        Will get all the screen touches without checking for errors.
        
        """
        if checkTime!=None:
            self.checkTime = checkTime
        
        number = self.touchQ.qsize()
        if not(self.touchQ.empty()):
            self.touchValues=[touch() for  i in range(self.touchQ.qsize())]
            for index in range(0,self.touchQ.qsize()):
                self.touchValues[index]=self.touchQ.get()
                
            #Display++ can sometimes issue a spurious touch event left over
            #from a previous series of touches. The following code should detect
            #and correct the error
            
            lastTouch = self.touchValues[number-1].dir
            
            #No need to worry if only one touch recorded or the user is happy
            #to forgo checks.
            if number>1 and caution: 
                

                #Detects if first timestamp is after second
                #Works if Display++ clock has  been reset between touch 
                #data collection sessions.
                if self.touchValues[0].time > self.touchValues[1].time:
                    del self.touchValues[0]
                    warning=("getTouchLog: Deleted first touch as recorded " 
                              "after second. This corrects an error in "
                              "the Display++")
                    logging.warning(warning)
                    
                #Detects that the last recorded touch in a previous call to 
                #getTouchLog was a 'touched' rather than a 'release' event.
                #this is likely to cause the error but won't capture and
                #error from the last run of an experiment that uses the 
                #touch screen
                elif self.lastTouch == 'touched':
                    del self.touchValues[0]
                    warning=("getTouchLog: Deleted first touch as the "
                             "last previously recorded touch event "
                             "was not a release and this can indicate an "
                             "error in the Display++. However, this could be the "
                             "wrong thing to have done")
                    logging.warning(warning)
                
                #Detects that gap between first two timestamps is not larger
                #than checkTime.
                #Due to finger jitter this is unlikely if first touch is real.
                #But this is not fool proof it could delete a first very 
                #clean touch
                #and if the other two tests failed and this is not
                #the first call to this function the chances are it a good
                #touch - hence just a warning in that case.
                elif (self.touchValues[1].time 
                       - self.touchValues[0].time) > self.checkTime:
                    warning=("getTouchLog: Gap between first and second "
                             "touches is large normally finger jitter means "
                             "it is quite short.")
                    logging.warning(warning)
                    if self.touchFirstTime == False:
                        del self.touchValues[0]
                        warning=("getTouchLog: Deleted first touch as "
                                 "the gap between first "
                                 "and second touches is large "
                                 "and this is not the first call of the run. "
                                 "But this could be the wrong thing to have "
                                 "done.")
                        logging.warning(warning)
            self.lastTouch = lastTouch
            self.touchFirstTime = False
            self.touch_nValues=len(self.touchValues)
            return self.touchValues
        else:
            self.touch_nValues=0
            return None


            
    #===============================================#
    #    Helper function for touch screen commands. #
    #    Normally run in its own thread.             #
    #===============================================#
            
    def _touchLog(self, args=(60,)):
        """ Gets raw touch screen events and put them in a Queue
            Not normally needed by the user.
        """
        
        t = args # Get the time to run for
        sT = clock() # start time
        msg = ""
        # While not timed out and until touchLogEnd is true
        # When run in a thread touchLogEnd can be set from outside this function.
        while (clock() - sT < t) and (self.touchLogEnd == False):
            # Complie the message
            smsg = self.read(timeout = 0.1)
            if smsg:
                msg = msg+smsg.decode("utf-8")
        self.touchDisable() # Turn off touch screen.
        self.touchLogEnd=True # Make sure this function marked as ending.
        self.flush()
        if msg:
            lines = msg.split('\r') # Split message into lines with CR
            N = len(lines)

            values=[touch() for  i in range(N)]
            #for all the touches
            for i in range(N):
                v = lines[i].split(';') # Split line into components at ;
                # If we have read a touch event.
                if '$touch' in v[0]:
                    #Grab the details of the event into a structure.
                    values[i].time = float(v[1])
                    values[i].x = int(float(v[2]))
                    values[i].y = int(float(v[3]))
                    if int(float(v[4])) == 1:
                        values[i].dir = 'touched'
                    else:
                        values[i].dir = 'released'
                    self.touchQ.put(values[i])
                elif '#status' in v[0]: # GOt a status event by mistake
                    warning=("_touchLog found" 
                            " status on input so skipping that")
                    logging.warning(warning)
                else: # Have picked up some other stuff on the input
                    warning=("_touchLog found"
                            " unknown data on input so skipping that")
                    logging.warning(warning)


    #============================================================#
    #    Touch event functions can be used to get a list of more #
    #    meaningful events following any getTouch commands       #
    #    works a bit like an eye movement gaze detector          #
    #============================================================#

    def setTouchEventParams(self, distance=None, t=None ,type=None):
        """ Sets the parameters for touch event detection.
            Distance is how far the touch should move to count
            as a new touch.
            Time is how long should lapse between touches for the 
            second one to count.
            
        Example:
            bits.startTouchLog()
            while not event:
                #do some processing
                continue
            bits.stopTouchLog()
            res=bits.getTouchLog()
            bits.setTouchEventParams(distance=20, t=0.001, type='touched')
            events=bits.getTouchEvents()
            
            Will extract touch events (not releases) that are 20 pixels and 1 ms apart.
        """
        if distance!=None:
            self.touchDistance = distance
        if t != None:
            self.touchTime = t
        if type != None:
            self.touchType = type

    def getTouchEvents(self, distance=None, t=None, type=None):
        """ Scans the touch log to extract touch events.
            You need to run getTouchLog before you run this function.
        
            Returns as list of Dict like structures with members
            time, x, y, and dir
            
            time is the time stamp of the event.
            x and y are the x and y locations of the event.
            direction is the type of event: 'touched', 'released'
            
            These values can be read as a structure:
            res=getTouchResponses(3)
            res[0].dir, res[0].x, res[0].time
            or dictionary
            res[0]['dir'], res[0]['x'], res[0]['time']
            
            
        Example:
            bits.startTouchLog()
            while not event:
                #do some processing
                continue
            bits.stopTouchLog()
            bits.getTouchLog()
            res=bits.getTouchEvents(distance=20, t=0.001, type='touched')
            print(res[0]['time']
            
            Will extract touch events (not releases) that are 20 pixels and 1 ms apart.
            
        """
        self.setTouchEventParams(distance,t,type)
        N=len(self.touchValues)
        self.touchEvents = []
        nEvents = 0
        rT = -999999
        rX = -999999
        rY = -999999
        rType = 'None'
        nEvents = 0
        for i in range(N):
            dist=(((self.touchValues[i].x - rX)**2.0)
                  +((self.touchValues[i].y - rY)**2.0))**0.5
            T = self.touchValues[i].time - rT
            
            # Only include events that are sufficiently far from
            # last recorded event in time and distance, or if
            # the direction of touch has changed and the new
            # direction is in the looked for type descriptor.
            if ((dist > self.touchDistance 
                    and T > self.touchTime) 
                or (rType != self.touchValues[i].dir 
                    and self.touchValues[i].dir in self.touchType)):
                self.touchEvents.append(touch())
                self.touchEvents[nEvents].time = self.touchValues[i].time
                self.touchEvents[nEvents].x = self.touchValues[i].x
                self.touchEvents[nEvents].y = self.touchValues[i].y
                self.touchEvents[nEvents].dir = self.touchValues[i].dir
                rT = self.touchValues[i].time
                rX = self.touchValues[i].x
                rY = self.touchValues[i].y
                rType = self.touchValues[i].dir
                nEvents = nEvents + 1
                self.touch_nEvents = nEvents
        return self.touchEvents


    def getTouchEvent(self, N=0, distance=None, t=None, type=None):
        """ Scans the touch log to return the Nth touch event.
            You need to run getTouchLog before you run this function.
        
           Returns as list of Dict like structures with members
            time, x, y, and dir
            
            time is the time stamp of the event.
            x and y are the x and y locations of the event.
            direction is the type of event: 'touched', 'released'
            
            These values can be read as a structure:
            res=getTouchResponses(3)
            res[0].dir, res[0].x, res[0].time
            or dictionary
            res[0]['dir'], res[0]['x'], res[0]['time']
            
            
        Example:
            bits.startTouchLog()
            while not event:
                #do some processing
                continue
            bits.stopTouchLog()
            bits.getTouchLog()
            res=bits.getTouchEvent(N=10, distance=20, time=0.001, type='touched')
            print(res.time)
            
            Will extract the 10th touch events (ingnoreing releases) that are 20 pixels and 1 ms apart.
        """
        values = self.getTouchEvents(distance, t, type)
        value = values[N]
        return value


class Config:

    def __init__(self, bits):
        # we need to set bits reference using weakref to avoid circular refs
        self.bits = bits
        self.load()  # try to fetch previous config file
        self.logFile = 0  # replace with a file handle if opened

    def load(self, filename=None):
        """If name is None then we'll try to save to
        """
        def parseLUTLine(line):
            return line.replace('[', '').replace(']', '').split(',')

        if filename is None:
            from psychopy import prefs
            filename = os.path.join(prefs.paths['userPrefsDir'],
                                    'crs_bits.cfg')
        if os.path.exists(filename):
            config = configparser.RawConfigParser()
            with open(filename) as f:
                config.readfp(f)
            self.os = config.get('system', 'os')
            self.gfxCard = config.get('system', 'gfxCard')
            self.identityLUT = np.ones([256, 3])
            _idLUT = 'identityLUT'
            self.identityLUT[:, 0] = parseLUTLine(config.get(_idLUT, 'r'))
            self.identityLUT[:, 1] = parseLUTLine(config.get(_idLUT, 'g'))
            self.identityLUT[:, 2] = parseLUTLine(config.get(_idLUT, 'b'))
            return True
        else:
            logging.warn('no config file yet for %s' % self.bits)
            self.identityLUT = None
            self.gfxCard = None
            self.os = None
            return False

    def _getGfxCardString(self):
        from pyglet.gl import gl_info
        return "%s: %s" % (gl_info.get_renderer(),
                           gl_info.get_version())

    def _getOSstring(self):
        import platform
        return platform.platform()

    def save(self, filename=None):
        if filename is None:
            from psychopy import prefs
            filename = os.path.join(prefs.paths['userPrefsDir'],
                                    'crs_bits.cfg')
            logging.info('saved Bits# config file to %r' % filename)
        # create the config object
        config = configparser.RawConfigParser()
        config.add_section('system')
        self.os = config.set('system', 'os', self._getOSstring())
        self.gfxCard = config.set('system', 'gfxCard',
                                  self._getGfxCardString())

        # save the current LUT
        config.add_section('identityLUT')
        config.set('identityLUT', 'r', list(self.identityLUT[:, 0]))
        config.set('identityLUT', 'g', list(self.identityLUT[:, 1]))
        config.set('identityLUT', 'b', list(self.identityLUT[:, 2]))

        # save it to disk
        with open(filename, 'w') as fileObj:
            config.write(fileObj)
        logging.info("Saved %s configuration to %s" % (self.bits, filename))

    def quickCheck(self):
        """Check whether the current graphics card and OS match those of
        the last saved LUT
        """
        if self._getGfxCardString() != self.gfxCard:
            logging.warn("The graphics card or its driver has changed. "
                         "We'll re-check the identity LUT for the card")
            return 0
        if self._getOSstring() != self.os:
            logging.warn("The OS has been changed/updated. We'll re-check"
                         " the identity LUT for the card")
            return 0
        return 1  # all seems the same as before

    def testLUT(self, LUT=None, demoMode=False):
        """Apply a LUT to the graphics card gamma table and test whether
        we get back 0:255 in all channels.
        :params:
            LUT: The lookup table to be tested (256x3).
            If None then the LUT will not be altered
        :returns:
            a 256 x 3 array of error values (integers in range 0:255)
        """
        bits = self.bits  # if you aren't yet in
        win = self.bits.win
        if LUT is not None:
            win.gammaRamp = LUT
        # create the patch of stimulus to test
        expectedVals = list(range(256))
        w, h = win.size
        # NB psychopy uses -1:1
        testArrLums = np.resize(np.linspace(-1, 1, 256), [256, 256])
        stim = visual.ImageStim(win, image=testArrLums, size=[256, h],
                                pos=[128 - w//2, 0], units='pix')
        expected = np.repeat(expectedVals, 3).reshape([-1, 3])
        stim.draw()
        # make sure the frame buffer was correct (before gamma was applied)
        frm = np.array(win.getMovieFrame(buffer='back'))
        assert np.alltrue(frm[0, 0:256, 0] == list(range(256)))
        win.flip()
        # use bits sharp to test
        if demoMode:
            return [0] * 256
        pixels = bits.getVideoLine(lineN=50, nPixels=256)
        errs = pixels - expected
        if self.logFile:
            for ii, channel in enumerate('RGB'):
                self.logFile.write(channel)
                for pixVal in pixels[:, ii]:
                    self.logFile.write(', %i' % pixVal)
                self.logFile.write('\n')
        return errs

    def findIdentityLUT(self, maxIterations=1000, errCorrFactor=1.0/5000,
                        nVerifications=50,
                        demoMode=True,
                        logFile=''):
        """Search for the identity LUT for this card/operating system.
        This requires that the window being tested is fullscreen on the Bits#
        monitor (or at least occupies the first 256 pixels in the top left
        corner!)
        :params:
            LUT: The lookup table to be tested (256 x 3).
            If None then the LUT will not be altered
            errCorrFactor: amount of correction done for each iteration
                number of repeats (successful) to check dithering
                has been eradicated
            demoMode: generate the screen but don't go into status mode
        :returns:
            a 256x3 array of error values (integers in range 0:255)
        """
        t0 = time.time()
        # create standard options
        intel = np.linspace(.05, .95, 256)
        one = np.linspace(0, 1.0, 256)
        fraction = np.linspace(0.0, 65535.0/65536.0, num=256)
        LUTs = {'intel': np.repeat(intel, 3).reshape([-1, 3]),
                '0-255': np.repeat(one, 3).reshape([-1, 3]),
                '0-65535': np.repeat(fraction, 3).reshape([-1, 3]),
                '1-65536': np.repeat(fraction, 3).reshape([-1, 3])}

        if logFile:
            self.logFile = open(logFile, 'w')

        if plotResults:
            pyplot.Figure()
            pyplot.subplot(1, 2, 1)
            pyplot.plot([0, 255], [0, 255], '-k')
            errPlot = pyplot.plot(list(range(256)), list(range(256)), '.r')[0]
            pyplot.subplot(1, 2, 2)
            pyplot.plot(200, 0.01, '.w')
            pyplot.show(block=False)

        lowestErr = 1000000000
        bestLUTname = None
        logging.flush()
        for LUTname, currentLUT in list(LUTs.items()):
            sys.stdout.write('Checking %r LUT:' % LUTname)
            errs = self.testLUT(currentLUT, demoMode)
            if plotResults:
                errPlot.set_ydata(list(range(256)) + errs[:, 0])
                pyplot.draw()
            print('mean err = %.3f per LUT entry' % abs(errs).mean())
            if abs(errs).mean() < abs(lowestErr):
                lowestErr = abs(errs).mean()
                bestLUTname = LUTname
        if lowestErr == 0:
            msg = "The %r identity LUT produced zero error. We'll use that!"
            print(msg % LUTname)
            self.identityLUT = LUTs[bestLUTname]
            # it worked so save this configuration for future
            self.save()
            return

        msg = "Best was %r LUT (mean err = %.3f). Optimising that..."
        print(msg % (bestLUTname, lowestErr))
        currentLUT = LUTs[bestLUTname]
        errProgression = []
        corrInARow = 0
        for n in range(maxIterations):
            errs = self.testLUT(currentLUT)
            tweaks = errs * errCorrFactor
            currentLUT -= tweaks
            currentLUT[currentLUT > 1] = 1.0
            currentLUT[currentLUT < 0] = 0.0
            meanErr = abs(errs).mean()
            errProgression.append(meanErr)
            if plotResults:
                errPlot.set_ydata(list(range(256)) + errs[:, 0])
                pyplot.subplot(1, 2, 2)
                if meanErr == 0:
                    point = '.k'
                else:
                    point = '.r'
                pyplot.plot(n, meanErr, '.k')
                pyplot.draw()
            if meanErr > 0:
                sys.stdout.write("%.3f " % meanErr)
                corrInARow = 0
            else:
                sys.stdout.write(". ")
                corrInARow += 1
            if corrInARow >= nVerifications:
                print('success in a total of %.1fs' % (time.time() - t0))
                self.identityLUT = currentLUT
                # it worked so save this configuration for future
                self.save()
                break
            elif (len(errProgression) > 10 and
                    max(errProgression) - min(errProgression) < 0.001):
                print("Trying to correct the gamma table was having no "
                      "effect. Make sure the window was fullscreen and "
                      "on the Bits# screen")
                break

        # did we get here by failure?!
        if n == maxIterations - 1:
            print("failed to converge on a successful identity LUT. "
                  "This is BAD!")

        if plotResults:
            pyplot.figure(figsize=[18, 12])
            pyplot.subplot(1, 3, 1)
            pyplot.plot(errProgression)
            pyplot.title('Progression of errors')
            pyplot.ylabel("Mean error per LUT entry (0-1)")
            pyplot.xlabel("Test iteration")
            r256 = np.reshape(list(range(256)), [256, 1])
            pyplot.subplot(1, 3, 2)
            pyplot.plot(r256, r256, 'k-')
            pyplot.plot(r256, currentLUT[:, 0] * 255, 'r.', markersize=2.0)
            pyplot.plot(r256, currentLUT[:, 1] * 255, 'g.', markersize=2.0)
            pyplot.plot(r256, currentLUT[:, 2] * 255, 'b.', markersize=2.0)
            pyplot.title('Final identity LUT')
            pyplot.ylabel("LUT value")
            pyplot.xlabel("LUT entry")

            pyplot.subplot(1, 3, 3)
            deviations = currentLUT - r256/255.0
            pyplot.plot(r256, deviations[:, 0], 'r.')
            pyplot.plot(r256, deviations[:, 1], 'g.')
            pyplot.plot(r256, deviations[:, 2], 'b.')
            pyplot.title('LUT deviations from sensible')
            pyplot.ylabel("LUT value")
            pyplot.xlabel("LUT deviation (multiples of 1024)")
            pyplot.savefig("bitsSharpIdentityLUT.pdf")
            pyplot.show()

    # Some properties for which we need weakref pointers, not std properties
    @property
    def bits(self):
        """The Bits box to which this config object refers
        """
        if self.__dict__.get('bits') is None:
            return None
        else:
            return self.__dict__.get('bits')()

    @bits.setter
    def bits(self, bits):
        self.__dict__['bits'] = weakref.ref(bits)


def init():
    """DEPRECATED: we used to initialise Bits++ via the compiled dll
    This only ever worked on windows and BitsSharp doesn't need it at all
    Note that, by default, Bits++ will perform gamma correction
    that you don't want (unless you have the CRS calibration device)
    (Recommended that you use the BitsPlusPlus class rather than
    calling this directly)
    """
    retVal = False
    if haveBitsDLL:
        try:
            retVal = _bits.bitsInit()  # returns null if fails?
        except Exception:
            logging.error('bits.init() barfed!')
    return retVal


def setVideoMode(videoMode):
    """Set the video mode of the Bits++ (win32 only)
    bits8BITPALETTEMODE = 0x00000001  # normal vsg mode
    NOGAMMACORRECT = 0x00004000  # No gamma correction mode
    GAMMACORRECT = 0x00008000  # Gamma correction mode
    VIDEOENCODEDCOMMS = 0x00080000
    (Recommended that you use the BitsLUT class rather than
    calling this directly)
    """
    if haveBitsDLL:
        return _bits.bitsSetVideoMode(videoMode)
    else:
        return 1


def reset(noGamma=True):
    """Reset the Bits++ box via the USB cable by initialising again
    Allows the option to turn off gamma correction
    """
    OK = init()
    if noGamma and OK:
        setVideoMode(NOGAMMACORRECT)
