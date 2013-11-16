# -*- coding: utf-8 -*-
"""
Created on Mon Jan 07 11:18:51 2013

@author: Sol
"""

import numpy as np
from weakref import proxy
from psychopy import core
from pyglet.gl import (glCallList,glGenLists,glNewList,glDisable,glEnable,
                glTranslatef,glColor4f,glLineWidth,glBegin,GL_LINES,glEndList,
               glDeleteLists,GL_COMPILE,glEnd, GL_TEXTURE0,GL_TEXTURE_2D,
               GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_MODULATE,GL_UNSIGNED_INT,
               glPopMatrix,glBindTexture,glActiveTexture,glTexEnvf,
               glPushMatrix,glCallLists,glVertex2i)
import parsedTextDocument
getTime = core.getTime

class TextGrid(object):
    def __init__(self, text_box, line_color=None, line_width=1,
                 font_color=(1,1,1,1),shape=None,
                 grid_horz_justification='left',
                 grid_vert_justification='top'):
        
        self._text_box=proxy(text_box)
        
        self._font_color=font_color
        if line_color:
            self._line_color=line_color
            self._line_width=line_width
        else:
            self._line_color=None
            self._line_width=None     
        
        max_size=self._text_box.getMaxTextCellSize()        
        self._cell_size=max_size[0],max_size[1]+self._text_box._getPixelTextLineSpacing()
        if self._cell_size[0]==0:
            print 'ERROR WITH CELL SIZE!!!! ', self._text_box.getLabel()
        #print 'self._cell_size:',self._cell_size
        self._horz_justification=grid_horz_justification
        self._vert_justification=grid_vert_justification
        
        self._text_dlist=None
        self._gridlines_dlist=None
        
        self._text_document=None

        #
        ## Text Grid line_spacing
        #
        te_size=[0,0]
        if self._text_box._size:
            te_size=list(self._text_box._getPixelSize())

        if shape:
            self._shape=shape
        else:
            self._shape=te_size[0]//self._cell_size[0],te_size[1]//self._cell_size[1]

        self._size=self._cell_size[0]*self._shape[0],self._cell_size[1]*self._shape[1]
        resized=False
        if shape and self._size[0]>te_size[0]:
            te_size[0]=self._size[0]       
            resized=True
        if shape and self._size[1]>te_size[1]:
            te_size[1]=self._size[1]       
            resized=True
        if resized:    
            self._text_box._setSize(te_size)    
        # For now, The text grid is centered in the TextBox area.
        #
        dx=(te_size[0]-self._size[0])//2
        dy=(te_size[1]-self._size[1])//2 
        
        # TextGrid Position is position within the TextBox component.
        # 
        self._position=dx,dy
        # TextGrid cell boundaries
        #
        self._col_lines=[int(np.floor(x)) for x in xrange(0,self._size[0]+1,self._cell_size[0])]    
        self._row_lines=[int(np.floor(y)) for y in xrange(0,-self._size[1]-1,-self._cell_size[1])]    
        
    def getSize(self):
        return self._size

    def getCellSize(self):
        return self._cell_size
        
    def getShape(self):
        return self._shape
        
    def getPosition(self):
        return self._position

    def getLineColor(self):
        return self._line_color

    def getLineWidth(self):
        return self._line_width
     
    def getHorzJust(self):
        return self._horz_justification

    def getVertJust(self):
        return self._vert_justification
  
    def _setText(self,text):
        self._text_document.deleteText(0,self._text_document.getTextLength(),
                                       text)
        self._deleteTextDL()
        
    def setCurrentFontDisplayLists(self,dlists):
        self._current_font_display_lists=dlists
        
    def _deleteTextDL(self):
        if self._text_dlist:
            glDeleteLists(self._text_dlist, 1)
            self._text_dlist=0

    def _deleteGridLinesDL(self):
        if self._gridlines_dlist:
            glDeleteLists(self._gridlines_dlist, 1)
            self._gridlines_dlist=None
                
    def _createParsedTextDocument(self,f):
        if self._shape:
            self._text_document=parsedTextDocument.ParsedTextDocument(f,self) 
            self._deleteTextDL()
        else:
            raise AttributeError("Could not create _text_document. num_columns needs to be known.")

    def _text_glyphs_gl(self):
        if not self._text_dlist:            
            dl_index = glGenLists(1)        
            glNewList(dl_index, GL_COMPILE)           

            #stime=getTime()

            #self._text_box._te_start_gl()                         
    
            ###
            glActiveTexture(GL_TEXTURE0)        
            glEnable( GL_TEXTURE_2D )
            glBindTexture( GL_TEXTURE_2D, self._text_box._current_glfont.atlas.texid)
            glTexEnvf(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_MODULATE )
            glTranslatef( self._position[0], -self._position[1], 0 )
            glPushMatrix()

            ###
            
            hjust=self._horz_justification
            vjust=self._vert_justification
            pad_left_proportion=0     
            pad_top_proportion=0     
            if hjust=='center':
                pad_left_proportion=0.5
            elif hjust=='right':
                pad_left_proportion=1.0
            if vjust=='center':
                pad_top_proportion=0.5
            elif vjust=='bottom':
                pad_top_proportion=1.0
            
            getLineInfoByIndex=self._text_document.getLineInfoByIndex
            active_text_style_dlist=self._current_font_display_lists.get
            cell_width,cell_height=self._cell_size
            num_cols,num_rows=self._shape
            line_spacing=self._text_box._getPixelTextLineSpacing()
            line_count=min(num_rows,self._text_document.getParsedLineCount())
            apply_padding=pad_left_proportion or (pad_top_proportion and line_count>1)
            trans_left=0
            trans_top=0
            glColor4f(*self._text_box._toRGBA(self._font_color))    

            for r in range(line_count):            
                line_length,line_display_list,line_ords=getLineInfoByIndex(r)
                if line_display_list[0]==0: 
                    line_display_list[0:line_length]=[active_text_style_dlist(c) for c in line_ords] 
                    
                if apply_padding:
                    empty_cell_count=num_cols-line_length
                    empty_line_count=num_rows-line_count
                    trans_left=int((empty_cell_count+1)*pad_left_proportion)*cell_width
                    trans_top=int(empty_line_count*pad_top_proportion)*cell_height
                    
                glTranslatef(trans_left,-int(line_spacing/2.0+trans_top),0)
                glCallLists(line_length,GL_UNSIGNED_INT,line_display_list[0:line_length].ctypes)
                glTranslatef(-line_length*cell_width-trans_left,-cell_height+int(line_spacing/2.0+trans_top),0)
    
                ###
            glPopMatrix()       
            glBindTexture( GL_TEXTURE_2D,0 )
            glDisable( GL_TEXTURE_2D ) 

            glEndList()            
            #print 'GL_TIME: %.3f'%((etime-stime)*1000.0)
            self._text_dlist=dl_index
        glCallList(self._text_dlist) 


    def _textgrid_lines_gl(self):
        if self._line_color:
            if not self._gridlines_dlist:                
                dl_index = glGenLists(1)        
                glNewList(dl_index, GL_COMPILE)           

                glLineWidth(self._line_width)
                glColor4f(*self._text_box._toRGBA(self._line_color))                   
                glBegin(GL_LINES)
                for x in self._col_lines:
                    for y in self._row_lines:
                        if x == 0:
                            glVertex2i(x,y)
                            glVertex2i(int(self._size[0]), y)
                        if y == 0:
                            glVertex2i(x, y)
                            glVertex2i(x, int(-self._size[1]))                        
                glEnd()
                glColor4f(0.0,0.0,0.0,1.0)
                glEndList() 
                self._gridlines_dlist=dl_index
            glCallList(self._gridlines_dlist) 
            
            #self._text_box._te_end_gl()                         

            #etime=getTime()


    def __del__(self):
        if self._text_dlist:
            glDeleteLists(self._text_dlist, 1)
            self._text_dlist=0
        self._current_font_display_lists=None
        self._text_document._free()
        del self._text_document
        
