#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Thu Mar 21 18:38:35 2013

@author: Sol
"""

import os
import inspect
import numbers
from weakref import proxy
import time
import numpy as np
from psychopy import core, misc, colors, logging
import psychopy.tools.colorspacetools as colortools
import psychopy.tools.arraytools as arraytools
import pyglet
pyglet.options['debug_gl'] = False
from pyglet.gl import (glCallList, glFinish, glGenLists, glNewList, glViewport,
                       glMatrixMode, glLoadIdentity, glDisable, glEnable, glColorMaterial,
                       glBlendFunc, glTranslatef, glColor4f, glRectf, glLineWidth, glBegin,
                       GL_LINES, glVertex2d, glEndList, glClearColor, gluOrtho2D, glOrtho,
                       glDeleteLists, GL_COMPILE, GL_PROJECTION, GL_MODELVIEW, glEnd,
                       GL_DEPTH_TEST, GL_BLEND, GL_COLOR_MATERIAL, GL_FRONT_AND_BACK,
                       GL_AMBIENT_AND_DIFFUSE, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                       glIsEnabled, GL_LINE_SMOOTH, GLint, GLfloat, glGetIntegerv,
                       GL_LINE_WIDTH, glGetFloatv, GL_ALIASED_LINE_WIDTH_RANGE,
                       GL_SMOOTH_LINE_WIDTH_RANGE, GL_SMOOTH_LINE_WIDTH_GRANULARITY,
                       GL_POLYGON_SMOOTH)

from .fontmanager import FontManager
from .textgrid import TextGrid


def getTime():
    return core.getTime()


def is_sequence(arg):
    return (  # not hasattr(arg, "strip") and
        hasattr(arg, "__getitem__") or
        hasattr(arg, "__iter__"))

_system_font_manager = None


def getFontManager(mono_only=True):
    global _system_font_manager
    if _system_font_manager is None:
        _system_font_manager = FontManager(mono_only)
    return _system_font_manager
# check that font manager is working
fm = getFontManager()
font_names = fm.getFontFamilyNames()
if len(font_names) == 0:
    logging.warn("TextBox Font Manager Found No Fonts.")


def getGLInfo():
    gl_info = dict()
    gl_info['GL_LINE_SMOOTH'] = glIsEnabled(GL_LINE_SMOOTH)
    lwidth = GLint()
    glGetIntegerv(GL_LINE_WIDTH, lwidth)
    gl_info['GL_LINE_WIDTH'] = lwidth
    awrange = (GLfloat * 2)(0.0, 0.0)
    glGetFloatv(GL_ALIASED_LINE_WIDTH_RANGE, awrange)
    gl_info['GL_ALIASED_LINE_WIDTH_RANGE'] = awrange[0], awrange[1]
    swrange = (GLfloat * 2)(0.0, 0.0)
    glGetFloatv(GL_SMOOTH_LINE_WIDTH_RANGE, swrange)
    gl_info['GL_SMOOTH_LINE_WIDTH_RANGE'] = swrange[0], swrange[1]
    swg = GLfloat()
    glGetFloatv(GL_SMOOTH_LINE_WIDTH_GRANULARITY, swg)
    gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY'] = swg
    return gl_info


class TextBox:
    """
    Similar to the visual.TextStim component, TextBox can be used to display
    text within a psychopy window. TextBox and TextStim each have different
    strengths and weaknesses. You should select the most appropriate text
    component type based on how it will be used within the experiment.

    NOTE: As of PsychoPy 1.79, TextBox should be considered experimental.
    The two TextBox demo scripts provided have been tested on
    all PsychoPy supported OS's and run without exceptions. However there are
    very likely bugs in the existing TextBox code and the TextBox API will
    be further enhanced and improved (i.e. changed) over the next couple months.

    **TextBox Features**

    * Text character placement is very well defined, useful when the exact
      positioning of each letter needs to be known.

    * The text string that is displayed can be changed ( setText() ) and
      drawn ( win.draw() ) **very** quickly. See the TextBox vs. TextStim
      comparison table for details.

    * Built-in font manager; providing easy access to the font family names
      and styles that are available on the computer being used.

    * TextBox is a composite stimulus type, with the following graphical
      elements, many of which can be changed to control many aspects of how
      the TextBox is displayed.:

         - TextBox Border / Outline
         - TextBox Fill Area
         - Text Grid Cell Lines
         - Text Glyphs

    * When using 'rgb' or 'rgb255' color spaces, colors can be specified as
      a list/tuple of 3 elements (red, green, blue), or with four elements
      (reg, green, blue, alpha) which allows different elements of the
      TextBox to use different opacity settings if desired. For colors that
      include the alpha channel value, it will be applied instead of the
      opacity setting of the TextBox, effectively overriding the stimulus
      defined opacity for that part of the textbox graphics. Colors that
      do not include an alpha channel use the opacity setting as normal.

    * Text Line Spacing can be controlled.

    **Textbox Limitations**

    * Only Monospace Fonts are supported.

    * TextBox component is not a completely **standard** psychopy visual
      stim and has the following functional difference:

          - TextBox attributes are never accessed directly; get* and set*
            methods are always used (this will be changed to use class
            properties in the future).
          - Setting an attribute of a TextBox only supports value replacement,
            ( textbox.setFontColor([1.0,1.0,1.0]) ) and does not support
            specifying operators.

    * Some key word arguments supported by other stimulus types in general,
      or by TextStim itself, are not supported by TextBox. See the TextBox
      class definition for the arguments that are supported.

    * When a new font, style, and size are used it takes about 1 second to
      load and process the font. This is a one time delay for a given
      font name, style, and size. After first being loaded,
      the same font style can be used or re-applied to multiple TextBox
      components with no significant delay.

    * Auto logging or auto drawing is not currently supported.

    TextStim and TextBox Comparison:

    ============================ ============= ===========
    Feature                      TextBox       TextStim
    ============================ ============= ===========
    Change text + redraw time^   1.513 msec    28.537 msec
    No change + redraw time^     0.240 msec    0.931 msec
    Initial Creation time^       0.927 msec    0.194 msec
    MonoSpace Font Support       Yes           Yes
    Non MonoSpace Font Support   No            Yes
    Adjustable Line Spacing      Yes           No
    Precise Text Pos. Info       Yes           No
    Auto logging Support         No            Yes
    Rotation Support             No            Yes
    Word Wrapping Support        Yes           Yes
    ============================ ============= ===========

    ^ Times are in msec.usec format. Tested using the textstim_vs_textbox.py
      demo script provided with the PsychoPy distribution. Results are
      dependent on text length, video card, and OS. Displayed results are
      based on 120 character string with an average of 24 words. Test computer
      used Windows 7 64 bit, PsychoPy 1.79, with a i7 3.4 Ghz CPU, 8 GB RAM,
      and NVIDIA 480 GTX 2GB graphics card.

    Example::

        from psychopy import visual

        win=visual.Window(...)

        # A Textbox stim that will look similar to a TextStim component

        textstimlike=visual.TextBox(
            window=win,
            text="This textbox looks most like a textstim.",
            font_size=18,
            font_color=[-1,-1,1],
            color_space='rgb',
            size=(1.8,.1),
            pos=(0.0,.5),
            units='norm')

        # A Textbox stim that uses more of the supported graphical features
        #
        textboxloaded=visual.TextBox(
            window=win
            text='TextBox showing all supported graphical elements',
            font_size=32,
            font_color=[1,1,1],
            border_color=[-1,-1,1], # draw a blue border around stim
            border_stroke_width=4, # border width of 4 pix.
            background_color=[-1,-1,-1], # fill the stim background
            grid_color=[1,-1,-1,0.5], # draw a red line around each
                                      # possible letter area,
                                      # 50% transparent
            grid_stroke_width=1,  # with a width of 1 pix
            textgrid_shape=[20,2],  # specify area of text box
                                    # by the number of cols x
                                    # number of rows of text to support
                                    # instead of by a screen
                                    # units width x height.
            pos=(0.0,-.5),
            # If the text string length < num rows * num cols in
            # textgrid_shape, how should text be justified?
            #
            grid_horz_justification='center',
            grid_vert_justification='center')

        textstimlike.draw()
        textboxloaded.draw()
        win.flip()

    """
    _textbox_instances = {}
    _gl_info = None

    def __init__(self,
                 window=None,                    # PsychoPy Window instance
                 text='Default Test Text.',      # Initial text to be displayed.
                 font_name=None,                 # Family name of Font
                 bold=False,                     # Bold and italics are used to
                 italic=False,                   # determine style of font
                 font_size=32,                   # Pt size to use for font.
                 font_color=(0, 0, 0, 1),        # Color to draw the text with.
                 dpi=72,                         # DPI used to create font bitmaps
                 line_spacing=0,                 # Amount of extra spacing to add between
                 line_spacing_units='pix',       # lines of text.
                 background_color=None,          # Color to use to fill the entire area
                                                 # on the screen TextBox is using.
                 border_color=None,              # TextBox border color to use.
                 border_stroke_width=1,          # Stroke width of TextBox boarder (in pix)
                 size=None,                      # (width,height) desired for the TextBox
                                                 # stim to use. Specify using the unit
                                                 # type the textBox is using.
                 textgrid_shape=None,            # (cols,rows) of characters to use when
                                                 # creating the textgrid layout.
                                                 # rows*cols = maximum number of chars
                                                 # that can be displayed. If textgrid_shape
                                                 # is not None, then the TextBox size
                                                 # must be at least large enough to hold
                                                 # the number of specified cols and rows.
                                                 # If the size specified is less than
                                                 # what is needed, the size will be increased
                                                 # automatically.      
                 pos=(0.0, 0.0),                 # (x,y) screen position for the TextBox
                                                 # stim. Specify using the unit
                                                 # type the textBox is using.
                 align_horz='center',            # Determines how TextBox x pos is
                                                 # should be interpreted to.
                                                 # 'left', 'center', 'right' are valid options.
                 align_vert='center',            # Determines how TextBox y pos is
                                                 # should be interpreted to.
                                                 # 'left', 'center', 'right' are valid options.
                 units='norm',                   # Coordinate unit type to use for position
                                                 # and size related attributes. Valid
                                                 # options are 'pix', 'cm', 'deg', 'norm'
                                                 # Only pix is currently working though.
                 grid_color=None,                # Color to draw the TextBox text grid
                                                 # lines with.        
                 grid_stroke_width=1,            # Line thickness (in pix) to use when
                                                 # displaying text grid lines.
                 color_space='rgb',              # PsychoPy color space to use for any
                                                 # color attributes of TextBox.
                 opacity=1.0,                    # Opacity (transparency) to use for
                                                 # TextBox graphics, assuming alpha
                                                 # channel was not specified in the color
                                                 # attribute.
                 grid_horz_justification='left', # 'left', 'center', 'right'
                 grid_vert_justification='top',  # 'top', 'bottom', 'center'
                 autoLog=True,                   # Log each time stim is updated.
                 interpolate=False,
                 name=None
                 ):
        self._window = proxy(window)

        self._font_name = font_name
        if self.getWindow().useRetina:
            self._font_size = font_size*2
        else:
            self._font_size = font_size
        self._dpi = dpi
        self._bold = bold
        self._italic = italic

        self._text = text
        self._label = name
        self._line_spacing = line_spacing
        self._line_spacing_units = line_spacing_units
        self._border_color = border_color
        self._background_color = background_color
        self._border_stroke_width = border_stroke_width
        self._grid_horz_justification = grid_horz_justification
        self._grid_vert_justification = grid_vert_justification
        self._align_horz = align_horz
        self._align_vert = align_vert
        self._size = size
        self._position = pos
        self._textgrid_shape = textgrid_shape
        self._interpolate = interpolate

        self._draw_start_dlist = None
        self._draw_end_dlist = None
        self._draw_te_background_dlist = None

        if TextBox._gl_info is None:
            TextBox._gl_info = getGLInfo()

        aliased_wrange = TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']
        antia_wrange = TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
        if grid_stroke_width and grid_color:
            if interpolate:
                if grid_stroke_width < antia_wrange[0]:
                    self._grid_stroke_width = antia_wrange[0]
                if grid_stroke_width > antia_wrange[1]:
                    self._grid_stroke_width = antia_wrange[1]
            else:
                if grid_stroke_width < aliased_wrange[0]:
                    self._grid_stroke_width = aliased_wrange[0]
                if grid_stroke_width > aliased_wrange[1]:
                    self._grid_stroke_width = aliased_wrange[1]
        if border_stroke_width and border_color:
            if interpolate:
                if border_stroke_width < antia_wrange[0]:
                    self._border_stroke_width = antia_wrange[0]
                if border_stroke_width > antia_wrange[1]:
                    self._border_stroke_width = antia_wrange[1]
            else:
                if border_stroke_width < aliased_wrange[0]:
                    self._border_stroke_width = aliased_wrange[0]
                if border_stroke_width > aliased_wrange[1]:
                    self._border_stroke_width = aliased_wrange[1]

        self._units = units
        if self._units is None:
            self._units = self._window.units

        self._opacity = opacity
        if opacity is None:
            self._opacity = 1.0
        elif float(opacity) and float(opacity) >= 0 and float(opacity) <= 1.0:
            self._opacity = float(opacity)
        else:
            raise ValueError(
                "Text Box: opacity must be a number between 0.0 and 1.0, or None (which == 1.0). %s is not valid" % (str(opacity)))

        self._color_space = color_space
        if self._color_space is None:
            self._color_space = self._window.colorSpace

        # TODO: Implement support for autoLog
        self._auto_log = autoLog

        self._current_glfont = None
        self._text_grid = None

        if self._label is None:
            self._label = 'TextBox_%s' % (str(int(time.time())))

        fm = getFontManager()
        if self._font_name is None:
            self._font_name = fm.getFontFamilyStyles()[0][0]
        gl_font = fm.getGLFont(
            self._font_name, self._font_size, self._bold, self._italic, self._dpi)
        self._current_glfont = gl_font

        if size is None and textgrid_shape is None:
            print('WARNING (TextBox) - No `size` or `textgrid_shape` given. Defaulting to displaying all text in a single row.')
            textgrid_shape = (len(text), 1)

        self._text_grid = TextGrid(self, line_color=grid_color,
                                   line_width=grid_stroke_width, font_color=list(
                                       font_color),
                                   shape=textgrid_shape,
                                   grid_horz_justification=grid_horz_justification,
                                   grid_vert_justification=grid_vert_justification)
        self._text_grid.setCurrentFontDisplayLists(
            gl_font.charcode2displaylist)

        self._text = self._text.replace('\r\n', '\n')
        self._text_grid._createParsedTextDocument(self._text)

        self._textbox_instances[self.getLabel()] = proxy(self)

    def getWindow(self):
        """
        Returns the psychopy window that the textBox is associated with.
        """
        return self._window

    def getText(self):
        """
        Return the text to display.
        """
        return self._text

    def setText(self, text_source):
        """
        Set the text to be displayed within the Textbox.

        Note that once a TextBox has been created, the number of character
        rows and columns is static. To change the size of a TextBox,
        a new TextBox stim must be created to replace the current Textbox stim.
        Therefore ensure that the textbox is large enough to display
        the largest length string to be presented in the TextBox. Characters
        that do not fit within the TextBox will not be displayed.

        Color value must be valid for the color space being used by the TextBox.
        """
        if not self._text:
            raise ValueError(
                "TextBox.setText only accepts strings with a length > 0")

        self._text = text_source.replace('\r\n', '\n')
        return self._text_grid._setText(self._text)

    def getDisplayedText(self):
        """
        Return the text that fits within the TextBox and therefore is actually
        seen. This is equal to::

            text_length=len(self.getText())
            cols,rows=self.getTextGridShape()

            displayed_text=self.getText()[0:min(text_length,rows*cols]

        """
        return self._getTextWrappedDoc().getDisplayedText()

    def getTextGridCellPlacement(self):
        """Returns a 3D numpy array containing position information for each
        text grid cell in the TextBox. The array has the shape (`num_cols`,
        `num_rows`, `cell_bounds`), where num_cols is the number of `textgrid`
        columns in the TextBox. `num_rows` is the number of `textgrid` rows in
        the `TextBox`. `cell_bounds` is a 4 element array containing the (x pos,
        y pos, width, height) data for the given cell. Position fields are for
        the top left hand corner of the cell box. Column and Row indices start
        at 0.

        To get the shape of the textgrid in terms of columns and rows, use::

            cell_pos_array=textbox.getTextGridCellPlacement()
            col_row_count=cell_pos_array.shape[:2]

        To access the position, width, and height for textgrid cell at
        column 0 and row 0 (so the top left cell in the textgrid)::

            cell00=cell_pos_array[0,0,:]

        For the cell at col 3, row 1 (so 4th cell on second row)::

            cell41=cell_pos_array[4,1,:]

        """
        col_lines = self._text_grid._col_lines
        row_lines = self._text_grid._row_lines

        cellinfo = np.zeros(
            (len(col_lines[:-1]), len(row_lines[:-1]), 4), dtype=np.float32)

        tb_tl = self._getTopLeftPixPos()
        tg_tl = self._text_grid._position
        starting_x, starting_y = tb_tl[0] + tg_tl[0], tb_tl[1] - tg_tl[1]

        for i, x in enumerate(col_lines[:-1]):
            for j, y in enumerate(row_lines[:-1]):
                px, py = starting_x + x, starting_y + y
                w, h = col_lines[i + 1] - px, -(row_lines[j + 1] - py)
                cellinfo[i, j, 0] = px
                cellinfo[i, j, 1] = py
                cellinfo[i, j, 2] = w
                cellinfo[i, j, 3] = h

        for i, x in enumerate(col_lines[:-1]):
            for j, y in enumerate(row_lines[:-1]):
                x, y = self._pix2units(
                    (float(cellinfo[i, j, 0]), float(cellinfo[i, j, 1])))
                w, h = self._pix2units(
                    (float(cellinfo[i, j, 2]), float(cellinfo[i, j, 3])), False)
                cellinfo[i, j, 0] = x
                cellinfo[i, j, 1] = y
                cellinfo[i, j, 2] = w
                cellinfo[i, j, 3] = h

        return cellinfo

    def getTextGridCellForCharIndex(self, char_index):
        return self._getTextWrappedDoc().getTextGridCellForCharIndex(char_index)

    def getGlyphPositionForTextIndex(self, char_index):
        """For the provided char_index, which is the index of one character in
        the current text being displayed by the TextBox ( getDisplayedText() ),
        return the bounding box position, width, and height for the associated
        glyph drawn to the screen. This factors in the glyphs position within
        the textgrid cell it is being drawn in, so the returned bounding box is
        for the actual glyph itself, not the textgrid cell. For textgrid cell
        placement information, see the getTextGridCellPlacement() method.

        The glyph position for the given text index is returned as a tuple
        (x,y,width,height), where x,y is the top left hand corner of the
        bounding box.

        Special Cases:

            * If the index provided is out of bounds for the currently displayed
              text, None is returned.
            * For u' ' (space) characters, the full textgrid cell bounding box
              is returned.
            * For u'\n' ( new line ) characters,the textgrid cell bounding box
              is returned, but with the box width set to 0.

        """

        if char_index < 0 or char_index >= len(self.getDisplayedText()):
            raise IndexError(
                "The provided index of %d is out of range for the currently displayed text." % (char_index))

        # Get the Glyph info for the char in question:
        gl_font = getFontManager().getGLFont(self._font_name, self._font_size,
                                             self._bold, self._italic, self._dpi)
        glyph_data = gl_font.charcode2glyph.get(ord(self._text[char_index]))
        ox, oy = glyph_data['offset'][
            0], gl_font.max_ascender - glyph_data['offset'][1]
        gw, gh = glyph_data['size']

        # get the col,row for the xhar index provided
        col_row = self._getTextWrappedDoc().getTextGridCellForCharIndex(char_index)
        if col_row is None:
            return None
        cline = self._getTextWrappedDoc().getParsedLine(col_row[1])
        c = col_row[0] + cline._trans_left
        r = col_row[1] + cline._trans_top
        x, y, width, height = self.getTextGridCellPlacement()[c, r, :]
        ox, oy = self._pix2units((ox, oy), False)
        gw, gh = self._pix2units((gw, gh), False)
        return x + ox, y - oy, gw, gh

    def _getTextWrappedDoc(self):
        return self._text_grid._text_document

    def getPosition(self):
        """Return the x,y position of the textbox, in getUnitType() coord space.

        """
        return self._position

    def setPosition(self, pos):
        """
        Set the (x,y) position of the TextBox on the Monitor. The position must
        be given using the unit coord type used by the stim.

        The TextBox position is interpreted differently depending on the
        Horizontal and Vertical Alignment settings of the stim. See
        getHorzAlignment() and getVertAlignment() for more information.


        For example,
        if the TextBox alignment is specified as left, top, then the position
        specifies the top left hand corner of where the stim will be drawn.
        An alignment of bottom,right indicates that the position value will
        define where the bottom right corner of the TextBox will be drawn.
        A horz., vert. alignment of center, center will place the center of
        the TextBox at pos.

        """
        if pos[0] != self._position[0] or pos[1] != self._position[1]:
            self._position = pos[0], pos[1]
            self._deleteBackgroundDL()
            self._deleteStartDL()

    def getUnitType(self):
        """
        Returns which of the psychopy coordinate systems are used by the
        TextBox. Position and size related attributes mush be specified
        relative to the unit type being used. Valid options are:

            * pix
            * norm
            * cm

        """
        return self._units

    def getHorzAlign(self):
        """
        Return what textbox x position should be interpreted as. Valid options
        are 'left', 'center', or 'right' .
        """
        return self._align_horz

    def setHorzAlign(self, v):
        """
        Specify how the horizontal (x) component of the TextBox position
        is to be interpreted. left = x position is the left edge, right =
        x position is the right edge x position, and center = the x position
        is used to center the stim horizontally.

        """
        if v != self._align_horz:
            self._align_horz = v
            self._deleteBackgroundDL()
            self._deleteStartDL()

    def getVertAlign(self):
        """
        Return what textbox y position should be interpreted as. Valid options
        are 'top', 'center', or 'bottom' .

        """
        return self._align_vert

    def setVertAlign(self, v):
        """
        Specify how the vertical (y) component of the TextBox position
        is to be interpreted. top = y position is the top edge, bottom =
        y position is the bottom edge y position, and center = the y position
        is used to center the stim vertically.

        """
        if v != self._align_vert:
            self._align_vert = v
            self._deleteBackgroundDL()
            self._deleteStartDL()

    def getSize(self):
        """
        Return the width,height of the TextBox, using the unit type being
        used by the stimulus.

        """
        return self._size

    def getFontSize(self):
        if self.getWindow().useRetina:
            return self._font_size//2
        return self._font_size
        
    def getFontColor(self):
        """
        Return the color used when drawing text glyphs.
        """
        return self._text_grid._font_color

    def setFontColor(self, c):
        """
        Set the color to use when drawing text glyphs within the TextBox.
        Color value must be valid for the color space being used by the TextBox.
        For 'rgb', 'rgb255', and 'norm' based colors, three or four element lists
        are valid. Three element colors use the TextBox getOpacity() value to
        determine the alpha channel for the color. Four element colors use the
        value of the fourth element to set the alpha value for the color.

        """
        if c != self._text_grid._font_color:
            self._text_grid._font_color = c
            self._text_grid._deleteTextDL()

    def getBorderColor(self):
        """
        A border can be drawn around the perimeter of the TextBox. This method
        sets the color of that border.
        """
        return self._border_color

    def setBorderColor(self, c):
        """
        Set the color to use for the border of the textBox. The TextBox border
        is a rectangular outline drawn around the edges of the TextBox stim.
        Color value must be valid for the color space being used by the TextBox.

        A value of None will disable drawing of the border.
        """
        if c != self._border_color:
            self._border_color = c
            self._deleteBackgroundDL()

    def getBackgroundColor(self):
        """
        Get the color used to fill the rectangular area of the TextBox stim.
        All other graphical elements of the TextBox are drawn on top of the
        background.
        """
        return self._background_color

    def setBackgroundColor(self, c):
        """
        Set the fill color used to fill the rectangular area of the TextBox stim.
        Color value must be valid for the color space being used by the TextBox.

        A value of None will disable drawing of the TextBox background.
        """
        if c != self._background_color:
            self._background_color = c
            self._deleteBackgroundDL()

    def getTextGridLineColor(self):
        """
        Return the color used when drawing the outline of the text grid cells.
        Each letter displayed in a TextBox populates one of the text cells
        defined by the shape of the TextBox text grid.
        Color value must be valid for the color space being used by the TextBox.

        A value of None indicates drawing of the textgrid lines is disabled.
        """
        return self._text_grid._line_color

    def setTextGridLineColor(self, c):
        """
        Set the color used when drawing text grid lines.
        These are lines that can be drawn which mark the bounding box for
        each character within the TextBox text grid.
        Color value must be valid for the color space being used by the TextBox.

        Provide a value of None to disable drawing of textgrid lines.
        """
        if c != self._text_grid._line_color:
            self._text_grid._line_color = c
            self._text_grid._deleteGridLinesDL()

    def getColorSpace(self):
        """Returns the psychopy color space used when specifying colors for
        the TextBox. Supported values are:

            * 'rgb'
            * 'rbg255'
            * 'norm'
            * hex (implicit)
            * html name (implicit)

        See the Color Space section of the PsychoPy docs for details.

        """
        return self._color_space

    def getHorzJust(self):
        """Return how text should laid out horizontally when the number of
        columns of each text grid row is greater than the number needed to
        display the text for that text row.

        """
        return self._text_grid._horz_justification

    def setHorzJust(self, v):
        """
        Specify how text within the TextBox should be aligned horizontally.
        For example, if a text grid has 10 columns, and the text being displayed
        is 6 characters in length, the horizontal justification determines
        if the text should be draw starting at the left of the text columns (left),
        or should be centered on the columns ('center', in this example
        there would be two empty text cells to the left and right of the text.),
        or should be drawn such that the last letter of text is drawn in the
        last column of the text row ('right').
        """
        if v != self._text_grid._horz_justification:
            self._text_grid.setHorzJust(v)
            self._text_grid._deleteTextDL()

    def getVertJust(self):
        """
        Return how text should laid out vertically when the
        number of text grid rows is greater than the number
        needed to display the current text
        """
        return self._text_grid._vert_justification

    def setVertJust(self, v):
        """
        Specify how text within the TextBox should be aligned vertically.
        For example, if a text grid has 3 rows for text, and the text being
        displayed all fits on one row, the vertical justification determines
        if the text should be draw on the top row of the text grid (top),
        or should be centered on the rows ('center', in this example
        there would be one row  above and below the row used to draw the text),
        or should be drawn on the last row of the text grid, ('bottom').
        """
        if v != self._text_grid._vert_justification:
            self._text_grid.setVertJust(v)
            self._text_grid._deleteTextDL()

    def getBorderWidth(self):
        """
        Get the stroke width of the optional TextBox area outline. This is always
        given in pixel units.
        """
        return self._border_stroke_width

    def setBorderWidth(self, c):
        """
        Set the stroke width (in pixels) to use for the border of the TextBox
        stim. Border values must be within the range of stroke widths supported
        by the OpenGL driver used by the graphics. Setting the
        width outside the valid range will result in the stroke width being
        clamped to the nearest end of the valid range.

        Use the TextBox.getValidStrokeWidths() to access the minimum -
        maximum range of valid line widths.
        """
        if c != self._border_stroke_width:
            if self._interpolate:
                lrange = TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
            else:
                lrange = TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']

            if c < lrange[0]:
                c = lrange[0]
            elif c > lrange[1]:
                c = lrange[1]

            self._border_stroke_width = c
            self._deleteBackgroundDL()

    def getTextGridLineWidth(self):
        """
        Return the stroke width (in pixels) of the optional lines drawn around
        the text grid cell areas.
        """
        return self._text_grid._line_width

    def setTextGridLineWidth(self, c):
        """
        Set the stroke width (in pixels) to use for the text grid character
        bounding boxes. Border values must be within the range of stroke
        widths supported by the OpenGL driver used by the computer graphics
        card. Setting the width outside the valid range will result in the
        stroke width being clamped to the nearest end of the valid range.

        Use the TextBox.getGLineRanges() to access a dict containing some
        OpenGL parameters which provide the minimum, maximum, and resolution
        of valid line widths.
        """
        if c != self._text_grid._line_width:
            if self._interpolate:
                lrange = TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
            else:
                lrange = TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']

            if c < lrange[0]:
                c = lrange[0]
            elif c > lrange[1]:
                c = lrange[1]

            self._text_grid._line_width = c
            self._text_grid._deleteGridLinesDL()

    def getValidStrokeWidths(self):
        """
        Returns the stroke width range supported by the graphics card being
        used. If the TextBox is Interpolated, a tuple is returns using
        float values, with the following structure:

        ((min_line_width, max_line_width), line_width_granularity)

        If Interpolation is disabled for the TextBox, the returned tuple elements
        are int values, with the following structure:

        (min_line_width, max_line_width)

        """
        if self._interpolate:
            return (TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE'],
                    TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY'])
        else:
            return self._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']

    def getOpacity(self):
        """
        Get the default TextBox transparency level used for color related
        attributes. 0.0 equals fully transparent, 1.0 equals fully opaque.
        """
        return self._opacity

    def setOpacity(self, o):
        """
        Sets the TextBox transparency level to use for color related
        attributes of the Textbox. 0.0 equals fully transparent, 1.0 equals
        fully opaque.

        If opacity is set to None, it is assumed to have a default value of 1.0.

        When a color is defined with a 4th element in the colors element list,
        then this opacity value is ignored and the alpha value provided in the
        color itself is used for that TextGrid element instead.
        """
        if o != self._opacity and o >= 0.0 and o <= 1.0:
            self._text_grid._deleteTextDL()
            self._deleteBackgroundDL()
            self._text_grid._deleteGridLinesDL()
            self._deleteStartDL()
            self._deleteEndDL()
            self._opacity = o

    def getInterpolated(self):
        """
        Returns whether interpolation is enabled for the TextBox
        when it is drawn. When True, GL_LINE_SMOOTH and GL_POLYGON_SMOOTH
        are enabled within OpenGL; otherwise they are disabled.
        """
        return self._interpolate

    def setInterpolated(self, interpolate):
        """
        Specify whether interpolation should be enabled for the TextBox
        when it is drawn. When interpolate == True, GL_LINE_SMOOTH and
        GL_POLYGON_SMOOTH are enabled within OpenGL. When interpolate is set
        to False, GL_POLYGON_SMOOTH and GL_LINE_SMOOTH are disabled.
        """
        if interpolate != self._interpolate:
            self._deleteStartDL()
            self._interpolate = interpolate

    def getLabel(self):
        """
        Return the label / name assigned to the textbox. This does not impact
        how the stimulus looks when drawn, and instead is used for internal
        purposes only.
        """
        return self._label

    def getName(self):
        """
        Same as the GetLabel method.
        """
        return self._label

    def getAutoLog(self):
        """
        Indicates if changes to textBox attribute values should be logged
        automatically by PsychoPy. *Currently not supported by TextBox.*
        """
        return self._auto_log

    def setAutoLog(self, v):
        """
        Specify if changes to textBox attribute values should be logged
        automatically by PsychoPy. True enables auto logging; False disables it.
        *Currently not supported by TextBox.*
        """
        self._auto_log = v

    def getLineSpacing(self):
        """
        Return the additional spacing being applied between rows of text.
        The value is in units specified by the textbox getUnits() method.
        """
        return self._line_spacing

    def draw(self):
        """
        Draws the TextBox to the back buffer of the graphics card. Then call
        win.flip() to display the changes drawn. If draw() is not called prior
        to a call to win.flip(), the textBox will not be displayed for that
        retrace.
        """
        self._te_start_gl()
        self._te_bakground_dlist()
        self._text_grid._text_glyphs_gl()
        self._text_grid._textgrid_lines_gl()
        self._te_end_gl()

    def _te_start_gl(self):
        if not self._draw_start_dlist:
            dl_index = glGenLists(1)
            glNewList(dl_index, GL_COMPILE)
            glViewport(0, 0, self._window.size[0],
                       self._window.size[1])
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, self._window.size[0], 0,
                    self._window.size[1], -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            self._window.depthTest = False
            glEnable(GL_BLEND)
            glEnable(GL_COLOR_MATERIAL)
            glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            if self._interpolate:
                glEnable(GL_LINE_SMOOTH)
                glEnable(GL_POLYGON_SMOOTH)
            else:
                glDisable(GL_LINE_SMOOTH)
                glDisable(GL_POLYGON_SMOOTH)
            t, l = self._getTopLeftPixPos()
            glTranslatef(t, l, 0)
            glEndList()
            self._draw_start_dlist = dl_index
        glCallList(self._draw_start_dlist)

    def _deleteStartDL(self):
        if self._draw_start_dlist:
            glDeleteLists(self._draw_start_dlist, 1)
            self._draw_start_dlist = None

    def _te_bakground_dlist(self):
        if not self._draw_te_background_dlist and (self._background_color or self._border_color):
            dl_index = glGenLists(1)
            glNewList(dl_index, GL_COMPILE)

            # draw textbox_background and outline
            border_thickness = self._border_stroke_width
            size = self._getPixelSize()
            if self._border_stroke_width is None:
                border_thickness = 0
            if self._background_color:
                bcolor = self._toRGBA(self._background_color)
                glColor4f(*bcolor)
                glRectf(0, 0, size[0], -size[1])
            if self._border_color:
                glLineWidth(border_thickness)
                bcolor = self._toRGBA(self._border_color)
                glColor4f(*bcolor)
                glBegin(GL_LINES)
                x1 = 0
                y1 = 0
                x2, y2 = size
                x2, y2 = x2, y2
                hbthick = border_thickness // 2
                if hbthick < 1:
                    hbthick = 1
                glVertex2d(x1 - border_thickness, y1 + hbthick)
                glVertex2d(x2 + border_thickness, y1 + hbthick)
                glVertex2d(x2 + hbthick, y1)
                glVertex2d(x2 + hbthick, -y2)
                glVertex2d(x2 + border_thickness, -y2 - hbthick)
                glVertex2d(x1 - border_thickness, -y2 - hbthick)
                glVertex2d(x1 - hbthick, -y2)
                glVertex2d(x1 - hbthick, y1)
                glEnd()
            glColor4f(0.0, 0.0, 0.0, 1.0)
            glEndList()
            self._draw_te_background_dlist = dl_index
        if (self._background_color or self._border_color):
            glCallList(self._draw_te_background_dlist)

    def _deleteBackgroundDL(self):
        if self._draw_te_background_dlist:
            glDeleteLists(self._draw_te_background_dlist, 1)
            self._draw_te_background_dlist = None

    def _te_end_gl(self):
        if not self._draw_end_dlist:
            dl_index = glGenLists(1)
            glNewList(dl_index, GL_COMPILE)

            rgb = self._window.rgb
            rgb = TextBox._toRGBA2(
                rgb, 1, self._window.colorSpace, self._window)
            glClearColor(rgb[0], rgb[1], rgb[2], 1.0)
            glViewport(0, 0, int(self._window.size[0]), int(
                self._window.size[1]))
            glMatrixMode(GL_PROJECTION)  # Reset The Projection Matrix
            glLoadIdentity()
            gluOrtho2D(-1, 1, -1, 1)
            glMatrixMode(GL_MODELVIEW)  # Reset The Projection Matrix
            glLoadIdentity()

            glEndList()
            self._draw_end_dlist = dl_index
        glCallList(self._draw_end_dlist)

    def _deleteEndDL(self):
        if self._draw_end_dlist:
            glDeleteLists(self._draw_end_dlist, 1)
            self._draw_end_dlist = None

    @staticmethod
    def _toPix(xy, units, window):
        if isinstance(xy, numbers.Number):
            xy = xy, xy
        elif is_sequence(xy):
            if len(xy) == 1:
                xy = xy[0], xy[0]
            else:
                xy = xy[:2]
        else:
            return ValueError("TextBox: coord variables must be array-like or a single number. Invalid: %s" % (str(xy)))

        if not isinstance(xy[0], numbers.Number) or not isinstance(xy[1], numbers.Number):
            return ValueError("TextBox: coord variables must only contain numbers. Invalid: %s" % (str(xy)))

        if units in ('pix', 'pixs'):
            return xy
        if units in ['deg', 'degs']:
            return misc.deg2pix(xy[0], window.monitor), misc.deg2pix(xy[1], window.monitor)
        if units in ['cm']:
            return misc.cm2pix(xy[0], window.monitor), misc.cm2pix(xy[1], window.monitor)
        if units in ['norm']:
            # -1.0 to 1.0
            if xy[0] <= 1.0 and xy[0] >= -1.0 and xy[1] <= 1.0 and xy[1] >= -1.0:
                return xy[0] * window.size[0] / 2.0, xy[1] * window.size[1] / 2.0

        return ValueError("TextBox: %s, %s could not be converted to pix units" % (str(xy), str(units)))

    def _pix2units(self, xy, is_position=True):
        units = self._units
        window = self._window
        ww, wh = float(window.size[0]), float(window.size[1])

        if isinstance(xy, numbers.Number):
            xy = xy, xy
        elif is_sequence(xy):
            if len(xy) == 1:
                xy = xy[0], xy[0]
            else:
                xy = xy[:2]
        else:
            raise ValueError(
                "TextBox: coord variables must be array-like or a single number. Invalid: %s" % (str(xy)))

        if not isinstance(xy[0], numbers.Number) or not isinstance(xy[1], numbers.Number):
            raise ValueError("TextBox: coord variables must only contain numbers. Invalid: %s, %s, %s" % (
                str(xy), str(type(xy[0])), str(type(xy[1]))))

        x, y = xy
        if is_position:
            # convert to psychopy pix, origin is center of monitor.
            x, y = int(x - ww / 2), int(y - wh / 2)
        if units in ('pix', 'pixs'):
            return x, y
        if units in ['deg', 'degs']:
            return misc.pix2deg(x, window.monitor), misc.deg2pix(y, window.monitor)
        if units in ['cm']:
            return misc.pix2cm(x, window.monitor), misc.cm2pix(y, window.monitor)
        if units in ['norm']:
            return x / ww * 2.0, y / wh * 2.0

        raise ValueError(
            "TextBox: %s, %s could not be converted to pix units" % (str(xy), str(units)))

    def _toRGBA(self, color):
        return self.__class__._toRGBA2(color, self._opacity, self._color_space, self._window)

    @classmethod
    def _toRGBA2(cls, color, opacity=None, color_space=None, window=None):

        if color is None:
            raise ValueError("TextBox: None is not a valid color input")
        #if not colors.isValidColor(color):
        #    raise ValueError(
        #        "TextBox: %s is not a valid color." % (str(color)))

        valid_opacity = opacity >= 0.0 and opacity <= 1.0
        if isinstance(color, str):
            if color[0] == '#' or color[0:2].lower() == '0x':
                rgb255color = colors.hex2rgb255(color)
                if rgb255color and valid_opacity:
                    return rgb255color[0] / 255.0, rgb255color[1] / 255.0, rgb255color[2] / 255.0, opacity
                else:
                    raise ValueError(
                        "TextBox: %s is not a valid hex color." % (str(color)))

            named_color = colors.colors.get(color.lower())
            if named_color and valid_opacity:
                return (named_color[0] + 1.0) / 2.0, (named_color[1] + 1.0) / 2.0, (named_color[2] + 1.0) / 2.0, opacity
            raise ValueError(
                "TextBox: String color value could not be translated: %s" % (str(color)))

        if isinstance(color, (float, int, int)) or (is_sequence(color) and len(color) == 3):
            color = arraytools.val2array(color, length=3)
            if color_space == 'dkl' and valid_opacity:
                dkl_rgb = None
                if window:
                    dkl_rgb = window.dkl_rgb
                rgb = colortools.dkl2rgb(color, dkl_rgb)
                return (rgb[0] + 1.0) / 2.0, (rgb[1] + 1.0) / 2.0, (rgb[2] + 1.0) / 2.0, opacity
            if color_space == 'lms' and valid_opacity:
                lms_rgb = None
                if window:
                    lms_rgb = window.lms_rgb
                rgb = colortools.lms2rgb(color, lms_rgb)
                return (rgb[0] + 1.0) / 2.0, (rgb[1] + 1.0) / 2.0, (rgb[2] + 1.0) / 2.0, opacity
            if color_space == 'hsv' and valid_opacity:
                rgb = colortools.hsv2rgb(color)
                return (rgb[0] + 1.0) / 2.0, (rgb[1] + 1.0) / 2.0, (rgb[2] + 1.0) / 2.0, opacity
            if color_space == 'rgb255' and valid_opacity:
                rgb = color
                if [cc for cc in color if cc < 0 or cc > 255]:
                    raise ValueError(
                        'TextBox: rgb255 colors must contain elements between 0 and 255. Value: ' + str(rgb))
                return rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, opacity
            if color_space == 'rgb' and valid_opacity:
                rgb = color
                if [cc for cc in color if cc < -1.0 or cc > 1.0]:
                    raise ValueError(
                        'TextBox: rgb colors must contain elements between -1.0 and 1.0. Value: ' + str(rgb))
                return (rgb[0] + 1.0) / 2.0, (rgb[1] + 1.0) / 2.0, (rgb[2] + 1.0) / 2.0, opacity

        if is_sequence(color) and len(color) == 4:
            if color_space == 'rgb255':
                if [cc for cc in color if cc < 0 or cc > 255]:
                    raise ValueError(
                        'TextBox: rgb255 colors must contain elements between 0 and 255. Value: ' + str(color))
                return color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, color[3] / 255.0
            if color_space == 'rgb':
                if [cc for cc in color if cc < -1.0 or cc > 1.0]:
                    raise ValueError(
                        'TextBox: rgb colors must contain elements between -1.0 and 1.0. Value: ' + str(color))
                return (color[0] + 1.0) / 2.0, (color[1] + 1.0) / 2.0, (color[2] + 1.0) / 2.0, (color[3] + 1.0) / 2.0

        raise ValueError("TextBox: color: %s, opacity: %s, is not a valid color for color space %s." % (
            str(color), str(opacity), color_space))

    def _reset(self):
        self._text_grid.reset()

    def _getPixelSize(self):
        if self._units == 'norm':
            r = self._toPix(
                (self._size[0] - 1.0, self._size[1] - 1.0), self._units, self._window)
            return int(r[0] + self._window.size[0] / 2), int(r[1] + self._window.size[1] / 2)
        return [int(x) for x in self._toPix(self._size, self._units, self._window)]

    def _setSize(self, pix_sz):
        units = self._units
        if units in ('pix', 'pixs'):
            self._size = list(pix_sz)
        if units in ['deg', 'degs']:
            self._size = misc.pix2deg(pix_sz[0], self._window.monitor), misc.pix2deg(
                pix_sz[1], self._window.monitor)
        if units in ['cm']:
            self._size = misc.pix2cm(pix_sz[0], self._window.monitor), misc.pix2cm(
                pix_sz[1], self._window.monitor)
        if units in ['norm']:
            pw, ph = pix_sz
            dw, dh = self._window.size
            nw = (pw / float(dw)) * 2.0
            nh = (ph / float(dh)) * 2.0
            self._size = nw, nh

    def _getPixelPosition(self):
        ppos = self._toPix(self._position, self._units, self._window)
        return int(ppos[0]), int(ppos[1])

    def _getPixelTextLineSpacing(self):
        if self._line_spacing:
            max_size = self._current_glfont.max_tile_width, self._current_glfont.max_tile_height
            line_spacing_units = self._line_spacing_units
            line_spacing_height = self._line_spacing

            if line_spacing_units == 'ratio':
                # run though _toPix to validate line_spacing value type only
                r = self._toPix(line_spacing_height, 'pix', self._window)[0]
                return int(max_size[1] * r)

            return self._toPix(line_spacing_height, line_spacing_units, self._window)
        return 0

    def _getTopLeftPixPos(self):
        # Create a window position based on the window size, alignment types,
        #   TextBox size, etc...
        win_w, win_h = self._window.size
        te_w, te_h = self._getPixelSize()
        te_x, te_y = self._getPixelPosition()
        # convert te_x,te_y from psychopy pix coord to gl pix coord
        te_x, te_y = te_x + win_w // 2, te_y + win_h // 2
        # convert from alignment to top left
        horz_align, vert_align = self._align_horz, self._align_vert
        if horz_align.lower() == u'center':
            te_x = te_x - te_w // 2
        elif horz_align.lower() == u'right':
            te_x = te_x - te_w
        if vert_align.lower() == u'center':
            te_y = te_y + te_h // 2
        if vert_align.lower() == u'bottom':
            te_y = te_y + te_h
        return te_x, te_y

    def __del__(self):
        if hasattr(self, '_textbox_instance') and self.getName() in self._textbox_instance:
            del self._textbox_instances[self.getName()]
        del self._current_glfont
        del self._text_grid
