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
from textRegions import TextRegionType
import parsedTextDocument
from collections import OrderedDict

getTime = core.getTime

class TextGrid(object):
    def __init__(self, text_box, line_color=None, line_width=1):
        self._text_editor=proxy(text_box)        
        self._window=proxy(text_box.getWindow())
        
        if line_color:
            self._lines_visible=True
            self._line_color=line_color
            self._line_width=line_width

        else:
            self._lines_visible=False
            self._line_color=None
            self._line_width=None     
        
        # Default display list        
        max_size=self.getTextBox().getMaxTextCellSize()
        self.default_display_lists=self.getTextBox().getDefaultGlyphDisplayListSet()
        self._pixel_line_spacing=self.getTextBox().getPixelTextLineSpacing()        
        self._cell_size=max_size[0],max_size[1]+self._pixel_line_spacing
        self._limit_text_to_grid_shape=True
        
        if self.default_display_lists is None:
            raise AttributeError('default_display_lists can not be None.')
                
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
        
        # _display_list: The display list used to draw the text grid cell borders
        #   if they are visible. This should be rebuilt whenever _rebuild is True
        #
        self._display_list=None
                
        self._first_visible_row_id=None
        self._last_visible_row_id=None
        self._text_document=None
        self.text_region_types=OrderedDict()
        
    def reset(self):
        #self.setVisibleLineIndexRange(0)
        for key,trt in self.text_region_types.iteritems():
            trt.clearRegions()
            
    def getTextBox(self):
        return self._text_editor

    def getWindow(self):
        return self._window

    def getSize(self):
        return self._size

    def getCellSize(self):
        return self._cell_size[0],self._cell_size[1]
        
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
                
    def setDefaultDisplayListsLabel(self,l):
        self.default_display_lists=self.getTextBox().getDefaultGlyphDisplayListSet(l)
        for rid in self.text_region_types.keys():
            if l == self.text_region_types[rid].getLabel():
                self.default_region_type_key=rid
                return rid
        self.default_region_type_key=len(self.region_type_display_list_tuple)-1     
        return self.default_region_type_key
        
    def getPixelBounds(self):
        """
        Returns l,t,r,b bounds of text grid in gl pix coords (0,0 is bottom left)
        """
        te_l,te_t,te_r,te_b=self.getTextBox().getPixelBounds()
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
        
    def getTextRegionTypes(self):
        return self.text_region_types
        
    def getGridCellIndex(self,pixel_position):
        wsize=self.getTextBox().getWindow().size
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
        te_size=self.getTextBox().getSize()
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
            self._display_list=dl_index  
                
        #
        ## Create region Objects
        #    
        self.text_region_types=self.getTextBox().getFontStims()        
        region_type_keys=self.text_region_types.keys()
        temp=['NOT_USED',]
        for rid in region_type_keys:
            temp.append(self.text_region_types[rid].getGlyphForCharCode)
        self.default_region_type_key=len(temp)
        temp.append(self.default_display_lists.get)                
        self.region_type_display_list_tuple=tuple(temp)
        
    def draw(self):
        gl.glActiveTexture(gl.GL_TEXTURE0)        
        gl.glEnable( gl.GL_TEXTURE_2D )
        gl.glBindTexture( gl.GL_TEXTURE_2D, TTFont.texture_atlas.getTextureID() )
        gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
        gl.glTranslatef( self._position[0], -self._position[1], 0 )

        gl.glPushMatrix( )
        
        getParsedLine=self._text_document.getParsedLine
        default_display_lists=self.default_display_lists.get
        display_list_tuple=None
        if len(self.region_type_display_list_tuple)>2:
            display_list_tuple=self.region_type_display_list_tuple
        
        def buildDisplayListForLine(line):
            line_ords=line.getOrds()
            if display_list_tuple:
                text_region_flags=line.text_region_flags[0,:]
                return [display_list_tuple[text_region_flags[i]](c) for i,c in enumerate(line_ords)]
            else:
                return [default_display_lists(c) for c in line_ords] 
        
        self.setVisibleLineIndexRange(self._first_visible_row_id)

        for current_row_index,r in enumerate(range(self._first_visible_row_id,self._last_visible_row_id+1)):            
            line=getParsedLine(r)
            line_length=line.getLength()
            line_display_list=line.getDisplayList()
            if line_display_list[0]==0:
                line_display_list[0:line_length]=buildDisplayListForLine(line)
            gl.glTranslatef(0,-int(self._pixel_line_spacing/2.0),0)
            gl.glCallLists(line_length,gl.GL_UNSIGNED_INT,line_display_list[0:line_length].ctypes)
            gl.glTranslatef(-line_length*self._cell_size[0],-self._cell_size[1]+int(self._pixel_line_spacing/2.0),0)
        
        gl.glPopMatrix()       
        gl.glBindTexture( gl.GL_TEXTURE_2D,0 )
        gl.glDisable( gl.GL_TEXTURE_2D ) 

        if self._display_list and self.getVisibility() is True:
            gl.glCallList(self._display_list)
            
        gl.glColor4f(0.0,0.0,0.0,1)

        gl.glPopMatrix() 
        