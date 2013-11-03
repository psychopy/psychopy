#!/usr/bin/env python

'''Display an image on `psycopy.visual.Window`'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
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

from psychopy.tools.arraytools import val2array
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.visual.helpers import (pointInPolygon, polygonsOverlap,
                                     createTexture)

import numpy


class ImageStim(BaseVisualStim):
    '''Display an image on `psycopy.visual.Window`'''
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
                 name='', autoLog=True,
                 maskParams=None):
        """
        :Parameters:

            image :
                The image file to be presented (most formats supported)
            mask :
                The alpha mask that can be used to control the outer shape of the stimulus

                + **None**, 'circle', 'gauss', 'raisedCos'
                + or the name of an image file (most formats supported)
                + or a numpy array (1xN or NxN) ranging -1:1

            texRes:
                Sets the resolution of the mask (this is independent of the image resolution)

            maskParams: Various types of input. Default to None.
                This is used to pass additional parameters to the mask if those
                are needed.
                - For the 'raisedCos' mask, pass a dict: {'fringeWidth':0.2},
                where 'fringeWidth' is a parameter (float, 0-1), determining
                the proportion of the patch that will be blurred by the raised
                cosine edge.

        """
        BaseVisualStim.__init__(self, win, units=units, name=name, autoLog=autoLog)
        self.useShaders = win._haveShaders  #use shaders if available by default, this is a good thing

        #initialise textures for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.maskParams= maskParams
        self.texRes=texRes

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

        # Set the image and mask
        self.setImage(image, log=False)
        self.setMask(mask, log=False)

        #fix scaling to window coords
        self._calcSizeRendered()
        self._calcPosRendered()

        # _verticesRendered for .contains() and .overlaps()
        v = [(-.5,-.5), (-.5,.5), (.5,.5), (.5,-.5)]
        self._verticesRendered = numpy.array(self._sizeRendered, dtype=float) * v

        #generate a displaylist ID
        self._listID = GL.glGenLists(1)
        self._updateList()#ie refresh display list

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
        if self.isLumImage:
            GL.glUseProgram(self.win._progSignedTexMask)
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1

        #mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)#implicitly disables 1D

        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        flipHoriz = self.flipHoriz*(-2)+1#True=(-1), False->(+1)
        flipVert = self.flipVert*(-2)+1
        #calculate coords in advance:
        L = -self._sizeRendered[0]/2 * flipHoriz#vertices
        R =  self._sizeRendered[0]/2 * flipHoriz
        T =  self._sizeRendered[1]/2 * flipVert
        B = -self._sizeRendered[1]/2 * flipVert

        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1,0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,1,0)
        GL.glVertex2f(R,B)
        # left bottom
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0,0)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,0,0)
        GL.glVertex2f(L,B)
        # left top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,0,1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,0,1)
        GL.glVertex2f(L,T)
        # right top
        GL.glMultiTexCoord2f(GL.GL_TEXTURE0,1,1)
        GL.glMultiTexCoord2f(GL.GL_TEXTURE1,1,1)
        GL.glVertex2f(R,T)
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

        flipHoriz = self.flipHoriz*(-2)+1#True=(-1), False->(+1)
        flipVert = self.flipVert*(-2)+1
        #calculate vertices
        L = -self._sizeRendered[0]/2 * flipHoriz
        R =  self._sizeRendered[0]/2 * flipHoriz
        T =  self._sizeRendered[1]/2 * flipVert
        B = -self._sizeRendered[1]/2 * flipVert

        GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
        # right bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,1,0)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,1,0)
        GL.glVertex2f(R,B)
        # left bottom
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,0,0)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,0,0)
        GL.glVertex2f(L,B)
        # left top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,0,1)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,0,1)
        GL.glVertex2f(L,T)
        # right top
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,1,1)
        GL.glMultiTexCoord2fARB(GL.GL_TEXTURE1_ARB,1,1)
        GL.glVertex2f(R,T)
        GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()


    def __del__(self):
        GL.glDeleteLists(self._listID, 1)
        self.clearTextures()#remove textures from graphics card to prevent crash

    def contains(self, x, y=None):
        """Determines if a point x,y is on the image (within its boundary).

        See :class:`~psychopy.visual.ShapeStim` `.contains()`.
        """
        if hasattr(x, 'getPos'):
            x,y = x.getPos()
        elif type(x) in [list, tuple, numpy.ndarray]:
            x,y = x[0:2]
        return pointInPolygon(x, y, self)

    def overlaps(self, polygon):
        """Determines if the image overlaps another image or shape (`polygon`).

        See :class:`~psychopy.visual.ShapeStim` `.overlaps()`.
        """
        return polygonsOverlap(self, polygon)

    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self._texID)
        GL.glDeleteTextures(1, self._maskID)
    def draw(self, win=None):
        if win==None: win=self.win
        self._selectWindow(win)

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        win.setScale(self._winScale)
        #move to centre of stimulus and rotate
        GL.glTranslatef(self._posRendered[0],self._posRendered[1],0)
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        #the list just does the texture mapping

        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

        if self._needUpdate:
            self._updateList()
        GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()
    def setImage(self, value, log=True):
        """Set the image to be used for the stimulus to this new value
        """
        self._imName = value

        wasLumImage = self.isLumImage
        if value==None:
            datatype = GL.GL_FLOAT
        else:
            datatype = GL.GL_UNSIGNED_BYTE
        self.isLumImage = createTexture(value, id=self._texID, stim=self,
            pixFormat=GL.GL_RGB, dataType=datatype,
            maskParams=self.maskParams, forcePOW2=False)
        #if user requested size=None then update the size for new stim here
        if hasattr(self, '_requestedSize') and self._requestedSize==None:
            self.size = None  # set size to default
        if log and self.autoLog:
            self.win.logOnFlip("Set %s image=%s" %(self.name, value),
                level=logging.EXP,obj=self)
        #if we switched to/from lum image then need to update shader rule
        if wasLumImage != self.isLumImage:
            self._needUpdate=True
    def setMask(self,value, log=True):
        """Change the image to be used as an alpha-mask for the image
        """
        self.mask = value
        createTexture(value, id=self._maskID,
            pixFormat=GL.GL_ALPHA,dataType=GL.GL_UNSIGNED_BYTE,
            stim=self,
            res=self.texRes, maskParams=self.maskParams)
        if log and self.autoLog:
            self.win.logOnFlip("Set %s mask=%s" %(self.name, value),
                level=logging.EXP,obj=self)
