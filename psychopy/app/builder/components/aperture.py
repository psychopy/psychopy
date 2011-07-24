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
    def __init__(self, exp, parentName, name='aperture', units='norm',
                size=[1,1], pos=(0,0),
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0):
        #initialise main parameters
        VisualComponent.__init__(self, parentName, name=name, units=units, 
                    pos=pos, 
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal)
        self.type = 'Aperture'
        self.url = "http://www.psychopy.org/builder/components/aperture.html"
        self.exp = exp #so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.parentName = parentName
        #params:
        #NB make some adjustments on the params defined by _visual component
        self.order = ['name', 'size', 'pos'] # make sure this is at top
        self.params['size'].hint = "Ho big is the apperture?"
        self.params['pos'].hint = "Where is the apperture centred?"
        self.params['startVal'].hint = "When does the apperture come into effect?"
        self.params['stopVal'].hint="When does the apperture stop having an effect?"
        del self.params['ori']
        del self.params['color']
        del self.params['colorSpace']
        
    def writeInitCode(self, buff):
        #do writing of init
        buff.writeIndented("%(name)s=visual.Aperture(win=win, name='%(name)s,\n" % (self.params))
        buff.writeIndented("    size=%(size)s, pos=%(pos)s, units='pix')\n" % (self.params))
        buff.writeIndented("%(name)s.disable() # is enabled by default\n" %(self.params))
    def writeFrameCode(self, buff):
        """Only activate the aperture for the required frames
        """
        #enable aperture
        if self.params['duration'].val=='':#infinite duration
            buff.writeIndented("if %(startTime)s <= t and not %(name)s.enabled:\n" %(self.params))
        else: buff.writeIndented("if %(startTime)s <= t < (%(startTime)s+%(duration)s) and not %(name)s.enabled:\n" %(self.params))
        buff.writeIndented("    %(name)s.enable()#needs to start\n" %(self.params))
        #disable aperture
        if self.params['duration'].val!='':#infinite duration
            buff.writeIndented("elif t>=(%(startTime)s+%(duration)s) and %(name)s.enabled:\n" %(self.params))
            buff.writeIndented("    %(name)s.disable()#needs to finish\n" %(self.params))
        
    def writeRoutineEndCode(self, buff):
        buff.writeIndented("%(name)s.disable() #just in case it was left enabled\n" % (self.params))
    
