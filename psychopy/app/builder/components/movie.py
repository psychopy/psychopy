# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'movie.png')

class MovieComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='movie', movie='', 
        units='window units', 
        pos=[0,0], size='', ori=0, startTime=0.0, duration=1.0, forceEndTrial=False):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units, 
                    pos=pos, size=size, ori=ori, startTime=startTime, duration=duration)
        self.type='Movie'
        self.url="http://www.psychopy.org/builder/components/movie.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.order = ['name','startTime','duration','forceEndTrial']
        
        #params
        self.params['name'] = Param(name, valType='code', allowedTypes=[])
        #these are normally added but we don't want them for a movie            
        del self.params['color']
        del self.params['colorSpace']
        self.params['movie']=Param(movie, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="A filename for the movie (including path)")     
        self.params['duration']=Param(duration, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="NB The movie will actually play for its duration - this is only used to represent the stimulus in the Routine window, ")   
        self.params['forceEndTrial']=Param(forceEndTrial, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should the end of the movie cause the end of the routine (e.g. trial)?")
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s=visual.MovieStim(win=win, filename=%(movie)s, name='%(name)s',\n" %(self.params))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s" %(self.params))
        if self.params['size'].val != '': buff.writeIndented(", size=%(size)s"%(self.params))
        buff.writeIndented(")\n")
        
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        self.writeTimeTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.setIndentLevel(1, relative=True)#because of the 'if' statement of the time test
        #set parameters that need updating every frame
        self.writeParamUpdates(buff, 'set every frame')
        #draw the stimulus
        buff.writeIndented("%(name)s.draw()\n" %(self.params))
        buff.setIndentLevel(-1, relative=True)
        #do force end of trial code
        if self.params['forceEndTrial'].val==True:
            buff.writeIndented("if %s.playing==visual.FINISHED: continueRoutine=False\n" %(self.params['name']))
            
    def writeTimeTestCode(self,buff):
        """Write the code for each frame that tests whether the component is being
        drawn/used.
        """
        buff.writeIndented("if t>=%(startTime)s and %(name)s.playing!=visual.FINISHED:\n" %(self.params))
        
