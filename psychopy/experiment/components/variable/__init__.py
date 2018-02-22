#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2015 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseComponent, Param, getInitVals, _translate

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'var.png')
tooltip = _translate('Variable: create a new variable')

# only use _localized values for label values, nothing functional:
_localized = {'name': _translate('Name'),
              'a_startExpValue': _translate('Initial value'),
              'b_startRoutineValue': _translate('Routine start value'),
              'c_startFrameValue': _translate('Frame start value'),
              'saveVarState': _translate('Save variable'),}


class VariableComponent(BaseComponent):
    """An class for creating variables in builder"""

    def __init__(self, exp, parentName,
                 name='var_1', startExpValue = None,
                 startRoutineValue=None, saveVarState = 'final',
                 startFrameValue = None):

        super(VariableComponent, self).__init__(
            exp, parentName, name)

        categories = ['Custom']
        self.type = 'Variable'
        self.url = "http://www.psychopy.org/builder/components/variable.html"
        # set parameters
        hnt = _translate("The start value. A variable can be set to any value.")
        self.params['a_startExpValue'] = Param(
            startExpValue, valType='code', allowedTypes=[], updates='constant',
            allowedUpdates=['constant'],
            hint=hnt,
            label=_localized['a_startExpValue'])
        hnt = _translate("Set the value for the beginning of each routine."
                         "Can be constant or updated at the beginning of every routine.")
        self.params['b_startRoutineValue'] = Param(
            startRoutineValue, valType='code', allowedTypes=[], updates='constant',
            allowedUpdates=['constant', 'routine'],
            hint=hnt,
            label=_localized['b_startRoutineValue'])
        hnt = _translate("Set the value for the beginning of every screen refresh."
                         "Can be constant or updated at the beginning of every routine or screen refresh.")
        self.params['c_startFrameValue'] = Param(
            startFrameValue, valType='code', allowedTypes=[], updates='constant',
            allowedUpdates=['constant', 'routine', 'set every frame'],
            hint=hnt,
            label=_localized['c_startFrameValue'])
        hnt = _translate(
            "How should the variable state be stored? "
            "Start values are stored by default. Choose to store values from every routine, or "
            "store and save a list of every value for every frame. If saving the final value, "
            "the final value will be taken from the routine, if no frame values were created. "
            "If frame values were created, the final frame value will be stored.")
        self.params['saveVarState'] = Param(
            saveVarState, valType='str',
            allowedVals=['final', 'routine', 'every frame', 'never'],
            hint=hnt,
            label=_localized['saveVarState'])

    def writeInitCode(self, buff):
        """Write initialisation code
        """
        inits = getInitVals(self.params)
        code = ("# set values for %s\n" % inits['name'])
        code += ("%s = %s\n" % (inits['name'], inits['a_startExpValue'].val))
        code += ("# Create variable dict for storage of values and fill with start value.\n")
        code += ("%s_container = dict(zip(['startValue', 'routineValues', 'frameValues'],[%s,'',[]]))\n"
                % (inits['name'], inits['a_startExpValue']))
        buff.writeIndented(code)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        inits = self.params
        code = ("# set Routine values for %s\n" % inits['name'])
        buff.writeIndented(code)
        if not inits['b_startRoutineValue'].val in ['', None, 'None']:
            if inits['b_startRoutineValue'].updates == 'routine':
                code = ("%s = %s\n" % (inits['name'], inits['b_startRoutineValue']))
                code += ("# Reset container dict and fill with start and routine values.\n")
                code += ("%s_container = dict(zip(['startValue', 'routineValues', 'frameValues'],[%s,%s,[]]))"
                        % (inits['name'], inits['a_startExpValue'], inits['b_startRoutineValue']))
                buff.writeIndentedLines(code)

    def writeFrameCode(self, buff):
        """Write the code that will be called at the start of the frame
        """
        inits = self.params
        if not inits['c_startFrameValue'].val in ['', None, 'None']:
            code = ("# set Frame values for %s\n" % inits['name'])
            if inits['c_startFrameValue'].updates == 'set every frame':
                code += ("%s = %s\n" % (inits['name'], inits['c_startFrameValue']))
                buff.writeIndentedLines(code)
        if inits['saveVarState'] in ['every frame', 'final'] and not inits['c_startFrameValue'].val in ['', None, 'None']:
            code = ("# storing Frame values for %s\n" % inits['name'])
            code += ("%s_container['frameValues'].append(%s)" % (inits['name'], inits['name']))
            buff.writeIndentedLines(code)

    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of the routine
        """
        inits = self.params
        noneTypes = ['', None, 'None']
        if inits['saveVarState'].val != 'never':
            code = ("# adding data from %s to trialHandler\n" % inits['name'])
            code += "for fields in %s_container:\n" % inits['name'] # start addData loop
            if inits['saveVarState'] == 'final':
                if not inits['c_startFrameValue'].val in noneTypes and not inits['b_startRoutineValue'].val in noneTypes:
                    code += "   if fields == 'frameValues':\n"
                    code += "       thisExp.addData(fields, %s_container[fields][-1])\n" % inits['name']
                    code += "   else:\n"
                    code += "       thisExp.addData(fields, %s_container[fields])" % inits['name']
                elif not inits['c_startFrameValue'].val in noneTypes and inits['b_startRoutineValue'].val in noneTypes:
                    code += "   if fields == 'frameValues':\n"
                    code += "       thisExp.addData(fields, %s_container[fields][-1])\n" % inits['name']
                    code += "   elif fields != 'routineValues': # because routine not defined.\n"
                    code += "       thisExp.addData(fields, %s_container[fields])\n" % inits['name']
                elif inits['c_startFrameValue'].val in noneTypes and not inits['b_startRoutineValue'].val in noneTypes:
                    code += "   if fields != 'frameValues': # because frame not defined\n"
                    code += "       thisExp.addData(fields, %s_container[fields])\n" % inits['name']
                elif inits['c_startFrameValue'].val in noneTypes and inits['b_startRoutineValue'].val in noneTypes:
                    code += "   if not fields in ['routineValues', 'frameValues']: # because neither defined.\n"
                    code += "       thisExp.addData(fields, %s_container[fields])\n" % inits['name']
            elif inits['saveVarState'] == 'routine' and not inits['b_startRoutineValue'].val in noneTypes:
                code += "   if fields != 'frameValues':\n"
                code += "       thisExp.addData(fields, %s_container[fields])\n" % inits['name']
            elif inits['saveVarState'] == 'routine' and inits['b_startRoutineValue'].val in noneTypes:
                code += "   if not fields in ['routineValues', 'frameValues']: # because neither defined or requested.\n"
                code += "       thisExp.addData(fields, %s_container[fields])\n" % inits['name']
            elif inits['saveVarState'] == 'every frame' and inits['c_startFrameValue'].val in noneTypes:
                code += "   if fields != 'frameValues': # because no values for frame defined.\n"
                code += "       thisExp.addData(fields, %s_container[fields])\n" % inits['name']
            elif inits['saveVarState'] == 'every frame': # Then save all values
                code += "   thisExp.addData(fields, %s_container[fields])" % inits['name']
        buff.writeIndentedLines(code)

