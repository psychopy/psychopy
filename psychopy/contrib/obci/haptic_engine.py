# -*- coding: utf-8 -*-
# author: Piotr Różański
from obci.devices.haptics.HapticsControl import HapticStimulator

class HapticEngine(object):
    stimulator = None

    def __init__(self):
        if HapticEngine.stimulator is None:
            HapticEngine.stimulator = HapticStimulator()
        self.status = None

    def stimulate(self, chnl, time):
        HapticEngine.stimulator.stimulate(chnl, time)

    def close(self):
        if HapticEngine.stimulator is not None:
            HapticEngine.stimulator.close()
            HapticEngine.stimulator = None
