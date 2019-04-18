#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Describes the Flow of an experiment
"""

from __future__ import absolute_import, print_function

from psychopy.constants import FOREVER


class Routine(list):
    """
    A Routine determines a single sequence of events, such
    as the presentation of trial. Multiple Routines might be
    used to comprise an Experiment (e.g. one for presenting
    instructions, one for trials, one for debriefing subjects).

    In practice a Routine is simply a python list of Components,
    each of which knows when it starts and stops.
    """

    def __init__(self, name, exp, components=()):
        super(Routine, self).__init__()
        self.params = {'name': name}
        self.name = name
        self.exp = exp
        self._clockName = None  # for scripts e.g. "t = trialClock.GetTime()"
        self.type = 'Routine'
        list.__init__(self, list(components))

    def __repr__(self):
        _rep = "psychopy.experiment.Routine(name='%s', exp=%s, components=%s)"
        return _rep % (self.name, self.exp, str(list(self)))

    @property
    def name(self):
        return self.params['name']
    @name.setter
    def name(self, name):
        self.params['name'] = name

    def addComponent(self, component):
        """Add a component to the end of the routine"""
        self.append(component)

    def removeComponent(self, component):
        """Remove a component from the end of the routine"""
        name = component.params['name']
        self.remove(component)
        # check if the component was using any Static Components for updates
        for thisParamName, thisParam in list(component.params.items()):
            if (hasattr(thisParam, 'updates') and
                    thisParam.updates and
                    'during:' in thisParam.updates):
                # remove the part that says 'during'
                updates = thisParam.updates.split(': ')[1]
                routine, static = updates.split('.')
                comp = self.exp.routines[routine].getComponentFromName(static)
                comp.remComponentUpdate(routine, name, thisParamName)

    def getStatics(self):
        """Return a list of Static components
        """
        statics = []
        for comp in self:
            if comp.type == 'Static':
                statics.append(comp)
        return statics

    def writeStartCode(self, buff):
        """This is start of the *experiment* (before window is created)
        """
        # few components will have this
        for thisCompon in self:
            # check just in case; try to ensure backwards compatibility _base
            if hasattr(thisCompon, 'writeStartCode'):
                thisCompon.writeStartCode(buff)

    def writeStartCodeJS(self, buff):
        """This is start of the *experiment*
        """
        # few components will have this
        for thisCompon in self:
            # check just in case; try to ensure backwards compatibility _base
            if hasattr(thisCompon, 'writeStartCodeJS'):
                thisCompon.writeStartCodeJS(buff)

    def writeInitCode(self, buff):
        code = '\n# Initialize components for Routine "%s"\n'
        buff.writeIndentedLines(code % self.name)
        self._clockName = self.name + "Clock"
        buff.writeIndented('%s = core.Clock()\n' % self._clockName)
        for thisCompon in self:
            thisCompon.writeInitCode(buff)

    def writeInitCodeJS(self, buff):
        code = '// Initialize components for Routine "%s"\n'
        buff.writeIndentedLines(code % self.name)
        self._clockName = self.name + "Clock"
        buff.writeIndented('%s = new util.Clock();\n' % self._clockName)
        for thisCompon in self:
            if hasattr(thisCompon, 'writeInitCodeJS'):
                thisCompon.writeInitCodeJS(buff)

    def writeResourcesCodeJS(self, buff):
        buff.writeIndented("// <<maybe need to load images for {}?>>\n"
                           .format(self.name))

    def writeMainCode(self, buff):
        """This defines the code for the frames of a single routine
        """
        # create the frame loop for this routine
        code = ('\n# ------Prepare to start Routine "%s"-------\n'
                't = 0\n'
                '%s.reset()  # clock\n'
                'frameN = -1\n'
                'continueRoutine = True\n')
        buff.writeIndentedLines(code % (self.name, self._clockName))
        # can we use non-slip timing?
        maxTime, useNonSlip = self.getMaxTime()
        if useNonSlip:
            buff.writeIndented('routineTimer.add(%f)\n' % (maxTime))

        code = "# update component parameters for each repeat\n"
        buff.writeIndentedLines(code)
        # This is the beginning of the routine, before the loop starts
        for event in self:
            event.writeRoutineStartCode(buff)

        code = '# keep track of which components have finished\n'
        buff.writeIndentedLines(code)
        compStr = ', '.join([c.params['name'].val for c in self
                             if 'startType' in c.params])
        buff.writeIndented('%sComponents = [%s]\n' % (self.name, compStr))
        code = ("for thisComponent in %sComponents:\n"
                "    thisComponent.tStart = None\n"
                "    thisComponent.tStop = None\n"
                "    thisComponent.tStartRefresh = None\n"
                "    thisComponent.tStopRefresh = None\n"
                "    if hasattr(thisComponent, 'status'):\n"
                "        thisComponent.status = NOT_STARTED\n"
                '\n# -------Start Routine "%s"-------\n')
        buff.writeIndentedLines(code % (self.name, self.name))
        if useNonSlip:
            code = 'while continueRoutine and routineTimer.getTime() > 0:\n'
        else:
            code = 'while continueRoutine:\n'
        buff.writeIndented(code)

        buff.setIndentLevel(1, True)
        # on each frame
        code = ('# get current time\n'
                't = %s.getTime()\n'
                'frameN = frameN + 1  # number of completed frames '
                '(so 0 is the first frame)\n')
        buff.writeIndentedLines(code % self._clockName)

        # write the code for each component during frame
        buff.writeIndentedLines('# update/draw components on each frame\n')
        # just 'normal' components
        for event in self:
            if event.type == 'Static':
                continue  # we'll do those later
            event.writeFrameCode(buff)
        # update static component code last
        for event in self.getStatics():
            event.writeFrameCode(buff)

        # allow subject to quit via Esc key?
        if self.exp.settings.params['Enable Escape'].val:
            code = ('\n# check for quit (typically the Esc key)\n'
                    'if endExpNow or keyboard.Keyboard().getKeys(keyList=["escape"]):\n'
                    '    core.quit()\n')
            buff.writeIndentedLines(code)

        # are we done yet?
        code = (
            '\n# check if all components have finished\n'
            'if not continueRoutine:  # a component has requested a '
            'forced-end of Routine\n'
            '    break\n'
            'continueRoutine = False  # will revert to True if at least '
            'one component still running\n'
            'for thisComponent in %sComponents:\n'
            '    if hasattr(thisComponent, "status") and '
            'thisComponent.status != FINISHED:\n'
            '        continueRoutine = True\n'
            '        break  # at least one component has not yet finished\n')
        buff.writeIndentedLines(code % self.name)

        # update screen
        code = ('\n# refresh the screen\n'
                "if continueRoutine:  # don't flip if this routine is over "
                "or we'll get a blank screen\n"
                '    win.flip()\n')
        buff.writeIndentedLines(code)

        # that's done decrement indent to end loop
        buff.setIndentLevel(-1, True)

        # write the code for each component for the end of the routine
        code = ('\n# -------Ending Routine "%s"-------\n'
                'for thisComponent in %sComponents:\n'
                '    if hasattr(thisComponent, "setAutoDraw"):\n'
                '        thisComponent.setAutoDraw(False)\n')
        buff.writeIndentedLines(code % (self.name, self.name))
        for event in self:
            event.writeRoutineEndCode(buff)

        # reset routineTimer at the *very end* of all non-nonSlip routines
        if not useNonSlip:
            code = ('# the Routine "%s" was not non-slip safe, so reset '
                    'the non-slip timer\n'
                    'routineTimer.reset()\n')
            buff.writeIndentedLines(code % self.name)


    def writeRoutineBeginCodeJS(self, buff, modular):

        # create the frame loop for this routine
        code = ("\nfunction %(name)sRoutineBegin() {\n" % self.params)
        buff.writeIndentedLines(code)
        buff.setIndentLevel(1, relative=True)
        code = ("//------Prepare to start Routine '%(name)s'-------\n"
                "t = 0;\n"
                "%(name)sClock.reset(); // clock\n"
                "frameN = -1;\n" % self.params)
        buff.writeIndentedLines(code)
        # can we use non-slip timing?
        maxTime, useNonSlip = self.getMaxTime()
        if useNonSlip:
            buff.writeIndented('routineTimer.add(%f);\n' % (maxTime))

        code = "// update component parameters for each repeat\n"
        buff.writeIndentedLines(code)
        # This is the beginning of the routine, before the loop starts
        for thisCompon in self:
            if "PsychoJS" in thisCompon.targets:
                thisCompon.writeRoutineStartCodeJS(buff)

        code = ("// keep track of which components have finished\n"
                "%(name)sComponents = [];\n" % self.params)
        buff.writeIndentedLines(code)
        for thisCompon in self:
            if (('startType' in thisCompon.params) and ("PsychoJS" in thisCompon.targets)):
                code = ("%sComponents.push(%s);\n" % (self.name, thisCompon.params['name']))
                buff.writeIndentedLines(code)

        if modular:
            code = ("\nfor (const thisComponent of %(name)sComponents)\n"
                    "  if ('status' in thisComponent)\n"
                    "    thisComponent.status = PsychoJS.Status.NOT_STARTED;\n"
                    "\nreturn Scheduler.Event.NEXT;\n" % self.params)
        else:
            code = ("\n%(name)sComponents.forEach( function(thisComponent) {\n"
                    "  if ('status' in thisComponent)\n"
                    "    thisComponent.status = PsychoJS.Status.NOT_STARTED;\n"
                    "   });\n"
                    "\nreturn Scheduler.Event.NEXT;\n" % self.params)

        buff.writeIndentedLines(code)
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")


    def writeEachFrameCodeJS(self, buff, modular):
        # can we use non-slip timing?
        maxTime, useNonSlip = self.getMaxTime()

        # write code for each frame
        code = ("\nfunction %(name)sRoutineEachFrame() {\n" % self.params)
        buff.writeIndentedLines(code)
        buff.setIndentLevel(1, relative=True)
        code = ("//------Loop for each frame of Routine '%(name)s'-------\n"
                "let continueRoutine = true; // until we're told otherwise\n"
                "// get current time\n"
                "t = %(name)sClock.getTime();\n"
                "frameN = frameN + 1;"
                "// number of completed frames (so 0 is the first frame)\n" % self.params)
        buff.writeIndentedLines(code)
        # write the code for each component during frame
        buff.writeIndentedLines('// update/draw components on each frame\n')
        # just 'normal' components
        for comp in self:
            if "PsychoJS" in comp.targets and comp.type != 'Static':
                comp.writeFrameCodeJS(buff)
        # update static component code last
        for comp in self.getStatics():
            if "PsychoJS" in comp.targets:
                comp.writeFrameCodeJS(buff)

        if self.exp.settings.params['Enable Escape'].val:
            code = ("// check for quit (typically the Esc key)\n"
                    "if (psychoJS.experiment.experimentEnded "
                    "|| psychoJS.eventManager.getKeys({keyList:['escape']}).length > 0) {\n"
                    "  return psychoJS.quit('The [Escape] key was pressed. Goodbye!', false);\n"
                    "}\n\n")
            buff.writeIndentedLines(code)

        # are we done yet?
        code = ("// check if the Routine should terminate\n"
                "if (!continueRoutine) {"
                "  // a component has requested a forced-end of Routine\n"
                "  return Scheduler.Event.NEXT;\n"
                "}\n\n"
                "continueRoutine = false;  "
                "// reverts to True if at least one component still running\n")
        buff.writeIndentedLines(code)

        if modular:
            code = ("for (const thisComponent of %(name)sComponents)\n"
                    "  if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {\n"
                    "    continueRoutine = true;\n"
                    "    break;\n"
                    "  }\n")
        else:
            code = ("%(name)sComponents.forEach( function(thisComponent) {\n"
                    "  if ('status' in thisComponent && thisComponent.status !== PsychoJS.Status.FINISHED) {\n"
                    "    continueRoutine = true;\n"
                    "  }});\n")
        buff.writeIndentedLines(code % self.params)

        buff.writeIndentedLines("\n// refresh the screen if continuing\n")
        if useNonSlip:
            buff.writeIndentedLines("if (continueRoutine "
                                    "&& routineTimer.getTime() > 0) {")
        else:
            buff.writeIndentedLines("if (continueRoutine) {")
        code = ("  return Scheduler.Event.FLIP_REPEAT;\n"
                "}\n"
                "else {\n"
                "  return Scheduler.Event.NEXT;\n"
                "}\n")
        buff.writeIndentedLines(code)

        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")

    def writeRoutineEndCodeJS(self, buff, modular):
        # can we use non-slip timing?
        maxTime, useNonSlip = self.getMaxTime()

        code = ("\nfunction %(name)sRoutineEnd() {\n" % self.params)
        buff.writeIndentedLines(code)
        buff.setIndentLevel(1, relative=True)

        if modular:
            code = ("//------Ending Routine '%(name)s'-------\n"
                    "for (const thisComponent of %(name)sComponents) {\n"
                    "  if (typeof thisComponent.setAutoDraw === 'function') {\n"
                    "    thisComponent.setAutoDraw(false);\n"
                    "  }\n"
                    "}\n")
        else:
            code = ("//------Ending Routine '%(name)s'-------\n"
                    "%(name)sComponents.forEach( function(thisComponent) {\n"
                    "  if (typeof thisComponent.setAutoDraw === 'function') {\n"
                    "    thisComponent.setAutoDraw(false);\n"
                    "  }});\n")
        buff.writeIndentedLines(code  % self.params)
        # add the EndRoutine code for each component
        for compon in self:
            if "PsychoJS" in compon.targets:
                compon.writeRoutineEndCodeJS(buff)

        # reset routineTimer at the *very end* of all non-nonSlip routines
        if not useNonSlip:
            code = ('// the Routine "%s" was not non-slip safe, so reset '
                    'the non-slip timer\n'
                    'routineTimer.reset();\n\n')
            buff.writeIndentedLines(code % self.name)

        buff.writeIndented('return Scheduler.Event.NEXT;\n')
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")

    def writeExperimentEndCode(self, buff):
        """Some components have
        """
        # This is the beginning of the routine, before the loop starts
        for component in self:
            component.writeExperimentEndCode(buff)

    def writeExperimentEndCodeJS(self, buff):
        """This defines the code for the frames of a single routine
        """
        # This is the beginning of the routine, before the loop starts
        for component in self:
            if 'writeExperimentEndCodeJS' in dir(component):
                component.writeExperimentEndCodeJS(buff)

    def getType(self):
        return 'Routine'

    def getComponentFromName(self, name):
        for comp in self:
            if comp.params['name'].val == name:
                return comp
        return None

    def getComponentFromType(self, type):
        for comp in self:
            if comp.type == type:
                return comp
        return None

    def hasOnlyStaticComp(self):
        return all([comp.type == 'Static' for comp in self])

    def getMaxTime(self):
        """What the last (predetermined) stimulus time to be presented. If
        there are no components or they have code-based times then will
        default to 10secs
        """
        maxTime = 0
        nonSlipSafe = True  # if possible
        for component in self:
            if 'startType' in component.params:
                start, duration, nonSlip = component.getStartAndDuration()
                if not nonSlip:
                    nonSlipSafe = False
                if duration == FOREVER:
                    # only the *start* of an unlimited event should contribute
                    # to maxTime
                    duration = 1  # plus some minimal duration so it's visible
                # now see if we have a end t value that beats the previous max
                try:
                    # will fail if either value is not defined:
                    thisT = start + duration
                except Exception:
                    thisT = 0
                maxTime = max(maxTime, thisT)
        if maxTime == 0:  # if there are no components
            maxTime = 10
            nonSlipSafe = False
        return maxTime, nonSlipSafe
