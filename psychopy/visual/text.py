#!/usr/bin/env python2

'''Class of text stimuli to be displayed in a :class:`~psychopy.visual.Window`
'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
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
from psychopy.tools.attributetools import logAttrib
from psychopy.visual.basevisual import BaseVisualStim
from psychopy.visual.basevisual import ColorMixin

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
                 flipHoriz=False, flipVert=False,
                 name='', autoLog=True):
        """
        :Parameters:
            win: A :class:`Window` object.
                Required - the stimulus must know where to draw itself
            text:
                The text to be rendered
            height:
                Height of the characters (including the ascent of the letter and the descent)
            antialias:
                boolean to allow (or not) antialiasing the text
            bold:
                Make the text bold (better to use a bold font name)
            italic:
                Make the text italic (better to use an actual italic font)
            alignHoriz:
                The horizontal alignment ('left', 'right' or 'center')
            alignVert:
                The vertical alignment ('top', 'bottom' or 'center')
            fontFiles:
                A list of additional files if the font is not in the standard system location (include the full path)
            wrapWidth:
                The width the text should run before wrapping
            flipHoriz : boolean
                Mirror-reverse the text in the left-right direction
            flipVert : boolean
                Mirror-reverse the text in the up-down direction
        """

        #what local vars are defined (these are the init params) for use by __repr__
        self._initParams = dir()
        self._initParams.remove('self')

        super(TextStim, self).__init__(win, units=units, name=name, autoLog=False)

        self.useShaders = win._haveShaders  #use shaders if available by default, this is a good thing
        self._needUpdate = True
        self.alignHoriz = alignHoriz
        self.alignVert = alignVert
        self.antialias = antialias
        self.bold=bold
        self.italic=italic
        self.text='' #NB just a placeholder - real value set below
        self.depth=depth
        self.ori=ori
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        self._pygletTextObj=None

        self.pos= numpy.array(pos, float)

        #height in pix (needs to be done after units which is done during _Base.__init__)
        if height==None:
            if self.units in defaultLetterHeight:
                height = defaultLetterHeight[self.units]
            else:
                raise AttributeError, "TextStim does now know a default letter height for units %s" %(repr(self.units))
        if wrapWidth==None:
            if self.units in defaultWrapWidth:
                wrapWidth = defaultWrapWidth[self.units]
            else:
                raise AttributeError, "TextStim does now know a default wrap width for units %s" %(repr(self.units))

        #treat letter height and wrapWidth as vertices (in degFlatPos they should not be 'corrected')
        wh = convertToPix(pos = numpy.array([0,0]), vertices=numpy.array([wrapWidth,height]), units=self.units, win=self.win)
        self._wrapWidthPix, self.heightPix = wh
        #generate the texture and list holders
        self._listID = GL.glGenLists(1)
        if not self.win.winType=="pyglet":#pygame text needs a surface to render to
            self._texID = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self._texID))

        self.colorSpace=colorSpace
        if rgb!=None:
            logging.warning("Use of rgb arguments to stimuli are deprecated. Please use color and colorSpace args instead")
            self.setColor(rgb, colorSpace='rgb', log=False)
        else:
            self.setColor(color, log=False)

        for thisFont in fontFiles:
            pyglet.font.add_file(thisFont)
        self.setFont(font, log=False)
        self.opacity = float(opacity)
        self.contrast = float(contrast)
        self.setText(text, log=False) #self.width and self.height get set with text and calcSizeRendered is called
        self._needUpdate = True

        #set autoLog (now that params have been initialised)
        self.autoLog= autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def __del__(self):
        GL.glDeleteLists(self._listID, 1)

    def setHeight(self,height, log=True):
        """Set the height of the letters (including the entire box that surrounds the letters
        in the font). The width of the letters is then defined by the font.
        """
        self.heightPix = convertToPix(pos = numpy.array([0,0]),
                                      vertices=numpy.array([0,height]),
                                      units=self.units, win=self.win)[1]
        #need to update the font to reflect the change
        self.setFont(self.fontname, log=False)
        logAttrib(self, log, 'height', height)
    def setFont(self, font, log=True):
        """Set the font to be used for text rendering.
        font should be a string specifying the name of the font (in system resources)
        """
        self.fontname=None#until we find one
        if self.win.winType=="pyglet":
            self._font = pyglet.font.load(font, int(self.heightPix), dpi=72, italic=self.italic, bold=self.bold)
            self.fontname=font
        else:
            if font==None or len(font)==0:
                self.fontname = pygame.font.get_default_font()
            elif font in pygame.font.get_fonts():
                self.fontname = font
            elif type(font)==str:
                #try to find a xxx.ttf file for it
                fontFilenames = glob.glob(font+'*')#check for possible matching filenames
                if len(fontFilenames)>0:
                    for thisFont in fontFilenames:
                        if thisFont[-4:] in ['.TTF', '.ttf']:
                            self.fontname = thisFont#take the first match
                            break #stop at the first one we find
                    #trhen check if we were successful
                    if self.fontname == None and font!="":
                        #we didn't find a ttf filename
                        logging.warning("Found %s but it doesn't end .ttf. Using default font." %fontFilenames[0])
                        self.fontname = pygame.font.get_default_font()

            if self.fontname is not None and os.path.isfile(self.fontname):
                self._font = pygame.font.Font(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
            else:
                try:
                    self._font = pygame.font.SysFont(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
                    self.fontname = font
                    logging.info('using sysFont ' + str(font))
                except:
                    self.fontname = pygame.font.get_default_font()
                    logging.error("Couldn't find font %s on the system. Using %s instead!\n \
                              Font names should be written as concatenated names all in lower case.\n \
                              e.g. 'arial', 'monotypecorsiva', 'rockwellextra'..." %(font, self.fontname))
                    self._font = pygame.font.SysFont(self.fontname, int(self.heightPix), italic=self.italic, bold=self.bold)
        #re-render text after a font change
        self._needSetText=True
        logAttrib(self, log, 'font', self.fontname)

    def setText(self,text=None, log=True):
        """Set the text to be rendered using the current font
        """
        if text!=None:#make sure we have unicode object to render
            self.text = unicode(text)
        if self.useShaders:
            self._setTextShaders(text)
        else:
            self._setTextNoShaders(text)
        self._needSetText=False
        logAttrib(self, log, 'text', text)
    def setRGB(self, text, operation='', log=True):
        self._set('rgb', text, operation, log=log)
        if not self.useShaders:
            self._needSetText=True
    def setColor(self, color, colorSpace=None, operation='', log=True):
        """Set the color of the stimulus. See :ref:`colorspaces` for further information
        about the various ways to specify colors and their various implications.

        :Parameters:

        color :
            Can be specified in one of many ways. If a string is given then it
            is interpreted as the name of the color. Any of the standard html/X11
            `color names <http://www.w3schools.com/html/html_colornames.asp>`
            can be used. e.g.::

                myStim.setColor('white')
                myStim.setColor('RoyalBlue')#(the case is actually ignored)

            A hex value can be provided, also formatted as with web colors. This can be
            provided as a string that begins with # (not using python's usual 0x000000 format)::

                myStim.setColor('#DDA0DD')#DDA0DD is hexadecimal for plum

            You can also provide a triplet of values, which refer to the coordinates
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
        #call setColor from super class to avoid recursion:
        ColorMixin.setColor(self, color, colorSpace=colorSpace,
            operation=operation, log=log)
        #but then update text objects if necess
        if not self.useShaders:
            self._needSetText=True
    def _setTextShaders(self,value=None):
        """Set the text to be rendered using the current font
        """
        if self.win.winType=="pyglet":
            self._pygletTextObj = pyglet.font.Text(self._font, self.text,
                                                       halign=self.alignHoriz, valign=self.alignVert,
                                                       color = (1.0,1.0,1.0, self.opacity),
                                                       width=self._wrapWidthPix)#width of the frame
#            self._pygletTextObj = pyglet.text.Label(self.text,self.fontname, int(self.heightPix),
#                                                       anchor_x=self.alignHoriz, anchor_y=self.alignVert,#the point we rotate around
#                                                       halign=self.alignHoriz,
#                                                       color = (int(127.5*self.rgb[0]+127.5),
#                                                            int(127.5*self.rgb[1]+127.5),
#                                                            int(127.5*self.rgb[2]+127.5),
#                                                            int(255*self.opacity)),
#                                                       multiline=True, width=self._wrapWidthPix)#width of the frame
            self.width, self.height = self._pygletTextObj.width, self._pygletTextObj.height
        else:
            self._surf = self._font.render(value, self.antialias, [255,255,255])
            self.width, self.height = self._surf.get_size()

            if self.antialias: smoothing = GL.GL_LINEAR
            else: smoothing = GL.GL_NEAREST
            #generate the textures from pygame surface
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)  #bind that name to the target
            GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, 4, self.width,self.height,
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
        if self.alignVert in ['center', 'centre']: bottom=-self.height/2.0; top=self.height/2.0
        elif self.alignVert =='top': bottom=-self.height; top=0
        else: bottom=0.0; top=self.height
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
            self.width, self.height = self._pygletTextObj.width, self._pygletTextObj.height
        else:
            self._surf = self._font.render(value, self.antialias,
                                           [desiredRGB[0]*255,
                                            desiredRGB[1]*255,
                                            desiredRGB[2]*255])
            self.width, self.height = self._surf.get_size()
            if self.antialias: smoothing = GL.GL_LINEAR
            else: smoothing = GL.GL_NEAREST
            #generate the textures from pygame surface
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)  #bind that name to the target
            GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA,
                            self.width,self.height,0,
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
        if self.alignVert in ['center', 'centre']: bottom=-self.height/2.0; top=self.height/2.0
        elif self.alignVert =='top': bottom=-self.height; top=0
        else: bottom=0.0; top=self.height
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

    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the text will be flipped horiztonally (left-to-right).
        Note that this is relative to the original, not relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')
    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the text will be flipped vertically (top-to-bottom).
        Note that this is relative to the original, not relative to the current state.
        """
        self.flipVert = newVal
        logAttrib(self, log, 'flipVert')
    def setFlip(self, direction, log=True):
        """(used by Builder to simplify the dialog)"""
        if direction == 'vert':
            self.setFlipVert(True, log=log)
        elif direction == 'horiz':
            self.setFlipHoriz(True, log=log)

    @property
    def posPix(self):
        """This determines the coordinates in pixels of the position for the
        current stimulus, accounting for pos and units. This property should
        automatically update if `pos` is changed
        """
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
        if win==None: win=self.win
        self._selectWindow(win)

        GL.glPushMatrix()
        GL.glLoadIdentity()#for PyOpenGL this is necessary despite pop/PushMatrix, (not for pyglet)
        #scale and rotate
        prevScale = win.setScale('pix')#to units for translations
        posPix = self.posPix
        GL.glTranslatef(posPix[0], posPix[1],0)#NB depth is set already
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
    def setUseShaders(self, val=True):
        """Set this stimulus to use shaders if possible.
        """
        if val==True and self.win._haveShaders==False:
            logging.warn("Shaders were requested but aren;t available. Shaders need OpenGL 2.0+ drivers")
        if val!=self.useShaders:
            self.useShaders=val
            self._needSetText=True
            self._needUpdate = True
    def overlaps(self, polygon):
        """Not implemented for TextStim
        """
        pass
    def contains(self, polygon):
        """Not implemented for TextStim
        """
        pass
