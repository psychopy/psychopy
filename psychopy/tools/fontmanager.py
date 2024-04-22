#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
#
#  FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#
# -----------------------------------------------------------------------------
# Shader compilation code
# -----------------------------------------------------------------------------
#
# Copyright Tristam Macdonald 2008.
#
# Distributed under the Boost Software License, Version 1.0
# (see http://www.boost.org/LICENSE_1_0.txt)
#
import inspect
import re
import sys, os
import math
import numpy as np
import ctypes
import freetype as ft
from pyglet import gl  # import OpenGL.GL not compatible with Big Sur (2020)
from pathlib import Path
import requests

from psychopy import logging
from psychopy import prefs
from psychopy.exceptions import MissingFontError

#  OS Font paths
_X11FontDirectories = [
    # an old standard installation point
    Path("/usr/X11R6/lib/X11/fonts/TTF"),
    Path("/usr/X11/lib/X11/fonts"),
    # here is the new standard location for fonts
    Path("/usr/share/fonts"),
    # documented as a good place to install new fonts
    Path("/usr/local/share/fonts"),
    # common application, not really useful
    Path("/usr/lib/openoffice/share/fonts/truetype"),
]

_OSXFontDirectories = [
    Path("/Library/Fonts/"),
    Path.home() / "Library" / "Fonts",
    Path("/Network/Library/Fonts"),
    Path("/System/Library/Fonts"),
    # fonts installed via MacPorts
    Path("/opt/local/share/fonts"),
]

_weightMap = {
    # Map of various potential values for "bold" and the numeric font weight which they correspond to
    100: 100, "thin": 100, "hairline": 100,
    200: 200, "extralight": 200, "ultralight": 200,
    300: 300, "light": 300,
    400: 400, False: 400, "normal": 400, "regular": 400,
    500: 500, "medium": 500,
    600: 600, "semibold": 600, "demibold": 600,
    700: 700, "bold": 700, True: 700,
    800: 800, "extrabold": 800, "ultrabold": 800,
    900: 900, "black": 900, "heavy": 900,
    950: 950, "extrablack": 950, "ultrablack": 950
}

supportedExtensions = ['ttf', 'otf', 'ttc', 'dfont', 'truetype']


def unicode(s, fmt='utf-8'):
    """Force to unicode if bytes"""
    if type(s) == bytes:
        return s.decode(fmt)
    else:
        return s

# this class was to get aorund the issue of constantly having to convert to
# and from utf-8 because the ft.Face class uses b'' for family_name,
# family_style but the problems run deeper than that (hot mess!). Maybe ft will
# update with better Py3 support?
# class Face(ft.Face):
#     """This is the same as freetype Face class but with unicode face"""
#     def __init__(self, *args, **kwargs):
#         self._ftFace = ft.Face(self, *args, **kwargs)
#         # store original properties of the ft.Face
#         self._family_name = ft.Face
#
#     @property
#     def family_name(self):
#         return unicode(self._ftFace.family_name)
#
#     @property
#     def style_name(self):
#         return unicode(self._ftFace.style_name)
#
#     def __get__(self, att):
#         if att in self.__dict__:
#             return self.__dict__[att]
#         else:
#             try:
#                 return getattr(self._ftFace, att)
#             except AttributeError:
#                 raise AttributeError("freetype.Face has no attribute '{}'"
#                                      .format(att))

