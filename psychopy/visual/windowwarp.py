#!/usr/bin/env python2

'''
Copyright (C) 2014 Allen Institute for Brain Science
                
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License Version 3
as published by the Free Software Foundation on 29 June 2007.

This program is distributed WITHOUT WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE OR ANY OTHER WARRANTY, EXPRESSED OR IMPLIED.  
See the GNU General Public License Version 3 for more details.

You should have received a copy of the GNU General Public License along with this program.  
If not, see http://www.gnu.org/licenses/

'''

import sys
import os
import numpy as np
import psychopy  # so we can get the __path__
from psychopy import core, platform_specific, logging, prefs, monitors, event
from psychopy.visual.window import BaseWarper
from abc import ABCMeta, abstractmethod, abstractproperty
from OpenGL.arrays import ArrayDatatype as ADT

class Warper(BaseWarper):
    '''Class to perform spherical, cylindrical, warpfile, or None (disabled) warps'''
    def __init__(self, 
                 warp=None, 
                 warpfile = None, 
                 warpGridsize = 300, 
                 eyepoint=(0.5, 0.5), 
                 flipHorizontal=False, 
                 flipVertical=False):
        """
        These attributes define the projection and can be altered 
        dynamically using the changeProjection() method.

        :Parameters:

            warp : 'spherical', 'cylindrical, 'warpfile' or *None*
                This table gives the main properties of each projection:
                              eyepoint        parallel   parallel      radial distance
                Warp          modifies warp   verticals  horizontals   perspective correct
                ---------------------------------------------------------------------------              
                Spherical      y              n          n             y
                Cylindrical    y              y          n             n
                warpfile       n              -          -             - 
                None           n              y          y             n
            warpfile : *None* or filename containing Blender and Paul Bourke compatible warp
                definition.  (see http://paulbourke.net/dome/warpingfisheye/) 
            warpGridsize : 300
                Defines the resolution of the warp in both X and Y when not using a warpfile.
                Typical values would be 64-300 trading off tolerance for jaggies for speed.
            eyepoint : [0.5, 0.5] center of the screen
                Position of the eye in X and Y as a fraction of the normailized screen width and height.
                [0,0] is the bottom left of the screen.  [1,1] is the top right of the screen.
            flipHorizontal: False
                Flip the entire output horizontally.  Useful for back projection scenarious.
            flipVertical: False
                Flip the entire output vertically. useful if projector is flipped upside down.

            :note: The eye distance from the screen is defined as part of the Monitor setup.
        """

        self.warp = warp
        self.warpfile = warpfile
        self.warpGridsize = warpGridsize
        self.eyepoint = eyepoint
        self.flipHorizontal = flipHorizontal
        self.flipVertical = flipVertical
        self.initDefaultWarpSize()

    def setWindowAndGL(self, window, GL):
        '''Associate a window and GL context with the warper'''
        self.window = window
        self.GL = GL
        #   get the eye distance from the monitor object,
        #   but the pixel dimensions from the actual window object
        w, h = window.size
        self.aspect = float(w) / h
        self.dist_cm = window.monitor.getDistance()
        if self.dist_cm is None:
            # create a fake monitor if one isn't defined
            self.dist_cm = 30.0
            self.mon_width_cm = 50.0
            logging.warning('Monitor is not calibrated')
        else:
            self.mon_width_cm = window.monitor.getWidth()
        self.mon_height_cm = self.mon_width_cm / self.aspect
        self.mon_width_pix = w 
        self.mon_height_pix = h
        self.changeProjection(self.warp, self.warpfile, self.eyepoint)    
    
    def drawWarp(self):
        ''' 
        Warp the output, using the vertex, texture, and optionally an opacity array
        '''
        self.GL.glUseProgram(0)
        self.GL.glColorMask(True, True, True, True) #jayb
            
        #point to color (opacity)
        if self.gl_color is not None:
            self.GL.glEnableClientState(self.GL.GL_COLOR_ARRAY)
            self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, self.gl_color)
            self.GL.glColorPointer(4, self.GL.GL_FLOAT, 0, None)
            self.GL.glEnable(self.GL.GL_BLEND)
            self.GL.glBlendFunc(self.GL.GL_SRC_ALPHA, self.GL.GL_ZERO)
        
        # point to vertex data
        self.GL.glEnableClientState(self.GL.GL_VERTEX_ARRAY)
        self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, self.gl_vb)
        self.GL.glVertexPointer(2, self.GL.GL_FLOAT, 0, None)
            
        #point to texture
        self.GL.glEnableClientState(self.GL.GL_TEXTURE_COORD_ARRAY)
        self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, self.gl_tb)
        self.GL.glTexCoordPointer(2, self.GL.GL_FLOAT, 0, None)

        #draw quads
        self.GL.glDrawArrays (self.GL.GL_QUADS, 0, self.nverts)

        # cleanup
        self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, 0)
        self.GL.glDisableClientState(self.GL.GL_VERTEX_ARRAY)
        self.GL.glDisableClientState(self.GL.GL_TEXTURE_COORD_ARRAY)

        if self.gl_color is not None:
            self.GL.glBlendFunc(self.GL.GL_SRC_ALPHA, self.GL.GL_ONE_MINUS_SRC_ALPHA)
            self.GL.glDisableClientState(self.GL.GL_COLOR_ARRAY)

    def initDefaultWarpSize(self):
        self.xgrid = self.warpGridsize
        self.ygrid = self.warpGridsize

    def changeProjection (self, warp, warpfile = None, eyepoint = [0.5,0.5], flipHorizontal = False, flipVertical = False):
        '''Allows changing the warp method on the fly as well as at initialization time'''
        self.warp = warp
        self.warpfile = warpfile
        self.eyepoint = eyepoint
        self.flipHorizontal = flipHorizontal
        self.flipVertical = flipVertical

        # warpfile might have changed the size...
        self.initDefaultWarpSize()  

        if (self.warp == None):
            self.projectionNone()
        elif (self.warp == 'spherical'):
            self.projectionSphericalOrCylindrical(False)
        elif self.warp == 'cylindrical':
            self.projectionSphericalOrCylindrical(True)
        elif self.warp == 'warpfile':
            self.projectionWarpfile()
        else:
            raise 'Unknown warp specification'

    def projectionNone(self):
        '''No warp, same projection as original PsychoPy'''
        # Vertex data 
        v0 = ( -1.0, -1.0)
        v1 = ( -1.0,  1.0)
        v2 = (  1.0,  1.0)
        v3 = (  1.0, -1.0)
        
        # Texture coordinates
        t0 = ( 0.0, 0.0)
        t1 = ( 0.0, 1.0)
        t2 = ( 1.0, 1.0)
        t3 = ( 1.0, 0.0)
        
        vertices = np.array( [ v0, v1, v2, v3 ], 'float32' )
        tcoords = np.array( [ t0, t1, t2, t3 ], 'float32' )

        #draw four quads during rendering loop
        self.nverts = 4  
        self.createVertexAndTextureBuffers (vertices, tcoords)        

    def projectionSphericalOrCylindrical(self, isCylindrical=False):
        '''Correct perspective on flat screen using either a spherical or cylindrical projection.'''
        self.nverts = (self.xgrid-1)*(self.ygrid-1)*4

        # eye position in cm
        xEye = self.eyepoint[0] * self.mon_width_cm
        yEye = self.eyepoint[1] * self.mon_height_cm

        #create vertex grid array, and texture coords
        #times 4 for quads
        vertices = np.zeros(((self.xgrid-1)*(self.ygrid-1)*4, 2),dtype='float32')
        tcoords = np.zeros(((self.xgrid-1)*(self.ygrid-1)*4, 2),dtype='float32')

        equalDistanceX = np.linspace(0, self.mon_width_cm, self.xgrid)
        equalDistanceY = np.linspace(0, self.mon_height_cm, self.ygrid)

        # vertex coordinates        
        x_c = np.linspace(-1.0,1.0,self.xgrid)
        y_c = np.linspace(-1.0,1.0,self.ygrid)
        x_coords, y_coords = np.meshgrid(x_c,y_c)

        x = np.zeros(((self.xgrid), (self.ygrid)),dtype='float32')
        y = np.zeros(((self.xgrid), (self.ygrid)),dtype='float32')

        x[:,:] = equalDistanceX - xEye
        y[:,:] = equalDistanceY - yEye
        y = np.transpose(y)

        r = np.sqrt(np.square(x) + np.square(y) + np.square(self.dist_cm))

        azimuth = np.arctan(x / self.dist_cm)
        altitude = np.arcsin(y / r)

        # calculate the texture coordinates
        if isCylindrical:
            tx = self.dist_cm * np.sin(azimuth)
            ty = self.dist_cm * np.sin(altitude)
        else:
            tx = self.dist_cm * (1 + x / r)- self.dist_cm
            ty = self.dist_cm * (1 + y / r) - self.dist_cm

        # prevent div0
        azimuth[azimuth==0] = np.finfo(np.float32).eps
        altitude[altitude==0] = np.finfo(np.float32).eps

        # the texture coordinates (which are now lying on the sphere)
        # need to be remapped back onto the plane of the display.
        # This effectively stretches the coordinates away from the eyepoint.
   
        if isCylindrical:
            tx = tx * azimuth / np.sin(azimuth) 
            ty = ty * altitude / np.sin(altitude)
        else:
            centralAngle = np.arccos (np.cos(altitude) * np.cos(np.abs(azimuth)))
            # distance from eyepoint to texture vertex
            arcLength = centralAngle * self.dist_cm
            # remap the texture coordinate
            theta = np.arctan2(ty, tx)
            tx = arcLength * np.cos(theta)
            ty = arcLength * np.sin(theta)

        u_coords = tx / self.mon_width_cm + 0.5
        v_coords = ty / self.mon_height_cm + 0.5

        #loop to create quads
        vdex = 0
        for y in xrange(0,self.ygrid-1):
            for x in xrange(0,self.xgrid-1):
                index = y*(self.xgrid) + x
                
                vertices[vdex+0,0] = x_coords[y,x]
                vertices[vdex+0,1] = y_coords[y,x]
                vertices[vdex+1,0] = x_coords[y,x+1]
                vertices[vdex+1,1] = y_coords[y,x+1]
                vertices[vdex+2,0] = x_coords[y+1,x+1]
                vertices[vdex+2,1] = y_coords[y+1,x+1]
                vertices[vdex+3,0] = x_coords[y+1,x]
                vertices[vdex+3,1] = y_coords[y+1,x]
                
                tcoords[vdex+0,0] = u_coords[y,x]
                tcoords[vdex+0,1] = v_coords[y,x]
                tcoords[vdex+1,0] = u_coords[y,x+1]
                tcoords[vdex+1,1] = v_coords[y,x+1]
                tcoords[vdex+2,0] = u_coords[y+1,x+1]
                tcoords[vdex+2,1] = v_coords[y+1,x+1]
                tcoords[vdex+3,0] = u_coords[y+1,x]
                tcoords[vdex+3,1] = v_coords[y+1,x]
                
                vdex += 4
        self.createVertexAndTextureBuffers (vertices, tcoords)        

    def projectionWarpfile (self):
        ''' Use a warp definition file to create the projection.
            See: http://paulbourke.net/dome/warpingfisheye/ 
        '''
        try:
            fh = open (self.warpfile)
            lines = fh.readlines()
            fh.close()
            filetype = int(lines[0])
            rc = map(int, lines[1].split())
            cols, rows = rc[0], rc[1]
            warpdata = np.loadtxt(self.warpfile, skiprows=2)
        except:
            error = 'Unable to read warpfile: ' + self.warpfile
            logging.warning(error)
            print error
            return

        if (cols * rows != warpdata.shape[0] or warpdata.shape[1] != 5 or filetype != 2 ):
            error = 'warpfile data incorrect: ' + self.warpfile
            logging.warning(error)
            print error
            return

        self.xgrid = cols
        self.ygrid = rows
          
        self.nverts = (self.xgrid-1)*(self.ygrid-1)*4

        # create vertex grid array, and texture coords times 4 for quads
        vertices = np.zeros(((self.xgrid-1)*(self.ygrid-1)*4, 2),dtype='float32')
        tcoords = np.zeros(((self.xgrid-1)*(self.ygrid-1)*4, 2),dtype='float32')
        # opacity is RGBA
        opacity = np.ones(((self.xgrid-1)*(self.ygrid-1)*4,4),dtype='float32')

        #loop to create quads
        vdex = 0
        for y in xrange(0,self.ygrid-1):
            for x in xrange(0,self.xgrid-1):
                index = y*(self.xgrid) + x
                
                vertices[vdex+0,0] = warpdata[index,0]          #x_coords[y,x]
                vertices[vdex+0,1] = warpdata[index,1]          #y_coords[y,x]
                vertices[vdex+1,0] = warpdata[index+1,0]        #x_coords[y,x+1]
                vertices[vdex+1,1] = warpdata[index+1,1]        #y_coords[y,x+1]
                vertices[vdex+2,0] = warpdata[index+cols+1,0]   #x_coords[y+1,x+1]
                vertices[vdex+2,1] = warpdata[index+cols+1,1]   #y_coords[y+1,x+1]
                vertices[vdex+3,0] = warpdata[index+cols,0]     #x_coords[y+1,x]
                vertices[vdex+3,1] = warpdata[index+cols,1]     #y_coords[y+1,x]
                
                tcoords[vdex+0,0] = warpdata[index,2]           # u_coords[y,x]
                tcoords[vdex+0,1] = warpdata[index,3]           # v_coords[y,x]
                tcoords[vdex+1,0] = warpdata[index+1,2]         # u_coords[y,x+1]
                tcoords[vdex+1,1] = warpdata[index+1,3]         # v_coords[y,x+1]
                tcoords[vdex+2,0] = warpdata[index+cols+1,2]    # u_coords[y+1,x+1]
                tcoords[vdex+2,1] = warpdata[index+cols+1,3]    # v_coords[y+1,x+1]
                tcoords[vdex+3,0] = warpdata[index+cols,2]      # u_coords[y+1,x]
                tcoords[vdex+3,1] = warpdata[index+cols,3]      # v_coords[y+1,x]
                
                opacity[vdex,3] = warpdata[index, 4]
                opacity[vdex+1,3] = warpdata[index+1, 4]
                opacity[vdex+2,3] = warpdata[index+cols+1, 4]
                opacity[vdex+3,3] = warpdata[index+cols, 4]

                vdex += 4

        self.createVertexAndTextureBuffers (vertices, tcoords, opacity)        
        
    def createVertexAndTextureBuffers(self, vertices, tcoords, opacity = None):
        ''' Allocate hardware buffers for vertices, texture coordinates, and optionally opacity '''
        if self.flipHorizontal:
            vertices[:,0] = -vertices[:,0]
        if self.flipVertical:
            vertices[:,1] = -vertices[:,1]

        self.GL.glEnableClientState (self.GL.GL_VERTEX_ARRAY)

        #vertex buffer in hardware
        self.gl_vb = self.GL.GLuint()
        self.GL.glGenBuffers(1 , self.gl_vb)
        self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, self.gl_vb)
        self.GL.glBufferData(self.GL.GL_ARRAY_BUFFER, ADT.arrayByteCount(vertices), ADT.voidDataPointer(vertices), self.GL.GL_STATIC_DRAW)

        #vertex buffer tdata in hardware
        self.gl_tb = self.GL.GLuint()
        self.GL.glGenBuffers(1 , self.gl_tb)
        self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, self.gl_tb)
        self.GL.glBufferData(self.GL.GL_ARRAY_BUFFER, ADT.arrayByteCount(tcoords), ADT.voidDataPointer(tcoords), self.GL.GL_STATIC_DRAW)

        # opacity buffer in hardware (only for warp files)
        if opacity is not None:
            self.gl_color = self.GL.GLuint()
            self.GL.glGenBuffers(1 , self.gl_color)
            self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, self.gl_color)
            #convert opacity to RGBA, one point for each corner of the quad
            self.GL.glBufferData(self.GL.GL_ARRAY_BUFFER, ADT.arrayByteCount(opacity), ADT.voidDataPointer(opacity), self.GL.GL_STATIC_DRAW)
        else:
            self.gl_color = None    

        self.GL.glBindBuffer(self.GL.GL_ARRAY_BUFFER, 0)
        self.GL.glDisableClientState(self.GL.GL_VERTEX_ARRAY)

