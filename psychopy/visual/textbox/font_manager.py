# -*- coding: utf-8 -*-
"""
Created on Sun Nov 10 12:18:45 2013

@author: Sol
"""
import os,math
import numpy as np
from psychopy.core import getTime
from psychopy import logging
from textureAtlas import TextureAtlas       

from pyglet.gl import (glGenLists,glNewList,GL_COMPILE,GL_QUADS,
                      glBegin,glTexCoord2f,glVertex2f,glEnd,glDeleteLists,
                      glEndList,glTranslatef,glPopMatrix,glPushMatrix
                       )
import pprint

global have_tables
try:
    import tables as tb
    have_tables=True
    
    def my_close_open_files(verbose):
        open_files = tb.file._open_files
        are_open_files = len(open_files) > 0
        if verbose and are_open_files:
            print >> sys.stderr, "Closing remaining open files:",
        for fileh in open_files.keys():
            if verbose:
                print >> sys.stderr, "%s..." % (open_files[fileh].filename,),
            open_files[fileh].close()
            if verbose:
                print >> sys.stderr, "done",
        if verbose and are_open_files:
            print >> sys.stderr
    
    import sys, atexit
    atexit.register(my_close_open_files, False)
    
except:
    print 'Error importing pytables. FontStore will not be supported.'
    have_tables=False
    
log=math.log
ceil=math.ceil

def nearestPow2(n):
    return pow(2, int(log(n, 2) + 0.5))

def nextPow2(n):
    return int(pow(2, ceil(log(n, 2))))

class FontStore(object):
    def __init__(self,file_path=None):
        self.file_path=file_path
        if have_tables is False:
            raise Exception("FontStore requires pytables package to be available.")
        
        if self.file_path is None:
            self.file_path=os.path.join(os.getcwd(),'fontstore.hdf5')
        self._tables=None
        self.open()
        
    def open(self):
        """
        Open the FontStore HDF5 file located at self.file_path
        """
        fs_filter = tb.Filters(complevel=1, complib='blosc', fletcher32=True)
        self._tables=tb.open_file(self.file_path, mode = "a", title = "PsychoPy Font Store",filter=fs_filter)
    
    def getStoredFontNames(self):
        """
        """
        pass
    
    def getFamilyGroup(self,family_name):
        group=None
        family_group_name=family_name.replace(u' ','_')
        for g in self._tables.list_nodes("/",classname='Group'):
            if g._v_attrs.TITLE==family_name:
                group=g
                break        
        if group is None:
            group = self._tables.create_group(self._tables.root,family_group_name, family_name)        
        return group

    def getStyleGroup(self,font_atlas,family_group):
        group=None
        style_name=font_atlas.font_info.style_name
        for g in self._tables.list_nodes(family_group, classname='Group'):
            if g._v_attrs.TITLE==style_name:
                group=g
                break        
        if group is None:
            group = self.createFontStyleGroup(font_atlas,family_group)
            
            # Add some font info used when recreating display lists.
            #
            
            self._tables.flush()
        return group

    def createFontStyleGroup(self,font_atlas,family_group):
        style_name=font_atlas.font_info.style_name      
        style_group_name=style_name.replace(u' ','_')        
        group = self._tables.create_group(family_group,style_group_name, style_name)    

        # add font info useful for re-creating display lists.
        for k,v in font_atlas.font_info.asdict().iteritems():
            group._v_attrs[k]=v

        self._tables.create_group(group, "sizes", "Glyph Data for different Font Sizes")
        return group
        
    def addFontAtlas(self,font_atlas):
        style_group=None
        family_group=self.getFamilyGroup(font_atlas.font_info.family_name)
        if family_group:
            style_group=self.getStyleGroup(font_atlas,family_group)  
        if style_group:
            size=font_atlas.size
            dpi=font_atlas.dpi        
            
            
            # save the original font file to the hdf5 file
            ttf_file_name=os.path.split(font_atlas.font_info.path)[-1]
            ttf_node_name=ttf_file_name.replace(u'.',u'_')
            try:
                ttf_exists=style_group._f_get_child(ttf_node_name) 
            except tb.NoSuchNodeError,e:
                import tables
                from tables.nodes import filenode
                f=file(font_atlas.font_info.path,'rb')                
                ttf_node=filenode.new_node(self._tables, where=style_group,name=ttf_node_name,title=ttf_file_name)
                ttf_node.write(f.read())
                f.close()
                ttf_node.close()
            
            # create 2d array to store the fontatlas bitmap data in.
            atlas_bmp=None
            for a in self._tables.list_nodes(style_group.sizes, classname='Array'):
                if a._v_attrs.TITLE=="%d pt, %d dpi"%(size,dpi):
                    atlas_bmp=a
            if atlas_bmp is None:
                atlas_bmp=tb.Array(style_group.sizes, "A_%d_%d"%(size,dpi), obj=font_atlas.atlas.data, title='%d pt, %d dpi'%(size,dpi))    
            
    def __del__(self):
        if self._tables:
            self._tables.flush()
            self._tables.close()
            self._tables=None
        
