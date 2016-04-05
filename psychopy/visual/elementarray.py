#!/usr/bin/env python2

'''This stimulus class defines a field of elements whose behaviour can be
independently controlled. Suitable for creating 'global form' stimuli or more
detailed random dot stimuli.'''

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
from psychopy.tools.attributetools import setWithOperation, logAttrib
from psychopy.tools.monitorunittools import convertToPix
from psychopy.visual.helpers import setColor
from psychopy.visual.basevisual import MinimalStim, TextureMixin
from . import glob_vars

import numpy

class ElementArrayStim(MinimalStim, TextureMixin):
    """
    This stimulus class defines a field of elements whose behaviour can be independently
    controlled. Suitable for creating 'global form' stimuli or more detailed random dot
    stimuli.
    This stimulus can draw thousands of elements without dropping a frame, but in order
    to achieve this performance, uses several OpenGL extensions only available on modern
    graphics cards (supporting OpenGL2.0). See the ElementArray demo.
    """
    def __init__(self,
                 win,
                 units = None,
                 fieldPos = (0.0,0.0),
                 fieldSize = (1.0,1.0),
                 fieldShape = 'circle',
                 nElements = 100,
                 sizes = 2.0,
                 xys = None,
                 rgbs = None,
                 colors=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacities = 1.0,
                 depths = 0,
                 fieldDepth = 0,
                 oris = 0,
                 sfs=1.0,
                 contrs = 1,
                 phases=0,
                 elementTex='sin',
                 elementMask='gauss',
                 texRes=48,
                 interpolate=True,
                 name='', autoLog=True):

        """
        :Parameters:

            win :
                a :class:`~psychopy.visual.Window` object (required)

            units : **None**, 'height', 'norm', 'cm', 'deg' or 'pix'
                If None then the current units of the :class:`~psychopy.visual.Window`
                will be used. See :ref:`units` for explanation of other options.

            fieldPos :
                The centre of the array of elements

            fieldSize :
                The size of the array of elements (this will be overridden by
                setting explicit xy positions for the elements)

            fieldShape :
                The shape of the array ('circle' or 'sqr')

            nElements :
                number of elements in the array

            sizes :
                an array of sizes Nx1, Nx2 or a single value

            xys :
                the xy positions of the elements, relative to the field centre
                (fieldPos)

            colors :
                specifying the color(s) of the elements.
                Should be Nx1 (different intensities), Nx3 (different colors) or 1x3
                (for a single color).

            colorSpace :
                The type of color specified is the same as
                those in other stimuli ('rgb','dkl','lms'...) but note that for
                this stimulus you cannot currently use text-based colors (e.g. names
                or hex values)

            opacities :
                the opacity of each element (Nx1 or a single value)

            depths :
                the depths of the elements (Nx1), relative the overall depth
                of the field (fieldDepth)

            fieldDepth :
                the depth of the field (will be added to the depths of the
                elements)

            oris :
                the orientations of the elements (Nx1 or a single value). oris
                are in degrees, and can be greater than 360 and smaller than 0.
                An ori of 0 is vertical, and increasing ori values are
                increasingly clockwise.

            sfs :
                the spatial frequencies of the elements (Nx1, Nx2 or a single
                value)

            contrs :
                the contrasts of the elements, ranging -1 to +1 (Nx1 or a
                single value)

            phases :
                the spatial phase of the texture on the stimulus (Nx1 or a
                single value)

            elementTex :
                the texture, to be used by all elements (e.g. 'sin', 'sqr',.. ,
                'myTexture.tif', numpy.ones([48,48]))

            elementMask :
                the mask, to be used by all elements (e.g. 'circle', 'gauss',... ,
                'myTexture.tif', numpy.ones([48,48]))

            texRes :
                the number of pixels in the textures (overridden if an array
                or image is provided)

            name : string
                The name of the objec to be using during logged messages about
                this stim

        """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(ElementArrayStim, self).__init__(name=name, autoLog=False)

        self.autoLog=False #until all params are set
        self.win=win
        self.name=name

        #unit conversions
        if units!=None and len(units): self.units = units
        else: self.units = win.units
        self.fieldPos = fieldPos
        self.fieldSize = fieldSize
        self.fieldShape = fieldShape
        self.nElements = nElements
        #info for each element
        self.sizes = sizes
        self.xys = self.verticesBase = xys
        self.opacities = opacities
        self.oris = oris
        self.contrs = contrs
        self.phases = phases
        self._needVertexUpdate=True
        self._needColorUpdate=True
        self.useShaders=True
        self.interpolate=interpolate
        self.fieldDepth=fieldDepth
        self.depths=depths
        if self.win.winType != 'pyglet':
            raise TypeError('ElementArrayStim requires a pyglet context')
        if not self.win._haveShaders:
            raise Exception("ElementArrayStim requires shaders support and floating point textures")

        self.colorSpace=colorSpace
        if rgbs!=None:
            logging.warning("Use of the rgb argument to ElementArrayStim is deprecated. Please use colors and colorSpace args instead")
            self.setColors(rgbs, colorSpace='rgb', log=False)
        else:
            self.setColors(colors, colorSpace=colorSpace, log=False)

        #Deal with input for fieldpos and fieldsize
        self.fieldPos = val2array(fieldPos, False)
        self.fieldSize = val2array(fieldSize, False)

        #create textures
        self.texRes = texRes
        self._texID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._texID))
        self._maskID = GL.GLuint()
        GL.glGenTextures(1, ctypes.byref(self._maskID))
        self.setMask(elementMask, log=False)
        self.setTex(elementTex, log=False)

        self.setContrs(contrs, log=False)
        self.setOpacities(opacities, log=False)#opacities is used by setRgbs, so this needs to be early
        self.setXYs(xys, log=False)
        self.setOris(oris, log=False)
        self.setSizes(sizes, log=False) #set sizes before sfs (sfs may need it formatted)
        self.setSfs(sfs, log=False)
        self.setPhases(phases, log=False)
        self._updateVertices()

        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def _selectWindow(self, win):
        #don't call switch if it's already the curr window
        if win!=glob_vars.currWindow and win.winType=='pyglet':
            win.winHandle.switch_to()
            glob_vars.currWindow = win

    def setXYs(self,value=None, operation='', log=True):
        """Set the xy values of the element centres (relative to the centre of the field).
        Values should be:

            - None
            - an array/list of Nx2 coordinates.

        If value is None then the xy positions will be generated automatically, based
        on the fieldSize and fieldPos. In this case opacity will also be overridden
        by this function (it is used to make elements outside the field invisible.
        """
        if value==None:
            if self.fieldShape in ['sqr', 'square']:
                self.xys = numpy.random.rand(self.nElements,2)*self.fieldSize - self.fieldSize/2 #initialise a random array of X,Y
                #gone outside the square
                self.xys[:,0] = ((self.xys[:,0]+self.fieldSize[0]/2) % self.fieldSize[0])-self.fieldSize[0]/2
                self.xys[:,1] = ((self.xys[:,1]+self.fieldSize[1]/2) % self.fieldSize[1])-self.fieldSize[1]/2
            elif self.fieldShape is 'circle':
                #take twice as many elements as we need (and cull the ones outside the circle)
                xys = numpy.random.rand(self.nElements*2,2)*self.fieldSize - self.fieldSize/2 #initialise a random array of X,Y
                #gone outside the square
                xys[:,0] = ((xys[:,0]+self.fieldSize[0]/2) % self.fieldSize[0])-self.fieldSize[0]/2
                xys[:,1] = ((xys[:,1]+self.fieldSize[1]/2) % self.fieldSize[1])-self.fieldSize[1]/2
                #use a circular envelope and flips dot to opposite edge if they fall
                #beyond radius.
                #NB always circular - uses fieldSize in X only
                normxy = xys/(self.fieldSize/2.0)
                dotDist = numpy.sqrt((normxy[:,0]**2.0 + normxy[:,1]**2.0))
                self.xys = xys[dotDist<1.0,:][0:self.nElements]
        else:
            #make into an array
            if type(value) in [int, float, list, tuple]:
                value = numpy.array(value, dtype=float)
            #check shape
            if not (value.shape in [(),(2,),(self.nElements,2)]):
                raise ValueError("New value for setXYs should be either None or Nx2")
            #set value
            setWithOperation(self, 'xys', value, operation)
        self._needVertexUpdate=True
        logAttrib(self, log, 'XYs', type(value))
    def setOris(self,value,operation='', log=True):
        """Set the orientation for each element.
        Should either be a single value or an Nx1 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,)]:
            value = value.repeat(self.nElements)
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            pass #is already Nx1
        else:
            raise ValueError("New value for setOris should be either Nx1 or a single value")

        #set value
        setWithOperation(self, 'oris', value, operation)
        logAttrib(self, log, 'oris', type(value))
        self._needVertexUpdate=True
    #----------------------------------------------------------------------
    def setSfs(self, value,operation='', log=True):
        """Set the spatial frequency for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list (spatial frequency of the element in X and Y).

        If the units for the stimulus are 'pix' or 'norm' then the units of sf
        are cycles per stimulus width. For units of 'deg' or 'cm' the units
        are c/cm or c/deg respectively.

        """

        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,),(2,)]:
            value = numpy.resize(value, [self.nElements,2])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(2,1) #repeat once on dim 1
        elif value.shape == (self.nElements,2):
            pass#all is good
        else:
            raise ValueError("New value for setSfs should be either Nx1, Nx2 or a single value")

        # Set value and log
        setWithOperation(self, 'sfs', value, operation)
        logAttrib(self, log, 'sfs', type(value))

    def setOpacities(self,value,operation='', log=True):
        """Set the opacity for each element.
        Should either be a single value or an Nx1 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,)]:
            value = value.repeat(self.nElements)
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            pass #is already Nx1
        else:
            raise ValueError("New value for setOpacities should be either Nx1 or a single value")

        #set value and log
        setWithOperation(self, 'opacities', value, operation)
        logAttrib(self, log, 'opacities', type(value))
    def setSizes(self,value,operation='', log=True):
        """Set the size for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape in [(),(1,),(2,)]:
            value = numpy.resize(value, [self.nElements,2])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(2,1) #repeat once on dim 1
        elif value.shape == (self.nElements,2):
            pass#all is good
        else:
            raise ValueError("New value for setSizes should be either Nx1, Nx2 or a single value")

        #set value and log
        setWithOperation(self, 'sizes', value, operation)
        logAttrib(self, log, 'sizes', type(value))
        self._needVertexUpdate=True
        self._needTexCoordUpdate=True
    def setPhases(self,value,operation='', log=True):
        """Set the phase for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
          - an Nx2 array/list (for separate X and Y phase)
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)

        #check shape
        if value.shape in [(),(1,),(2,)]:
            value = numpy.resize(value, [self.nElements,2])
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            value.shape=(self.nElements,1)#set to be 2D
            value = value.repeat(2,1) #repeat once on dim 1
        elif value.shape == (self.nElements,2):
            pass#all is good
        else:
            raise ValueError("New value for setPhases should be either Nx1, Nx2 or a single value")

        #set value and log
        setWithOperation(self, 'phases', value, operation)
        logAttrib(self, log, 'phases', type(value))
        self._needTexCoordUpdate=True
    def setRgbs(self,value,operation='', log=True):
        """DEPRECATED (as of v1.74.00). Please use setColors() instead
        """
        self.setColors(value,operation, log=log)
    def setColors(self, color, colorSpace=None, operation='', log=True):
        """Set the color of the stimulus. See :ref:`colorspaces` for further information
        about the various ways to specify colors and their various implications.

        :Parameters:

        color :
            Can be specified in one of many ways.

            You must provide a triplet of values, which refer to the coordinates
            in one of the :ref:`colorspaces`. If no color space is specified then the color
            space most recently used for this stimulus is used again.

                myStim.setColor([1.0,-1.0,-1.0], 'rgb')#a red color in rgb space
                myStim.setColor([0.0,45.0,1.0], 'dkl') #DKL space with elev=0, azimuth=45
                myStim.setColor([0,0,255], 'rgb255') #a blue stimulus using rgb255 space

            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x].

                myStim.setColor(255, 'rgb255') #all guns o max

        colorSpace : string or None

            defining which of the :ref:`colorspaces` to use. For strings and hex
            values this is not needed. If None the default colorSpace for the stimulus is
            used (defined during initialisation).

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)

            for colors specified as a triplet of values (or single intensity value)
            the new value will perform this operation on the previous color

                thisStim.setColor([1,1,1],'rgb255','+')#increment all guns by 1 value
                thisStim.setColor(-1, 'rgb', '*') #multiply the color by -1 (which in this space inverts the contrast)
                thisStim.setColor([10,0,0], 'dkl', '+')#raise the elevation from the isoluminant plane by 10 deg
        """
        setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='rgbs', #or 'fillRGB' etc
                    colorAttrib='colors',
                    colorSpaceAttrib='colorSpace',log=log)
        #check shape
        if self.rgbs.shape in [(), (1,),(3,)]:
            self.rgbs = numpy.resize(self.rgbs, [self.nElements,3])
        elif self.rgbs.shape in [(self.nElements,), (self.nElements,1)]:
            self.rgbs.shape=(self.nElements,1)#set to be 2D
            self.rgbs = self.rgbs.repeat(3,1) #repeat once on dim 1
        elif self.rgbs.shape == (self.nElements,3):
            pass#all is good
        else:
            raise ValueError("New value for setRgbs should be either Nx1, Nx3 or a single value")
        self._needColorUpdate=True
    def setContrs(self,value,operation='', log=True):
        """Set the contrast for each element.
        Should either be:

          - a single value
          - an Nx1 array/list
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape in [(),(1,)]:
            value = value.repeat(self.nElements)
        elif value.shape in [(self.nElements,), (self.nElements,1)]:
            pass #is already Nx1
        else:
            raise ValueError("New value for setContrs should be either Nx1 or a single value")

        #set value and log
        setWithOperation(self, 'contrs', value, operation)
        logAttrib(self, log, 'contrs', type(value))
        self._needColorUpdate=True
    def setFieldPos(self,value,operation='', log=True):
        """Set the centre of the array (X,Y)
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape != (2,):
            raise ValueError("New value for setFieldPos should be [x,y]")

        #set value and log
        setWithOperation(self, 'fieldPos', value, operation)
        logAttrib(self, log, 'fieldPos', type(value))
        self._needVertexUpdate = True
    def setPos(self, newPos=None, operation='', units=None, log=True):
        """Obselete - users should use setFieldPos or instead of setPos
        """
        logging.error("User called ElementArrayStim.setPos(pos). Use ElementArrayStim.setFieldPos(pos) instead.")

    def setFieldSize(self,value,operation='', log=True):
        """Set the size of the array on the screen (will override
        current XY positions of the elements)
        """
        #make into an array
        if type(value) in [int, float, list, tuple]:
            value = numpy.array(value, dtype=float)
        #check shape
        if value.shape not in [(2,),(1,)]:
            raise ValueError("New value for setFieldSize should be [x,y] or a single value")

        #set value and log
        setWithOperation(self, 'fieldSize', value, operation)
        logAttrib(self, log, 'fieldSize')
        self.setXYs(log=False)#to reflect new settings, overriding individual xys
    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.update() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win==None: win=self.win
        self._selectWindow(win)

        if self._needVertexUpdate:
            self._updateVertices()
        if self._needColorUpdate:
            self.updateElementColors()
        if self._needTexCoordUpdate:
            self.updateTextureCoords()

        #scale the drawing frame and get to centre of field
        GL.glPushMatrix()#push before drawing, pop after
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)#push the data for client attributes

        #GL.glLoadIdentity()
        self.win.setScale('pix')

        GL.glColorPointer(4, GL.GL_DOUBLE, 0, self._RGBAs.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        GL.glVertexPointer(3, GL.GL_DOUBLE, 0, self.verticesPix.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))

        #setup the shaderprogram
        GL.glUseProgram(self.win._progSignedTexMask)
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "texture"), 0) #set the texture to be texture unit 0
        GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTexMask, "mask"), 1)  # mask is texture unit 1

        #bind textures
        GL.glActiveTexture (GL.GL_TEXTURE1)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture (GL.GL_TEXTURE0)
        GL.glBindTexture (GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        #setup client texture coordinates first
        GL.glClientActiveTexture (GL.GL_TEXTURE0)
        GL.glTexCoordPointer (2, GL.GL_DOUBLE, 0, self._texCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glClientActiveTexture (GL.GL_TEXTURE1)
        GL.glTexCoordPointer (2, GL.GL_DOUBLE, 0, self._maskCoords.ctypes)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, self.verticesPix.shape[0]*4)

        #unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        #main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)
        #disable states
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glUseProgram(0)
        GL.glPopClientAttrib()
        GL.glPopMatrix()

    def _updateVertices(self):
        """Sets Stim.verticesPix from fieldPos and
        """

        #Handle the orientation, size and location of each element in native units
        #
        radians = 0.017453292519943295

        #so we can do matrix rotation of coords we need shape=[n*4,3]
        #but we'll convert to [n,4,3] after matrix math
        verts=numpy.zeros([self.nElements*4, 3],'d')
        wx = -self.sizes[:,0]*numpy.cos(self.oris[:]*radians)/2
        wy = self.sizes[:,0]*numpy.sin(self.oris[:]*radians)/2
        hx = self.sizes[:,1]*numpy.sin(self.oris[:]*radians)/2
        hy = self.sizes[:,1]*numpy.cos(self.oris[:]*radians)/2

        #X vals of each vertex relative to the element's centroid
        verts[0::4,0] = -wx - hx
        verts[1::4,0] = +wx - hx
        verts[2::4,0] = +wx + hx
        verts[3::4,0] = -wx + hx

        #Y vals of each vertex relative to the element's centroid
        verts[0::4,1] = -wy - hy
        verts[1::4,1] = +wy - hy
        verts[2::4,1] = +wy + hy
        verts[3::4,1] = -wy + hy

        positions = self.xys+self.fieldPos #set of positions across elements

        #depth
        verts[:,2] = self.depths + self.fieldDepth
        #rotate, translate, scale by units
        if positions.shape[0]*4 == verts.shape[0]:
            positions = positions.repeat(4,0)
        verts[:,:2] = convertToPix(vertices = verts[:,:2], pos = positions, units=self.units, win=self.win)
        verts = verts.reshape([self.nElements,4,3])

        #assign to self attrbute
        self.__dict__['verticesPix'] = numpy.require(verts,requirements=['C'])#make sure it's contiguous
        self._needVertexUpdate = False

    #----------------------------------------------------------------------
    def updateElementColors(self):
        """Create a new array of self._RGBAs based on self.rgbs. Not needed by the
        user (simple call setColors())

        For element arrays the self.rgbs values correspond to one element so
        this function also converts them to be one for each vertex of each element
        """
        N=self.nElements
        self._RGBAs=numpy.zeros([N,4],'d')
        if self.colorSpace in ['rgb','dkl','lms','hsv']: #these spaces are 0-centred
            self._RGBAs[:,0:3] = self.rgbs[:,:] * self.contrs[:].reshape([N,1]).repeat(3,1)/2+0.5
        else:
            self._RGBAs[:,0:3] = self.rgbs * self.contrs[:].reshape([N,1]).repeat(3,1)/255.0
        self._RGBAs[:,-1] = self.opacities.reshape([N,])
        self._RGBAs=self._RGBAs.reshape([N,1,4]).repeat(4,1)#repeat for the 4 vertices in the grid

        self._needColorUpdate=False

    def updateTextureCoords(self):
        """Create a new array of self._maskCoords"""

        N=self.nElements
        self._maskCoords=numpy.array([[1,0],[0,0],[0,1],[1,1]],'d').reshape([1,4,2])
        self._maskCoords = self._maskCoords.repeat(N,0)

        #for the main texture
        if self.units in ['norm', 'pix', 'height']:#sf is dependent on size (openGL default)
            L = -self.sfs[:,0]/2 - self.phases[:,0]+0.5
            R = +self.sfs[:,0]/2 - self.phases[:,0]+0.5
            T = +self.sfs[:,1]/2 - self.phases[:,1]+0.5
            B = -self.sfs[:,1]/2 - self.phases[:,1]+0.5
        else: #we should scale to become independent of size
            L = -self.sfs[:,0]*self.sizes[:,0]/2 - self.phases[:,0]+0.5
            R = +self.sfs[:,0]*self.sizes[:,0]/2 - self.phases[:,0]+0.5
            T = +self.sfs[:,1]*self.sizes[:,1]/2 - self.phases[:,1]+0.5
            B = -self.sfs[:,1]*self.sizes[:,1]/2 - self.phases[:,1]+0.5

        #self._texCoords=numpy.array([[1,1],[1,0],[0,0],[0,1]],'d').reshape([1,4,2])
        self._texCoords=numpy.concatenate([[R,B],[L,B],[L,T],[R,T]]) \
            .transpose().reshape([N,4,2]).astype('d')
        self._texCoords = numpy.ascontiguousarray(self._texCoords)
        self._needTexCoordUpdate=False

    def setTex(self,value, log=True):
        """Change the texture (all elements have the same base texture). Avoid this
        during time-critical points in your script. Uploading new textures to the
        graphics card can be time-consuming.
        """
        self.tex = value
        self.createTexture(value, id=self._texID, pixFormat=GL.GL_RGB, stim=self, res=self.texRes)
        logAttrib(self, log, 'tex')
    def setMask(self,value, log=True):
        """Change the mask (all elements have the same mask). Avoid doing this
        during time-critical points in your script. Uploading new textures to the
        graphics card can be time-consuming."""
        self.mask = value
        self.createTexture(value, id=self._maskID, pixFormat=GL.GL_ALPHA, stim=self, res=self.texRes)
        logAttrib(self, log, 'mask')
    def __del__(self):
        self.clearTextures()#remove textures from graphics card to prevent crash
    def clearTextures(self):
        """
        Clear the textures associated with the given stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self._texID)
        GL.glDeleteTextures(1, self._maskID)
