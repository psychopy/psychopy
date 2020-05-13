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
                 editable=False,
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
        self._lines = None  # np.array the line numbers for each char
        self._colors = None

        self.flipHoriz = flipHoriz
        self.flipVert = flipVert
        self.text = text  # setting this triggers a _layout() call so do last
        # box border and fill
        self.box = Rect(win, pos=pos,
                        width=self.size[0], height=self.size[1], units=units,
                        lineColor=borderColor, fillColor=fillColor)
        self.borderColor = borderColor
        self.fillColor = fillColor

        # caret
        self.editable = editable
        self.caretIndex = None
        if editable:
            self.win.addEditable(self)

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

    @property
    def caretIndex(self):
        if 'caretIndex' not in self.__dict__ or self.__dict__['caretIndex'] is None:
            self.__dict__['caretIndex'] = len(self.text)
        return self.__dict__['caretIndex']

    @caretIndex.setter
    def caretIndex(self, newIndex):
        self.__dict__['caretIndex'] = newIndex

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

        self._pixelScaling = self._pixLetterHeight / self.letterHeight
        self._lineHeight = font.height * self.lineSpacing
        lineMax = (self.size[0] - self.padding) * self._pixelScaling
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

                index = i * 4
                theseVertices = [[xTopL, yTop], [xBotL, yBot],
                                 [xBotR, yBot], [xTopR, yTop]]
                texcoords = [[u0, v0], [u0, v1],
                             [u1, v1], [u1, v0]]

                vertices[i * 4:i * 4 + 4] = theseVertices
                self._texcoords[i * 4:i * 4 + 4] = texcoords
                self._colors[i * 4:i * 4 + 4] = color
                self._lineNs[i] = lineN
                current[0] = current[0] + glyph.advance[0] + fakeBold / 2
                current[1] = current[1] + glyph.advance[1]

            # are we wrapping the line?
            if charcode == "\n":
                lineWPix = current[0]
                current[0] = 0
                current[1] -= self._lineHeight
                lineN += 1
                self._lineLenChars.append(charsThisLine)
                lineWidth = lineWPix / self._pixelScaling + self.padding * 2
                self._lineWidths.append(lineWidth)
                charsThisLine = 0
            elif charcode in wordBreaks:
                wordLen = 0
                charsThisLine += 1
            elif printable:
                wordLen += 1
                charsThisLine += 1

            # end line with auto-wrap
            if current[0] >= lineMax and wordLen > 0:
                # move the current word to next line
                lineBreakPt = vertices[(i - wordLen + 1) * 4, 0]
                wordWidth = current[0] - lineBreakPt
                # shift all chars of the word left by wordStartX
                vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 0] -= lineBreakPt
                vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 1] -= self._lineHeight
                # update line values
                self._lineNs[i - wordLen + 1: i + 1] += 1
                self._lineLenChars.append(charsThisLine - wordLen)
                self._lineWidths.append(
                        lineBreakPt / self._pixelScaling + self.padding * 2)
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

        # convert the vertices to stimulus units
        self.vertices = vertices / self._pixelScaling

        # thisW = current[0] - glyph.advance[0] + glyph.size[0] * alphaCorrection
        # calculate final self.size and tightBox
        if self.size[0] == -1:
            self.size[0] = max(self._lineWidths)
        if self.size[1] == -1:
            self.size[1] = ((lineN + 1) * self._lineHeight / self._pixelScaling
                            + self.padding * 2)

        # to start with the anchor is bottom left of *first line*
        if self._anchorY == 'top':
            self._anchorOffsetY = (-font.ascender / self._pixelScaling
                                   - self.padding)
        elif self._anchorY == 'center':
            self._anchorOffsetY = (
                    self.size[1] / 2
                    - (font.height / 2 - font.descender) / self._pixelScaling
                    - self.padding)
        elif self._anchorY == 'bottom':
            self._anchorOffsetY = (
                        self.size[1] / 2 - font.descender / self._pixelScaling)
        else:
            raise ValueError('Unexpected error for _anchorY')

        if self._anchorX == 'right':
            self._anchorOffsetX = - (self.size[0] - self.padding) / 1.0
        elif self._anchorX == 'center':
            self._anchorOffsetX = - (self.size[0] - self.padding) / 2.0
        elif self._anchorX == 'left':
            self._anchorOffsetX = 0
        else:
            raise ValueError('Unexpected error for _anchorX')
        self.vertices += (self._anchorOffsetX, self._anchorOffsetY)

        # if we had to add more glyphs to make possible then 
        if self.glFont._dirty:
            self.glFont.upload()
            self.glFont._dirty = False
        self._needVertexUpdate = True

    def draw(self):
        """Draw the text to the back buffer"""
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

        if self.editable:  # draw caret line
            caretVerts = self._caretVertices
            gl.glLineWidth(2)
            gl.glColor4f(0, 0, 0, 0.9)
            gl.glBegin(gl.GL_LINES)
            gl.glVertex2f(caretVerts[0, 0], caretVerts[0, 1])
            gl.glVertex2f(caretVerts[1, 0], caretVerts[1, 1])
            gl.glEnd()

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

        self.box.size = self.size
        print('updatedBoxSize')
        self._needVertexUpdate = False

    @property
    def _caretVertices(self):
        # check we have a caret index
        if self.caretIndex is None or self.caretIndex > len(self._lineNs):
            self.caretIndex = len(self.text)
        # get the verts of character next to caret (chr is the next one so use
        # left edge unless last index then use the right of prev chr)
        # lastChar = [bottLeft, topLeft, **bottRight**, **topRight**]
        if self.caretIndex >= len(self.text):  # caret is after last chr
            chrVerts = self._index2vertices(self.caretIndex-1)
            lineN = self._lineNs[self.caretIndex-1]
            x = chrVerts[2, 0]  # x-coord of right edge (of final char)
        else:
            chrVerts = self._index2vertices(self.caretIndex)
            lineN = self._lineNs[self.caretIndex]
            x = chrVerts[1, 0]  # x-coord of left edge
        # the y locations are the top and bottom of this line
        y1 = self._lineBottoms[lineN] / self._pixelScaling
        y2 = self._lineTops[lineN] / self._pixelScaling

        # char x pos has been corrected for anchor location already but lines
        # haven't
        verts = (np.array([[x, y1], [x, y2]])
                 + (0, self._anchorOffsetY))
        return convertToPix(vertices=verts, pos=self.pos,
                            win=self.win, units=self.units)

    def _index2vertices(self, ii):
        if ii > len(self.text):
            ii = len(self.text)
        return self.vertices[range(ii*4, ii*4+4)]

    def _index2lineChar(self, ii):
        if ii >= len(self._lineNs):
            ii = len(self._lineNs)-1
        line = self._lineNs[ii]
        chars = ii - sum(self._lineLenChars[:line])
        return line, chars

    def _lineChar2index(self, line, chars):
        # if this isn't the last line then check if there are more chars on this
        # line that the requested number
        if line<len(self._lineLenChars):
            chars = min(chars, self._lineLenChars[line])
        ii = sum(self._lineLenChars[:line]) + chars
        return ii

    def _caretCheckBounds(self):
        # then check if out of bounds
        self.caretIndex = max(self.caretIndex, 0)
        self.caretIndex = min(self.caretIndex, len(self.text))

    def _caretMoveChars(self, chars=0):
        self.caretIndex = self.caretIndex + chars

    def _caretMoveLines(self, lines=0):
        line, chr = self._index2lineChar(self.caretIndex)
        line += lines
        line = max(0, line)
        line = min(line, len(self._lineLenChars))
        self.caretIndex = self._lineChar2index(line, chr)

    def _caretMoveLineStart(self):
        line, chr = self._index2lineChar(self.caretIndex)
        self.caretIndex = self._lineChar2index(line, 0)

    def _caretMoveLineEnd(self):
        line, chr = self._index2lineChar(self.caretIndex)
        self.caretIndex = self._lineChar2index(line, self._lineLenChars[line]-1)

    # def _vertices2Index(self, XY):
    #
    # def _lineChar2vertices(self, line, chrN):

    def _onText(self, chr):
        """Called by the window when characters are received"""
        if chr == '\t':
            self.win.nextEditable()
            return
        if chr == '\r':  # make it newline not Carriage Return
            chr = '\n'
        txt = self.text
        self.text = txt[:self.caretIndex] + chr + txt[self.caretIndex:]
        self.caretIndex += 1

    def _onCursorKeys(self, key):
        """Called by the window when cursor/del/backspace... are received"""
        if key == 'MOTION_UP':
            self._caretMoveLines(-1)
        elif key == 'MOTION_DOWN':
            self._caretMoveLines(+1)
        elif key == 'MOTION_RIGHT':
            self._caretMoveChars(+1)
        elif key == 'MOTION_LEFT':
            self._caretMoveChars(-1)
        elif key == 'MOTION_BACKSPACE':
            self.text = txt[:self.caretIndex-1] + txt[self.caretIndex:]
            self.caretIndex -= 1
        elif key == 'MOTION_DELETE':
            self.text = txt[:self.caretIndex] + txt[self.caretIndex+1:]
        elif key == 'MOTION_NEXT_WORD':
            pass
        elif key == 'MOTION_PREVIOUS_WORD':
            pass
        elif key == 'MOTION_BEGINNING_OF_LINE':
            self._caretMoveLineStart()
        elif key == 'MOTION_END_OF_LINE':
            self._caretMoveLineEnd()
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
