# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path
from psychopy.app.builder.experiment import Param

thisFolder = path.abspath(path.dirname(__file__))#the absolute path to the folder containing this path
iconFile = path.join(thisFolder,'mouse.png')
tooltip = _translate('Mouse: query mouse position and buttons')

# only use _localized values for label values, nothing functional:
_localized = {'saveMouseState': _translate('Save mouse state'),
              'forceEndRoutineOnPress': _translate('End Routine on press'),
              'timeRelativeTo': _translate('Time relative to')
              }

class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons at given timepoints"""
    categories = ['Responses']
    def __init__(self, exp, parentName, name='mouse',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim='',
                save='final',forceEndRoutineOnPress=True, timeRelativeTo='routine'):
        super(MouseComponent, self).__init__(exp, parentName, name=name,
                    startType=startType, startVal=startVal,
                    stopType=stopType, stopVal=stopVal,
                    startEstim=startEstim, durationEstim=durationEstim)
        self.type='Mouse'
        self.url="http://www.psychopy.org/builder/components/mouse.html"
        self.exp.requirePsychopyLibs(['event'])
        self.categories=['Inputs']
        #params
        self.params['saveMouseState']=Param(save, valType='str',
            allowedVals=['final','on click', 'every frame', 'never'],
            hint=_translate("How often should the mouse state (x,y,buttons) be stored? On every video frame, every click or just at the end of the Routine?"),
            label=_localized['saveMouseState'])
        self.params['forceEndRoutineOnPress']=Param(forceEndRoutineOnPress, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("Should a button press force the end of the routine (e.g end the trial)?"),
            label=_localized['forceEndRoutineOnPress'])
        self.params['timeRelativeTo']=Param(timeRelativeTo, valType='str',
            allowedVals=['experiment','routine'],
            updates='constant', allowedUpdates=[],
            hint=_translate("What should the values of mouse.time should be relative to?"),
            label=_localized['timeRelativeTo'])
    def writeInitCode(self,buff):
        buff.writeIndented("%(name)s = event.Mouse(win=win)\n" %(self.params))
        buff.writeIndented("x, y = [None, None]\n" %(self.params))
    def writeRoutineStartCode(self,buff):
        """Write the code that will be called at the start of the routine
        """
        #create some lists to store recorded values positions and events if we need more than one
        buff.writeIndented("# setup some python lists for storing info about the %(name)s\n" %(self.params))
        if self.params['saveMouseState'].val in ['every frame', 'on click']:
            buff.writeIndented("%(name)s.x = []\n" %(self.params))
            buff.writeIndented("%(name)s.y = []\n" %(self.params))
            buff.writeIndented("%(name)s.leftButton = []\n" %(self.params))
            buff.writeIndented("%(name)s.midButton = []\n" %(self.params))
            buff.writeIndented("%(name)s.rightButton = []\n" %(self.params))
            buff.writeIndented("%(name)s.time = []\n" %(self.params))
    def writeFrameCode(self,buff):
        """Write the code that will be called every frame
        """
        forceEnd = self.params['forceEndRoutineOnPress'].val
        routineClockName = self.exp.flow._currentRoutine._clockName

        #only write code for cases where we are storing data as we go (each frame or each click)
        if self.params['saveMouseState'].val not in ['every frame', 'on click'] \
            and not forceEnd:#might not be saving clicks, but want it to force end of trial
            return

        buff.writeIndented("# *%s* updates\n" %(self.params['name']))
        self.writeStartTestCode(buff)#writes an if statement to determine whether to draw etc
        buff.writeIndented("%(name)s.status = STARTED\n" %(self.params))
        buff.writeIndented("event.mouseButtons = [0, 0, 0]  # reset mouse buttons to be 'up'\n")
        buff.setIndentLevel(-1, relative=True)#to get out of the if statement
        #test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)#writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.status = STOPPED\n" %(self.params))
            buff.setIndentLevel(-1, relative=True)#to get out of the if statement

        #if STARTED and not STOPPED!
        buff.writeIndented("if %(name)s.status == STARTED:  # only update if started and not stopped!\n" %(self.params))
        buff.setIndentLevel(1, relative=True)#to get out of the if statement
        dedentAtEnd=1#keep track of how far to dedent later

        #get a clock for timing
        if self.params['timeRelativeTo'].val=='experiment':clockStr = 'globalClock'
        elif self.params['timeRelativeTo'].val=='routine':clockStr = routineClockName

        #write param checking code
        if self.params['saveMouseState'].val == 'on click' or forceEnd:
            buff.writeIndented("buttons = %(name)s.getPressed()\n" %(self.params))
            buff.writeIndented("if sum(buttons) > 0:  # ie if any button is pressed\n")
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd+=1
        elif self.params['saveMouseState'].val == 'every frame':
            buff.writeIndented("buttons = %(name)s.getPressed()\n" %(self.params))

        #only do this if buttons were pressed
        if self.params['saveMouseState'].val in ['on click','every frame']:
            buff.writeIndented("x, y = %(name)s.getPos()\n" %(self.params))
            buff.writeIndented("%(name)s.x.append(x)\n" %(self.params))
            buff.writeIndented("%(name)s.y.append(y)\n" %(self.params))
            buff.writeIndented("%(name)s.leftButton.append(buttons[0])\n" %(self.params))
            buff.writeIndented("%(name)s.midButton.append(buttons[1])\n" %(self.params))
            buff.writeIndented("%(name)s.rightButton.append(buttons[2])\n" %(self.params))
            buff.writeIndented("%s.time.append(%s.getTime())\n" %(self.params['name'], clockStr))

        #does the response end the trial?
        if forceEnd==True:
            buff.writeIndented("# abort routine on response\n" %self.params)
            buff.writeIndented("continueRoutine = False\n")

        #dedent
        buff.setIndentLevel(-dedentAtEnd, relative=True)#'if' statement of the time test and button check

    def writeRoutineEndCode(self,buff):
        #some shortcuts
        name = self.params['name']
        store = self.params['saveMouseState'].val#do this because the param itself is not a string!
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop=self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type=='StairHandler':
            buff.writeIndented("# NB PsychoPy doesn't handle a 'correct answer' for mouse events so doesn't know how to handle mouse with StairHandler\n")
        else:
            buff.writeIndented("# store data for %s (%s)\n" %(currLoop.params['name'], currLoop.type))
        if store == 'final':
            #buff.writeIndented("# get info about the %(name)s\n" %(self.params))
            buff.writeIndented("x, y = %(name)s.getPos()\n" %(self.params))
            buff.writeIndented("buttons = %(name)s.getPressed()\n" %(self.params))
            if currLoop.type!='StairHandler':
                buff.writeIndented("%s.addData('%s.x', x)\n" %(currLoop.params['name'], name))
                buff.writeIndented("%s.addData('%s.y', y)\n" %(currLoop.params['name'], name))
                buff.writeIndented("%s.addData('%s.leftButton', buttons[0])\n" %(currLoop.params['name'], name))
                buff.writeIndented("%s.addData('%s.midButton', buttons[1])\n" %(currLoop.params['name'], name))
                buff.writeIndented("%s.addData('%s.rightButton', buttons[2])\n" %(currLoop.params['name'], name))
        elif store != 'never':
            #buff.writeIndented("# save %(name)s data\n" %(self.params))
            for property in ['x','y','leftButton','midButton','rightButton','time']:
                if store=='every frame' or not forceEnd:
                    buff.writeIndented("%s.addData('%s.%s', %s.%s)\n" %(currLoop.params['name'], name,property,name,property))
                else:
                    #we only had one click so don't return a list
                    buff.writeIndented("%s.addData('%s.%s', %s.%s[0])\n" %(currLoop.params['name'], name,property,name,property))
        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)
