#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function

from builtins import str, object, super
from past.builtins import basestring

from psychopy import prefs
from psychopy.constants import FOREVER
from ..params import Param
from psychopy.experiment.utils import CodeGenerationException
from psychopy.experiment.utils import unescapedDollarSign_re
from psychopy.experiment.params import getCodeFromParamStr
from psychopy.alerts import alerttools

from psychopy.localization import _translate, _localized


class BaseComponent(object):
    """A template for components, defining the methods to be overridden"""
    # override the categories property below
    # an attribute of the class, determines the section in the components panel
    categories = ['Custom']
    targets = ['PsychoPy']

    def __init__(self, exp, parentName, name='',
                 startType='time (s)', startVal='',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False):
        self.type = 'Base'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed

        self.params = {}
        self.depends = []  # allows params to turn each other off/on
        """{
         "dependsOn": "shape",
         "condition": "=='n vertices",
         "param": "n vertices",
         "true": "enable",  # what to do with param if condition is True
         "false": "disable",  # permitted: hide, show, enable, disable
         }"""

        msg = _translate(
            "Name of this component (alpha-numeric or _, no spaces)")
        self.params['name'] = Param(
            name, valType='code',
            hint=msg,
            label=_localized['name'])

        msg = _translate("How do you want to define your start point?")
        self.params['startType'] = Param(
            startType, valType='str',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint=msg,
            label=_localized['startType'])

        msg = _translate("How do you want to define your end point?")
        self.params['stopType'] = Param(
            stopType, valType='str',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)',
                         'frame N', 'condition'],
            hint=msg,
            label=_localized['stopType'])

        self.params['startVal'] = Param(
            startVal, valType='code', allowedTypes=[],
            hint=_translate("When does the component start?"),
            label=_localized['startVal'])

        self.params['stopVal'] = Param(
            stopVal, valType='code', allowedTypes=[],
            updates='constant', allowedUpdates=[],
            hint=_translate("When does the component end? (blank is endless)"),
            label=_localized['stopVal'])

        msg = _translate("(Optional) expected start (s), purely for "
                         "representing in the timeline")
        self.params['startEstim'] = Param(
            startEstim, valType='code', allowedTypes=[],
            hint=msg,
            label=_localized['startEstim'])

        msg = _translate("(Optional) expected duration (s), purely for "
                         "representing in the timeline")
        self.params['durationEstim'] = Param(
            durationEstim, valType='code', allowedTypes=[],
            hint=msg,
            label=_localized['durationEstim'])

        msg = _translate("Store the onset/offset times in the data file "
                         "(as well as in the log file).")
        self.params['saveStartStop'] = Param(
            saveStartStop, valType='bool', allowedTypes=[],
            hint=msg, categ="Data",
            label=_translate('Save onset/offset times'))

        msg = _translate("Synchronize times with screen refresh (good for "
                         "visual stimuli and responses based on them)")
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType='bool', allowedTypes=[],
            hint=msg, categ="Data",
            label=_translate('Sync timing with screen refresh'))

        msg = _translate("Disable this component")
        self.params['disabled'] = Param(
            disabled, valType='bool', allowedTypes=[],
            hint=msg, categ="Testing",
            label=_translate('Disable component'))

        self.order = ['name']  # name first, then timing, then others

    def integrityCheck(self):
        """
        Run component integrity checks for non-visual components
        """
        alerttools.testDisabled(self)
        alerttools.testStartEndTiming(self)

    def _dubiousConstantUpdates(self):
        """Return a list of fields in component that are set to be constant
        but seem intended to be dynamic. Some code fields are constant, and
        some denoted as code by $ are constant.
        """
        warnings = []
        # treat expInfo as likely to be constant; also treat its keys as
        # constant because its handy to make a short-cut in code:
        # exec(key+'=expInfo[key]')
        expInfo = self.exp.settings.getInfo()
        keywords = self.exp.namespace.nonUserBuilder[:]
        keywords.extend(['expInfo'] + list(expInfo.keys()))
        reserved = set(keywords).difference({'random', 'rand'})
        for key in self.params:
            field = self.params[key]
            if (not hasattr(field, 'val') or
                    not isinstance(field.val, basestring)):
                continue  # continue == no problem, no warning
            if not (field.allowedUpdates and
                    isinstance(field.allowedUpdates, list) and
                    len(field.allowedUpdates) and
                    field.updates == 'constant'):
                continue
            # now have only non-empty, possibly-code, and 'constant' updating
            if field.valType == 'str':
                if not bool(unescapedDollarSign_re.search(field.val)):
                    continue
                code = getCodeFromParamStr(field.val)
            elif field.valType == 'code':
                code = field.val
            else:
                continue
            # get var names in the code; no names == constant
            try:
                names = compile(code, '', 'eval').co_names
            except SyntaxError:
                continue
            # ignore reserved words:
            if not set(names).difference(reserved):
                continue
            warnings.append((field, key))
        return warnings or [(None, None)]

    def writeInitCode(self, buff):
        """Write any code that a component needs that should only ever be done
        at start of an experiment, BEFORE window creation.
        """
        pass

    def writeStartCode(self, buff):
        """Write any code that a component needs that should only ever be done
        at start of an experiment, AFTER window creation.
        """
        # e.g., create a data subdirectory unique to that component type.
        # Note: settings.writeStartCode() is done first, then
        # Routine.writeStartCode() will call this method for each component in
        # each routine
        pass

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        pass

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the beginning of
        a routine (e.g. to update stimulus parameters)
        """
        self.writeParamUpdates(buff, 'set every repeat')

    def writeRoutineStartCodeJS(self, buff):
        """Same as writeRoutineStartCode, but for JS
        """
        self.writeParamUpdatesJS(buff, 'set every repeat')

    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of
        a routine (e.g. to save data)
        """
        if 'saveStartStop' in self.params and self.params['saveStartStop'].val:
            # what loop are we in (or thisExp)?
            if len(self.exp.flow._loopList):
                currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
            else:
                currLoop = self.exp._expHandler

            if 'Stair' in currLoop.type:
                addDataFunc = 'addOtherData'
            else:
                addDataFunc = 'addData'

            if self.params['syncScreenRefresh'].val:
                code = (
                    "{loop}.{addDataFunc}('{name}.started', {name}.tStartRefresh)\n"
                    "{loop}.{addDataFunc}('{name}.stopped', {name}.tStopRefresh)\n"
                )
            else:
                code = (
                    "{loop}.{addDataFunc}('{name}.started', {name}.tStart)\n"
                    "{loop}.{addDataFunc}('{name}.stopped', {name}.tStop)\n"
                )
            buff.writeIndentedLines(code.format(loop=currLoop.params['name'],
                                                name=self.params['name'],
                                                addDataFunc=addDataFunc))

    def writeRoutineEndCodeJS(self, buff):
        """Write the code that will be called at the end of
        a routine (e.g. to save data)
        """
        pass

    def writeExperimentEndCode(self, buff):
        """Write the code that will be called at the end of
        an experiment (e.g. save log files or reset hardware)
        """
        pass

    def writeStartTestCode(self, buff):
        """Test whether we need to start
        """
        if self.params['syncScreenRefresh']:
            tCompare = 'tThisFlip'
        else:
            tCompare = 't'
        if self.params['startType'].val == 'time (s)':
            # if startVal is an empty string then set to be 0.0
            if (isinstance(self.params['startVal'].val, basestring) and
                    not self.params['startVal'].val.strip()):
                self.params['startVal'].val = '0.0'
            code = ("if {params[name]}.status == NOT_STARTED and "
                    "{t} >= {params[startVal]}-frameTolerance:\n")
        elif self.params['startType'].val == 'frame N':
            code = ("if {params[name]}.status == NOT_STARTED and "
                    "frameN >= {params[startVal]}:\n")
        elif self.params['startType'].val == 'condition':
            code = ("if {params[name]}.status == NOT_STARTED and "
                    "{params[startVal]}:\n")
        else:
            msg = "Not a known startType (%(startType)s) for %(name)s"
            raise CodeGenerationException(msg % self.params)

        buff.writeIndented(code.format(params=self.params, t=tCompare))

        buff.setIndentLevel(+1, relative=True)
        code = ("# keep track of start time/frame for later\n"
                "{params[name]}.frameNStart = frameN  # exact frame index\n"
                "{params[name]}.tStart = t  # local t and not account for scr refresh\n"
                "{params[name]}.tStartRefresh = tThisFlipGlobal  # on global time\n")
        if self.type != "Sound":  # for sounds, don't update to actual frame time
                code += ("win.timeOnFlip({params[name]}, 'tStartRefresh')"
                         "  # time at next scr refresh\n")
        buff.writeIndentedLines(code.format(params=self.params))

    def writeStartTestCodeJS(self, buff):
        """Test whether we need to start
        """
        if self.params['startType'].val == 'time (s)':
            # if startVal is an empty string then set to be 0.0
            if (isinstance(self.params['startVal'].val, basestring) and
                    not self.params['startVal'].val.strip()):
                self.params['startVal'].val = '0.0'
            code = ("if (t >= %(startVal)s "
                    "&& %(name)s.status === PsychoJS.Status.NOT_STARTED) {\n")
        elif self.params['startType'].val == 'frame N':
            code = ("if (frameN >= %(startVal)s "
                    "&& %(name)s.status === PsychoJS.Status.NOT_STARTED) {\n")
        elif self.params['startType'].val == 'condition':
            code = ("if ((%(startVal)s) "
                    "&& %(name)s.status === PsychoJS.Status.NOT_STARTED) {\n")
        else:
            msg = "Not a known startType (%(startType)s) for %(name)s"
            raise CodeGenerationException(msg % self.params)

        buff.writeIndented(code % self.params)

        buff.setIndentLevel(+1, relative=True)
        code = ("// keep track of start time/frame for later\n"
                "%(name)s.tStart = t;  // (not accounting for frame time here)\n"
                "%(name)s.frameNStart = frameN;  // exact frame index\n\n")
        buff.writeIndentedLines(code % self.params)

    def writeStopTestCode(self, buff):
        """Test whether we need to stop
        """
        buff.writeIndentedLines("if %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(+1, relative=True)

        if self.params['stopType'].val == 'time (s)':
            code = ("# is it time to stop? (based on local clock)\n"
                    "if tThisFlip > %(stopVal)s-frameTolerance:\n"
                    )
        # duration in time (s)
        elif (self.params['stopType'].val == 'duration (s)'):
            code = ("# is it time to stop? (based on global clock, using actual start)\n"
                    "if tThisFlipGlobal > %(name)s.tStartRefresh + %(stopVal)s-frameTolerance:\n"
                    )
        elif self.params['stopType'].val == 'duration (frames)':
            code = ("if frameN >= (%(name)s.frameNStart + %(stopVal)s):\n")
        elif self.params['stopType'].val == 'frame N':
            code = "if frameN >= %(stopVal)s:\n"
        elif self.params['stopType'].val == 'condition':
            code = "if bool(%(stopVal)s):\n"
        else:
            msg = ("Didn't write any stop line for startType=%(startType)s, "
                   "stopType=%(stopType)s")
            raise CodeGenerationException(msg % self.params)

        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(+1, relative=True)
        code = ("# keep track of stop time/frame for later\n"
                "%(name)s.tStop = t  # not accounting for scr refresh\n"
                "%(name)s.frameNStop = frameN  # exact frame index\n"
                "win.timeOnFlip(%(name)s, 'tStopRefresh')"
                "  # time at next scr refresh\n")
        buff.writeIndentedLines(code % self.params)

    def writeStopTestCodeJS(self, buff):
        """Test whether we need to stop
        """
        if self.params['stopType'].val == 'time (s)':
            code = ("frameRemains = %(stopVal)s "
                    " - psychoJS.window.monitorFramePeriod * 0.75;"
                    "  // most of one frame period left\n"
                    "if (%(name)s.status === PsychoJS.Status.STARTED "
                    "&& t >= frameRemains) {\n")
        # duration in time (s)
        elif (self.params['stopType'].val == 'duration (s)' and
              self.params['startType'].val == 'time (s)'):
            code = ("frameRemains = %(startVal)s + %(stopVal)s"
                    " - psychoJS.window.monitorFramePeriod * 0.75;"
                    "  // most of one frame period left\n"
                    "if (%(name)s.status === PsychoJS.Status.STARTED "
                    "&& t >= frameRemains) {\n")
        # start at frame and end with duratio (need to use approximate)
        elif self.params['stopType'].val == 'duration (s)':
            code = ("if (%(name)s.status === PsychoJS.Status.STARTED "
                    "&& t >= (%(name)s.tStart + %(stopVal)s)) {\n")
        elif self.params['stopType'].val == 'duration (frames)':
            code = ("if (%(name)s.status === PsychoJS.Status.STARTED "
                    "&& frameN >= (%(name)s.frameNStart + %(stopVal)s)) {\n")
        elif self.params['stopType'].val == 'frame N':
            code = ("if (%(name)s.status === PsychoJS.Status.STARTED "
                    "&& frameN >= %(stopVal)s) {\n")
        elif self.params['stopType'].val == 'condition':
            code = ("if (%(name)s.status === PsychoJS.Status.STARTED "
                    "&& Boolean(%(stopVal)s)) {\n")
        else:
            msg = ("Didn't write any stop line for startType="
                   "%(startType)s, "
                   "stopType=%(stopType)s")
            raise CodeGenerationException(msg % self.params)

        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(+1, relative=True)

    def writeParamUpdates(self, buff, updateType, paramNames=None,
                          target="PsychoPy"):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        if paramNames is None:
            paramNames = list(self.params.keys())
        for thisParamName in paramNames:
            if thisParamName == 'advancedParams':
                continue  # advancedParams is not really a parameter itself
            thisParam = self.params[thisParamName]
            if thisParam.updates == updateType:
                self.writeParamUpdate(
                    buff, self.params['name'],
                    thisParamName, thisParam, thisParam.updates,
                    target=target)

    def writeParamUpdatesJS(self, buff, updateType, paramNames=None):
        """Pass this to the standard writeParamUpdates but with new 'target'
        """
        self.writeParamUpdates(buff, updateType, paramNames,
                               target="PsychoJS")

    def writeParamUpdate(self, buff, compName, paramName, val, updateType,
                         params=None, target="PsychoPy"):
        """Writes an update string for a single parameter.
        This should not need overriding for different components - try to keep
        constant
        """
        if params is None:
            params = self.params
        # first work out the name for the set____() function call
        if paramName == 'advancedParams':
            return  # advancedParams is not really a parameter itself
        elif paramName == 'letterHeight':
            paramCaps = 'Height'  # setHeight for TextStim
        elif paramName == 'image' and self.getType() == 'PatchComponent':
            paramCaps = 'Tex'  # setTex for PatchStim
        elif paramName == 'sf':
            paramCaps = 'SF'  # setSF, not SetSf
        elif paramName == 'coherence':
            paramCaps = 'FieldCoherence'
        elif paramName == 'fieldPos':
            paramCaps = 'FieldPos'
        else:
            paramCaps = paramName[0].capitalize() + paramName[1:]

        # code conversions for PsychoJS
        if target == 'PsychoJS':
            endStr = ';'
            # convert (0,0.5) to [0,0.5] but don't convert "rand()" to "rand[]"
            valStr = str(val).strip()
            if valStr.startswith("(") and valStr.endswith(")"):
                valStr = valStr.replace("(", "[", 1)
                valStr = valStr[::-1].replace(")", "]", 1)[
                         ::-1]  # replace from right
            # filenames (e.g. for image) need to be loaded from resources
            if paramName in ["sound"]:
                valStr = (
                    "psychoJS.resourceManager.getResource({})".format(valStr))
        else:
            endStr = ''

        # then write the line
        if updateType == 'set every frame' and target == 'PsychoPy':
            loggingStr = ', log=False'
        else:
            loggingStr = ''

        if target == 'PsychoPy':
            if paramName == 'color':
                buff.writeIndented("%s.setColor(%s, colorSpace=%s" %
                                   (compName, params['color'],
                                    params['colorSpace']))
                buff.write("%s)%s\n" % (loggingStr, endStr))
            elif paramName == 'sound':
                stopVal = params['stopVal'].val
                if stopVal in ['', None, -1, 'None']:
                    stopVal = '-1'
                buff.writeIndented("%s.setSound(%s, secs=%s)%s\n" %
                                   (compName, params['sound'], stopVal, endStr))
            else:
                buff.writeIndented("%s.set%s(%s%s)%s\n" %
                                   (compName, paramCaps, val, loggingStr,
                                    endStr))
        elif target == 'PsychoJS':
            # write the line
            if paramName == 'color':
                buff.writeIndented("%s.setColor(new util.Color(%s)" % (
                    compName, params['color']))
                buff.write("%s)%s\n" % (loggingStr, endStr))
            elif paramName == 'fillColor':
                buff.writeIndented("%s.setFillColor(new util.Color(%s)" % (compName, params['fillColor']))
                buff.write("%s)%s\n" % (loggingStr, endStr))
            elif paramName == 'lineColor':
                buff.writeIndented("%s.setLineColor(new util.Color(%s)" % (compName, params['lineColor']))
                buff.write("%s)%s\n" % (loggingStr, endStr))
            elif paramName == 'sound':
                stopVal = params['stopVal']
                if stopVal in ['', None, -1, 'None']:
                    stopVal = '-1'
                buff.writeIndented("%s.setSound(%s, secs=%s)%s\n" %
                                   (compName, params['sound'], stopVal, endStr))
            else:
                buff.writeIndented("%s.set%s(%s%s)%s\n" %
                                   (compName, paramCaps, val, loggingStr,
                                    endStr))

    def checkNeedToUpdate(self, updateType):
        """Determine whether this component has any parameters set to repeat
        at this level

        usage::
            True/False = checkNeedToUpdate(self, updateType)

        """
        for thisParamName in self.params:
            if thisParamName == 'advancedParams':
                continue
            thisParam = self.params[thisParamName]
            if thisParam.updates == updateType:
                return True

        return False

    def getStartAndDuration(self):
        """Determine the start and duration of the stimulus
        purely for Routine rendering purposes in the app (does not affect
        actual drawing during the experiment)

        start, duration, nonSlipSafe = component.getStartAndDuration()

        nonSlipSafe indicates that the component's duration is a known fixed
        value and can be used in non-slip global clock timing (e.g for fMRI)
        """
        if not 'startType' in self.params:
            # this component does not have any start/stop
            return None, None, True

        startType = self.params['startType'].val
        stopType = self.params['stopType'].val
        numericStart = canBeNumeric(self.params['startVal'].val)
        numericStop = canBeNumeric(self.params['stopVal'].val)

        # deduce a start time (s) if possible
        # user has given a time estimate
        if canBeNumeric(self.params['startEstim'].val):
            startTime = float(self.params['startEstim'].val)
        elif startType == 'time (s)' and numericStart:
            startTime = float(self.params['startVal'].val)
        else:
            startTime = None

        if stopType == 'time (s)' and numericStop and startTime is not None:
            duration = float(self.params['stopVal'].val) - startTime
        elif stopType == 'duration (s)' and numericStop:
            duration = float(self.params['stopVal'].val)
        else:
            # deduce duration (s) if possible. Duration used because component
            # time icon needs width
            if canBeNumeric(self.params['durationEstim'].val):
                duration = float(self.params['durationEstim'].val)
            elif self.params['stopVal'].val in ['', '-1', 'None']:
                duration = FOREVER  # infinite duration
            else:
                duration = None

        nonSlipSafe = numericStop and (numericStart or stopType == 'time (s)')
        return startTime, duration, nonSlipSafe

    def getPosInRoutine(self):
        """Find the index (position) in the parent Routine (0 for top)
        """
        routine = self.exp.routines[self.parentName]
        return routine.index(self)

    def getType(self):
        """Returns the name of the current object class"""
        return self.__class__.__name__

    def getShortType(self):
        """Replaces word component with empty string"""
        return self.getType().replace('Component', '')


class BaseVisualComponent(BaseComponent):
    """Base class for most visual stimuli
    """
    # an attribute of the class, determines section in the components panel
    categories = ['Stimuli']

    def __init__(self, exp, parentName, name='',
                 units='from exp settings', color='$[1,1,1]',
                 pos=(0, 0), size=(0, 0), ori=0, colorSpace='rgb', opacity=1,
                 startType='time (s)', startVal='',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=True):

        super(BaseVisualComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            saveStartStop=saveStartStop,
            syncScreenRefresh=syncScreenRefresh)

        self.exp.requirePsychopyLibs(
            ['visual'])  # needs this psychopy lib to operate

        msg = _translate("Units of dimensions for this stimulus")
        self.params['units'] = Param(
            units, valType='str',
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                         'height', 'degFlatPos', 'degFlat'],
            hint=msg,
            label=_localized['units'])

        msg = _translate("Color of this stimulus (e.g. $[1,1,0], red );"
                         " Right-click to bring up a color-picker (rgb only)")
        self.params['color'] = Param(
            color, valType='str', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['color'])

        msg = _translate("Opacity of the stimulus (1=opaque, 0=fully "
                         "transparent, 0.5=translucent)")
        self.params['opacity'] = Param(
            opacity, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['opacity'])

        msg = _translate(
            "Choice of color space for the color (rgb, dkl, lms, hsv)")
        self.params['colorSpace'] = Param(
            colorSpace, valType='str',
            allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
            updates='constant',
            hint=msg,
            label=_localized['colorSpace'])

        msg = _translate("Position of this stimulus (e.g. [1,2] )")
        self.params['pos'] = Param(
            pos, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['pos'])

        msg = _translate("Size of this stimulus (either a single value or "
                         "x,y pair, e.g. 2.5, [1,2] ")
        self.params['size'] = Param(
            size, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_localized['size'])

        self.params['ori'] = Param(
            ori, valType='code', allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate("Orientation of this stimulus (in deg)"),
            label=_localized['ori'])

        self.params['syncScreenRefresh'].readOnly = True

    def integrityCheck(self):
        """
        Run component integrity checks.
        """
        super().integrityCheck()  # run parent class checks first

        win = alerttools.TestWin(self.exp)

        # get units for this stimulus
        if 'units' in self.params:  # e.g. BrushComponent doesn't have this
            units = self.params['units'].val
        else:
            units = None
        if units == 'use experiment settings':
            units = self.exp.settings.params[
                'Units'].val  # this 1 uppercase
        if not units or units == 'use preferences':
            units = prefs.general['units']

        # tests for visual stimuli
        alerttools.testSize(self, win, units)
        alerttools.testPos(self, win, units)
        alerttools.testAchievableVisualOnsetOffset(self)
        alerttools.testValidVisualStimTiming(self)
        alerttools.testFramesAsInt(self)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % self.params['name'])
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.setAutoDraw(True)\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ('', None, -1, 'None'):
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-2, relative=True)

        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            code = "if %(name)s.status == STARTED:  # only update if drawing\n"
            buff.writeIndented(code % self.params)
            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame
        """
        if "PsychoJS" not in self.targets:
            buff.writeIndented("// *%s* not supported by PsychoJS\n"
                               % self.params['name'])
            return

        buff.writeIndentedLines("\n// *%s* updates\n" % self.params['name'])
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCodeJS(buff)
        buff.writeIndented("%(name)s.setAutoDraw(true);\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("}\n\n")

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ('', None, -1, 'None'):
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCodeJS(buff)
            buff.writeIndented("%(name)s.setAutoDraw(false);\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)
            buff.writeIndented("}\n")

        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            code = ("\nif (%(name)s.status === PsychoJS.Status.STARTED){ "
                    "// only update if being drawn\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdatesJS(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block
            buff.writeIndented("}\n")


def canBeNumeric(inStr):
    """Determines whether the input can be converted to a float
    (using a try: float(instr))
    """
    try:
        float(inStr)
        return True
    except Exception:
        return False
