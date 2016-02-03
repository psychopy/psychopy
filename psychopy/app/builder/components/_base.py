# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import

from ..experiment import Param
from ..components import getInitVals
from psychopy.constants import FOREVER

# only use _localized values for label values, nothing functional
_localized = {
    # for BaseComponent:
    'name': _translate('Name'),  # fieldName: display label
    'startType': _translate('start type'), 'stopType': _translate('stop type'),
    'startVal': _translate('Start'), 'stopVal': _translate('Stop'),
    'startEstim': _translate('Expected start (s)'),
    'durationEstim': _translate('Expected duration (s)'),

    # for BaseVisualComponent:
    'units': _translate('Units'),
    'color': _translate('Color'), 'colorSpace': _translate('Color space'),
    'opacity': _translate('Opacity'), 'pos': _translate('Position [x,y]'),
    'ori': _translate('Orientation'), 'size': _translate('Size [w,h]')
}


class BaseComponent(object):
    """A template for components, defining the methods to be overridden"""
    # override the categories property below
    # an attribute of the class, determines the section in the components panel
    categories = ['Custom']

    def __init__(self, exp, parentName, name='',
                 startType='time (s)', startVal='',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim=''):
        self.type = 'Base'
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed

        self.params = {}
        self.params['name'] = Param(name, valType='code',
                                    hint=_translate(
                                        "Name of this component (alpha-numeric or _, no spaces)"),
                                    label=_localized['name'])
        self.params['startType'] = Param(startType, valType='str',
                                         allowedVals=[
                                             'time (s)', 'frame N', 'condition'],
                                         hint=_translate(
                                             "How do you want to define your start point?"),
                                         label=_localized['startType'])
        self.params['stopType'] = Param(stopType, valType='str',
                                        allowedVals=[
                                            'duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
                                        hint=_translate(
                                            "How do you want to define your end point?"),
                                        label=_localized['stopType'])
        self.params['startVal'] = Param(startVal, valType='code', allowedTypes=[],
                                        hint=_translate(
                                            "When does the component start?"),
                                        label=_localized['startVal'])
        self.params['stopVal'] = Param(stopVal, valType='code', allowedTypes=[],
                                       updates='constant', allowedUpdates=[],
                                       hint=_translate(
                                           "When does the component end? (blank is endless)"),
                                       label=_localized['stopVal'])
        self.params['startEstim'] = Param(startEstim, valType='code', allowedTypes=[],
                                          hint=_translate(
                                              "(Optional) expected start (s), purely for representing in the timeline"),
                                          label=_localized['startEstim'])
        self.params['durationEstim'] = Param(durationEstim, valType='code', allowedTypes=[],
                                             hint=_translate(
                                                 "(Optional) expected duration (s), purely for representing in the timeline"),
                                             label=_localized['durationEstim'])

        self.order = ['name']  # name first, then timing, then others

    def writeStartCode(self, buff):
        """Write any code that a component needs that should only ever be done at
        start of an experiment (done once only)
        """
        # e.g., create a data subdirectory unique to that component type.
        # Note: settings.writeStartCode() is done first, then Routine.writeStartCode()
        # will call this method for each component in each routine
        pass

    def writeInitCode(self, buff):
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

    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of
        a routine (e.g. to save data)
        """
        pass

    def writeExperimentEndCode(self, buff):
        """Write the code that will be called at the end of
        an experiment (e.g. save log files or reset hardware)
        """
        pass

    def writeTimeTestCode(self, buff):
        """Original code for testing whether to draw.
        Most objects should migrate to using writeStartTestCode and writeEndTestCode
        """
        if self.params['duration'].val == '':
            buff.writeIndented("if (%(startTime)s <= t):\n" % (self.params))
        else:
            buff.writeIndented(
                "if (%(startTime)s <= t < (%(startTime)s + %(duration)s)):\n" % (self.params))

    def writeStartTestCode(self, buff):
        """Test whether we need to start
        """
        if self.params['startType'].val == 'time (s)':
            # if startVal is an empty string then set to be 0.0
            if isinstance(self.params['startVal'].val, basestring) and not self.params['startVal'].val.strip():
                self.params['startVal'].val = '0.0'
            buff.writeIndented(
                "if t >= %(startVal)s and %(name)s.status == NOT_STARTED:\n" % (self.params))
        elif self.params['startType'].val == 'frame N':
            buff.writeIndented(
                "if frameN >= %(startVal)s and %(name)s.status == NOT_STARTED:\n" % (self.params))
        elif self.params['startType'].val == 'condition':
            buff.writeIndented(
                "if (%(startVal)s) and %(name)s.status == NOT_STARTED:\n" % (self.params))
        else:
            raise "Not a known startType (%(startType)s) for %(name)s" % (
                self.params)
        buff.setIndentLevel(+1, relative=True)
        buff.writeIndented(
            "# keep track of start time/frame for later\n" % self.params)
        buff.writeIndented(
            "%(name)s.tStart = t  # underestimates by a little under one frame\n" % self.params)
        buff.writeIndented(
            "%(name)s.frameNStart = frameN  # exact frame index\n" % self.params)

    def writeStopTestCode(self, buff):
        """Test whether we need to stop
        """
        if self.params['stopType'].val == 'time (s)':
            frameVal = "frameRemains = %(stopVal)s - win.monitorFramePeriod * 0.75  # most of one frame period left\n" % self.params
            buff.writeIndented(frameVal)
            buff.writeIndented(
                "if %(name)s.status == STARTED and t >= frameRemains:\n" % self.params)
        #duration in time (s)
        elif self.params['stopType'].val == 'duration (s)' and self.params['startType'].val == 'time (s)':
            frameVal = "frameRemains = %(startVal)s + %(stopVal)s - win.monitorFramePeriod * 0.75  # most of one frame period left\n" % self.params
            buff.writeIndented(frameVal)
            buff.writeIndented(
                "if %(name)s.status == STARTED and t >= frameRemains:\n" % self.params)
        # start at frame and end with duratio (need to use approximate)
        elif self.params['stopType'].val == 'duration (s)':
            buff.writeIndented(
                "if %(name)s.status == STARTED and t >= (%(name)s.tStart + %(stopVal)s):\n" % (self.params))
        #duration in frames
        elif self.params['stopType'].val == 'duration (frames)':
            buff.writeIndented(
                "if %(name)s.status == STARTED and frameN >= (%(name)s.frameNStart + %(stopVal)s):\n" % (self.params))
        # stop frame number
        elif self.params['stopType'].val == 'frame N':
            buff.writeIndented(
                "if %(name)s.status == STARTED and frameN >= %(stopVal)s:\n" % (self.params))
        # end according to a condition
        elif self.params['stopType'].val == 'condition':
            buff.writeIndented(
                "if %(name)s.status == STARTED and bool(%(stopVal)s):\n" % (self.params))
        else:
            raise "Didn't write any stop line for startType=%(startType)s, stopType=%(stopType)s" % (
                self.params)
        buff.setIndentLevel(+1, relative=True)

    def writeParamUpdates(self, buff, updateType, paramNames=None):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        if paramNames is None:
            paramNames = self.params.keys()
        for thisParamName in paramNames:
            if thisParamName == 'advancedParams':
                continue  # advancedParams is not really a parameter itself
            thisParam = self.params[thisParamName]
            if thisParam.updates == updateType:
                self.writeParamUpdate(buff, self.params['name'],
                                      thisParamName, thisParam, thisParam.updates)

    def writeParamUpdate(self, buff, compName, paramName, val, updateType, params=None):
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
        # then write the line
        if updateType == 'set every frame':
            loggingStr = ', log=False'
        else:
            loggingStr = ''
        # write the line
        if paramName == 'color':
            buff.writeIndented("%s.setColor(%s, colorSpace=%s"
                               % (compName, params['color'], params['colorSpace']))
            buff.write("%s)\n" % (loggingStr))
        elif paramName == 'sound':
            stopVal = params['stopVal'].val
            if stopVal in ['', None, -1, 'None']:
                stopVal = '-1'
            buff.writeIndented("%s.setSound(%s, secs=%s)\n"
                               % (compName, params['sound'], stopVal))
        else:
            buff.writeIndented("%s.set%s(%s%s)\n" %
                               (compName, paramCaps, val, loggingStr))

    def checkNeedToUpdate(self, updateType):
        """Determine whether this component has any parameters set to repeat at this level

        usage::
            True/False = checkNeedToUpdate(self, updateType)

        """
        for thisParamName in self.params.keys():
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
            return None, None, True  # this component does not have any start/stop
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
        return self.__class__.__name__

    def getShortType(self):
        return self.getType().replace('Component', '')


class BaseVisualComponent(BaseComponent):
    """Base class for most visual stimuli
    """
    categories = [
        'Stimuli']  # an attribute of the class, determines the section in the components panel

    def __init__(self, exp, parentName, name='', units='from exp settings', color='$[1,1,1]',
                 pos=(0, 0), size=(0, 0), ori=0, colorSpace='rgb', opacity=1,
                 startType='time (s)', startVal='',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim=''):
        super(BaseVisualComponent, self).__init__(exp, parentName, name,
                                                  startType=startType, startVal=startVal,
                                                  stopType=stopType, stopVal=stopVal,
                                                  startEstim=startEstim, durationEstim=durationEstim)
        self.psychopyLibs = ['visual']  # needs this psychopy lib to operate

        self.params['units'] = Param(units, valType='str',
                                     allowedVals=[
                                         'from exp settings', 'deg', 'cm', 'pix', 'norm', 'height', 'degFlatPos', 'degFlat'],
                                     hint=_translate(
                                         "Units of dimensions for this stimulus"),
                                     label=_localized['units'])
        self.params['color'] = Param(color, valType='str', allowedTypes=[],
                                     updates='constant', allowedUpdates=['constant', 'set every repeat', 'set every frame'],
                                     hint=_translate(
                                         "Color of this stimulus (e.g. $[1,1,0], red ); Right-click to bring up a color-picker (rgb only)"),
                                     label=_localized['color'])
        self.params['opacity'] = Param(opacity, valType='code', allowedTypes=[],
                                       updates='constant', allowedUpdates=['constant', 'set every repeat', 'set every frame'],
                                       hint=_translate(
                                           "Opacity of the stimulus (1=opaque, 0=fully transparent, 0.5=translucent)"),
                                       label=_localized['opacity'])
        self.params['colorSpace'] = Param(colorSpace, valType='str', allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
                                          updates='constant',
                                          hint=_translate(
                                              "Choice of color space for the color (rgb, dkl, lms, hsv)"),
                                          label=_localized['colorSpace'])
        self.params['pos'] = Param(pos, valType='code', allowedTypes=[],
                                   updates='constant', allowedUpdates=['constant', 'set every repeat', 'set every frame'],
                                   hint=_translate(
                                       "Position of this stimulus (e.g. [1,2] )"),
                                   label=_localized['pos'])
        self.params['size'] = Param(size, valType='code', allowedTypes=[],
                                    updates='constant', allowedUpdates=['constant', 'set every repeat', 'set every frame'],
                                    hint=_translate(
                                        "Size of this stimulus (either a single value or x,y pair, e.g. 2.5, [1,2] "),
                                    label=_localized['size'])
        self.params['ori'] = Param(ori, valType='code', allowedTypes=[],
                                   updates='constant', allowedUpdates=['constant', 'set every repeat', 'set every frame'],
                                   hint=_translate(
                                       "Orientation of this stimulus (in deg)"),
                                   label=_localized['ori'])

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % (self.params['name']))
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.setAutoDraw(True)\n" % (self.params))
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.setAutoDraw(False)\n" % (self.params))
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)
        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            buff.writeIndented(
                "if %(name)s.status == STARTED:  # only update if being drawn\n" % (self.params))
            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block


def canBeNumeric(inStr):
    """Determines whether the input can be converted to a float
    (using a try: float(instr))
    """
    try:
        float(inStr)
        return True
    except Exception:
        return False
