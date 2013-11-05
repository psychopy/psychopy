# -*- coding: utf-8 -*-
"""
Created on Fri Jun 07 22:19:25 2013

@author: Sol
"""

# -*- coding: utf-8 -*-
"""
Created on Wed May 29 19:03:10 2013

@author: Sol
"""
from weakref import proxy
from collections import OrderedDict

class TextRegion(object):
    region_counter=1
    def __init__(self,start_index,end_index=None,parent=None):
        start_index=int(start_index)
        if end_index is not None:
            end_index=int(end_index)
        if start_index is None or not isinstance(start_index,(int,long)):
            raise ValueError("start_index must be an int and not None.")
        
        self.setParent(parent)
        self._text_grid=proxy(self.parent._text_grid)
        self.id=self.region_counter
        TextRegion.region_counter+=1        

        self.start_index=start_index
        self.end_index=end_index
        self._index_range=[]
        self._min_index=None
        self._max_index=None
        self._length=0
        self._flagsSet=False
        self._selected=False
        self._updateState()

        
    def _updateState(self):
        self._max_index=max(self.start_index,self.end_index)
        self._min_index=min(self.start_index,self.end_index)
        self._index_range=range(self._min_index,self._max_index)
        self._length=self._max_index-self._min_index  
        self.setFlags()      

        
    def getID(self):
        return self.id
    
    def getParent(self):
        return self.parent
        
    def setParent(self,p):
        self.parent=proxy(p)
        self._getDocumentTextIndex=self.parent._text_grid.getDocumentTextIndex

    def clearFlags(self):
        if self._flagsSet and self._text_grid:
            text_document=self._text_grid._text_document
            getParsedLine=text_document.getParsedLine
            default_region_type_key=self._text_grid.default_region_type_key
            rmin,rmax=self.minmax()
            if rmin >= 0 and rmax >=0 and rmin!=rmax:
                min_line_index=text_document.getLineIndex(rmin)
                max_line_index=text_document.getLineIndex(rmax)
                
                if min_line_index==max_line_index:
                    line=getParsedLine(min_line_index)
                    if line:
                        line_region_start=rmin-line.getIndexRange()[0]
                        line_region_end=rmax-line.getIndexRange()[0]
                        #min_line.text_region_flags[0,min_line_region_start:max_line_region_start]=self._text_grid.default_region_type_key
                        line.text_region_flags[0:2,line_region_start:line_region_end]=default_region_type_key
                else:
                    min_line=getParsedLine(min_line_index)
                    max_line=getParsedLine(max_line_index)
                    if min_line and max_line and self._text_grid:
                        min_line_region_start=rmin-min_line.getIndexRange()[0]
                        max_line_region_start=rmax-max_line.getIndexRange()[0]
                        
                        min_line.text_region_flags[0:2,min_line_region_start:]=default_region_type_key
                        max_line.text_region_flags[0:2,:max_line_region_start+1]=default_region_type_key
                    
                    for line_index in range(min_line_index+1,max_line_index):
                        l=getParsedLine(line_index)
                        if l and self._text_grid:
                            l.text_region_flags[0:2,:]=default_region_type_key
                
