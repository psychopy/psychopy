# -*- coding: utf-8 -*-
"""
Created on Sat May 25 00:09:01 2013

@author: Sol
"""
from textwrap import TextWrapper
import codecs,os
from collections import deque
from weakref import proxy
from psychopy.core import getTime
            
class ParsedTextDocument(object):
    def __init__(self,text_data,text_grid,parse_text_as_needed=True):
        if os.path.isfile(text_data):
            tfile=codecs.open(text_data,'rU','utf-8')
            text_data=tfile.read()
            tfile.close()
            
        text_data=text_data.replace('\r\n','\n')
        if len(text_data) and text_data[-1] != u'\n':
            text_data=text_data+u'\n'
        elif len(text_data)==0:
            text_data=text_data+u'\n'
        self._text=text_data
        self._children=[]

        self._num_columns,self._max_visible_rows=text_grid._shape
        self._limit_text_length=0
        
        if text_grid.limitTextLengthToVisibleRowCount():
           self._limit_text_length =self._max_visible_rows*self._num_columns
        
        if self._limit_text_length>0 and self._limit_text_length<len(self._text):
            self._text=self._text[:self._limit_text_length]
            
        self._text_grid=proxy(text_grid)
        self._default_parse_chunk_size=self._num_columns*(self._max_visible_rows+1)
        self._text_wrapper=TextWrapper(width=self._num_columns,drop_whitespace=False,replace_whitespace=False,expand_tabs=False) 
        
        self._text_parsed_to_index=0
        if parse_text_as_needed is False:
            self._parse(0,len(self._text))
        else:            
            self._parse(0)

    def addChild(self,c):
        self._children.append(c)
        
    def getChildren(self):
        return self._children
    
    def getChildCount(self):
        return len(self._children)
        
    def getText(self):
        return self._text

    def getCharAtIndex(self,text_index):
        try:
            return self._text[text_index]
        except:
            print "WARNING: ParsedTextDocument.getCharAtIndex received out of bounds index: ",text_index,self.getTextLength()
            return None

    def getTextLength(self):
          return len(self._text)

    def deleteText(self,start_index,end_index,insertText=None):
        start_index=int(start_index)
        end_index=int(end_index) 
        deleted_text=self._text[start_index:end_index]
        if insertText is None:
            self._text=''.join([self._text[:start_index],self._text[end_index:]])
        else:
            self._text=''.join([self._text[:start_index],insertText,self._text[end_index:]])
        self._parse(start_index)
        return deleted_text
        
    def insertText(self,text,start_index,end_index=None):
        start_index=int(start_index)
        if end_index is None:
            end_index=start_index
        else:
            end_index=int(end_index)        

        self._text=''.join([self._text[:int(start_index)],text,self._text[int(end_index):]])
        return self._parse(start_index)

    def parseTextTo(self,requested_line_index):
        requested_line_index=int(requested_line_index)
        if self.getParsedLineCount()>requested_line_index:
            return requested_line_index
        add_line_count=(requested_line_index-self.getParsedLineCount())+1
        
        max_chars_to_add=add_line_count*self._num_columns
        start_index= self._children[-1]._index_range[0]
        self._parse(start_index,start_index+max_chars_to_add)
        if self.getParsedLineCount()>=requested_line_index:
            return requested_line_index
        return self.getParsedLineCount()-1
        
    def _parse(self,from_text_index,to_text_index=None):
        from_text_index=int(from_text_index)
        if to_text_index is not None: 
            to_text_index=int(to_text_index)
            
        if from_text_index < 0:
            raise IndexError("Parse from_text_index must be >= 0.")        

        line_index=None        
        if self._children and from_text_index<=self._text_parsed_to_index:
            line_index=self.getLineIndex(from_text_index)
            from_text_index=self.getParsedLine(line_index).getIndexRange()[0]
        else:
            from_text_index=self._text_parsed_to_index
        if to_text_index is None:
            try:
                to_row_index=self._text_grid.getFirstVisibleRowIndex()+self._text_grid._shape[1]+1
                line=self.getParsedLine(to_row_index)
                to_text_index=line.getIndexRange()[1]+self._num_columns
            except:            
                to_text_index = from_text_index+self._default_parse_chunk_size

        if to_text_index  > self.getTextLength():
            to_text_index=self.getTextLength()
        
        update_lines=[]
        if line_index is not None:
            update_lines=deque(self._children[line_index:])
        para_split_text=self._text[from_text_index:to_text_index].splitlines(True)
        if len(para_split_text)==0:
            return
          
        current_index=from_text_index        
        for para_text in para_split_text:
            current_index=self._wrapText(para_text,current_index,update_lines)
                
        if len(update_lines)>0:
            self._children=self._children[:-len(update_lines)]            
        self._text_parsed_to_index=current_index

    def _wrapText(self,para_text,current_index,update_lines):
        rewrap=False
        para_text_index=0
        for linestr in self._text_wrapper.wrap(para_text):
            if linestr[-1]!=u' ' and len(self._text) > current_index+len(linestr) and self._text[current_index+len(linestr)]==u' ':
                last_space=linestr.rfind(u' ')
                if last_space>0:
                    linestr=linestr[:last_space+1]
                    rewrap=True
            if len(update_lines)>0:
                line=update_lines.popleft()
                line._text=linestr             
                line._index_range=[current_index,current_index+len(linestr)]
                line._ords=[ord(c) for c in linestr]
                line._length=len(line._ords)
                line._gl_display_list[0]=0
                line.text_region_flags[:,:]=self._text_grid.default_region_type_key                    
            else:
                ParsedTextLine(self,linestr,[current_index,current_index+len(linestr)])
                line=self._children[-1]
            current_index+=len(linestr)                    
            para_text_index+=len(linestr)  
            if rewrap is True:
                return self._wrapText(para_text[para_text_index:],current_index,update_lines)
        return current_index
        
    def clearCachedLineDisplayLists(self,from_char_index, to_char_index):
        if from_char_index<0:
            from_char_index=0
        elif from_char_index>=len(self._text):
            from_char_index=len(self._text)-1
        
        if to_char_index<0:
            to_char_index=0
        elif to_char_index>=len(self._text):
            to_char_index=len(self._text)-1
            
        start_line=self.getLineIndex(from_char_index)        
        to_line=self.getLineIndex(to_char_index)
        
        for l in range(start_line,to_line+1):
            self._children[l]._gl_display_list[0]=0
        
    def getParsedLine(self,i):
        if i is None:
            return None
        i=int(i)
        if i<0 or i>=self.getChildCount():
            return None
        return self._children[i]

    def getParsedLines(self):
        return self._children
        
    def getParsedLineCount(self):
        return self.getChildCount()
        
    def getTextGridCellForCharIndex(self,char_index):
        for line in self._children:
            rsi,rei=line._index_range    
            if char_index >= rsi and char_index < rei:
                r=line._line_index
                c=char_index-rsi
                return c,r
        return None

    def getLineIndex(self,char_index):
        for line in self._children:
            rsi,rei=line._index_range    
            if char_index >= rsi and char_index < rei:
                return line.getIndex()
        return None
        
    def getLineFromCharIndex(self,char_index):
        if char_index < 0:
            return None 
        for line in self._children:
            rsi,rei=line._index_range    
            if char_index >= rsi and char_index < rei:
                return line
        return None
        
import numpy
 
class ParsedTextLine(object):
    def __init__(self,parent,source_text,index_range):
        if parent:
            self._parent=proxy(parent)
            self._parent.addChild(self)
        else:
            self._parent=None
        self._text=source_text
        self._index_range=index_range
        self._line_index=parent.getChildCount()-1
        self._ords=[ord(c) for c in source_text]
        self._length=len(self._ords)
        self.text_region_flags=numpy.ones((2,parent._num_columns),numpy.uint32)*parent._text_grid.default_region_type_key
        self._gl_display_list=numpy.zeros(parent._num_columns,numpy.uint)
            
    def getIndex(self):
        return self._line_index
        
    def getParent(self):
        return self._parent
        
    def getIndexRange(self):
        return self._index_range

    def getText(self):
        return self._text
        
    def getOrds(self):
        return self._ords
    
    def getLength(self):
        return self._length
        
    def getDisplayList(self):
        return self._gl_display_list

    def getTextRegionFlags(self):
        return self.text_region_flags
        
    def setTextRegionFlags(self,f):
        self.text_region_flags=f

    def __del__(self):
        self.text_region_flags=None 
        self._gl_display_list=None
        self._ords=None