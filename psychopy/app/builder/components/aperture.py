# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * # to get the template visual component
from os import path

__author__ = 'Jeremy Gray' # March 2011; builder-component for Yuri Spitsyn's visual.Aperture class

thisFolder = path.abspath(path.dirname(__file__)) # the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'aperture.png')

class ApertureComponent(VisualComponent):
    """An event class for using GL stencil to restrict the viewing area to a circle of a given size and position"""
    def __init__(self, exp, parentName, name='aperture', units='pix',
                 size=120, pos=(0,0), startTime=0.0, duration=''):
        #initialise main parameters
        VisualComponent.__init__(self, parentName, name=name, units=units, 
                    pos=pos, startTime=startTime, duration=duration)
        self.type = 'Aperture'
        self.url = "http://www.psychopy.org/builder/components/aperture.html"
        self.exp = exp #so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.parentName = parentName
        #params:
        self.order = ['name', 'size', 'pos'] # make sure this is at top
        self.params['size'] = Param(size, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="size of the aperture in pix")
        self.params['pos'] = Param(pos, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="position on the screen")
        self.params['duration'] = Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[], hint="An aperture is on for the entire duration of the routine, start to finish. aperture.disable() in a code component could be used to turn it on or off.")
        del self.params['ori']
        del self.params['startTime']
        del self.params['color']
        del self.params['colorSpace']
        
    def writeInitCode(self, buff):
        #do writing of init
        buff.writeIndented("%(name)s=visual.Aperture(win=win, size=%(size)s, pos=%(pos)s, units='pix') # enabled by default\n" % (self.params))  
    
    def writeFrameCode(self, buff):
       """No code that will be called every frame for an aperture
       """
       # an aperture is imposed on the whole window, persistently, via enable() or disable()
       # there's nothing to draw or do each frame, so we need to override the default for VisualComponent:
       pass
        
    def writeRoutineEndCode(self, buff):
        buff.writeIndented("%(name)s.disable()\n" % (self.params))
    
