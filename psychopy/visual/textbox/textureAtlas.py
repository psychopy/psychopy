# -*- coding: utf-8 -*-
"""
Created on Mon May 20 16:10:57 2013

@author: Sol
"""
# -----------------------------------------------------------------------------
#
#  FreeType high-level python API - Copyright 2011 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#
# -----------------------------------------------------------------------------
import pyglet.gl as gl
import ctypes
import math
import numpy as np
import sys

class TextureAtlas:
    '''
    Group multiple small data regions into a larger texture.

    The algorithm is based on the article by Jukka Jylänki : "A Thousand Ways
    to Pack the Bin - A Practical Approach to Two-Dimensional Rectangle Bin
    Packing", February 27, 2010. More precisely, this is an implementation of
    the Skyline Bottom-Left algorithm based on C++ sources provided by Jukka
    Jylänki at: http://clb.demon.fi/files/RectangleBinPack/

    Example usage:
    --------------

    atlas = TextureAtlas(512,512,3)
    region = atlas.get_region(20,20)
    ...
    atlas.set_region(region, data)
    '''

    def __init__(self, width=1024, height=1024, depth=1):
        '''
        Initialize a new atlas of given size.

        Parameters
        ----------

        width : int
            Width of the underlying texture

        height : int
            Height of the underlying texture

        depth : 1 or 3
            Depth of the underlying texture
        '''
        self.width  = int(math.pow(2, int(math.log(width, 2) + 0.5)))
        self.height = int(math.pow(2, int(math.log(height, 2) + 0.5)))
        self.depth  = depth
        self.nodes  = [ (0,0,self.width), ]
        self.data   = np.zeros((self.height, self.width, self.depth),
                               dtype=np.ubyte)
        self.texid  = None
        self.used   = 0


    def getTextureID(self):
        return self.texid
        
    def upload(self):
        '''
        Upload atlas data into video memory.
        '''
        gl.glEnable( gl.GL_TEXTURE_2D )

        if self.texid is None:
            self.texid = gl.GLuint(0)
            gl.glGenTextures(1,ctypes.byref(self.texid))


        gl.glBindTexture( gl.GL_TEXTURE_2D, self.texid )

        gl.glTexParameteri( gl.GL_TEXTURE_2D,
                            gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP )
        gl.glTexParameteri( gl.GL_TEXTURE_2D,
                            gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP )
        gl.glTexParameteri( gl.GL_TEXTURE_2D,
                            gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
        gl.glTexParameteri( gl.GL_TEXTURE_2D,
                            gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )

        if self.depth == 1:
            gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_ALPHA,
                             self.width, self.height, 0,
                             gl.GL_ALPHA, gl.GL_UNSIGNED_BYTE, self.data.ctypes )
        elif self.depth == 3:
            gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_RGB,
                             self.width, self.height, 0,
                             gl.GL_RGB, gl.GL_UNSIGNED_BYTE, self.data.ctypes )
        else:
            gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_RGBA,
                             self.width, self.height, 0,
                             gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, self.data.ctypes )

        gl.glBindTexture( gl.GL_TEXTURE_2D, 0 )

