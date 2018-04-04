#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2015 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseComponent, Param, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'var.png')
tooltip = _translate('Variable: create a new variable')

# only use _localized values for label values, nothing functional:
_localized = {'name': _translate('Name'),
              'startExpValue': _translate('Experiment start value'),
              'startRoutineValue': _translate('Routine start value'),
              'startFrameValue': _translate('Frame start value'),
              'saveStartExp': _translate('Save exp start value'),
              'saveStartRoutine': _translate('Save routine start value'),
              'saveFrameValue': _translate('Save frame value'),
              'saveEndRoutine': _translate('Save routine end value'),
              'saveEndExp': _translate('Save exp end value')}


class VariableComponent(BaseComponent):
    """An class for creating variables in builder."""

    def __init__(self, exp, parentName,
                 name='var1', startExpValue = '',
                 startRoutineValue='',
                 startFrameValue=''):

        super(VariableComponent, self).__init__(
            exp, parentName, name)

        categories = ['Custom']
        self.type = 'Variable'
        self.url = "http://www.psychopy.org/builder/components/variable.html"
        self.order += ['startExpValue', 'saveStartExp', 'startRoutineValue', 'saveStartRoutine', 'startFrameValue',
                       'saveFrameValue', 'saveEndRoutine', 'saveEndExp']
        # set parameters
        hnt = _translate("The start value. A variable can be set to any value.")
        self.params['startExpValue'] = Param(
            startExpValue, valType='code', allowedTypes=[], updates='constant',
            hint=hnt,
            label=_localized['startExpValue'])
        hnt = _translate("Set the value for the beginning of each routine.")
        self.params['startRoutineValue'] = Param(
            startRoutineValue, valType='code', allowedTypes=[], updates='constant',
            hint=hnt,
            label=_localized['startRoutineValue'])
        hnt = _translate("Set the value for the beginning of every screen refresh.")
        self.params['startFrameValue'] = Param(
            startFrameValue, valType='code', allowedTypes=[],
            hint=hnt,
            label=_localized['startFrameValue'])
        # Save options
        hnt = _translate('Save the experiment start value in data file.')
        self.params['saveStartExp'] = Param(
            False, valType='bool',
            updates='constant',
            hint=hnt,
            label=_localized['saveStartExp'],
            categ='Save')
        hnt = _translate('Save the experiment end value in data file.')
        self.params['saveEndExp'] = Param(
            False, valType='bool',
            updates='constant',
            hint=hnt,
            label=_localized['saveEndExp'],
            categ='Save')
        hnt = _translate('Save the routine start value in data file.')
        self.params['saveStartRoutine'] = Param(
            False, valType='bool',
            updates='constant',
            hint=hnt,
            label=_localized['saveStartRoutine'],
            categ='Save')
        hnt = _translate('Save the routine end value in data file.')
        self.params['saveEndRoutine'] = Param(
            True, valType='bool',
            updates='constant',
            hint=hnt,
            label=_localized['saveEndRoutine'],
            categ='Save')
        hnt = _translate('Save choice of frame value in data file.')
        self.params['saveFrameValue'] = Param(
            'nothing', valType='str',
            allowedVals=['first', 'last', 'average', 'nothing'],
            updates='constant',
            hint=hnt,
            label=_localized['saveFrameValue'],
            categ='Save')

    def writeInitCode(self, buff):
        """Write variable initialisation code.
        """
        code = ("# Set experiment start values for variable component %(name)s\n"
                "%(name)s = %(startExpValue)s\n" % self.params)
        buff.writeIndented(code)
    #
    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine.
        """
        code = ("%(name)s = %(startRoutineValue)s  # Set routine start values for %(name)s\n" % self.params)
        if self.params['saveStartRoutine'] == True:
            code += ("thisExp.addData('routineStartVal', %(name)s)  # Save exp start value\n" % self.params)
        # Create new container at beginning of each routine, to ensure frame data is cleared between trials
        if self.params['saveFrameValue'] == True:
            code += ("%(name)sContainer = []  # Create %(name)s container for frame values\n" % self.params)
        buff.writeIndentedLines(code)

    def writeFrameCode(self, buff):
        """Write the code that will be called at the start of the frame.
        """
        basestring = (str, bytes)
        # Create dict for hold start and end types and converting them from types to variables
        timeTypeDict = {'time (s)': 't', 'frame N': 'frameN', 'condition': self.params['startVal'].val,
                        'duration (s)': 't','duration (frames)': 'frameN'}
        # Useful values for string creation
        startType = timeTypeDict[self.params['startType'].val]
        endType = timeTypeDict[self.params['stopType'].val]
        code = ''
        # Create default string
        frameCode = ("%(name)s = %(startFrameValue)s  # Set frame start values for %(name)s\n" % self.params)
        if self.params['saveFrameValue'] == True:
            frameCode += ("%(name)sContainer.append(%(name)s)  # Save frame values\n" % self.params)
        # Check for start or end values, and commence conditional timing string creation
        if self.params['startVal'].val or self.params['stopVal'].val:
            if self.params['startType'].val == 'time (s)':
                # if startVal is an empty string then set to be 0.0
                if (isinstance(self.params['startVal'].val, basestring) and
                        not self.params['startVal'].val.strip()):
                    self.params['startVal'].val = '0.0'

            # Begin string construction for start values
            if startType == 't':
                code = (('if ' + startType + ' >= %(startVal)s') % self.params)
            elif startType == 'frameN':
                code = (('if ' + startType + ' >= %(startVal)s') % self.params)
            elif self.params['startType'].val == 'condition':
                code = ('if bool(%(startVal)s)' % self.params)

            # Begin string construction for end values
            if not self.params['stopVal'].val:
                code += (':\n' % self.params)
            # Duration types must be calculated
            elif u'duration' in self.params['stopType'].val:
                if 'frame' in self.params['startType'].val and 'frame' in self.params['stopType'].val \
                        or '(s)' in self.params['startType'].val and '(s)' in self.params['stopType'].val:
                    endTime = str((float(self.params['startVal'].val) + float(self.params['stopVal'].val)))
                else:  # do not add mismatching value types
                    endTime = self.params['stopVal'].val
                code += (' and ' + endType + ' <= ' + endTime + ':\n' % (self.params))
            elif endType == 't' :
                code += (' and ' + endType + ' <= %(stopVal)s:\n' % (self.params))
            elif endType == 'frameN' :
                code += (' and ' + endType + ' <= %(stopVal)s:\n' % (self.params))
            elif self.params['stopType'].val == 'condition':
                code += (' and bool(%(stopVal)s):\n' % self.params)
            code += ''.join(['    ' + lines + '\n' for lines in frameCode.splitlines()])
        else:
            code = frameCode
        buff.writeIndentedLines(code)

    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of the routine.
        """
        code = ''
        if self.params['saveStartExp'] == True:
            code += ("thisExp.addData('expStartVal', %(startExpValue)s)  # Save exp start value\n" % self.params)
        if self.params['saveEndRoutine'] == True:
            code = ("thisExp.addData('routineEndVal', %(name)s)  # Save end routine value\n" % self.params)
        if self.params['saveFrameValue'] == True and self.params['saveFrameValue'].updates == 'last':
            code += ("thisExp.addData('frameEndVal', %(name)sContainer[-1])  # Save end frame value\n" % self.params)
        elif self.params['saveFrameValue'] == True and self.params['saveFrameValue'].updates == 'first':
            code += ("thisExp.addData('frameStartVal', %(name)sContainer[0])  # Save start frame value\n" % self.params)
        elif self.params['saveFrameValue'] == True and self.params['saveFrameValue'].updates == 'average':
            code += ("thisExp.addData('meanFrameVal', average(%(name)sContainer))  # Save average frame value\n" % self.params)
        if self.params['saveEndExp'] == True:
            code += ("thisExp.addData('endExpVal', %(name)s)  # Save end experiment value\n" % self.params)
        buff.writeIndentedLines(code)