class _TextureAtlas:
    """ A TextureAtlas is the texture used by the GLFont to store the glyphs

    Group multiple small data regions into a larger texture.

    The algorithm is based on the article by Jukka Jylänki : "A Thousand Ways
    to Pack the Bin - A Practical Approach to Two-Dimensional Rectangle Bin
    Packing", February 27, 2010. More precisely, this is an implementation of
    the Skyline Bottom-Left algorithm based on C++ sources provided by Jukka
    Jylänki at: http://clb.demon.fi/files/RectangleBinPack/

    Example usage:
    --------------

    atlas = TextureAtlas(512,512,3)
    region = atlas.get_region(20,20)
    ...
    atlas.set_region(region, data)
    """

    def __init__(self, width=2048, height=2048, format='alpha',
                 name='fontname'):  # name just for logging purposes
        """
        Initialize a new atlas of given size.

        Parameters
        ----------

        width : int
            Width of the underlying texture

        height : int
            Height of the underlying texture

        format : 'alpha' or 'rgb'
            Depth of the underlying texture
        """
        self.name = name
        self.width = int(math.pow(2, int(math.log(width, 2) + 0.5)))
        self.height = int(math.pow(2, int(math.log(height, 2) + 0.5)))
        self.format = format
        self.nodes = [(0, 0, self.width), ]
        self.textureID = 0
        self.used = 0
        if format == 'rgb':
            self.data = np.zeros((self.height, self.width, 3),
                                 dtype=np.ubyte)
        elif format == 'alpha':
            self.data = np.zeros((self.height, self.width),
                                 dtype=np.ubyte)
        else:
            raise TypeError("TextureAtlas should have format of 'alpha' or "
                            "'rgb' not {}".format(repr(format)))

    def set_region(self, region, data):
        """
        Set a given region width provided data.

        Parameters
        ----------

        region : (int,int,int,int)
            an allocated region (x,y,width,height)

        data : numpy array
            data to be copied into given region
        """

        x, y, width, height = region
        if self.format == 'rgb':
            self.data[int(y):int(y + height), int(x):int(x + width), :] = data
        else:
            self.data[int(y):int(y + height), int(x):int(x + width)] = data

    def get_region(self, width, height):
        """
        Get a free region of given size and allocate it

        Parameters
        ----------

        width : int
            Width of region to allocate

        height : int
            Height of region to allocate

        Return
        ------
            A newly allocated region as (x,y,width,height) or (-1,-1,0,0)
        """

        best_height = sys.maxsize
        best_index = -1
        best_width = sys.maxsize
        region = 0, 0, width, height

        for i in range(len(self.nodes)):
            y = self.fit(i, width, height)
            if y >= 0:
                node = self.nodes[i]
                if (y + height < best_height or
                        (y + height == best_height and node[2] < best_width)):
                    best_height = y + height
                    best_index = i
                    best_width = node[2]
                    region = node[0], y, width, height

        if best_index == -1:
            return -1, -1, 0, 0

        node = region[0], region[1] + height, width
        self.nodes.insert(best_index, node)

        i = best_index + 1
        while i < len(self.nodes):
            node = self.nodes[i]
            prev_node = self.nodes[i - 1]
            if node[0] < prev_node[0] + prev_node[2]:
                shrink = prev_node[0] + prev_node[2] - node[0]
                x, y, w = self.nodes[i]
                self.nodes[i] = x + shrink, y, w - shrink
                if self.nodes[i][2] <= 0:
                    del self.nodes[i]
                    i -= 1
                else:
                    break
            else:
                break
            i += 1

        self.merge()
        self.used += width * height
        return region

    def fit(self, index, width, height):
        """
        Test if region (width,height) fit into self.nodes[index]

        Parameters
        ----------

        index : int
            Index of the internal node to be tested

        width : int
            Width or the region to be tested

        height : int
            Height or the region to be tested

        """

        node = self.nodes[index]
        x, y = node[0], node[1]
        width_left = width

        if x + width > self.width:
            return -1

        i = index
        while width_left > 0:
            node = self.nodes[i]
            y = max(y, node[1])
            if y + height > self.height:
                return -1
            width_left -= node[2]
            i += 1
        return y

    def merge(self):
        """
        Merge nodes
        """

        i = 0
        while i < len(self.nodes) - 1:
            node = self.nodes[i]
            next_node = self.nodes[i + 1]
            if node[1] == next_node[1]:
                self.nodes[i] = node[0], node[1], node[2] + next_node[2]
                del self.nodes[i + 1]
            else:
                i += 1

    def upload(self):
        """Upload the local atlas data into graphics card memory
        """
        if not self.textureID:
            self.textureID = gl.GLuint(0)
            gl.glGenTextures(1, ctypes.byref(self.textureID))
        logging.debug("Uploading Texture Font {} to graphics card"
                      .format(self.name))
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.textureID)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        if self.format == 'alpha':
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_ALPHA,
                            self.width, self.height, 0,
                            gl.GL_ALPHA, gl.GL_UNSIGNED_BYTE, self.data.ctypes)
        else:
            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB,
                            self.width, self.height, 0,
                            gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.data.ctypes)
        logging.debug("Upload of Texture Font {} complete"
                      .format(self.name))

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


