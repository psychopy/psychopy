# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:38:35 2013

@author: Sol
"""
from __future__ import division
import os,inspect,numbers
from weakref import proxy
import time
import pyglet
pyglet.options['debug_gl'] = False
from pyglet.gl import (glCallList,glFinish,glGenLists,glNewList,glViewport,
               glMatrixMode,glLoadIdentity,glDisable,glEnable,glColorMaterial,
               glBlendFunc,glTranslatef,glColor4f,glRectf,glLineWidth,glBegin,
               GL_LINES,glVertex2d,glEndList,glClearColor,gluOrtho2D,glOrtho,
               glDeleteLists,GL_COMPILE,GL_PROJECTION,GL_MODELVIEW,glEnd,
               GL_DEPTH_TEST,GL_BLEND,GL_COLOR_MATERIAL,GL_FRONT_AND_BACK ,
               GL_AMBIENT_AND_DIFFUSE,GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA,
               glIsEnabled,GL_LINE_SMOOTH,GLint,GLfloat,glGetIntegerv,
               GL_LINE_WIDTH,glGetFloatv,GL_ALIASED_LINE_WIDTH_RANGE,
               GL_SMOOTH_LINE_WIDTH_RANGE,GL_SMOOTH_LINE_WIDTH_GRANULARITY,
               GL_POLYGON_SMOOTH)


from psychopy import core,misc,colors
import psychopy.tools.colorspacetools as colortools
import psychopy.tools.arraytools as arraytools
from font_manager import SystemFontManager

from textGrid import TextGrid
from glyph import GlyphSet
from font import TTFont

print 'TODO: '
print ' - Fix crash when > 1 textbox is added to a window.'
print
def getTime():
    return core.getTime()

def is_sequence(arg):
    return (#not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def getGLInfo():
    gl_info=dict()
    gl_info['GL_LINE_SMOOTH']=glIsEnabled(GL_LINE_SMOOTH)
    lwidth=GLint()
    glGetIntegerv(GL_LINE_WIDTH,lwidth)
    gl_info['GL_LINE_WIDTH']=lwidth
    awrange=(GLfloat*2)(0.0,0.0)
    glGetFloatv(GL_ALIASED_LINE_WIDTH_RANGE,awrange)
    gl_info['GL_ALIASED_LINE_WIDTH_RANGE']=awrange[0],awrange[1]
    swrange=(GLfloat*2)(0.0,0.0)
    glGetFloatv(GL_SMOOTH_LINE_WIDTH_RANGE,swrange)
    gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']=swrange[0],swrange[1]
    swg=GLfloat()
    glGetFloatv(GL_SMOOTH_LINE_WIDTH_GRANULARITY,swg)
    gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY']=swg
    return gl_info
       
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
    font_manager = SystemFontManager() 
    _textbox_instances={}
    _text_style_cache={}
    _te_glyph_set_label_to_max_size={}
    _gl_info=None
    default_font_family_style=None
    def __init__(self, 
             window=None,               # PsychoPy Window instance
             text='Default Test Text.', # Initial text to be displayed.
             font_name=None,            # Family name of Font
             bold=False,                # Bold and italics are used to 
             italic=False,             #    determine style of font
             font_size=32,              # Pt size to use for font.
             font_color=[0,0,0,1],      # Color to draw the text with.  
             font_background_color=None,# Color to fill each text cell with.
             dpi=72,                    # DPI used to create font bitmaps
             font_file_name=None,       # to hand a ttf file for use directly
                                        # (should match your system DPI setting)
             line_spacing=0,            # Amount of extra spacing to add between
             line_spacing_units='pix',  # lines of text.
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
             units='norm',                # Coordinate unit type to use for position
                                        # and size related attributes. Valid
                                        # options are 'pix', 'cm', 'deg', 'norm'
                                        # Only pix is currently working though.
             grid_color=None,           # Color to draw the TextBox text grid
                                        # lines with.
             grid_stroke_width=1,       # Line thickness (in pix) to use when
                                        # displaying text grid lines.
             color_space='rgb',          # PsychoPy color space to use for any
                                        # color attributes of TextBox.
             opacity=1.0,               # Opacity (transparency) to use for
                                        # TextBox graphics, assuming alpha
                                        # channel was not specified in the color
                                        # attribute.
             grid_horz_justification='left', # 'left', 'center', 'right'
             grid_vert_justification='top',  # 'top', 'bottom', 'center'
             autoLog=True,              # Log each time stim is updated.
             interpolate=False,

             # -- Below TextStim params are NOT supported by TextBox --
             depth=None, 
             rgb=None,
             contrast=None,
             ori=None,
             antialias=None,
             height=None,
             alignHoriz=None,
             alignVert=None,
             fontFiles=None,
             wrapWidth=None,
             flipHoriz=None, 
             flipVert=None,
             name=None                 # Name for the TextBox Stim
             ):
        self._window=window  
        self._text=text
        self._label=name
        self._line_spacing=line_spacing
        self._line_spacing_units=line_spacing_units
        self._border_color=border_color
        self._background_color=background_color        
        self._grid_color=grid_color
        self._grid_stroke_width=grid_stroke_width
        self._border_stroke_width=border_stroke_width         
        self._grid_horz_justification=grid_horz_justification
        self._grid_vert_justification=grid_vert_justification
        self._align_horz=align_horz
        self._align_vert=align_vert      
        self._size=size
        self._position=pos
        self._interpolate=interpolate
        
        if TextBox._gl_info is None:
            TextBox._gl_info =getGLInfo()
        
        aliased_wrange=TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']
        antia_wrange=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
        #antia_gran=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY']
        
        if grid_stroke_width and grid_color:
            if interpolate:
                if grid_stroke_width < antia_wrange[0]:
                    self._grid_stroke_width= antia_wrange[0]   
                if grid_stroke_width > antia_wrange[1]:
                    self._grid_stroke_width= antia_wrange[1]   
            else:
                if grid_stroke_width < aliased_wrange[0]:
                    self._grid_stroke_width= aliased_wrange[0]   
                if grid_stroke_width > aliased_wrange[1]:
                    self._grid_stroke_width= aliased_wrange[1]   

        if border_stroke_width and border_color:
            if interpolate:
                if border_stroke_width < antia_wrange[0]:
                    self._border_stroke_width= antia_wrange[0]   
                if border_stroke_width > antia_wrange[1]:
                    self._border_stroke_width= antia_wrange[1]   
            else:
                if border_stroke_width < aliased_wrange[0]:
                    self._border_stroke_width= aliased_wrange[0]   
                if border_stroke_width > aliased_wrange[1]:
                    self._border_stroke_width= aliased_wrange[1]   
                    
        self._units=units
        if self._units is None:
            self._units=self._window.units

        self._opacity=opacity
        if opacity is None:
            self._opacity=1.0
        elif float(opacity) and float(opacity)>=0 and float(opacity)<=1.0:
            self._opacity=float(opacity)
        else:
            raise ValueError("Text Box: opacity must be a number between 0.0 and 1.0, or None (which == 1.0). %s is not valid"%(str(opacity)))
            
        self._color_space=color_space    
        if self._color_space is None:
            self._color_space =self._window.colorSpace
            
        #TODO: Implement support for autoLog
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

        self._glyph_set_max_tile_sizes=None
        self._alignment=align_horz,align_vert
        self._active_text_style=None
        self._text_grid=None
        self._text_styles={}
        
        if self._label is None:
            self._label='TextBox_%s'%(str(int(time.time())))


        text_style=None        
        if font_name:
            matching_fonts=self.font_manager.getFontsMatching(font_name,bold=bold,italic=italic)
            if matching_fonts:
                text_style=matching_fonts[0]
        else:
            for family_name,style in self.font_manager.font_family_styles:
                b,i=self.font_manager.booleansFromStyleName(style)
                if b==bold and i==italic:
                    text_style=self.font_manager.getFontsMatching(family_name,style=style)[0]

        #print 'Text Info Match:',text_style
        if text_style:
            text_style=self.createTextStyle(text_style,
                                            font_size=font_size,
                                            dpi=dpi,
                                            font_color=font_color,
                                            font_background_color=font_background_color,
                                            color_space=color_space,
                                            opacity=opacity,
                                            window=window)                        
        #print 'text_style Match:',text_style
 
        self._setActiveTextStyleFromArgs(text_style,font_file_name,
                                         font_size,
                                         dpi,
                                         font_color,
                                         font_background_color,
                                         color_space,
                                         opacity)
                                    
        ###
        #print 'self._active_text_style:', self._active_text_style                            
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

        self._text_grid=TextGrid(self, line_color=self._grid_color, 
                                 line_width=self._grid_stroke_width,
                                 grid_horz_justification=self._grid_horz_justification,
                                 grid_vert_justification=self._grid_vert_justification)

        ###

        self._text_grid._setActiveGlyphDisplayLists(
            self._active_text_style._display_lists[self.getMaxTextCellSize()])

        if not self._text or len(self._text) == 0:                
            self._text=u'\n'
        self._text_grid._createParsedTextDocument(self._text)

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
        if not self._text:                
            self._text=u'\n'
        self._text=text_source
        self._text_grid._setText(self._text)
        
    def getUnits(self):
        return self._units
            
    def getPosition(self):
        return self._position

    def setPosition(self,pos):            
        self._position=pos
        
    def getSize(self):
        return self._size
        
    def getColorSpace(self):
        return self._color_space

    def getAutoLog(self):
        return self._auto_log

    def setAutoLog(self,v):
        print 'TextBox.setAutoLog: Auto Log not yet supported'
        self._auto_log=v

    def getOpacity(self):
        return self._opacity

    def getLineSpacing(self):
        return self._line_spacing

    def getBorderColor(self):
        return self._border_color

    def getBorderWidth(self):
        return self._border_stroke_width

    def getBackgroundColor(self):
        return self._background_color

    def getTextGridLineColor(self):
        return self._grid_color

    def getTextGridLineWidth(self):
        return self._grid_stroke_width

    def getHorzAlignment(self):
        return self._align_horz

    def getVertAlignment(self):
        return self._align_vert

    def getTextGrid(self):
        return self._text_grid
            

    @staticmethod
    def createTextStyle(font_info=None,file_path=None,font_size=24,dpi=72,font_color=[0,0,0,1],font_background_color=None,color_space='rgb',opacity=1.0,window=None):
        if len(TextBox._textbox_instances)>0:
            raise ValueError("TextBox.createTextStyle can not be called after a TextBox object has been created. Current TextBox count: %d"%(len(TextBox._textbox_instances)))

        font=None
        if font_info:
            font=TTFont.load(font_info.path,font_size,dpi) 
        else:
            font=TTFont.load(file_path,font_size,dpi) 
            
        if font and font.getLabel() in TextBox._text_style_cache:
            raise ValueError("TextBox.createTextStyle TextBox Label Already In Use: %s"%( font.getLabel()))
            
        font_rgba=TextBox._toRGBA2(font_color,opacity,color_space,window)
        back_rgba=None
        if font_background_color:
            back_rgba=TextBox._toRGBA2(font_background_color,opacity,color_space,window)
        gs=GlyphSet.createCached(font,
                                 font_rgba,
                                 back_rgba,
                                 org_color_info=dict(font_color=font_color,
                                                     font_background_color=font_background_color,
                                                     color_space=color_space,
                                                     opacity=opacity))
    
        return TextBox._text_style_cache.setdefault( font.getLabel(),proxy(gs))

    def setActiveTextStyle(self,text_style_label):
        if text_style_label and text_style_label in self._text_styles.keys():
            self._active_text_style=self._text_styles.get(text_style_label)
            self._text_grid._deleteDisplayList()
            self._text_grid._setActiveGlyphDisplayLists(
                self._active_text_style._display_lists[self.getMaxTextCellSize()])

    def getActiveTextStyle(self):
        return self._active_text_style

    def getMaxTextCellSize(self):
        return self._glyph_set_max_tile_sizes[self._active_text_style.getLabel()]

    def getAlignment(self):
        return self._alignment
     
    def draw(self):
#        atime=getTime()        
        self._text_grid._buildDisplayList() 
#        btime=getTime()
        glCallList(self._text_grid._textgrid_dlist) 
#        ctime=getTime()
        #glFinish()
        #dtime=getTime()
        
#        print 'BUILD LIST: %.3f'%((btime-atime)*1000.0)
#        print 'CALL_LIST: %.3f'%((ctime-btime)*1000.0)
#        #print 'FINISH: %.3f'%((dtime-ctime)*1000.0)
#        print 'TOTAL: %.3f'%((ctime-atime)*1000.0)
#        print '----'
        
    def _te_start_gl(self):
        glViewport( 0, 0, self._window.winHandle.screen.width,self._window.winHandle.screen.height )
        glMatrixMode( GL_PROJECTION )
        glLoadIdentity()
        glOrtho( 0, self._window.winHandle.screen.width, 0, self._window.winHandle.screen.height, -1, 1 )
        glMatrixMode( GL_MODELVIEW )
        glLoadIdentity()
        glDisable( GL_DEPTH_TEST )
        glEnable( GL_BLEND )
        glEnable( GL_COLOR_MATERIAL )
        glColorMaterial( GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
        glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
        if self._interpolate:
            glEnable(GL_LINE_SMOOTH)
            glEnable(GL_POLYGON_SMOOTH)
        else:
            glDisable(GL_LINE_SMOOTH)
            glDisable(GL_POLYGON_SMOOTH)
 
        # draw textbox_background and outline
        t,l=self._getTopLeftPixPos()
        glTranslatef(t,l, 0 )         
        if self._background_color or self._border_color:
            border_thickness=self._border_stroke_width
            size=self._getPixelSize()
            if self._border_stroke_width is None:
                border_thickness=0            
            if self._background_color:
                bcolor=self._toRGBA(self._background_color)
                glColor4f(*bcolor)
                #size=self._getPixelSize()
                glRectf(0,0, size[0],-size[1])      
            if self._border_color:
                glLineWidth(border_thickness)
                bcolor=self._toRGBA(self._border_color)
                glColor4f(*bcolor)
                glBegin(GL_LINES)    
                x1=0
                y1=0
                x2,y2=size
                x2,y2=x2,y2
                hbthick=border_thickness//2
                if hbthick<1:
                    hbthick=1
                glVertex2d(x1-border_thickness, y1+hbthick)             
                glVertex2d(x2+border_thickness, y1+hbthick)              
                glVertex2d(x2+hbthick, y1)                 
                glVertex2d(x2+hbthick, -y2)              
                glVertex2d(x2+border_thickness, -y2-hbthick)              
                glVertex2d(x1-border_thickness, -y2-hbthick)                 
                glVertex2d(x1-hbthick, -y2)                 
                glVertex2d(x1-hbthick, y1)             
                glEnd()    
            glColor4f(0.0,0.0,0.0,1.0)

    def _te_end_gl(self):
        rgb=self._window.rgb
        rgb=TextBox._toRGBA2(rgb,1,self._window.colorSpace,self._window)
        glClearColor(rgb[0],rgb[1],rgb[2], 1.0) 
        glViewport(0, 0, int(self._window.winHandle.screen.width), int(self._window.winHandle.screen.height))
        glMatrixMode(GL_PROJECTION) # Reset The Projection Matrix
        glLoadIdentity()
        gluOrtho2D(-1,1,-1,1)
        glMatrixMode(GL_MODELVIEW)# Reset The Projection Matrix
        glLoadIdentity()

    @staticmethod
    def _toPix(xy,units,window):
        if isinstance(xy, numbers.Number):
            xy=xy,xy           
        elif is_sequence(xy):
            if len(xy)==1:
                xy=xy[0],xy[0]
            else:
                xy=xy[:2]
        else:                
            return ValueError("TextBox: coord variables must be array-like or a single number. Invalid: %s"%(str(xy)))

        if not isinstance(xy[0], numbers.Number) or not isinstance(xy[1], numbers.Number):
            return ValueError("TextBox: coord variables must only contain numbers. Invalid: %s"%(str(xy)))
                
        if units in ('pix','pixs'):
            return xy           
        if units in ['deg','degs']:
            return misc.deg2pix(xy[0],window.monitor),misc.deg2pix(xy[1],window.monitor)                        
        if units in ['cm']:
            return misc.cm2pix(xy[0],window.monitor),misc.cm2pix(xy[1],window.monitor)                         
        if units in ['norm']:
            # -1.0 to 1.0
            if xy[0] <=1.0 and xy[0]>=-1.0 and xy[1] <=1.0 and xy[1]>=-1.0:
                return xy[0]*window.size[0]/2.0,xy[1]*window.size[1]/2.0

        return ValueError("TextBox: %s, %s could not be converted to pix units"%(str(xy),str(units)))
        
    def _toRGBA(self,color):
        return self.__class__._toRGBA2(color,self._opacity,self._color_space,self._window)

    @classmethod
    def _toRGBA2(cls,color,opacity=None,color_space=None,window=None):
        
        if color is None:
            raise ValueError("TextBox: None is not a valid color input")
        if not colors.isValidColor(color):
            raise ValueError("TextBox: %s is not a valid color."%(str(color)))

        valid_opacity=opacity>=0.0 and opacity<=1.0 
        if isinstance(color,basestring):
            if color[0] == '#' or color[0:2].lower() == '0x':
                rgb255color=colors.hex2rgb255(color)
                if rgb255color and valid_opacity:
                    return rgb255color[0]/255.0,rgb255color[1]/255.0,rgb255color[2]/255.0,opacity
                else:
                    raise ValueError("TextBox: %s is not a valid hex color."%(str(color)))
           

            named_color=colors.colors.get(color.lower())
            if named_color and valid_opacity:
                return (named_color[0]+1.0)/2.0,(named_color[1]+1.0)/2.0,(named_color[2]+1.0)/2.0,opacity                                
            raise ValueError("TextBox: String color value could not be translated: %s"%(str(color)))

        if isinstance(color,(float,int,long)) or (is_sequence(color) and len(color)==3):
            color=arraytools.val2array(color,length=3)
            if color_space == 'dkl' and valid_opacity:
                dkl_rgb=None
                if window:
                   dkl_rgb=window.dkl_rgb 
                rgb=colortools.dkl2rgb(color,dkl_rgb)
                return (rgb[0]+1.0)/2.0,(rgb[1]+1.0)/2.0,(rgb[2]+1.0)/2.0,opacity
            if color_space == 'lms' and valid_opacity:
                lms_rgb=None
                if window:
                   lms_rgb=window.lms_rgb 
                rgb=colortools.lms2rgb(color,lms_rgb)
                return (rgb[0]+1.0)/2.0,(rgb[1]+1.0)/2.0,(rgb[2]+1.0)/2.0,opacity
            if color_space == 'hsv' and valid_opacity:
                rgb=colortools.hsv2rgb(color)
                return (rgb[0]+1.0)/2.0,(rgb[1]+1.0)/2.0,(rgb[2]+1.0)/2.0,opacity
            if color_space == 'rgb255' and valid_opacity:
                rgb=color
                if [cc for cc in color if cc < 0 or cc > 255]:
                    raise ValueError('TextBox: rgb255 colors must contain elements between 0 and 255. Value: '+str(rgb)) 
                return rgb[0]/255.0,rgb[1]/255.0,rgb[2]/255.0,opacity
            if color_space == 'rgb' and valid_opacity:
                rgb=color
                if [cc for cc in color if cc < -1.0 or cc > 1.0]:
                    raise ValueError('TextBox: rgb colors must contain elements between -1.0 and 1.0. Value: '+str(rgb)) 
                return (rgb[0]+1.0)/2.0,(rgb[1]+1.0)/2.0,(rgb[2]+1.0)/2.0,opacity

        if is_sequence(color) and len(color)==4:
            if color_space == 'rgb255':
                if [cc for cc in color if cc < 0 or cc > 255]:
                    raise ValueError('TextBox: rgb255 colors must contain elements between 0 and 255. Value: '+str(color)) 
                return color[0]/255.0,color[1]/255.0,color[2]/255.0,color[3]/255.0
            if color_space == 'rgb':
                if [cc for cc in color if cc < -1.0 or cc > 1.0]:
                    raise ValueError('TextBox: rgb colors must contain elements between -1.0 and 1.0. Value: '+str(color)) 
                return (color[0]+1.0)/2.0,(color[1]+1.0)/2.0,(color[2]+1.0)/2.0,(color[3]+1.0)/2.0

        raise ValueError("TextBox: color: %s, opacity: %s, is not a valid color for color space %s."%(str(color),str(opacity),color_space))
            
    def _setActiveTextStyleFromArgs(self,text_style=None,font_file_name=None,font_size=None,dpi=None,font_color=None,font_background_color=None,color_space=None,opacity=None):
        if text_style:
            tslabel= text_style.getLabel()
            if tslabel in self._text_styles.keys():
                self._active_text_style=self._text_styles[tslabel]              
            elif tslabel in self._text_style_cache.keys():            
                self._active_text_style=self._text_styles[tslabel]
            else:
                self._text_styles.setdefault(text_style.getLabel(),text_style) 
                self._active_text_style=text_style
        if self._active_text_style is None and font_file_name:
                # create new font stim using TextBox args
                self._active_text_style=self.createTextStyle(None,font_file_name,font_size,dpi,font_color,font_background_color,color_space,opacity,self._window)
                if self._active_text_style:                
                    self._text_styles.setdefault(text_style.getLabel(),self._active_text_style)   
        if self._active_text_style is None:
                raise ValueError("No Text Style could be created based on information given!")
                         
    def _reset(self):
        self._text_grid.reset()                       

    def _getPixelSize(self):
        if self._units == 'norm':
            r = self._toPix((self._size[0]-1.0,self._size[1]-1.0) ,self._units, self._window)
            return int(r[0]+self._window.size[0]/2),int(r[1]+self._window.size[1]/2)
        return [int(x) for x in self._toPix(self._size ,self._units, self._window)]
     
    def _getPixelPosition(self):
        return [int(x) for x in self._toPix(self._position ,self._units, self._window)]
                    
    def _getPixelTextLineSpacing(self):
        if self._line_spacing:
            max_size=self.getMaxTextCellSize()
            line_spacing_units=self._line_spacing_units
            line_spacing_height=self._line_spacing
            
            if line_spacing_units == 'ratio':
                # run though _toPix to validate line_spacing value type only
                r=self._toPix(line_spacing_height,'pix',self._window)[0]
                return max_size*r
                
            return self._toPix(line_spacing_height,line_spacing_units,self._window)
        return 0

    def _getTopLeftPixPos(self):
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
        return te_x,te_y   

    def __del__(self):
        del self._textbox_instances[self.getName()]
        self._text_styles.clear()
        self._glyph_set_max_tile_sizes=None
        del self._active_text_style
        del self._text_grid
        if len(self._textbox_instances) == 0:
            for gs in GlyphSet.loaded_glyph_sets.values():
                if gs._label is not None:                
                    gs._free()
        
#def _module_directory(local_function):
#    mp=os.path.abspath(inspect.getsourcefile(local_function))
#    moduleDirectory,mname=os.path.split(mp)
#    return moduleDirectory
#        
#_THIS_DIR=_module_directory(getTime)    
#TTFont.addSearchDirectories(_THIS_DIR)
#TTFont.addSearchDirectories(os.path.join(_THIS_DIR,'fonts'))


#_label=TextBox._default_text_style_info.get('label')
#if _label and _label not in TextBox._text_style_cache:
#        dtsi=TextBox._default_text_style_info
#        label=_label
#        file_name=dtsi['file_name']
#        size=dtsi['font_size']
#        dpi=dtsi['dpi']
#        font_color=dtsi['font_color']
#        background_color=dtsi['font_background_color']
#        color_space=dtsi['color_space']
#        opacity=dtsi['opacity']
#        TextBox.createTextStyle(label,file_name,
#                        size,dpi,font_color,
#                        background_color,color_space,opacity)                
