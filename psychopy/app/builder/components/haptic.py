# -*- coding: utf-8 -*-
# author: Piotr Różański

from os import path
from _base import BaseComponent
from psychopy.app.builder.experiment import Param

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, "haptic.png")

class HapticComponent(BaseComponent):
    def __init__(self, exp, parentName, name="haptic", startType="time (s)", startVal=0.0, stopType="duration (s)", stopVal=1.0, startEstim="", durationEstim=1.0):
        self.type = "Haptic stimulation"
        self.exp = exp
        self.parentName = parentName
        self.params = {
            "name": Param(name, valType = "code", hint = "A name for this object", label = "Name"),
            "startType": Param(startType, valType = "str", allowedVals = ["time (s)", "frame N", "condition"], hint = "How to specify the start time", label = ""),
            "stopType": Param(stopType, valType = "str", allowedVals = ['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'], hint = "How duration is defined"),
            "startVal": Param(startVal, valType = "code", allowedTypes = [], hint = "Time of appliance timestamp"),
            "stopVal": Param(stopVal, allowedVals = [1], valType= "code", allowedTypes = [], updates = 'constant', allowedUpdates = [], hint = "One-shot"),
            "startEstim": Param(startEstim, valType = 'code', allowedTypes = [], hint = "(Optional) expected start (s), purely for representing in the timeline"),
            "durationEstim": Param(durationEstim, valType = "code", allowedVals = [0.02], allowedTypes = [], hint = "One-shot"),
            "channel": Param('1', valType="code", allowedTypes=[], hint="Index of active channel for haptic stimulator", label="haptic channel"),
        }
        self.order = ["channel"]

    def writeStartCode(self, buff):
        buff.writeIndented("import psychopy.contrib.obci.haptic_engine\n")

    def writeInitCode(self, buff):
        buff.writeIndented("%s = psychopy.contrib.obci.haptic_engine.HapticEngine()\n" % self.params["name"].val)

    def writeFrameCode(self, buff):
        codeEntries = {
            "name": self.params["name"].val,
            "duration": self.getStartAndDuration()[1],
        }
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.stimulate(%(duration)s)\n" % codeEntries)
        buff.writeIndented("%(name)s.status = STARTED\n" % codeEntries)
        buff.setIndentLevel(-1, relative = True)
        self.writeStopTestCode(buff)
        buff.writeIndented("%(name)s.status = FINISHED\n" % codeEntries)
        buff.setIndentLevel(-1, relative = True)

    def writeExperimentEndCode(self, buff):
        buff.writeIndented("%s.close()\n" % self.params["name"].val)
