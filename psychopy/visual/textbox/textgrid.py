#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Mon Jan 07 11:18:51 2013

@author: Sol
"""
import numpy as np
from weakref import proxy
from psychopy import core
from pyglet.gl import (glCallList, glGenLists, glNewList, glDisable, glEnable,
                       glTranslatef, glColor4f, glLineWidth, glBegin,
                       GL_LINES, glEndList, glDeleteLists, GL_COMPILE, glEnd,
                       GL_TEXTURE0, GL_TEXTURE_2D, GL_TEXTURE_ENV,
                       GL_TEXTURE_ENV_MODE, GL_MODULATE, GL_UNSIGNED_INT,
                       glPopMatrix, glBindTexture, glActiveTexture, glTexEnvf,
                       glPushMatrix, glCallLists, glVertex2i)
from . import parsedtext
getTime = core.getTime


class TextGrid:

    def __init__(self, text_box, line_color=None, line_width=1,
                 font_color=(1, 1, 1, 1), shape=None,
                 grid_horz_justification='left',
                 grid_vert_justification='top'):

        self._text_box = proxy(text_box)

        self._font_color = font_color
        if line_color:
            self._line_color = line_color
            self._line_width = line_width
        else:
            self._line_color = None
            self._line_width = None

        cfont = self._text_box._current_glfont
        max_size = cfont.max_tile_width, cfont.max_tile_height
        self._cell_size = (max_size[0],
                           max_size[1] + self._text_box._getPixelTextLineSpacing())
        if self._cell_size[0] == 0:
            print('ERROR WITH CELL SIZE!!!! ', self._text_box.getLabel())

        self._text_dlist = None
        self._gridlines_dlist = None

        self._text_document = None

        # Text Grid line_spacing
        te_size = [0, 0]
        if self._text_box._size:
            te_size = list(self._text_box._getPixelSize())

        if shape:
            self._shape = shape
        else:
            self._shape = (te_size[0] // self._cell_size[0],
                           te_size[1] // self._cell_size[1])

        self._size = (self._cell_size[0] * self._shape[0],
                      self._cell_size[1] * self._shape[1])
        resized = False
        if shape and self._size[0] > te_size[0]:
            te_size[0] = self._size[0]
            resized = True
        if shape and self._size[1] > te_size[1]:
            te_size[1] = self._size[1]
            resized = True
        if resized:
            self._text_box._setSize(te_size)
        # For now, The text grid is centered in the TextBox area.
        dx = (te_size[0] - self._size[0]) // 2
        dy = (te_size[1] - self._size[1]) // 2

        # TextGrid Position is position within the TextBox component.
        self._position = dx, dy

        # TextGrid cell boundaries
        self._col_lines = [int(np.floor(x)) for x in range(
            0, self._size[0] + 1, self._cell_size[0])]
        self._row_lines = [int(np.floor(y)) for y in range(
            0, -self._size[1] - 1, -self._cell_size[1])]

        self._apply_padding = False
        self._pad_top_proportion = 0
        self._pad_left_proportion = 0

        self.setHorzJust(grid_horz_justification)
        self.setVertJust(grid_vert_justification)

    def getSize(self):
        return self._size

    def getCellSize(self):
        return self._cell_size

    def getShape(self):
        return self._shape

    def getPosition(self):
        return self._position

    def getLineColor(self):
        return self._line_color

    def getLineWidth(self):
        return self._line_width

    def getHorzJust(self):
        return self._horz_justification

    def getVertJust(self):
        return self._vert_justification

    def setHorzJust(self, j):
        self._horz_justification = j
        self._pad_left_proportion = 0
        if j == 'center':
            self._pad_left_proportion = 0.5
        elif j == 'right':
            self._pad_left_proportion = 1.0

        self.applyPadding()

    def setVertJust(self, j):
        self._vert_justification = j
        self._pad_top_proportion = 0
        if j == 'center':
            self._pad_top_proportion = 0.5
        elif j == 'bottom':
            self._pad_top_proportion = 1.0

        self.applyPadding()

    def applyPadding(self):
        self._apply_padding = self._pad_left_proportion or (
            self._pad_top_proportion and self.getRowCountWithText() > 1)
        num_cols, num_rows = self._shape
        line_count = self.getRowCountWithText()
        for li in range(line_count):
            cline = self._text_document.getParsedLine(li)
            line_length = cline.getLength()
            if self._apply_padding:
                cline._trans_left = int(
                    (num_cols - line_length + 1) * self._pad_left_proportion)
                cline._trans_top = int(
                    (num_rows - line_count) * self._pad_top_proportion)
            else:
                cline._trans_left = 0
                cline._trans_top = 0

    def getRowCountWithText(self):
        if self._text_document:
            return min(self._shape[1], self._text_document.getParsedLineCount())
        return 0

    def _setText(self, text):
        self._text_document.deleteText(0, self._text_document.getTextLength(),
                                       text)

        self._deleteTextDL()
        self.applyPadding()
        return self._text_document.getDisplayedText()

    def setCurrentFontDisplayLists(self, dlists):
        self._current_font_display_lists = dlists

    def _deleteTextDL(self):
        if self._text_dlist:
            glDeleteLists(self._text_dlist, 1)
            self._text_dlist = 0

    def _deleteGridLinesDL(self):
        if self._gridlines_dlist:
            glDeleteLists(self._gridlines_dlist, 1)
            self._gridlines_dlist = None

    def _createParsedTextDocument(self, f):
        if self._shape:
            self._text_document = parsedtext.ParsedTextDocument(f, self)
            self._deleteTextDL()
            self.applyPadding()
        else:
            raise AttributeError(
                "Could not create _text_document. num_columns needs to be known.")

    def _text_glyphs_gl(self):
        if not self._text_dlist:
            dl_index = glGenLists(1)
            glNewList(dl_index, GL_COMPILE)

            ###
            glActiveTexture(GL_TEXTURE0)
            glEnable(GL_TEXTURE_2D)
            glBindTexture(
                GL_TEXTURE_2D, self._text_box._current_glfont.atlas.texid)
            glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
            glTranslatef(self._position[0], -self._position[1], 0)
            glPushMatrix()

            ###

            getLineInfoByIndex = self._text_document.getLineInfoByIndex
            active_text_style_dlist = self._current_font_display_lists.get
            cell_width, cell_height = self._cell_size
            num_cols, num_rows = self._shape
            line_spacing = self._text_box._getPixelTextLineSpacing()
            line_count = self.getRowCountWithText()

            glColor4f(*self._text_box._toRGBA(self._font_color))

            for r in range(line_count):
                cline, line_length, line_display_list, line_ords = getLineInfoByIndex(
                    r)
                if line_display_list[0] == 0:
                    line_display_list[0:line_length] = [
                        active_text_style_dlist(c) for c in line_ords]

                glTranslatef(cline._trans_left * cell_width, -
                             int(line_spacing/2.0 + cline._trans_top * cell_height), 0)
                glCallLists(line_length, GL_UNSIGNED_INT,
                            line_display_list[0:line_length].ctypes)
                cline._trans_left = 0
                glTranslatef(-line_length * cell_width - cline._trans_left * cell_width, -
                             cell_height + int(line_spacing/2.0 + cline._trans_top * cell_height), 0)

                ###
            glPopMatrix()
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

            glEndList()
            self._text_dlist = dl_index
        glCallList(self._text_dlist)

    def _textgrid_lines_gl(self):
        if self._line_color:
            if not self._gridlines_dlist:
                dl_index = glGenLists(1)
                glNewList(dl_index, GL_COMPILE)

                glLineWidth(self._line_width)
                glColor4f(*self._text_box._toRGBA(self._line_color))
                glBegin(GL_LINES)
                for x in self._col_lines:
                    for y in self._row_lines:
                        if x == 0:
                            glVertex2i(x, y)
                            glVertex2i(int(self._size[0]), y)
                        if y == 0:
                            glVertex2i(x, y)
                            glVertex2i(x, int(-self._size[1]))
                glEnd()
                glColor4f(0.0, 0.0, 0.0, 1.0)
                glEndList()
                self._gridlines_dlist = dl_index
            glCallList(self._gridlines_dlist)

            # self._text_box._te_end_gl()

            # etime=getTime()

    def __del__(self):
        try:
            self._text_document._free()
            del self._text_document
            if self._text_dlist:
                glDeleteLists(self._text_dlist, 1)
                self._text_dlist = 0
            self._current_font_display_lists = None
        except (ModuleNotFoundError, ImportError):
            pass