class GLFont:
    """
    A GLFont gathers a set of glyphs for a given font filename and size.

        size : int
            Distance between the tops of capital letters and the bottoms of descenders

        height : int
            Total distance from one baseline to the next

        capheight : int
            Position of the tops of capital letters relative to the baseline

        ascender : int
            Position of the tops of ascenders relative to the baseline

        descender : int
            Position of the bottoms of descenders relative to the baseline

        linegap : int
            Distance between the bottoms of this line's descenders and the tops of the next line's ascenders

        leading : int
            Position of the tops of the next line's ascenders relative to this line's baseline
    """

    def __init__(self, filename, size, lineSpacing=1, textureSize=2048):
        """
        Initialize font

        Parameters:
        -----------

        atlas: TextureAtlas
            Texture atlas where glyph texture will be stored
        
        filename: str
            Font filename

        size : float
            Font size

        lineSpacing : float
            Leading between lines, proportional to font size
        """
        self.scale = 64.0
        self.atlas = _TextureAtlas(textureSize, textureSize, format='alpha')
        self.format = self.atlas.format
        self.filename = filename
        self.face = ft.Face(str(filename))  # ft.Face doesn't support Pathlib yet
        self.size = size
        self.glyphs = {}
        self.info = FontInfo(filename, self.face)
        self._dirty = False
        # Get metrics
        metrics = self.face.size
        self.ascender = metrics.ascender / self.scale
        self.descender = metrics.descender / self.scale
        self.height = metrics.height / self.scale
        # Set spacing
        self.lineSpacing = lineSpacing

    def __getitem__(self, charcode):
        """
        x.__getitem__(y) <==> x[y]
        """
        if charcode not in self.glyphs:
            self.fetch('%c' % charcode)
        return self.glyphs[charcode]

    def __str__(self):
        """Returns a string rep of the font, such as 'Arial_24_bold' """
        return "{}_{}".format(self.info, self.size)

    @property
    def leading(self):
        """
        Position of the next row's ascender line relative to this row's base line.
        """
        return self.ascender - self.height

    @leading.setter
    def leading(self, value):
        self.height = self.ascender - value

    @property
    def linegap(self):
        return -(self.leading - self.descender)

    @linegap.setter
    def linegap(self, value):
        self.leading = self.descender - value

    @property
    def capheight(self):
        """
        Position of the top of capital letters relative to the base line.
        """
        return self.descender + self.size

    @capheight.setter
    def capheight(self, value):
        self.size = value - self.descender

    @property
    def size(self):
        """
        Distance from the descender line to the capheight line.
        """
        if hasattr(self, "_size"):
            return self._size

    @size.setter
    def size(self, value):
        self._size = value
        self.face.set_char_size(int(self.size * self.scale))

    @property
    def lineSpacing(self):
        return self.height / (self.ascender - self.descender)

    @lineSpacing.setter
    def lineSpacing(self, value):
        self.height = value * (self.ascender - self.descender)

    @property
    def name(self):
        """Name of the Font (e.g. 'Arial_24_bold')
        """
        return str(self)

    @property
    def textureID(self):
        """
        Get underlying texture identity .
        """

        if self._dirty:
            self.atlas.upload()
        self._dirty = False
        return self.atlas.textureID

    def preload(self, nMax=None):
        """
        :return:
        """
        if nMax is None:
            note = "entire glyph set"
        else:
            note = "{} glyphs".format(nMax)
        logging.debug("Preloading {} for Texture Font {}"
                      .format(note, self.name))
        face = ft.Face(str(self.filename))  # ft.Face doesn't support Pathlib

        chrs = (list(face.get_chars()))[:nMax]
        charcodes = [chr(c[1]) for c in chrs]
        self.fetch(charcodes, face=face)
        logging.debug("Preloading of glyph set for Texture Font {} complete"
                      .format(self.name))

    def fetch(self, charcodes='', face=None):
        """
        Build glyphs corresponding to individual characters in charcodes.

        Parameters:
        -----------

        charcodes: [str | unicode]
            Set of characters to be represented
        """
        if face is None:
            face = ft.Face(str(self.filename))  # doesn't support Pathlib yet

        # if current glyph is same as last then maybe blank glyph?
        lastGlyph = None
        possibleBlank = None
        nBlanks = 0

        for charcode in charcodes:
            if charcode in self.glyphs:
                continue
            face.set_pixel_sizes(int(self.size), int(self.size))

            self._dirty = True
            flags = ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT
            flags |= ft.FT_LOAD_TARGET_LCD

            face.load_char(charcode, flags)
            bitmap = face.glyph.bitmap
            # check if this looks like a blank (same as a prev glyph)
            if bitmap.buffer == lastGlyph:
                possibleBlank = lastGlyph
            if bitmap.buffer == possibleBlank:  # whether newly detected or not
                nBlanks += 1
                continue
            lastGlyph = bitmap.buffer
            left = face.glyph.bitmap_left
            top = face.glyph.bitmap_top
            width = face.glyph.bitmap.width
            rows = face.glyph.bitmap.rows
            pitch = face.glyph.bitmap.pitch

            if self.format == 'rgb':
                x, y, w, h = self.atlas.get_region(width / 5, rows + 2)
            else:
                x, y, w, h = self.atlas.get_region(width + 2, rows + 2)

            if x < 0:
                msg = ("Failed to fit char into font texture ({} at size {}px)"
                       .format(face.family_name, self.size))
                raise RuntimeError(msg)

            x, y = x + 1, y + 1
            w, h = w - 2, h - 2

            data = np.array(bitmap.buffer).reshape(rows, pitch)
            data = data[:h, :w]

            if self.format == 'rgb':
                Z = (((data / 255.0) ** 1.5) * 255).astype(np.ubyte)
            self.atlas.set_region((x, y, w, h), data)

            # Build glyph
            size = w, h
            offset = left, top
            advance = (face.glyph.advance.x / self.scale,
                       face.glyph.advance.y / self.scale)

            u0 = (x + 0.0) / float(self.atlas.width)
            v0 = (y + 0.0) / float(self.atlas.height)
            u1 = (x + w - 0.0) / float(self.atlas.width)
            v1 = (y + h - 0.0) / float(self.atlas.height)
            texcoords = (u0, v0, u1, v1)
            glyph = TextureGlyph(charcode, size, offset, advance, texcoords)
            self.glyphs[charcode] = glyph

            # Generate kerning
            # for g in self.glyphs.values():
            #     kerning = face.get_kerning(g.charcode, charcode,
            #                                mode=ft.FT_KERNING_UNFITTED)
            #     if kerning.x != 0:
            #         glyph.kerning[g.charcode] = kerning.x / self.scale
            #
            #     kerning = face.get_kerning(charcode, g.charcode,
            #                                mode=ft.FT_KERNING_UNFITTED)
            #     if kerning.x != 0:
            #         g.kerning[charcode] = kerning.x / self.scale

        logging.debug("TextBox2 loaded {} chars with {} blanks and {} valid"
                     .format(len(charcodes), nBlanks, len(charcodes) - nBlanks))

    def saveToCache(self):
        """Store the current font texture as an image file.

        As yet we aren't storing the offset, advance and texcoords as needed to
        retrieve the necessary chars, but it's a start!
            (see  TextureGlyph(charcode, size, offset, advance, texcoords) )

        """
        from PIL import Image
        im = Image.fromarray(self.atlas.data)
        fname = "{}/.psychopy3/{}_{}_texture.png".format(
            os.path.expanduser("~"), self.name, self.size)
        im.save(fname)

    def upload(self):
        """Upload the font data into graphics card memory.
        """
        self.atlas.upload()


