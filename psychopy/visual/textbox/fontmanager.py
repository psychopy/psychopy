#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on Sun Nov 10 12:18:45 2013

@author: Sol
"""

from __future__ import absolute_import, division, print_function

from builtins import chr
from builtins import object
import os
import math
import numpy as np
import unicodedata as ud
from matplotlib import font_manager
from psychopy.core import getTime

from freetype import Face, FT_LOAD_RENDER, FT_LOAD_FORCE_AUTOHINT, FT_Exception
                                                     
from .textureatlas import TextureAtlas

from pyglet.gl import (glGenLists, glNewList, GL_COMPILE, GL_QUADS,
                       glBegin, glTexCoord2f, glVertex2f, glEnd, glDeleteLists,
                       glEndList, glTranslatef, glDeleteTextures)

log = math.log
ceil = math.ceil


def nearestPow2(n):
    return pow(2, int(log(n, 2) + 0.5))


def nextPow2(n):
    return int(pow(2, ceil(log(n, 2))))


class FontManager(object):
    """FontManager provides a simple API for finding and loading font files
    (.ttf) via the FreeType lib

    The FontManager finds supported font files on the computer and
    initially creates a dictionary containing the information about
    available fonts. This can be used to quickly determine what font family
    names are available on the computer and what styles (bold, italic) are
    supported for each family.

    This font information can then be used to create the resources necessary
    to display text using a given font family, style, size, color, and dpi.

    The FontManager is currently used by the psychopy.visual.TextBox stim
    type. A user script can access the FontManager via:

    font_mngr=visual.textbox.getFontManager()

    A user script never creates an instance of the FontManager class and
    should always access it using visual.textbox.getFontManager().

    Once a font of a given size and dpi has been created; it is cached by the
    FontManager and can be used by all TextBox instances created within the
    experiment.

    """
    freetype_import_error = None
    font_atlas_dict = {}
    font_family_styles = []
    _available_font_info = {}
    font_store = None

    def __init__(self, monospace_only=True):
        # if FontManager.freetype_import_error:
        #    raise Exception('Appears the freetype library could not load.
        #       Error: %s'%(str(FontManager.freetype_import_error)))

        self.load_monospace_only = monospace_only
        self.updateFontInfo(monospace_only)

    def getFontFamilyNames(self):
        """Returns a list of the available font family names.
        """
        return list(self._available_font_info.keys())

    def getFontStylesForFamily(self, family_name):
        """For the given family_name, a list of style names supported is
        returned.
        """
        style_dict = self._available_font_info.get(family_name)
        if style_dict:
            return list(style_dict.keys())

    def getFontFamilyStyles(self):
        """Returns a list where each element of the list is a itself a
        two element list of [font_family_name,[font_style_names_list]]
        """
        return self.font_family_styles

    def getFontsMatching(self, font_family_name, bold=False, italic=False,
                         font_style=None):
        """
        Returns the list of FontInfo instances that match the provided
        font_family_name and style information. If no matching fonts are
        found, None is returned.
        """
        style_dict = self._available_font_info.get(font_family_name)
        if style_dict is None:
            return None
        if font_style and font_style in style_dict:
            return style_dict[font_style]
        for style, fonts in style_dict.items():
            b, i = self.booleansFromStyleName(style)
            if b == bold and i == italic:
                return fonts
        return None

    def addFontFile(self, font_path, monospace_only=True):
        """
        Add a Font File to the FontManger font search space. The
        font_path must be a valid path including the font file name.
        Relative paths can be used, with the current working directory being
        the origin.

        If monospace_only is True, the font file will only be added if it is a
        monospace font (as only monospace fonts are currently supported by
        TextBox).

        Adding a Font to the FontManager is not persistent across runs of
        the script, so any extra font paths need to be added each time the
        script starts.
        """
        return self.addFontFiles((font_path,), monospace_only)

    def addFontFiles(self, font_paths, monospace_only=True):
        """ Add a list of font files to the FontManger font search space.
        Each element of the font_paths list must be a valid path including
        the font file name. Relative paths can be used, with the current
        working directory being the origin.

        If monospace_only is True, each font file will only be added if it is
        a monospace font (as only monospace fonts are currently supported by
        TextBox).

        Adding fonts to the FontManager is not persistent across runs of
        the script, so any extra font paths need to be added each time the
        script starts.
        """

        fi_list = []
        for fp in font_paths:
            if os.path.isfile(fp) and os.path.exists(fp):
                face = Face(fp)
                if monospace_only:
                    if face.is_fixed_width:
                        fi_list.append(self._createFontInfo(fp, face))
                else:
                    fi_list.append(self._createFontInfo(fp, face))

        self.font_family_styles.sort()

        return fi_list

    def addFontDirectory(self, font_dir, monospace_only=True, recursive=False):
        """
        Add any font files found in font_dir to the FontManger font search
        space. Each element of the font_paths list must be a valid path
        including the font file name. Relative paths can be used, with the
        current working directory being the origin.

        If monospace_only is True, each font file will only be added if it is
        a monospace font (as only monospace fonts are currently supported by
        TextBox).

        Adding fonts to the FontManager is not persistent across runs of
        the script, so any extra font paths need to be added each time the
        script starts.
        """

        from os import walk

        font_paths = []
        for (dirpath, dirnames, filenames) in walk(font_dir):
            ttf_files = [os.path.join(dirpath, fname)
                         for fname in filenames
                         if fname.lower().endswith('.ttf')]
            font_paths.extend(ttf_files)
            if not recursive:
                break

        return self.addFontFiles(font_paths)

        return fi

    # Class methods for FontManager below this comment should not need to be
    # used by user scripts in most situations. Accessing them is okay.

    @staticmethod
    def getGLFont(font_family_name, size=32, bold=False, italic=False, dpi=72):
        """
        Return a FontAtlas object that matches the family name, style info,
        and size provided. FontAtlas objects are cached, so if multiple
        TextBox instances use the same font (with matching font properties)
        then the existing FontAtlas is returned. Otherwise, a new FontAtlas is
        created , added to the cache, and returned.
        """
        from psychopy.visual.textbox import getFontManager
        fm = getFontManager()

        if fm:
            font_infos = fm.getFontsMatching(font_family_name, bold, italic)
            if len(font_infos) == 0:
                return False
            font_info = font_infos[0]
            fid = MonospaceFontAtlas.getIdFromArgs(font_info, size, dpi)
            font_atlas = fm.font_atlas_dict.get(fid)
            if font_atlas is None:
                font_atlas = fm.font_atlas_dict.setdefault(
                    fid, MonospaceFontAtlas(font_info, size, dpi))
                font_atlas.createFontAtlas()
            if fm.font_store:
                t1 = getTime()
                fm.font_store.addFontAtlas(font_atlas)
                t2 = getTime()
                print('font store add atlas:', t2 - t1)
        return font_atlas

    def getFontInfo(self, refresh=False, monospace=True):
        """
        Returns the available font information as a dict of dict's.
        The first level dict has keys for the available font families.
        The second level dict has keys for the available styles of the
        associated font family. The values in the second level font
        family - style dict are each a list containing FontInfo objects.
        There is one FontInfo object for each physical font file found that
        matches the associated font family and style.
        """
        if refresh or not self._available_font_info:
            self.updateFontInfo(monospace)
        return self._available_font_info

    def updateFontInfo(self, monospace_only=True):
        self._available_font_info.clear()
        del self.font_family_styles[:]
        fonts_found = font_manager.findSystemFonts()
        self.addFontFiles(fonts_found, monospace_only)

    def booleansFromStyleName(self, style):
        """
        For the given style name, return a
        bool indicating if the font is bold, and a second indicating
        if it is italics.
        """
        italic = False
        bold = False
        s = style.lower().strip()
        if s == 'regular':
            return False, False
        if s.find(b'italic') >= 0 or s.find(b'oblique') >= 0:
            italic = True
        if s.find(b'bold') >= 0:
            bold = True
        return bold, italic

    def _createFontInfo(self, fp, fface):
        fns = (fface.family_name, fface.style_name)
        if fns in self.font_family_styles:
            pass
        else:
            self.font_family_styles.append(
                (fface.family_name, fface.style_name))

        styles_for_font_dict = self._available_font_info.setdefault(
            fface.family_name, {})
        fonts_for_style = styles_for_font_dict.setdefault(fface.style_name, [])
        fi = FontInfo(fp, fface)
        fonts_for_style.append(fi)
        return fi

    def __del__(self):
        self.font_store = None
        if self.font_atlas_dict:
            self.font_atlas_dict.clear()
            self.font_atlas_dict = None
        if self._available_font_info:
            self._available_font_info.clear()
            self._available_font_info = None


class FontInfo(object):

    def __init__(self, fp, face):
        self.path = fp
        self.family_name = face.family_name
        self.style_name = face.style_name
        self.charmaps = [charmap.encoding_name for charmap in face.charmaps]
        self.num_faces = face.num_faces
        self.num_glyphs = face.num_glyphs
        #self.size_info= [dict(width=s.width,height=s.height,
        #    x_ppem=s.x_ppem,y_ppem=s.y_ppem) for s in face.available_sizes]
        self.units_per_em = face.units_per_EM
        self.monospace = face.is_fixed_width
        self.charmap_id = face.charmap.index
        self.label = "%s_%s" % (face.family_name, face.style_name)
        self.id = self.label

    def getID(self):
        return self.id

    def asdict(self):
        d = {}
        for k, v in self.__dict__.items():
            if k[0] != '_':
                d[k] = v
        return d


class MonospaceFontAtlas(object):

    def __init__(self, font_info, size, dpi):
        self.font_info = font_info
        self.size = size
        self.dpi = dpi
        self.id = self.getIdFromArgs(font_info, size, dpi)
        self._face = Face(font_info.path)
        self._face.set_char_size(height=self.size * 64, vres=self.dpi)

        self.charcode2glyph = None
        self.charcode2unichr = None
        self.charcode2displaylist = None
        self.max_ascender = None
        self.max_descender = None
        self.max_tile_width = None
        self.max_tile_height = None
        self.max_bitmap_size = None
        self.total_bitmap_area = 0
        self.atlas = None

    def getID(self):
        return self.id

    @staticmethod
    def getIdFromArgs(font_info, size, dpi):
        return "%s_%d_%d" % (font_info.getID(), size, dpi)

    def createFontAtlas(self):
        if self.atlas:
            self.atlas.free()
            self.atlas = None
        self.charcode2glyph = {}
        self.charcode2unichr = {}
        self.max_ascender = None
        self.max_descender = None
        self.max_tile_width = None
        self.max_tile_height = None
        self.max_bitmap_size = None
        self.total_bitmap_area = 0
        # load font glyphs and calculate max. char size.
        # This is used when the altas is created to properly size the tex.
        # i.e. max glyph size * num glyphs

        max_w, max_h = 0, 0
        max_ascender, max_descender, max_tile_width = 0, 0, 0
        face = self._face
        face.set_char_size(height=self.size * 64, vres=self.dpi)

        # Create texAtlas for glyph set.
        x_ppem = face.size.x_ppem
        y_ppem = face.size.x_ppem
        units_ppem = self.font_info.units_per_em
        est_max_width = ((face.bbox.xMax - face.bbox.xMin) /
                         float(units_ppem) * x_ppem)
        est_max_height = face.size.ascender / float(units_ppem) * y_ppem
        target_atlas_area = int(
            est_max_width * est_max_height) * face.num_glyphs
        # make sure it is big enough. ;)
        # height is trimmed before sending to video ram anyhow.
        target_atlas_area = target_atlas_area * 3.0
        pow2_area = nextPow2(target_atlas_area)
        atlas_width = 2048
        atlas_height = pow2_area / atlas_width
        self.atlas = TextureAtlas(atlas_width, atlas_height * 2)
        charcode, gindex = face.get_first_char()

        while gindex:
            uchar = chr(charcode)
            if ud.category(uchar) not in (u'Zl', u'Zp', u'Cc', u'Cf',
                                          u'Cs', u'Co', u'Cn'):
                self.charcode2unichr[charcode] = uchar
                face.load_char(uchar, FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT)
                bitmap = face.glyph.bitmap

                self.total_bitmap_area += bitmap.width * bitmap.rows
                max_ascender = max(max_ascender, face.glyph.bitmap_top)
                max_descender = max(
                    max_descender, bitmap.rows - face.glyph.bitmap_top)
                max_tile_width = max(max_tile_width, bitmap.width)
                max_w = max(bitmap.width, max_w)
                max_h = max(bitmap.rows, max_h)

                x, y, w, h = self.atlas.get_region(
                    bitmap.width + 2, bitmap.rows + 2)

                if x < 0:
                    msg = ("MonospaceFontAtlas.get_region failed "
                           "for: {0}, requested area: {1}. Atlas Full!")
                    vals = charcode, (bitmap.width + 2, bitmap.rows + 2)
                    raise Exception(msg.format(vals))
                x, y = x + 1, y + 1
                w, h = w - 2, h - 2
                data = np.array(
                    bitmap._FT_Bitmap.buffer[:(bitmap.rows * bitmap.width)],
                    dtype=np.ubyte).reshape(h, w, 1)
                self.atlas.set_region((x, y, w, h), data)

                self.charcode2glyph[charcode] = dict(
                    offset=(face.glyph.bitmap_left, face.glyph.bitmap_top),
                    size=(w, h),
                    atlas_coords=(x, y, w, h),
                    texcoords=[x, y, x + w, y + h],
                    index=gindex,
                    unichar=uchar)

            charcode, gindex = face.get_next_char(charcode, gindex)

        self.max_ascender = max_ascender
        self.max_descender = max_descender
        self.max_tile_width = max_tile_width
        self.max_tile_height = max_ascender + max_descender
        self.max_bitmap_size = max_w, max_h

        # resize atlas
        height = nextPow2(self.atlas.max_y + 1)
        self.atlas.resize(height)
        self.atlas.upload()
        self.createDisplayLists()
        self._face = None

    def createDisplayLists(self):
        glyph_count = len(self.charcode2unichr)
        max_tile_width = self.max_tile_width
        max_tile_height = self.max_tile_height
        display_lists_for_chars = {}

        base = glGenLists(glyph_count)
        for i, (charcode, glyph) in enumerate(self.charcode2glyph.items()):
            dl_index = base + i
            uchar = self.charcode2unichr[charcode]

            # update tex coords to reflect earlier resize of atlas height.
            gx1, gy1, gx2, gy2 = glyph['texcoords']
            gx1 = gx1/float(self.atlas.width)
            gy1 = gy1/float(self.atlas.height)
            gx2 = gx2/float(self.atlas.width)
            gy2 = gy2/float(self.atlas.height)
            glyph['texcoords'] = [gx1, gy1, gx2, gy2]

            glNewList(dl_index, GL_COMPILE)
            if uchar not in [u'\t', u'\n']:
                glBegin(GL_QUADS)
                x1 = glyph['offset'][0]
                x2 = x1 + glyph['size'][0]
                y1 = (self.max_ascender - glyph['offset'][1])
                y2 = y1 + glyph['size'][1]

                glTexCoord2f(gx1, gy2), glVertex2f(x1, -y2)
                glTexCoord2f(gx1, gy1), glVertex2f(x1, -y1)
                glTexCoord2f(gx2, gy1), glVertex2f(x2, -y1)
                glTexCoord2f(gx2, gy2), glVertex2f(x2, -y2)
                glEnd()
                glTranslatef(max_tile_width, 0, 0)
            glEndList()

            display_lists_for_chars[charcode] = dl_index

        self.charcode2displaylist = display_lists_for_chars

    def saveGlyphBitmap(self, file_name=None):
        if file_name is None:
            import os
            file_name = os.path.join(os.getcwd(),
                                     self.getID().lower().replace(u' ', u'_') + '.png')
        from scipy import misc
        if self.atlas is None:
            self.loadAtlas()
        if self.atlas.depth == 1:
            misc.imsave(file_name, self.atlas.data.reshape(
                self.atlas.data.shape[:2]))
        else:
            misc.imsave(file_name, self.atlas.data)

    def __del__(self):
        self._face = None
        if self.atlas.texid is not None:
            #glDeleteTextures(1, self.atlas.texid)
            self.atlas.texid = None
            self.atlas = None
        if self.charcode2displaylist is not None:
            # for dl in self.charcode2displaylist.values():
            #    glDeleteLists(dl, 1)
            self.charcode2displaylist.clear()
            self.charcode2displaylist = None
        if self.charcode2glyph is not None:
            self.charcode2glyph.clear()
            self.charcode2glyph = None
        if self.charcode2unichr is not None:
            self.charcode2unichr.clear()
            self.charcode2unichr = None
