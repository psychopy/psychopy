# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from _base import *
from os import path

from psychopy.app.builder.experiment import CodeGenerationException, _valid_var_re

__author__ = 'Jeremy Gray'

thisFolder = path.abspath(path.dirname(__file__))  # abs path to the folder containing this path
iconFile = path.join(thisFolder, 'ioLabs.png')
tooltip = 'ioLabs ButtonBox: check and record response buttons on ioLab Systems ButtonBox'

class ioLabsButtonBoxComponent(BaseComponent):
    """An event class for checking an ioLab Systems buttonbox.

    This is based on keyboard component, several important differences:
    - no special response class analogous to event.BuilderKeyResponse()
    - enabled responses (active buttons) are handled by the hardware device

    More than one component in a routine will produce conflicts between
    components over which active buttons (for responses and lights).
    """
    categories = ['Responses']  # which section(s) in the components panel
    def __init__(self, exp, parentName, name='bbox',
                active="(0,1,2,3,4,5,6,7)", store='first button',
                forceEndRoutine=True, storeCorrect=False, correctAns="0",
                discardPrev=True, lights=True, lightsOff=False,
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=1.0,
                startEstim='', durationEstim=''):
        self.type = 'ioLabsButtonBox'
        self.url = "http://www.psychopy.org/builder/components/ioLabs.html"
        self.exp = exp  # so we can access the experiment
        self.exp.requirePsychopyLibs(['hardware'])
        self.parentName = parentName

        self.params = {}
        self.order = ['forceEndRoutine', 'active', #NB name and timing params always come 1st
            'lights', 'store', 'storeCorrect', 'correctAns']
        self.params['name'] = Param(name, valType='code', hint="A name for this ButtonBox object (e.g. bbox)",
            label="Name")
        self.params['active'] = Param(active, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=['constant','set every repeat'],
            hint="Active buttons, such as '1,6', '(1,2,5,6)' or '0' (without quotes)",
            label="Active buttons")
        self.params['startType'] = Param(startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint="How do you want to define your start point?",
            label="")
        self.params['stopType'] = Param(stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint="How do you want to define your end point?")
        self.params['startVal'] = Param(startVal, valType='code', allowedTypes=[],
            hint="When does the bbox checking start?")
        self.params['stopVal'] = Param(stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="When does the bbox checking end?")
        self.params['startEstim'] = Param(startEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected start (s), purely for representing in the timeline")
        self.params['durationEstim'] = Param(durationEstim, valType='code', allowedTypes=[],
            hint="(Optional) expected duration (s), purely for representing in the timeline")
        self.params['discard previous'] = Param(discardPrev, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to discard all button presses occuring before the onset of this component?",
            label="Discard previous")
        self.params['store'] = Param(store, valType='str', allowedTypes=[],
            allowedVals=['last button', 'first button', 'all buttons', 'nothing'],
            updates='constant', allowedUpdates=[],
            hint="Choose which (if any) responses to store at end of a trial",
            label="Store")
        self.params['forceEndRoutine'] = Param(forceEndRoutine, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Should a button press force the end of the routine (e.g end the trial)?",
            label="Force end of Routine")
        self.params['storeCorrect'] = Param(storeCorrect, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Do you want to save the response as correct/incorrect?",
            label="Store correct")
        self.params['lights'] = Param(lights, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Turn ON the lights for the active buttons?",
            label="Lights")
        self.params['lights off'] = Param(lightsOff, valType='bool', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="Turn OFF all lights at the end of each routine?",
            label="Lights off")
        self.params['correctAns'] = Param(correctAns, valType='str', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint="What is the 'correct' response? Enter 'None' (no quotes) if withholding a response is correct. Might be helpful to add a correctAns column and use $thisTrial.correctAns",
            label="Correct answer")

    def writeStartCode(self, buff):
        # avoid duplicates; ok for init but not safe to do in routine, frame, etc
        lines = ("# connect to ioLabs bbox, turn lights off\n" +
                "from psychopy.hardware import iolab\n" +
                "iolab.ButtonBox().standby()\n")
        if not lines in buff.getvalue():
            buff.writeIndentedLines(lines)

    def writeInitCode(self, buff):
        lines = "%(name)s = iolab.ButtonBox()\n"
        if not lines % self.params in buff.getvalue():  # avoid duplicates
            buff.writeIndentedLines(lines % self.params)

    def writeRoutineStartCode(self,buff):
        if self.params['discard previous'].val:
            buff.writeIndented('%(name)s.clearEvents()\n' % self.params)
        active = self.params['active'].val.strip(')], ').lstrip('([, ')
        if not _valid_var_re.match(active):
            if not ',' in active:
                active += ','  # to turn an int into tuple
            active = '(' + active + ')'
        lines = ('%(name)s.active = ' + '%s  # tuple or list of int 0..7\n' % active +
                 '%(name)s.setEnabled(%(name)s.active)\n')
        if self.params['lights'].val:
            lines += '%(name)s.setLights(%(name)s.active)\n'
        if self.params['store'].val != 'nothing' or self.params['storeCorrect'].val:
            lines += ("%(name)s.btns = []  # responses stored in .btns and .rt\n" +
                  "%(name)s.rt = []\n")
        buff.writeIndentedLines(lines % self.params)

    def writeFrameCode(self,buff):
        """Write the code that will be called every frame.
        """
        #some shortcuts
        store = self.params['store'].val
        storeCorr = self.params['storeCorrect'].val
        forceEnd = self.params['forceEndRoutine'].val
        active = self.params['active'].val

        # if just now starting on this frame:
        buff.writeIndented("# *%(name)s* updates\n" % self.params)
        self.writeStartTestCode(buff)  #writes an if statement to determine whether to draw etc
        lines = "%(name)s.status = STARTED\n"
        if self.params['discard previous'].val:
            lines += "%(name)s.clearEvents()\n"
        # ioLabs bbox handles active internally, via setEnable(active)
        # this is not the same as keyboard components, which have to handle their own allowedKeys
        lines += "# buttonbox checking is just starting\n"
        if store != 'nothing':
            lines += ("%(name)s.resetClock()  # set bbox hardware internal clock to 0.000; ms accuracy\n")
        buff.writeIndentedLines(lines % self.params)
        buff.setIndentLevel(-1, relative=True)  # to get out of the if statement
        #test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)  # writes an if statement to determine whether to draw etc
            buff.writeIndented("%(name)s.status = STOPPED\n" % self.params)
            buff.setIndentLevel(-1, True)

        buff.writeIndented("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)  #to get out of the if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        # check for button presses
        buff.writeIndented("theseButtons = %(name)s.getEvents()\n" % self.params)
        # store something?
        if store != 'nothing' or forceEnd:
            buff.writeIndented("if theseButtons:  # at least one button was pressed this frame\n")
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1

        """theseButtons[0] is an iolabs button event
        - event.rt is in sec, as recorded on the bbox unit (ms accuracy)
        - event.key is type str: , '0'..'7'
        two things ignored here:
        - bbox events have evt.direction (+1 press down, -1 release up)
        - bbox evt.key can be 'voice' (for "voice-key was triggered", button 64)
        """
        if store == 'first button':
            buff.writeIndented("if %(name)s.btns == []:  # True if the first\n" % self.params)
            buff.setIndentLevel(1, True)
            dedentAtEnd += 1
            buff.writeIndented("%(name)s.btns = theseButtons[0].key  # just the first button\n" % self.params)
            buff.writeIndented("%(name)s.rt = theseButtons[0].rt\n" %(self.params))
        elif store == 'last button':
            buff.writeIndented("%(name)s.btns = theseButtons[-1].key  # just the last button\n" % self.params)
            buff.writeIndented("%(name)s.rt = theseButtons[-1].rt\n" % self.params)
        elif store == 'all buttons':
            buff.writeIndented("%(name)s.btns.extend([evt.key for evt in theseButtons])  # all buttons\n" % self.params)
            buff.writeIndented("%(name)s.rt.extend([evt.rt for evt in theseButtons])\n  # all RT (timed by bbox)" % self.params)
            # each bbox event is time-stamped, unlike keys in keyboard component

        lines = ''
        if storeCorr:
            lines += ("# was this 'correct'?\n" +
                     "if %(name)s.btns == str(%(correctAns)s):\n" +
                     "    %(name)s.corr = 1\n" +
                     "else:\n    %(name)s.corr=0\n")
        if forceEnd:
            lines += ("# a response forces the end of the routine\n" +
                     "continueRoutine = False\n")
        buff.writeIndentedLines(lines % self.params)
        buff.setIndentLevel(-(dedentAtEnd), relative=True)

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        store = self.params['store'].val
        if store == 'nothing':
            return
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        # write the actual code
        lines = ''
        if self.params['lights off'].val:
            lines += '%(name)s.setLights(None)\n'
        lines += "# store ioLabs bbox data for %s (%s)\n" % (name, currLoop.type)
        lines += ("if len(%(name)s.btns) == 0:  # no ioLabs responses\n" +
                  "    %(name)s.btns = None\n")
        if self.params['storeCorrect'].val:  #check for correct NON-repsonse
            lines += "    # was no response the correct answer?\n"
            lines += "    if str(%(correctAns)s).lower() == 'none':\n"
            lines += "        %(name)s.corr = 1  # correct non-response\n"
            lines += "    else:\n        %(name)s.corr = 0  # failed to withold a response\n"
        buff.writeIndentedLines(lines % self.params)
        if currLoop.type == 'StairHandler':
            # StairHandler only needs correct-ness
            if self.params['storeCorrect'].val:
                buff.writeIndented("%s.addData(%s.corr)\n" % (currLoop.params['name'], name))
        else:
            # TrialHandler gets button and RT info:
            loopnamename = (currLoop.params['name'], name, name)
            buff.writeIndented("%s.addData('%s.btns', %s.btns)\n" % loopnamename)
            if self.params['storeCorrect'].val:
                buff.writeIndented("%s.addData('%s.corr', %s.corr)\n" % loopnamename)
            buff.writeIndented("if %(name)s.btns != None:  # add RTs if there are responses\n" % self.params)
            buff.writeIndented("    %s.addData('%s.rt', %s.rt)\n" % loopnamename)
        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)

    def writeExperimentEndCode(self, buff):
        buff.writeIndented('%(name)s.standby()  # lights out etc\n' % self.params)
