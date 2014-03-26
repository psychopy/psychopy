#!/usr/bin/env python2

'''A simple stimulus for loading images from a file and presenting at exactly
the resolution and color in the file (subject to gamma correction if set).'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import core, logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.monitorunittools import convertToPix
from psychopy.tools.attributetools import setWithOperation, logAttrib
from . import glob_vars

try:
    from PIL import Image
except ImportError:
    import Image

import numpy


class SimpleImageStim(object):
    """A simple stimulus for loading images from a file and presenting at exactly
    the resolution and color in the file (subject to gamma correction if set).

    Unlike the ImageStim, this type of stimulus cannot be rescaled, rotated or
    masked (although flipping horizontally or vertically is possible). Drawing will
    also tend to be marginally slower, because the image isn't preloaded to the
    graphics card. The slight advantage, however is that the stimulus will always be in its
    original aspect ratio, with no interplotation or other transformation.

    SimpleImageStim does not support a depth parameter (the OpenGL method
    that draws the pixels does not support it). Simple images will obscure any other
    stimulus type.


    """
    def __init__(self,
                 win,
                 image     ="",
                 units   ="",
                 pos     =(0.0,0.0),
                 flipHoriz=False,
                 flipVert=False,
                 name='', autoLog=True):
        """
        :Parameters:
            win :
                a :class:`~psychopy.visual.Window` object (required)
            image :
                The filename, including relative or absolute path. The image
                can be any format that the Python Imagin Library can import
                (which is almost all).
            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window` will be used.
                See :ref:`units` for explanation of other options.
            pos :
                a tuple (0.0,0.0) or a list [0.0,0.0] for the x and y of the centre of the stimulus.
                The origin is the screen centre, the units are determined
                by units (see above). Stimuli can be position beyond the
                window!
            name : string
                The name of the object to be using during logged messages about
                this stim
        """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(SimpleImageStim, self).__init__()

        #NB most stimuli use BaseVisualStim for the _set method and for
        # setting up win, name, units and autolog in __init__ but SimpleImage
        # shares very little with _Base so we do it manually here
        self.autoLog=False #this will be set later
        self.win=win
        self.name=name
        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units

        self.useShaders = win._haveShaders  #use shaders if available by default, this is a good thing

        self.pos = numpy.array(pos, float)
        self.setImage(image)
        #check image size against window size
        if (self.size[0]>self.win.size[0]) or (self.size[1]>self.win.size[1]):
            logging.warning("Image size (%s, %s)  was larger than window size (%s, %s). Will draw black screen." % (self.size[0], self.size[1], self.win.size[0], self.win.size[1]))

        #check position with size, warn if stimuli not fully drawn
        if ((self.pos[0]+(self.size[0]/2.0) > self.win.size[0]/2.0) or (self.pos[0]-(self.size[0]/2.0) < -self.win.size[0]/2.0)):
            logging.warning("Image position and width mean the stimuli does not fit the window in the X direction.")

        if ((self.pos[1]+(self.size[1]/2.0) > self.win.size[1]/2.0) or (self.pos[1]-(self.size[1]/2.0) < -self.win.size[1]/2.0)):
            logging.warning("Image position and height mean the stimuli does not fit the window in the Y direction.")

        #flip if necessary
        self.flipHoriz=False#initially it is false, then so the flip according to arg above
        self.setFlipHoriz(flipHoriz)
        self.flipVert=False#initially it is false, then so the flip according to arg above
        self.setFlipVert(flipVert)

        self._calcPosRendered()

        #set autoLog (now that params have been initialised)
        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, repr(self)))

    def setFlipHoriz(self,newVal=True, log=True):
        """If set to True then the image will be flipped horiztonally (left-to-right).
        Note that this is relative to the original image, not relative to the current state.
        """
        if newVal!=self.flipHoriz: #we need to make the flip
            self.imArray = numpy.flipud(self.imArray)#numpy and pyglet disagree about ori so ud<=>lr
        self.flipHoriz=newVal
        logAttrib(self, log, 'flipHoriz')
        self._needStrUpdate=True
    def setFlipVert(self,newVal=True, log=True):
        """If set to True then the image will be flipped vertically (top-to-bottom).
        Note that this is relative to the original image, not relative to the current state.
        """
        if newVal!=self.flipVert: #we need to make the flip
            self.imArray = numpy.fliplr(self.imArray)#numpy and pyglet disagree about ori so ud<=>lr
        self.flipVert=newVal
        logAttrib(self, log, 'flipVert')
        self._needStrUpdate=True
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        #NB TextStim overrides this function, so changes here may need changing there too
        if val==True and self.win._haveShaders==False:
            logging.error("Shaders were requested but aren't available. Shaders need OpenGL 2.0+ drivers")
        if val!=self.useShaders:
            self.useShaders=val
            self.setImage()
    def _updateImageStr(self):
        self._imStr=self.imArray.tostring()
        self._needStrUpdate=False
    def _selectWindow(self, win):
        #don't call switch if it's already the curr window
        if win!=glob_vars.currWindow and win.winType=='pyglet':
            win.winHandle.switch_to()
            glob_vars.currWindow = win
    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win==None: win=self.win
        self._selectWindow(win)
        #push the projection matrix and set to orthorgaphic
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glOrtho( 0, self.win.size[0],0, self.win.size[1], 0, 1 )#this also sets the 0,0 to be top-left
        #but return to modelview for rendering
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        if self._needStrUpdate: self._updateImageStr()
        #unbind any textures
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        #move to centre of stimulus
        GL.glRasterPos2f(self.win.size[0]/2.0 - self.size[0]/2.0 + self._posRendered[0],
            self.win.size[1]/2.0 - self.size[1]/2.0 + self._posRendered[1])

        #GL.glDrawPixelsub(GL.GL_RGB, self.imArr)
        GL.glDrawPixels(self.size[0],self.size[1],
            self.internalFormat,self.dataType,
            self._imStr)
        #return to 3D mode (go and pop the projection matrix)
        GL.glMatrixMode( GL.GL_PROJECTION )
        GL.glPopMatrix()
        GL.glMatrixMode( GL.GL_MODELVIEW )
    def _set(self, attrib, val, op='', log=True):
        """
        Deprecated. Use methods specific to the parameter you want to set

        e.g. ::

             stim.pos = [3,2.5]
             stim.ori = 45
             stim.phase += 0.5

        NB this method does not flag the need for updates any more - that is
        done by specific methods as described above.
        """
        if op==None: op=''
        #format the input value as float vectors
        if type(val) in (tuple, list):
            val=numpy.array(val, float)

        setWithOperation(self, attrib, val, op)
        logAttrib(self, log, attrib)
    def setPos(self, newPos, operation='', units=None, log=True):
        self._set('pos', val=newPos, op=operation, log=log)
        self._calcPosRendered()
    def setDepth(self,newDepth, operation='', log=True):
        self._set('depth', newDepth, operation, log=log)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in pixels"""
        self._posRendered = convertToPix(pos = self.pos, vertices=numpy.array([0,0]), units=self.units, win=self.win)

    def setImage(self,filename=None, log=True):
        """Set the image to be drawn.

        :Parameters:
            - filename:
                The filename, including relative or absolute path if necessary.
                Can actually also be an image loaded by PIL.

        """
        self.image=filename
        if type(filename) in [str, unicode]:
        #is a string - see if it points to a file
            if os.path.isfile(filename):
                self.filename=filename
                im = Image.open(self.filename)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
            else:
                logging.error("couldn't find image...%s" %(filename))
                core.quit()
                raise #so thatensure we quit
        else:
        #not a string - have we been passed an image?
            try:
                im = filename.copy().transpose(Image.FLIP_TOP_BOTTOM)
            except AttributeError: # ...but apparently not
                logging.error("couldn't find image...%s" %(filename))
                core.quit()
                raise #ensure we quit
            self.filename = repr(filename) #'<Image.Image image ...>'

        self.size = im.size
        #set correct formats for bytes/floats
        if im.mode=='RGBA':
              self.imArray = numpy.array(im).astype(numpy.ubyte)
              self.internalFormat = GL.GL_RGBA
        else:
             self.imArray = numpy.array(im.convert("RGB")).astype(numpy.ubyte)
             self.internalFormat = GL.GL_RGB
        self.dataType = GL.GL_UNSIGNED_BYTE
        self._needStrUpdate = True
        logAttrib(self, log, 'image', filename)
