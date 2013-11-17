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
from fontmanager import SystemFontManager

from textgrid import TextGrid

def getTime():
    return core.getTime()

def is_sequence(arg):
    return (#not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

global _system_font_manager
_system_font_manager=None

def getFontManager():
    global _system_font_manager
    if _system_font_manager is None:
        _system_font_manager = SystemFontManager() 
    return _system_font_manager
    
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

    * TextBox Read/Write Attributes:
        text
        font_color
        background_color
        border_color
        border_stroke_width
        pos
        align_horz
        align_vert
        grid_color
        grid_stroke_width
        grid_horz_justification
        grid_vert_justification
        opacity         
        interpolate
        
    * Read Only Attributes (Currently):
        window
        font_name
        bold
        italic
        font_size
        dpi
        line_spacing
        line_spacing_units
        size
        textgrid_shape
        units
        color_space

       
    Textbox vs. TextStim:
        * TBC
     
    """
    _textbox_instances={}
    _gl_info=None
    def __init__(self, 
             window=None,               # PsychoPy Window instance
             text='Default Test Text.', # Initial text to be displayed.
             font_name=None,            # Family name of Font
             bold=False,                # Bold and italics are used to 
             italic=False,             #    determine style of font
             font_size=32,              # Pt size to use for font.
             font_color=[0,0,0,1],      # Color to draw the text with.  
             dpi=72,                    # DPI used to create font bitmaps
             line_spacing=0,            # Amount of extra spacing to add between
             line_spacing_units='pix',  # lines of text.
             background_color=None,     # Color to use to fill the entire area
                                        # on the screen TextBox is using.
             border_color=None,         # TextBox border color to use.
             border_stroke_width=1,     # Stroke width of TextBox boarder (in pix)
             size=None,                 # (width,height) desired for the TextBox
                                        # stim to use. Specify using the unit
                                        # type the textBox is using.
             textgrid_shape=None,        # (cols,rows) of characters to use when
                                        # creating the textgrid layout. 
                                        # rows*cols = maximum number of chars
                                        # that can be displayed. If textgrid_shape
                                        # is not None, then the TextBox size
                                        # must be atleast large enough to hold
                                        # the number of specified cols and rows.
                                        # If the size specified is less than
                                        # what is needed, the size will be increased
                                        # automatically.
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
        self._border_stroke_width=border_stroke_width         
        self._grid_horz_justification=grid_horz_justification
        self._grid_vert_justification=grid_vert_justification
        self._align_horz=align_horz
        self._align_vert=align_vert      
        self._size=size
        self._position=pos
        self._textgrid_shape=textgrid_shape
        self._interpolate=interpolate
        
        self._draw_start_dlist=None
        self._draw_end_dlist=None
        self._draw_te_background_dlist=None

        
        if TextBox._gl_info is None:
            TextBox._gl_info =getGLInfo()
        
        aliased_wrange=TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']
        antia_wrange=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
        antia_gran=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY']
        
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

        self._current_glfont=None
        self._text_grid=None

        
        if self._label is None:
            self._label='TextBox_%s'%(str(int(time.time())))

        fm=getFontManager()
        if font_name is None:
            font_name=fm.getFontFamilyStyles()[0][0]
        gl_font=fm.getGLFont(font_name,font_size,bold,italic,dpi)
        self._current_glfont=gl_font

        self._text_grid=TextGrid(self, line_color=grid_color, 
                 line_width=grid_stroke_width, font_color=font_color,
                 shape=textgrid_shape,
                 grid_horz_justification=grid_horz_justification,
                 grid_vert_justification=grid_vert_justification)

        self._text_grid.setCurrentFontDisplayLists(gl_font.charcode2displaylist)
        
        self._text=self._text.replace('\r\n','\n')
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
        """
        Set the text to be displayed within the Textbox. 
        
        Note that once a TextBox has been created, the number of character
        rows and columns is static. To change the size of a TextBox,
        a new TextBox stim must be created to replace the current Textbox stim.
        Therefore ensure that the textbox is large enough to display
        the largest length string to be presented in the TextBox. Characters
        that do not fit within the TextBox will not be displayed.
        
        Color value must be valid for the color space being used by the TextBox.
        """        
        if not self._text:                
            raise ValueError("TextBox.setText only accepts strings with a length > 0")

        self._text=text_source.replace('\r\n','\n')
        return self._text_grid._setText(self._text)

    def getDisplayedText(self):
        return self._text_grid._text_document.getDisplayedText()   
        
    def getInterpolate(self):
        return self._interpolate
        
    def setInterpolate(self,i):
        """ 
        Using a bool value, specify whether interpolation should be enabled 
        for the TextStim. When interpolate == True, GL_LINE_SMOOTH and
        GL_POLYGON_SMOOTH are enabled within OpenGL. When interpolate is set 
        to False, they are disabled.
        """                
        if i != self._interpolate:
            self._deleteStartDL()
            self._interpolate=i
        
    def getUnits(self):
        return self._units
            
    def getPosition(self):
        return self._position

    def setPosition(self,pos): 
        """
        Set the (x,y) position of the TextBox on the Monitor. The position must 
        be given using the unit coord type being used by the stim.
        
        The TextBox position is interpreted differently depending on the 
        Horzontal and Vertical Alignment settings of the stim. For example,
        if the TextBox alignment is specified as left, top, then the position
        specifies the top left hand corner of where the stim will be drawn.
        An alignment of bottom,right indicates that the position value will
        define where the bottom right corner of the TextBox will be drawn.
        A horz., vert. alignment of center, center will place the center of
        the TextBox at pos.
        """
        if pos != self._position:           
            self._position=pos
            self._deleteBackgroundDL()
            self._deleteStartDL()
        
    def getSize(self):
        return self._size
        
    def getColorSpace(self):
        return self._color_space

    def getFontColor(self):
        return self._text_grid._font_color

    def setFontColor(self,c):
        """
        Set the color to use when drawing text within the TextBox.
        Color value must be valid for the color space being used by the TextBox.
        """        
        if c != self._text_grid._font_color:
            self._text_grid._font_color=c
            self._text_grid._deleteTextDL()
   
    def getHorzJust(self):
        return self._text_grid._horz_justification

    def getVertJust(self):
        return self._text_grid._vert_justification
        
    def setHorzJust(self,v):
        """
        Specify how text within the TextBox should be aligned horizontally.
        For example, if a text grid has 10 columns, and the text being displayed
        is 6 characters in length, the horizontal justification determines
        if the text should be draw starting at the left of the text columns (left),
        or should be centered on the columns ('center', in this example 
        there would be two empty text cells to the left and right of the text.),
        or should be drawn such that the last letter of text is drawn in the
        last column of the text row ('right'). 
        """
        if v != self._text_grid._horz_justification:
            self._text_grid._horz_justification=v
            self._text_grid._deleteTextDL()

    def setVertJust(self,v):
        """
        Specify how text within the TextBox should be aligned vertically.
        For example, if a text grid has 3 rows for text, and the text being 
        displayed all fits on one row, the vertical justification determines
        if the text should be draw on the top row of the text grid (top),
        or should be centered on the rows ('center', in this example 
        there would be one row  above and below the row used to draw the text),
        or should be drawn on the last row of the text grid, ('bottom'). 
        """
        if v != self._text_grid._vert_justification:
            self._text_grid._vert_justification=v
            self._text_grid._deleteTextDL()

    def getAutoLog(self):
        return self._auto_log

    def setAutoLog(self,v):
        print 'TextBox.setAutoLog: Auto Log not yet supported'
        self._auto_log=v

    def getOpacity(self):
        return self._opacity

    def setOpacity(self,o):
        """
        Sets the TextBox wide transparency level for the stim. 0.0 equals
        no visibility, while 1.0 is fully visible.
        
        When Opacity is set to a value between 0.0 and 1.0, it is used to set the
        alpha channel of all drawing done within the TextBox stim.
        
        If opacity is set to None, then each element of the TextBox stim 
        can have a different opacity, by providing rgb or rgb255 colors with a 
        4th element in the color list. Colors that only have three channels 
        specified use an alpha channel value of 1.0. 
        """
        if o != self._opacity and o >=0.0 and o <= 1.0:
            self._text_grid._deleteTextDL()   
            self._deleteBackgroundDL()
            self._text_grid._deleteGridLinesDL()
            self._deleteStartDL()
            self._deleteEndDL()
            self._opacity=o

    def getLineSpacing(self):
        return self._line_spacing

    def getBorderColor(self):
        return self._border_color

    def setBorderColor(self,c):
        """
        Set the line color to use for the border which can be drawn around
        the edges of the TextBox stim. Color value must 
        be valid for the color space being used by the TextBox.
        
        A value of None will result in no border being drawn.
        """        
        if c!= self._border_color:
            self._border_color=c
            self._deleteBackgroundDL()

    def getBorderWidth(self):
        return self._border_stroke_width

    def setBorderWidth(self,c):
        """
        Set the stroke width (in pixels) to use for the border of the TextBox 
        stim. Border values must be within the range of stroke widths supported
        by the OpenGL driver used by the computer graphics card. Setting the 
        width outside the valid range will result in the stroke width being 
        clamped to the nearest end of the valid range.
        
        Use the TextBox.getGLineRanges() to access a dict containing some
        OpenGL parameters which provide the minimum, maximum, and resolution
        of valid line widths.
        """        
        if c!= self._border_stroke_width:
            if self._interpolate:
                lrange=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
                antia_gran=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY']
            else:
                lrange=TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']

            if c < lrange[0]:
                c=lrange[0]
            elif c > lrange[1]:
                c=lrange[1]
                
            self._border_stroke_width=c
            self._deleteBackgroundDL()

    def getBackgroundColor(self):
        return self._background_color

    def setBackgroundColor(self,c):
        """
        Set the fill color to use for the TextBox stim area. Color value must 
        be valid for the color space being used by the TextBox.
        
        A value of None will result in no backgrount being drawn.
        """
        if c!= self._background_color:
            self._background_color=c
            self._deleteBackgroundDL()

    def getTextGridLineColor(self):
        return self._text_grid._line_color

    def setTextGridLineColor(self,c):
        """
        Lines can be drawn which mark the bounding box for each character
        within the TextEditors text grid. Set the text grid line color 
        to change whatcolor should be used. Color value must 
        be valid for the color space being used by the TextBox.
        
        A value of None will result in no text grid lines being drawn.
        """
        if c!= self._text_grid._line_color:
            self._text_grid._line_color=c
            self._text_grid._deleteGridLinesDL()

    def getTextGridLineWidth(self):
        return self._text_grid._line_width

    def setTextGridLineWidth(self,c):
        """
        Set the stroke width (in pixels) to use for the text grid character
        bounding boxes. Border values must be within the range of stroke 
        widths supported by the OpenGL driver used by the computer graphics 
        card. Setting the width outside the valid range will result in the 
        stroke width being clamped to the nearest end of the valid range.
        
        Use the TextBox.getGLineRanges() to access a dict containing some
        OpenGL parameters which provide the minimum, maximum, and resolution
        of valid line widths.
        """
        if c!= self._text_grid._line_width:
            if self._interpolate:
                lrange=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_RANGE']
                antia_gran=TextBox._gl_info['GL_SMOOTH_LINE_WIDTH_GRANULARITY']
            else:
                lrange=TextBox._gl_info['GL_ALIASED_LINE_WIDTH_RANGE']

            if c < lrange[0]:
                c=lrange[0]
            elif c > lrange[1]:
                c=lrange[1]

            self._text_grid._line_width=c
            self._text_grid._deleteGridLinesDL()

    def getHorzAlignment(self):
        return self._align_horz

    def getVertAlignment(self):
        return self._align_vert

    def setHorzAlignment(self,v):
        """
        Specify how the horizontal (x) component of the TextBox position
        is to be interpreted. left = x position is the left edge, right =
        x position is the right edge x position, and center = the x position
        is used to center the stim horizontally.
        """
        if v!= self._align_horz:
            self._align_horz=v
            self._deleteBackgroundDL()
            self._deleteStartDL()

    def setVertAlignment(self,v):
        """
        Specify how the vertical (y) component of the TextBox position
        is to be interpreted. top = y position is the top edge, bottom =
        y position is the bottom edge y position, and center = the y position
        is used to center the stim vertically.
        """
        if v!= self._align_vert:
            self._align_vert=v
            self._deleteBackgroundDL()
            self._deleteStartDL()
    
    def getMaxTextCellSize(self):
        return self._current_glfont.max_tile_width,self._current_glfont.max_tile_height

    def getOpenGLSettings(self):
        return self._gl_info
        
    def draw(self):
        self._te_start_gl()
        self._te_bakground_dlist()
        self._text_grid._text_glyphs_gl() 
        self._text_grid._textgrid_lines_gl()
        self._te_end_gl()

        
    def _te_start_gl(self):
        if not self._draw_start_dlist:            
            dl_index = glGenLists(1)        
            glNewList(dl_index, GL_COMPILE)           
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
            t,l=self._getTopLeftPixPos()
            glTranslatef(t,l, 0 )   
            glEndList()
            self._draw_start_dlist=dl_index
        glCallList(self._draw_start_dlist) 

    def _deleteStartDL(self):
        if self._draw_start_dlist:
            glDeleteLists(self._draw_start_dlist, 1)
            self._draw_start_dlist=None

    def _te_bakground_dlist(self):
        if not self._draw_te_background_dlist and (self._background_color or self._border_color):            
            dl_index = glGenLists(1)        
            glNewList(dl_index, GL_COMPILE)           
        
            # draw textbox_background and outline
            #t,l=self._getTopLeftPixPos()
            #glTranslatef(t,l, 0 )         
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
            glEndList()
            self._draw_te_background_dlist=dl_index
        if (self._background_color or self._border_color):
            glCallList(self._draw_te_background_dlist) 
            
    def _deleteBackgroundDL(self):
        if self._draw_te_background_dlist:
            glDeleteLists(self._draw_te_background_dlist, 1)
            self._draw_te_background_dlist=None

    def _te_end_gl(self):
        if not self._draw_end_dlist:            
            dl_index = glGenLists(1)        
            glNewList(dl_index, GL_COMPILE)           

            rgb=self._window.rgb
            rgb=TextBox._toRGBA2(rgb,1,self._window.colorSpace,self._window)
            glClearColor(rgb[0],rgb[1],rgb[2], 1.0) 
            glViewport(0, 0, int(self._window.winHandle.screen.width), int(self._window.winHandle.screen.height))
            glMatrixMode(GL_PROJECTION) # Reset The Projection Matrix
            glLoadIdentity()
            gluOrtho2D(-1,1,-1,1)
            glMatrixMode(GL_MODELVIEW)# Reset The Projection Matrix
            glLoadIdentity()

            glEndList()
            self._draw_end_dlist=dl_index    
        glCallList(self._draw_end_dlist) 

    def _deleteEndDL(self):
        if self._draw_end_dlist:
            glDeleteLists(self._draw_end_dlist, 1)
            self._draw_end_dlist=None
            
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
                                     
    def _reset(self):
        self._text_grid.reset()                       

    def _getPixelSize(self):
        if self._units == 'norm':
            r = self._toPix((self._size[0]-1.0,self._size[1]-1.0) ,self._units, self._window)
            return int(r[0]+self._window.size[0]/2),int(r[1]+self._window.size[1]/2)
        return [int(x) for x in self._toPix(self._size ,self._units, self._window)]

    def _setSize(self,pix_sz):
        units=self._units
        if units in ('pix','pixs'):
            self._size=list(pix_sz) 
        if units in ['deg','degs']:
            self._size= misc.pix2deg(pix_sz[0],self._window.monitor),misc.pix2deg(pix_sz[1],self._window.monitor)  
        if units in ['cm']:
            self._size= misc.pix2cm(pix_sz[0],self._window.monitor),misc.pix2cm(pix_sz[1],self._window.monitor)     
        if units in ['norm']:
            pw,ph=pix_sz
            dw,dh=self._window.size
            nw=(pw/float(dw))*2.0
            nh=(ph/float(dh))*2.0
            self._size=nw,nh
            
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
        del self._current_glfont
        del self._text_grid
        
