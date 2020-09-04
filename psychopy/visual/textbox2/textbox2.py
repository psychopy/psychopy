#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
#  FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#
# -----------------------------------------------------------------------------

"""
TextBox2 provides a combination of features from TextStim and TextBox and then
some more added:

    - fast like TextBox (TextStim is pyglet-based and slow)
    - provides for fonts that aren't monospaced (unlike TextBox)
    - adds additional options to use <b>bold<\b> and <i>italic<\i> tags in text

"""
import numpy as np
import OpenGL.GL as gl

from ..basevisual import BaseVisualStim, ColorMixin, ContainerMixin
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import convertToPix
from .fontmanager import FontManager, GLFont
from .. import shaders
from ..rect import Rect
from ... import core

allFonts = FontManager()

# compile global shader programs later (when we're certain a GL context exists)
rgbShader = None
alphaShader = None
showWhiteSpace = False

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
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 contrast=1,
                 opacity=1.0,
                 bold=False,
                 italic=False,
                 lineSpacing=1.0,
                 padding=None,  # gap between box and text
                 anchor='center',
                 alignment='left',
                 fillColor=None,
                 borderWidth=2,
                 borderColor=None,
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
        self.color = color
        self.contrast = contrast
        self.opacity = opacity
        self.onTextCallback = onTextCallback

        if units=='norm':
            raise NotImplemented("TextBox2 doesn't support 'norm' units at the "
                                 "moment. Use 'height' units instead")
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
        self.pallette = { # If no focus
                'lineColor': borderColor,
                'lineRGB': self.box.lineRGB,
                'lineWidth': borderWidth,
                'fillColor': fillColor,
                'fillRGB': self.box.fillRGB
        }
        # then layout the text (setting text triggers _layout())
        self.text = text if text is not None else ""

        # caret
        self.editable = editable
        self.caret = Caret(self, color=self.color, width=5)
        self._hasFocus = False
        if editable:  # may yet gain focus if the first editable obj
            self.win.addEditable(self)

        self.autoLog = autoLog

    @property
    def pallette(self):
        return self._pallette[self.hasFocus]

    @pallette.setter
    def pallette(self, value):
        pal = {}
        # Double border width
        if value['lineWidth']:
            pal['lineWidth'] = max(value['lineWidth'], 2) * 2
        else:
            pal['lineWidth'] = 5 * 2
        # Darken border
        if value['lineColor']:
            pal['lineRGB'] = pal['lineColor'] = [max(c - 0.05, 0.05) for c in value['lineRGB']]
        else:
            # Use window colour as base if border colour is none
            pal['lineRGB'] = pal['lineColor'] = [max(c - 0.05, 0.05) for c in self.win.color]
        # Lighten background
        if value['fillColor']:
            pal['fillRGB'] = pal['fillColor'] = [min(c + 0.05, 0.95) for c in value['fillRGB']]
        else:
            # Use window colour as base if fill colour is none
            pal['fillRGB'] = pal['fillColor'] = [min(c + 0.05, 0.95) for c in self.win.color]
        self._pallette = {
            False: value,
            True: pal
        }

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

    @attributeSetter
    def text(self, text):
        self.__dict__['text'] = text
        self._layout()

    def _layout(self):
        """Layout the text, calculating the vertex locations
        """
        def getLineWidthFromPix(pixVal):
            return pixVal / self._pixelScaling + self.padding * 2

        text = self.text
        text = text.replace('<i>', codes['ITAL_START'])
        text = text.replace('</i>', codes['ITAL_END'])
        text = text.replace('<b>', codes['BOLD_START'])
        text = text.replace('</b>', codes['BOLD_END'])
        rgb = self._getDesiredRGB(self.rgb, self.colorSpace, self.contrast)
        font = self.glFont

        # the vertices are initially pix (natural for freetype)
        # then we convert them to the requested units for self._vertices
        # then they are converted back during rendering using standard BaseStim
        vertices = np.zeros((len(text) * 4, 2), dtype=np.float32)
        self._charIndices = np.zeros((len(text)), dtype=int)
        self._colors = np.zeros((len(text) * 4, 4), dtype=np.float32)
        self._texcoords = np.zeros((len(text) * 4, 2), dtype=np.float32)
        self._glIndices = np.zeros((len(text) * 4), dtype=int)

        # the following are used internally for layout
        self._lineNs = np.zeros(len(text), dtype=int)
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

        for i, charcode in enumerate(text):

            printable = True  # unless we decide otherwise
            # handle formatting codes
            if charcode in codes.values():
                if charcode == codes['ITAL_START']:
                    fakeItalic = 0.1 * font.size
                elif charcode == codes['ITAL_END']:
                    fakeItalic = 0.0
                elif charcode == codes['BOLD_START']:
                    fakeBold = 0.3 * font.size
                elif charcode == codes['BOLD_END']:
                    current[0] -= fakeBold / 2  # we expected bigger current
                    fakeBold = 0.0
                continue
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

            index = i * 4
            theseVertices = [[xTopL, yTop], [xBotL, yBot],
                             [xBotR, yBot], [xTopR, yTop]]
            texcoords = [[u0, v0], [u0, v1],
                         [u1, v1], [u1, v0]]

            vertices[i * 4:i * 4 + 4] = theseVertices
            self._texcoords[i * 4:i * 4 + 4] = texcoords
            self._colors[i*4 : i*4+4, :3] = rgb
            self._colors[i*4 : i*4+4, 3] = self.opacity
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
        glyph = self.glFont["A"]  # just to get height
        yTop = 0
        yBot = yTop - glyph.size[1]
        x = 0
        theseVertices = np.array([[x, yTop], [x, yBot], [x, yBot], [x, yTop]])
        return theseVertices

    def draw(self):
        """Draw the text to the back buffer"""
        # Border width
        self.box.setLineWidth(self.pallette['lineWidth']) # Use 1 as base if border width is none
        #self.borderWidth = self.box.lineWidth
        # Border colour
        self.box.setLineColor(self.pallette['lineRGB'], colorSpace='rgb')
        #self.borderColor = self.box.lineColor
        # Background
        self.box.setFillColor(self.pallette['fillRGB'], colorSpace='rgb')
        #self.fillColor = self.box.fillColor

        if self._needVertexUpdate:
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

        gl.glVertexPointer(2, gl.GL_FLOAT, 0, self.verticesPix)
        gl.glColorPointer(4, gl.GL_FLOAT, 0, self._colors)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, self._texcoords)

        self.shader.bind()
        self.shader.setInt('texture', 0)
        self.shader.setFloat('pixel', [1.0 / 512, 1.0 / 512])
        nVerts = len(self.text)*4
        gl.glDrawElements(gl.GL_QUADS, nVerts,
                          gl.GL_UNSIGNED_INT, list(range(nVerts)))
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
        txt = self.text
        self.text = txt[:self.caret.index] + chr + txt[self.caret.index:]
        self.caret.index += 1
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
            self.text = self.text[:self.caret.index-1] + self.text[self.caret.index:]
            self.caret.index -= 1
        elif key == 'MOTION_DELETE':
            self.text = self.text[:self.caret.index] + self.text[self.caret.index+1:]
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
        return self._hasFocus

    @hasFocus.setter
    def hasFocus(self, state):
        # Store focus
        self._hasFocus = state
        # Redraw text box
        self.draw()

    def getText(self):
        """Returns the current text in the box"""
        return self.text

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
        self.index = len(textbox.text)  # start off at the end
        self.autoLog = False
        self.width = width
        self.units = textbox.units
        self.colorSpace = colorSpace
        self.color = color

    @attributeSetter
    def color(self, color):
        self.setColor(color)
        self._desiredRGB = [0.89, -0.35, -0.28]
        # if self.colorSpace not in ['rgb', 'dkl', 'lms', 'hsv']:
        #     self._desiredRGB = [c / 127.5 - 1 for c in self.rgb]
        # else:
        #     self._desiredRGB = self.rgb

    def draw(self):
        if not self.visible:
            return
        if core.getTime() % 1 > 0.6:  # Flash every other second
            return
        gl.glLineWidth(self.width)
        rgb = self._desiredRGB
        gl.glColor4f(
            rgb[0], rgb[1], rgb[2], self.textbox.opacity
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
        if self.index is None or self.index > len(textbox.text):
            self.index = len(textbox.text)
        if self.index < 0:
            self.index = 0
        # get the verts of character next to caret (chr is the next one so use
        # left edge unless last index then use the right of prev chr)
        # lastChar = [bottLeft, topLeft, **bottRight**, **topRight**]
        ii = self.index
        if textbox.vertices.shape[0] == 0:
            verts = self.textbox._getStartingVertices()
            verts[:,1] = verts[:,1] / float(textbox._pixelScaling)
            verts[:,1] = verts[:,1] + float(textbox._anchorOffsetY)
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