class SystemFontManager(object):
    """
    SystemFontManager provides a simple API for finding, loading, and creating
    OpenGL based glyph graphics for font files supported by the FreeType lib.
    
    The SystemFontManager finds supported font files on the computer and
    initially creates a dictionary containing the information about 
    available fonts. This can be used to quickly determine what font family 
    names are available on the computer and what styles (bold, italic) are
    supported for each family.
    
    When the font glyph set is needed in a form that can be used within OpenGL,
    SystemFontManager can be used to get a FontAtlas object based on the
    requested family anme, style, font size, and dpi. 
    
    A FontAtlas object creates an OpenGL texture for the glyph set requested,
    drawn based on the size and dpi information provided. An OpenGL display
    list is created for each glyph which will run the appropriate function
    calls to have the glyph for the requested character to be drawn at the
    current pointer position.
    
    """
    freetype_import_error=None
    font_atlas_dict={}
    font_family_styles=[]
    _available_font_info={}
    font_store=None
    def __init__(self,monospace_only=True):
        if SystemFontManager.freetype_import_error:
            raise Exception('Appears the freetype library could not load. Error: %s'%(str(SystemFontManager.freetype_import_error)))
 
        self.load_monospace_only=monospace_only
        self.updateFontInfo(monospace_only)
        #self.enableFontStore()        

    def enableFontStore(self,path=None):
        SystemFontManager.font_store=FontStore(path)
        
    def getFontFamilyNames(self):
        """
        Returns a list of the available font family names
        """
        return self._available_font_info.keys()

    def getFontStylesForFamily(self,family_name):
        """
        For the given family_name, a list of style names supported is returned.
        """
        style_dict= self._available_font_info.get(family_name)
        if style_dict:
            return style_dict.keys()

    def getFontFamilyStyles(self):
        """
        Returns a list where each element of the list is a itself a two element
        list of [font_family_name,[font_style_names_list]]
        """
        return self.font_family_styles

    def getFontInfo(self,refresh=False,monospace=True):
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

    def getFontsMatching(self,font_family_name,bold=False,italic=False,font_style=None):
        """
        Returns the list of FontInfo instances that match the provided
        font_family_name and style information. If no matching fonts are
        found, None is returned.
        """
        style_dict=self._available_font_info.get(font_family_name)
        if style_dict is None:
            return None
        if font_style and font_style in style_dict.keys():
            return style_dict[font_style]
        for style,fonts in style_dict.iteritems():
            b,i=self.booleansFromStyleName(style)
            if b==bold and i==italic:
                return fonts
        return None

    @staticmethod
    def getGLFont(font_family_name,size=32,bold=False,italic=False,dpi=72):
        """
        Return a FontAtlas object that matches the family name, style info,
        and size provided. FontAtlas objects are cached, so if multiple
        TextBox instances use the same font (with matching font properties)
        then the existing FontAtlas is returned. Otherwise, a new FontAtlas is 
        created , added to the cache, and returned.
        """
