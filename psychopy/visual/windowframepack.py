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
import pyglet
GL = pyglet.gl


class ProjectorFramePacker():
    '''Class which packs 3 monochrome images per RGB frame allowing 180Hz stimuli
    with DLP projectors (such as TI LightCrafter 4500) operating in structured light mode.
    '''
    def __init__(self, win):
        '''
        :Parameters:
            win : Handle to the window.
        '''
        self.win = win
        # monkey patch window
        win._startOfFlip = self.startOfFlip
        win._endOfFlip = self.endOfFlip

        # This part is increasingly ugly.  Add a function to set these values?
        win._monitorFrameRate = 180.0
        win.monitorFramePeriod=1.0/win._monitorFrameRate
        win._refreshThreshold = (1.0/win._monitorFrameRate)*1.2

        #enable Blue initially, since projector output sequence is BGR
        GL.glColorMask(False, False, True, True)
        self.flipCounter = 0
    
    def startOfFlip(self):
        '''Return True if all channels of the RGB frame have been filled with monochrome images,
        and the associated window should perform a hardware flip'''
        return self.flipCounter %3 == 2

    def endOfFlip(self, clearBuffer):
        '''Mask RGB cyclically after each flip.  
        We ignore clearBuffer and just auto-clear after each hardware flip.
        '''
        if self.flipCounter %3 == 2:
            GL.glClear(GL.GL_COLOR_BUFFER_BIT) 

        self.flipCounter += 1
        if self.flipCounter %3 == 0:
            GL.glColorMask(False, True, False, True)  # enable green
        elif self.flipCounter %3 == 1:
            GL.glColorMask(True, False, False, True)  # enable red
        elif self.flipCounter %3 == 2:
            GL.glColorMask(False, False, True, True)  # enable blue

        