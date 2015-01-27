# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _visual import * #to get the template visual component
from os import path
from psychopy.app.builder import components #for getInitVals()

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'movie.png')
tooltip = _translate('Movie: play movie files')

# only use _localized values for label values, nothing functional:
_localized = {'movie': _translate('Movie file'), 'forceEndRoutine': _translate('Force end of Routine'), 
              'backend':_translate('backend')}

class MovieComponent(VisualComponent):
    """An event class for presenting movie-based stimuli"""
    def __init__(self, exp, parentName, name='movie', movie='',
                units='from exp settings',
                pos=[0,0], size='', ori=0,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim='',
                forceEndRoutine=False, backend='avbin'):
        #initialise main parameters from base stimulus
        super(MovieComponent, self).__init__(exp,parentName,name=name, units=units,
                    pos=pos, size=size, ori=ori,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Movie'
        self.url="http://www.psychopy.org/builder/components/movie.html"
        self.order = ['forceEndRoutine']#comes immediately after name and timing params

        #params
        self.params['stopVal'].hint=_translate("When does the component end? (blank to use the duration of the media)")
        self.params['movie']=Param(movie, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint=_translate("A filename for the movie (including path)"),
            label=_localized['movie'])
        self.params['backend']=Param(backend, valType='str', allowedVals=['avbin','opencv'],
            hint=_translate("What underlying lib to use for loading movies"),
            label=_localized['backend'])
        self.params['forceEndRoutine']=Param(forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("Should the end of the movie cause the end of the routine (e.g. trial)?"),
            label=_localized['forceEndRoutine'])
        #these are normally added but we don't want them for a movie
        del self.params['color']
        del self.params['colorSpace']
    def _writeCreationCode(self,buff,useInits):
        #This will be called by either self.writeInitCode() or self.writeRoutineStartCode()
        #The reason for this is that moviestim is actually created fresh each time the
        #movie is loaded.
        #leave units blank if not needed
        if self.params['units'].val=='from exp settings': unitsStr=""
        else: unitsStr="units=%(units)s, " %self.params
        #If we're in writeInitCode then we need to convert params to initVals
        #because some (variable) params haven't been created yet.
        if useInits:
            params = components.getInitVals(self.params)
        else:
            params = self.params
        if self.params['backend'].val=='avbin':
            buff.writeIndented("%s = visual.MovieStim(win=win, name='%s',%s\n" %(params['name'],params['name'],unitsStr))
        else:
            buff.writeIndented("%s = visual.MovieStim2(win=win, name='%s',%s\n" %(params['name'],params['name'],unitsStr))
        buff.writeIndented("    filename=%(movie)s,\n" %(params))
        buff.writeIndented("    ori=%(ori)s, pos=%(pos)s, opacity=%(opacity)s,\n" %(params))
        if self.params['size'].val != '':
            buff.writeIndented("    size=%(size)s,\n"%(params))
        depth = -self.getPosInRoutine()
        buff.writeIndented("    depth=%.1f,\n" %depth)
        buff.writeIndented("    )\n")
    def writeInitCode(self,buff):
        #If needed then use _writeCreationCode()
        #Movie could be created here or in writeRoutineStart()
        if self.params['movie'].updates=='constant':
            self._writeCreationCode(buff, useInits=True)#create the code using init vals
    def writeRoutineStartCode(self,buff):
        #If needed then use _writeCreationCode()
        #Movie could be created here or in writeInitCode()
        if self.params['movie'].updates!='constant':#
            self._writeCreationCode(buff, useInits=False)#create the code using params, not vals
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        #buff.writeIndented("%s.seek(0.00001)#make sure we're at the start\n" %(self.params['name']))
        buff.writeIndented("%s.setAutoDraw(True)\n" %(self.params['name']))
        buff.setIndentLevel(-1, relative=True)#because of the 'if' statement of the time test
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" %(self.params))
            buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #set parameters that need updating every frame
        if self.checkNeedToUpdate('set every frame'):#do any params need updating? (this method inherited from _base)
            buff.writeIndented("if %(name)s.status == STARTED:  # only update if being drawn\n" %(self.params))
            buff.setIndentLevel(+1, relative=True)#to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)#to exit the if block
        #do force end of trial code
        if self.params['forceEndRoutine'].val==True:
            buff.writeIndented("if %s.status == FINISHED:  # force-end the routine\n" % (self.params['name']))
            buff.writeIndented("    continueRoutine = False\n")
