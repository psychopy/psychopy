# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * # to get the template visual component
from os import path
from psychopy.app.builder import components #for getInitVals()

__author__ = 'Jeremy Gray, Jon Peirce'
# March 2011; builder-component for Yuri Spitsyn's visual.Aperture class
# July 2011: jwp added the code for it to be enabled only when needed

thisFolder = path.abspath(path.dirname(__file__)) # the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'aperture.png')
tooltip = 'Aperture: restrict the drawing of stimuli to a given region'

class ApertureComponent(VisualComponent):
    """An event class for using GL stencil to restrict the viewing area to a
    circle or square of a given size and position"""
    def __init__(self, exp, parentName, name='aperture', units='norm',
                size=1, pos=(0,0),
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        #initialise main parameters
        VisualComponent.__init__(self, exp, parentName, name=name, units=units,
                    pos=pos,size=size,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type = 'Aperture'
        self.url = "http://www.psychopy.org/builder/components/aperture.html"
        self.exp.requirePsychopyLibs(['visual'])
        #params:
        #NB make some adjustments on the params defined by _visual component
        self.order = ['name', 'size', 'pos'] # make sure this is at top
        self.params['size'].hint = "How big is the aperture? (a single number for diameter)"
        self.params['size'].label="Size"
        self.params['pos'].hint = "Where is the aperture centred?"
        self.params['startVal'].hint = "When does the aperture come into effect?"
        self.params['stopVal'].hint="When does the aperture stop having an effect?"
        #inherited from _visual component but not needed
        del self.params['ori']
        del self.params['color']
        del self.params['colorSpace']
        del self.params['opacity']

    def writeInitCode(self, buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        #do writing of init
        inits = components.getInitVals(self.params)
        buff.writeIndented("%(name)s = visual.Aperture(win=win, name='%(name)s',\n" % (inits))
        buff.writeIndented("    "+unitsStr+"size=%(size)s, pos=%(pos)s)\n" % (inits))
        buff.writeIndented("%(name)s.disable()  # disable until its actually used\n" %(inits))
    def writeFrameCode(self, buff):
        """Only activate the aperture for the required frames
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.enable()\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.disable()\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #set parameters that need updating every frame
        if self.checkNeedToUpdate('set every frame'):#do any params need updating? (this method inherited from _base)
            buff.writeIndented("if %(name)s.status == STARTED:  # only update if being drawn\n" %(self.params))
            buff.setIndentLevel(+1, relative=True)#to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)#to exit the if block

    def writeRoutineEndCode(self, buff):
        buff.writeIndented("%(name)s.disable()  # just in case it was left enabled\n" % (self.params))

