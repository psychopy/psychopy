#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
#  FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#
# -----------------------------------------------------------------------------
r"""
TextBox2 provides a combination of features from TextStim and TextBox and then
some more added:

    - fast like TextBox (TextStim is pyglet-based and slow)
    - provides for fonts that aren't monospaced (unlike TextBox)
    - adds additional options to use <b>bold<\b> and <i>italic<\i> tags in text

"""
import numpy as np
from pyglet import gl

from ..basevisual import BaseVisualStim, ColorMixin, ContainerMixin
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import convertToPix
from .fontmanager import FontManager, GLFont
from .. import shaders
from ..rect import Rect
from ... import core, alerts

allFonts = FontManager()

# compile global shader programs later (when we're certain a GL context exists)
rgbShader = None
alphaShader = None
showWhiteSpace = False

NONE=0
ITALIC=1
BOLD=2

codes = {'BOLD_START': u'\uE100',
         'BOLD_END': u'\uE101',
         'ITAL_START': u'\uE102',
         'ITAL_END': u'\uE103'}

defaultLetterHeight = {'cm': 1.0,
                       'deg': 1.0,
                       'degs': 1.0,
                       'degFlatPos': 1.0,
                       'degFlat': 1.0,
                       'norm': 0.1,
                       'height': 0.2,
                       'pix': 20,
                       'pixels': 20}

defaultBoxWidth = {'cm': 15.0,
                   'deg': 15.0,
                   'degs': 15.0,
                   'degFlatPos': 15.0,
                   'degFlat': 15.0,
                   'norm': 1,
                   'height': 1,
                   'pix': 500,
                   'pixels': 500}

wordBreaks = " -\n"  # what about ",."?

END_OF_THIS_LINE = 983349843

# If text is ". " we don't want to start next line with single space?

