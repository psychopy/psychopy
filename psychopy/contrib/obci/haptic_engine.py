# -*- coding: utf-8 -*-
# author: Piotr Różański
from obci.devices.haptics.HapticsControl import HapticStimulator

class HapticEngine(object):
    stimulator = None

    def __init__(self):
        if HapticEngine.stimulator is None:
            HapticEngine.stimulator = HapticStimulator()
        self.status = None
        self.channel = None

    def setChannel(self, chnl):
        self.channel = int(chnl)

    def stimulate(self, time):
        if self.channel is not None:
            HapticEngine.stimulator.stimulate(self.channel, time)

    def close(self):
        if HapticEngine.stimulator is not None:
            HapticEngine.stimulator.close()
            HapticEngine.stimulator = None
