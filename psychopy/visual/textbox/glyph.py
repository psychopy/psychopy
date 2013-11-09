# -*- coding: utf-8 -*-
"""
Created on Tue May 28 23:49:38 2013

@author: Sol
"""
from pyglet.gl import (glGenLists,glNewList,glTranslatef,glColor4f,glBegin,glEndList,
               glDeleteLists,GL_COMPILE,glEnd,GL_QUADS,glTexCoord2f,glVertex2f)
from weakref import proxy

class Glyph(object):
    def __init__(self,gindex,charcode,uchar,size, offset, advance, texcoords,region):
        self.gindex=gindex
        self.charcode=charcode
        self.uchar=uchar
        self.size=size
        self.offset=offset
        self.advance=advance
        self.texcoords=texcoords
        self.atlas_region=region
   
class GlyphSet(object):
    loaded_glyph_sets=dict()
    def __init__(self,ttfont,font_color,background_color):
        self._label=self.getNameFromValues(ttfont.getLabel(),font_color,background_color)
        self._font=proxy(ttfont)
        self._background_color = background_color
        self._font_color = font_color
        
        # this gets set later..
        self.max_tile_sizes=[]
        # keys = max tile sizes, values dict of unichr keys, values = display list id
        #
        self._display_lists=dict()

    def getFont(self):
        return self._font

    def getLabel(self):
        return self._label
    
    @staticmethod
    def getNameFromValues(ttfont_label,font_color,background_color):
        return "{font_label}_{font_color}_{background_color}".format(
                                    font_label=ttfont_label,
                                    font_color=font_color,
                                    background_color=background_color)
    @classmethod    
    def createCached(cls,ttfont,font_color,background_color,org_color_info):
        gs_label=cls.getNameFromValues(ttfont.getLabel(),font_color,background_color)
        if gs_label in GlyphSet.loaded_glyph_sets:
            return GlyphSet.loaded_glyph_sets[gs_label]
        else:
            gs=GlyphSet(ttfont,font_color,background_color)
            gs._org_color_info=org_color_info
            GlyphSet.loaded_glyph_sets[gs_label]=gs
            return gs

    @classmethod 
    def getCache(cls):
        GlyphSet.loaded_glyph_sets
        
    def removeFromCache(self):
        del GlyphSet.loaded_glyph_sets[self.getLabel()]

    def createDisplayListsForMaxTileSizes(self):
            for ts in self.max_tile_sizes:
                if ts in self._display_lists:
                    pass
                else:
                    self._display_lists[ts]=self._createDisplayLists(ts)
                     
    def _createDisplayLists(self,max_tile_size):
        if self._font:
            bx1,by1,bx2,by2=self._font._background_swatch
            glyph_count=self._font.getGlyphCount()
            base = glGenLists(glyph_count)      
            space_code=None            
            max_tile_width,max_tile_height=max_tile_size
            display_lists_for_chars={}
            
            for i,(charcode,glyph) in enumerate(self._font._charcode2glyph.iteritems()):
                dl_index=base+i
                uchar=unichr(charcode)                
                if uchar == u' ':
                    space_code=charcode                
                cell_color=self._background_color
                font_color=self._font_color 
                gx1,gy1,gx2,gy2=glyph.texcoords               
 
                hdiff=(max_tile_height-self._font._max_tile_height)/2.0
                wdiff=(max_tile_width-self._font._max_tile_width)/2.0
 
                glNewList(dl_index, GL_COMPILE)           
                if cell_color:
                    glColor4f(*cell_color)                
                    glBegin( GL_QUADS )
                    glTexCoord2f( bx1, by2 ),    glVertex2f( 0,-max_tile_height)#glyph.size[1] )
                    glTexCoord2f( bx1, by1 ),    glVertex2f( 0,0 )
                    glTexCoord2f( bx2, by1 ),    glVertex2f( max_tile_width,0)#glyph.size[0],0 )
                    glTexCoord2f( bx2, by2 ),    glVertex2f( max_tile_width, -max_tile_height)#glyph.size[0],glyph.size[1] )
                    glEnd()        
                if uchar != u' ':
                    glColor4f(*font_color)  
                    glBegin( GL_QUADS )
                    x1 = glyph.offset[0]
                    x2 = x1+glyph.size[0]
                    x1+=wdiff
                    x2+=wdiff
                    y1=(self._font._max_ascender-glyph.offset[1])                 
                    y2=y1+glyph.size[1]
                    y1+=hdiff
                    y2+=hdiff         
                    
                    glTexCoord2f( gx1, gy2 ),    glVertex2f( x1,-y2 )
                    glTexCoord2f( gx1, gy1 ),    glVertex2f( x1,-y1 )
                    glTexCoord2f( gx2, gy1 ),    glVertex2f( x2,-y1 )
                    glTexCoord2f( gx2, gy2 ),    glVertex2f( x2,-y2 )
                    glEnd( )        
                glTranslatef( max_tile_width,0,0)                
                glEndList( )
                display_lists_for_chars[charcode]=dl_index
            
            if space_code and ord(u'\n') not in display_lists_for_chars:
                display_lists_for_chars[ord(u'\n')]=display_lists_for_chars[space_code]
                i=i+1
            return display_lists_for_chars
            
    def _free(self):
        del self._font
        del GlyphSet.loaded_glyph_sets[self._label]
        self._label=None
        for dlists in self._display_lists:
            for dl in dlists:
                glDeleteLists(dl, 1)
            del dlists
        self._display_lists.clear()
        if len(GlyphSet.loaded_glyph_sets)==0:
           for f in TTFont._loaded_fonts.values():
               f._free()
           TTFont._loaded_fonts.clear()
           
    def __del__(self):
        if self._label is not None:
            self._free()

from font import TTFont            

    