class TextureGlyph:
    """
    A texture glyph gathers information relative to the size/offset/advance and
    texture coordinates of a single character. It is generally built
    automatically by a TextureFont.
    """

    def __init__(self, charcode, size, offset, advance, texcoords):
        """
        Build a new texture glyph

        Parameter:
        ----------

        charcode : char
            Represented character

        size: tuple of 2 ints
            Glyph size in pixels

        offset: tuple of 2 floats
            Glyph offset relatively to anchor point

        advance: tuple of 2 floats
            Glyph advance

        texcoords: tuple of 4 floats
            Texture coordinates of bottom-left and top-right corner
        """
        self.charcode = charcode
        self.size = size
        self.offset = offset
        self.advance = advance
        self.texcoords = texcoords
        self.kerning = {}

    def get_kerning(self, charcode):
        """ Get kerning information

        Parameters:
        -----------

        charcode: char
            Character preceding this glyph
        """
        if charcode in self.kerning.keys():
            return self.kerning[charcode]
        else:
            return 0


def findFontFiles(folders=None, recursive=True):
    """
    Search for font files in the folder (or system folders)

    Parameters
    ----------
    folders: list
        Folders to search in addition to usual system folders and current script's folder
    recursive : bool
        If True, then also search subfolders within specified folders

    Returns
    -------
    list[str]
        Paths to font files (as strings)
    """
    # start off with nothing
    found = []
    # start off with whatever matplotlib finds
    try:
        from matplotlib import font_manager
        found += font_manager.findSystemFonts()
    except Exception as err:
        logging.warn(
            f"Matplotlib failed to find fonts, original error: {err}"
        )
    # if no folders given, start off with blank list
    if folders is None:
        folders = []
    # make sure folders are all paths
    for i, thisFolder in enumerate(folders):
        if not isinstance(thisFolder, Path):
            folders[i] = Path(thisFolder)
    # add packaged assets folder
    folders.append(
        Path(prefs.paths['assets']) / "fonts"
    )
    # add the user folder
    folders.append(
        Path(prefs.paths['userPrefsDir']) / "fonts"
    )
    # add the folder the current script was called from
    _frame = inspect.currentframe()
    folders.append(
        Path(inspect.getfile(_frame))
    )
    # add OS folders (windows is already covered by matplotlib)
    if sys.platform == 'darwin':
        folders += _OSXFontDirectories
    elif sys.platform.startswith('linux'):
        folders += _X11FontDirectories
    # check requested folders
    for thisFolder in folders:
        # try all extensions...
        for ext in supportedExtensions:
            # construct glob based on recursive or not
            if recursive:
                searchStr = f"**/*.{ext}"
            else:
                searchStr = f"*.{ext}"
            # do recursive glob search
            for file in thisFolder.glob(searchStr):
                # stringify Path object
                file = str(file)
                # if file is new, append to found array
                if file not in found:
                    found.append(file)

    return found


