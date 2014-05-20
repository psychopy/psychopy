#!/usr/bin/env python
#coding=utf-8

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

#Acknowledgements:
#    This code was mostly written by Jon Peirce.
#    CRS Ltd provided support as needed.
#    Shader code for mono++ and color++ modes was based on code in Psythtoolbox
#    (Kleiner) but does not actually use that code directly

__docformat__ = "restructuredtext en"

DEBUG=True

import sys, time, glob
import numpy
import shaders
from copy import copy
from psychopy import logging
import serial
from OpenGL import GL
import OpenGL.GL.ARB.multitexture as GL_multitexture
try:
    from psychopy.ext import _bits
    haveBitsDLL=True
except:
    haveBitsDLL=False

if DEBUG: #we don't want error skipping in debug mode!
    import shaders
    haveShaders=True
else:
    try:
        import shaders
        haveShaders=True
    except:
        haveShaders=False

#bits++ modes
bits8BITPALETTEMODE=  0x00000001  #/* normal vsg mode */
NOGAMMACORRECT     =  0x00004000  #/* Gamma correction mode */
GAMMACORRECT       =  0x00008000  #/* Gamma correction mode */
VIDEOENCODEDCOMMS  =  0x00080000 # needs to be set so that LUT is read from screen

class BitsPlusPlus(object):
    """The main class to control a bits++ box.

    This is usually a class added within the window object and is typically accessed from there.
    e.g.::

        from psychopy import visual
        win = visual.Window([800,600], mode='bits++')
        win.bits.setContrast(0.5)#use bits++ to reduce the whole screen contrast by 50%

    """
    def __init__(self,
                    win,
                    contrast=1.0,
                    gamma=[1.0,1.0,1.0],
                    nEntries=256,
                    mode='bits++',):
        self.win = win
        self.contrast=contrast
        self.nEntries=nEntries
        self.mode = mode
        self.method = 'fast' #used to allow setting via USB which was 'slow'

        if len(gamma)>2: # [Lum,R,G,B] or [R,G,B]
            self.gamma=gamma[-3:]
        else:
            self.gamma = [gamma, gamma, gamma]

        if init():
            setVideoMode(NOGAMMACORRECT|VIDEOENCODEDCOMMS)
            self.initialised=True
            logging.debug('found and initialised bits++')
        else:
            self.initialised=False
            logging.warning("couldn't initialise bits++")

        #do the processing
        self._HEADandLUT = numpy.zeros((524,1,3),numpy.uint8)
        self._HEADandLUT[:12,:,0] = numpy.asarray([ 36, 63, 8, 211, 3, 112, 56, 34,0,0,0,0]).reshape([12,1])#R
        self._HEADandLUT[:12,:,1] = numpy.asarray([ 106, 136, 19, 25, 115, 68, 41, 159,0,0,0,0]).reshape([12,1])#G
        self._HEADandLUT[:12,:,2] = numpy.asarray([ 133, 163, 138, 46, 164, 9, 49, 208,0,0,0,0]).reshape([12,1])#B
        self.LUT=numpy.zeros((256,3),'d')        #just a place holder
        self.setLUT()#this will set self.LUT and update self._LUTandHEAD
        self._setupShaders()

    def setLUT(self,newLUT=None, gammaCorrect=True, LUTrange=1.0):
        """Sets the LUT to a specific range of values in Bits++ mode only

        Note that, if you leave gammaCorrect=True then any LUT values you supply
        will automatically be gamma corrected.

        The LUT will take effect on the next `Window.flip()`

        **Examples:**
            ``bitsBox.setLUT()``
                builds a LUT using bitsBox.contrast and bitsBox.gamma

            ``bitsBox.setLUT(newLUT=some256x1array)``
                (NB array should be float 0.0:1.0)
                Builds a luminance LUT using newLUT for each gun
                (actually array can be 256x1 or 1x256)

            ``bitsBox.setLUT(newLUT=some256x3array)``
               (NB array should be float 0.0:1.0)
               Allows you to use a different LUT on each gun

        (NB by using BitsBox.setContr() and BitsBox.setGamma() users may not
        need this function)
        """

        #choose endpoints
        LUTrange=numpy.asarray(LUTrange)
        if LUTrange.size==1:
            startII = int(round((0.5-LUTrange/2.0)*255.0))
            endII = int(round((0.5+LUTrange/2.0)*255.0))+1 #+1 because python ranges exclude last value
        elif LUTrange.size==2:
            multiplier=1.0
            if LUTrange[1]<=1: multiplier=255.0
            startII= int(round(LUTrange[0]*multiplier))
            endII = int(round(LUTrange[1]*multiplier))+1 #+1 because python ranges exclude last value
        stepLength = 2.0/(endII-startII-1)

        if newLUT is None:
            #create a LUT from scratch (based on contrast and gamma)
            #rampStep = 2.0/(self.nEntries-1)
            ramp = numpy.arange(-1.0,1.0+stepLength, stepLength)
            ramp = (ramp*self.contrast+1.0)/2.0
            #self.LUT will be stored as 0.0:1.0 (gamma-corrected)
            self.LUT[startII:endII,0] = copy(ramp)
            self.LUT[startII:endII,1] = copy(ramp)
            self.LUT[startII:endII,2] = copy(ramp)
        elif type(newLUT) in [float, int] or (newLUT.shape==()):
            self.LUT[startII:endII,0]= newLUT
            self.LUT[startII:endII,1]= newLUT
            self.LUT[startII:endII,2]= newLUT
        elif len(newLUT.shape) == 1: #one dimensional LUT
            #replicate LUT to other channels
            #check range is 0:1
            if newLUT>1.0:
                logging.warning('newLUT should be float in range 0.0:1.0')
            self.LUT[startII:endII,0]= copy(newLUT.flat)
            self.LUT[startII:endII,1]= copy(newLUT.flat)
            self.LUT[startII:endII,2]= copy(newLUT.flat)

        elif len(newLUT.shape) == 2: #one dimensional LUT
            #use LUT as is
            #check range is 0:1
            if max(max(newLUT))>1.0:
                raise AttributeError, 'newLUT should be float in range 0.0:1.0'
            self.LUT[startII:endII,:]= newLUT

        else:
            logging.warning('newLUT can be None, nx1 or nx3')

        #do gamma correction if necessary
        if gammaCorrect==True:
            gamma=self.gamma
            if hasattr(self.win.monitor, 'lineariseLums'):
                self.LUT[startII:endII, : ] = self.win.monitor.lineariseLums(self.LUT[startII:endII, : ], overrideGamma=gamma)

        #update the bits++ box with new LUT
        if self.method=='fast':
            #get bits into correct order, shape and add to header
            ramp16 = (self.LUT*(2**16-1)).astype(numpy.uint16) #go from ubyte to uint16
            ramp16 = numpy.reshape(ramp16,(256,1,3))
            #set most significant bits
            self._HEADandLUT[12::2,:,:] = (ramp16[:,:,:]>>8).astype(numpy.uint8)
            #set least significant bits
            self._HEADandLUT[13::2,:,:] = (ramp16[:,:,:]&255).astype(numpy.uint8)
            self._HEADandLUTstr = self._HEADandLUT.tostring()

    def _drawLUTtoScreen(self):
        """(private) Used to set the LUT in Bits++ mode.

        Should not be needed by user if attached to a ``psychopy.visual.Window()``
        since this will automatically draw the LUT as part of the screen refresh.
        """
        #push the projection matrix and set to orthorgaphic

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho( 0, self.win.size[0],self.win.size[1], 0, 0, 1 )    #this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        #draw the pixels
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL_multitexture.glActiveTextureARB(GL_multitexture.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glRasterPos2i(0,1)
        GL.glDrawPixelsub(GL.GL_RGB, self._HEADandLUT)
        #GL.glDrawPixels(524,1, GL.GL_RGB,GL.GL_UNSIGNED_BYTE, self._HEADandLUTstr)
        #return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode( GL.GL_PROJECTION )
        GL.glPopMatrix()
        GL.glMatrixMode( GL.GL_MODELVIEW )

    def setContrast(self,contrast,LUTrange=1.0):
        """Set the contrast of the LUT for bits++ mode only

        :Parameters:
            contrast : float in the range 0:1
                The contrast for the range being set
            LUTrange : float or array
                If a float is given then this is the fraction of the LUT to be used.
                If an array of floats is given, these will specify the start/stop points
                as fractions of the LUT. If an array of ints (0-255) is given these
                determine the start stop *indices* of the LUT

        Examples:
            ``setContrast(1.0,0.5)``
                will set the central 50% of the LUT so that a stimulus with
                contr=0.5 will actually be drawn with contrast 1.0

            ``setContrast(1.0,[0.25,0.5])``

            ``setContrast(1.0,[63,127])``
                will set the lower-middle quarter of the LUT
                (which might be useful in LUT animation paradigms)

        """
        self.contrast = contrast
        #setLUT uses contrast automatically
        self.setLUT(newLUT=None, gammaCorrect=True, LUTrange=LUTrange)

    def setGamma(self, newGamma):
        """Set the LUT to have the requested gamma value
        Currently also resets the LUT to be a linear contrast
        ramp spanning its full range. May change this to read
        the current LUT, undo previous gamm and then apply
        new one?"""
        self.gamma=newGamma
        self.setLUT() #easiest way to update
    def reset(self):
        """Deprecated: This was used on the old Bits++ to power-cycle the box
        It required the compiled dll, which only worked on windows and doesn't
        work with Bits#
        """
        reset()
    def _setupShaders(self):
        """creates and stores the shader programs needed for mono++ and color++ modes
        """
        if not haveShaders:
            return
        self._shaders={}
        self._shaders['mono++'] = shaders.compileProgram(shaders.vertSimple,
            shaders.bitsMonoModeFrag)
        self._shaders['color++'] = shaders.compileProgram(shaders.vertSimple,
            shaders.bitsColorModeFrag)

    def _prepareFBOrender(self):
        if self.mode=='mono++':
            GL.glUseProgram(self._shaders['mono++'])
        if self.mode=='color++':
            GL.glUseProgram(self._shaders['color++'])
    def _finishFBOrender(self):
        GL.glUseProgram(0)

class BitsSharp(BitsPlusPlus):
    """A class to support functions of the Bits#

    This device uses the CDC (serial port) connection to the bits box. To use it
    you must have followed the instructions from CRS Ltd to get your box into
    the CDC communication mode.

    On windows you must specify the COM port name.
    On OSX, if you don't specify a port then the first match of /dev/tty.usbmodemfa* will be used
    ON linux, if you don't specify a port then /dev/ttyS0 will be used
    """
    def __init__(self, win=None, portName=None, mode=''):
        self.OK=False
        if portName==None:
            if sys.platform == 'darwin':
                portNames = glob.glob('/dev/tty.usbmodemfa*')
                if not portNames:
                    logging.error("Could not connect to Bits Sharp: No serial ports were found at /dev/tty.usbmodemfa*")
                    return None
                else:
                    portName = portNames[0]
            elif sys.platform.startswith('linux'):
                portName = '/dev/ttyACM0'
        self.portName = portName
        self._com = self._connect()
        if self._com:
            self.OK=True
        else:
            return None
        self.info = self.getInfo()
        self.mode = mode
        self.win = win
        if self.win is not None:
            if not hasattr(self.win, '_prepareFBOrender'):
                logging.error("BitsSharp was given an object as win argument but this is not a visual.Window")
            self.win._prepareFBOrender = self._prepareFBOrender
            self.win._finishFBOrender = self._finishFBOrender
            self._setupShaders()
        else:
            logging.warning("%s was not given any PsychoPy win")

    def _connect(self):
        com = serial.Serial(self.portName)
        com.setBaudrate(19200)
        com.setParity('N')#none
        com.setStopbits(1)
        if not com.isOpen():
            com.open()
        return com
    def __del__(self):
        """If the user discards this object then close the serial port so it is released"""
        if hasattr(self, '_com'):
            self._com.close()
    def getInfo(self):
        """Returns a python dictionary of info about the box
        """
        self.read(timeout=0.5) #clear input buffer
        info={}
        #get product ('Bits_Sharp'?)
        self.sendMessage('$ProductType\r')
        time.sleep(0.1)
        info['ProductType'] = self.read().replace('#ProductType;','').replace(';\n\r','')
        #get serial number
        self.sendMessage('$SerialNumber\r')
        time.sleep(0.1)
        info['SerialNumber'] = self.read().replace('#SerialNumber;','').replace('\x00\n\r','')
        #get firmware date
        self.sendMessage('$FirmwareDate\r')
        time.sleep(0.1)
        info['FirmwareDate'] = self.read().replace('#FirmwareDate;','').replace(';\n\r','')
        return info

    @property
    def mode(self):
        return self.__dict__['mode']

    @mode.setter
    def mode(self, value):
        if value in [None, '']:
            self.__dict__['mode'] = ''
        elif ('mode' in self.__dict__) and value==self.mode:
            return #nothing to do here. Move along please
        elif value=='status':
            self.sendMessage('$statusScreen\r')
            self.__dict__['mode'] = 'status'
        elif 'storage' in value.lower():
            self.sendMessage('$USB_massStorage\r')
            self.__dict__['mode'] = 'massStorage'
            logging.info('Switched %s to %s mode' %(self.info['ProductType'], self.__dict__['mode']))
        elif value.startswith('bits'):
            self.sendMessage('$BitsPlusPlus\r')
            self.__dict__['mode'] = 'bits++'
            logging.info('Switched %s to %s mode' %(self.info['ProductType'], self.__dict__['mode']))
        elif value.startswith('mono'):
            self.sendMessage('$monoPlusPlus\r')
            self.__dict__['mode'] = 'mono++'
            logging.info('Switched %s to %s mode' %(self.info['ProductType'], self.__dict__['mode']))
        elif value.startswith('colo'):
            self.sendMessage('$colorPlusPlus\r')
            self.__dict__['mode'] = 'color++'
            logging.info('Switched %s to %s mode' %(self.info['ProductType'], self.__dict__['mode']))
        elif value.startswith('auto'):
            self.sendMessage('$colorPlusPlus\r')
            self.__dict__['mode'] = 'auto++'
            logging.info('Switched %s to %s mode' %(self.info['ProductType'], self.__dict__['mode']))

    @property
    def temporalDithering(self):
        """Temporal dithering can be set to True or False
        """
        return self.__dict__['temporalDithering']
    @temporalDithering.setter
    def temporalDithering(self, value):
        if value:
            self.sendMessage('$TemporalDithering=[ON]\r')
        else:
            self.sendMessage('$TemporalDithering=[OFF]\r')
        self.__dict__['temporalDithering'] = value

    @property
    def gammaCorrectFile(self):
        """The gamma correction file to be used
        """
        return self.__dict__['gammaCorrectFile']
    @gammaCorrectFile.setter
    def gammaCorrectFile(self, value):
        self.sendMessage('$enableGammaCorrection=[%s]\r' %(value))
        self.__dict__['gammaCorrectFile'] = value

    @property
    def monitorEDID(self):
        """Stores/sets the EDID file for the monitor.
        The edid files will be located in the EDID subdirectory of the flash disk.
        The file “automatic.edid” will be the file read from the connected monitor
        """
        return self.__dict__['monitorEDID']
    @monitorEDID.setter
    def monitorEDID(self, value):
        self.sendMessage('$setMonitorType=[%s]\r' %(value))
        self.__dict__['monitorEDID'] = value

    #functions
    def beep(self, freq=800, dur=1):
        """Make a beep with the internal
        """
        self.sendMessage('$Beep=[%i, %.4f]\r' %(freq, dur))

    def getVideoLine(self, lineN, nPixels):
        """Return the r,g,b values for a number of pixels on a particular video line

        :param lineN: the line number you want to read
        :param nPixels: the number of pixels you want to read

        :return: an Nx3 numpy array of uint8 values
        """
        self.read(timeout=0.5)
        self.sendMessage('$GetVideoLine=[%i, %i]\r' %(lineN, nPixels))
        time.sleep(0.5)
        raw = self.read(timeout=0.5)
        vals = raw.split(';')[1:-1]
        if len(vals)==0:
            logging.warning("No values returned by BitsSharp.getVideoLine(). Possibly not enough time to swith to status mode?")
        vals = numpy.array(vals, dtype=int).reshape([-1,3])
        return vals

    #helper functions (lower level)
    def sendMessage(self, msg):
        """Sends a string message to the BitsSharp. If the user has not ended the
        string with '\r' this will be added.
        """
        if not msg.endswith('\r'):
            msg += '\r'
        self._com.write(msg)
        logging.debug("Sent BitsSharp message: %s" %(repr(msg)))
    def read(self, timeout=0.1):
        """Get the current waiting characters from the serial port if there are any
        """
        self._com.setTimeout(timeout)
        nChars = self._com.inWaiting()
        raw = self._com.read(nChars)
        logging.debug("Got BitsSharp reply: %s" %(repr(raw)))
        return raw

    #TO DO: The following are either not yet implemented (or not tested)
    def start(self):
        raise NotImplemented
    def stop(self):
        raise NotImplemented

def init():
    """DEPRECATED: we used to initialise Bits++ via the compiled dll

    This only ever worked on windows and BitsSharp doesn't need it at all

    Note that, by default, bits++ will perform gamma correction
    that you don't want (unless you have the CRS calibration device)
    (Recommended that you use the BitsPlusPlus class rather than
    calling this directly)
    """
    if haveBitsDLL:
        try:
            retVal = _bits.bitsInit() #returns null if fails?
        except:
            logging.error('bits.init() barfed!')
            return 0
    return retVal

def setVideoMode(videoMode):
    """set the video mode of the bits++ (win32 only)

    bits8BITPALETTEMODE         =  0x00000001  #normal vsg mode

    NOGAMMACORRECT      =  0x00004000  #No gamma correction mode

    GAMMACORRECT            =  0x00008000  #Gamma correction mode

    VIDEOENCODEDCOMMS =  0x00080000

    (Recommended that you use the BitsLUT class rather than
    calling this directly)
    """
    if haveBitsDLL:
        return _bits.bitsSetVideoMode(videoMode)
    else:
        return 1

def reset(noGamma=True):
    """reset the bits++ box via the USB cable by initialising again
    Allows the option to turn off gamma correction
    """
    OK = init()
    if noGamma and OK: setVideoMode(NOGAMMACORRECT)
