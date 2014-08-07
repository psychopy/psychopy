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
from abc import ABCMeta, abstractmethod, abstractproperty
from psychopy.visual.window import BaseFramePacker

class ProjectorFramePacker(BaseFramePacker):
    '''Class which packs 3 monochrome images per RGB frame allowing 180Hz stimuli
    with DLP projectors (such as TI LightCrafter 4500) operating in structured light mode.
    '''

    def __init__(self):
        self.flipCounter = 0
        pass

    def setWindowAndGL(self, window, GL):
        '''Associate a window and GL context with the frame packer'''
        self.window = window
        self.GL = GL
         # enable Blue channel initially since the DLP output sequence is BGR
        self.GL.glColorMask(False, False, True, True)
    
    def getActualFrameRate(self):
        return 180.0

    def shouldHardwareFlipThisFrame(self):
        '''Return True if all channels of the RGB frame have been filled with monochrome images'''
        return self.flipCounter %3 == 2

    def afterHardwareFlip(self, clearBuffer):
        '''Mask RGB cyclically after each flip.  
        We ignore clearBuffer and just auto-clear after each hardware flip.
        '''
        if self.shouldHardwareFlipThisFrame():
            self.GL.glClear(self.GL.GL_COLOR_BUFFER_BIT) 

        self.flipCounter += 1
        if self.flipCounter %3 == 0:
            self.GL.glColorMask(False, True, False, True)  # enable green
        elif self.flipCounter %3 == 1:
            self.GL.glColorMask(True, False, False, True)  # enable red
        elif self.flipCounter %3 == 2:
            self.GL.glColorMask(False, False, True, True)  # enable blue
        