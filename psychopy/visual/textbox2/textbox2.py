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
from arabic_reshaper import ArabicReshaper
from pyglet import gl
from bidi import algorithm as bidi

from ..basevisual import BaseVisualStim, ColorMixin, ContainerMixin, WindowMixin
from psychopy.tools.attributetools import attributeSetter, setAttribute
from psychopy.tools.arraytools import val2array
from psychopy.tools.monitorunittools import convertToPix
from .fontmanager import FontManager, GLFont
from .. import shaders
from ..rect import Rect
from ... import core, alerts, layout

from psychopy.tools.linebreak import get_breakable_points, break_units

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

wordBreaks = " -\n"  # what about ",."?


END_OF_THIS_LINE = 983349843

# Setting debug to True will make the sub-elements on TextBox2 to be outlined in red, making it easier to determine their position
debug = False

# If text is ". " we don't want to start next line with single space?


class TextBox2(BaseVisualStim, ContainerMixin, ColorMixin):
    def __init__(self, win, text,
                 font="Open Sans",
                 pos=(0, 0), units=None, letterHeight=None,
                 size=None,
                 color=(1.0, 1.0, 1.0), colorSpace='rgb',
                 fillColor=None, fillColorSpace=None,
                 borderWidth=2, borderColor=None, borderColorSpace=None,
                 contrast=1,
                 opacity=None,
                 bold=False,
                 italic=False,
                 lineSpacing=None,
                 padding=None,  # gap between box and text
                 anchor='center',
                 alignment='left',
                 flipHoriz=False,
                 flipVert=False,
                 languageStyle="LTR",
                 editable=False,
                 lineBreaking='default',
                 name='',
                 autoLog=None,
                 autoDraw=False,
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
        lineBreaking: Specifying 'default', text will be broken at a set of
            characters defined in the module. Specifying 'uax14', text will be
            broken in accordance with UAX#14 (Unicode Line Breaking Algorithm).
        name
        autoLog
        """

        BaseVisualStim.__init__(self, win, units=units, name=name)
        self.win = win
        self.colorSpace = colorSpace
        ColorMixin.foreColor.fset(self, color)  # Have to call the superclass directly on init as text has not been set
        self.onTextCallback = onTextCallback

        # Box around the whole textbox - drawn
        self.box = Rect(
            win,
            units=self.units, pos=(0, 0), size=(0, 0),  # set later by self.size and self.pos
            colorSpace=colorSpace, lineColor=borderColor, fillColor=fillColor,
            lineWidth=borderWidth,
            opacity=self.opacity,
            autoLog=False,
        )
        # Box around just the content area, excluding padding - not drawn
        self.contentBox = Rect(
            win,
            units=self.units, pos=(0, 0), size=(0, 0),  # set later by self.size and self.pos
            colorSpace=colorSpace, lineColor='red', fillColor=None,
            lineWidth=1, opacity=int(debug),
            autoLog=False
        )
        # Box around current content, wrapped tight - not drawn
        self.boundingBox = Rect(
            win,
            units='pix', pos=(0, 0), size=(0, 0),  # set later by self.size and self.pos
            colorSpace=colorSpace, lineColor='blue', fillColor=None,
            lineWidth=1, opacity=int(debug),
            autoLog=False
        )
        # Sizing params
        self.letterHeight = letterHeight
        self.padding = padding
        self.size = size
        self.pos = pos

        # self._pixLetterHeight helps get font size right but not final layout
        if 'deg' in self.units:  # treat deg, degFlat or degFlatPos the same
            scaleUnits = 'deg'  # scale units are just for font resolution
        else:
            scaleUnits = self.units
        self._pixelScaling = self.letterHeightPix / self.letterHeight
        self.bold = bold
        self.italic = italic
        self.glFont = None  # will be set by the self.font attribute setter
        self.font = font
        if lineSpacing is not None:
            self.lineSpacing = lineSpacing
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
        self.borderWidth = borderWidth
        self.borderColor = borderColor
        self.fillColor = fillColor
        self.contrast = contrast
        self.opacity = opacity

        # set linebraking option
        if lineBreaking not in ('default', 'uax14'):
            raise ValueError("Unknown lineBreaking option ({}) is"
                "specified.".format(lineBreaking))
        self._lineBreaking = lineBreaking
        # then layout the text (setting text triggers _layout())
        self.languageStyle = languageStyle
        self._text = ''
        self.text = self.placeholder = text if text is not None else ""

        # Initialise arabic reshaper
        arabic_config = {'delete_harakat': False,  # if present, retain any diacritics
                         'shift_harakat_position': False}  # shift by 1 to be compatible with the bidi algorithm
        self.arabicReshaper = ArabicReshaper(configuration=arabic_config)

        # caret
        self.editable = editable
        self.caret = Caret(self, color=self.color, width=2)

        self.autoDraw = autoDraw
        self.autoLog = autoLog

    def __copy__(self):
        return TextBox2(
            self.win, self.text, self.font,
            pos=self.pos, units=self.units, letterHeight=self.letterHeight,
            size=self.size,
            color=self.color, colorSpace=self.colorSpace,
            fillColor=self.fillColor,
            borderWidth=self.borderWidth, borderColor=self.borderColor,
            contrast=self.contrast,
            opacity=self.opacity,
            bold=self.bold,
            italic=self.italic,
            lineSpacing=self.lineSpacing,
            padding=self.padding,  # gap between box and text
            anchor=self.anchor,
            alignment=self.alignment,
            flipHoriz=self.flipHoriz,
            flipVert=self.flipVert,
            editable=self.editable,
            lineBreaking=self._lineBreaking,
            name=self.name,
            autoLog=self.autoLog,
            onTextCallback=self.onTextCallback
        )

    @property
    def editable(self):
        """Determines whether or not the TextBox2 instance can receive typed text"""
        return self._editable
    
    @editable.setter
    def editable(self, editable):
        self._editable = editable
        if editable is False:
            if self.win:
                self.win.removeEditable(self)
        if editable is True:
            if self.win:
                self.win.addEditable(self)

    @property
    def palette(self):
        """Describes the current visual properties of the TextBox in a dict"""
        self._palette = {
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
        return self._palette[self.hasFocus]

    @property
    def pallette(self):  # deprecated, use palette instead
        self._palette = {
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
        return self._palette[self.hasFocus]

    @palette.setter
    def pallette(self, value):
        self._palette = {
            False: value,
            True: value
        }

    @pallette.setter
    def pallette(self, value):  # deprecated, use palette instead
        self._palette = {
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
                    size=self.letterHeightPix,
                    bold=self.bold, italic=self.italic)

    @property
    def units(self):
        return WindowMixin.units.fget(self)

    @units.setter
    def units(self, value):
        WindowMixin.units.fset(self, value)
        if hasattr(self, "box"):
            self.box.units = value
        if hasattr(self, "contentBox"):
            self.contentBox.units = value
        if hasattr(self, "caret"):
            self.caret.units = value

    @property
    def size(self):
        """The (requested) size of the TextBox (w,h) in whatever units the stimulus is using

        This determines the outer extent of the area.

        If the width is set to None then the text will continue extending and not wrap.
        If the height is set to None then the text will continue to grow downwards as needed.
        """
        return WindowMixin.size.fget(self)

    @size.setter
    def size(self, value):
        WindowMixin.size.fset(self, value)
        if hasattr(self, "box"):
            self.box.size = self._size
        if hasattr(self, "contentBox"):
            self.contentBox.size = self._size - self._padding * 2
        # Refresh pos
        self.pos = self.pos

    @property
    def pos(self):
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

            myTextbox._pos.pix
        """
        return WindowMixin.pos.fget(self)

    @pos.setter
    def pos(self, value):
        WindowMixin.pos.fset(self, value)
        if hasattr(self, "box"):
            self.box.size = self._pos
        if hasattr(self, "contentBox"):
            # Content box should be anchored center relative to box, but its pos needs to be relative to box's vertices, not its pos
            self.contentBox.pos = self.pos + self.size * self.box._vertices.anchorAdjust
            self.contentBox._needVertexUpdate = True

        # Set caret pos again so it recalculates its vertices
        if hasattr(self, "caret"):
            self.caret.index = self.caret.index

        if hasattr(self, "_text"):
            self._layout()
        self._needVertexUpdate = True

    @property
    def vertices(self):
        return WindowMixin.vertices.fget(self)

    @vertices.setter
    def vertices(self, value):
        # If None, use defaut
        if value is None:
            value = [
                [0.5, -0.5],
                [-0.5, -0.5],
                [-0.5, 0.5],
                [0.5, 0.5],
            ]
        # Create Vertices object
        self._vertices = layout.Vertices(value, obj=self.contentBox, flip=self.flip)

    @property
    def padding(self):
        if hasattr(self, "_padding"):
            return getattr(self._padding, self.units)

    @padding.setter
    def padding(self, value):
        # Substitute None for a default value
        if value is None:
            value = self.letterHeight / 2
        # Create a Size object to handle padding
        self._padding = layout.Size(value, self.units, self.win)
        # Update size of bounding box
        if hasattr(self, "contentBox") and hasattr(self, "_size"):
            self.contentBox.size = self._size - self._padding * 2

    @property
    def letterHeight(self):
        if hasattr(self, "_letterHeight"):
            return getattr(self._letterHeight, self.units)[1]

    @letterHeight.setter
    def letterHeight(self, value):
        if isinstance(value, layout.Vector):
            # If given a Vector, use it directly
            self._letterHeight = value
        elif isinstance(value, (int, float)):
            # If given an integer, convert it to a 2D Vector with width 0
            self._letterHeight = layout.Size([0, value], units=self.units, win=self.win)
        elif value is None:
            # If None, use default (20px)
            self._letterHeight = layout.Size([0, 20], units='pix', win=self.win)
        elif isinstance(value, (list, tuple, np.ndarray)):
            # If given an array, convert it to a Vector
            self._letterHeight = layout.Size(value, units=self.units, win=self.win)

    @property
    def letterHeightPix(self):
        """
        Convenience function to get self._letterHeight.pix and be guaranteed a return that is a single integer
        """
        return self._letterHeight.pix[1]

    @property
    def lineSpacing(self):
        if hasattr(self.glFont, "lineSpacing"):
            return self.glFont.lineSpacing

    @lineSpacing.setter
    def lineSpacing(self, value):
        if hasattr(self.glFont, "lineSpacing"):
            self.glFont.lineSpacing = value
        self._needVertexUpdate = True

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

    @property
    def languageStyle(self):
        """
        How is text laid out? Left to right (LTR), right to left (RTL) or using Arabic layout rules?
        """
        if hasattr(self, "_languageStyle"):
            return self._languageStyle

    @languageStyle.setter
    def languageStyle(self, value):
        self._languageStyle = value
        # If layout is anything other than LTR, mark that we need to use bidi to lay it out
        self._needsBidi = value != "LTR"
        self._needsArabic = value.lower() == "arabic"

    @property
    def anchor(self):
        return self.box.anchor

    @anchor.setter
    def anchor(self, anchor):
        # Box should use this anchor
        self.box.anchor = anchor
        # Set pos again to update sub-element vertices
        self.pos = self.pos

    @property
    def alignment(self):
        if hasattr(self, "_alignX") and hasattr(self, "_alignY"):
            return (self._alignX, self._alignY)
        else:
            return ("top", "left")

    @alignment.setter
    def alignment(self, alignment):
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
        if hasattr(self, "_text"):
            # If text has been set, layout
            self._layout()

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
        # Convert to string
        text = str(text)
        # Substitute HTML tags
        text = text.replace('<i>', codes['ITAL_START'])
        text = text.replace('</i>', codes['ITAL_END'])
        text = text.replace('<b>', codes['BOLD_START'])
        text = text.replace('</b>', codes['BOLD_END'])      
        visible_text = ''.join([c for c in text if c not in codes.values()])
        self._styles = [0,]*len(visible_text)
        self._text = visible_text
        if self._needsArabic and hasattr(self, "arabicReshaper"):
            self._text = self.arabicReshaper.reshape(self._text)
        if self._needsBidi:
            self._text = bidi.get_display(self._text)
        
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
        """Allows a character to be added programmatically at the current caret"""
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
        """Deletes 1 character to the left of the caret"""
        if self.caret.index > 0:
            txt = self._text
            ci = self.caret.index
            txt = txt[:ci-1] + txt[ci:]
            self._styles = self._styles[:ci-1]+self._styles[ci:]
            self.caret.index -= 1
            self._text = txt
            self._layout()

    def deleteCaretRight(self):
        """Deletes 1 character to the right of the caret"""
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
        _lineBottoms = []
        self._lineLenChars = []  #
        _lineWidths = []  # width in stim units of each line

        lineMax = self.contentBox._size.pix[0]
        current = [0, 0 - font.ascender]
        fakeItalic = 0.0
        fakeBold = 0.0
        # for some reason glyphs too wide when using alpha channel only
        if font.atlas.format == 'alpha':
            alphaCorrection = 1 / 3.0
        else:
            alphaCorrection = 1

        if self._lineBreaking == 'default':

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
                elif self._styles[i] == BOLD:
                    fakeBold = 0.3 * font.size

                # handle newline
                if charcode == '\n':
                    printable = False

                # handle printable characters
                if printable:
                    glyph = font[charcode]
                    if showWhiteSpace and charcode == " ":
                        glyph = font[u"·"]
                    elif charcode == " ":
                        # glyph size of space is smaller than actual size, so use size of dot instead
                        glyph.size = font[u"·"].size
                    # Get top and bottom coords
                    yTop = current[1] + glyph.offset[1]
                    yBot = yTop - glyph.size[1]
                    # Get x mid point
                    xMid = current[0] + glyph.offset[0] + glyph.size[0] * alphaCorrection / 2 + fakeBold / 2
                    # Get left and right corners from midpoint
                    xBotL = xMid - glyph.size[0] * alphaCorrection / 2 - fakeItalic - fakeBold / 2
                    xBotR = xMid + glyph.size[0] * alphaCorrection / 2 - fakeItalic + fakeBold / 2
                    xTopL = xMid - glyph.size[0] * alphaCorrection / 2 - fakeBold / 2
                    xTopR = xMid + glyph.size[0] * alphaCorrection / 2 + fakeBold / 2

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
                    current[1] -= font.height
                    lineN += 1
                    charsThisLine += 1
                    self._lineLenChars.append(charsThisLine)
                    _lineWidths.append(lineWPix)
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
                if current[0] >= lineMax and wordLen > 0 and wordsThisLine > 1:
                    # move the current word to next line
                    lineBreakPt = vertices[(i - wordLen + 1) * 4, 0]
                    wordWidth = current[0] - lineBreakPt
                    # shift all chars of the word left by wordStartX
                    vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 0] -= lineBreakPt
                    vertices[(i - wordLen + 1) * 4: (i + 1) * 4, 1] -= font.height
                    # update line values
                    self._lineNs[i - wordLen + 1: i + 1] += 1
                    self._lineLenChars.append(charsThisLine - wordLen)
                    _lineWidths.append(lineBreakPt)
                    lineN += 1
                    # and set current to correct location
                    current[0] = wordWidth
                    current[1] -= font.height
                    charsThisLine = wordLen
                    wordsThisLine = 1

                # have we stored the top/bottom of this line yet
                if lineN + 1 > len(_lineBottoms):
                    _lineBottoms.append(current[1])

            # add length of this (unfinished) line
            _lineWidths.append(current[0])
            self._lineLenChars.append(charsThisLine)

        elif self._lineBreaking == 'uax14':

            # get a list of line-breakable points according to UAX#14
            breakable_points = list(get_breakable_points(self._text))
            text_seg = list(break_units(self._text, breakable_points))
            styles_seg = list(break_units(self._styles, breakable_points))

            lineN = 0
            charwidth_list = []
            segwidth_list = []
            y_advance_list = []
            vertices_list = []
            texcoords_list = []

            # calculate width of each segments
            for this_seg in range(len(text_seg)):

                thisSegWidth = 0 # width of this segment

                for i, charcode in enumerate(text_seg[this_seg]):
                    printable = True  # unless we decide otherwise
                    # handle formatting codes
                    if styles_seg[this_seg][i] == NONE:
                        fakeItalic = 0.0
                        fakeBold = 0.0
                    elif styles_seg[this_seg][i] == ITALIC:
                        fakeItalic = 0.1 * font.size
                    elif styles_seg[this_seg][i] == ITALIC:
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
                        xBotL = glyph.offset[0] - fakeItalic - fakeBold / 2
                        xTopL = glyph.offset[0] - fakeBold / 2
                        yTop = glyph.offset[1]
                        xBotR = xBotL + glyph.size[0] * alphaCorrection + fakeBold
                        xTopR = xTopL + glyph.size[0] * alphaCorrection + fakeBold
                        yBot = yTop - glyph.size[1]
                        u0 = glyph.texcoords[0]
                        v0 = glyph.texcoords[1]
                        u1 = glyph.texcoords[2]
                        v1 = glyph.texcoords[3]
                    else:
                        glyph = font[u"·"]
                        x = glyph.offset[0]
                        yTop = glyph.offset[1]
                        yBot = yTop - glyph.size[1]
                        xBotL = x
                        xTopL = x
                        xBotR = x
                        xTopR = x
                        u0 = glyph.texcoords[0]
                        v0 = glyph.texcoords[1]
                        u1 = glyph.texcoords[2]
                        v1 = glyph.texcoords[3]

                    # calculate width and update segment width
                    w = glyph.advance[0] + fakeBold / 2
                    thisSegWidth += w

                    # keep vertices, texcoords, width and y_advance of this character
                    vertices_list.append([[xTopL, yTop], [xBotL, yBot],
                                          [xBotR, yBot], [xTopR, yTop]])
                    texcoords_list.append([[u0, v0], [u0, v1],
                                           [u1, v1], [u1, v0]])
                    charwidth_list.append(w)
                    y_advance_list.append(glyph.advance[1])

                # append width of this segment to the list
                segwidth_list.append(thisSegWidth)

            # concatenate segments to build line
            lines = []
            while text_seg:
                line_width = 0
                for i in range(len(text_seg)):
                    # if this segment is \n, break line here.
                    if text_seg[i][-1] == '\n':
                        i+=1 # increment index to include \n to current line
                        break
                    # concatenate next segment
                    line_width += segwidth_list[i]
                    # break if line_width is greater than lineMax
                    if lineMax < line_width:
                        break
                else:
                    # if for sentence finished without break, all segments 
                    # should be concatenated.
                    i = len(text_seg)
                p = max(1, i)
                # concatenate segments and remove from segment list
                lines.append("".join(text_seg[:p]))
                del text_seg[:p], segwidth_list[:p] #, avoid[:p]

            # build lines
            i = 0 # index of the current character
            if lines:
                for line in lines:
                    for c in line:
                        theseVertices = vertices_list[i]
                        #update vertices
                        for j in range(4):
                            theseVertices[j][0] += current[0]
                            theseVertices[j][1] += current[1]
                        texcoords = texcoords_list[i]

                        vertices[i * 4:i * 4 + 4] = theseVertices
                        self._texcoords[i * 4:i * 4 + 4] = texcoords
                        self._colors[i*4 : i*4+4, :4] = rgb
                        self._lineNs[i] = lineN

                        current[0] = current[0] + charwidth_list[i]
                        current[1] = current[1] + y_advance_list[i]
                        
                        # have we stored the top/bottom of this line yet
                        if lineN + 1 > len(_lineBottoms):
                            _lineBottoms.append(current[1])

                        # next chacactor
                        i += 1

                    # prepare for next line
                    current[0] = 0
                    current[1] -= font.height
                    
                    lineBreakPt = vertices[(i-1) * 4, 0]
                    self._lineLenChars.append(len(line))
                    _lineWidths.append(lineBreakPt)

                    # need not increase lineN when the last line doesn't end with '\n'
                    if lineN < len(lines)-1 or line[-1] == '\n' :
                        lineN += 1
        else:
            raise ValueError("Unknown lineBreaking option ({}) is"
                "specified.".format(self._lineBreaking))

        # Apply vertical alignment
        if self.alignment[1] in ("bottom", "center"):
            # Get bottom of last line (or starting line, if there are none)
            if len(_lineBottoms):
                lastLine = min(_lineBottoms)
            else:
                lastLine = current[1]
            if self.alignment[1] == "bottom":
                # Work out how much we need to adjust by for the bottom base line to sit at the bottom of the content box
                adjustY = lastLine + self.contentBox._size.pix[1]
            if self.alignment[1] == "center":
                # Work out how much we need to adjust by for the line midpoint (mean of ascender and descender) to sit in the middle of the content box
                adjustY = (lastLine + font.descender + self.contentBox._size.pix[1]) / 2
            # Adjust vertices and line bottoms
            vertices[:, 1] = vertices[:, 1] - adjustY
            _lineBottoms -= adjustY

        # Apply horizontal alignment
        if self.alignment[0] in ("right", "center"):
            if self.alignment[0] == "right":
                # Calculate adjust value per line
                lineAdjustX = self.contentBox._size.pix[0] - np.array(_lineWidths)
            if self.alignment[0] == "center":
                # Calculate adjust value per line
                lineAdjustX = (self.contentBox._size.pix[0] - np.array(_lineWidths)) / 2
            # Get adjust value per vertex
            adjustX = lineAdjustX[np.repeat(self._lineNs, 4)]
            # Adjust vertices
            vertices[:, 0] = vertices[:, 0] + adjustX

        # Convert the vertices to be relative to content box and set
        self.vertices = vertices / self.contentBox._size.pix + (-0.5, 0.5)
        if len(_lineBottoms):
            if self.flipVert:
                self._lineBottoms = min(self.contentBox._vertices.pix[:, 1]) - np.array(_lineBottoms)
            else:
                self._lineBottoms = max(self.contentBox._vertices.pix[:, 1]) + np.array(_lineBottoms)
            self._lineWidths = min(self.contentBox._vertices.pix[:, 0]) + np.array(_lineWidths)
        else:
            self._lineBottoms = np.array(_lineBottoms)
            self._lineWidths = np.array(_lineWidths)

        # if we had to add more glyphs to make possible then 
        if self.glFont._dirty:
            self.glFont.upload()
            self.glFont._dirty = False
        self._needVertexUpdate = True

    def draw(self):
        """Draw the text to the back buffer"""
        # Border width
        self.box.setLineWidth(self.palette['lineWidth']) # Use 1 as base if border width is none
        #self.borderWidth = self.box.lineWidth
        # Border colour
        self.box.setLineColor(self.palette['lineColor'], colorSpace='rgb')
        #self.borderColor = self.box.lineColor
        # Background
        self.box.setFillColor(self.palette['fillColor'], colorSpace='rgb')
        #self.fillColor = self.box.fillColor

        # Inherit win
        self.box.win = self.win
        self.contentBox.win = self.win
        self.boundingBox.win = self.win

        if self._needVertexUpdate:
            #print("Updating vertices...")
            self._updateVertices()
        if self.fillColor is not None or self.borderColor is not None:
            self.box.draw()

        # Draw sub-elements if in debug mode
        if debug:
            self.contentBox.draw()
            self.boundingBox.draw()

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
        """Resets the TextBox2 to hold **whatever it was given on initialisation**"""
        # Reset contents
        self.text = self.startText

    def clear(self):
        """Resets the TextBox2 to a blank string"""
        # Clear contents
        self.text = ""


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

        self.__dict__['verticesPix'] = self._vertices.pix

        # tight bounding box
        if hasattr(self._vertices, self.units) and self.vertices.shape[0] >= 1:
            verts = self._vertices.pix
            L = verts[:, 0].min()
            R = verts[:, 0].max()
            B = verts[:, 1].min()
            T = verts[:, 1].max()
            tightW = R-L
            Xmid = (R+L)/2
            tightH = T-B
            Ymid = (T+B)/2
            # for the tight box anchor offset is included in vertex calcs
            self.boundingBox.size = tightW, tightH
            self.boundingBox.pos = self.pos + (Xmid, Ymid)
        else:
            self.boundingBox.size = 0, 0
            self.boundingBox.pos = self.pos
        # box (larger than bounding box) needs anchor offest adding
        self.box.pos = self.pos
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
        """Returns the current text in the box, including formatting tokens."""
        return self.text

    @property
    def visibleText(self):
        """Returns the current visible text in the box"""
        return self._text

    def getVisibleText(self):
        """Returns the current visible text in the box"""
        return self.visibleText

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

    # -------- legacy attributes --------

    @property
    def startText(self):
        """
        In v2022.1.4, `.startText` was replaced by `.placeholder` for consistency with PsychoJS. The two attributes
        are fully interchangeable.
        """
        return self.placeholder

    @startText.setter
    def startText(self, value):
        self.placeholder = value


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
        # Get vertices of caret based on characters and index
        ii = self.index
        if textbox.vertices.shape[0] == 0:
            # If there are no chars, put caret at start position (determined by alignment)
            if textbox.alignment[1] == "bottom":
                bottom = min(textbox.contentBox._vertices.pix[:, 1])
            elif textbox.alignment[1] == "center":
                bottom = (min(textbox.contentBox._vertices.pix[:, 1]) + max(textbox.contentBox._vertices.pix[:, 1]) - textbox.glFont.ascender - textbox.glFont.descender) / 2
            else:
                bottom = max(textbox.contentBox._vertices.pix[:, 1]) - textbox.glFont.ascender
            if textbox.alignment[0] == "right":
                x = max(textbox.contentBox._vertices.pix[:, 0])
            elif textbox.alignment[0] == "center":
                x = (min(textbox.contentBox._vertices.pix[:, 0]) + max(textbox.contentBox._vertices.pix[:, 0])) / 2
            else:
                x = min(textbox.contentBox._vertices.pix[:, 0])
        else:
            # Otherwise, get caret position from character vertices
            if self.index >= len(textbox._lineNs):
                # If the caret is after the last char, position it to the right
                chrVerts = textbox._vertices.pix[range((ii-1) * 4, (ii-1) * 4 + 4)]
                x = chrVerts[2, 0]  # x-coord of left edge (of final char)
            else:
                # Otherwise, position it to the left
                chrVerts = textbox._vertices.pix[range(ii * 4, ii * 4 + 4)]
                x = chrVerts[1, 0]  # x-coord of right edge
            # Get top of this line
            bottom = textbox._lineBottoms[self.row]
        # Top will always be line bottom + font height
        if self.textbox.flipVert:
            top = bottom - self.textbox.glFont.size
        else:
            top = bottom + self.textbox.glFont.size
        return np.array([
            [x, bottom],
            [x, top]
        ])
