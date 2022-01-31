#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.hardware import qmix
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

_localized.update({'pumpIndex': _translate('Pump index'),
                   'syringeType': _translate('Syringe type'),
                   'pumpAction': _translate('Pump action'),
                   'flowRate': _translate('Flow rate'),
                   'flowRateUnit': _translate('Flow rate unit'),
                   'switchValveWhenDone': _translate('Switch valve after dosing'),
                   'syncToScreen': _translate('Sync to screen')})


class QmixPumpComponent(BaseComponent):
    """Operate a Cetoni neMESYS syringe pump"""
    targets = ['PsychoPy']
    categories = ['I/O']
    iconFile = Path(__file__).parent / 'pump.png'
    tooltip = _translate('Pump: deliver liquid stimuli via a Cetoni neMESYS syringe pump')

    def __init__(self, exp, parentName, name='pump',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 pumpIndex=0,
                 syringeType='50 mL glass',
                 pumpAction='dispense',
                 flowRate=1.0,
                 flowRateUnit='mL/s',
                 switchValveWhenDone=True,
                 syncToScreen=True):

        super(QmixPumpComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'QmixPump'
        self.url = 'https://www.psychopy.org/builder/components/pump.html'

        self.exp.requireImport(importName='qmix',
                               importFrom='psychopy.hardware')

        # Order in which the user-settable parameters will be displayed
        # in the component's properties window.
        self.order += ['syncToScreen',  # Basic tab
                      'pumpIndex', 'syringeType', 'pumpAction', 'flowRate', 'flowRateUnit', 'switchValveWhenDone',  # Hardware tab
                      ]

        self.params['pumpIndex'] = Param(
            pumpIndex, categ='Hardware',
            valType='code', inputType="single",
            hint=_translate('The index of the pump(s) (first pump is 0).'),
            label=_localized['pumpIndex'])

        self.params['syringeType'] = Param(
            syringeType, categ='Hardware',
            valType='str', inputType="choice",
            allowedVals=qmix.syringeTypes,
            hint=_translate('Syringe type and dimensions'),
            label=_localized['syringeType'])

        self.params['pumpAction'] = Param(
            pumpAction, categ='Hardware',
            valType='str', inputType="choice",
            allowedVals=['aspirate', 'dispense'],
            direct=False,
            hint=_translate('Whether the syringe should be filled (aspirate) '
                            'or emptied (dispense'),
            label=_localized['pumpAction'])

        self.params['flowRate'] = Param(
            flowRate, categ='Hardware',
            valType='num', inputType="single",
            hint='The flow rate',
            label=_localized['flowRate'])

        self.params['flowRateUnit'] = Param(
            flowRateUnit, categ='Hardware',
            valType='str', inputType="choice",
            allowedVals=qmix.flowRateUnits,
            hint='The unit of the flow rate',
            label=_localized['flowRateUnit'])

        self.params['switchValveWhenDone'] = Param(
            switchValveWhenDone, valType='bool', inputType="bool", categ='Hardware',
            allowedVals=[True, False],
            hint=_translate('Switch the valve after pump operation'),
            label=_localized['switchValveWhenDone'])

        self.params['syncToScreen'] = Param(
            syncToScreen, valType='bool', inputType="bool", categ='Basic',
            allowedVals=[True, False],
            hint=_translate('Sync pump onset to the screen refresh'),
            label=_localized['syncToScreen'])

    def writeRunOnceInitCode(self, buff):
        code = ('# Initialize all pumps so they are ready to be used when we\n'
                '# need them later. This enables us to dynamically select\n'
                '# pumps during the experiment without worrying about their\n'
                '# initialization.\n'
                'qmix._init_all_pumps()\n')
        buff.writeOnceIndentedLines(code)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine.
        """
        code = ('\n'
                '# Select the correct pre-initialized pump, and set the \n'
                '# syringe type according to the Pumo Component properties.\n'
                '_pumpInstance = qmix.pumps[%(pumpIndex)s]\n'
                '%(name)s = qmix._PumpWrapperForBuilderComponent(_pumpInstance)\n'
                '%(name)s.syringeType = %(syringeType)s\n'
                '%(name)s.flowRateUnit = %(flowRateUnit)s\n'
                '%(name)s.status = None\n'
                % self.params)
        buff.writeIndentedLines(code)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame.
        """
        buff.writeIndented("# *%s* updates\n" % (self.params['name']))
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)

        if self.params['syncToScreen'].val:
            if self.params['pumpAction'] == 'aspirate':
                code = ('win.callOnFlip(%(name)s.fill, '
                        'flowRate=%(flowRate)s)\n') % self.params
            else:
                code = 'win.callOnFlip(%(name)s.empty, flowRate=%(flowRate)s)\n' % self.params
        else:
            if self.params['pumpAction'] == 'aspirate':
                code = '%(name)s.fill(flowRate=%(flowRate)s)\n' % self.params
            else:
                code = '%(name)s.empty(flowRate=%(flowRate)s)\n' % self.params

        buff.writeIndentedLines(code)
        buff.setIndentLevel(-1, relative=True)

        # Test for stop (only if there was some setting for duration or
        # stop).
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)

            if self.params['syncToScreen'].val:
                if self.params['switchValveWhenDone'].val:
                    code = ('win.callOnFlip(%(name)s.stop)\n'
                            'win.callOnFlip(%(name)s.switchValvePosition)\n'
                            % self.params)
                else:
                    code = 'win.callOnFlip(%(name)s.stop)\n' % self.params
            else:
                if self.params['switchValveWhenDone'].val:
                    code = ('%(name)s.stop()\n'
                            '%(name)s.switchValvePosition()\n'
                            % self.params)
                else:
                    code = '%(name)s.stop()\n' % self.params

            buff.writeIndentedLines(code)
            buff.setIndentLevel(-2, relative=True)

    def writeRoutineEndCode(self, buff):
        # Make sure that we stop the pumps even if the routine has been
        # ended prematurely.
        if self.params['switchValveWhenDone'].val:
            code = ('\nif %(name)s.status == STARTED:\n'
                    '    %(name)s.stop()\n'
                    '    %(name)s.switchValvePosition()\n\n'
                    % self.params)
        else:
            code = ('\nif %(name)s.status == STARTED:\n'
                    '    %(name)s.stop()\n\n' % self.params)

        buff.writeIndentedLines(code)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)
