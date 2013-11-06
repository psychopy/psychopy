# -*- coding: utf-8 -*-
"""
Created on Mon Jan 07 11:18:51 2013

@author: Sol
"""

from psychopy import core
import numpy as np
from weakref import proxy
import pyglet.gl as gl
from font import TTFont

import parsedTextDocument

getTime = core.getTime

class TextGrid(object):
    def __init__(self, text_box, line_color=None, line_width=1, 
                 grid_horz_justification='left',
                 grid_vert_justification='top'):
        self._text_box=proxy(text_box)        
        self._window=proxy(text_box.getWindow())
        
        if line_color:
            self._lines_visible=True
            self._line_color=line_color
            self._line_width=line_width

        else:
            self._lines_visible=False
            self._line_color=None
            self._line_width=None     

        self._possible_glyth_sets=dict()
        
        # Default display list        
        max_size=self._text_box.getMaxTextCellSize()
        
        self._cell_size=max_size[0],max_size[1]+self._text_box._getPixelTextLineSpacing()
        self._limit_text_to_grid_shape=True
        
        self._horz_justification=grid_horz_justification
        self._vert_justification=grid_vert_justification
                       
        # Attributes to fill in at grid build time.
        #
        # _shape = cell column count, cell row count 
        #
        self._shape=None,None

        # _size = width,height for full text grid.
        #   = _shape*_cell_size
        #
        self._size=None,None

        # _position: top left position of text grid **WITHIN Text Box**
        #
        self._position=None         
        
        # _grid_lines_dlist: The display list used to draw the text grid cell borders
        #   if they are visible. This should be rebuilt whenever _rebuild is True
        #
        self._grid_lines_dlist=None

        self._draw_start_dlist=None
        self._draw_end_dlist=None
                
        self._first_visible_row_id=None
        self._last_visible_row_id=None
        self._text_document=None

    def getWindow(self):
        return self._window

    def getSize(self):
        return self._size

    def getCellSize(self):
        return self._cell_size
        
    def getShape(self):
        return self._shape

    def limitTextLengthToVisibleRowCount(self):
        return True
        
    def getGridRowCount(self):
        return self._shape[1]
        
    def getPosition(self):
        return self._position

    def getVisibility(self):
        return self._lines_visible
            
    def setVisibility(self,v):
        self._lines_visible=v
        
    def getPixelBounds(self):
        """
        Returns l,t,r,b bounds of text grid in gl pix coords (0,0 is bottom left)
        """
        te_l,te_t,te_r,te_b=self._text_box._getPixelBounds()
        px,py=self.getPosition()
        w,h=self.getSize()
        return te_l+px,te_t-py,te_l+px+w,te_t-py-h
                
    def createParsedTextDocument(self,f):
        if self._shape:
            self._text_document=parsedTextDocument.ParsedTextDocument(f,self,False) 
            self.setVisibleLineIndexRange(0)
        else:
            raise AttributeError("Could not create _text_document. num_columns needs to be known.")

    def getParsedTextDocument(self):
        return self._text_document
               
    def getFirstVisibleRowIndex(self):
        return self._first_visible_row_id

    def getLastVisibleRowIndex(self):
        return self._last_visible_row_id

    def setVisibleLineIndexRange(self,first_index,last_index=None):
        if first_index<0:
            first_index=0
        if last_index is None or last_index<0:
            last_index=min(first_index+self._shape[1]-1,self._text_document.getParsedLineCount()-1)
        if last_index-first_index>=self._shape[1]:
            last_index=first_index+self._shape[1]-1
        if last_index>=self._text_document.getParsedLineCount():
            last_index=self._text_document.getParsedLineCount()-1
        elif last_index<0:
            last_index=0

        if self._first_visible_row_id!=first_index or self._last_visible_row_id!=last_index:
            self._first_visible_row_id=first_index
            self._last_visible_row_id=last_index

    def getFirstVisibleCharIndex(self):
        return self.getParsedTextDocument().getParsedLine(self._first_visible_row_id).getIndexRange()[0]

    def getLastVisibleCharIndex(self):
        return self.getParsedTextDocument().getParsedLine(self.getLastVisibleRowIndex()).getIndexRange()[1]-1
        
    def getGridCellIndex(self,pixel_position):
        wsize=self._text_box._window.size
        px,py=pixel_position
        px,py=px+wsize[0]//2,py+wsize[1]//2
        l,t,r,b=self.getPixelBounds()
        if px >= l and px <= r and py >= b and py <= t:
            cw,ch=self.getCellSize()
            cols,rows=self.getShape()
            hit_cell=[(px-l)//cw,rows-1-(py-b)//ch]
            return hit_cell
        return None

    def getDocumentTextIndex(self,pixel_position):
        grid_cell=self.getGridCellIndex(pixel_position)
        if grid_cell:
            first_visible_row_id=self._first_visible_row_id
            doc_line_index=first_visible_row_id+grid_cell[1]
            line_data=self.getParsedTextDocument().getParsedLine(doc_line_index)
            if line_data:
                index_range=line_data.getIndexRange()
                max_col=index_range[1]-index_range[0]
                if grid_cell[0]<max_col:
                    return index_range[0]+grid_cell[0]
        return -1

    def getLastTextColForRow(self,grid_row_index):
        if grid_row_index>=0:          
            doc_line_index=self._first_visible_row_id+grid_row_index
            line_data=self.getParsedTextDocument().getParsedLine(doc_line_index)
            if line_data:
                return line_data.getIndexRange()[1]-line_data.getIndexRange()[0]
        
    def getDocumentTextIndexForCell(self,cell_cr_index):
        if cell_cr_index:
            doc_line_index=self._first_visible_row_id+cell_cr_index[1]
            if doc_line_index < 0 or doc_line_index > self.getParsedTextDocument().getParsedLineCount():
                print "error: doc_line_index out of range!", doc_line_index, self.getParsedTextDocument().getParsedLineCount()
                return -1
            line_data=self.getParsedTextDocument().getParsedLine(doc_line_index)
            if line_data is not None:
                line_index_start, line_index_end=line_data.getIndexRange()
                text_index_for_cell=line_index_start+cell_cr_index[0]
                if text_index_for_cell < 0 or text_index_for_cell >= line_index_end:
                    print "error: text_index_for_cell out of range!", text_index_for_cell, line_index_start, line_index_end              
                    return -1
                return text_index_for_cell
        return -1
                    
    def configure(self):        
        #
        ## Text Grid line_spacing
        #
        te_size=self._text_box._getPixelSize()
        self._shape=te_size[0]//self._cell_size[0],te_size[1]//self._cell_size[1]
        self._size=self._cell_size[0]*self._shape[0],self._cell_size[1]*self._shape[1]
        # For now, The text grid will be cenetered in the TextBox area.
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

        self._createDisplayLists()
        
    def _createDisplayLists(self):
        dl_index = gl.glGenLists(1)        
        gl.glNewList(dl_index, gl.GL_COMPILE)           
        gl.glActiveTexture(gl.GL_TEXTURE0)        
        gl.glEnable( gl.GL_TEXTURE_2D )
        gl.glBindTexture( gl.GL_TEXTURE_2D, TTFont.texture_atlas.getTextureID() )
        gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
        gl.glTranslatef( self._position[0], -self._position[1], 0 )
        gl.glPushMatrix( )
        gl.glEndList( )
        self._draw_start_dlist=dl_index  

        dl_index = gl.glGenLists(1)        
        gl.glNewList(dl_index, gl.GL_COMPILE)           
        gl.glPopMatrix()       
        gl.glBindTexture( gl.GL_TEXTURE_2D,0 )
        gl.glDisable( gl.GL_TEXTURE_2D ) 
        if self._grid_lines_dlist and self.getVisibility() is True:
            gl.glCallList(self._grid_lines_dlist)            
        gl.glColor4f(0.0,0.0,0.0,1)
        gl.glPopMatrix() 
        gl.glEndList( )
        self._draw_end_dlist=dl_index  
        
        if self._line_color:                
            # create grid lines display list
            dl_index = gl.glGenLists(1)        
            gl.glNewList(dl_index, gl.GL_COMPILE)           
            gl.glLineWidth(self._line_width)
            gl.glColor4f(*self._line_color)                   
            gl.glBegin(gl.GL_LINES)
            for x in self._col_lines:
                for y in self._row_lines:
                    if x == 0:
                        gl.glVertex2i(x,y)
                        gl.glVertex2i(int(self._size[0]), y)
                    if y == 0:
                        gl.glVertex2i(x, y)
                        gl.glVertex2i(x, int(-self._size[1]))                        
            gl.glEnd()
            gl.glLineWidth(1)
            gl.glColor4f(0.0,0.0,0.0,1)
            gl.glEndList( )
            self._grid_lines_dlist=dl_index         

        
    def draw(self):
        gl.glCallList(self._draw_start_dlist) 
        
        getParsedLine=self._text_document.getParsedLine
        active_text_style_dlist=self._text_box._active_text_style._display_lists[self._text_box.getMaxTextCellSize()].get#_active_text_style._display_lists[ts]
        
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
        
        cell_width,cell_height=self._cell_size
        num_cols,num_rows=self._shape
        line_spacing=self._text_box._getPixelTextLineSpacing()
        self.setVisibleLineIndexRange(self._first_visible_row_id)
        line_count=(self._last_visible_row_id+1)-self._first_visible_row_id
        
        for current_row_index,r in enumerate(range(self._first_visible_row_id,self._last_visible_row_id+1)):            
            line=getParsedLine(r)
            line_length=line.getLength()
            line_display_list=line.getDisplayList()
            if line_display_list[0]==0: 
                # line_display_list[0]==0 Indicates parsed line text has 
                # changed since last draw, so rebuild line display list. 
                line_display_list[0:line_length]=[active_text_style_dlist(c) for c in line.getOrds()] 
                
            if pad_left_proportion or (pad_top_proportion and line_count>1):
                empty_cell_count=num_cols-line_length
                empty_line_count=num_rows-line_count
                trans_left=int(empty_cell_count*pad_left_proportion)*cell_width
                trans_top=int(empty_line_count*pad_top_proportion)*cell_height
                
            gl.glTranslatef(trans_left,-int(line_spacing/2.0+trans_top),0)
            gl.glCallLists(line_length,gl.GL_UNSIGNED_INT,line_display_list[0:line_length].ctypes)
            gl.glTranslatef(-line_length*cell_width-trans_left,-cell_height+int(line_spacing/2.0+trans_top),0)

        gl.glCallList(self._draw_end_dlist) 
