# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'movie.png')
tooltip = 'Movie: play movie files'

class MovieComponent(VisualComponent):
    """An event class for presenting image-based stimuli"""
    def __init__(self, exp, parentName, name='movie', movie='',
                units='from exp settings',
                pos=[0,0], size='', ori=0,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim='',
                forceEndRoutine=False):
        #initialise main parameters from base stimulus
        VisualComponent.__init__(self,parentName,name=name, units=units,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Movie'
        self.url="http://www.psychopy.org/builder/components/movie.html"
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual'])
        self.order = ['forceEndRoutine']#comes immediately after name and timing params

        #params
        self.params['stopVal'].hint="Leave blank simply to play the movie for its full duration"
        self.params['movie']=Param(movie, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="A filename for the movie (including path)")
        self.params['forceEndRoutine']=Param(forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should the end of the movie cause the end of the routine (e.g. trial)?")
        #these are normally added but we don't want them for a movie
        del self.params['color']
        del self.params['colorSpace']
    def writeInitCode(self,buff):
        #if the movie is constant then load it once at beginning of script.
        #if it changes each repeat then we should wait and creat the entire object at
        #Routine start
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        if self.params['movie'].updates=='constant':
            initVals = components.getInitVals(self.params)
            buff.writeIndented("%s=visual.MovieStim(win=win, name='%s',%s\n" %(initVals['name'],initVals['name'],unitsStr))
            buff.writeIndented("    filename=%(movie)s,\n" %(self.params))
            buff.writeIndented("    ori=%(ori)s, pos=%(pos)s" %(self.params))
            if self.params['size'].val != '': buff.writeIndented(", size=%(size)s"%(self.params))
            buff.writeIndented(")\n")
    def writeRoutineStartCode(self,buff):
        #do we need units code?
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        if self.params['movie'].updates!='constant':
            initVals = components.getInitVals(self.params)
            buff.writeIndented("%s=visual.MovieStim(win=win, name='%s',%s\n" %(initVals['name'],initVals['name'],unitsStr))
            buff.writeIndented("    filename=%(movie)s,\n" %(self.params))
            buff.writeIndented("    ori=%(ori)s, pos=%(pos)s" %(self.params))
            if self.params['size'].val != '': buff.writeIndented(", size=%(size)s"%(self.params))
            buff.writeIndented(")\n")
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("#*%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%s.setAutoDraw(True)\n" %(self.params['name']))
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the time test
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" %(self.params))
            buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #set parameters that need updating every frame
        if self.checkNeedToUpdate('set every frame'):#do any params need updating? (this method inherited from _base)
            buff.writeIndented("if %(name)s.status==STARTED:#only update if being drawn\n" %(self.params))
            buff.setIndentLevel(+1, relative=True)#to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(+1, relative=True)#to exit the if block
        #do force end of trial code
        if self.params['forceEndRoutine'].val==True:
            buff.writeIndented("if %s.status==FINISHED: continueRoutine=False\n" %(self.params['name']))