#        stime=getTime()
        from psychopy.visual.textbox import getFontManager
        fm=getFontManager()

        if fm:
            if fm.font_store:
                # should be loading from font store if requested font settings
                # have been saved to the hdf5 file (assuming it is faster)
                pass
                #print "TODO: Check if requested font is in FontStore"
#            t1=getTime()    
            font_infos=fm.getFontsMatching(font_family_name,bold,italic)
            if len(font_infos) == 0:
                return False
            font_info=font_infos[0]   
            fid=MonospaceFontAtlas.getIdFromArgs(font_info,size,dpi)
            font_atlas=fm.font_atlas_dict.get(fid)
#            t2=getTime() 
            if font_atlas is None:
                font_atlas=fm.font_atlas_dict.setdefault(fid,MonospaceFontAtlas(font_info,size,dpi))
                font_atlas.createFontAtlas()
#            t3=getTime() 
            if fm.font_store:
                fm.font_store.addFontAtlas(font_atlas)

#        etime=getTime()
#        print 'getGLFont:',t2-t1,t3-t2,t3-t1
        return font_atlas
        
    def updateFontInfo(self,monospace_only=True):
        self._available_font_info.clear()
        del self.font_family_styles[:]
        import matplotlib.font_manager as font_manager    
        font_paths=font_manager.findSystemFonts()

        def createFontInfo(fp,fface):
            fns=(fface.family_name,fface.style_name)
            if fns in self.font_family_styles:
                pass
            else:
                self.font_family_styles.append((fface.family_name,fface.style_name))
            
            styles_for_font_dict=self._available_font_info.setdefault(fface.family_name,{})
            fonts_for_style=styles_for_font_dict.setdefault(fface.style_name,[])
            fi=FontInfo(fp,fface)
            fonts_for_style.append(fi)
            
        for fp in  font_paths:
            if os.path.isfile(fp) and os.path.exists(fp):
                try:                
                    face=Face(fp)
                    if monospace_only:
                        if face.is_fixed_width:
                            createFontInfo(fp,face)
                    else:
                        createFontInfo(fp,face)
                except Exception, e:
                    logging.debug('Error during FontManager.updateFontInfo(): %s\nFont File: %s'%(str(e),fp))

        self.font_family_styles.sort() 
               
    def booleansFromStyleName(self,style):
        """
        For the given style name, return a
        bool indicating if the font is bold, and a second indicating
        if it is italics.
        """
        italic=False
        bold=False
        s=style.lower().strip()
        if s == 'regular':
            return False, False
        if s.find('italic')>=0 or s.find('oblique')>=0:
            italic=True    
        if s.find('bold')>=0:
            bold=True    
        return bold,italic
        
    def __del__(self):
        self.font_store=None       
        if self.font_atlas_dict:
            for fa in self.font_atlas_dict.values():
                if fa:
                    fa.free()
            self.font_atlas_dict.clear()
        if self._available_font_info:    
            self._available_font_info.clear()
        

class FontInfo(object):
    def __init__(self,fp,face):
        self.path=fp
        self.family_name=face.family_name
        self.style_name=face.style_name
        self.charmaps=[charmap.encoding_name for charmap in face.charmaps]
        self.num_faces=face.num_faces
        #self.size_info= [dict(width=s.width,height=s.height,x_ppem=s.x_ppem,y_ppem=s.y_ppem) for s in face.available_sizes]
        self.units_per_em=face.units_per_EM
        self.monospace=face.is_fixed_width
        self.charmap_id=face.charmap.index
        self.label="%s_%s"%(face.family_name,face.style_name)
        self.id=self.label
        
    def getID(self):
        return self.id
        
    def asdict(self):
        d={}
        for k,v in self.__dict__.iteritems():
            if k[0]!='_':
                d[k]=v
        return d

