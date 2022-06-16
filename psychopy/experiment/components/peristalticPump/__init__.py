#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from os import path
from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate
from psychopy.localization import _localized as __localized
import serial.tools.list_ports
_localized = __localized.copy()

_localized.update({'pulseDuration': _translate('Pulse duration (s)'),
                    'numberOfPulses': _translate('Number of pulses'),
                    'numberOfSequences': _translate('Number of sequences'),
                    'delayBetweenSeq': _translate('Delay between sequences (s)'),
                    'delayBetweenPulses': _translate('Delay between pulses (s)'),
                    'saveStats': _translate('Save actions of pump and licks to txt file'),
                    'stopVal': _translate('Duration (s)'),
                    'com_port': _translate('COM port'),})


class PeristalticPumpComponent(BaseComponent):
    """Delivers a water reward to the animal and monitor licks"""
    targets = ['PsychoPy']
    categories = ['I/O']
    iconFile = Path(__file__).parent / 'reward.png'
    tooltip = _translate(
        'LabeoTech Pump: Delivers a water reward to the animal and monitor '
        'water consumption (licks)')

    def __init__(self, exp, parentName, name='reward',
                 pulseDuration=0, numberOfPulses = 0, delayBetweenSeq = 0,
                 numberOfSequences = 0, delayBetweenPulses = 0,
                 startType='time (s)', startVal='0.0', stopVal='1.0',
                 stopType='duration (s)', saveStats = False,
                 com_port="Select pump com port"):

        super(PeristalticPumpComponent, self).__init__(
            exp, parentName, name, startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal
            )

        self.type = 'PeristalticPump'
        self.url = 'file:///C:/Users/delam/Desktop/BehavioralTask/pompe_sequence.html'
        # TODO : create a html help page with pump sequence on the options panel
        #self.url = Path(__file__).parent / 'pompe_sequence.html'

        # Order in which the user-settable parameters will be displayed
        # in the component's properties window.
        #self.order += ['PulseDuration',  # Basic tab]

        self.params['pulseDuration'] = Param(
            pulseDuration, categ='Basic',
            valType='num', inputType="single",
            hint=_translate('The duration of the pulse sent to the peristaltic pump'),
            label=_localized['pulseDuration'])

        self.params['numberOfPulses'] = Param(
            numberOfPulses, categ='Basic',
            valType='num', inputType="single",
            hint=_translate('Number of pulses in a burst sequence'),
            label=_localized['numberOfPulses'])

        self.params['delayBetweenSeq'] = Param(
            delayBetweenSeq, categ='Basic',
            valType='num', inputType="single",
            hint=_translate('Delay between sequences'),
            label=_localized['delayBetweenSeq'])

        self.params['numberOfSequences'] = Param(
            numberOfSequences, categ='Basic',
            valType='num', inputType="single",
            hint=_translate('Number of sequence in a single reward event'),
            label=_localized['numberOfSequences'])

        self.params['delayBetweenPulses'] = Param(
            delayBetweenPulses, categ='Basic',
            valType='num', inputType="single",
            hint=_translate('Delay between pulses in a burst sequence'),
            label=_localized['delayBetweenPulses'])

        self.params['saveStats'] = Param(
            saveStats, categ='Basic',
            valType='bool', inputType="bool",
            hint=_translate('Save log to txt file'),
            label=_localized['saveStats'])

        self.params['stopVal'] = Param(
            ((((pulseDuration * numberOfPulses + delayBetweenPulses) *
               (numberOfPulses - 1)) * numberOfSequences) +
             (delayBetweenSeq * (numberOfSequences - 1))),
            categ='Basic', valType='num', inputType="single",
            hint=_translate('The duration of the pulse sent to the peristaltic pump'),
            label=_localized['stopVal'])
            
        self.params['com_port'] = Param(
            com_port, valType='str', inputType="choice", categ='Basic',
            allowedVals=[p.device for p in serial.tools.list_ports.comports()],
            updates='constant',
            hint=_translate("COM port"),
            label=_localized['com_port'])


    def writeInitCode(self, buff):
            
        """Write variable initialisation code."""
        code =  ("%(name)s = event.Mouse(win=win)\n")
        code += ("pulse_dur = %(pulseDuration)s\n")
        code+= ("number_pulses = %(numberOfPulses)s\n")
        code+= ("delay_sequences = %(delayBetweenSeq)s\n")
        code+= ("number_sequences = %(numberOfSequences)s\n")
        code+= ("delay_pulses = %(delayBetweenPulses)s\n")
        code+= ("saveStats = %(saveStats)s\n")
        code+= ("import psychopy\n")
        code+= ("import serial\n")
        code+= ("import time\n")
        code+=("from datetime import datetime\n")
        code+= ("pump = serial.Serial(port=%(com_port)s, baudrate=115200, timeout=.1)\n")
        code+= ("pulse_started = False\n")
        code+= ("reward_start = %(startVal)s\n")
        code+=("n=0\n")
        code+=("ns=0\n")
        code+=("tp0=0\n")
        code+=("td0=0\n")
        code+=("ts0=0\n")
        code+=("firstFrame = False\n")
        code+=("pause = False\n")
        code+=("""expInfo = {'participant': '', 'session': '001'}\n""")
        code+=("""expInfo['date'] = data.getDateStr()\n""")
        buff.writeIndented(code % self.params)
        code=("""filename_pump = _thisDir + os.sep + u'data/%s_pump_%s' % (expInfo['participant'], expInfo['date'])\n""")
        buff.writeIndented(code)
        code=("""text_file_pump = open(filename_pump + '.txt', 'w')\n""")
        buff.writeIndented(code)


    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine."""
        pass

    def writeFrameCode(self, buff):
        
        buff.writeIndented("if pump.inWaiting():\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("lick_state = pump.readline()\n")
        buff.writeIndented("""if lick_state == b'l\\r\\n':\n""")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("try:\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("if behavioral_sys == True:\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("behavioral_sys = True\n")
        buff.setIndentLevel(-2, relative=True)
        buff.writeIndented("except:\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("""print(str(round(t,2)) + ': lick')\n""")
        buff.writeIndented("if saveStats == True:\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("""text_file_pump.write(str(round(t,2)) + 'lick')\n""")
        #code+=("""    lick_state = b''\n""")
        buff.setIndentLevel(-4, relative=True)
        
        buff.writeIndented("if t>= %(startVal)s and %(name)s.status != FINISHED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("%(name)s.status = STARTED\n" % self.params)
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("if firstFrame == False and  %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)

        buff.writeIndented("firstFrame = True\n")
        buff.writeIndented("tp0 = time.time()\n")
        buff.writeIndented("td=0\n")
        buff.writeIndented("td0=time.time()\n")
        buff.writeIndented("ts0=time.time()\n")
        buff.writeIndented("ts=0\n")
        buff.writeIndented("""pump.write(bytes('o', 'utf-8'))\n""")
        buff.writeIndented("""print(str(round(t,2)) + ': pump ON')\n""")
        buff.writeIndented("pulse_started = True\n")

        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("tp = time.time() - tp0\n")
        buff.writeIndented("ts = time.time() - ts0\n")
        buff.writeIndented("if tp>= pulse_dur and pulse_started == True and pause == False and firstFrame == True and %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("""pump.write(bytes('f', 'utf-8'))\n""")
        buff.writeIndented("""print(str(round(t,2)) + ': pump OFF')\n""")
        buff.writeIndented("pulse_started = False\n")
        buff.writeIndented("n+=1\n")
        buff.writeIndented("td0 = time.time()\n")

        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("td = time.time() - td0\n")
        buff.writeIndented("if td >= delay_pulses and pulse_started == False and pause == False and firstFrame == True:\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("pulse_started = True\n")
        buff.writeIndented("if not n >= number_pulses :\n")
        buff.setIndentLevel(1, relative=True)

        buff.writeIndented("""pump.write(bytes('o', 'utf-8'))\n""")
        buff.writeIndented("""print(str(round(t,2)) + ': pump ON')\n""")
        buff.writeIndented("pulse_started = True\n")
        buff.writeIndented("tp0 = time.time()\n")
        buff.setIndentLevel(-2, relative=True)
        buff.writeIndented("if n == number_pulses and %(name)s.status == STARTED and pause == False:\n" % self.params)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("""pump.write(bytes('f', 'utf-8'))\n""")
        buff.writeIndented("ts0 = time.time()\n")
        buff.writeIndented("pause=True\n")
        buff.writeIndented("ns+=1\n")
        buff.writeIndented("n=0\n")
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("if ns == number_sequences and %(name)s.status == STARTED:\n" % self.params)
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("pump.write(bytes('f', 'utf-8'))\n")
        buff.writeIndented("%(name)s.status = FINISHED\n" % self.params)
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("ts = time.time()-ts0\n")
        buff.writeIndented("if ts >= delay_sequences and pause == True and firstFrame == True:\n")
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("pause=False\n")
        buff.writeIndented("pulse_started = True\n")
        buff.writeIndented("""pump.write(bytes('o', 'utf-8'))\n""")
        buff.writeIndented("""print(str(round(t,2)) + ': pump ON')\n""")
        buff.writeIndented("tp0 = time.time()\n")
    
        buff.setIndentLevel(-1, relative=True)

    def writeRoutineEndCode(self, buff):
        buff.writeIndented("%(name)s.status = 0\n" % self.params)
        buff.writeIndented("ns = 0\n")
        buff.writeIndented("n = 0\n")
        buff.writeIndented("firstFrame = False\n")
        buff.writeIndented("pause = False\n")


    def writeExperimentEndCode(self, buff):
        pass