#!/usr/bin/env python2

'''Take a "screen-shot" (full or partial), save to a ImageStim()-like
RBGA object.`'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

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
from psychopy.tools.attributetools import attributeSetter, logAttrib
from psychopy.tools.typetools import float_uint8
from psychopy.visual.grating import GratingStim

try:
    from PIL import Image
except ImportError:
    import Image

import numpy


class BufferImageStim(GratingStim):
    """
    Take a "screen-shot" (full or partial), save to a ImageStim()-like RBGA object.

    The class returns a screen-shot, i.e., a single collage image composed of static
    elements, ones that you want to treat as effectively a single stimulus. The
    screen-shot can be of the visible screen (front buffer) or hidden (back buffer).

    BufferImageStim aims to provide fast rendering, while still allowing dynamic
    orientation, position, and opacity. Its fast to draw but slow to init (like
    ImageStim). There is no support for dynamic depth.

    You specify the part of the screen to capture (in norm units), and optionally
    the stimuli themselves (as a list of items to be drawn). You get a screenshot
    of those pixels. If your OpenGL does not support arbitrary sizes, the image
    will be larger, using square powers of two if needed, with the excess image
    being invisible (using alpha). The aim is to preserve the buffer contents as
    rendered.

    Checks for OpenGL 2.1+, or uses square-power-of-2 images.

    status: seems to work on Mac, but limitations:
    - Screen units are not properly sorted out, would be better to allow pix too
    - Not tested on Windows, Linux, FreeBSD

    **Example**::

        # define lots of stimuli, make a list:
        mySimpleImageStim = ...
        myTextStim = ...
        stimList = [mySimpleImageStim, myTextStim]

        # draw stim list items & capture (slow; see EXP log for time required):
        screenshot = visual.BufferImageStim(myWin, stim=stimList)

        # render to screen (very fast, except for the first draw):
        while <conditions>:
            screenshot.draw()  # fast; can vary .ori, ._position, .opacity
            other_stuff.draw() # dynamic
            myWin.flip()

    See coder Demos > stimuli > bufferImageStim.py for a demo, with timing stats.

    :Author:
        - 2010 Jeremy Gray
    """
    def __init__(self, win, buffer='back', rect=(-1, 1, 1, -1), sqPower2=False,
        stim=(), interpolate=True, flipHoriz=False, flipVert=False, mask='None', pos=(0,0),
        name='', autoLog=True):
        """
        :Parameters:

            buffer :
                the screen buffer to capture from, default is 'back' (hidden).
                'front' is the buffer in view after win.flip()
            rect :
                a list of edges [left, top, right, bottom] defining a screen rectangle
                which is the area to capture from the screen, given in norm units.
                default is fullscreen: [-1, 1, 1, -1]
            stim :
                a list of item(s) to be drawn to the back buffer (in order). The back
                buffer is first cleared (without the win being flip()ed), then stim items
                are drawn, and finally the buffer (or part of it) is captured.
                Each item needs to have its own .draw() method, and have the same
                window as win.
            interpolate :
                whether to use interpolation (default = True, generally good,
                especially if you change the orientation)
            sqPower2 :
                - False (default) = use rect for size if OpenGL = 2.1+
                - True = use square, power-of-two image sizes
            flipHoriz :
                horizontally flip (mirror) the captured image, default = False
            flipVert :
                vertically flip (mirror) the captured image; default = False
        """
        # depends on: window._getRegionOfFrame

        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        self.autoLog=False #set this False first and change after attribs are set
        _clock = core.Clock()
        if stim: # draw all stim to the back buffer
            win.clearBuffer()
            buffer = 'back'
            for stimulus in list(stim):
                try:
                    if stimulus.win == win:
                        stimulus.draw()
                    else:
                        logging.warning('BufferImageStim.__init__: user requested "%s" drawn in another window' % repr(stimulus))
                except AttributeError:
                    logging.warning('BufferImageStim.__init__: "%s" failed to draw' % repr(stimulus))

        # take a screenshot of the buffer using win._getRegionOfFrame():
        glversion = pyglet.gl.gl_info.get_version()
        if glversion >= '2.1' and not sqPower2:
            region = win._getRegionOfFrame(buffer=buffer, rect=rect)
        else:
            if not sqPower2:
                logging.debug('BufferImageStim.__init__: defaulting to square power-of-2 sized image (%s)' % glversion )
            region = win._getRegionOfFrame(buffer=buffer, rect=rect, squarePower2=True)
        if stim:
            win.clearBuffer()

        # turn the RGBA region into a GratingStim()-like object:
        if win.units in ['norm']:
            pos *= win.size/2.
        super(BufferImageStim, self).__init__(win, tex=region, units='pix', mask=mask, pos=pos,
                             interpolate=interpolate, name=name, autoLog=False)

        # to improve drawing speed, move these out of draw:
        self.desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        self.thisScale = numpy.array([4, 4])
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        self.autoLog = autoLog

        if self.autoLog:
            logging.exp('BufferImageStim %s: took %.1fms to initialize' % (name, 1000 * _clock.getTime()))

    @attributeSetter
    def tex(self, value):
        """For BufferImageStim this method is not called by the user
        """
        self.__dict__['tex'] = tex = value
        id = self._texID
        pixFormat = GL.GL_RGB
        useShaders = self.useShaders
        interpolate = self.interpolate

        im = tex.transpose(Image.FLIP_TOP_BOTTOM)
        self._origSize=im.size

        #im = im.convert("RGBA") # should be RGBA because win._getRegionOfFrame() returns RGBA
        intensity = numpy.array(im).astype(numpy.float32)*0.0078431372549019607 - 1  # same as *2/255-1, but much faster

        if useShaders:#pixFormat==GL.GL_RGB and not wasLum
            internalFormat = GL.GL_RGB32F_ARB
            dataType = GL.GL_FLOAT
            data = intensity
        else: #pixFormat==GL.GL_RGB:# not wasLum, not useShaders  - an RGB bitmap with no shader options
            internalFormat = GL.GL_RGB
            dataType = GL.GL_UNSIGNED_BYTE
            data = float_uint8(intensity)

        pixFormat=GL.GL_RGBA # because win._getRegionOfFrame() returns RGBA
        internalFormat=GL.GL_RGBA32F_ARB

        if self.win.winType=='pygame':
            texture = data.tostring()#serialise
        else:#pyglet on linux needs ctypes instead of string object!?
            texture = data.ctypes#serialise

        #bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, id) #bind that name to the target
        GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
        #important if using bits++ because GL_LINEAR
        #sometimes extrapolates to pixel vals outside range
        if interpolate:
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
            if useShaders:#GL_GENERATE_MIPMAP was only available from OpenGL 1.4
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                    data.shape[1], data.shape[0], 0,
                    pixFormat, dataType, texture)
            else:#use glu
                GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)
                GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, internalFormat,
                    data.shape[1], data.shape[0], pixFormat, dataType, texture)
        else:
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, internalFormat,
                            data.shape[1], data.shape[0], 0,
                            pixFormat, dataType, texture)
    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the image will be flipped horiztonally (left-to-right).
        Note that this is relative to the original image, not relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')
    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the image will be flipped vertically (top-to-bottom).
        Note that this is relative to the original image, not relative to the current state.
        """
        self.flipVert = newVal
        logAttrib(self, log, 'flipVert')
    def draw(self, win=None):
        """
        Draws the BufferImage on the screen, similar to :class:`~psychopy.visual.ImageStim` `.draw()`.
        Allows dynamic position, size, rotation, mirroring, and opacity.
        Limitations / bugs: not sure what happens with shaders & self._updateList()
        """
        if win==None:
            win=self.win
        self._selectWindow(win)

        GL.glPushMatrix() # preserve state
        #GL.glLoadIdentity()

        GL.glScalef(self.thisScale[0] * (1,-1)[self.flipHoriz],  # dynamic flip
                    self.thisScale[1] * (1,-1)[self.flipVert], 1.0)

        # enable dynamic position, orientation, opacity; depth not working?
        GL.glColor4f(self.desiredRGB[0], self.desiredRGB[1], self.desiredRGB[2], self.opacity)

        GL.glCallList(self._listID) # make it happen
        GL.glPopMatrix() #return the view to previous state