class TextBox2(BaseVisualStim, ContainerMixin, ColorMixin):
    def __init__(self, win, text, font,
                 pos=(0, 0), units=None, letterHeight=None,
                 size=None,
                 color=(1.0, 1.0, 1.0), colorSpace='rgb',
                 fillColor=None, fillColorSpace=None,
                 borderWidth=2, borderColor=None, borderColorSpace=None,
                 contrast=1,
                 opacity=None,
                 bold=False,
                 italic=False,
                 lineSpacing=1.0,
                 padding=None,  # gap between box and text
                 anchor='center',
                 alignment='left',
                 flipHoriz=False,
                 flipVert=False,
                 editable=False,
                 name='',
                 autoLog=None,
                 onTextCallback=None):
        """

        Parameters
        ----------
        win
        text
        font
        pos
        units
        letterHeight
        size : Specifying None gets the default size for this type of unit.
            Specifying [None, None] gets a TextBox that's expandable in both
            dimensions. Specifying [0.75, None] gets a textbox that expands in the
            length but fixed at 0.75 units in the width
        color
        colorSpace
        contrast
        opacity
        bold
        italic
        lineSpacing
        padding
        anchor
        alignment
        fillColor
        borderWidth
        borderColor
        flipHoriz
        flipVert
        editable
        name
        autoLog
        """

        BaseVisualStim.__init__(self, win, units=units, name=name)
        self.win = win
        self.colorSpace = colorSpace
        ColorMixin.foreColor.fset(self, color)  # Have to call the superclass directly on init as text has not been set
        self.onTextCallback = onTextCallback

        if units=='norm':
            raise NotImplementedError("TextBox2 doesn't support 'norm' units "
                                 "at the moment. Use 'height' units instead")
        # first set params needed to create font (letter sizes etc)
        if letterHeight is None:
            self.letterHeight = defaultLetterHeight[self.units]
        else:
            self.letterHeight = letterHeight
        # self._pixLetterHeight helps get font size right but not final layout
        if 'deg' in self.units:  # treat deg, degFlat or degFlatPos the same
            scaleUnits = 'deg'  # scale units are just for font resolution
        else:
            scaleUnits = self.units
        self._pixLetterHeight = convertToPix(
                self.letterHeight, pos=0, units=scaleUnits, win=self.win)
        if isinstance(self._pixLetterHeight, np.ndarray):
            # If pixLetterHeight is an array, take the Height value
            self._pixLetterHeight = self._pixLetterHeight[1]
        self._pixelScaling = self._pixLetterHeight / self.letterHeight
        if size is None:
            size = [defaultBoxWidth[self.units], None]
        self.size = size  # but this will be updated later to actual size
        self.bold = bold
        self.italic = italic
        self.lineSpacing = lineSpacing
        if padding is None:
            padding = self.letterHeight / 2.0
        self.padding = padding
        self.glFont = None  # will be set by the self.font attribute setter
        self.font = font
        # If font not found, default to Open Sans Regular and raise alert
        if not self.glFont:
            alerts.alert(4325, self, {
                'font': font,
                'weight': 'bold' if self.bold is True else 'regular' if self.bold is False else self.bold,
                'style': 'italic' if self.italic else '',
                'name': self.name})
            self.bold = False
            self.italic = False
            self.font = "Open Sans"

        # once font is set up we can set the shader (depends on rgb/a of font)
        if self.glFont.atlas.format == 'rgb':
            global rgbShader
            self.shader = rgbShader = shaders.Shader(
                    shaders.vertSimple, shaders.fragTextBox2)
        else:
            global alphaShader
            self.shader = alphaShader = shaders.Shader(
                    shaders.vertSimple, shaders.fragTextBox2alpha)
        self._needVertexUpdate = False  # this will be set True during layout

        # standard stimulus params
        self.pos = pos
        self.ori = 0.0
        self.depth = 0.0
        # used at render time
        self._lines = None  # np.array the line numbers for each char
        self._colors = None
        self._styles = None
        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        # params about positioning (after layout has occurred)
        self.anchor = anchor  # 'center', 'top_left', 'bottom-center'...
        self.alignment = alignment

        # box border and fill
        w, h = self.size
        self.borderWidth = borderWidth
        self.borderColor = borderColor
        self.fillColor = fillColor
        self.contrast = contrast
        self.opacity = opacity

        self.box = Rect(
                win, pos=self.pos,
                units=self.units,
                lineWidth=borderWidth, lineColor=borderColor,
                fillColor=fillColor, opacity=self.opacity,
                autoLog=False, fillColorSpace=self.colorSpace)
        # also bounding box (not normally drawn but gives tight box around chrs)
        self.boundingBox = Rect(
                win, pos=self.pos,
                units=self.units,
                lineWidth=1, lineColor=None, fillColor=fillColor, opacity=0.1,
                autoLog=False)
        # then layout the text (setting text triggers _layout())
        self._text = ''
        self.text = self.startText = text if text is not None else ""

        # caret
        self._editable = editable
        self.caret = Caret(self, color=self.color, width=5)


        self.autoLog = autoLog

    @property
    def editable(self):
        return self._editable
    
    @editable.setter
    def editable(self, editable):
        self._editable = editable
        if editable is False and self.hasFocus:
            if self.win:
                self.win.removeEditable(self)
        if editable is True:
            if self.win:
                self.win.addEditable(self)
        
    @property
    def pallette(self):
        self._pallette = {
            False: {
                'lineColor': self._borderColor,
                'lineWidth': self.borderWidth,
                'fillColor': self._fillColor
            },
            True: {
                'lineColor': self._borderColor-0.1,
                'lineWidth': self.borderWidth+1,
                'fillColor': self._fillColor+0.1
            }
        }
        return self._pallette[self.hasFocus]

    @pallette.setter
    def pallette(self, value):
        self._pallette = {
            False: value,
            True: value
        }

    @property
    def foreColor(self):
        return ColorMixin.foreColor.fget(self)
    @foreColor.setter
    def foreColor(self, value):
        ColorMixin.foreColor.fset(self, value)
        self._layout()
        if hasattr(self, "foreColor") and hasattr(self, 'caret'):
            self.caret.color = self._foreColor

    @attributeSetter
    def font(self, fontName, italic=False, bold=False):
        if isinstance(fontName, GLFont):
            self.glFont = fontName
            self.__dict__['font'] = fontName.name
        else:
            self.__dict__['font'] = fontName
            self.glFont = allFonts.getFont(
                    fontName,
                    size=int(round(self._pixLetterHeight)),
                    bold=self.bold, italic=self.italic)

    @property
    def fontMGR(self):
            return allFonts
    @fontMGR.setter
    def fontMGR(self, mgr):
        global allFonts
        if isinstance(mgr, FontManager):
            allFonts = mgr
        else:
            raise TypeError(f"Could not set font manager for TextBox2 object `{self.name}`, must be supplied with a FontManager object")

    @attributeSetter
    def anchor(self, anchor):
        """anchor is a string of terms, top, bottom, left, right, center

        e.g. 'top_center', 'center-right', 'topleft', 'center' are all valid"""
        self.__dict__['anchor'] = anchor
        # look for unambiguous terms first (top, bottom, left, right)
        self._anchorY = None
        self._anchorX = None
        if 'top' in anchor:
            self._anchorY = 'top'
        elif 'bottom' in anchor:
            self._anchorY = 'bottom'
        if 'right' in anchor:
            self._anchorX = 'right'
        elif 'left' in anchor:
            self._anchorX = 'left'
        # then 'center' can apply to either axis that isn't already set
        if self._anchorX is None:
            self._anchorX = 'center'
        if self._anchorY is None:
            self._anchorY = 'center'

    @attributeSetter
    def alignment(self, alignment):
        self.__dict__['alignment'] = alignment
        # look for unambiguous terms first (top, bottom, left, right)
        self._alignY = None
        self._alignX = None
        if 'top' in alignment:
            self._alignY = 'top'
        elif 'bottom' in alignment:
            self._alignY = 'bottom'
        if 'right' in alignment:
            self._alignX = 'right'
        elif 'left' in alignment:
            self._alignX = 'left'
        # then 'center' can apply to either axis that isn't already set
        if self._alignX is None:
            self._alignX = 'center'
        if self._alignY is None:
            self._alignY = 'center'

        self._needVertexUpdate = True

    @property
    def text(self):
        lastFormatter = NONE
        formatted_text = ''
        styles = self._styles
        for i, c in enumerate(self._text):
            if styles[i] == ITALIC and lastFormatter != styles[i]:
                formatted_text+='<i>%s'%(c)
            elif styles[i] == BOLD and lastFormatter != styles[i]:
                formatted_text+='<b>%s'%(c)
            
            elif styles[i] != ITALIC and lastFormatter == ITALIC:
                formatted_text+='</i>%s'%(c)
            elif styles[i] != BOLD and lastFormatter == BOLD:
                formatted_text+='</b>%s'%(c)
            else:
                formatted_text+=c
            lastFormatter = styles[i]
        return formatted_text
    
    @text.setter
    def text(self, text):
        text = text.replace('<i>', codes['ITAL_START'])
        text = text.replace('</i>', codes['ITAL_END'])
        text = text.replace('<b>', codes['BOLD_START'])
        text = text.replace('</b>', codes['BOLD_END'])      
        visible_text = ''.join([c for c in text if c not in codes.values()])
        self._styles = [0,]*len(visible_text)
        self._text = visible_text
        
        current_style=0
        ci = 0
        for c in text:
            if c == codes['ITAL_START']:
                current_style += ITALIC
            elif c == codes['BOLD_START']:
                current_style += BOLD
            elif c == codes['BOLD_END']:
                current_style -= BOLD
            elif c == codes['ITAL_END']:
                current_style -= ITALIC
            else:
                self._styles[ci]=current_style
                ci+=1
                
        self._layout()

    def addCharAtCaret(self, char):
        txt = self._text
        txt = txt[:self.caret.index] + char + txt[self.caret.index:]
        cstyle = NONE
        if len(self._styles) and self.caret.index <= len(self._styles):
            cstyle = self._styles[self.caret.index-1]
        self._styles.insert(self.caret.index, cstyle)
        self.caret.index += 1
        self._text = txt
        self._layout()

    def deleteCaretLeft(self):
        if self.caret.index > 0:
            txt = self._text
            ci = self.caret.index
            txt = txt[:ci-1] + txt[ci:]
            self._styles = self._styles[:ci-1]+self._styles[ci:]
            self.caret.index -= 1
            self._text = txt
            self._layout()

    def deleteCaretRight(self):
        ci = self.caret.index
        if ci < len(self._text):
            txt = self._text
            txt = txt[:ci] + txt[ci+1:]
            self._styles = self._styles[:ci]+self._styles[ci+1:]
            self._text = txt
            self._layout()
        
    def _layout(self):
        """Layout the text, calculating the vertex locations
        """
        def getLineWidthFromPix(pixVal):
            return pixVal / self._pixelScaling + self.padding * 2
        
        rgb = self._foreColor.render('rgba1')
        font = self.glFont

        # the vertices are initially pix (natural for freetype)
        # then we convert them to the requested units for self._vertices
        # then they are converted back during rendering using standard BaseStim
        visible_text = self._text
        vertices = np.zeros((len(visible_text) * 4, 2), dtype=np.float32)
        self._charIndices = np.zeros((len(visible_text)), dtype=int)
        self._colors = np.zeros((len(visible_text) * 4, 4), dtype=np.double)
        self._texcoords = np.zeros((len(visible_text) * 4, 2), dtype=np.double)
        self._glIndices = np.zeros((len(visible_text) * 4), dtype=int)

        # the following are used internally for layout
        self._lineNs = np.zeros(len(visible_text), dtype=int)
        self._lineTops = []  # just length of nLines
        self._lineBottoms = []
        self._lineLenChars = []  #
        self._lineWidths = []  # width in stim units of each line

        self._lineHeight = font.height * self.lineSpacing

        if np.isnan(self._requestedSize[0]):
            lineMax = float('inf')
        else:
            lineMax = (self._requestedSize[0] - self.padding) * self._pixelScaling

        current = [0, 0]
        fakeItalic = 0.0
        fakeBold = 0.0
        # for some reason glyphs too wide when using alpha channel only
        if font.atlas.format == 'alpha':
            alphaCorrection = 1 / 3.0
        else:
            alphaCorrection = 1

        wordLen = 0
        charsThisLine = 0
        wordsThisLine = 0
        lineN = 0

        for i, charcode in enumerate(self._text):
            printable = True  # unless we decide otherwise
            # handle formatting codes
            if self._styles[i] == NONE:
                fakeItalic = 0.0
                fakeBold = 0.0
            elif self._styles[i] == ITALIC:
                fakeItalic = 0.1 * font.size
            elif self._styles[i] == ITALIC:
                fakeBold = 0.3 * font.size

            # handle newline
            if charcode == '\n':
                printable = False

            # handle printable characters
            if printable:
                if showWhiteSpace and charcode == " ":
                    glyph = font[u"·"]
                else:
                    glyph = font[charcode]
                xBotL = current[0] + glyph.offset[0] - fakeItalic - fakeBold / 2
                xTopL = current[0] + glyph.offset[0] - fakeBold / 2
                yTop = current[1] + glyph.offset[1]
                xBotR = xBotL + glyph.size[0] * alphaCorrection + fakeBold
                xTopR = xTopL + glyph.size[0] * alphaCorrection + fakeBold
                yBot = yTop - glyph.size[1]
                u0 = glyph.texcoords[0]
                v0 = glyph.texcoords[1]
                u1 = glyph.texcoords[2]
                v1 = glyph.texcoords[3]
            else:
                glyph = font[u"·"]
                x = current[0] + glyph.offset[0]
                yTop = current[1] + glyph.offset[1]
                yBot = yTop - glyph.size[1]
                xBotL = x
                xTopL = x
                xBotR = x
                xTopR = x
                u0 = glyph.texcoords[0]
                v0 = glyph.texcoords[1]
                u1 = glyph.texcoords[2]
                v1 = glyph.texcoords[3]

            theseVertices = [[xTopL, yTop], [xBotL, yBot],
                             [xBotR, yBot], [xTopR, yTop]]
            texcoords = [[u0, v0], [u0, v1],
                         [u1, v1], [u1, v0]]

            vertices[i * 4:i * 4 + 4] = theseVertices
            self._texcoords[i * 4:i * 4 + 4] = texcoords
            self._colors[i*4 : i*4+4, :4] = rgb
            self._lineNs[i] = lineN
            current[0] = current[0] + glyph.advance[0] + fakeBold / 2
            current[1] = current[1] + glyph.advance[1]

            # are we wrapping the line?
            if charcode == "\n":
                lineWPix = current[0]
                current[0] = 0
                current[1] -= self._lineHeight
                lineN += 1
                charsThisLine += 1
                self._lineLenChars.append(charsThisLine)
                self._lineWidths.append(getLineWidthFromPix(lineWPix))
                charsThisLine = 0
                wordsThisLine = 0
            elif charcode in wordBreaks:
                wordLen = 0
                charsThisLine += 1
                wordsThisLine += 1
            elif printable:
                wordLen += 1
                charsThisLine += 1

            # end line with auto-wrap on space
            if current[0] >= lineMax and wordLen > 0 and wordsThisLine:
                # move the current word to next line
                lineBreakPt = vertices[(i - wordLen + 1) * 4, 0]
                wordWidth = current[0] - lineBreakPt
                # shift all chars of the word left by wordStartX
                vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 0] -= lineBreakPt
                vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 1] -= self._lineHeight
                # update line values
                self._lineNs[i - wordLen + 1: i + 1] += 1
                self._lineLenChars.append(charsThisLine - wordLen)
                self._lineWidths.append(getLineWidthFromPix(lineBreakPt))
                lineN += 1
                # and set current to correct location
                current[0] = wordWidth
                current[1] -= self._lineHeight
                charsThisLine = wordLen

            # have we stored the top/bottom of this line yet
            if lineN + 1 > len(self._lineTops):
                self._lineBottoms.append(current[1] + font.descender)
                self._lineTops.append(current[1] + self._lineHeight
                                      + font.descender/2)
            
        # finally add length of this (unfinished) line
        self._lineWidths.append(getLineWidthFromPix(current[0]))
        self._lineLenChars.append(charsThisLine)

        # convert the vertices to stimulus units
        self._rawVerts = vertices / self._pixelScaling

        # thisW = current[0] - glyph.advance[0] + glyph.size[0] * alphaCorrection
        # calculate final self.size and tightBox
        if np.isnan(self._requestedSize[0]):
            self.size[0] = max(self._lineWidths) + self.padding*2
        if np.isnan(self._requestedSize[1]):
            self.size[1] = ((lineN + 1) * self._lineHeight / self._pixelScaling
                            + self.padding * 2)

        # if we had to add more glyphs to make possible then 
        if self.glFont._dirty:
            self.glFont.upload()
            self.glFont._dirty = False
        self._needVertexUpdate = True

    def _getStartingVertices(self):
        """Returns vertices for a single non-printing char as a proxy
        (needed to get location for caret when there are no actual chars)"""
        yTop = self._anchorOffsetY - (self.glFont.height - self.glFont.ascender) * self.lineSpacing
        yBot = yTop - self._lineHeight
        x = 0
        theseVertices = np.array([[x, yTop], [x, yBot], [x, yBot], [x, yTop]])
        return theseVertices

    def draw(self):
        """Draw the text to the back buffer"""
        # Border width
        self.box.setLineWidth(self.pallette['lineWidth']) # Use 1 as base if border width is none
        #self.borderWidth = self.box.lineWidth
        # Border colour
        self.box.setLineColor(self.pallette['lineColor'], colorSpace='rgb')
        #self.borderColor = self.box.lineColor
        # Background
        self.box.setFillColor(self.pallette['fillColor'], colorSpace='rgb')
        #self.fillColor = self.box.fillColor

        if self._needVertexUpdate:
            #print("Updating vertices...")
            self._updateVertices()
        if self.fillColor is not None or self.borderColor is not None:
            self.box.draw()

        # self.boundingBox.draw()  # could draw for debug purposes
        gl.glPushMatrix()
        self.win.setScale('pix')

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.glFont.textureID)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glDisable(gl.GL_DEPTH_TEST)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        gl.glVertexPointer(2, gl.GL_DOUBLE, 0, self.verticesPix.ctypes)
        gl.glColorPointer(4, gl.GL_DOUBLE, 0, self._colors.ctypes)
        gl.glTexCoordPointer(2, gl.GL_DOUBLE, 0, self._texcoords.ctypes)

        self.shader.bind()
        self.shader.setInt('texture', 0)
        self.shader.setFloat('pixel', [1.0 / 512, 1.0 / 512])
        nVerts = len(self._text)*4

        gl.glDrawArrays(gl.GL_QUADS, 0, nVerts)
        self.shader.unbind()

        # removed the colors and font texture
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glDisableVertexAttribArray(1)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisable(gl.GL_TEXTURE_2D)

        if self.hasFocus:  # draw caret line
            self.caret.draw()

        gl.glPopMatrix()

    def reset(self):
        # Reset contents
        self.text = self.startText


    def contains(self, x, y=None, units=None, tight=False):
        """Returns True if a point x,y is inside the stimulus' border.

        Can accept variety of input options:
            + two separate args, x and y
            + one arg (list, tuple or array) containing two vals (x,y)
            + an object with a getPos() method that returns x,y, such
                as a :class:`~psychopy.event.Mouse`.

        Returns `True` if the point is within the area defined either by its
        `border` attribute (if one defined), or its `vertices` attribute if
        there is no .border. This method handles
        complex shapes, including concavities and self-crossings.

        Note that, if your stimulus uses a mask (such as a Gaussian) then
        this is not accounted for by the `contains` method; the extent of the
        stimulus is determined purely by the size, position (pos), and
        orientation (ori) settings (and by the vertices for shape stimuli).

        See Coder demos: shapeContains.py
        See Coder demos: shapeContains.py
        """
        if tight:
            return self.boundingBox.contains(x, y, units)
        else:
            return self.box.contains(x, y, units)

    def overlaps(self, polygon, tight=False):
        """Returns `True` if this stimulus intersects another one.

        If `polygon` is another stimulus instance, then the vertices
        and location of that stimulus will be used as the polygon.
        Overlap detection is typically very good, but it
        can fail with very pointy shapes in a crossed-swords configuration.

        Note that, if your stimulus uses a mask (such as a Gaussian blob)
        then this is not accounted for by the `overlaps` method; the extent
        of the stimulus is determined purely by the size, pos, and
        orientation settings (and by the vertices for shape stimuli).

        Parameters

        See coder demo, shapeContains.py
        """
        if tight:
            return self.boundingBox.overlaps(polygon)
        else:
            return self.box.overlaps(polygon)

    def _updateVertices(self):
        """Sets Stim.verticesPix and ._borderPix from pos, size, ori,
        flipVert, flipHoriz
        """
        # check whether stimulus needs flipping in either direction
        flip = np.array([1, 1])
        if hasattr(self, 'flipHoriz') and self.flipHoriz:
            flip[0] = -1  # True=(-1), False->(+1)
        if hasattr(self, 'flipVert') and self.flipVert:
            flip[1] = -1  # True=(-1), False->(+1)

        font = self.glFont
        # to start with the anchor is bottom left of *first line*
        if self._anchorY == 'top':
            self._anchorOffsetY = (-font.ascender / self._pixelScaling
                                   - self.padding)
            boxOffsetY = - self.size[1] / 2.0
        elif self._anchorY == 'center':
            self._anchorOffsetY = (
                    self.size[1] / 2
                    - (font.height / 2 - font.descender) / self._pixelScaling
                    - self.padding
            )
            boxOffsetY = 0
        elif self._anchorY == 'bottom':
            self._anchorOffsetY = (
                    self.size[1]
                    - (font.height / 2 + font.ascender) / self._pixelScaling
            )
            # self._anchorOffsetY = (-font.ascender / self._pixelScaling
            #                        - self.padding)
            boxOffsetY = + (self.size[1]) / 2.0
        else:
            raise ValueError('Unexpected value for _anchorY')

        # calculate anchor offsets (text begins on left=0, box begins center=0)
        if self._anchorX == 'right':
            self._anchorOffsetX = - self.size[0] + self.padding
            boxOffsetX = - self.size[0] / 2.0
        elif self._anchorX == 'center':
            self._anchorOffsetX = - self.size[0] / 2.0 + self.padding
            boxOffsetX = 0
        elif self._anchorX == 'left':
            self._anchorOffsetX = 0 + self.padding
            boxOffsetX = + self.size[0] / 2.0
        else:
            raise ValueError('Unexpected value for _anchorX')
        self.vertices = self._rawVerts + (self._anchorOffsetX, self._anchorOffsetY)

        vertsPix = convertToPix(vertices=self.vertices,
                                pos=self.pos,
                                win=self.win, units=self.units)
        self.__dict__['verticesPix'] = vertsPix

        # tight bounding box
        if self.vertices.shape[0] < 1:  # editable box with no letters?
            self.boundingBox.size = 0, 0
            self.boundingBox.pos = self.pos
        else:
            L = self.vertices[:, 0].min()
            R = self.vertices[:, 0].max()
            B = self.vertices[:, 1].min()
            T = self.vertices[:, 1].max()
            tightW = R-L
            Xmid = (R+L)/2
            tightH = T-B
            Ymid = (T+B)/2
            # for the tight box anchor offset is included in vertex calcs
            self.boundingBox.size = tightW, tightH
            self.boundingBox.pos = self.pos + (Xmid, Ymid)
        # box (larger than bounding box) needs anchor offest adding
        self.box.pos = self.pos + (boxOffsetX, boxOffsetY)
        self.box.size = self.size  # this might have changed from _requested

        self._needVertexUpdate = False

    def _onText(self, chr):
        """Called by the window when characters are received"""
        if chr == '\t':
            self.win.nextEditable()
            return
        if chr == '\r':  # make it newline not Carriage Return
            chr = '\n'
        self.addCharAtCaret(chr)
        if self.onTextCallback:
            self.onTextCallback()

    def _onCursorKeys(self, key):
        """Called by the window when cursor/del/backspace... are received"""
        if key == 'MOTION_UP':
            self.caret.row -= 1
        elif key == 'MOTION_DOWN':
            self.caret.row += 1
        elif key == 'MOTION_RIGHT':
            self.caret.char += 1
        elif key == 'MOTION_LEFT':
            self.caret.char -= 1
        elif key == 'MOTION_BACKSPACE':
            self.deleteCaretLeft()
        elif key == 'MOTION_DELETE':
            self.deleteCaretRight()
        elif key == 'MOTION_NEXT_WORD':
            pass
        elif key == 'MOTION_PREVIOUS_WORD':
            pass
        elif key == 'MOTION_BEGINNING_OF_LINE':
            self.caret.char = 0
        elif key == 'MOTION_END_OF_LINE':
            self.caret.char = END_OF_THIS_LINE
        elif key == 'MOTION_NEXT_PAGE':
            pass
        elif key == 'MOTION_PREVIOUS_PAGE':
            pass
        elif key == 'MOTION_BEGINNING_OF_FILE':
            pass
        elif key == 'MOTION_END_OF_FILE':
            pass
        else:
            print("Received unhandled cursor motion type: ", key)

    @property
    def hasFocus(self):
        if self.win and self.win.currentEditable == self:
            return True
        return False

    @hasFocus.setter
    def hasFocus(self, focus):
        if focus is False and self.hasFocus:
            # If focus is being set to False, tell window to 
            # give focus to next editable.
            if self.win:
                self.win.nextEditable()
        elif focus is True and self.hasFocus is False:
            # If focus is being set True, set textbox instance to be
            # window.currentEditable.
            if self.win:
                self.win.currentEditable=self
        return False

    def getText(self):
        """Returns the current text in the box, including formating tokens."""
        return self.text

    @property
    def visibleText(self):
        """Returns the current visible text in the box"""
        return self._text

    def getVisibleText(self):
        """Returns the current visible text in the box"""
        return self.visibleText

    @attributeSetter
    def pos(self, value):
        """The position of the center of the TextBox in the stimulus
        :ref:`units <units>`

        `value` should be an :ref:`x,y-pair <attrib-xy>`.
        :ref:`Operations <attrib-operations>` are also supported.

        Example::

            stim.pos = (0.5, 0)  # Set slightly to the right of center
            stim.pos += (0.5, -1)  # Increment pos rightwards and upwards.
                Is now (1.0, -1.0)
            stim.pos *= 0.2  # Move stim towards the center.
                Is now (0.2, -0.2)

        Tip: If you need the position of stim in pixels, you can obtain
        it like this:

            from psychopy.tools.monitorunittools import posToPix
            posPix = posToPix(stim)
        """
        self.__dict__['pos'] = val2array(value, False, False)
        try:
            self.box.pos = (self.__dict__['pos'] +
                            (self._anchorOffsetX, self._anchorOffsetY))
        except AttributeError:
            pass  # may not be created yet, which is fine
        self._needVertexUpdate = True
        self._needUpdate = True

    def setText(self, text=None, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'text', text, log)

    def setHeight(self, height, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message. """
        setAttribute(self, 'height', height, log)

    def setFont(self, font, log=None):
        """Usually you can use 'stim.attribute = value' syntax instead,
        but use this method if you need to suppress the log message.
        """
        setAttribute(self, 'font', font, log)


class Caret(ColorMixin):
    """
    Class to handle the caret (cursor) within a textbox. Do **not** call without a textbox.
    Parameters
        ----------
        textbox : psychopy.visual.TextBox2
            Textbox which caret corresponds to
        visible : bool
            Whether the caret is visible
        row : int
            Textbox row which caret is on
        char : int
            Text character within row which caret is on
        index : int
            Index of character which caret is on
        vertices : list, tuple
            Coordinates of each corner of caret
        width : int, float
            Width of caret line
        color : list, tuple, str
            Caret colour
    """

    def __init__(self, textbox, color, width, colorSpace='rgb'):
        self.textbox = textbox
        self.index = len(textbox._text)  # start off at the end
        self.autoLog = False
        self.width = width
        self.units = textbox.units
        self.colorSpace = colorSpace
        self.color = color

    def draw(self):
        if not self.visible:
            return
        if core.getTime() % 1 > 0.6:  # Flash every other second
            return
        gl.glLineWidth(self.width)
        gl.glColor4f(
            *self._foreColor.rgba1
        )
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(self.vertices[0, 0], self.vertices[0, 1])
        gl.glVertex2f(self.vertices[1, 0], self.vertices[1, 1])
        gl.glEnd()

    @property
    def visible(self):
        return self.textbox.hasFocus

    @property
    def row(self):
        """What row is caret on?"""
        # Check that index is with range of all character indices
        if len(self.textbox._lineNs) == 0:  # no chars at all
            return 0
        elif self.index > len(self.textbox._lineNs):
            self.index = len(self.textbox._lineNs)
        # Get line of index
        if self.index >= len(self.textbox._lineNs):
            return self.textbox._lineNs[-1]
        else:
            return self.textbox._lineNs[self.index]
    @row.setter
    def row(self, value):
        """Use line to index conversion to set index according to row value"""
        # Figure out how many characters into previous row the cursor was
        charsIn = self.char
        nRows = len(self.textbox._lineLenChars)
        # If new row is more than total number of rows, move to end of last row
        if value >= nRows:
            value = nRows
            charsIn = self.textbox._lineLenChars[-1]
        # If new row is less than 0, move to beginning of first row
        elif value < 0:
            value = 0
            charsIn = 0
        elif value == nRows-1 and charsIn > self.textbox._lineLenChars[value]:
            # last row last char
            charsIn = self.textbox._lineLenChars[value]
        elif charsIn > self.textbox._lineLenChars[value]-1:
            # end of a middle row (account for the newline)
            charsIn = self.textbox._lineLenChars[value]-1
        # Set new index in new row
        self.index = sum(self.textbox._lineLenChars[:value]) + charsIn

    @property
    def char(self):
        """What character within current line is caret on?"""
        # Check that index is with range of all character indices
        self.index = min(self.index, len(self.textbox._lineNs))
        self.index = max(self.index, 0)
        # Get first index of line, subtract from index to get char
        return self.index - sum(self.textbox._lineLenChars[:self.row])
    @char.setter
    def char(self, value):
        """Set character within row"""
        # If setting char to less than 0, move to last char on previous line
        row = self.row
        if value < 0:
            if row == 0:
                value = 0
            else:
                row -= 1
                value = self.textbox._lineLenChars[row]-1  # end of that row
        elif row >= len(self.textbox._lineLenChars)-1 and \
                value >= self.textbox._lineLenChars[-1]:
            # this is the last row
            row = len(self.textbox._lineLenChars)-1
            value = self.textbox._lineLenChars[-1]
        elif value == END_OF_THIS_LINE:
            value = self.textbox._lineLenChars[row]-1
        elif value >= self.textbox._lineLenChars[row]:
            # end of this row (not the last) so go to next
            row += 1
            value = 0
        # then calculate index
        if row:  # if not on first row
            self.index = sum(self.textbox._lineLenChars[:row]) + value
        else:
            self.index = value

    @property
    def vertices(self):
        textbox = self.textbox
        # check we have a caret index
        if self.index is None or self.index > len(textbox._text):
            self.index = len(textbox._text)
        if self.index < 0:
            self.index = 0
        # get the verts of character next to caret (chr is the next one so use
        # left edge unless last index then use the right of prev chr)
        # lastChar = [bottLeft, topLeft, **bottRight**, **topRight**]
        ii = self.index
        if textbox.vertices.shape[0] == 0:
            verts = textbox._getStartingVertices() / textbox._pixelScaling
            verts[:,1] = verts[:,1]
            verts[:,0] = verts[:,0] + float(textbox._anchorOffsetX)
        else:
            if self.index >= len(textbox._lineNs):  # caret is after last chr
                chrVerts = textbox.vertices[range((ii-1) * 4, (ii-1) * 4 + 4)]
                x = chrVerts[2, 0]  # x-coord of left edge (of final char)
            else:
                chrVerts = textbox.vertices[range(ii * 4, ii * 4 + 4)]
                x = chrVerts[1, 0]  # x-coord of right edge
            # the y locations are the top and bottom of this line
            y1 = textbox._lineBottoms[self.row] / textbox._pixelScaling
            y2 = textbox._lineTops[self.row] / textbox._pixelScaling
            # char x pos has been corrected for anchor already but lines haven't
            verts = (np.array([[x, y1], [x, y2]])
                     + (0, textbox._anchorOffsetY))

        return convertToPix(vertices=verts, pos=textbox.pos,
                            win=textbox.win, units=textbox.units)