class FontManager():
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

    fonts = visual.textbox2.getFontManager()

    A user script never creates an instance of the FontManager class and
    should always access it using visual.textbox.getFontManager().

    Once a font of a given size and dpi has been created; it is cached by the
    FontManager and can be used by all TextBox instances created within the
    experiment.

    """
    freetype_import_error = None
    _glFonts = {}
    fontStyles = []
    _fontInfos = {}  # JWP: dict of name:FontInfo objects

    def __init__(self, monospaceOnly=False):
        self.addFontDirectory(prefs.paths['assets'])
        # if FontManager.freetype_import_error:
        #    raise Exception('Appears the freetype library could not load.
        #       Error: %s'%(str(FontManager.freetype_import_error)))

        self.monospaceOnly = monospaceOnly
        self.updateFontInfo(monospaceOnly)

    def __str__(self):
        S = "Loaded:\n"
        if len(self._glFonts):
            for name in self._glFonts:
                S += "  {}\n".format(name)
        else:
            S += "None\n"
        S += ("Available: {} see fonts.getFontFamilyNames()\n"
              .format(len(self.getFontFamilyNames())))
        return S

    def getDefaultSansFont(self):
        """Load and return the FontInfo for the first found default font"""
        for name in ['Arial', 'Verdana', 'DejaVu Sans', 'Bitstream Vera Sans', 'Tahoma']:
            these = self.getFontsMatching(name, fallback=False)
            if not these:
                continue
            if type(these) in (list, set):
                this = these[0]
            # if str or Path then get a FontInfo object
            if type(this) in [str, Path]:
                this = self.addFontFiles(this)
            return this
        raise MissingFontError("Failed to find any of the default fonts. "
                               "Existing fonts: {}"
                               .format(list(self._fontInfos)))

    def getFontFamilyNames(self):
        """Returns a list of the available font family names.
        """
        return list(self._fontInfos.keys())

    def getFontStylesForFamily(self, family_name):
        """For the given family, a list of style names supported is
        returned.
        """
        style_dict = self._fontInfos.get(family_name)
        if style_dict:
            return list(style_dict.keys())

    def getFontFamilyStyles(self):
        """Returns a list where each element of the list is a itself a
        two element list of [fontName,[fontStyle_names_list]]
        """
        return self.fontStyles

    def getFontsMatching(self, fontName, bold=False, italic=False,
                         fontStyle=None, fallback=True):
        """
        Returns the list of FontInfo instances that match the provided
        fontName and style information. If no matching fonts are
        found, None is returned.
        """
        if type(fontName) != bytes:
            fontName = bytes(fontName, sys.getfilesystemencoding())
        # Convert value of "bold" to a numeric font weight
        if bold in _weightMap or str(bold).lower().strip() in _weightMap:
            bold = _weightMap[bold]
        else:
            bold = _weightMap[False] # Default to regular
        style_dict = self._fontInfos.get(fontName)
        if not style_dict:
            if not fallback:
                return None
            similar = self.getFontNamesSimilar(fontName)
            if len(similar) == 0:
                logging.warning("Font {} was requested. No similar font found.".format(repr(fontName)))
                return [self.getDefaultSansFont()]
            elif len(similar) == 1:
                logging.warning("Font {} was requested. Exact match wasn't "
                                "found but we will proceed with {}?"
                                .format(repr(fontName), repr(similar[0])))
                style_dict = self._fontInfos.get(similar[0])
            else:  # more than 1 alternatives. Which to use?
                raise ValueError("Font {} was requested. Exact match wasn't "
                                 "found, but maybe one of these was intended:"
                                 "{}?".format(repr(fontName), similar))
            if not style_dict:
                return None
        # check if we have a valid style too
        if fontStyle and fontStyle in style_dict:
            return style_dict[fontStyle]
        for style, fonts in style_dict.items():
            b, i = self.booleansFromStyleName(style)
            if b == bold and i == italic:
                return fonts
        return None

    def getFontNamesSimilar(self, fontName):
        if type(fontName) != bytes:
            fontName = bytes(fontName, sys.getfilesystemencoding())
        allNames = list(self._fontInfos)
        similar = [this for this in allNames if
                   (fontName.lower() in this.lower())]
        return similar

    def addGoogleFont(self, fontName):
        """Add a font directly from the Google Font repository, saving it to the user prefs folder"""

        # Construct and send Google Font url from name
        repoURL = f"https://fonts.googleapis.com/css2?family={ fontName.replace(' ', '+') }&display=swap"
        repoResp = requests.get(repoURL)
        if not repoResp.ok:
            # If font name is not found, raise error
            raise MissingFontError("Font `{}` could not be retrieved from the Google Font library.".format(fontName))
        # Get and send file url from returned CSS data
        fileURL = re.findall(r"(?<=src: url\().*(?=\) format)", repoResp.content.decode())[0]
        fileFormat = re.findall(r"(?<=format\(\').*(?=\'\)\;)", repoResp.content.decode())[0]
        fileResp = requests.get(fileURL)
        if not fileResp.ok:
            # If font file is not available, raise error
            raise MissingFontError("OST file for Google font `{}` could not be accessed".format(fontName))
        # Save retrieved font as an OST file
        fileName = Path(prefs.paths['fonts']) / f"{fontName}.{fileFormat}"
        logging.info("Font \"{}\" was successfully installed at: {}".format(fontName, prefs.paths['fonts']))
        with open(fileName, "wb") as fileObj:
            fileObj.write(fileResp.content)
        # Add font and return
        return self.addFontFile(fileName)

    def addFontFile(self, fontPath, monospaceOnly=False):
        """Add a Font File to the FontManger font search space. The
        fontPath must be a valid path including the font file name.
        Relative paths can be used, with the current working directory being
        the origin.

        If monospaceOnly is True, the font file will only be added if it is a
        monospace font.

        Adding a Font to the FontManager is not persistent across runs of
        the script, so any extra font paths need to be added each time the
        script starts.
        """
        fi_list = set()
        if os.path.isfile(fontPath) and os.path.exists(fontPath):
            # try to make a Face object
            try:
                face = ft.Face(str(fontPath))
            except Exception:
                logging.warning("Font Manager failed to load file {}"
                                .format(fontPath))
                return
            # make sure it has a name
            if face.family_name is None:
                logging.warning("{} doesn't have valid font family name"
                                .format(fontPath))
                return
            # create a FontInfo object
            if face.is_fixed_width or not monospaceOnly:
                fi_obj = self._createFontInfo(fontPath, face)
            else:
                return
            # store in local list
            fi_list.add(fi_obj)
            # store in object list
            if face.family_name not in self._fontInfos:
                self._fontInfos[face.family_name] = fi_obj

        return fi_list

    def addFontFiles(self, fontPaths, monospaceOnly=False):
        """ Add a list of font files to the FontManger font search space.
        Each element of the fontPaths list must be a valid path including
        the font file name. Relative paths can be used, with the current
        working directory being the origin.

        If monospaceOnly is True, each font file will only be added if it is
        a monospace font.

        Adding fonts to the FontManager is not persistent across runs of
        the script, so any extra font paths need to be added each time the
        script starts.
        """

        fi_list = []
        for fp in fontPaths:
            self.addFontFile(fp, monospaceOnly)
        self.fontStyles.sort()

        return fi_list

    def addFontDirectory(self, fontDir, monospaceOnly=False, recursive=False):
        """
        Add any font files found in fontDir to the FontManger font search
        space. Each element of the fontPaths list must be a valid path
        including the font file name. Relative paths can be used, with the
        current working directory being the origin.

        If monospaceOnly is True, each font file will only be added if it is
        a monospace font (as only monospace fonts are currently supported by
        TextBox).

        Adding fonts to the FontManager is not persistent across runs of
        the script, so any extra font paths need to be added each time the
        script starts.
        """
        fontPaths = findFontFiles([fontDir], recursive=recursive)
        return self.addFontFiles(fontPaths)

    @staticmethod
    def isFamily(font, family):
        """
        Check whether a font is of a particular family

        Parameters
        ----------
        font : freetype.Face
            Font object whose family attribute to check
        family : str
            Family name to check against

        Returns
        -------
        bool
            True if the given font appears to be of the given family
        """
        # get font name
        fontName = font.family_name.decode("utf-8")
        # if it's already a perfect match, our work here is done!
        if fontName == family:
            return True
        # convert both names to lowercase
        fontName = fontName.lower()
        family = family.lower()
        # do they match now?
        if fontName == family:
            return True
        # convert space-like chars to underscores
        spacelike = r"[\s\t-_+]"
        fontName = re.sub(pattern=spacelike, repl="_", string=fontName)
        family = re.sub(pattern=spacelike, repl="_", string=family)
        # do they match now?
        if fontName == family:
            return True

        # if this all failed, it's not the same family
        return False

    # Class methods for FontManager below this comment should not need to be
    # used by user scripts in most situations. Accessing them is okay.

    def getFont(self, name, size=32, bold=False, italic=False, lineSpacing=1,
                monospace=False):
        """
        Return a FontAtlas object that matches the family name, style info,
        and size provided. FontAtlas objects are cached, so if multiple
        TextBox instances use the same font (with matching font properties)
        then the existing FontAtlas is returned. Otherwise, a new FontAtlas is
        created , added to the cache, and returned.
        """
        fontInfos = self.getFontsMatching(name, bold, italic, fallback=False)
        if not fontInfos:
            # If font not found, try to retrieve it from Google
            try:
                self.addGoogleFont(name)
            except (MissingFontError, ValueError):
                pass
            # Then try again with fallback
            fontInfos = self.getFontsMatching(name, bold, italic, fallback=True)
            if not fontInfos:
                return False
        # If font is found, make glfont
        fontInfo = fontInfos[0]
        identifier = "{}_{}".format(str(fontInfo), size)
        glFont = self._glFonts.get(identifier)
        if glFont is None:
            glFont = GLFont(fontInfo.path, size, lineSpacing=lineSpacing)
            self._glFonts[identifier] = glFont

        return glFont

    def updateFontInfo(self, monospaceOnly=False):
        self._fontInfos.clear()
        del self.fontStyles[:]
        fonts_found = findFontFiles()
        self.addFontFiles(fonts_found, monospaceOnly)

    def booleansFromStyleName(self, style):
        """
        For the given style name, return a
        bool indicating if the font is bold, and a second indicating
        if it is italics.
        """
        italic = False
        bold = False
        s = style.lower().strip()
        if type(s) == bytes:
            s = s.decode('utf-8')
        # Work out Italic
        italic = False # Default false
        if s.find('italic') >= 0 or s.find('oblique') >= 0:
            italic = True
        # Work out font weight
        bold = _weightMap[False] # Default regular weight
        for key in _weightMap:
            if s.find(str(key)) >= 0:
                bold = _weightMap[key]
        return bold, italic

    def _createFontInfo(self, fp, fface):
        """"""
        fns = (fface.family_name, fface.style_name)
        if fns in self.fontStyles:
            pass
        else:
            self.fontStyles.append(
                (fface.family_name, fface.style_name))

        styles_for_font_dict = FontManager._fontInfos.setdefault(
            fface.family_name, {})
        fonts_for_style = styles_for_font_dict.setdefault(fface.style_name, [])
        fi = FontInfo(fp, fface)
        fonts_for_style.append(fi)
        return fi

    def __del__(self):
        self.font_store = None
        if self._glFonts:
            self._glFonts.clear()
            self._glFonts = None
        if self._fontInfos:
            self._fontInfos.clear()
            self._fontInfos = None


class FontInfo():

    def __init__(self, fp, face):
        self.path = fp
        self.family = unicode(face.family_name)
        self.style = unicode(face.style_name)
        self.charmaps = [charmap.encoding_name for charmap in face.charmaps]
        self.num_faces = face.num_faces
        self.num_glyphs = face.num_glyphs
        # self.size_info= [dict(width=s.width,height=s.height,
        #    x_ppem=s.x_ppem,y_ppem=s.y_ppem) for s in face.available_sizes]
        self.units_per_em = face.units_per_EM
        self.monospace = face.is_fixed_width
        self.charmap_id = face.charmap.index
        self.label = "%s_%s" % (face.family_name, face.style_name)

    def __str__(self):
        """Generate a string identifier for this font name_style
        """
        fullName = "{}".format(self.family)
        if self.style:
            fullName += "_" + self.style
        return fullName

    def asdict(self):
        d = {}
        for k, v in self.__dict__.items():
            if k[0] != '_':
                d[k] = v
        return d
