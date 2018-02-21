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
    #     # params
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
            "How often should the variable state be stored? "
            "On every video frame, every routine or just at the end of the "
            "experiment?")
        self.params['saveVarState'] = Param(
            saveVarState, valType='str',
            allowedVals=['final', 'routine', 'every frame', 'never'],
            hint=hnt,
            label=_localized['saveVarState'])
    #
    def writeInitCode(self, buff):
        # replaces variable params with sensible defaults
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
        # create some lists to store recorded values positions and events if
        # we need more than one
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
        code = ("# set Frame values for %s\n" % inits['name'])
        buff.writeIndented(code)
        if not inits['c_startFrameValue'].val in ['', None, 'None']:
            if inits['c_startFrameValue'].updates == 'set every frame':
                code = ("%s = %s\n" % (inits['name'], inits['c_startFrameValue']))
                buff.writeIndented(code)
        code = ("# storing Frame values for %s\n" % inits['name'])
        buff.writeIndented(code)
        if inits['c_startFrameValue']:
            # if inits['saveVarState'] == 'every frame':
            code = ("%s_container['frameValues'].append(%s)" % (inits['name'], inits['name']))
            buff.writeIndented(code)

    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of the routine
        """
        inits = self.params
        code = ("# adding data to trialHandler\n" % inits['name'])
        buff.writeIndented(code)
        if inits['saveVarState'] in ['final', 'routine'] and inits['c_startFrameValue'].updates == 'set every frame':
            if inits['c_startFrameValue']:
                if inits['saveVarState'] in ['final', 'routine']:
                    code = "for fields in %s_container:\n" % inits['name']
                    code += "   if fields == 'frameValues':\n"
                    code += "       thisExp.addData(fields, %s_container[fields][-1])\n" % inits['name']
                    code += "   else:\n"
                    code += "       thisExp.addData(fields, %s_container[fields])" % inits['name']
        elif inits['saveVarState'] == 'every frame':
            code = "for fields in %s_container:\n" % inits['name']
            code += "   thisExp.addData(fields, %s_container[fields])" % inits['name']
        buff.writeIndentedLines(code)