#!/usr/bin/env python2

'''Class of text stimuli to be displayed in a :class:`~psychopy.visual.Window`
'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import os
import glob

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
import ctypes
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import logging, core
import psychopy.event

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.tools.monitorunittools import cm2pix, deg2pix, convertToPix
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.visual.basevisual import BaseVisualStim, ColorMixin

import numpy

try:
    import pygame
    havePygame = True
except:
    havePygame = False

defaultLetterHeight = {'cm': 1.0,
                     'deg': 1.0,
                     'degs': 1.0,
                     'degFlatPos': 1.0,
                     'degFlat': 1.0,
                     'norm': 0.1,
                     'height': 0.2,
                     'pix': 20,
                     'pixels': 20,
                     }
defaultWrapWidth = {'cm': 15.0,
                     'deg': 15.0,
                     'degs': 15.0,
                     'degFlatPos': 15.0,
                     'degFlat': 15.0,
                     'norm': 1,
                     'height': 1,
                     'pix': 500,
                     'pixels': 500,
                     }

class TextStim(BaseVisualStim, ColorMixin):
    """Class of text stimuli to be displayed in a :class:`~psychopy.visual.Window`
    """
    def __init__(self, win,
                 text="Hello World",
                 font="",
                 pos=(0.0,0.0),
                 depth=0,
                 rgb=None,
                 color=(1.0,1.0,1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 contrast=1.0,
                 units="",
                 ori=0.0,
                 height=None,
                 antialias=True,
                 bold=False,
                 italic=False,
                 alignHoriz='center',
                 alignVert='center',
                 fontFiles=[],
                 wrapWidth=None,
                 flipHoriz=False,
                 flipVert=False,
                 name=None,
                 autoLog=None):
        """
        **Performance OBS:** in general, TextStim is slower than many other visual
        stimuli, i.e. it takes longer to change some attributes. In general, it's
        the attributes that affect the shapes of the letters:
        ``text``, ``height``, ``font``, ``bold`` etc. These make the next .draw()
        slower because that sets the text again. You can make the draw()
        quick by calling re-setting the text (```myTextStim.text = myTextStim.text)
        when you've changed the parameters.

        In general, other attributes which merely affect the presentation of
        unchanged shapes are as fast as usual. This includes ``pos``, ``opacity`` etc.
        """

        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(TextStim, self).__init__(win, units=units, name=name, autoLog=False)

        self._needUpdate = True
        self._needVertexUpdate = True
        self.__dict__['useShaders'] = win._haveShaders  #use shaders if available by default, this is a good thing
        self.__dict__['alignHoriz'] = alignHoriz
        self.__dict__['alignVert'] = alignVert
        self.__dict__['antialias'] = antialias
        self.__dict__['font'] = font
        self.__dict__['bold'] = bold
        self.__dict__['italic'] = italic
        self.__dict__['text'] = '' #NB just a placeholder - real value set below
        self.__dict__['depth'] = depth
        self.__dict__['ori'] = ori
        self.__dict__['flipHoriz']= flipHoriz
        self.__dict__['flipVert'] = flipVert
        self._pygletTextObj=None
        self.__dict__['pos']= numpy.array(pos, float)

        #generate the texture and list holders
        self._listID = GL.glGenLists(1)
        if not self.win.winType=="pyglet":#pygame text needs a surface to render to
            self._texID = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self._texID))

        # Color stuff
        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb', log=False)
        else:
            self.setColor(color, log=False)

        self.__dict__['fontFiles'] = []
        self.fontFiles = fontFiles  # calls attributeSetter
        self.setHeight(height, log=False)  # calls setFont() at some point
        setAttribute(self, 'wrapWidth', wrapWidth, log=False)  # calls attributeSetter without log
        self.__dict__['opacity'] = float(opacity)
        self.__dict__['contrast'] = float(contrast)
        self.setText(text, log=False) #self.width and self._fontHeightPix get set with text and calcSizeRendered is called
        self._needUpdate = True

        # set autoLog now that params have been initialised
        self.__dict__['autoLog'] = autoLog or autoLog is None and self.win.autoLog
        if self.autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def __del__(self):
        if GL:  # because of pytest fail otherwise
            GL.glDeleteLists(self._listID, 1)

    @attributeSetter
    def height(self, height):
        """Float/int or None (set default).
        The height of the letters (including the entire box that surrounds the letters
        in the font). The width of the letters is then defined by the font.

        :ref:`Operations <attrib-operations>` supported."""
        #height in pix (needs to be done after units which is done during _Base.__init__)
        if height is None:
            if self.units in defaultLetterHeight:
                height = defaultLetterHeight[self.units]
            else:
                raise AttributeError, "TextStim does now know a default letter height for units %s" %(repr(self.units))
        self.__dict__['height'] = height
        self._heightPix = convertToPix(pos = numpy.array([0, 0]), vertices=numpy.array([0, self.height]), units=self.units, win=self.win)[1]

        #need to update the font to reflect the change
        self.setFont(self.font, log=False)
    def setHeight(self, height, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message. """
        setAttribute(self, 'height', height, log)

    @attributeSetter
    def font(self, font):
        """String. Set the font to be used for text rendering.
        font should be a string specifying the name of the font (in system resources)."""
        self.__dict__['font'] = None  #until we find one
        if self.win.winType=="pyglet":
            self._font = pyglet.font.load(font, int(self._heightPix), dpi=72, italic=self.italic, bold=self.bold)
            self.__dict__['font'] = font
        else:
            if font is None or len(font) == 0:
                self.__dict__['font'] = pygame.font.get_default_font()
            elif font in pygame.font.get_fonts():
                self.__dict__['font'] = font
            elif type(font) == str:
                #try to find a xxx.ttf file for it
                fontFilenames = glob.glob(font + '*')  #check for possible matching filenames
                if len(fontFilenames) > 0:
                    for thisFont in fontFilenames:
                        if thisFont[-4:] in ['.TTF', '.ttf']:
                            self.__dict__['font'] = thisFont  #take the first match
                            break #stop at the first one we find
                    #trhen check if we were successful
                    if self.font is None and font != "":
                        #we didn't find a ttf filename
                        logging.warning("Found %s but it doesn't end .ttf. Using default font." %fontFilenames[0])
                        self.__dict__['font'] = pygame.font.get_default_font()

            if self.font is not None and os.path.isfile(self.font):
                self._font = pygame.font.Font(self.font, int(self._heightPix), italic=self.italic, bold=self.bold)
            else:
                try:
                    self._font = pygame.font.SysFont(self.font, int(self._heightPix), italic=self.italic, bold=self.bold)
                    self.__dict__['font'] = font
                    logging.info('using sysFont ' + str(font))
                except:
                    self.__dict__['font'] = pygame.font.get_default_font()
                    logging.error("Couldn't find font %s on the system. Using %s instead!\n \
                              Font names should be written as concatenated names all in lower case.\n \
                              e.g. 'arial', 'monotypecorsiva', 'rockwellextra'..." %(font, self.font))
                    self._font = pygame.font.SysFont(self.font, int(self._heightPix), italic=self.italic, bold=self.bold)
        #re-render text after a font change
        self._needSetText=True
    def setFont(self, font, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message."""
        setAttribute(self, 'font', font, log)

    @attributeSetter
    def text(self, text):
        """String
        The text to be rendered. Use \n to make new lines. OBS: may be slow."""
        if text != None:  #make sure we have unicode object to render
            self.__dict__['text'] = unicode(text)
        if self.useShaders:
            self._setTextShaders(text)
        else:
            self._setTextNoShaders(text)
        self._needSetText = False
    def setText(self, text=None, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message."""
        setAttribute(self, 'text', text, log)

    def _setTextShaders(self,value=None):
        """Set the text to be rendered using the current font
        """
        if self.win.winType=="pyglet":
            self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (1.0,1.0,1.0, self.opacity),
                                                       width=self._wrapWidthPix)#width of the frame
#            self._pygletTextObj = pyglet.text.Label(self.text,self.font, int(self._heightPix),
#                                                       anchor_x=self.alignHoriz, anchor_y=self.alignVert,#the point we rotate around
#                                                       halign=self.alignHoriz,
#                                                       color = (int(127.5*self.rgb[0]+127.5),
#                                                            int(127.5*self.rgb[1]+127.5),
#                                                            int(127.5*self.rgb[2]+127.5),
#                                                            int(255*self.opacity)),
#                                                       multiline=True, width=self._wrapWidthPix)#width of the frame
            self.width, self._fontHeightPix = self._pygletTextObj.width, self._pygletTextObj.height
        else:
            self._surf = self._font.render(value, self.antialias, [255,255,255])
            self.width, self._fontHeightPix = self._surf.get_size()

            if self.antialias: smoothing = GL.GL_LINEAR
            else: smoothing = GL.GL_NEAREST
            #generate the textures from pygame surface
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)  #bind that name to the target
            GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, 4, self.width,self._fontHeightPix,
                                  GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pygame.image.tostring( self._surf, "RGBA",1))
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?

        self._needSetText=False
        self._needUpdate = True

    def _updateListShaders(self):
        """
        This is only used with pygame text - pyglet handles all from the draw()
        """
        if self._needSetText:
            self.setText(log=False)
        GL.glNewList(self._listID, GL.GL_COMPILE)
        #GL.glPushMatrix()

        #setup the shaderprogram
        #no need to do texture maths so no need for programs?
        #If we're using pyglet then this list won't be called, and for pygame shaders aren't enabled
        GL.glUseProgram(0)#self.win._progSignedTex)
        #GL.glUniform1i(GL.glGetUniformLocation(self.win._progSignedTex, "texture"), 0) #set the texture to be texture unit 0

        #coords:
        if self.alignHoriz in ['center', 'centre']: left = -self.width/2.0;    right = self.width/2.0
        elif self.alignHoriz =='right':    left = -self.width;    right = 0.0
        else: left = 0.0; right = self.width
        #how much to move bottom
        if self.alignVert in ['center', 'centre']: bottom=-self._fontHeightPix/2.0; top=self._fontHeightPix/2.0
        elif self.alignVert =='top': bottom=-self._fontHeightPix; top=0
        else: bottom=0.0; top=self._fontHeightPix
        Btex, Ttex, Ltex, Rtex = -0.01, 0.98, 0,1.0#there seems to be a rounding err in pygame font textures

        #unbind the mask texture regardless
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        if self.win.winType=="pyglet":
            #unbind the main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
#            GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0) #the texture is specified by pyglet.font.GlyphString.draw()
            GL.glEnable(GL.GL_TEXTURE_2D)
        else:
            #bind the appropriate main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            GL.glEnable(GL.GL_TEXTURE_2D)

        if self.win.winType=="pyglet":
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            self._pygletTextObj.draw()
        else:
            GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
            # right bottom
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Rtex, Btex)
            GL.glVertex3f(right,bottom,0)
            # left bottom
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Ltex,Btex)
            GL.glVertex3f(left,bottom,0)
            # left top
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Ltex,Ttex)
            GL.glVertex3f(left,top,0)
            # right top
            GL.glMultiTexCoord2f(GL.GL_TEXTURE0,Rtex,Ttex)
            GL.glVertex3f(right,top,0)
            GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glUseProgram(0)
        #GL.glPopMatrix()

        GL.glEndList()
        self._needUpdate = False

    def _setTextNoShaders(self,value=None):
        """Set the text to be rendered using the current font
        """
        desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)

        if self.win.winType=="pyglet":
            self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (desiredRGB[0],desiredRGB[1], desiredRGB[2], self.opacity),
                                                       width=self._wrapWidthPix,#width of the frame
                                                       )
            self.width, self._fontHeightPix = self._pygletTextObj.width, self._pygletTextObj.height
        else:
            self._surf = self._font.render(value, self.antialias,
                                           [desiredRGB[0]*255,
                                            desiredRGB[1]*255,
                                            desiredRGB[2]*255])
            self.width, self._fontHeightPix = self._surf.get_size()
            if self.antialias: smoothing = GL.GL_LINEAR
            else: smoothing = GL.GL_NEAREST
            #generate the textures from pygame surface
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)  #bind that name to the target
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA,
                            self.width,self._fontHeightPix,0,
                            GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, pygame.image.tostring( self._surf, "RGBA",1))
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,smoothing)    #linear smoothing if texture is stretched?
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,smoothing)    #but nearest pixel value if it's compressed?
        self._needUpdate = True

    def _updateListNoShaders(self):
        """
        The user shouldn't need this method since it gets called
        after every call to .set() Basically it updates the OpenGL
        representation of your stimulus if some parameter of the
        stimulus changes. Call it if you change a property manually
        rather than using the .set() command
        """
        if self._needSetText:
            self.setText(log=False)
        GL.glNewList(self._listID, GL.GL_COMPILE)

        #coords:
        if self.alignHoriz in ['center', 'centre']: left = -self.width/2.0;    right = self.width/2.0
        elif self.alignHoriz =='right':    left = -self.width;    right = 0.0
        else: left = 0.0; right = self.width
        #how much to move bottom
        if self.alignVert in ['center', 'centre']: bottom=-self._fontHeightPix/2.0; top=self._fontHeightPix/2.0
        elif self.alignVert =='top': bottom=-self._fontHeightPix; top=0
        else: bottom=0.0; top=self._fontHeightPix
        Btex, Ttex, Ltex, Rtex = -0.01, 0.98, 0,1.0#there seems to be a rounding err in pygame font textures
        if self.win.winType=="pyglet":
            #unbind the mask texture
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            #unbind the main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
        else:
            #bind the appropriate main texture
            GL.glActiveTextureARB(GL.GL_TEXTURE0_ARB)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
            #unbind the mask texture regardless
            GL.glActiveTextureARB(GL.GL_TEXTURE1_ARB)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

        if self.win.winType=="pyglet":
            self._pygletTextObj.draw()
        else:
            GL.glBegin(GL.GL_QUADS)                  # draw a 4 sided polygon
            # right bottom
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Rtex, Btex)
            GL.glVertex2f(right,bottom)
            # left bottom
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Ltex,Btex)
            GL.glVertex2f(left,bottom)
            # left top
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Ltex,Ttex)
            GL.glVertex2f(left,top)
            # right top
            GL.glMultiTexCoord2fARB(GL.GL_TEXTURE0_ARB,Rtex,Ttex)
            GL.glVertex2f(right,top)
            GL.glEnd()

        GL.glDisable(GL.GL_TEXTURE_2D)
        GL.glEndList()
        self._needUpdate = False

    @attributeSetter
    def flipHoriz(self, value):
        """If set to True then the text will be flipped horiztonally (left-to-right).
        Note that this is relative to the original, not relative to the current state."""
        self.__dict__['flipHoriz'] = value
    def setFlipHoriz(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message."""
        setAttribute(self, 'flipHoriz', newVal, log)

    @attributeSetter
    def flipVert(self, value):
        """If set to True then the text will be flipped vertically (top-to-bottom).
        Note that this is relative to the original, not relative to the current state."""
        self.__dict__['flipVert'] = value
    def setFlipVert(self, newVal=True, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message"""
        setAttribute(self, 'flipVert', newVal, log)

    def setFlip(self, direction, log=None):
        """(used by Builder to simplify the dialog)"""
        if direction == 'vert':
            self.setFlipVert(True, log=log)
        elif direction == 'horiz':
            self.setFlipHoriz(True, log=log)

    @attributeSetter
    def antialias(self, value):
        """True/False.
       Allow (or not) antialiasing the text. OBS: sets text, slow."""
        self.__dict__['antialias'] = value
        self._needSetText = True

    @attributeSetter
    def bold(self, value):
        """True/False.
        Make the text bold (better to use a bold font name)."""
        self.__dict__['bold'] = value
        self.font = self.font  # call attributeSetter

    @attributeSetter
    def italic(self, value):
        """True/False.
        Make the text italic (better to use a italic font name)."""
        self.__dict__['italic'] = value
        self.font = self.font  # call attributeSetter

    @attributeSetter
    def alignVert(self, value):
        """The vertical alignment ('top', 'bottom' or 'center')"""
        self.__dict__['alignVert'] = value
        self._needSetText = True

    @attributeSetter
    def alignHoriz(self, value):
        """The horizontal alignment ('left', 'right' or 'center')"""
        self.__dict__['alignHoriz'] = value
        self._needSetText = True

    @attributeSetter
    def fontFiles(self, fontFiles):
        """A list of additional files if the font is not in the standard system
        location (include the full path). OBS: fonts are added every time this
        value is set. Previous aren't deleted.

        E.g.::

            stim.fontFiles = ['SpringRage.ttf']  # load file(s)
            stim.font = 'SpringRage'  # set to font
            """
        self.__dict__['fontFiles'] += fontFiles
        for thisFont in fontFiles:
            pyglet.font.add_file(thisFont)

    @attributeSetter
    def wrapWidth(self, wrapWidth):
        """Int/float or None (set default).
        The width the text should run before wrapping.

        :ref:`Operations <attrib-operations>` supported."""
        if wrapWidth is None:
            if self.units in defaultWrapWidth:
                wrapWidth = defaultWrapWidth[self.units]
            else:
                raise AttributeError, "TextStim does now know a default wrap width for units %s" %(repr(self.units))
        self.__dict__['wrapWidth'] = wrapWidth
        self._wrapWidthPix = convertToPix(pos = numpy.array([0, 0]), vertices=numpy.array([self.wrapWidth, 0]), units=self.units, win=self.win)[0]
        self._needSetText = True

    @property
    def posPix(self):
        """This determines the coordinates in pixels of the position for the
        current stimulus, accounting for pos and units. This property should
        automatically update if `pos` is changed"""
        #because this is a property getter we can check /on-access/ if it needs updating :-)
        if self._needVertexUpdate:
            self.__dict__['posPix'] = convertToPix(vertices = [0,0], pos = self.pos, units=self.units, win = self.win)
        self._needVertexUpdate = False
        return self.__dict__['posPix']

    def draw(self, win=None):
        """
        Draw the stimulus in its relevant window. You must call
        this method after every MyWin.flip() if you want the
        stimulus to appear on that frame and then update the screen
        again.

        If win is specified then override the normal window of this stimulus.
        """
        if win is None:
            win=self.win
        self._selectWindow(win)

        GL.glPushMatrix()
        GL.glLoadIdentity()#for PyOpenGL this is necessary despite pop/PushMatrix, (not for pyglet)
        #scale and rotate
        prevScale = win.setScale('pix')#to units for translations
        GL.glTranslatef(self.posPix[0], self.posPix[1],0)  #NB depth is set already
        GL.glRotatef(-self.ori,0.0,0.0,1.0)
        win.setScale('pix', None, prevScale)#back to pixels for drawing surface
        GL.glScalef((1,-1)[self.flipHoriz], (1,-1)[self.flipVert], 1)  # x,y,z; -1=flipped

        if self.useShaders: #then rgb needs to be set as glColor
            #setup color
            desiredRGB = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
            GL.glColor4f(desiredRGB[0],desiredRGB[1],desiredRGB[2], self.opacity)

            GL.glUseProgram(self.win._progSignedTexFont)#self.win._progSignedTex)
#            GL.glUniform3iv(GL.glGetUniformLocation(self.win._progSignedTexFont, "rgb"), 1,
#                desiredRGB.ctypes.data_as(ctypes.POINTER(ctypes.c_float))) #set the texture to be texture unit 0
            GL.glUniform3f(GL.glGetUniformLocation(self.win._progSignedTexFont, "rgb"), desiredRGB[0],desiredRGB[1],desiredRGB[2])

        else: #color is set in texture, so set glColor to white
            GL.glColor4f(1,1,1,1)

        GL.glDisable(GL.GL_DEPTH_TEST) #should text have a depth or just on top?
        #update list if necss and then call it
        if win.winType=='pyglet':
            if self._needSetText:
                self.setText()
            #and align based on x anchor
            if self.alignHoriz=='right':
                GL.glTranslatef(-self.width,0,0)#NB depth is set already
            if self.alignHoriz in ['center', 'centre']:
                GL.glTranslatef(-self.width/2,0,0)#NB depth is set already

            #unbind the mask texture regardless
            GL.glActiveTexture(GL.GL_TEXTURE1)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
            #unbind the main texture
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glEnable(GL.GL_TEXTURE_2D)
            #then allow pyglet to bind and use texture during drawing

            self._pygletTextObj.draw()
            GL.glDisable(GL.GL_TEXTURE_2D)
        else:
            #for pygame we should (and can) use a drawing list
            if self._needUpdate:
                self._updateList()
            GL.glCallList(self._listID)
        if self.useShaders: GL.glUseProgram(0)#disable shader (but command isn't available pre-OpenGL2.0)

        #GL.glEnable(GL.GL_DEPTH_TEST)                   # Enables Depth Testing
        GL.glPopMatrix()
