#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple example of Cetoni neMESYS syringe pump control, based on the `pyqmix`
library. The syringe pump system is described in the following publication:

    CA Andersen, L Alfine, K Ohla, & R Höchenberger (2018):
    "A new gustometer: Template for the construction of a portable and
     modular stimulator for taste and lingual touch."
    Behavior Research Methods. doi: 10.3758/s13428-018-1145-1

"""

from psychopy import event
from psychopy import core
from psychopy.visual import Window, TextStim
from psychopy.hardware import qmix


print('Supported syringe types: %s' % qmix.syringeTypes)
print('Supported volume units: %s' % qmix.volumeUnits)
print('Supported flow rate units: %s' % qmix.flowRateUnits)

# Initialize the first pump (index 0). We assume the pump is
# equipped with a 50 mL glass syringe.
pump = qmix.Pump(index=0,
                 volumeUnit='mL',
                 flowRateUnit='mL/s',
                 syringeType='50 mL glass')

print('Max. flow rate: .3%f %s' % (pump.maxFlowRate, pump.flowRateUnit))

win = Window()
msg = ('Press one of the following keys: \n\n'
       '    F – Fill Syringe at 1 mL/s\n'
       '    E – Empty Syringe at 1 mL/s\n'
       '    A – Aspirate 1 mL at 1 mL/s\n'
       '    D – Dispense 1 mL at 1 mL/s\n'
       '\n'
       '    Q – Quit')
t = TextStim(win, msg)

event.clearEvents()
while True:
    t.draw()
    win.flip()

    # Retrieve keypresses. The user can completely fill or empty the syringe,
    # or aspirate or dispense a small volume (1 mL) by pressing the
    # corresponding keys.
    #
    # When aspirating or dispensing, the code halts further script execution
    # until the pump operation has finished, and then immediately switches the
    # valve position (i.e., from inlet to outlet after aspiration, and from
    # outlet to inlet after dispense). During an experiment, this can ensure
    # a sharp(er) stimulus offset.

    keys = event.getKeys(keyList=['f', 'e', 'a', 'd', 'q'])
    if 'f' in keys:
        pump.fill(flowRate=1, waitUntilDone=False)
    elif 'e' in keys:
        pump.empty(flowRate=1, waitUntilDone=False)
    elif 'a' in keys:
        pump.aspirate(volume=1,
                      flowRate=1,
                      waitUntilDone=True,
                      switchValveWhenDone=True)
    elif 'd' in keys:
        pump.dispense(volume=1,
                      flowRate=1,
                      waitUntilDone=True,
                      switchValveWhenDone=True)
    elif 'q' in keys:
        break

# Immdiately halt all pump operation and shutdown PsychoPy.
pump.stop()
core.quit()
