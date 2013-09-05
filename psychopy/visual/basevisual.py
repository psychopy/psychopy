#!/usr/bin/env python

'''A base class that is subclassed to produce specific visual stimuli'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import copy

import psychopy  # so we can get the __path__
from psychopy import logging

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import attributeSetter, setWithOperation
from psychopy.tools.colorspacetools import dkl2rgb, lms2rgb
from psychopy.tools.monitorunittools import cm2pix, deg2pix, pix2cm, pix2deg
from psychopy.visual.helpers import (pointInPolygon, polygonsOverlap,
                                     setColor, setTexIfNoShaders)

import numpy

global currWindow
currWindow = None

from psychopy.constants import NOT_STARTED, STARTED, STOPPED


class BaseVisualStim(object):
    """A template for a stimulus class, on which GratingStim, TextStim etc... are based.
    Not finished...?
    """
    def __init__(self, win, units=None, name='', autoLog=True):
        self.win = win
        self.name = name
        self.autoLog = autoLog
        self.status = NOT_STARTED
        self.units = units

    @attributeSetter
    def win(self, value):
        """
        a :class:`~psychopy.visual.Window` object (required)

           Example, drawing same stimulus in two different windows and display
           simultaneously. Assuming that you have two windows and a stimulus (win1, win2 and stim)::

               stim.win = win1  # stimulus will be drawn in win1
               stim.draw()  # stimulus is now drawn to win1
               stim.win = win2  # stimulus will be drawn in win2
               stim.draw()  # it is now drawn in win2
               win1.flip(waitBlanking=False)  # do not wait for next monitor update
               win2.flip()  # wait for vertical blanking.
        """
        self.__dict__['win'] = value

    # Might seem simple at first, but this ensures that "name" attribute
    # appears in docs and that name setting and updating is logged.
    @attributeSetter
    def name(self, value):
        """
        String

            The name of the object to be using during logged messages about this stim.
            Example::

                stim = visual.TextStim(win, text='happy message', name='positive')
                stim.draw(); win.flip();  # log will include name
                stim.text = 'sad message'
                stim.name = 'negative'
                stim.draw(); win.flip()  # log will include name
        """
        self.__dict__['name'] = value

    @attributeSetter
    def units(self, value):
        """
        None, 'norm', 'cm', 'deg' or 'pix'

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

        if self.units in ['norm', 'height']:
            self._winScale=self.units
        else:
            self._winScale='pix' #set the window to have pixels coords

        # Update size and position if they are defined. If not, this is probably
        # during some init and they will be defined later, given the new unit.
        if not isinstance(self.size, attributeSetter) and not isinstance(self.pos, attributeSetter):
            self.size = self.size
            self.pos = self.pos

    @attributeSetter
    def opacity(self, value):
        """
        Float. :ref:`operations <attrib-operations>` supported.
            Set the opacity of the stimulus.
            Should be between 1.0 (opaque) and 0.0 (transparent).
        """
        self.__dict__['opacity'] = value

        if not 0 <= value <= 1 and self.autoLog:
            logging.warning('Setting opacity outside range 0.0 - 1.0 has no additional effect')

        #opacity is coded by the texture, if not using shaders
        if hasattr(self, 'useShaders') and not self.useShaders:
            if hasattr(self,'mask'):
                self.mask = self.mask

    @attributeSetter
    def contrast(self, value):
        """
        Float between -1 (negative) and 1 (unchanged). :ref:`operations <attrib-operations>` supported.
            Set the contrast of the stimulus, i.e. scales how far the stimulus
            deviates from the middle grey. (This is a multiplier for the values
            given in the color description of the stimulus). Examples::

                stim.contrast = 1.0  # unchanged contrast
                stim.contrast = 0.5  # decrease contrast
                stim.contrast = 0.0  # uniform, no contrast
                stim.contrast = -0.5 # slightly inverted
                stim.contrast = -1   # totally inverted

            Setting contrast outside range -1 to 1 is possible, but may
            produce strange results if color values exceeds the colorSpace limits.::

                stim.contrast = 1.2 # increases contrast.
                stim.contrast = -1.2  # inverts with increased contrast
        """
        self.__dict__['contrast'] = value

        # If we don't have shaders we need to rebuild the stimulus
        if hasattr(self, 'useShaders'):
            if not self.useShaders:
                if self.__class__.__name__ == 'TextStim':
                    self.setText(self.text)
                if self.__class__.__name__ == 'ImageStim':
                    self.setImage(self._imName)
                if self.__class__.__name__ in ('GratingStim', 'RadialStim'):
                    self.tex = self.tex
                if self.__class__.__name__ in ('ShapeStim','DotStim'):
                    pass # They work fine without shaders?
                else:
                    logging.warning('Tried to set contrast while useShaders = False but stimulus was not rebuild. Contrast might remain unchanged.')
        elif log:
            logging.warning('Contrast was set on class where useShaders was undefined. Contrast might remain unchanged')

    @attributeSetter
    def useShaders(self, value):
        """
        True/False (default is *True*, if shaders are supported by the system)
            Set whether shaders are used to render stimuli.
        """
        #NB TextStim overrides this function, so changes here may need changing there too
        self.__dict__['useShaders'] = value
        if value == True and self.win._haveShaders == False:
            logging.error("Shaders were requested but aren't available. Shaders need OpenGL 2.0+ drivers")
        if value != self.useShaders:
            self.useShaders = value
            if hasattr(self,'tex'):
                self.tex = self.tex
            elif hasattr(self,'_imName'):
                self.setIm(self._imName, log=False)
            self.mask = self.mask
            self._needUpdate = True

    @attributeSetter
    def ori(self, value):
        """
        :ref:`scalar <attrib-scalar>`. :ref:`operations <attrib-operations>` supported.
            Set the stimulus orientation in degrees.
            ori can be greater than 360 and smaller than 0.
        """
        self.__dict__['ori'] = value

    @attributeSetter
    def autoDraw(self, value):
        """
        True or False.
            Add or remove a stimulus from the list of stimuli that will be
            automatically drawn on each flip. You do NOT need to call this on every frame flip!
            True to add the stimulus to the draw list, False to remove it.
        """
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

    @attributeSetter
    def pos(self, value):
        """
        :ref:`x,y-pair <attrib-xy>`. :ref:`operations <attrib-operations>` supported.
            Set the stimulus position in the `units` inherited from the stimulus.
            Either list [x, y], tuple (x, y) or numpy.ndarray ([x, y]) with two elements.

            Example::

                stim.pos = (0.5, 0)  # Slightly to the right
                stim.pos += (0.5, -1)  # Move right and up. Is now (1.0, -1.0)
                stim.pos *= 0.2  # Move towards the center. Is now (0.2, -0.2)

            Tip: if you can see the actual pixel range this corresponds to by
            looking at stim._posRendered
        """
        self.__dict__['pos'] = val2array(value, False, False)
        self._calcPosRendered()

    @attributeSetter
    def size(self, value):
        """
        :ref:`x,y-pair <attrib-xy>`, :ref:`scalar <attrib-scalar>` or None (resets to default). Supports :ref:`operations <attrib-operations>`.
            Units are inherited from the stimulus.
            Sizes can be negative and can extend beyond the window.

            Example::

                stim.size = 0.8  # Set size to (xsize, ysize) = (0.8, 0.8), quadratic.
                print stim.size  # Outputs array([0.8, 0.8])
                stim.size += (0,5, -0.5)  # make wider and flatter. Is now (1.3, 0.3)

            Tip: if you can see the actual pixel range this corresponds to by
            looking at stim._sizeRendered
        """
        value = val2array(value)  # Check correct user input
        self._requestedSize = value  #to track whether we're just using a default
        # None --> set to default
        if value == None:
            """Set the size to default (e.g. to the size of the loaded image etc)"""
            #calculate new size
            if self._origSize is None:  #not an image from a file
                value = numpy.array([0.5, 0.5])  #this was PsychoPy's original default
            else:
                #we have an image - calculate the size in `units` that matches original pixel size
                if self.units == 'pix': value = numpy.array(self._origSize)
                elif self.units == 'deg': value = pix2deg(numpy.array(self._origSize, float), self.win.monitor)
                elif self.units == 'cm': value = pix2cm(numpy.array(self._origSize, float), self.win.monitor)
                elif self.units == 'norm': value = 2 * numpy.array(self._origSize, float) / self.win.size
                elif self.units == 'height': value = numpy.array(self._origSize, float) / self.win.size[1]
        self.__dict__['size'] = value
        self._calcSizeRendered()
        if hasattr(self, '_calcCyclesPerStim'):
            self._calcCyclesPerStim()
        self._needUpdate = True

    @attributeSetter
    def autoLog(self, value):
        """
        True or False.
            Turn on (or off) autoLogging for this stimulus. This logs every
            parameter change and other significant events.
        """
        self.__dict__['autoLog'] = value

    @attributeSetter
    def depth(self, value):
        """
        Deprecated. Depth is now controlled simply by drawing order.
        """
        self.__dict__['depth'] = value

    @attributeSetter
    def color(self, value):
        """
        String: color name or hex.

        Scalar or sequence for rgb, dkl or other :ref:`colorspaces`. :ref:`operations <attrib-operations>` supported for these.

            OBS: when color is specified using numbers, it is interpreted with
            respect to the stimulus' current colorSpace.

            Can be specified in one of many ways. If a string is given then it
            is interpreted as the name of the color. Any of the standard html/X11
            `color names <http://www.w3schools.com/html/html_colornames.asp>`
            can be used. e.g.::

                myStim.color = 'white'
                myStim.color = 'RoyalBlue'  #(the case is actually ignored)

            A hex value can be provided, also formatted as with web colors. This can be
            provided as a string that begins with # (not using python's usual 0x000000 format)::

                myStim.color = '#DDA0DD'  #DDA0DD is hexadecimal for plum

            You can also provide a triplet of values, which refer to the coordinates
            in one of the :ref:`colorspaces`. If no color space is specified then the color
            space most recently used for this stimulus is used again.::

                myStim.color = [1.0,-1.0,-1.0]  #if colorSpace='rgb': a red color in rgb space
                myStim.color = [0.0,45.0,1.0] #if colorSpace='dkl': DKL space with elev=0, azimuth=45
                myStim.color = [0,0,255] #if colorSpace='rgb255': a blue stimulus using rgb255 space

            Lastly, a single number can be provided, x, which is equivalent to providing
            [x,x,x].::

                myStim.color = 255  #if colorSpace='rgb255': all guns o max

            :ref:`Operations <attrib-operations>` work just like with x-y pairs,
            but has a different meaning here. For colors specified as a triplet
            of values (or single intensity value) the new value will perform
            this operation on the previous color. Assuming that colorSpace='rgb'::

                thisStim.color += [1,1,1]  #increment all guns by 1 value
                thisStim.color *= -1  #multiply the color by -1 (which in this space inverts the contrast)
                thisStim.color *= [0.5, 0, 1]  #decrease red, remove green, keep blue
        """
        setColor(self, value, rgbAttrib='rgb', colorAttrib='color')

    @attributeSetter
    def colorSpace(self, value):
        """
        String or None

            defining which of the :ref:`colorspaces` to use. For strings and hex
            values this is not needed. If None the default colorSpace for the stimulus is
            used (defined during initialisation).

            Please note that changing colorSpace does not change stimulus parameters. Example::

                # A light green text
                stim = visual.TextStim(win, 'Color me!', color=(0, 1, 0), colorSpace='rgb')

                # An almost-black text
                stim.colorSpace = 'rgb255'

                # Make it light green again
                stim.color = (128, 255, 128)
        """
        self.__dict__['colorSpace'] = value

    def draw(self):
        raise NotImplementedError('Stimulus classes must overide _BaseVisualStim.draw')
    def setPos(self, newPos, operation='', log=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self._set('pos', val=newPos, op=operation, log=log)
    def setDepth(self, newDepth, operation='', log=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self._set('depth', newDepth, operation, log)
    def setSize(self, newSize, operation='', units=None, log=True):
        """Set the stimulus size [X,Y] in the specified (or inherited) `units`
        """
        if units==None: units=self.units#need to change this to create several units from one
        self._set('size', newSize, op=operation, log=log)
    def setOri(self, newOri, operation='', log=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self._set('ori',val=newOri, op=operation, log=log)
    def setOpacity(self, newOpacity, operation='', log=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self._set('opacity', newOpacity, operation, log=log)
    def setContrast(self, newContrast, operation='', log=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self._set('contrast', newContrast, operation, log=log)
    def setDKL(self, newDKL, operation=''):
        """DEPRECATED since v1.60.05: Please use setColor
        """
        self._set('dkl', val=newDKL, op=operation)
        self.setRGB(dkl2rgb(self.dkl, self.win.dkl_rgb))
    def setLMS(self, newLMS, operation=''):
        """DEPRECATED since v1.60.05: Please use setColor
        """
        self._set('lms', value=newLMS, op=operation)
        self.setRGB(lms2rgb(self.lms, self.win.lms_rgb))
    def setRGB(self, newRGB, operation=''):
        """DEPRECATED since v1.60.05: Please use setColor
        """
        self._set('rgb', newRGB, operation)
        setTexIfNoShaders(self)
    def setColor(self, color, colorSpace=None, operation='', log=True):
        """
        Set the color of the stimulus.
        OBS: can be set using stim.color = value syntax instead.

        :Parameters:

        color :
            see documentation for color.

        colorSpace : string or None
            see documentation for colorSpace

        operation : one of '+','-','*','/', or '' for no operation (simply replace value)
            see documentation for color.
        """
        setColor(self,color, colorSpace=colorSpace, operation=operation,
                    rgbAttrib='rgb', #or 'fillRGB' etc
                    colorAttrib='color',
                    log=log)
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
        if type(val) in [tuple, list, numpy.ndarray]:
            val = val2array(val)

        # Handle operations
        setWithOperation(self, attrib, val, op)

        if log and self.autoLog:
            self.win.logOnFlip("Set %s %s=%s" %(self.name, attrib, getattr(self,attrib)),
                level=logging.EXP,obj=self)

    def setUseShaders(self, value=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self.useShaders = value
    def _selectWindow(self, win):
        global currWindow
        #don't call switch if it's already the curr window
        if win!=currWindow and win.winType=='pyglet':
            win.winHandle.switch_to()
            currWindow = win

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
    def _calcSizeRendered(self):
        """Calculate the size of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._sizeRendered=copy.copy(self.size)
        elif self.units in ['deg', 'degs']: self._sizeRendered=deg2pix(self.size, self.win.monitor)
        elif self.units=='cm': self._sizeRendered=cm2pix(self.size, self.win.monitor)
        else:
            logging.ERROR("Stimulus units should be 'height', 'norm', 'deg', 'cm' or 'pix', not '%s'" %self.units)
    def _calcPosRendered(self):
        """Calculate the pos of the stimulus in coords of the :class:`~psychopy.visual.Window` (normalised or pixels)"""
        if self.units in ['norm','pix', 'height']: self._posRendered= copy.copy(self.pos)
        elif self.units in ['deg', 'degs']: self._posRendered=deg2pix(self.pos, self.win.monitor)
        elif self.units=='cm': self._posRendered=cm2pix(self.pos, self.win.monitor)
    def setAutoDraw(self, value, log=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self.autoDraw = value
    def setAutoLog(self, value=True):
        """ Deprecated. Use 'stim.attribute = value' syntax instead"""
        self.autoLog = value
    def contains(self, x, y=None):
        """Determines if a point x,y is inside the extent of the stimulus.

        Can accept: a) two args, x and y; b) one arg, as a point (x,y) that is
        list-like; or c) an object with a getPos() method that returns x,y, such
        as a mouse. Returns True if the point is within the area defined by `vertices`.
        This handles complex shapes, including concavities and self-crossings.

        Note that, if your stimulus uses a mask (such as a Gaussian blob) then
        this is not accounted for by the `contains` method; the extent of the
        stmulus is determined purely by the size, pos and orientation settings
        (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        if self.needVertexUpdate:
            self._calcVerticesRendered()
        if hasattr(x, 'getPos'):
            x, y = x.getPos()
        elif type(x) in [list, tuple, numpy.ndarray]:
            x, y = x[0], x[1]
        if self.units in ['deg','degs']:
            x, y = deg2pix(numpy.array((x, y)), self.win.monitor)
        elif self.units == 'cm':
            x, y = cm2pix(numpy.array((x, y)), self.win.monitor)
        if self.ori:
            oriRadians = numpy.radians(self.ori)
            sinOri = numpy.sin(oriRadians)
            cosOri = numpy.cos(oriRadians)
            x0, y0 = x-self._posRendered[0], y-self._posRendered[1]
            x = x0 * cosOri - y0 * sinOri + self._posRendered[0]
            y = x0 * sinOri + y0 * cosOri + self._posRendered[1]

        return pointInPolygon(x, y, self)

    def _getPolyAsRendered(self):
        """return a list of vertices as rendered; used by overlaps()
        """
        oriRadians = numpy.radians(self.ori)
        sinOri = numpy.sin(-oriRadians)
        cosOri = numpy.cos(-oriRadians)
        x = self._verticesRendered[:,0] * cosOri - self._verticesRendered[:,1] * sinOri
        y = self._verticesRendered[:,0] * sinOri + self._verticesRendered[:,1] * cosOri
        return numpy.column_stack((x,y)) + self._posRendered

    def overlaps(self, polygon):
        """Determines if this stimulus intersects another one. If `polygon` is
        another stimulus instance, then the vertices and location of that stimulus
        will be used as the polygon. Overlap detection is only approximate; it
        can fail with pointy shapes. Returns `True` if the two shapes overlap.

        Note that, if your stimulus uses a mask (such as a Gaussian blob) then
        this is not accounted for by the `overlaps` method; the extent of the
        stimulus is determined purely by the size, pos, and orientation settings
        (and by the vertices for shape stimuli).

        See coder demo, shapeContains.py
        """
        if self.needVertexUpdate:
            self._calcVerticesRendered()
        if self.ori:
            polyRendered = self._getPolyAsRendered()
            return polygonsOverlap(polyRendered, polygon)
        else:
            return polygonsOverlap(self, polygon)

    def _getDesiredRGB(self, rgb, colorSpace, contrast):
        """ Convert color to RGB while adding contrast
        Requires self.rgb, self.colorSpace and self.contrast"""
        # Ensure that we work on 0-centered color (to make negative contrast values work)
        if colorSpace not in ['rgb', 'dkl', 'lms', 'hsv']:
            rgb = (rgb / 255.0) * 2 - 1

        # Convert to RGB in range 0:1 and scaled for contrast
        desiredRGB = (rgb * contrast + 1) / 2.0

        # Check that boundaries are not exceeded
        if numpy.any(desiredRGB > 1.0) or numpy.any(desiredRGB < 0):
            logging.warning('Desired color %s (in RGB 0->1 units) falls outside the monitor gamut. Drawing blue instead'%desiredRGB) #AOH
            desiredRGB=[0.0, 0.0, 1.0]

        return desiredRGB
