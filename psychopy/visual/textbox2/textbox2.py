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
from psychopy.tools.attributetools import attributeSetter
from psychopy.tools.monitorunittools import convertToPix
from .fontmanager import FontManager, GLFont
from .. import shaders
from ..rect import Rect

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


# If text is ". " we don't want to start next line with single space?

class TextBox2(BaseVisualStim, ContainerMixin):
    def __init__(self, win, text, font,
                 pos=(0, 0), units='pix', letterHeight=None,
                 size=None,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 bold=False,
                 italic=False,
                 lineSpacing=1.0,
                 padding=None,  # gap between box and text
                 anchor='center',
                 fillColor=None,
                 borderColor=None,
                 flipHoriz=False,
                 flipVert=False,
                 name='', autoLog=None):

        BaseVisualStim.__init__(self, win, units=units, name=name,
                                autoLog=autoLog)
        self.win = win
        # first set params needed to create font (letter sizes etc)
        if letterHeight is None:
            self.letterHeight = defaultLetterHeight[units]
        else:
            self.letterHeight = letterHeight
        # self._pixLetterHeight helps get font size right but not final layout
        if 'deg' in units:  # treat deg, degFlat or degFlatPos the same
            scaleUnits = 'deg'  # scale units are just for font resolution
        else:
            scaleUnits = units
        self._pixLetterHeight = convertToPix(
                self.letterHeight, pos=0, units=scaleUnits, win=self.win)
        if size is None:
            size = (defaultBoxWidth[units], -1)
        self._requestedSize = size  # (-1 in either dim means not constrained)
        self.size = size  # but this will be updated later to actual size
        self.bold = bold
        self.italic = italic
        self.lineSpacing = lineSpacing
        if padding is None:
            padding = defaultLetterHeight[units] / 2.0
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
        # params about positioning
        self.anchor = anchor  # 'center', 'top_left', 'bottom-center'...
        self._needVertexUpdate = False  # this will be set True during layout
        # standard stimulus params
        self.pos = pos
        self.color = color
        self.colorSpace = colorSpace
        self.opacity = opacity
        # used at render time
        self._indices = None
        self._colors = None

        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        self.text = text  # setting this triggers a _layout() call so do last
        self.box = Rect(win, pos=pos,
                        width=self.size[0], height=self.size[1], units=units,
                        lineColor=borderColor, fillColor=fillColor)
        self.borderColor = borderColor
        self.fillColor = fillColor

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
    def text(self, text):
        self.__dict__['text'] = text
        self._layout()

    @property
    def boundingBox(self):
        """(read only) attribute representing the bounding box of the text
        (w,h). This differs from `width` in that the width represents the
        width of the margins, which might differ from the width of the text
        within them."""
        return self.__dict__['boundingBox']

    def _layout(self):
        """Layout the text, calculating the vertex locations
        """

        text = self.text
        text = text.replace('<i>', codes['ITAL_START'])
        text = text.replace('</i>', codes['ITAL_END'])
        text = text.replace('<b>', codes['BOLD_START'])
        text = text.replace('</b>', codes['BOLD_END'])
        color = self.color
        font = self.glFont

        # the vertices are initially pix (natural for freetype)
        # then we convert them to the requested units for self._vertices
        # then they are converted back during rendering using standard BaseStim
        vertices = np.zeros((len(text) * 4, 2), dtype=np.float32)
        self._indices = np.zeros((len(text) * 6), dtype=np.uint)
        self._colors = np.zeros((len(text) * 4, 4), dtype=np.float32)
        self._texcoords = np.zeros((len(text) * 4, 2), dtype=np.float32)

        # the following are used internally for layout
        self._lineNs = np.zeros(len(text), dtype=np.int)
        self._lineLenChars = []  #
        self._lineWidths = []  # width in stim units of each line
        self._charIndices = []  # NB self._indices is index of each vertex

        pixelScaling = self._pixLetterHeight / self.letterHeight
        lineHeight = font.height * self.lineSpacing
        lineMax = (self.size[0] - self.padding) * pixelScaling

        cursor = [0, 0]
        fakeItalic = 0.0
        fakeBold = 0.0
        # for some reason glyphs too wide when using alpha channel only
        if font.atlas.format == 'alpha':
            alphaCorrection = 1 / 3.0
        else:
            alphaCorrection = 1

        wordLen = 0
        charsThisLine = 0
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
                    cursor[0] -= fakeBold / 2  # we expected bigger cursor
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
                xBotL = cursor[0] + glyph.offset[0] - fakeItalic - fakeBold / 2
                xTopL = cursor[0] + glyph.offset[0] - fakeBold / 2
                yTop = cursor[1] + glyph.offset[1]
                xBotR = xBotL + glyph.size[0] * alphaCorrection + fakeBold
                xTopR = xTopL + glyph.size[0] * alphaCorrection + fakeBold
                yBot = yTop - glyph.size[1]
                u0 = glyph.texcoords[0]
                v0 = glyph.texcoords[1]
                u1 = glyph.texcoords[2]
                v1 = glyph.texcoords[3]

                index = i * 4
                indices = [index, index + 1, index + 2,
                           index, index + 2, index + 3]
                theseVertices = [[xTopL, yTop], [xBotL, yBot],
                                 [xBotR, yBot], [xTopR, yTop]]
                texcoords = [[u0, v0], [u0, v1],
                             [u1, v1], [u1, v0]]

                vertices[i * 4:i * 4 + 4] = theseVertices
                self._indices[i * 6:i * 6 + 6] = indices
                self._texcoords[i * 4:i * 4 + 4] = texcoords
                self._colors[i * 4:i * 4 + 4] = color
                self._lineNs[i] = lineN
                cursor[0] = cursor[0] + glyph.advance[0] + fakeBold / 2
                cursor[1] = cursor[1] + glyph.advance[1]

            # are we wrapping the line?
            if charcode == "\n":
                lineWPix = cursor[0]
                cursor[0] = 0
                cursor[1] -= lineHeight
                charsThisLine = 0
                lineN += 1
                self._lineLenChars.append(charsThisLine)
                lineWidth = lineWPix / pixelScaling + self.padding * 2
                self._lineWidths.append(lineWidth)
            elif charcode in wordBreaks:
                wordLen = 0
            elif printable:
                wordLen += 1
                charsThisLine += 1

            # end line with auto-wrap
            if cursor[0] >= lineMax and wordLen > 0:
                # move the current word to next line
                lineBreakPt = vertices[(i - wordLen + 1) * 4, 0]
                wordWidth = cursor[0] - lineBreakPt
                # shift all chars of the word left by wordStartX
                vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 0] -= lineBreakPt
                vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 1] -= lineHeight
                # update line values
                self._lineNs[i - wordLen + 1: i + 1] += 1
                self._lineLenChars.append(charsThisLine - wordLen)
                self._lineWidths.append(
                        lineBreakPt / pixelScaling + self.padding * 2)
                lineN += 1
                # and set cursor to correct location
                cursor[0] = wordWidth
                cursor[1] -= lineHeight

        # convert the vertices to stimulus units
        self.vertices = vertices / pixelScaling

        # thisW = cursor[0] - glyph.advance[0] + glyph.size[0] * alphaCorrection
        # calculate final self.size and tightBox
        if self.size[0] == -1:
            self.size[0] = max(self._lineWidths)
        if self.size[1] == -1:
            self.size[1] = ((lineN + 1) * lineHeight / pixelScaling
                            + self.padding * 2)

        # to start with the anchor is bottom left of *first line*
        if self._anchorY == 'top':
            dy = -font.ascender / pixelScaling - self.padding
        elif self._anchorY == 'center':
            dy = self.size[1] / 2 - (font.height / 2 - font.descender) / (
                pixelScaling) - self.padding
        elif self._anchorY == 'bottom':
            dy = self.size[1] / 2 - font.descender / pixelScaling
        else:
            raise ValueError('Unexpected error for _anchorY')

        if self._anchorX == 'right':
            dx = 0 - self.padding
        elif self._anchorX == 'center':
            dx = - self.size[0] / 4.0
        elif self._anchorX == 'left':
            dx = - self.size[0] / 2.0 + self.padding
        else:
            raise ValueError('Unexpected error for _anchorX')
        self.vertices += (dx, dy)

        # if we had to add more glyphs to make possible then 
        if self.glFont._dirty:
            self.glFont.upload()
            self.glFont._dirty = False
        self._needVertexUpdate = True

    def draw(self):
        if self._needVertexUpdate:
            self._updateVertices()
        if self.fillColor is not None or self.borderColor is not None:
            self.box.draw()
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

        gl.glVertexPointer(2, gl.GL_FLOAT, 0,
                           self.verticesPix)
        gl.glColorPointer(4, gl.GL_FLOAT, 0,
                          self._colors)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 0,
                             self._texcoords)

        self.shader.bind()
        self.shader.setInt('texture', 0)
        self.shader.setFloat('pixel', [1.0 / 512, 1.0 / 512])
        gl.glDrawElements(gl.GL_TRIANGLES, len(self._indices),
                          gl.GL_UNSIGNED_INT, self._indices)
        self.shader.unbind()
        gl.glDisableVertexAttribArray(1);
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_COLOR_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisable(gl.GL_TEXTURE_2D)

        gl.glPopMatrix()

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

        if hasattr(self, 'vertices'):
            verts = self.vertices
        else:
            verts = self._verticesBase

        verts = convertToPix(vertices=verts, pos=self.pos,
                             win=self.win, units=self.units)
        self.__dict__['verticesPix'] = verts

        if hasattr(self, 'border'):
            # border = self.border
            border = np.dot(self.size * self.border *
                            flip, self._rotationMatrix)
            border = convertToPix(
                    vertices=border, pos=self.pos, win=self.win,
                    units=self.units)
            self.__dict__['_borderPix'] = border

        self._needVertexUpdate = False
