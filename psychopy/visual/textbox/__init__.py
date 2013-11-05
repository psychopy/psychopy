# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:38:35 2013

@author: Sol
"""
import os,inspect
from weakref import proxy

import pyglet
pyglet.options['debug_gl'] = False
gl=pyglet.gl

from psychopy import core,misc
from textGrid import TextGrid
from glyph import GlyphSet
from font import TTFont
from textRegions import TextRegionType

def getTime():
    return core.getTime()

        
class TextBox(object):
    _textbox_instances={}
    _font_stim_cache={}
    _font_stim_cache_created=False
    _te_glyph_set_label_to_max_size=None
    _active_font_stim_glyphs_info=dict(
                                label='textbox_active_font_stim',
                                file_name='VeraMono.ttf',
                                font_size=14,
                                dpi=72,
                                font_color=[0,0,0,1],
                                font_background_color=None
                                )
    _active_font_stim_glyphs=None       
    def __init__(self, 
                 window=None,
                 label=None, 
                 font_stim_label=None, 
                 text='Default Test Text.', 
                 font_file_name=None, 
                 font_size=32,
                 dpi=72, 
                 font_color=[0,0,0,1], 
                 font_background_color=None,
                 line_spacing=None,
                 line_spacing_units=None,
                 background_color=None,
                 border_color=None,
                 border_stroke_width=1,
                 size=None,
                 pos=(0.0,0.0), 
                 align_horz='center',
                 align_vert='center',
                 units=None,  
                 grid_color=None,
                 grid_stroke_width=1,
                 grid_horz_justification='left',
                 grid_vert_justification='top'
                 ):
        self._window=window  
        self._text=text
        self._set_text=True
        self._label=label
        self._line_spacing=line_spacing
        self._line_spacing_units=line_spacing_units
        self._border_color=border_color
        self._border_stroke_width=border_stroke_width 
        self._background_color=background_color        
        self._grid_color=grid_color
        self._grid_stroke_width=grid_stroke_width
        self._grid_horz_justification=grid_horz_justification
        self._grid_vert_justification=grid_vert_justification
        self._align_horz=align_horz
        self._align_vert=align_vert      
        self._size=size
        self._position=pos
        self._units=units

        self._display_list=None
        self._pixel_line_spacing=0
        self._glyph_set_max_tile_sizes=None
        self._alignment=align_horz,align_vert    
        self._top_left_gl=None
        self._active_font_stim=None
        self._text_grid=None
        self._font_stims={}
        self._glyph_sets_to_convert={}
        
        self._setActiveFontStimFromArgs(font_stim_label,font_file_name,font_size,dpi,font_color,font_background_color)
                
        self.setUnits(self._units)
            
        self.setPosition(self._position)
        self.setSize(self._size)
        
        self._textbox_instances[self.getLabel()]=proxy(self)
        
    def getWindow(self):
        return self._window

    def getLabel(self):
        return self._label

    def getText(self):
        return self._text

    def setText(self,text_source):
        self._text=text_source
        self._set_text=True
        #self._reset()
        
    def getUnits(self):
        return self._units

    def setUnits(self,units):
        if units is None:
            self._units=self._window.units
        else:
            self._units=units
            
    def getPosition(self):
        return self._position

    def setPosition(self,pos):            
        self._position=pos
        
    def getSize(self):
        return self._size

    def setSize(self,size):
        self._size=size

    @staticmethod
    def getFontSearchDirectories():
        return TTFont.getSearchDirectories()

    @staticmethod
    def addFontSearchDirectories(*font_dir_list):
        return TTFont.addSearchDirectories(*font_dir_list)
            
    @staticmethod
    def removeFontSearchDirectories(*font_dir_list):
        return TTFont.removeSearchDirectories(*font_dir_list)

    @staticmethod
    def createCachedFontStim(font_stim_label,file_name,font_size=24,dpi=72,font_color=[0,0,0,1],font_background_color=None):
        gs=GlyphSet.createCached(TTFont.load(file_name,font_size,dpi),font_color,font_background_color)
        return TextBox._font_stim_cache.setdefault(font_stim_label,proxy(gs))

    def addFontStim(self,font_stim_label,file_name=None,size=24,dpi=72,font_color=[0,0,0,1],background_color=None): 
        fs=self._font_stims.get(font_stim_label)
        if fs:
            return font_stim_label,fs.getGlyphSet()

        gs=TextBox._font_stim_cache.get(font_stim_label)
        if gs:
            self._glyph_sets_to_convert[font_stim_label]=gs
            return font_stim_label,gs

        if file_name:
            gs=TextBox.createCachedFontStim(font_stim_label,file_name,size,dpi,font_color,background_color)
            if gs:
                self._glyph_sets_to_convert[font_stim_label]=gs
                return font_stim_label,gs

    @staticmethod
    def deleteFontStim(font_stim_label):
        print '** TODO: deleteFontStim: destroy all objects associated with font stim.'
        gs=TextBox._font_stim_cache.get(font_stim_label)
        if gs:
            del TextBox._font_stim_cache[font_stim_label]
            for tb in TextBox._textbox_instances:                
                tb.removeFontStim(font_stim_label)
        del gs
    
    def removeFontStim(self,font_stim_label):
        tbfs=self._font_stims.get(font_stim_label)
        if tbfs:
            del self._font_stims[font_stim_label]
            tbfs.clearRegions()
            del tbfs

    def setActiveFontStim(self,font_stim_label):
        if font_stim_label and font_stim_label in self._font_stims.keys():
            self._active_font_stim=self._font_stims.get(font_stim_label)
            if self._text_grid:
                self._text_grid.setDefaultDisplayListsLabel(font_stim_label)

    def getMaxTextCellSize(self):
        return self._glyph_set_max_tile_sizes[self._active_font_stim.getGlyphSet().getLabel()]

    def getAlignment(self):
        return self._alignment
    
    def draw(self):              
        self._buildResourcesIfNeeded()
        
        self._resetPygletCompatState()                             
        gl.glPushMatrix()
        t,l=self._getTopLeftPixPos()
        gl.glTranslatef(t,l, 0 ) 
        gl.glCallList(self._getDisplayList())            
        self._text_grid.draw()    
        gl.glPopMatrix()        
        self._resetPsychoPyWindow(self._window.rgb,self._window.colorSpace)                 
        gl.glFinish()

    def _getGlyphSets(self):
        gs_dict={}
        for k,v in self._font_stims.iteritems():
            gs_dict[k]=v.getGlyphSet()
        for k,v in self._glyph_sets_to_convert.iteritems():
            gs_dict[k]=v
        return gs_dict
    
    def _setActiveFontStimFromArgs(self,font_stim_label=None,font_file_name=None,font_size=None,dpi=None,font_color=None,font_background_color=None):
        if font_stim_label:
            if self._font_stims.get(font_stim_label):
                self._active_font_stim=self._font_stims.get(font_stim_label)                
            elif self._font_stim_cache.get(font_stim_label):
                self._active_font_stim=self.addFontStim(font_stim_label=font_stim_label)             
        if self._active_font_stim is None and font_file_name:
                # create new font stim using TextBox args
                self._active_font_stim=self.addFontStim(font_stim_label,font_file_name,font_size,dpi,font_color,font_background_color)
                    
        if self._active_font_stim is None:
                self._active_font_stim=self.addFontStim(self._active_font_stim_glyphs_info.get('label'))
                
    @classmethod
    def _createDefaultFontGlyphs(cls):
        if cls._active_font_stim_glyphs is None:
            label=cls._active_font_stim_glyphs_info['label']
            file_name=cls._active_font_stim_glyphs_info['file_name']
            size=cls._active_font_stim_glyphs_info['font_size']
            dpi=cls._active_font_stim_glyphs_info['dpi']
            font_color=cls._active_font_stim_glyphs_info['font_color']
            background_color=cls._active_font_stim_glyphs_info['font_background_color']
            cls._active_font_stim_glyphs=cls.createCachedFontStim(
                            label,file_name,
                            size,dpi,font_color,
                            background_color)                

    def _buildFontGlyphStim(self):            
        if TTFont._glyphs_loaded is False:
            TTFont._loadGlyphs()

        TextBox._te_glyph_set_label_to_max_size={}

        TTFont.getTextureAtlas().upload()
             
        #
        ########################################
    
        #Preparse Text Editors to determine glyph label sets
        # which in turn determines the max tile size conbinations
        #
        for te_name, te in TextBox._textbox_instances.iteritems():   
            te_glyph_sets=te._getGlyphSets().values()
                        
            # calculate max tile size for each text editor instance, and set the value in the Glyph Set
            TextBox._te_glyph_set_label_to_max_size[te_name]={}
            
            max_width=0
            max_height=0            
            for gs in te_glyph_sets:
                max_width=max(gs._font._max_tile_width,max_width)
                max_height=max(gs._font._max_tile_height,max_height)

            for gs in te_glyph_sets:
                gs.max_tile_sizes.append((max_width,max_height))
                TextBox._te_glyph_set_label_to_max_size[te_name][gs.getLabel()]=(max_width,max_height)
   
        ###
   
        self._glyph_set_max_tile_sizes=self._te_glyph_set_label_to_max_size[self._label]

        for gs_label,gs in GlyphSet.loaded_glyph_sets.iteritems():
            gs.createDisplayListsForMaxTileSizes()

        ###

        if isinstance(self._active_font_stim,(list,tuple)):
            font_stim_label,gs=self._active_font_stim
            fs=TextRegionType(self,gs)
            self._font_stims.setdefault(font_stim_label,fs)
            self._active_font_stim=fs
            if self._glyph_sets_to_convert.get(font_stim_label):
                del self._glyph_sets_to_convert[font_stim_label]    
            
        ###

        for font_stim_label,gs in self._glyph_sets_to_convert.iteritems():#[font_stim_label]=gs
            self._font_stims.setdefault(font_stim_label,TextRegionType(self,gs))
        self._glyph_sets_to_convert.clear()
        
        
    def _reset(self):
        self._text_grid.reset()                       

    def _getPixelSize(self):
        units=self.getUnits()
        w,h=self.getSize()
        
        if units in ['deg','degs']:
            w=misc.deg2pix(w,self._window.monitor)                        
            h=misc.deg2pix(h,self._window.monitor)  
        elif units in ['cm',]:
            w=misc.cm2pix(w,self._window.monitor)                        
            h=misc.cm2pix(h,self._window.monitor)  
        elif units in ['norm']:
            print 'ERROR: TextBox._getPixelSize: norm unit type not yet supported'                      
        return int(w),int(h)
     
    def _getPixelPosition(self):
        units=self.getUnits()
        x,y=self.getPosition()
        
        if units in ['deg','degs']:
            x=misc.deg2pix(x,self._window.monitor)                        
            y=misc.deg2pix(y,self._window.monitor)  
        elif units in ['cm',]:
            x=misc.cm2pix(x,self._window.monitor)                        
            y=misc.cm2pix(y,self._window.monitor)  
        elif units == 'perc':
            x=self._window.winHandle.screen.width*(x/100.0)-self._window.winHandle.screen.width/2.0
            y=self._window.winHandle.screen.height*(y/100.0)-self._window.winHandle.screen.height/2.0 
            return int(x),int(y)
        elif units in ['norm']:
            print 'ERROR: TextBox._getPixelPosition: norm unit type not yet supported'                      
        return int(x),int(y)

    def _getDisplayList(self):
        if self._display_list is None:
            dl_index = gl.glGenLists(1)        
            gl.glNewList(dl_index, gl.GL_COMPILE)           
    
            border_thickness=self._border_stroke_width
            if self._border_stroke_width is None:
                border_thickness=0
                
            if self._background_color:
                gl.glColor4f(*self._background_color)
                size=self._getPixelSize()
                gl.glRectf(border_thickness,-border_thickness, size[0]-border_thickness,-size[1]+border_thickness)      

            if self._border_color:
                gl.glLineWidth(border_thickness)
                gl.glColor4f(*self._border_color)
                gl.glBegin(gl.GL_LINES)    

                x1=0
                y1=0
                x2=self._size[0]
                y2=-self._size[1]
                
                gl.glVertex2d(x1, y1)             
                gl.glVertex2d(x2, y1)              

                gl.glVertex2d(x2, y1)                 
                gl.glVertex2d(x2, y2)              

                gl.glVertex2d(x2, y2)              
                gl.glVertex2d(x1, y2)                 

                gl.glVertex2d(x1, y2)                 
                gl.glVertex2d(x1, y1)             

                gl.glEnd()    
                        
            gl.glColor4f(0.0,0.0,0.0,1.0)

            gl.glEndList( )
            self._display_list=dl_index
        return self._display_list
    
    def _getDefaultGlyphDisplayListSet(self):
        if self._active_font_stim is None:
            raise AttributeError("_getDefaultGlyphDisplayListSet: default_font_stim can not be None")
        return self._active_font_stim.getGlyphSet()._display_lists[self.getMaxTextCellSize()]
                
    def _getPixelTextLineSpacing(self):
        if self._line_spacing:
            max_size=self.getMaxTextCellSize()
            line_spacing_units=self._line_spacing_units
            line_spacing_height=self._line_spacing
            
            if line_spacing_units in ['pixel','pixels','pix']:
                self._pixel_line_spacing=int(line_spacing_height)
            elif line_spacing_units in ['perc',]:
                self._pixel_line_spacing=int(line_spacing_height*(self.getWindow().winHandle.screen.height*(line_spacing_height/100.0)))
            elif line_spacing_units in ['ratio',]:
                self._pixel_line_spacing=int(line_spacing_height*max_size[1])
        
            return self._pixel_line_spacing
        return 0

                
    def _getPixelBounds(self):
        l,t=self._getTopLeftPixPos()
        w,h=self.getSize()
        r=l+w
        b=t-h
        return l,t,r,b

    def _getTopLeftPixPos(self):
        if self._top_left_gl is None:
            # Create a window position based on the window size, alignment types, 
            #   TextBox size, etc...
            win_w,win_h=self._window.size
            te_w,te_h=self._getPixelSize()
            te_x,te_y=self._getPixelPosition()
            # convert te_x,te_y from psychopy pix coord to gl pix coord
            te_x,te_y= te_x+win_w//2,te_y+win_h//2 
            # convert from alignment to top left
            horz_align,vert_align=self._align_horz,self._align_vert
            if horz_align.lower() == u'center':
                te_x=te_x-te_w//2
            elif horz_align.lower() == u'right':
                te_x=te_x-te_w
            if vert_align.lower() == u'center':
                te_y=te_y+te_h//2
            if vert_align.lower() == u'bottom':
                te_y=te_y+te_h
            self._top_left_gl=te_x,te_y   
        return self._top_left_gl
        
    def _buildResourcesIfNeeded(self):    
        if self._font_stim_cache_created is False:
            print ' ** _buildFontGlyphStim **'
            self._buildFontGlyphStim()
            TextBox._font_stim_cache_created=True
            
        #
        ## Text Editor Glyph Grid Settings
        #
        if self._text_grid is None:
            self._text_grid=TextGrid(self, line_color=self._grid_color, 
                                     line_width=self._grid_stroke_width,
                                     grid_horz_justification=self._grid_horz_justification,
                                     grid_vert_justification=self._grid_vert_justification)
            self._text_grid.configure()
            print ' ** _text_grid.configure() **'

        # Load initial text for textgrid....
        if self._set_text:
            #print ' ** createParsedTextDocument() **'
            if not self._text:                
                self._text=u'\n'
            ptd=self._text_grid.getParsedTextDocument()
            if ptd:
                ptd.deleteText(0,ptd.getTextLength(),self._text)
            else:
                self._text_grid.createParsedTextDocument(self._text)
            self._set_text=False
             
    def _resetPygletCompatState(self):
        gl.glViewport( 0, 0, self._window.winHandle.screen.width,self._window.winHandle.screen.height )
        gl.glMatrixMode( gl.GL_PROJECTION )
        gl.glLoadIdentity()
        gl.glOrtho( 0, self._window.winHandle.screen.width, 0, self._window.winHandle.screen.height, -1, 1 )
        gl.glMatrixMode( gl.GL_MODELVIEW )
        gl.glLoadIdentity()
        gl.glDisable( gl.GL_DEPTH_TEST )
        gl.glEnable( gl.GL_BLEND )
        gl.glEnable( gl.GL_COLOR_MATERIAL )
        gl.glColorMaterial( gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE )
        gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
        
    def _resetPsychoPyWindow(self,rgb,colorSpace):
        #setup screen color
        if colorSpace in ['rgb','dkl','lms','hsv']: #these spaces are 0-centred
            desiredRGB = (rgb+1)/2.0#RGB in range 0:1 and scaled for contrast
        else:
            desiredRGB = rgb/255.0

        gl.glClearColor(desiredRGB[0],desiredRGB[1],desiredRGB[2], 1.0)
        gl.glViewport(0, 0, int(self._window.winHandle.screen.width), int(self._window.winHandle.screen.height))

        gl.glMatrixMode(gl.GL_PROJECTION) # Reset The Projection Matrix
        gl.glLoadIdentity()
        gl.gluOrtho2D(-1,1,-1,1)

        gl.glMatrixMode(gl.GL_MODELVIEW)# Reset The Projection Matrix
        gl.glLoadIdentity()

def _module_directory(local_function):
    mp=os.path.abspath(inspect.getsourcefile(local_function))
    moduleDirectory,mname=os.path.split(mp)
    return moduleDirectory
        
_THIS_DIR=_module_directory(getTime)    
TTFont.addSearchDirectories(os.path.join(_THIS_DIR,'fonts'))

if TextBox._active_font_stim_glyphs is None:
    TextBox._createDefaultFontGlyphs()