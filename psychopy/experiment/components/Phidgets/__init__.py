#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
# Contributor: maqadri - mqadri@holycross.edu

"""
    Interface to Phidgets for analog input, digital input, digital output (5V), and relay control.
"""
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy import prefs, logging

#Modeled after qmix/pump

from pathlib import Path
from psychopy.localization import _localized as __localized
_localized = __localized.copy()

_localized.update({'channelList': _translate('Channel List'),
                   'serialNumber': _translate('Serial Number'),
                   'reversedRelay': _translate('Reversed Relay'),
                   'syncToScreen': _translate('Sync to screen')
                   })

class PhidgetRelayComponent(BaseComponent):
    """Operate a Phidget Relay (0/0/4) or (0/0/8)"""
    targets = ['PsychoPy']
    categories = ['I/O']
    iconFile = Path(__file__).parent / 'phidgets.png'
    tooltip = _translate('Phidget: control operant chamber events using (a) relay(s)')

    def __init__(self, exp, parentName, name='phidgetRelay',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=3.0,
                 startEstim='', durationEstim='',
                 channelList='',
                 serialNumber='',
                 reversedRelay=False,
                 syncToScreen=True):

        super(PhidgetRelayComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'PhidgetOutputRelays'
        self.url = 'https://www.psychopy.org/builder/components/phidget.html'

        self.exp.requireImport(importName='phidgets',
                               importFrom='psychopy.hardware')

        # Order in which the user-settable parameters will be displayed
        # in the component's properties window.
        self.order += ['syncToScreen',  # Basic tab
                        'channelList', 'serialNumber', 'reversedRelay', # Hardware tab
                      ]

        self.params['channelList'] = Param(
            channelList, categ='Hardware',
            valType='list', inputType="single",
            hint=_translate('The list of channels controlled by this component'),
            label=_localized['channelList'])

        self.params['serialNumber'] = Param(
            serialNumber, categ='Hardware',
            valType='num', inputType="int",
            hint=_translate('Serial number for your Phidget Output relay (leave empty if only one Phidget attached to PC)'),
            label=_localized['serialNumber'])

        self.params['reversedRelay'] = Param(
            reversedRelay, categ='Hardware',
            valType='bool', inputType="bool", allowedVals=[True, False],
            hint=_translate('Set reversed if you want the relay to start on and turn off for the indicated duration'),
            label=_localized['reversedRelay'])

        self.params['syncToScreen'] = Param(
            syncToScreen, valType='bool', inputType="bool", categ='Basic',
            allowedVals=[True, False],
            hint=_translate('Sync relay events to the screen refresh'),
            label=_localized['syncToScreen'])

    def writeRunOnceInitCode(self, buff):
        code = ('# Initialize relays\n'
                '%(name)s = phidgets.phidgetOutputComponent(channelList = %(channelList)s, '
                                                           'serialNumber = %(serialNumber)s, '
                                                           'reversedRelay = %(reversedRelay)s)\n'
                % self.params )
        buff.writeOnceIndentedLines(code)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine.
        """

        code = ('\n'
                '%(name)s.openRelay()\n'
                % self.params)

        buff.writeIndentedLines(code)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame.
        """


        buff.writeIndented("# *%s* updates\n" % (self.params['name']))
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)

        if self.params['syncToScreen'].val:
            code = ('\n'
                    'win.callOnFlip(%(name)s.closeRelay)\n'
                    % self.params)
        else:
            code = ('\n'
                    '%(name)s.closeRelay()\n'
                    % self.params)

        buff.writeIndentedLines(code)
        buff.setIndentLevel(-1, relative=True)

        # Test for stop (only if there was some setting for duration or
        # stop).
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)

            if self.params['syncToScreen'].val:
                code = ('\n'
                        'win.callOnFlip(%(name)s.openRelay)\n'
                        % self.params)
            else:
                code = ('\n'
                        '%(name)s.openRelay()\n'
                        % self.params)

            buff.writeIndentedLines(code)
            buff.setIndentLevel(-2, relative=True)


    def writeRoutineEndCode(self, buff):
        #Leave the relay in the default state
        code = ('\n'
                '%(name)s.openRelay()\n'
                % self.params)

        buff.writeIndentedLines(code)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)

    def writeExperimentEndCode(self, buff):
        #Leave the relay in the default state
        code = ('\n'
                '%(name)s.openRelay()\n'
                % self.params)

        buff.writeIndentedLines(code)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeExperimentEndCode(buff)