#        print 'Updated Data: ',self.depth
#        print 'self.data.shape: ', self.data.shape


    def draw(self):
        gl.glBindTexture( gl.GL_TEXTURE_2D, self.texid )
        
        gl.glPushMatrix( )  
        gl.glTranslatef( 0, self.height, 0 )   
        gl.glPushMatrix( )
        gl.glEnable( gl.GL_TEXTURE_2D )
        gl.glBindTexture( gl.GL_TEXTURE_2D, self.texid )
        gl.glColor4f(1,1,1,1)  
        gl.glBegin( gl.GL_QUADS )
        gl.glTexCoord2f( 0, 1 ), gl.glVertex2f( 0,-self.height )
        gl.glTexCoord2f( 0, 0 ), gl.glVertex2f( 0,0 )
        gl.glTexCoord2f( 1, 0), gl.glVertex2f( self.width,0 )
        gl.glTexCoord2f( 1, 1 ), gl.glVertex2f( self.width, -self.height )
        gl.glEnd( )

        gl.glPopMatrix( )
        gl.glPopMatrix( )
        gl.glFinish()
        
        
    def set_region(self, region, data):
        '''
        Set a given region width provided data.

        Parameters
        ----------

        region : (int,int,int,int)
            an allocated region (x,y,width,height)

        data : numpy array
            data to be copied into given region
        '''

        x, y, width, height = region
        self.data[y:y+height,x:x+width, :] = data



    def get_region(self, width, height):
        '''
        Get a free region of given size and allocate it

        Parameters
        ----------

        width : int
            Width of region to allocate

        height : int
            Height of region to allocate

        Return
        ------
            A newly allocated region as (x,y,width,height) or (-1,-1,0,0)
        '''

        best_height = sys.maxint
        best_index = -1
        best_width = sys.maxint
        region = 0, 0, width, height

        for i in range(len(self.nodes)):
            y = self.fit(i, width, height)
            if y >= 0:
                node = self.nodes[i]
                if (y+height < best_height or
                    (y+height == best_height and node[2] < best_width)):
                    best_height = y+height
                    best_index = i
                    best_width = node[2]
                    region = node[0], y, width, height

        if best_index == -1:
            return -1,-1,0,0

        node = region[0], region[1]+height, width
        self.nodes.insert(best_index, node)

        i = best_index+1
        while i < len(self.nodes):
            node = self.nodes[i]
            prev_node = self.nodes[i-1]
            if node[0] < prev_node[0]+prev_node[2]:
                shrink = prev_node[0]+prev_node[2] - node[0]
                x,y,w = self.nodes[i]
                self.nodes[i] = x+shrink, y, w-shrink
                if self.nodes[i][2] <= 0:
                    del self.nodes[i]
                    i -= 1
                else:
                    break
            else:
                break
            i += 1

        self.merge()
        self.used += width*height
        return region



    def fit(self, index, width, height):
        '''
        Test if region (width,height) fit into self.nodes[index]

        Parameters
        ----------

        index : int
            Index of the internal node to be tested

        width : int
            Width or the region to be tested

        height : int
            Height or the region to be tested

        '''

        node = self.nodes[index]
        x,y = node[0], node[1]
        width_left = width        
        
        if x+width > self.width:
            return -1

        i = index
        while width_left > 0:
            node = self.nodes[i]
            y = max(y, node[1])
            if y+height > self.height:
                return -1
            width_left -= node[2]
            i += 1
        return y



    def merge(self):
        '''
        Merge nodes
        '''

        i = 0
        while i < len(self.nodes)-1:
            node = self.nodes[i]
            next_node = self.nodes[i+1]
            if node[1] == next_node[1]:
                self.nodes[i] = node[0], node[1], node[2]+next_node[2]
                del self.nodes[i+1]
            else:
                i += 1
                
    def deleteTexture(self):
        gl.glDeleteTextures(1, self.texid)
        
    def __del__(self):
        self.deleteTexture()
        
#from psychopy import visual,core
#
#class AtlasWindow(visual.Window):
#    def __init__(self,*args,**kwargs):
#        visual.Window.__init__(self,*args,**kwargs)
#
#        window_width, window_height=args[0]
#        
#        gl.glViewport( 0, 0, window_width, window_height )
#        gl.glMatrixMode( gl.GL_PROJECTION )
#        gl.glLoadIdentity( )
#        gl.glOrtho( 0, window_width, 0, window_height, -1, 1 )
#        gl.glMatrixMode( gl.GL_MODELVIEW )
#        gl.glLoadIdentity( )
#        gl.glEnable( gl.GL_TEXTURE_2D )
#        gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
#        gl.glDisable( gl.GL_DEPTH_TEST )
#        gl.glEnable( gl.GL_BLEND )
#        gl.glEnable( gl.GL_COLOR_MATERIAL )
#        gl.glColorMaterial( gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE )
#        gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
#
#
#    def onResize( self, width, height ):
#        gl.glViewport( 0, 0, width, height )
#        gl.glMatrixMode( gl.GL_PROJECTION )
#        gl.glLoadIdentity( )
#        gl.glOrtho( 0, width, 0, height, -1, 1 )
#        gl.glMatrixMode( gl.GL_MODELVIEW )
#        gl.glLoadIdentity( )