# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 02:18:38 2013

@author: Sol
"""
import os

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

class FontGlyphData(tb.IsDescription):
    index      = tb.IntCol(pos=1)  
    charcode  = tb.IntCol(pos=2)  
    unichar  = tb.StringCol(8,pos=3)     
    offset_x  = tb.Int16Col(pos=4)   
    offset_y  = tb.Int16Col(pos=5)    
    width    = tb.UInt8Col(pos=6)    
    height    = tb.UInt8Col(pos=7)     
    atlas_x    = tb.UInt16Col(pos=8)
    atlas_y    = tb.UInt16Col(pos=9) 
    atlas_w    = tb.UInt16Col(pos=10)
    atlas_h    = tb.UInt16Col(pos=11) 
    tex_x1  = tb.Float32Col(pos=12)
    tex_y1  = tb.Float32Col(pos=13)
    tex_x2  = tb.Float32Col(pos=14)
    tex_y2  = tb.Float32Col(pos=15)
                    
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
            
            # Create a group for this font size, dpi combo.
            font_size_group=None
            for a in self._tables.list_nodes(style_group.sizes, classname='Group'):
                if a._v_attrs.TITLE=="%d PT, %d DPI Data"%(size,dpi):
                    font_size_group=a
                    break
            
            if font_size_group is None:
                font_size_group=self._tables.create_group(style_group.sizes, "D_%d_%d"%(size,dpi), "%d PT, %d DPI Data"%(size,dpi))

                #Save some atlas info for later use..
                font_size_group._v_attrs['max_ascender']=font_atlas.max_ascender
                font_size_group._v_attrs['max_descender']=font_atlas.max_descender
                font_size_group._v_attrs['max_tile_width']=font_atlas.max_tile_width
                font_size_group._v_attrs['max_tile_height']=font_atlas.max_tile_height
                font_size_group._v_attrs['max_bitmap_size']=font_atlas.max_bitmap_size
                font_size_group._v_attrs['total_bitmap_area']=font_atlas.total_bitmap_area
        
                # create 2d array to store the fontatlas bitmap data in.
                atlas_bmp=tb.Array(font_size_group, "FontGlyphAtlas", obj=font_atlas.atlas.data, title='Array Holding the Font Face Glyph Bitmaps')
                
                # Save the info for each glyph so atlas data array and glyph 
                # location can be used to generate display lists when the font
                # store is retrieved.


                chr_glyph_table = self._tables.create_table(font_size_group, 'UnicharGlyphData', FontGlyphData, "Data regarding one char/glyph within the font set.",expectedrows = 400)                
                tdata=[]
                for charcode,gfinfo in font_atlas.charcode2glyph.iteritems():
                    x,y,w,h=gfinfo['atlas_coords']
                    x1,y1,x2,y2 = gfinfo['texcoords']
                    tdata.append((gfinfo['index'], 
                                  charcode,
                                 gfinfo['unichar'].encode('utf-8'),
                                 gfinfo['offset'][0],
                                 gfinfo['offset'][1],
                                 gfinfo['size'][0],
                                 gfinfo['size'][1],
                                 x,y,w,h,
                                 x1,y1,x2,y2))
                chr_glyph_table.append(tdata)
                chr_glyph_table.flush()
            else:
                print 'Font Size Group already exists!!','%d pt, %d dpi'%(size,dpi)
            
    def __del__(self):
        if self._tables:
            self._tables.flush()
            self._tables.close()
            self._tables=None