#!/usr/bin/env python2

'''Display an image on `psycopy.visual.Window`'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging

from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.visual.basevisual import ContainerMixin, ColorMixin, TextureMixin

import numpy


class ImageStim(BaseVisualStim, ContainerMixin, ColorMixin, TextureMixin):
    '''Display an image on a :class:`psychopy.visual.Window`'''
    def __init__(self,
                 win,
                 image     =None,
                 mask    =None,
                 units   ="",
                 pos     =(0.0,0.0),
                 size    =None,
                 ori     =0.0,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 interpolate=False,
                 flipHoriz=False,
                 flipVert=False,
                 texRes=128,
                 name=None,
                 autoLog=None,
                 maskParams=None):
        """ """  # Empty docstring. All doc is in attributes
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(ImageStim, self).__init__(win, units=units, name=name, autoLog=False)#set autoLog at end of init
        self.__dict__['useShaders'] = win._haveShaders  #use shaders if available by default, this is a good thing

        #initialise textures for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.__dict__['maskParams'] = maskParams
        self.__dict__['mask'] = mask
        self.__dict__['texRes'] = texRes  # Not pretty (redefined later) but it works!

        # Other stuff
        self._imName = image
        self.isLumImage = None
        self.interpolate=interpolate
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        self._requestedSize=size
        self._origSize=None#if an image texture is loaded this will be updated
        self.size = val2array(size)
        self.pos = numpy.array(pos,float)
        self.ori = float(ori)
        self.depth=depth

        #color and contrast etc
        self.contrast = float(contrast)
        self.opacity = float(opacity)
        self.__dict__['colorSpace'] = colorSpace  #omit decorator
        self.setColor(color, colorSpace=colorSpace, log=False)
        self.rgbPedestal=[0,0,0]#does an rgb pedestal make sense for an image?

        # Set the image and mask-
        self.setImage(image, log=False)
        self.texRes = texRes  # rebuilds the mask

        #generate a displaylist ID
        self._listID = GL.glGenLists(1)
        self._updateList()#ie refresh display list

        # set autoLog now that params have been initialised
        self.__dict__['autoLog'] = autoLog or autoLog is None and self.win.autoLog
        if self.autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def _updateListShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False
        GL.glNewList(self._listID,GL.GL_COMPILE)

        #setup the shaderprogram
        if self.isLumImage: #for a luminance image do recoloring
            GL.glUseProgram(self.win._progSignedTexMask)
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1
        else: #for an rgb image there is no recoloring
            GL.glUseProgram(self.win._progImageStim)
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progImageStim, "texture"), 0) #set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progImageStim, "mask"), 1)  # mask is texture unit 1

        #mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D

        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        vertsPix = self.verticesPix #access just once because it's slower than basic property
        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1,0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,1,0)
        GL.glVertex2f(vertsPix[0,0], vertsPix[0,1])
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0,0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,0,0)
        GL.glVertex2f(vertsPix[1,0], vertsPix[1,1])
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0,1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,0,1)
        GL.glVertex2f(vertsPix[2,0], vertsPix[2,1])
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1,1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,1,1)
        GL.glVertex2f(vertsPix[3,0], vertsPix[3,1])
        GL.glEnd()

        #unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)

        GL.glEndList()

    #for the sake of older graphics cards------------------------------------
    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        self._needUpdate = False
        GL.glNewList(self._listID,GL.GL_COMPILE)
        GL.glColor4f(1.0,1.0,1.0,1.0)#glColor can interfere with multitextures
        #mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)

        #main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

        vertsPix = self.verticesPix #access just once because it's slower than basic property
        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,1,0)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,1,0)
        GL.glVertex2f(vertsPix[0,0], vertsPix[0,1])
        # left bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,0,0)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,0,0)
        GL.glVertex2f(vertsPix[1,0], vertsPix[1,1])
        # left top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,0,1)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,0,1)
        GL.glVertex2f(vertsPix[2,0], vertsPix[2,1])
        # right top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,1,1)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,1,1)
        GL.glVertex2f(vertsPix[3,0], vertsPix[3,1])
        GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()


    def __del__(self):
        if hasattr(self, '_listID'):
            GL.glDeleteLists(self._listID, 1)
        self.clearTextures()#remove textures from graphics card to prevent crash

    def draw(self, win=None):
        if win is None:
            win=self.win
        self._selectWindow(win)

        GL.glPushMatrix()#push before the list, pop after
        win.setScale('pix')

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

        if self._needTextureUpdate:
            self.setImage(value=self._imName, log=False)
        if self._needUpdate:
            self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()

    @attributeSetter
    def image(self, value):
        """The image file to be presented (most formats supported)
        """
        self.__dict__['image'] = self._imName = value

        wasLumImage = self.isLumImage
        if value is None:
            datatype = GL.GL_FLOAT
        else:
            datatype = GL.GL_UNSIGNED_BYTE
        self.isLumImage = self._createTexture(value, id=self._texID, stim=self,
            pixFormat=GL.GL_RGB, dataType=datatype,
            maskParams=self.maskParams, forcePOW2=False)
        #if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize is None:
            self.size = None  # set size to default
        #if we switched to/from lum image then need to update shader rule
        if wasLumImage != self.isLumImage:
            self._needUpdate=True
        self._needTextureUpdate = False
    def setImage(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'image', value, log)

    @attributeSetter
    def mask(self, value):
        """The alpha mask that can be used to control the outer shape of the stimulus

                + **None**, 'circle', 'gauss', 'raisedCos'
                + or the name of an image file (most formats supported)
                + or a numpy array (1xN or NxN) ranging -1:1
        """
        self.__dict__['mask'] = value
        self._createTexture(value, id=self._maskID,
            pixFormat=GL.GL_ALPHA,dataType=GL.GL_UNSIGNED_BYTE,
            stim=self,
            res=self.texRes, maskParams=self.maskParams)

    def setMask(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'mask', value, log)