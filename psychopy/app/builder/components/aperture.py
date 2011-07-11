# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * # to get the template visual component
from os import path

__author__ = 'Jeremy Gray, Jon Peirce' 
# March 2011; builder-component for Yuri Spitsyn's visual.Aperture class
# July 2011: jwp added the code for it to be enabled only when needed

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
        self.params['startTime']=Param(startTime, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The time that the aperture starts to be used for drawing")
        self.params['duration']=Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="The duration for which the aperture is used for drawing")
        self.order=['name','startTime','duration']#make name come first (others don't matter)
        del self.params['ori']
        del self.params['color']
        del self.params['colorSpace']
        
    def writeInitCode(self, buff):
        #do writing of init
        buff.writeIndented("%(name)s=visual.Aperture(win=win, size=%(size)s, pos=%(pos)s, units='pix') # enabled by default\n" % (self.params))  
        buff.writeIndented("%(name)s.disable()\n" %(self.params))
    def writeFrameCode(self, buff):
        """Only activate the aperture for the required frames
        """
        buff.writeIndented("if %(startTime)s <= t < (%(startTime)s+%(duration)s) and not %(name)s.enabled:\n" %(self.params))
        buff.writeIndented("    %(name)s.enable()#needs to start\n" %(self.params))
        buff.writeIndented("elif t>=(%(startTime)s+%(duration)s) and %(name)s.enabled:\n" %(self.params))
        buff.writeIndented("    %(name)s.disable()#needs to finish\n" %(self.params))
        
    def writeRoutineEndCode(self, buff):
        buff.writeIndented("%(name)s.disable() #this was probably done anyway\n" % (self.params))
    
