# -*- coding: utf-8 -*-
"""
Created on Sun May 19 12:20:03 2013

@author: isolver
"""

import os
import numpy
from psychopy.visual.textbox.freetype_bf import Face, version, FT_LOAD_RENDER,  FT_LOAD_FORCE_AUTOHINT
from textureAtlas import TextureAtlas
              
class TTFont(object):
    _font_dirs=[]
    _loaded_fonts=dict()
    _glyphs_loaded=False
    _texture_atlas=TextureAtlas(1024,1024)
    _background_swatch=None
    def __init__(self,label,file_name,size,dpi=72):
        self._label=label
        self._charcode2glyph=dict()
        self._max_ascender = 0
        self._max_descender = 0
        self._max_tile_width = 0
        self._max_tile_height = 0
        self._size=size
        self._dpi=dpi
        
        font_dir=None
        for fdir in self._font_dirs:
            fd=os.path.normcase(os.path.join(fdir,file_name))
            if os.path.exists(fd):
                font_dir=fdir
                break
                
        fdir=font_dir  
        ffile=file_name  
        fsize=size
        fdpi=dpi

        if fdir is None:
            raise IOError("TTFont file name could not be found: ",file_name)
            
        if ffile is None:
            raise AttributeError("TTFont file name can not be None.")

        self._path=os.path.normcase(os.path.join(fdir,file_name))

        if os.path.exists(self._path) and os.path.isfile(self._path):
            self._font=Face(self._path)
        else:
            raise IOError("TTFont file not found or not a file: {0}".format(self._path))
            
        self._font.set_char_size(height=fsize*64,vres=fdpi)

        if not self.isMonoType():
            raise 'Font is not monotype'
       
    
    @classmethod
    def getSearchDirectories(cls):
        return cls._font_dirs

    @classmethod
    def addSearchDirectories(cls,*font_dir_list):
        for fdir in font_dir_list:
            try:
                abs_fdir=os.path.normcase(os.path.abspath(fdir))
                if os.path.exists(abs_fdir) and abs_fdir not in cls._font_dirs:
                    cls._font_dirs.append(abs_fdir)
            except Exception, e:
                print 'Error in addFontDirectories:'
                print e
            
    @classmethod
    def removeSearchDirectories(cls,*font_dir_list):
        for fdir in font_dir_list:
            try:
                abs_fdir=os.path.normcase(os.path.abspath(fdir))
                if abs_fdir in cls._font_dirs:
                    cls._font_dirs.remove(abs_fdir)
            except Exception, e:
                print 'Error in removeFontDirectories:'
                print e

    @staticmethod
    def getNameFromValues(file_name,size,dpi):
        return '{file_name}_{size}_{dpi}'.format(file_name=file_name.replace(' ','_'),size=size,dpi=dpi)

    @classmethod
    def fontSpecLoaded(cls,file_name,size,dpi=72):
        font_label=cls.getNameFromValues(file_name,size,dpi)
        if font_label in cls._loaded_fonts:
            return True
        return False

    @classmethod
    def load(cls,file_name,size=24,dpi=72):
        font_label=cls.getNameFromValues(file_name,size,dpi)
        if font_label in cls._loaded_fonts:
            return cls._loaded_fonts[font_label]
        new_font=cls(font_label,file_name,size,dpi)    
        cls._loaded_fonts[font_label]=new_font
        return new_font
        
    @classmethod
    def getLoadedFonts(cls):
        return cls._loaded_fonts.values()

    @classmethod
    def removeLoadedFonts(cls,font_label):
        font_label=font_label.replace(' ','_')
        print '** TODO: Ensure memory and textures is freed for all associated objects when font is deleted'
        del cls._loaded_fonts[font_label]

    @classmethod
    def getTextureAtlas(cls):
        return cls._texture_atlas
    
    def getLabel(self):
        return self._label
        
    def isMonoType(self):
        if self._font and self._font.is_fixed_width:
            return True
        return False

    def getGlyphCount(self):
        return len(self._charcode2glyph.keys())

    @classmethod
    def _loadGlyphs(cls):
        # Create a list of all code points available in the font face.
        # Determine bitmap size for each glyph and largest glyph size
        #        
        from glyph import Glyph
        
        for ttfont in cls.getLoadedFonts():        
            max_ascender, max_descender, max_tile_width = 0, 0, 0
            charcode, gindex=ttfont._font.get_first_char()
            while gindex:        
                uchar=unichr(charcode)
                ttfont._font.load_char(uchar, FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
    
                bitmap = ttfont._font.glyph.bitmap
                left   = ttfont._font.glyph.bitmap_left
                top    = ttfont._font.glyph.bitmap_top
                width  = ttfont._font.glyph.bitmap.width
                rows   = ttfont._font.glyph.bitmap.rows
                pitch  = ttfont._font.glyph.bitmap.pitch
    
                region = TTFont._texture_atlas.get_region(width+2, rows+2)
                x,y,w,h=region
                if x < 0:
                    raise "TTFont._texture_atlas.get_region failed for: {0}, requested area: {1}".format(uchar,(width+2, rows+2))
                    
                x,y = x+1, y+1
                w,h = w-2, h-2
                data = []
                for i in range(rows):
                    data.extend(bitmap.buffer[i*pitch:i*pitch+width])
                data = numpy.array(data,dtype=numpy.ubyte).reshape(h,w,1)
                gamma = 1.0
                Z = ((data/255.0)**(gamma))
                data = (Z*255).astype(numpy.ubyte)
                TTFont._texture_atlas.set_region((x,y,w,h), data)
    
                # Build glyph
                size   = w,h
                offset = left, top
                advance= ttfont._font.glyph.advance.x, ttfont._font.glyph.advance.y
                
                u0     = (x +     0.0)/float(TTFont._texture_atlas.width)
                v0     = (y +     0.0)/float(TTFont._texture_atlas.height)
                u1     = (x + w - 0.0)/float(TTFont._texture_atlas.width)
                v1     = (y + h - 0.0)/float(TTFont._texture_atlas.height)
    
                texcoords = (u0,v0,u1,v1)
                g=Glyph(gindex,charcode,uchar,size, offset, advance, texcoords,region)                      
                ttfont._charcode2glyph[charcode]=g
    
                max_ascender = max( max_ascender, ttfont._font.glyph.bitmap_top)
                max_descender = max( max_descender,bitmap.rows-ttfont._font.glyph.bitmap_top )
                max_tile_width = max( max_tile_width,bitmap.width )
   
                charcode, gindex = ttfont._font.get_next_char(charcode, gindex)
                    
            ttfont._max_ascender = max_ascender
            ttfont._max_descender = max_descender
            ttfont._max_tile_width = max_tile_width
            ttfont._max_tile_height = max_ascender+max_descender

        for ttfont in cls.getLoadedFonts():        
            if ttfont._background_swatch is None:
                ttfont._createBackgroundTexture()

        cls._glyphs_loaded=True
        
    @classmethod
    def _createBackgroundTexture(cls):
        max_width,max_height=0,0
        for font_label, ttfont in cls._loaded_fonts.iteritems():
            max_width=max(ttfont._max_tile_width,max_width)            
            max_height=max(ttfont._max_tile_height,max_height)
        
        region=TTFont._texture_atlas.get_region(max_width,max_height)
        x,y,w,h=region
        if x<0:
            raise u"Font background_swatch could not find texture Atlas space: {1},{2}".format(max_width,max_height)
        
        u0     = (x)/float(TTFont._texture_atlas.width)
        v0     = (y)/float(TTFont._texture_atlas.height)
        u1     = (x + w)/float(TTFont._texture_atlas.width)
        v1     = (y + h)/float(TTFont._texture_atlas.height)

        texcoords = (u0,v0,u1,v1)

        TTFont._background_swatch=texcoords
        bswatch=numpy.ones((h,w,1),dtype=numpy.ubyte)
        bswatch*=255
        TTFont._texture_atlas.set_region(region,bswatch)  

    def _free(self):
        self._glyphs_loaded=False
        del self._loaded_fonts[self.getLabel()]
        self._label=None
        self._charcode2glyph.clear()
        
        if len(self._loaded_fonts)==0:
            TTFont._texture_atlas.deleteTexture()
            del TTFont._texture_atlas
            del TTFont._font_dirs

    def __del__(self):
        if self._label is not None:        
            self._free()
        
    @staticmethod
    def getFreeTypeVersion():
        return version()