class MonospaceFontAtlas(object):
    def __init__(self,font_info,size,dpi):
        self.font_info=font_info
        self.size=size
        self.dpi=dpi
        self.id=self.getIdFromArgs(font_info,size,dpi)
        self._face=Face(font_info.path)
        self._face.set_char_size(height=self.size*64,vres=self.dpi)
        
        self.charcode2glyph=None
        self.charcode2unichr=None
        self.charcode2displaylist=None
        self.max_ascender = None
        self.max_descender = None
        self.max_tile_width = None
        self.max_tile_height = None
        self.max_bitmap_size = None
        self.total_bitmap_area=0
        self.atlas=None
    
    def getID(self):
        return self.id

    @staticmethod
    def getIdFromArgs(font_info,size,dpi):
        return "%s_%d_%d"%(font_info.getID(),size,dpi)
    
    def createFontAtlas(self):
        t1=getTime()
        if self.atlas:
            self.atlas.free()
            self.atlas=None
        self.charcode2glyph={}
        self.charcode2unichr={}
        self.max_ascender = None
        self.max_descender = None
        self.max_tile_width = None
        self.max_tile_height = None
        self.max_bitmap_size = None
        self.total_bitmap_area=0
        # load font glyphs and calculate max. char size.
        # This is used when the altas is created to properly size the tex.
        # i.e. max glyph size * num glyphs
        #


        max_w,max_h=0,0
        max_ascender, max_descender, max_tile_width = 0, 0, 0
        face=self._face
        face.set_char_size(height=self.size*64,vres=self.dpi)

        # Create texAtlas for glyph set.
        x_ppem=face.size.x_ppem
        y_ppem=face.size.x_ppem
        units_ppem=self.font_info.units_per_em
        est_max_width=(face.bbox.xMax-face.bbox.xMin)/float(units_ppem)*x_ppem
        est_max_height=face.size.ascender/float(units_ppem)*y_ppem
        target_atlas_area=int(est_max_width*est_max_height)*face.num_glyphs
        pow2_area=nextPow2(target_atlas_area)
        atlas_width=2048
        atlas_height=pow2_area/atlas_width
        t2=getTime()        
        self.atlas=TextureAtlas(atlas_width,atlas_height)
        t3=getTime()  
        charcode, gindex=face.get_first_char()
        while gindex:        
            uchar=self.charcode2unichr.setdefault(charcode,unichr(charcode))

            face.load_char(uchar, FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
            bitmap = face.glyph.bitmap      
            
            self.total_bitmap_area+=bitmap.width*bitmap.rows
            max_ascender = max( max_ascender, face.glyph.bitmap_top)
            max_descender = max( max_descender, bitmap.rows - face.glyph.bitmap_top )
            max_tile_width = max( max_tile_width,bitmap.width)
            max_w=max(bitmap.width,max_w)
            max_h=max(bitmap.rows,max_h)

            x,y,w,h = self.atlas.get_region(bitmap.width+2, bitmap.rows+2)
            
            #glyphdata['atlas_region']=x,y,w,h
            if x < 0:
                raise Exception("MonospaceFontAtlas.get_region failed for: {0}, requested area: {1}. Atlas Full!".format(charcode,(bitmap.width+2, bitmap.rows+2)))              
            x,y = x+1, y+1
            w,h = w-2, h-2
            #print 'bitmap.width,bitmap.rows,bitmap.pitch : h,w:',bitmap.width,bitmap.rows,bitmap.pitch,h,w
            data = np.array(bitmap._FT_Bitmap.buffer[:(bitmap.rows*bitmap.width)],dtype=np.ubyte).reshape(h,w,1)
            #gamma = 1.0
            #Z = ((data/255.0)**(gamma))
            #data = (Z*255).astype(np.ubyte)
            self.atlas.set_region((x,y,w,h), data)
            
#            u0     = (x +     0.0)
#            v0     = (y +     0.0)
#            u1     = (x + w - 0.0)
#            v1     = (y + h - 0.0)

            self.charcode2glyph[charcode]=dict(
                        offset=(face.glyph.bitmap_left,face.glyph.bitmap_top),
                        size=(w,h),
                        texcoords = [x, y, x + w, y + h]
                        )
            
            charcode, gindex = face.get_next_char(charcode, gindex)
        t4=getTime()          
        self.max_ascender = max_ascender
        self.max_descender = max_descender
        self.max_tile_width = max_tile_width
        self.max_tile_height = max_ascender+max_descender
        self.max_bitmap_size=max_w,max_h

        # resize atlas
        height=nextPow2(self.atlas.max_y+1)
        self.atlas.resize(height)
        self.atlas.upload()        
        t5=getTime()  
        self.createDisplayLists()
        t6=getTime()
        
#        print "Creating Atlas Times:"
#        print "\tDetermine size",t2-t1
#        print "\tCreating Atlas",t3-t2
#        print "\tCreate bitmap glyphs",t4-t3
#        print "\tResize+Upload",t5-t4
#        print "\tMake DLs:",t6-t5
#        print "\tTotal:",t6-t1
        self._face=None
       #self.atlas.freeMemoryBuffer()
   
    def createDisplayLists(self):
        glyph_count=len(self.charcode2unichr)
        max_tile_width,max_tile_height=self.max_tile_width,self.max_tile_height        
        display_lists_for_chars={}
        
        base = glGenLists(glyph_count)               
        for i,(charcode,glyph) in enumerate( self.charcode2glyph.iteritems()):
            dl_index=base+i
            uchar=self.charcode2unichr[charcode]                

            # update tex coords to reflect earlier resize of atlas height.            
            gx1,gy1,gx2,gy2=glyph['texcoords']             
            gx1=gx1/float(self.atlas.width)
            gy1=gy1/float(self.atlas.height)
            gx2=gx2/float(self.atlas.width)
            gy2=gy2/float(self.atlas.height)
            glyph['texcoords'] =[gx1,gy1,gx2,gy2]
            
            glNewList(dl_index, GL_COMPILE)           
            if uchar not in [u'\t',u'\n']:               
                glBegin( GL_QUADS )
                x1 = glyph['offset'][0]
                x2 = x1+glyph['size'][0]
                y1=(self.max_ascender-glyph['offset'][1])                 
                y2=y1+glyph['size'][1]
                
                glTexCoord2f( gx1, gy2 ),    glVertex2f( x1,-y2 )
                glTexCoord2f( gx1, gy1 ),    glVertex2f( x1,-y1 )
                glTexCoord2f( gx2, gy1 ),    glVertex2f( x2,-y1 )
                glTexCoord2f( gx2, gy2 ),    glVertex2f( x2,-y2 )
                glEnd( )        
                glTranslatef( max_tile_width,0,0)                    
            glEndList( )

            display_lists_for_chars[charcode]=dl_index
        
        self.charcode2displaylist=display_lists_for_chars

    def saveGlyphBitmap(self,file_name=None):
        if file_name is None:
            import os
            #print 'CWD:',os.getcwd()
            file_name=os.path.join(os.getcwd(),self.getID().lower().replace(u' ',u'_')+'.png')
        from scipy import misc
        if self.atlas is None:
            self.loadAtlas()
        if self.atlas.depth==1:    
            misc.imsave(file_name, self.atlas.data.reshape(self.atlas.data.shape[:2]))
        else:
            misc.imsave(file_name, self.atlas.data)
    
    def free(self):
        if self.atlas:
            self.atlas.free()
        if self.charcode2displaylist:
            for dl in self.charcode2displaylist.values():
                glDeleteLists(dl, 1)
        
    def __del__(self):   
        self.free()
        self._face=None
        if self.charcode2glyph:    
            self.charcode2glyph.clear()
        if self.charcode2unichr:
            self.charcode2unichr.clear()

        
try:
    from psychopy.visual.textbox.freetype_bf import Face,FT_LOAD_RENDER,FT_LOAD_FORCE_AUTOHINT 
except Exception, e:
    SystemFontManager.freetype_import_error=e
