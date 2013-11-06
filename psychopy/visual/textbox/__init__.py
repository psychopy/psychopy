# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:38:35 2013

@author: Sol
"""
import os,inspect
from weakref import proxy
import time
import pyglet
pyglet.options['debug_gl'] = False
gl=pyglet.gl

from psychopy import core,misc
from textGrid import TextGrid
from glyph import GlyphSet
from font import TTFont

def getTime():
    return core.getTime()

        
class TextBox(object):
    """
    TextBox is a psychopy visual stimulus type that supports the presentation
    of text using TTF font files. TextBox is an alternative to the TextStim
    psychopy component. TextBox and TextStim each have different strengths
    and weaknesses. You should select the most appropriate text component type
    based on the intended use of the stimulus within an experiment.

    TextBox Features:
        * Each character displayed by TextBox is positioned very precisely,
          allowing the exact window position and area of each text character 
          to be reported.
        * The text string being displayed can be changed and then displayed 
          **very** quickly (often in under 1 - 2 msec); 
          see TextBox Draw Performance section for details.
        * TextBox is a composite stimulus type, with the following graphical
          elements:
             - TextBox Border / Outline
             - TextBox Fill Area
             - Text Grid Cell Lines
             - Text Grid Cell Areas
             - Text Glyphs
          Attributes for each of the TextBox graphical elements can be specified 
          to control many aspects of how the textBox is displayed.
        * Different font character sets, colors, and sizes can be used within
          a single TextBox. (Internally supported but not brought out to the 
          user level API at this time. This will be fixed soon.)
          
    Textbox Limitations:
        * Only Monospace Fonts are supported. 
        * TTF files must be used. 
        * Changing the text to be displayed after the Textbox is first drawn
          is very fast, however the initial time to create a TextBox instance
          is very slow ( relative to TextStim ).
        * TextBox's can not be rotated or flipped.
        
    Textbox vs. TextStim:
        * TBC
     
    """
    _textbox_instances={}
    _text_style_cache={}
    _te_glyph_set_label_to_max_size={}
    _default_text_style_info=dict(
                                label='default_textbox_text_style',
                                file_name='VeraMono.ttf',
                                font_size=14,
                                dpi=72,
                                font_color=[0,0,0,1],
                                font_background_color=None
                                )    
    def __init__(self, 
             window=None,               # PsychoPy Window instance
             name=None,                 # Name for the TextBox Stim
             active_text_style_label=None,# Label of an already loaded 
                                        # FontStim.
             available_text_styles_labels=[],# List of pre loaded test style labels
                                        # that should be made available for this
                                        # instance of TextBox
             text='Default Test Text.', # Initial text to be displayed.
             font_file_name=None,       # Name of TTF file to use. File
                                        # must be in one of the Font Search
                                        # Directories registed with TextBox. 
             font_size=32,              # Pt size to use for font.
             dpi=72,                    # DPI used to create font bitmaps
                                        # (should match your system DPI setting)
             font_color=[0,0,0,1],      # Color to draw the text with.  
             font_background_color=None,# Color to fill each text cell with.
             line_spacing=None,         # Amount of extra spacing to add between
             line_spacing_units=None,   # lines of text.
             background_color=None,     # Color to use to fill the entire area
                                        # on the screen TextBox is using.
             border_color=None,         # TextBox border color to use.
             border_stroke_width=1,     # Stroke width of TextBox boarder (in pix)
             size=None,                 # (width,height) desired for the TextBox
                                        # stim to use. Specify using the unit
                                        # type the textBox is using.
             pos=(0.0,0.0),             # (x,y) screen position for the TextBox
                                        # stim. Specify using the unit
                                        # type the textBox is using.
             align_horz='center',       # Determines how TextBox x pos is 
                                        # should be interpreted to.
                                        # 'left', 'center', 'right' are valid options.
             align_vert='center',       # Determines how TextBox y pos is 
                                        # should be interpreted to.
                                        # 'left', 'center', 'right' are valid options.
             units=None,                # Coordinate unit type to use for position
                                        # and size related attributes. Valid
                                        # options are 'pix', 'cm', 'deg', 'norm'
                                        # Only pix is currently working though.
             grid_color=None,           # Color to draw the TextBox text grid
                                        # lines with.
             grid_stroke_width=1,       # Line thickness (in pix) to use when
                                        # displaying text grid lines.
             colorSpace='rgb',          # PsychoPy color space to use for any
                                        # color attributes of TextBox.
             opacity=1.0,               # Opacity (transparency) to use for
                                        # TextBox graphics, assuming alpha
                                        # channel was not specified in the color
                                        # attribute.
             grid_horz_justification='left', # 'left', 'center', 'right'
             grid_vert_justification='top',  # 'top', 'bottom', 'center'
             autoLog=True,              # Log each time stim is updated.

             # -- Below TextStim params are NOT supported by TextBox --
             depth=None, 
             rgb=None,
             contrast=None,
             ori=None,
             antialias=None,
             height=None,
             bold=None,
             italic=None,
             alignHoriz=None,
             alignVert=None,
             fontFiles=None,
             wrapWidth=None,
             flipHoriz=None, 
             flipVert=None
             ):
        self._window=window  
        self._text=text
        self._set_text=True
        self._label=name
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
        
        #TODO: Implement support for following 3 attributes
        self._color_space=colorSpace
        self._opacity=opacity
        self._auto_log=autoLog
        
        # Notify that a TextStim param was passed that is not supported by
        # TextBox. TODO: Move to log??
        if rgb:
            print 'Parameter "rgb" is not supported by TextBox'
        if depth:
            print 'Parameter "depth" is not supported by TextBox'
        if contrast:
            print 'Parameter "contrast" is not supported by TextBox'
        if ori:
            print 'Parameter "ori" is not supported by TextBox'
        if antialias:
            print 'Parameter "antialias" is not supported by TextBox'
        if height:
            print 'Parameter "height" is not supported by TextBox'
        if bold:
            print 'Parameter "bold" is not supported by TextBox'
        if italic:
            print 'Parameter "italic" is not supported by TextBox'
        if alignHoriz:
            print 'Parameter "alignHoriz" is not supported by TextBox'
        if alignVert:
            print 'Parameter "alignVert" is not supported by TextBox'
        if fontFiles:
            print 'Parameter "fontFiles" is not supported by TextBox'
        if wrapWidth:
            print 'Parameter "wrapWidth" is not supported by TextBox'
        if flipHoriz:
            print 'Parameter "flipHoriz" is not supported by TextBox'
        if flipVert:
            print 'Parameter "flipVert" is not supported by TextBox'
        
        self._display_lists=dict(textbox_background=None,
                                 enable_psychopy_gl_settings=None,
                                 enable_pyglet_gl_settings=None)         

        self._pixel_line_spacing=0
        self._glyph_set_max_tile_sizes=None
        self._alignment=align_horz,align_vert    
        self._top_left_gl=None
        self._active_text_style=None
        self._available_text_styles_labels=available_text_styles_labels
        self._text_grid=None
        self._text_styles={}
        
        if self._label is None:
            self._label='TextBox_%s'%(str(int(time.time())))
        
        for tsl in self._available_text_styles_labels:
            ts = self._text_style_cache.get(tsl)
            if ts:
                self._text_styles.setdefault(tsl,ts)
                
        self._setActiveTextStyleFromArgs(active_text_style_label,font_file_name,font_size,dpi,font_color,font_background_color)
                                    
        ###

        if TTFont._glyphs_loaded is False:
            TTFont._loadGlyphs()
            TTFont.getTextureAtlas().upload()

        ###
                    
        # calculate max tile size, and set the value in the Glyph Set
        TextBox._te_glyph_set_label_to_max_size[self._label]={}
        
        max_width=0
        max_height=0            
        for gs in self._text_styles.itervalues():
            max_width=max(gs._font._max_tile_width,max_width)
            max_height=max(gs._font._max_tile_height,max_height)

        for gs in self._text_styles.itervalues():
            gs.max_tile_sizes.append((max_width,max_height))
            TextBox._te_glyph_set_label_to_max_size[self._label][gs.getLabel()]=(max_width,max_height)
   
        ###
   
        self._glyph_set_max_tile_sizes=self._te_glyph_set_label_to_max_size[self._label]

        for gs_label,gs in GlyphSet.loaded_glyph_sets.iteritems():
            gs.createDisplayListsForMaxTileSizes()

        ###

        self._textbox_instances[self.getLabel()]=proxy(self)
        
    def getWindow(self):
        return self._window

    def getLabel(self):
        return self._label
        
    def getName(self):
        return self._label

    def getText(self):
        return self._text

    def setText(self,text_source):
        self._text=text_source
        self._set_text=True
        #self._reset()
        
    def getUnits(self):
        return self._units
            
    def getPosition(self):
        return self._position

    def setPosition(self,pos):            
        self._position=pos
        
    def getSize(self):
        return self._size
        
    def getColorSpace(self):
        print 'TextBox.getColorSpace: Color Space not yet supported'
        return self._color_space

    def setColorSpace(self,v):
        print 'TextBox.setColorSpace: Color Space not yet supported'
        self._color_space=v

    def getAutoLog(self):
        print 'TextBox.getAutoLog: Auto Log not yet supported'
        return self._auto_log

    def setAutoLog(self,v):
        print 'TextBox.setAutoLog: Auto Log not yet supported'
        self._auto_log=v

    def getOpacity(self):
        print 'TextBox.getOpacity: Opacity not yet supported'
        return self._opacity

    def setOpacity(self,v):
        print 'TextBox.setOpacity: Opacity not yet supported'
        self._opacity=v
            
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
    def createTextStyle(text_style_label,file_name,font_size=24,dpi=72,font_color=[0,0,0,1],font_background_color=None):
        gs=GlyphSet.createCached(TTFont.load(file_name,font_size,dpi),font_color,font_background_color)
        return TextBox._text_style_cache.setdefault(text_style_label,gs)

    def setActiveTextStyle(self,text_style_label):
        if text_style_label and text_style_label in self._text_styles.keys():
            self._active_text_style=self._text_styles.get(text_style_label)

    def getMaxTextCellSize(self):
        return self._glyph_set_max_tile_sizes[self._active_text_style.getLabel()]

    def getAlignment(self):
        return self._alignment
     
    def draw(self):              
        self._buildResourcesIfNeeded()
        
        # enable_pyglet_gl_settings
        gl.glCallList(self._display_lists['enable_pyglet_gl_settings'])#self._resetPygletCompatState()                             
        t,l=self._getTopLeftPixPos()
        gl.glTranslatef(t,l, 0 ) 
        
        # draw textbox_background and outline
        tbdl=self._display_lists['textbox_background']
        if tbdl:
            gl.glCallList(tbdl)  

        # draw text grid and char glyphs.          
        self._text_grid.draw()    
        
        # enable_psychopy_gl_settings
        rgb=self._window.rgb
        colorSpace=self._window.colorSpace
        if colorSpace in ['rgb','dkl','lms','hsv']: #these spaces are 0-centred
            desiredRGB = (rgb+1)/2.0#RGB in range 0:1 and scaled for contrast
        else:
            desiredRGB = rgb/255.0
        gl.glClearColor(desiredRGB[0],desiredRGB[1],desiredRGB[2], 1.0)
        gl.glCallList(self._display_lists['enable_psychopy_gl_settings'])                  
  
        gl.glFinish()

    def _createDisplayLists(self):
        # create DL for switching to pyglet compatible GL state
        dl_index = gl.glGenLists(1)        
        gl.glNewList(dl_index, gl.GL_COMPILE)           
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
        gl.glPushMatrix()
        gl.glEndList()
        self._display_lists['enable_pyglet_gl_settings']=dl_index

        # create DL for switching to psychopy compatible GL state
        dl_index = gl.glGenLists(1)        
        gl.glNewList(dl_index, gl.GL_COMPILE)           
        gl.glPopMatrix()        
        gl.glViewport(0, 0, int(self._window.winHandle.screen.width), int(self._window.winHandle.screen.height))
        gl.glMatrixMode(gl.GL_PROJECTION) # Reset The Projection Matrix
        gl.glLoadIdentity()
        gl.gluOrtho2D(-1,1,-1,1)
        gl.glMatrixMode(gl.GL_MODELVIEW)# Reset The Projection Matrix
        gl.glLoadIdentity()
        gl.glEndList( )
        self._display_lists['enable_psychopy_gl_settings']=dl_index 


        #display list for drawing textbox border and background fill
        if self._background_color or self._border_color:
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
            self._display_lists['textbox_background']=dl_index  

    def _freeDisplayList(self,dlist_name=None):
        # if no dlist_name is given, delete all dlists
        if dlist_name:
            dlist=self._display_lists.get(dlist_name)
            if dlist:
                gl.glDeleteLists(dlist, 1)
                self._display_lists[dlist_name]=None
        else:
            dlist_names=self._display_lists.keys()
            for dlist_name in dlist_names:
                dlist=self._display_lists.get(dlist_name)
                if dlist:
                    gl.glDeleteLists(dlist, 1)
                    self._display_lists[dlist_name]=None

    
    def _setActiveTextStyleFromArgs(self,text_style_label=None,font_file_name=None,font_size=None,dpi=None,font_color=None,font_background_color=None):
        if text_style_label:
            if self._text_styles.get(text_style_label):
                self._active_text_style=self._text_styles.get(text_style_label)                
            elif self._text_style_cache.get(text_style_label):
                ts=self._text_style_cache.get(text_style_label)
                self._text_styles[text_style_label]=ts
                self._active_text_style=ts             
        if self._active_text_style is None and font_file_name:
                # create new font stim using TextBox args
                self._active_text_style=self.createTextStyle(text_style_label,font_file_name,font_size,dpi,font_color,font_background_color)
                if self._active_text_style:                
                    self._text_styles[text_style_label]=self._active_text_style   
        if self._active_text_style is None:
                self._active_text_style=self._text_style_cache[self._default_text_style_info.get('label')]
                         
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
            print 'TODO: Add support for Norm Unit Type'
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
    
    def _getDefaultGlyphDisplayListSet(self):
        if self._active_text_style is None:
            raise AttributeError("_getDefaultGlyphDisplayListSet: default_font_stim can not be None")
        return self._active_text_style._display_lists[self.getMaxTextCellSize()]
                
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

            self._createDisplayLists()

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

    def __del__(self):
        del self._textbox_instances[self.getName()]
        self._freeDisplayList()
        self._text_styles.clear()
        self._glyph_set_max_tile_sizes=None
        self._active_text_style=None
        self._text_grid=None


        
def _module_directory(local_function):
    mp=os.path.abspath(inspect.getsourcefile(local_function))
    moduleDirectory,mname=os.path.split(mp)
    return moduleDirectory
        
_THIS_DIR=_module_directory(getTime)    
TTFont.addSearchDirectories(os.path.join(_THIS_DIR,'fonts'))

_label=TextBox._default_text_style_info.get('label')
if _label and _label not in TextBox._text_style_cache:
        dtsi=TextBox._default_text_style_info
        label=_label
        file_name=dtsi['file_name']
        size=dtsi['font_size']
        dpi=dtsi['dpi']
        font_color=dtsi['font_color']
        background_color=dtsi['font_background_color']
        TextBox.createTextStyle(label,file_name,
                        size,dpi,font_color,
                        background_color)                
