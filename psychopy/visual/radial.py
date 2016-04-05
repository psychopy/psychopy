#!/usr/bin/env python2

'''Stimulus object for drawing radial stimuli, like an annulus, a rotating wedge,
    a checkerboard etc...'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
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

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter, logAttrib
from psychopy.visual.grating import GratingStim

try:
    from PIL import Image
except ImportError:
    import Image

import numpy
from numpy import pi

class RadialStim(GratingStim):
    """Stimulus object for drawing radial stimuli, like an annulus, a rotating wedge,
    a checkerboard etc...

    Ideal for fMRI retinotopy stimuli!

    Many of the capabilities are built on top of the GratingStim.

    This stimulus is still relatively new and I'm finding occasional gliches. it also takes longer to draw
    than a typical GratingStim, so not recommended for tasks where high frame rates are needed.
    """
    def __init__(self,
                 win,
                 tex     ="sqrXsqr",
                 mask    ="none",
                 units   ="",
                 pos     =(0.0,0.0),
                 size    =(1.0,1.0),
                 radialCycles=3,
                 angularCycles=4,
                 radialPhase=0,
                 angularPhase=0,
                 ori     =0.0,
                 texRes =64,
                 angularRes=100,
                 visibleWedge=(0, 360),
                 rgb   =None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 dkl=None,
                 lms=None,
                 contrast=1.0,
                 opacity=1.0,
                 depth=0,
                 rgbPedestal = (0.0,0.0,0.0),
                 interpolate=False,
                 name='', autoLog=True):
        """
        :Parameters:

            texRes : (default= *128* )
                resolution of the texture (if not loading from an image file)
            angularRes : (default= *100* )
                100, the number of triangles used to make the sti
            radialPhase :
                the phase of the texture from the centre to the perimeter
                of the stimulus (in radians)
            angularPhase :
                the phase of the texture around the stimulus (in radians)
        """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(RadialStim, self).__init__(win, units=units, name=name, autoLog=False) #autolog should start off false

        self.useShaders = win._haveShaders  #use shaders if available by default, this is a good thing

        # JRG: hack to dodge method-resolution-order issues:
        # work-around #1 (not currently implemented: ugly, and lead to test failures on travis-ci)
        # self._updateList() is defined in BaseVisualStim and calls _updateListShaders or NoShaders
        # as needed. However, this also gets called in GratingStim.__init__, which is
        # called above by super(RadialStim, self).__init__()
        # so strategy: let GratingStim.__init__ do its thing, THEN rearrange the
        # namespace so that BaseVisualStim._updateList can do its thing during
        # the normal operation of RadialStim. There's got to be a better way:
        # initially hide _updateListShadersRadial and _updateListNoShadersRadial
        # now unhide them, since will not need GratingStim.__init__ again:

        # uncomment these lines to implement #1, and change _updataListShaders to _updateListShadersRadial, etc
        #self._updateListShaders = self._updateListShadersRadial
        #self._updateListNoShaders = self._updateListNoShadersRadial

        # workaround #2: comment out self._updateList() in GratingStim.__init__ line 162

        # UGLY HACK again. (See same section in GratingStim for ideas)
        self.__dict__['contrast'] = 1
        self.__dict__['size'] = 1
        self.__dict__['sf'] = 1
        self.__dict__['tex'] = tex

        #initialise textures for stimulus
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.maskParams = None
        self.maskRadialPhase = 0
        self.texRes = texRes #must be power of 2
        self.interpolate = interpolate
        self.rgbPedestal = val2array(rgbPedestal, False, length=3)

        #these are defined by the GratingStim but will just cause confusion here!
        self.setSF = None
        self.setPhase = None

        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        elif dkl!=None:
            logging.warning("Use of dkl arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(dkl, colorSpace='dkl')
        elif lms!=None:
            logging.warning("Use of lms arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(lms, colorSpace='lms')
        else:
            self.setColor(color)

        self.ori = float(ori)
        self.angularRes = angularRes
        self.radialPhase = radialPhase
        self.radialCycles = radialCycles
        self.visibleWedge = visibleWedge
        self.angularCycles = angularCycles
        self.angularPhase = angularPhase
        self.pos = numpy.array(pos, float)
        self.depth=depth
        self.__dict__['sf'] = 1
        self.size = val2array(size, False)

        self.tex = tex
        self.mask = mask
        self.contrast = float(contrast)
        self.opacity = float(opacity)

        #
        self._triangleWidth = pi*2/self.angularRes
        self._angles = numpy.arange(0,pi*2, self._triangleWidth, dtype='float64')
        #which vertices are visible?
        self._visible = (self._angles>=(self.visibleWedge[0]*pi/180))#first edge of wedge
        self._visible[(self._angles+self._triangleWidth)*180/pi>(self.visibleWedge[1])] = False#second edge of wedge
        self._nVisible = numpy.sum(self._visible)*3

        self._updateTextureCoords()
        self._updateMaskCoords()
        self._updateVerticesBase()
        self._updateVertices()
        if not self.useShaders:
            #generate a displaylist ID
            self._listID = GL.glGenLists(1)
            self._updateList()#ie refresh display list

        #set autoLog (now that params have been initialised)
        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, repr(self)))

    @attributeSetter
    def mask(self, value):
        """The alpha mask that forms the shape of the resulting image

        Value should one of:

            + 'circle', 'gauss', 'raisedCos', **None** (resets to default)
            + or the name of an image file (most formats supported)
            + or a numpy array (1xN) ranging -1:1

        Note that the mask for `RadialStim` is somewhat different to the
        mask for :class:`ImageStim`. For `RadialStim` it is a 1D array
        specifying the luminance profile extending outwards from the
        center of the stimulus, rather than a 2D array
        """
        self.__dict__['mask'] = value
        res = self.texRes#resolution of texture - 128 is bearable
        step = 1.0/res
        rad = numpy.arange(0,1+step,step)
        if type(self.mask) == numpy.ndarray:
            #handle a numpy array
            intensity = 255*self.mask.astype(float)
            res = len(intensity)
            fromFile=0
        elif type(self.mask) == list:
            #handle a numpy array
            intensity = 255*numpy.array(self.mask, float)
            res = len(intensity)
            fromFile=0
        elif self.mask == "circle":
            intensity = 255.0*(rad<=1)
            fromFile=0
        elif self.mask == "gauss":
            sigma = 1/3.0;
            intensity = 255.0*numpy.exp( -rad**2.0 / (2.0*sigma**2.0) )#3sd.s by the edge of the stimulus
            fromFile=0
        elif self.mask == "radRamp":#a radial ramp
            intensity = 255.0-255.0*rad
            intensity = numpy.where(rad<1, intensity, 0)#half wave rectify
            fromFile=0
        elif self.mask in [None,"none","None"]:
            res=4
            intensity = 255.0*numpy.ones(res,float)
            fromFile=0
        else:#might be a filename of a tiff
            try:
                im = Image.open(self.mask)
                im = im.transpose(Image.FLIP_TOP_BOTTOM)
                im = im.resize([max(im.size), max(im.size)],Image.BILINEAR)#make it square
            except IOError, (details):
                logging.error("couldn't load mask...%s: %s" %(value,details))
                return
            res = im.size[0]
            im = im.convert("L")#force to intensity (in case it was rgb)
            intensity = numpy.asarray(im)

        data = intensity.astype(numpy.uint8)
        mask = data.tostring()#serialise

        #do the openGL binding
        if self.interpolate: smoothing=GL.GL_LINEAR
        else: smoothing=GL.GL_NEAREST
        GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
        GL.glTexImage1D(GL.GL_TEXTURE_1D, 0, GL.GL_ALPHA,
                        res, 0,
                        GL.GL_ALPHA, GL.GL_UNSIGNED_BYTE, mask)
        GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
        GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_MAG_FILTER,smoothing)     #linear smoothing if texture is stretched
        GL.glTexParameteri(GL.GL_TEXTURE_1D,GL.GL_TEXTURE_MIN_FILTER,smoothing)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)
        GL.glEnable(GL.GL_TEXTURE_1D)

        self._needUpdate = True

    def setSize(self, value, operation='', log=True):
        self._set('size', value, operation, log=log)
        self._needVertexUpdate=True
        self._needUpdate = True
    def setAngularCycles(self,value,operation='', log=True):
        """Set the number of cycles going around the stimulus.

        i.e. it controls the number of 'spokes'
        """
        self._set('angularCycles', value, operation, log=log)
        self._updateTextureCoords()
        self._needUpdate = True
    def setRadialCycles(self,value,operation='', log=True):
        """Set the number of texture cycles from centre to periphery

        i.e. it controls the number of 'rings'
        """
        self._set('radialCycles', value, operation, log=log)
        self._updateTextureCoords()
        self._needUpdate = True
    def setAngularPhase(self,value, operation='', log=True):
        """Set the angular phase (like orientation) of the texture (wraps 0-1).

        This is akin to setting the orientation of the texture around the
        stimulus. If possible, it is more efficient to rotate the stimulus
        using its `ori` setting instead."""
        self._set('angularPhase', value, operation, log=log)
        self._updateTextureCoords()
        self._needUpdate = True
    def setRadialPhase(self,value, operation='', log=True):
        """Set the radial phase of the texture (wraps 0-1).

        Can be used to drift concentric rings out/inwards
        """
        self._set('radialPhase', value, operation, log=log)
        self._updateTextureCoords()
        self._needUpdate = True

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every `win.flip()` if you want the
        stimulus to appear on that frame and then update the screen
        again.

        If `win` is specified then override the normal window of this stimulus.
        """
        if win==None: win=self.win
        self._selectWindow(win)

        #do scaling
        GL.glPushMatrix()#push before the list, pop after
        #scale the viewport to the appropriate size
        self.win.setScale('pix')
        if self.useShaders:
            #setup color
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

            #assign vertex array
            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.verticesPix.ctypes)

            #then bind main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            GL.glEnable(GL.GL_TEXTURE_2D)
            #and mask
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glEnable(GL.GL_TEXTURE_1D)

            #setup the shaderprogram
            GL.glUseProgram(self.win._progSignedTexMask1D)
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "texture"), 0) #set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "mask"), 1)  # mask is texture unit 1

            #set pointers to visible textures
            GL.glClientActiveTexture(GL.GL_TEXTURE0)
            GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._visibleTexture.ctypes)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            #mask
            GL.glClientActiveTexture(GL.GL_TEXTURE1)
            GL.glTexCoordPointer(1, GL.GL_DOUBLE, 0, self._visibleMask.ctypes)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            #do the drawing
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

            #unbind the textures
            GL.glClientActiveTexture(GL.GL_TEXTURE1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            #main texture
            GL.glClientActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glDisable(GL.GL_TEXTURE_2D)
            #disable set states
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            GL.glUseProgram(0)
        else:
            #the list does the texture mapping
            if self._needTextureUpdate:
                self.setTex(value=self.tex, log=False)
            if self._needUpdate:
                self._updateList()
            GL.glCallList(self._listID)

        #return the view to previous state
        GL.glPopMatrix()

    def _updateVerticesBase(self):
        """Update the base vertices if angular resolution changes. These will be
        multiplied by the size and rotation matrix before rendering"""
        #triangles = [trisX100, verticesX3, xyX2]
        vertsBase = numpy.zeros([self.angularRes, 3, 2])
        vertsBase[:,1,0] = numpy.sin(self._angles) #x position of 1st outer vertex
        vertsBase[:,1,1] = numpy.cos(self._angles) #y position of 1st outer vertex
        vertsBase[:,2,0] = numpy.sin(self._angles+self._triangleWidth)#x position of 2nd outer vertex
        vertsBase[:,2,1] = numpy.cos(self._angles+self._triangleWidth)#y position of 2nd outer vertex
        vertsBase /= 2.0 #size should be 1.0, so radius should be 0.5
        vertsBase = vertsBase[self._visible,:,:]
        self._verticesBase = vertsBase.reshape(self._nVisible,2)

    def _updateTextureCoords(self):
        #calculate texture coordinates if angularCycles or Phase change
        self._textureCoords = numpy.zeros([self.angularRes, 3, 2])
        self._textureCoords[:,0,0] = (self._angles+self._triangleWidth/2)*self.angularCycles/(2*pi)+self.angularPhase #x position of inner vertex
        self._textureCoords[:,0,1] = 0.25+-self.radialPhase #y position of inner vertex
        self._textureCoords[:,1,0] = (self._angles)*self.angularCycles/(2*pi)+self.angularPhase #x position of 1st outer vertex
        self._textureCoords[:,1,1] = 0.25+self.radialCycles-self.radialPhase#y position of 1st outer vertex
        self._textureCoords[:,2,0] = (self._angles+self._triangleWidth)*self.angularCycles/(2*pi)+self.angularPhase#x position of 2nd outer vertex
        self._textureCoords[:,2,1] = 0.25+self.radialCycles-self.radialPhase#y position of 2nd outer vertex
        self._visibleTexture = self._textureCoords[self._visible,:,:].reshape(self._nVisible,2)

    def _updateMaskCoords(self):
        #calculate mask coords
        self._maskCoords = numpy.zeros([self.angularRes,3]) + self.maskRadialPhase
        self._maskCoords[:,1:] = 1 + self.maskRadialPhase#all outer points have mask value of 1
        self._visibleMask = self._maskCoords[self._visible,:]

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

        #assign vertex array
        arrPointer = self.verticesPix.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, arrPointer)

        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask1D)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask1D, "mask"), 1)  # mask is texture unit 1

        #set pointers to visible textures
        GL.glClientActiveTexture(GL.GL_TEXTURE0)
        arrPointer = self._visibleTexture.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, arrPointer)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #then bind main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        #mask
        GL.glClientActiveTexture(GL.GL_TEXTURE1)
        arrPointer = self._visibleMask.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glTexCoordPointer(1, GL.GL_FLOAT, 0, arrPointer)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #and mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        #do the drawing
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible*3)
        #disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glUseProgram(0)
        #setup the shaderprogram
        GL.glEndList()

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
        GL.glColor4f(1.0,1.0,1.0,self.opacity)#glColor can interfere with multitextures

        #assign vertex array
        GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.verticesPix.ctypes)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)

        #bind and enable textures
        #main texture
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        #mask
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glBindTexture(GL.GL_TEXTURE_1D, self._maskID)
        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_TEXTURE_1D)

        #set pointers to visible textures
        #mask
        GL.glClientActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0, self._visibleMask.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        #texture
        GL.glClientActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glTexCoordPointer(2, GL.GL_DOUBLE, 0,self._visibleTexture.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        #do the drawing
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, self._nVisible)

        #disable set states
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glEndList()

    def setMask(self,value, log=True):
        """Change the alpha-mask for the stimulus
        """
        self.mask = value
        logAttrib(self, log, 'mask')

    def __del__(self):
        if not self.useShaders:
            GL.glDeleteLists(self._listID, 1)
        self.clearTextures()#remove textures from graphics card to prevent crash

    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self._texID)
        GL.glDeleteTextures(1, self._maskID)