#                if text_document:
#                    text_document.clearCachedLineDisplayLists(rmin,rmax)
            self._flagsSet=False
    
    def setFlags(self):
        if self._flagsSet is False:
            rmin,rmax=self.minmax()
            text_document=self._text_grid._text_document
            getParsedLine=text_document.getParsedLine
            pid=self.parent.id
            sid=self.id
            if rmin >= 0 and rmax >=0 and rmin!=rmax:
                min_line_index=text_document.getLineIndex(rmin)
                max_line_index=text_document.getLineIndex(rmax)
                
                if min_line_index==max_line_index:
                    line=getParsedLine(min_line_index)
                    line_region_start=rmin-line.getIndexRange()[0]
                    line_region_end=rmax-line.getIndexRange()[0]
                    line.text_region_flags[0,line_region_start:line_region_end]=pid
                    line.text_region_flags[1,line_region_start:line_region_end]=sid
                else:
                    min_line=getParsedLine(min_line_index)
                    max_line=getParsedLine(max_line_index)
                    min_line_region_start=rmin-min_line.getIndexRange()[0]
                    max_line_region_start=rmax-max_line.getIndexRange()[0]
                    
                    min_line.text_region_flags[0,min_line_region_start:]=pid
                    max_line.text_region_flags[0,:max_line_region_start+1]=pid
                    min_line.text_region_flags[1,min_line_region_start:]=pid
                    max_line.text_region_flags[1,:max_line_region_start+1]=pid
                    
                    for line_index in range(min_line_index+1,max_line_index):
                        getParsedLine(line_index).text_region_flags[0,:]=pid
                        getParsedLine(line_index).text_region_flags[1,:]=sid
            
#            text_document.clearCachedLineDisplayLists(rmin,rmax)
        self._flagsSet=True
        
    def getTypeAndInstanceIDs(self):
        return self.parent.id,self.id

    def getGlyphForCharCode(self,charcode):
        return self.parent.getGlyphForCharCode(charcode)
            
    def minmax(self):
        return self._min_index,self._max_index    
   
    def __len__(self):
        return self._length
        
    def __getitem__(self, key):
        if key == 'start':
            return self.start_index

        if key == 'end':
            return self.end_index
            
        return self._index_range[key]

    def __setitem__(self, key, value):
        value=int(value)
        if key == 'start':
            if value!=self.start_index:
                self.clearFlags()
                self.start_index=value
                self._updateState()

            return
        if key == 'end':
            if value!=self.end_index:
                self.clearFlags()
                self.end_index=value
                self._updateState()
            return

        raise IndexError("TextRegion only supports assignment of the first and last elements using the keys 'start' and 'end'.")
    
    def __iter__(self):
        for x in self._index_range:
            yield x
  
    def __contains__(self,v):
        minv,maxv=self.minmax()        
        if v>=minv and v < maxv:
            return True
        return False

    def __repr__(self):
        return u"{0}".format(self._index_range)

    def __str__(self):
        return u"{0}".format(self.__repr__())
    
    def free(self):
        self.clearFlags()
        self.parent=None
        self._getDocumentTextIndex=None
        self._text_grid=None
        self._index_range=None

    def __del__(self):
        self.free()
        
class TextRegionType(object):
    region_type_counter=1
    
    def __init__(self,text_box=None,glyph_set=None):
        self._text_box=proxy(text_box)  
        self._glyph_set=glyph_set
        self._display_lists=None
        self.regions=OrderedDict()
        
        self.id=self.region_type_counter
        TextRegionType.region_type_counter+=1
                
        self._display_lists=glyph_set._display_lists[text_box._glyph_set_max_tile_sizes[glyph_set.getLabel()]]

    def getID(self):
        return self.id
    
    def getLabel(self):
        return self._glyph_set.getLabel()
    
    def getGlyphSet(self):
        return self._glyph_set
        
    def getTextRegionList(self):
        return self.regions.values()

    def getTextRegions(self):
        return self.regions
    
    def getRegionIDs(self):
        return self.regions.keys()
        
    def createTextRegion(self,start_index,end_index):
        r=TextRegion(int(start_index),int(end_index),self)        
        self.regions[r.id]=r
        return proxy(r)

    def getTextRegion(self,r_id):
        r=self.regions.get(r_id,None)
        if r:
            return proxy(r)
        return r
        
    def removeTextRegion(self,r_id):
        if r_id in self.regions.keys():
            r=self.regions[r_id]
            r.free()
            del self.regions[r_id]

    def clearRegions(self):
        self.regions.clear()
                
    def getGlyphForCharCode(self,charcode):
        return self._display_lists.get(charcode)