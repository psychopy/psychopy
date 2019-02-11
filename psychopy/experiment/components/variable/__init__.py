#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2015 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseComponent, Param, _translate
import numpy as np

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

        super().__init__(exp, parentName, name)

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
            'never', valType='str',
            allowedVals=['first', 'last', 'all', 'never'],
            updates='constant',
            hint=hnt,
            label=_localized['saveFrameValue'],
            categ='Save')

    def writeInitCode(self, buff):
        """Write variable initialisation code."""
        code = ("# Set experiment start values for variable component %(name)s\n")
        if self.params['startExpValue'] == '':
            code += ("%(name)s = ''\n")
        else:
            code += ("%(name)s = %(startExpValue)s\n")
        # Create variable container
        code += ("%(name)sContainer = []\n")
        buff.writeIndented(code % self.params)
    #
    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine."""
        if not self.params['startRoutineValue'] == '':
            code = ("%(name)s = %(startRoutineValue)s  # Set routine start values for %(name)s\n")
            if self.params['saveStartRoutine'] == True:
                code += ("thisExp.addData('%(name)s.routineStartVal', %(name)s)  # Save exp start value\n")
            buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called at the start of the frame."""
        if not self.params['startFrameValue'] == '':
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
            if not self.params['saveFrameValue'] == 'Never':
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
        """Write the code that will be called at the end of the routine."""
        code = ''
        if self.params['saveStartExp'] == True and not self.params['startExpValue'] == '':
            code = ("thisExp.addData('%(name)s.expStartVal', %(startExpValue)s)  # Save exp start value\n")
        if self.params['saveEndRoutine'] == True and not self.params['startRoutineValue'] == '':
            code += ("thisExp.addData('%(name)s.routineEndVal', %(name)s)  # Save end routine value\n")
        if not self.params['startFrameValue'] == '':
            if self.params['saveFrameValue'] == 'last':
                code += ("thisExp.addData('%(name)s.frameEndVal', %(name)sContainer[-1])  # Save end frame value\n")
            elif self.params['saveFrameValue'] == 'first':
                code += ("thisExp.addData('%(name)s.frameStartVal', %(name)sContainer[0])  # Save start frame value\n")
            elif self.params['saveFrameValue'] == 'all':
                code += ("thisExp.addData('%(name)s.allFrameVal', %(name)sContainer)  # Save all frame value\n")
        buff.writeIndentedLines(code % self.params)

    def writeExperimentEndCode(self, buff):
        """Write the code that will be called at the end of the experiment."""
        code=''
        writeData = []
        # For saveEndExp, check whether any values were initiated.
        for vals in ['startExpValue', 'startRoutineValue', 'startFrameValue']:
            if not self.params[vals] == '':
                writeData.append(True)
        # Write values to file if requested, and if any variables defined
        if self.params['saveEndExp'] == True and np.any(writeData):
            code = ("thisExp.addData('%(name)s.endExpVal', %(name)s)  # Save end experiment value\n")
        buff.writeIndentedLines(code % self.params)