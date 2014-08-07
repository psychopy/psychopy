#!/usr/bin/env python2

'''A class to pack multiple monochrome images into a single RGB frame for 
TI LightCrafter 4500 (and similar) DLP projectors to achieve 180Hz stimuli'''

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

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
        