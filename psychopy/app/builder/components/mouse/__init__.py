# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from .._base import BaseComponent, Param, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'mouse.png')
tooltip = _translate('Mouse: query mouse position and buttons')

# only use _localized values for label values, nothing functional:
_localized = {'saveMouseState': _translate('Save mouse state'),
              'forceEndRoutineOnPress': _translate('End Routine on press'),
              'timeRelativeTo': _translate('Time relative to')}


class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons
    at given timepoints
    """
    categories = ['Responses']

    def __init__(self, exp, parentName, name='mouse',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 save='final', forceEndRoutineOnPress=True,
                 timeRelativeTo='routine'):
        super(MouseComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Mouse'
        self.url = "http://www.psychopy.org/builder/components/mouse.html"
        self.exp.requirePsychopyLibs(['event'])
        self.categories = ['Inputs']

        # params
        msg = _translate(
            "How often should the mouse state (x,y,buttons) be stored? "
            "On every video frame, every click or just at the end of the "
            "Routine?")
        self.params['saveMouseState'] = Param(
            save, valType='str',
            allowedVals=['final', 'on click', 'every frame', 'never'],
            hint=msg,
            label=_localized['saveMouseState'])

        msg = _translate("Should a button press force the end of the routine"
                         " (e.g end the trial)?")
        self.params['forceEndRoutineOnPress'] = Param(
            forceEndRoutineOnPress, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['forceEndRoutineOnPress'])

        msg = _translate("What should the values of mouse.time should be "
                         "relative to?")
        self.params['timeRelativeTo'] = Param(
            timeRelativeTo, valType='str',
            allowedVals=['experiment', 'routine'],
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['timeRelativeTo'])

    def writeInitCode(self, buff):
        code = ("%(name)s = event.Mouse(win=win)\n"
                "x, y = [None, None]\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        # create some lists to store recorded values positions and events if
        # we need more than one
        code = ("# setup some python lists for storing info about the "
                "%(name)s\n")

        if self.params['saveMouseState'].val in ['every frame', 'on click']:
            code += ("%(name)s.x = []\n"
                     "%(name)s.y = []\n"
                     "%(name)s.leftButton = []\n"
                     "%(name)s.midButton = []\n"
                     "%(name)s.rightButton = []\n"
                     "%(name)s.time = []\n")

        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        forceEnd = self.params['forceEndRoutineOnPress'].val
        routineClockName = self.exp.flow._currentRoutine._clockName

        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveMouseState'].val not in
                ['every frame', 'on click'] and not forceEnd):
            return

        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        code = ("%(name)s.status = STARTED\n"
                "event.mouseButtons = [0, 0, 0]  # reset mouse buttons to be 'up'\n")
        buff.writeIndentedLines(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = STOPPED\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # if STARTED and not STOPPED!
        code = ("if %(name)s.status == STARTED:  "
                "# only update if started and not stopped!\n") % self.params
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        # get a clock for timing
        if self.params['timeRelativeTo'].val == 'experiment':
            clockStr = 'globalClock'
        elif self.params['timeRelativeTo'].val == 'routine':
            clockStr = routineClockName

        # write param checking code
        if self.params['saveMouseState'].val == 'on click' or forceEnd:
            code = ("buttons = %(name)s.getPressed()\n"
                    "if sum(buttons) > 0:  # ie if any button is pressed\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1
        elif self.params['saveMouseState'].val == 'every frame':
            code = "buttons = %(name)s.getPressed()\n" % self.params
            buff.writeIndented(code)

        # only do this if buttons were pressed
        if self.params['saveMouseState'].val in ['on click', 'every frame']:
            code = ("x, y = %(name)s.getPos()\n"
                    "%(name)s.x.append(x)\n"
                    "%(name)s.y.append(y)\n"
                    "%(name)s.leftButton.append(buttons[0])\n"
                    "%(name)s.midButton.append(buttons[1])\n"
                    "%(name)s.rightButton.append(buttons[2])\n" %
                    self.params)

            code += ("%s.time.append(%s.getTime())\n" %
                     (self.params['name'], clockStr))

            buff.writeIndentedLines(code)

        # does the response end the trial?
        if forceEnd is True:
            code = ("# abort routine on response\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code % self.params)

        # dedent
        # 'if' statement of the time test and button check
        buff.setIndentLevel(-dedentAtEnd, relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        # do this because the param itself is not a string!
        store = self.params['saveMouseState'].val
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type == 'StairHandler':
            code = ("# NB PsychoPy doesn't handle a 'correct answer' for "
                    "mouse events so doesn't know how to handle mouse with "
                    "StairHandler\n")
        else:
            code = ("# store data for %s (%s)\n" %
                    (currLoop.params['name'], currLoop.type))

        buff.writeIndentedLines(code)

        if store == 'final':
            # buff.writeIndented("# get info about the %(name)s\n"
            # %(self.params))
            code = ("x, y = %(name)s.getPos()\n"
                    "buttons = %(name)s.getPressed()\n" %
                    self.params)

            if currLoop.type != 'StairHandler':
                vals = (currLoop.params['name'], name)
                code += (
                    "%s.addData('%s.x', x)\n" % vals +
                    "%s.addData('%s.y', y)\n" % vals +
                    "%s.addData('%s.leftButton', buttons[0])\n" % vals +
                    "%s.addData('%s.midButton', buttons[1])\n" % vals +
                    "%s.addData('%s.rightButton', buttons[2])\n" % vals)

            buff.writeIndentedLines(code)
        elif store != 'never':
            # buff.writeIndented("# save %(name)s data\n" %(self.params))
            for property in ['x', 'y', 'leftButton', 'midButton',
                             'rightButton', 'time']:
                if store == 'every frame' or not forceEnd:
                    code = ("%s.addData('%s.%s', %s.%s)\n" %
                            (currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)
                else:
                    # we only had one click so don't return a list
                    code = ("if len(%s.%s): %s.addData('%s.%s', %s.%s[0])\n" %
                            (name, property,
                             currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)

        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)
