#!/usr/bin/env python2

'''This stimulus class defines a field of dots with an update rule that
determines how they change on every call to the .draw() method.'''

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
from psychopy.tools.attributetools import setWithOperation, logAttrib
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import cm2pix, deg2pix
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.visual.basevisual import ColorMixin, ContainerMixin

import numpy
from numpy import pi


class DotStim(BaseVisualStim, ColorMixin, ContainerMixin):
    """
    This stimulus class defines a field of dots with an update rule that determines how they change
    on every call to the .draw() method.

    This single class can be used to generate a wide variety of dot motion types. For a review of
    possible types and their pros and cons see Scase, Braddick & Raymond (1996). All six possible
    motions they describe can be generated with appropriate choices of the signalDots (which
    determines whether signal dots are the 'same' or 'different' on each frame), noiseDots
    (which determines the locations of the noise dots on each frame) and the dotLife (which
    determines for how many frames the dot will continue before being regenerated).

    The default settings (as of v1.70.00) is for the noise dots to have identical velocity
    but random direction and signal dots remain the 'same' (once a signal dot, always a signal dot).

    For further detail about the different configurations see :ref:`dots` in the Builder
    Components section of the documentation.

    If further customisation is required, then the DotStim should be subclassed and its
    _update_dotsXY and _newDotsXY methods overridden.
    """
    def __init__(self,
                 win,
                 units  ='',
                 nDots  =1,
                 coherence      =0.5,
                 fieldPos       =(0.0,0.0),
                 fieldSize      = (1.0,1.0),
                 fieldShape     = 'sqr',
                 dotSize        =2.0,
                 dotLife = 3,
                 dir    =0.0,
                 speed  =0.5,
                 rgb    =None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacity = 1.0,
                 contrast = 1.0,
                 depth  =0,
                 element=None,
                 signalDots='same',
                 noiseDots='direction',
                 name='', autoLog=True):
        """
        :Parameters:

            nDots : int
                number of dots to be generated
            fieldPos : (x,y) or [x,y]
                specifying the location of the centre of the stimulus.
            fieldSize : (x,y) or [x,y] or single value (applied to both dimensions)
                Sizes can be negative and can extend beyond the window.
            fieldShape : *'sqr'* or 'circle'
                Defines the envelope used to present the dots
            dotSize
                specified in pixels (overridden if `element` is specified)
            dotLife : int
                Number of frames each dot lives for (default=3, -1=infinite)
            dir : float (degrees)
                direction of the coherent dots
            speed : float
                speed of the dots (in *units*/frame)
            signalDots : 'same' or *'different'*
                If 'same' then the signal and noise dots are constant. If different
                then the choice of which is signal and which is noise gets
                randomised on each frame. This corresponds to Scase et al's (1996) categories of RDK.
            noiseDots : *'direction'*, 'position' or 'walk'
                Determines the behaviour of the noise dots, taken directly from
                Scase et al's (1996) categories. For 'position', noise dots take a
                random position every frame. For 'direction' noise dots follow a
                random, but constant direction. For 'walk' noise dots vary their
                direction every frame, but keep a constant speed.

            element : *None* or a visual stimulus object
                This can be any object that has a ``.draw()`` method and a
                ``.setPos([x,y])`` method (e.g. a GratingStim, TextStim...)!!
                See `ElementArrayStim` for a faster implementation of this idea.
            """
        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = __builtins__['dir']()
        self._initParams.remove('self')

        super(DotStim, self).__init__(win, units=units, name=name, autoLog=False)#set autoLog at end of init

        self.nDots = nDots
        #pos and size are ambiguous for dots so DotStim explicitly has
        #fieldPos = pos, fieldSize=size and then dotSize as additional param
        self.fieldPos = self.pos = val2array(fieldPos, False, False)
        self.fieldSize = self.size = val2array(fieldSize, False)
        if type(dotSize) in [tuple,list]:
            self.dotSize = numpy.array(dotSize)
        else:
            self.dotSize=dotSize
        self.fieldShape = fieldShape
        self.dir = dir
        self.speed = speed
        self.element = element
        self.dotLife = dotLife
        self.signalDots = signalDots
        self.noiseDots = noiseDots
        self.opacity = float(opacity)
        self.contrast = float(contrast)

        self.useShaders=False#not needed for dots?
        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb')
        else:
            self.setColor(color)

        self.depth=depth

        #initialise the dots themselves - give them all random dir and then
        #fix the first n in the array to have the direction specified

        self.coherence=round(coherence*self.nDots)/self.nDots#store actual coherence

        self. _verticesBase = self._dotsXY = self._newDotsXY(self.nDots) #initialise a random array of X,Y
        self._dotsSpeed = numpy.ones(self.nDots, 'f')*self.speed#all dots have the same speed
        self._dotsLife = abs(dotLife)*numpy.random.rand(self.nDots)#abs() means we can ignore the -1 case (no life)
        #determine which dots are signal
        self._signalDots = numpy.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence*self.nDots)]=True
        #numpy.random.shuffle(self._signalDots)#not really necessary
        #set directions (only used when self.noiseDots='direction')
        self._dotsDir = numpy.random.rand(self.nDots)*2*pi
        self._dotsDir[self._signalDots] = self.dir*pi/180

        self._update_dotsXY()
        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def _set(self, attrib, val, op='', log=True):
        """Use this to set attributes of your stimulus after initialising it.

        :Parameters:

        attrib : a string naming any of the attributes of the stimulus (set during init)
        val : the value to be used in the operation on the attrib
        op : a string representing the operation to be performed (optional) most maths operators apply ('+','-','*'...)

        examples::

            myStim.set('rgb',0) #will simply set all guns to zero (black)
            myStim.set('rgb',0.5,'+') #will increment all 3 guns by 0.5
            myStim.set('rgb',(1.0,0.5,0.5),'*') # will keep the red gun the same and halve the others

        """
        #format the input value as float vectors
        if type(val) in [tuple,list]:
            val=numpy.array(val,float)

        #change the attribute as requested
        setWithOperation(self, attrib, val, op)

        #update the actual coherence for the requested coherence and nDots
        if attrib in ['nDots','coherence']:
            self.coherence=round(self.coherence*self.nDots)/self.nDots

        logAttrib(self, log, attrib)

    def set(self, attrib, val, op='', log=True):
        """DotStim.set() is obsolete and may not be supported in future
        versions of PsychoPy. Use the specific method for each parameter instead
        (e.g. setFieldPos(), setCoherence()...)
        """
        self._set(attrib, val, op, log=log)
    def setPos(self, newPos=None, operation='', units=None, log=True):
        """Obsolete - users should use setFieldPos instead of setPos
        """
        logging.error("User called DotStim.setPos(pos). Use DotStim.SetFieldPos(pos) instead.")
    def setFieldPos(self,val, op='', log=True):
        self._set('fieldPos', val, op, log=log)
        self.pos = self.fieldPos #we'll store this as both
    def setFieldCoherence(self,val, op='', log=True):
        """Change the coherence (%) of the DotStim. This will be rounded according
        to the number of dots in the stimulus.
        """
        self._set('coherence', val, op, log=log)
        self.coherence=round(self.coherence*self.nDots)/self.nDots#store actual coherence rounded by nDots
        self._signalDots = numpy.zeros(self.nDots, dtype=bool)
        self._signalDots[0:int(self.coherence*self.nDots)]=True
        #for 'direction' method we need to update the direction of the number
        #of signal dots immediately, but for other methods it will be done during updateXY
        if self.noiseDots in ['direction','position']:
            self._dotsDir=numpy.random.rand(self.nDots)*2*pi
            self._dotsDir[self._signalDots]=self.dir*pi/180
    def setDir(self,val, op='', log=True):
        """Change the direction of the signal dots (units in degrees)
        """
        #check which dots are signal
        signalDots = self._dotsDir==(self.dir*pi/180)
        self._set('dir', val, op, log=log)
        #dots currently moving in the signal direction also need to update their direction
        self._dotsDir[signalDots] = self.dir*pi/180
    def setSpeed(self,val, op='', log=True):
        """Change the speed of the dots (in stimulus `units` per second)
        """
        self._set('speed', val, op, log=log)
    def draw(self, win=None):
        """Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.
        """
        if win==None: win=self.win
        self._selectWindow(win)

        self._update_dotsXY()

        GL.glPushMatrix()#push before drawing, pop after

        #draw the dots
        if self.element==None:
            win.setScale('pix')
            GL.glPointSize(self.dotSize)

            #load Null textures into multitexteureARB - they modulate with glColor
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

            GL.glVertexPointer(2, GL.GL_DOUBLE, 0, self.verticesPix.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)

            GL.glColor4f(desiredRGB[0], desiredRGB[1], desiredRGB[2], self.opacity)
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glDrawArrays(GL.GL_POINTS, 0, self.nDots)
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        else:
            #we don't want to do the screen scaling twice so for each dot subtract the screen centre
            initialDepth=self.element.depth
            for pointN in range(0,self.nDots):
                self.element.setPos(self.verticesPix[pointN,:]+self.fieldPos)
                self.element.draw()
            self.element.setDepth(initialDepth)#reset depth before going to next frame
        GL.glPopMatrix()

    def _newDotsXY(self, nDots):
        """Returns a uniform spread of dots, according to the fieldShape and fieldSize

        usage::

            dots = self._newDots(nDots)

        """
        if self.fieldShape=='circle':#make more dots than we need and only use those that are within circle
            while True:#repeat until we have enough
                new=numpy.random.uniform(-1, 1, [nDots*2,2])#fetch twice as many as needed
                inCircle= (numpy.hypot(new[:,0],new[:,1])<1)
                if sum(inCircle)>=nDots:
                    return new[inCircle,:][:nDots,:]*self.fieldSize/2.0
        else:
            return numpy.random.uniform(-self.fieldSize/2.0, self.fieldSize/2.0, [nDots,2])

    def _update_dotsXY(self):
        """
        The user shouldn't call this - its gets done within draw()
        """

        """Find dead dots, update positions, get new positions for dead and out-of-bounds
        """
        #renew dead dots
        if self.dotLife>0:#if less than zero ignore it
            self._dotsLife -= 1 #decrement. Then dots to be reborn will be negative
            dead = (self._dotsLife<=0.0)
            self._dotsLife[dead]=self.dotLife
        else:
            dead=numpy.zeros(self.nDots, dtype=bool)

        ##update XY based on speed and dir
        #NB self._dotsDir is in radians, but self.dir is in degs
        #update which are the noise/signal dots
        if self.signalDots =='different':
            #  **up to version 1.70.00 this was the other way around, not in keeping with Scase et al**
            #noise and signal dots change identity constantly
            numpy.random.shuffle(self._dotsDir)
            self._signalDots = (self._dotsDir==(self.dir*pi/180))#and then update _signalDots from that

        #update the locations of signal and noise
        if self.noiseDots=='walk':
            # noise dots are ~self._signalDots
            self._dotsDir[~self._signalDots] = numpy.random.rand((~self._signalDots).sum())*pi*2
            #then update all positions from dir*speed
            self._verticesBase[:,0] += self.speed*numpy.reshape(numpy.cos(self._dotsDir),(self.nDots,))
            self._verticesBase[:,1] += self.speed*numpy.reshape(numpy.sin(self._dotsDir),(self.nDots,))# 0 radians=East!
        elif self.noiseDots == 'direction':
            #simply use the stored directions to update position
            self._verticesBase[:,0] += self.speed*numpy.reshape(numpy.cos(self._dotsDir),(self.nDots,))
            self._verticesBase[:,1] += self.speed*numpy.reshape(numpy.sin(self._dotsDir),(self.nDots,))# 0 radians=East!
        elif self.noiseDots=='position':
            #update signal dots
            self._verticesBase[self._signalDots,0] += \
                self.speed*numpy.reshape(numpy.cos(self._dotsDir[self._signalDots]),(self._signalDots.sum(),))
            self._verticesBase[self._signalDots,1] += \
                self.speed*numpy.reshape(numpy.sin(self._dotsDir[self._signalDots]),(self._signalDots.sum(),))# 0 radians=East!
            #update noise dots
            dead = dead+(~self._signalDots)#just create new ones

        #handle boundaries of the field
        if self.fieldShape in  [None, 'square', 'sqr']:
            dead = dead+(numpy.abs(self._verticesBase[:,0])>(self.fieldSize[0]/2.0))+(numpy.abs
                                                                                  (self
                                                                                   ._verticesBase[:,1])>(self.fieldSize[1]/2.0))
        elif self.fieldShape == 'circle':
            #transform to a normalised circle (radius = 1 all around) then to polar coords to check
            normXY = self._verticesBase/(self.fieldSize/2.0)#the normalised XY position (where radius should be <1)
            dead = dead + (numpy.hypot(normXY[:,0],normXY[:,1])>1) #add out-of-bounds to those that need replacing

        #update any dead dots
        if sum(dead):
            self._verticesBase[dead,:] = self._newDotsXY(sum(dead))

        #update the pixel XY coordinates in pixels (using _BaseVisual class)
        self._updateVertices()
