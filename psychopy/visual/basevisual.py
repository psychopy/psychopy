#!/usr/bin/env python2

'''Provides class BaseVisualStim and mixins; subclass to get visual stimuli'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl
try:
    from PIL import Image
except ImportError:
    import Image

import copy
import sys
import os

import psychopy  # so we can get the __path__
from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter, logAttrib, setAttribute
from psychopy.tools.colorspacetools import dkl2rgb, lms2rgb
from psychopy.tools.monitorunittools import cm2pix, deg2pix, pix2cm, pix2deg, convertToPix
from psychopy.visual.helpers import pointInPolygon, polygonsOverlap, setColor
from psychopy.tools.typetools import float_uint8
from psychopy.tools.arraytools import makeRadialMatrix
from . import glob_vars

import numpy
from numpy import pi

from psychopy.constants import NOT_STARTED, STARTED, STOPPED

reportNImageResizes = 5 #permitted number of resizes

"""
There are several base and mix-in visual classes for multiple inheritance:
  - MinimalStim:       non-visual house-keeping code common to all visual stim
        RatingScale inherits only from MinimalStim.
  - WindowMixin:       attributes/methods about the stim relative to a visual.Window.
  - LegacyVisualMixin: deprecated visual methods (eg, setRGB)
        added to BaseVisualStim
  - ColorMixin:        for Stim that need color methods (most, not Movie)
        color-related methods and attribs
  - ContainerMixin:    for stim that need polygon .contains() methods (most, not Text)
        .contains(), .overlaps()
  - TextureMixin:      for texture methods namely _createTexture (Grating, not Text)
        seems to work; caveat: There were issues in earlier (non-MI) versions
        of using _createTexture so it was pulled out of classes. Now it's inside
        classes again. Should be watched.
  - BaseVisualStim:    = Minimal + Window + Legacy. Furthermore adds common attributes
        like orientation, opacity, contrast etc.

Typically subclass BaseVisualStim to create new visual stim classes, and add
mixin(s) as needed to add functionality.
"""

class MinimalStim(object):
    """Non-visual methods and attributes for BaseVisualStim and RatingScale.

    Includes: name, autoDraw, autoLog, status, __str__
    """
    def __init__(self, name=None, autoLog=None):
        self.__dict__['name'] = name if name not in (None, '') else 'unnamed %s' %self.__class__.__name__
        self.status = NOT_STARTED
        self.autoLog = autoLog
        super(MinimalStim, self).__init__()
        if self.autoLog:
            logging.warning("%s is calling MinimalStim.__init__() with autolog=True. Set autoLog to True only at the end of __init__())" \
                            %(self.__class__.__name__))

    def __str__(self, complete=False):
        """
        """
        if hasattr(self, '_initParams'):
            className = self.__class__.__name__
            paramStrings = []
            for param in self._initParams:
                if hasattr(self, param):
                    val = getattr(self, param)
                    valStr = repr(getattr(self, param))
                    if len(repr(valStr))>50 and not complete:
                        if val.__class__.__name__ == 'attributeSetter':
                            valStr = "%s(...)" %val.__getattribute__.__class__.__name__
                        else:
                            valStr = "%s(...)" %val.__class__.__name__
                else:
                    valStr = 'UNKNOWN'
                paramStrings.append("%s=%s" %(param, valStr))
            #this could be used if all params are known to exist:
            # paramStrings = ["%s=%s" %(param, getattr(self, param)) for param in self._initParams]
            params = ", ".join(paramStrings)
            s = "%s(%s)" %(className, params)
        else:
            s = object.__repr__(self)
        return s

    # Might seem simple at first, but this ensures that "name" attribute
    # appears in docs and that name setting and updating is logged.
    @attributeSetter
    def name(self, value):
        """String or None. The name of the object to be using during logged messages about
        this stim. If you have multiple stimuli in your experiment this really
        helps to make sense of log files!

        If name = None your stimulus will be called "unnamed <type>", e.g.
        visual.TextStim(win) will be called "unnamed TextStim" in the logs.
        """
        self.__dict__['name'] = value

    @attributeSetter
    def autoDraw(self, value):
        """Determines whether the stimulus should be automatically drawn on every frame flip.

        Value should be: `True` or `False`. You do NOT need to set this on every frame flip!
        """
        self.__dict__['autoDraw'] = value
        toDraw = self.win._toDraw
        toDrawDepths = self.win._toDrawDepths
        beingDrawn = (self in toDraw)
        if value == beingDrawn:
            return #nothing to do
        elif value:
            #work out where to insert the object in the autodraw list
            depthArray = numpy.array(toDrawDepths)
            iis = numpy.where(depthArray < self.depth)[0]#all indices where true
            if len(iis):#we featured somewhere before the end of the list
                toDraw.insert(iis[0], self)
                toDrawDepths.insert(iis[0], self.depth)
            else:
                toDraw.append(self)
                toDrawDepths.append(self.depth)
            self.status = STARTED
        elif value == False:
            #remove from autodraw lists
            toDrawDepths.pop(toDraw.index(self))  #remove from depths
            toDraw.remove(self)  #remove from draw list
            self.status = STOPPED

    def setAutoDraw(self, value, log=None):
        """Sets autoDraw. Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message"""
        setAttribute(self, 'autoDraw', value, log)

    @attributeSetter
    def autoLog(self, value):
        """Whether every change in this stimulus should be logged automatically

        Value should be: `True` or `False`. Set to `False` if your stimulus is updating frequently (e.g.
        updating its position every frame) and you want to avoid swamping the log file with
        messages that aren't likely to be useful.
        """
        self.__dict__['autoLog'] = value

    def setAutoLog(self, value=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message"""
        setAttribute(self, 'autoLog', value, log)

class LegacyVisualMixin(object):
    """Class to hold deprecated visual methods and attributes.

    Intended only for use as a mixin class for BaseVisualStim, to maintain
    backwards compatibility while reducing clutter in class BaseVisualStim.
    """
    #def __init__(self):
    #    super(LegacyVisualMixin, self).__init__()

    def _calcSizeRendered(self):
        """DEPRECATED in 1.80.00. This functionality is now handled by _updateVertices() and verticesPix"""
        #raise DeprecationWarning, "_calcSizeRendered() was deprecated in 1.80.00. This functionality is now handled by _updateVertices() and verticesPix"
        if self.units in ['norm','pix', 'height']: self._sizeRendered=copy.copy(self.size)
        elif self.units in ['deg', 'degs']: self._sizeRendered=deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=cm2pix(self.size, self.win.monitor)
        else:
            logging.error("Stimulus units should be 'height', 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)

    def _calcPosRendered(self):
        """DEPRECATED in 1.80.00. This functionality is now handled by _updateVertices() and verticesPix"""
        #raise DeprecationWarning, "_calcSizeRendered() was deprecated in 1.80.00. This functionality is now handled by _updateVertices() and verticesPix"
        if self.units in ['norm','pix', 'height']: self._posRendered= copy.copy(self.pos)
        elif self.units in ['deg', 'degs']: self._posRendered=deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=cm2pix(self.pos, self.win.monitor)

    def _getPolyAsRendered(self):
        """DEPRECATED. Return a list of vertices as rendered; used by overlaps()
        """
        oriRadians = numpy.radians(self.ori)
        sinOri = numpy.sin(-oriRadians)
        cosOri = numpy.cos(-oriRadians)
        x = self._verticesRendered[:,0] * cosOri - self._verticesRendered[:,1] * sinOri
        y = self._verticesRendered[:,0] * sinOri + self._verticesRendered[:,1] * cosOri
        return numpy.column_stack((x,y)) + self._posRendered

    def setDKL(self, newDKL, operation=''):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        self._set('dkl', val=newDKL, op=operation)
        self.setRGB(dkl2rgb(self.dkl, self.win.dkl_rgb))
    def setLMS(self, newLMS, operation=''):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        self._set('lms', value=newLMS, op=operation)
        self.setRGB(lms2rgb(self.lms, self.win.lms_rgb))
    def setRGB(self, newRGB, operation='', log=None):
        """DEPRECATED since v1.60.05: Please use the `color` attribute
        """
        from psychopy.visual.helpers import setTexIfNoShaders
        self._set('rgb', newRGB, operation)
        setTexIfNoShaders(self)
        if self.__class__.__name__ == 'TextStim' and not self.useShaders:
            self._needSetText=True

    @attributeSetter
    def depth(self, value):
        """DEPRECATED. Depth is now controlled simply by drawing order.
        """
        self.__dict__['depth'] = value

class ColorMixin(object):
    """Mixin class for visual stim that need color and or contrast.
    """
    #def __init__(self):
    #    super(ColorStim, self).__init__()

    @attributeSetter
    def color(self, value):
        """Color of the stimulus

        Value should be one of:
            + string: to specify a :ref:`colorNames`. Any of the standard
              html/X11 `color names <http://www.w3schools.com/html/html_colornames.asp>`
              can be used.
            + :ref:`hexColors`
            + numerically: (scalar or triplet) for DKL, RGB or other :ref:`colorspaces`. For
                these, :ref:`operations <attrib-operations>` are supported.

        When color is specified using numbers, it is interpreted with
        respect to the stimulus' current colorSpace. If color is given as a
        single value (scalar) then this will be applied to all 3 channels.

        Examples::
                # ... for whatever stim you have, e.g. stim = visual.ShapeStim(win):
                stim.color = 'white'
                stim.color = 'RoyalBlue'  # (the case is actually ignored)
                stim.color = '#DDA0DD'  # DDA0DD is hexadecimal for plum
                stim.color = [1.0, -1.0, -1.0]  # if stim.colorSpace='rgb': a red color in rgb space
                stim.color = [0.0, 45.0, 1.0]  # if stim.colorSpace='dkl': DKL space with elev=0, azimuth=45
                stim.color = [0, 0, 255]  # if stim.colorSpace='rgb255': a blue stimulus using rgb255 space
                stim.color = 255  # interpreted as (255, 255, 255) which is white in rgb255.


        :ref:`Operations <attrib-operations>` work as normal for all numeric
        colorSpaces (e.g. 'rgb', 'hsv' and 'rgb255') but not for strings, like
        named and hex. For example, assuming that colorSpace='rgb'::

            stim.color += [1, 1, 1]  # increment all guns by 1 value
            stim.color *= -1  # multiply the color by -1 (which in this space inverts the contrast)
            stim.color *= [0.5, 0, 1]  # decrease red, remove green, keep blue

        You can use `setColor` if you want to set color and colorSpace in one
        line. These two are equivalent::

            stim.setColor((0, 128, 255), 'rgb255')
            # ... is equivalent to
            stim.colorSpace = 'rgb255'
            stim.color = (0, 128, 255)
        """
        self.setColor(value, log=False)  # logging already done by attributeSettter

    @attributeSetter
    def colorSpace(self, value):
        """The name of the color space currently being used (for numeric colors)

        Value should be: a string or None

        For strings and hex values this is not needed.
        If None the default colorSpace for the stimulus is
        used (defined during initialisation).

        Please note that changing colorSpace does not change stimulus parameters.
        Thus you usually want to specify colorSpace before setting the color. Example::

            # A light green text
            stim = visual.TextStim(win, 'Color me!', color=(0, 1, 0), colorSpace='rgb')

            # An almost-black text
            stim.colorSpace = 'rgb255'

            # Make it light green again
            stim.color = (128, 255, 128)
        """
        self.__dict__['colorSpace'] = value

    @attributeSetter
    def contrast(self, value):
        """A value that is simply multiplied by the color

        Value should be: a float between -1 (negative) and 1 (unchanged).
            :ref:`Operations <attrib-operations>` supported.

        Set the contrast of the stimulus, i.e. scales how far the stimulus
        deviates from the middle grey. You can also use the stimulus
        `opacity` to control contrast, but that cannot be negative.

        Examples::

            stim.contrast =  1.0  # unchanged contrast
            stim.contrast =  0.5  # decrease contrast
            stim.contrast =  0.0  # uniform, no contrast
            stim.contrast = -0.5  # slightly inverted
            stim.contrast = -1.0  # totally inverted

        Setting contrast outside range -1 to 1 is permitted, but may
        produce strange results if color values exceeds the monitor limits.::

            stim.contrast =  1.2  # increases contrast
            stim.contrast = -1.2  # inverts with increased contrast
        """
        self.__dict__['contrast'] = value

        # If we don't have shaders we need to rebuild the stimulus
        if hasattr(self, 'useShaders'):
            if not self.useShaders:
                #we'll need to update the textures for the stimulus
                #(sometime before drawing but not now)
                if self.__class__.__name__ == 'TextStim':
                    self.text = self.text  # call attributeSetter to rebuild text
                elif hasattr(self,'_needTextureUpdate'): #GratingStim, RadialStim, ImageStim etc
                    self._needTextureUpdate = True
                elif self.__class__.__name__ in ('ShapeStim','DotStim'):
                    pass # They work fine without shaders?
                elif self.autoLog:
                    logging.warning('Tried to set contrast while useShaders = False but stimulus was not rebuild. Contrast might remain unchanged.')
        elif self.autoLog:
            logging.warning('Contrast was set on class where useShaders was undefined. Contrast might remain unchanged')
    def setColor(self, color, colorSpace=None, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        and/or set colorSpace simultaneously.
        """
        # NB: the setColor helper function! Not this function itself :-)
        setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='rgb', #or 'fillRGB' etc
                    colorAttrib='color')
        if self.__class__.__name__ == 'TextStim' and not self.useShaders:
            self._needSetText = True
        logAttrib(self, log, 'color', value='%s (%s)' %(self.color, self.colorSpace))
    def setContrast(self, newContrast, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'contrast', newContrast, log, operation)

    def _getDesiredRGB(self, rgb, colorSpace, contrast):
        """ Convert color to RGB while adding contrast
        Requires self.rgb, self.colorSpace and self.contrast"""
        # Ensure that we work on 0-centered color (to make negative contrast values work)
        if colorSpace not in ['rgb', 'dkl', 'lms', 'hsv']:
            rgb = (rgb / 255.0) * 2 - 1

        # Convert to RGB in range 0:1 and scaled for contrast
        # NB glColor will clamp it to be 0-1 (whether or not we use FBO)
        desiredRGB = (rgb * contrast + 1) / 2.0
        if not self.win.useFBO:
            # Check that boundaries are not exceeded. If we have an FBO that can handle this
            if numpy.any(desiredRGB > 1.0) or numpy.any(desiredRGB < 0):
                logging.warning('Desired color %s (in RGB 0->1 units) falls outside the monitor gamut. Drawing blue instead' %desiredRGB) #AOH
                desiredRGB=[0.0, 0.0, 1.0]

        return desiredRGB

class ContainerMixin(object):
    """Mixin class for visual stim that have verticesPix attrib and .contains() methods.
    """
    def __init__(self):
        super(ContainerMixin, self).__init__()
        self._verticesBase = numpy.array([[0.5,-0.5],[-0.5,-0.5],[-0.5,0.5],[0.5,0.5]]) #sqr
        self._rotationMatrix = [[1.,0.],[0.,1.]] #no rotation as a default

    @property
    def verticesPix(self):
        """This determines the coordinates of the vertices for the
        current stimulus in pixels, accounting for size, ori, pos and units
        """
        #because this is a property getter we can check /on-access/ if it needs updating :-)
        if self._needVertexUpdate:
            self._updateVertices()
        return self.__dict__['verticesPix']
    def _updateVertices(self):
        """Sets Stim.verticesPix from pos and size
        """
        if hasattr(self, 'vertices'):
            verts = self.vertices
        else:
            verts = self._verticesBase
        #check whether stimulus needs flipping in either direction
        flip = numpy.array([1,1])
        if hasattr(self, 'flipHoriz'):
            flip[0] = self.flipHoriz*(-2)+1#True=(-1), False->(+1)
        if hasattr(self, 'flipVert'):
            flip[1] = self.flipVert*(-2)+1#True=(-1), False->(+1)
        # set size and orientation
        verts = numpy.dot(self.size*verts*flip, self._rotationMatrix)
        #then combine with position and convert to pix
        verts = convertToPix(vertices=verts, pos=self.pos, win=self.win, units=self.units)
        #assign to self attribute
        self.__dict__['verticesPix'] = verts
        self._needVertexUpdate = False
        self._needUpdate = True #but we presumably need to update the list
    def contains(self, x, y=None, units=None):
        """Returns True if a point x,y is inside the extent of the stimulus.

        Can accept variety of input options:
            + two separate args, x and y
            + one arg (list, tuple or array) containing two vals (x,y)
            + an object with a getPos() method that returns x,y, such
                as a :class:`~psychopy.event.Mouse`.

        Returns `True` if the point is within the area defined by `vertices`.
        This method handles complex shapes, including concavities and self-crossings.

        Note that, if your stimulus uses a mask (such as a Gaussian) then
        this is not accounted for by the `contains` method; the extent of the
        stimulus is determined purely by the size, position (pos), and orientation (ori) settings
        (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        #get the object in pixels
        if hasattr(x, 'verticesPix'):
            xy = x.verticesPix #access only once - this is a property (slower to access)
            units = 'pix' #we can forget about the units
        elif hasattr(x, 'getPos'):
            xy = x.getPos()
            units = x.units
        elif type(x) in [list, tuple, numpy.ndarray]:
            xy = numpy.array(x)
        else:
            xy = numpy.array((x,y))
        #try to work out what units x,y has
        if units is None:
            if hasattr(xy, 'units'):
                units = xy.units
            else:
                units = self.units
        if units != 'pix':
            xy = convertToPix(xy, pos=(0,0), units=units, win=self.win)
        # ourself in pixels
        selfVerts = self.verticesPix
        return pointInPolygon(xy[0], xy[1], poly = selfVerts)

    def overlaps(self, polygon):
        """Returns `True` if this stimulus intersects another one.

        If `polygon` is
        another stimulus instance, then the vertices and location of that stimulus
        will be used as the polygon. Overlap detection is typically very good, but it
        can fail with very pointy shapes in a crossed-swords configuration.

        Note that, if your stimulus uses a mask (such as a Gaussian blob) then
        this is not accounted for by the `overlaps` method; the extent of the
        stimulus is determined purely by the size, pos, and orientation settings
        (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        return polygonsOverlap(self, polygon)

class TextureMixin(object):
    """Mixin class for visual stim that have textures.

    Could move visual.helpers.setTexIfNoShaders() into here
    """
    #def __init__(self):
    #    super(TextureMixin, self).__init__()

    def _createTexture(self, tex, id, pixFormat, stim, res=128, maskParams=None,
                      forcePOW2=True, dataType=None):
        """
        :params:
            id:
                is the texture ID
            pixFormat:
                GL.GL_ALPHA, GL.GL_RGB
            useShaders:
                bool
            interpolate:
                bool (determines whether texture will use GL_LINEAR or GL_NEAREST
            res:
                the resolution of the texture (unless a bitmap image is used)
            dataType:
                None, GL.GL_UNSIGNED_BYTE, GL_FLOAT. Only affects image files (numpy arrays will be float)

        For grating stimuli (anything that needs multiple cycles) forcePOW2 should
        be set to be True. Otherwise the wrapping of the texture will not work.
        """

        """
        Create an intensity texture, ranging -1:1.0
        """
        notSqr=False #most of the options will be creating a sqr texture
        wasImage=False #change this if image loading works
        useShaders = stim.useShaders
        interpolate = stim.interpolate
        if dataType is None:
            if useShaders and pixFormat==GL.GL_RGB:
                dataType = GL.GL_FLOAT
            else:
                dataType = GL.GL_UNSIGNED_BYTE

        # Fill out unspecified portions of maskParams with default values
        if maskParams is None:
            maskParams = {}
        allMaskParams = {'fringeWidth': 0.2, 'sd': 3}  # fringeWidth affects the proportion of the stimulus diameter that is devoted to the raised cosine.
        allMaskParams.update(maskParams)

        if type(tex) == numpy.ndarray:
            #handle a numpy array
            #for now this needs to be an NxN intensity array
            intensity = tex.astype(numpy.float32)
            if intensity.max()>1 or intensity.min()<-1:
                logging.error('numpy arrays used as textures should be in the range -1(black):1(white)')
            if len(tex.shape)==3:
                wasLum=False
            else: wasLum = True
            ##is it 1D?
            if tex.shape[0]==1:
                stim._tex1D=True
                res=tex.shape[1]
            elif len(tex.shape)==1 or tex.shape[1]==1:
                stim._tex1D=True
                res=tex.shape[0]
            else:
                stim._tex1D=False
                #check if it's a square power of two
                maxDim = max(tex.shape)
                powerOf2 = 2**numpy.ceil(numpy.log2(maxDim))
                if forcePOW2 and (tex.shape[0]!=powerOf2 or tex.shape[1]!=powerOf2):
                    logging.error("Requiring a square power of two (e.g. 16x16, 256x256) texture but didn't receive one")
                res=tex.shape[0]
            if useShaders:
                dataType=GL.GL_FLOAT
        elif tex in [None,"none", "None"]:
            res = 1 #4x4 (2x2 is SUPPOSED to be fine but generates weird colors!)
            intensity = numpy.ones([res,res],numpy.float32)
            wasLum = True
        elif tex == "sin":
            onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
            intensity = numpy.sin(onePeriodY-pi/2)
            wasLum = True
        elif tex == "sqr":#square wave (symmetric duty cycle)
            onePeriodX, onePeriodY = numpy.mgrid[0:res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
            sinusoid = numpy.sin(onePeriodY-pi/2)
            intensity = numpy.where(sinusoid>0, 1, -1)
            wasLum = True
        elif tex == "saw":
            intensity = numpy.linspace(-1.0,1.0,res,endpoint=True)*numpy.ones([res,1])
            wasLum = True
        elif tex == "tri":
            intensity = numpy.linspace(-1.0,3.0,res,endpoint=True)#-1:3 means the middle is at +1
            intensity[int(res/2.0+1):] = 2.0-intensity[int(res/2.0+1):]#remove from 3 to get back down to -1
            intensity = intensity*numpy.ones([res,1])#make 2D
            wasLum = True
        elif tex == "sinXsin":
            onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:1j*res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
            intensity = numpy.sin(onePeriodX-pi/2)*numpy.sin(onePeriodY-pi/2)
            wasLum = True
        elif tex == "sqrXsqr":
            onePeriodX, onePeriodY = numpy.mgrid[0:2*pi:1j*res, 0:2*pi:1j*res]# NB 1j*res is a special mgrid notation
            sinusoid = numpy.sin(onePeriodX-pi/2)*numpy.sin(onePeriodY-pi/2)
            intensity = numpy.where(sinusoid>0, 1, -1)
            wasLum = True
        elif tex == "circle":
            rad=makeRadialMatrix(res)
            intensity = (rad<=1)*2-1
            wasLum=True
        elif tex == "gauss":
            rad=makeRadialMatrix(res)
            intensity = numpy.exp( -rad**2.0 / (2.0*(1.0 / allMaskParams['sd'])**2.0) )*2-1 #3sd.s by the edge of the stimulus
            wasLum=True
        elif tex == "cross":
            X, Y = numpy.mgrid[-1:1:1j*res, -1:1:1j*res]
            tf_neg_cross = ((X < -0.2) & (Y < -0.2)) | ((X < -0.2) & (Y > 0.2)) | ((X > 0.2) & (Y < -0.2)) | ((X > 0.2) & (Y > 0.2))
            #tf_neg_cross == True at places where the cross is transparent, i.e. the four corners
            intensity = numpy.where(tf_neg_cross, -1, 1)
            wasLum = True
        elif tex == "radRamp":#a radial ramp
            rad=makeRadialMatrix(res)
            intensity = 1-2*rad
            intensity = numpy.where(rad<-1, intensity, -1)#clip off the corners (circular)
            wasLum=True
        elif tex == "raisedCos": # A raised cosine
            wasLum=True
            hamming_len = 1000 # This affects the 'granularity' of the raised cos

            rad = makeRadialMatrix(res)
            intensity = numpy.zeros_like(rad)
            intensity[numpy.where(rad < 1)] = 1
            raised_cos_idx = numpy.where(
                [numpy.logical_and(rad <= 1, rad >= 1 - allMaskParams['fringeWidth'])])[1:]

            # Make a raised_cos (half a hamming window):
            raised_cos = numpy.hamming(hamming_len)[:hamming_len/2]
            raised_cos -= numpy.min(raised_cos)
            raised_cos /= numpy.max(raised_cos)

            # Measure the distance from the edge - this is your index into the hamming window:
            d_from_edge = numpy.abs((1 - allMaskParams['fringeWidth']) - rad[raised_cos_idx])
            d_from_edge /= numpy.max(d_from_edge)
            d_from_edge *= numpy.round(hamming_len/2)

            # This is the indices into the hamming (larger for small distances from the edge!):
            portion_idx = (-1 * d_from_edge).astype(int)

            # Apply the raised cos to this portion:
            intensity[raised_cos_idx] = raised_cos[portion_idx]

            # Scale it into the interval -1:1:
            intensity = intensity - 0.5
            intensity = intensity / numpy.max(intensity)

            #Sometimes there are some remaining artifacts from this process, get rid of them:
            artifact_idx = numpy.where(numpy.logical_and(intensity == -1,
                                                         rad < 0.99))
            intensity[artifact_idx] = 1
            artifact_idx = numpy.where(numpy.logical_and(intensity == 1, rad >
                                                         0.99))
            intensity[artifact_idx] = 0

        else:
            if type(tex) in [str, unicode, numpy.string_]:
                # maybe tex is the name of a file:
                if not os.path.isfile(tex):
                    logging.error("Couldn't find image file '%s'; check path?" %(tex)); logging.flush()
                    raise OSError, "Couldn't find image file '%s'; check path? (tried: %s)" \
                        % (tex, os.path.abspath(tex))#ensure we quit
                try:
                    im = Image.open(tex)
                    im = im.transpose(Image.FLIP_TOP_BOTTOM)
                except IOError:
                    logging.error("Found file '%s' but failed to load as an image" %(tex)); logging.flush()
                    raise IOError, "Found file '%s' [= %s] but it failed to load as an image" \
                        % (tex, os.path.abspath(tex))#ensure we quit
            else:
                # can't be a file; maybe its an image already in memory?
                try:
                    im = tex.copy().transpose(Image.FLIP_TOP_BOTTOM) # ? need to flip if in mem?
                except AttributeError: # nope, not an image in memory
                    logging.error("Couldn't make sense of requested image."); logging.flush()
                    raise AttributeError, "Couldn't make sense of requested image."#ensure we quit
            # at this point we have a valid im
            stim._origSize=im.size
            wasImage=True
            #is it 1D?
            if im.size[0]==1 or im.size[1]==1:
                logging.error("Only 2D textures are supported at the moment")
            else:
                maxDim = max(im.size)
                powerOf2 = int(2**numpy.ceil(numpy.log2(maxDim)))
                if im.size[0]!=powerOf2 or im.size[1]!=powerOf2:
                    if not forcePOW2:
                        notSqr=True
                    elif glob_vars.nImageResizes<reportNImageResizes:
                        logging.warning("Image '%s' was not a square power-of-two image. Linearly interpolating to be %ix%i" %(tex, powerOf2, powerOf2))
                        glob_vars.nImageResizes+=1
                        im=im.resize([powerOf2,powerOf2],Image.BILINEAR)
                    elif glob_vars.nImageResizes==reportNImageResizes:
                        logging.warning("Multiple images have needed resizing - I'll stop bothering you!")
                        im=im.resize([powerOf2,powerOf2],Image.BILINEAR)
            #is it Luminance or RGB?
            if pixFormat==GL.GL_ALPHA and im.mode!='L':#we have RGB and need Lum
                wasLum = True
                im = im.convert("L")#force to intensity (in case it was rgb)
            elif im.mode=='L': #we have lum and no need to change
                wasLum = True
                if useShaders:
                    dataType=GL.GL_FLOAT
            elif pixFormat==GL.GL_RGB: #we want RGB and might need to convert from CMYK or Lm
                #texture = im.tostring("raw", "RGB", 0, -1)
                im = im.convert("RGBA")
                wasLum=False
            if dataType==GL.GL_FLOAT:
                #convert from ubyte to float
                intensity = numpy.array(im).astype(numpy.float32)*0.0078431372549019607-1.0 # much faster to avoid division 2/255
            else:
                intensity = numpy.array(im)
        if pixFormat==GL.GL_RGB and wasLum and dataType==GL.GL_FLOAT: #grating stim on good machine
            #keep as float32 -1:1
            if sys.platform!='darwin' and stim.win.glVendor.startswith('nvidia'):
                #nvidia under win/linux might not support 32bit float
                internalFormat = GL.GL_RGB16F_ARB #could use GL_LUMINANCE32F_ARB here but check shader code?
            else:#we've got a mac or an ATI card and can handle 32bit float textures
                internalFormat = GL.GL_RGB32F_ARB #could use GL_LUMINANCE32F_ARB here but check shader code?
            data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.float32)#initialise data array as a float
            data[:,:,0] = intensity#R
            data[:,:,1] = intensity#G
            data[:,:,2] = intensity#B
        elif pixFormat==GL.GL_RGB and wasLum and dataType!=GL.GL_FLOAT and stim.useShaders:
            #was a lum image: stick with ubyte for speed
            internalFormat = GL.GL_RGB
            data = numpy.ones((intensity.shape[0],intensity.shape[1],3),numpy.ubyte)#initialise data array as a float
            data[:,:,0] = intensity#R
            data[:,:,1] = intensity#G
            data[:,:,2] = intensity#B
        elif pixFormat==GL.GL_RGB and wasLum and not stim.useShaders: #Grating on legacy hardware, or ImageStim with wasLum=True
            #scale by rgb and convert to ubyte
            internalFormat = GL.GL_RGB
            if stim.colorSpace in ['rgb', 'dkl', 'lms','hsv']:
                rgb=stim.rgb
            else:
                rgb=stim.rgb/127.5-1.0#colour is not a float - convert to float to do the scaling
            # if wasImage it will also have ubyte values for the intensity
            if wasImage:
                intensity = intensity/127.5-1.0
            #scale by rgb
            data = numpy.ones((intensity.shape[0],intensity.shape[1],4),numpy.float32)#initialise data array as a float
            data[:,:,0] = intensity*rgb[0]  + stim.rgbPedestal[0]#R
            data[:,:,1] = intensity*rgb[1]  + stim.rgbPedestal[1]#G
            data[:,:,2] = intensity*rgb[2]  + stim.rgbPedestal[2]#B
            data[:,:,:-1] = data[:,:,:-1]*stim.contrast
            #convert to ubyte
            data = float_uint8(data)
        elif pixFormat==GL.GL_RGB and dataType==GL.GL_FLOAT: #probably a custom rgb array or rgb image
            internalFormat = GL.GL_RGB32F_ARB
            data = intensity
        elif pixFormat==GL.GL_RGB:# not wasLum, not useShaders  - an RGB bitmap with no shader optionsintensity.min()
            internalFormat = GL.GL_RGB
            data = intensity #float_uint8(intensity)
        elif pixFormat==GL.GL_ALPHA:
            internalFormat = GL.GL_ALPHA
            dataType = GL.GL_UNSIGNED_BYTE
            if wasImage:
                data = intensity
            else:
                data = float_uint8(intensity)
        #check for RGBA textures
        if len(data.shape)>2 and data.shape[2] == 4:
            if pixFormat==GL.GL_RGB:
                pixFormat=GL.GL_RGBA
            if internalFormat==GL.GL_RGB:
                internalFormat=GL.GL_RGBA
            elif internalFormat==GL.GL_RGB32F_ARB:
                internalFormat=GL.GL_RGBA32F_ARB
        texture = data.ctypes#serialise

        #bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, id)#bind that name to the target
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)  # data from PIL/numpy is packed, but default for GL is 4 bytes
        #important if using bits++ because GL_LINEAR
        #sometimes extrapolates to pixel vals outside range
        if interpolate:
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
            if useShaders:#GL_GENERATE_MIPMAP was only available from OpenGL 1.4
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                    data.shape[1],data.shape[0], 0, # [JRG] for non-square, want data.shape[1], data.shape[0]
                    pixFormat, dataType, texture)
            else:#use glu
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)
                GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internalFormat,
                    data.shape[1],data.shape[0], pixFormat, dataType, texture)    # [JRG] for non-square, want data.shape[1], data.shape[0]
        else:
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                            data.shape[1],data.shape[0], 0, # [JRG] for non-square, want data.shape[1], data.shape[0]
                            pixFormat, dataType, texture)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)#?? do we need this - think not!
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)#unbind our texture so that it doesn't affect other rendering
        return wasLum

    def clearTextures(self):
        """
        Clear all textures associated with the stimulus.
        As of v1.61.00 this is called automatically during garbage collection of
        your stimulus, so doesn't need calling explicitly by the user.
        """
        GL.glDeleteTextures(1, self._texID)
        GL.glDeleteTextures(1, self._maskID)

    @attributeSetter
    def mask(self, value):
        """The alpha mask (forming the shape of the image)

        This can be one of various options:
            + 'circle', 'gauss', 'raisedCos', 'cross', **None** (resets to default)
            + the name of an image file (most formats supported)
            + a numpy array (1xN or NxN) ranging -1:1
        """
        self.__dict__['mask'] = value
        if self.__class__.__name__ == 'ImageStim':
            dataType = GL.GL_UNSIGNED_BYTE
        else:
            dataType = None
        self._createTexture(value, id=self._maskID, pixFormat=GL.GL_ALPHA, dataType=dataType,
            stim=self, res=self.texRes, maskParams=self.maskParams)
    def setMask(self, value, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'mask', value, log)

    @attributeSetter
    def texRes(self, value):
        """Power-of-two int. Sets the resolution of the mask and texture.
        texRes is overridden if an array or image is provided as mask.

        :ref:`Operations <attrib-operations>` supported.
        """
        self.__dict__['texRes'] = value

        # ... now rebuild textures (call attributeSetters without logging).
        if hasattr(self, 'tex'): setAttribute(self, 'tex', self.tex, log=False)
        if hasattr(self, 'mask'): setAttribute(self, 'mask', self.mask, log=False)

    @attributeSetter
    def maskParams(self, value):
        """Various types of input. Default to None.
        This is used to pass additional parameters to the mask if those are needed.

            - For 'gauss' mask, pass dict {'sd': 5} to control standard deviation.
            - For the 'raisedCos' mask, pass a dict: {'fringeWidth':0.2},
                where 'fringeWidth' is a parameter (float, 0-1), determining
                the proportion of the patch that will be blurred by the raised
                cosine edge."""
        self.__dict__['maskParams'] = value
        setAttribute(self, 'mask', self.mask, log=False)  # call attributeSetter without log

class WindowMixin(object):
    """Window-related attributes and methods.
    Used by BaseVisualStim, SimpleImageStim and ElementArrayStim."""

    @attributeSetter
    def win(self, value):
        """ The :class:`~psychopy.visual.Window` object in which the stimulus will be rendered
        by default. (required)

       Example, drawing same stimulus in two different windows and display
       simultaneously. Assuming that you have two windows and a stimulus (win1, win2 and stim)::

           stim.win = win1  # stimulus will be drawn in win1
           stim.draw()  # stimulus is now drawn to win1
           stim.win = win2  # stimulus will be drawn in win2
           stim.draw()  # it is now drawn in win2
           win1.flip(waitBlanking=False)  # do not wait for next monitor update
           win2.flip()  # wait for vertical blanking.

        Note that this just changes **default** window for stimulus.
        You could also specify window-to-draw-to when drawing::

           stim.draw(win1)
           stim.draw(win2)
        """
        self.__dict__['win'] = value

    @attributeSetter
    def units(self, value):
        """
        None, 'norm', 'cm', 'deg', 'degFlat', 'degFlatPos', or 'pix'

        If None then the current units of the :class:`~psychopy.visual.Window` will be used.
        See :ref:`units` for explanation of other options.

        Note that when you change units, you don't change the stimulus parameters
        and it is likely to change appearance. Example::

            # This stimulus is 20% wide and 50% tall with respect to window
            stim = visual.PatchStim(win, units='norm', size=(0.2, 0.5)

            # This stimulus is 0.2 degrees wide and 0.5 degrees tall.
            stim.units = 'deg'
        """
        if value != None and len(value):
            self.__dict__['units'] = value
        else:
            self.__dict__['units'] = self.win.units

        # Update size and position if they are defined (tested as numeric). If not, this is probably
        # during some init and they will be defined later, given the new unit.
        try:
            self.size * self.pos  # quick and dirty way to check that both are numeric. This avoids the heavier attributeSetter calls.
            self.size = self.size
            self.pos = self.pos
        except:
            pass

    @attributeSetter
    def useShaders(self, value):
        """Should shaders be used to render the stimulus (typically leave as `True`)

        If the system support the use of OpenGL shader language then leaving
        this set to True is highly recommended. If shaders cannot be used then
        various operations will be slower (notably, changes to stimulus color
        or contrast)
        """
        if value == True and self.win._haveShaders == False:
            logging.error("Shaders were requested but aren't available. Shaders need OpenGL 2.0+ drivers")
        if value != self.useShaders:  # if there's a change...
            self.__dict__['useShaders'] = value
            if hasattr(self,'tex'):
                self.tex = self.tex  # calling attributeSetter
            elif hasattr(self, 'mask'):
                self.mask = self.mask  # calling attributeSetter (does the same as mask)
            if hasattr(self,'_imName'):
                self.setIm(self._imName, log=False)
            if self.__class__.__name__ == 'TextStim':
                self._needSetText = True
            self._needUpdate = True
    def setUseShaders(self, value=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message"""
        setAttribute(self, 'useShaders', value, log)  # call attributeSetter

    def draw(self):
        raise NotImplementedError('Stimulus classes must override visual.BaseVisualStim.draw')

    def _selectWindow(self, win):
        #don't call switch if it's already the curr window
        if win!=glob_vars.currWindow and win.winType=='pyglet':
            win.winHandle.switch_to()
            glob_vars.currWindow = win

    def _updateList(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set()
        Chooses between using and not using shaders each call.
        """
        if self.useShaders:
            self._updateListShaders()
        else:
            self._updateListNoShaders()

class BaseVisualStim(MinimalStim, WindowMixin, LegacyVisualMixin):
    """A template for a visual stimulus class.

    Actual visual stim like GratingStim, TextStim etc... are based on this.
    Not finished...?

    Methods defined here will override Minimal & Legacy, but best to avoid
    that for simplicity & clarity.
    """
    def __init__(self, win, units=None, name='', autoLog=None):
        self.autoLog = False  # just to start off during init, set at end
        self.win = win
        self.units = units
        self._rotationMatrix = [[1.,0.],[0.,1.]] #no rotation as a default
        # self.autoLog is set at end of MinimalStim.__init__
        super(BaseVisualStim, self).__init__(name=name, autoLog=autoLog)
        if self.autoLog:
            logging.warning("%s is calling BaseVisualStim.__init__() with autolog=True. Set autoLog to True only at the end of __init__())" \
                            %(self.__class__.__name__))

    @attributeSetter
    def opacity(self, value):
        """Determines how visible the stimulus is relative to background

        The value should be a single float ranging 1.0 (opaque) to 0.0
        (transparent). :ref:`Operations <attrib-operations>` are supported.
        Precisely how this is used depends on the :ref:`blendMode`.
        """
        self.__dict__['opacity'] = value

        if not 0 <= value <= 1 and self.autoLog:
            logging.warning('Setting opacity outside range 0.0 - 1.0 has no additional effect')

        #opacity is coded by the texture, if not using shaders
        if hasattr(self, 'useShaders') and not self.useShaders:
            if hasattr(self,'mask'):
                self.mask = self.mask  # call attributeSetter

    @attributeSetter
    def ori(self, value):
        """The orientation of the stimulus (in degrees).

        Should be a single value (:ref:`scalar <attrib-scalar>`). :ref:`Operations <attrib-operations>` are supported.

        Orientation convention is like a clock: 0 is vertical, and positive
        values rotate clockwise. Beyond 360 and below zero values wrap
        appropriately.

        """
        self.__dict__['ori'] = value
        radians = value*0.017453292519943295
        self._rotationMatrix = numpy.array([[numpy.cos(radians), -numpy.sin(radians)],
                                [numpy.sin(radians), numpy.cos(radians)]])
        self._needVertexUpdate=True #need to update update vertices
        self._needUpdate = True

    @attributeSetter
    def size(self, value):
        """The size (width, height) of the stimulus in the stimulus :ref:`units <units>`

        Value should be :ref:`x,y-pair <attrib-xy>`, :ref:`scalar <attrib-scalar>` (applies to both dimensions)
        or None (resets to default). :ref:`Operations <attrib-operations>` are supported.

        Sizes can be negative (causing a mirror-image reversal) and can extend beyond the window.

        Example::

            stim.size = 0.8  # Set size to (xsize, ysize) = (0.8, 0.8), quadratic.
            print stim.size  # Outputs array([0.8, 0.8])
            stim.size += (0.5, -0.5)  # make wider and flatter. Is now (1.3, 0.3)

        Tip: if you can see the actual pixel range this corresponds to by
        looking at `stim._sizeRendered`
        """
        value = val2array(value)  # Check correct user input
        self._requestedSize = value  #to track whether we're just using a default
        # None --> set to default
        if value is None:
            """Set the size to default (e.g. to the size of the loaded image etc)"""
            #calculate new size
            if self._origSize is None:  #not an image from a file
                value = numpy.array([0.5, 0.5])  #this was PsychoPy's original default
            else:
                #we have an image - calculate the size in `units` that matches original pixel size
                if self.units == 'pix':
                    value = numpy.array(self._origSize)
                elif self.units in ['deg', 'degFlatPos', 'degFlat']:
                    #NB when no size has been set (assume to use orig size in pix) this should not
                    #be corrected for flat anyway, so degFlat==degFlatPos
                    value = pix2deg(numpy.array(self._origSize, float), self.win.monitor)
                elif self.units == 'norm':
                    value = 2 * numpy.array(self._origSize, float) / self.win.size
                elif self.units == 'height':
                    value = numpy.array(self._origSize, float) / self.win.size[1]
                elif self.units == 'cm':
                    value = pix2cm(numpy.array(self._origSize, float), self.win.monitor)
                else:
                    raise AttributeError, "Failed to create default size for ImageStim. Unsupported unit, %s" %(repr(self.units))
        self.__dict__['size'] = value
        self._needVertexUpdate=True
        self._needUpdate = True
        if hasattr(self, '_calcCyclesPerStim'):
            self._calcCyclesPerStim()

    @attributeSetter
    def pos(self, value):
        """The position of the center of the stimulus in the stimulus :ref:`units <units>`

        `value` should be an :ref:`x,y-pair <attrib-xy>`. :ref:`Operations <attrib-operations>`
        are also supported.

        Example::

            stim.pos = (0.5, 0)  # Set slightly to the right of center
            stim.pos += (0.5, -1)  # Increment pos rightwards and upwards. Is now (1.0, -1.0)
            stim.pos *= 0.2  # Move stim towards the center. Is now (0.2, -0.2)

        Tip: If you need the position of stim in pixels, you can obtain it like this:

            from psychopy.tools.monitorunittools import posToPix
            posPix = posToPix(stim)
        """
        self.__dict__['pos'] = val2array(value, False, False)
        self._needVertexUpdate=True
        self._needUpdate = True

    def setPos(self, newPos, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'pos', val2array(newPos, False), log, operation)
    def setDepth(self, newDepth, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'depth', newDepth, log, operation)
    def setSize(self, newSize, operation='', units=None, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        if units is None:
            units=self.units#need to change this to create several units from one
        setAttribute(self, 'size', val2array(newSize, False), log, operation)
    def setOri(self, newOri, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'ori', newOri, log, operation)
    def setOpacity(self, newOpacity, operation='', log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message
        """
        setAttribute(self, 'opacity', newOpacity, log, operation)
    def _set(self, attrib, val, op='', log=None):
        """DEPRECATED since 1.80.04 + 1. Use setAttribute() and val2array() instead."""
        #format the input value as float vectors
        if type(val) in [tuple, list, numpy.ndarray]:
            val = val2array(val)

        # Set attribute with operation and log
        setAttribute(self, attrib, val, log, op)

        # For DotStim
        if attrib in ['nDots','coherence']:
            self.coherence=round(self.coherence*self.nDots)/self.nDots
