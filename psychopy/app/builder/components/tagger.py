# -*- coding: utf-8 -*-
# author: Piotr Iwaniuk

from _base import *

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, "tagger.png")

class TagOnFlipComponent(BaseComponent):
    def __init__(
            self, exp, parentName, name="tagger", startType="time (s)", startVal=0.0,
            stopType="duration (frames)", stopVal=1, startEstim="", durationEstim=0.02, tagName="tag"):
        self.type = "TagOnFlip"
        self.exp = exp
        self.parentName = parentName
        self.params = {}
        self.order = ["doTag", "tagName", "doSignal", "signalByte"]
        self.params["name"] = Param(name, valType = "code", hint = "A name for this object", label = "Name")
        self.params["startType"]=Param(startType, valType = "str", allowedVals = ["time (s)", "frame N", "condition"],
            hint = "How to specify the start time", label = "")
        self.params["stopType"] = Param(stopType, valType = "str", allowedVals = ["duration (frames)"],
            hint = "How duration is defined")
        self.params["startVal"] = Param(startVal, valType = "code", allowedTypes = [],
            hint = "Time of tag timestamp")
        self.params["stopVal"] = Param(stopVal, allowedVals = [1], valType= "code", allowedTypes = [],
            updates = 'constant', allowedUpdates = [], hint = "One-shot")
        self.params['startEstim'] = Param(startEstim, valType = 'code', allowedTypes = [],
            hint = "(Optional) expected start (s), purely for representing in the timeline")
        self.params["durationEstim"] = Param(durationEstim, valType = "code", allowedVals = [0.02], allowedTypes = [],
            hint = "One-shot")
        self.params["doTag"] = Param(True, valType = "bool", hint = "Should tag be sent?")
        self.params["tagName"] = Param(tagName, valType = "str", hint = "Name of tag to be sent")
        self.params["doSignal"] = Param(False, valType = "bool", hint = "Should signal be sent?")
        self.params["signalByte"] = Param("A", valType = "str", hint = "Byte to be sent through serial port")
    
    def writeInitCode(self, buff):
        codeEntries = {
          "name": self.params["name"].val,
          "doTag": self.params["doTag"].val,
          "tagName": self.params["tagName"].val,
          "doSignal": self.params["doSignal"].val,
          "signalByte": self.params["signalByte"].val
        }
        buff.writeIndented("%(name)s = obci.TagOnFlip(\n" % codeEntries)
        buff.writeIndented("        window=win, doTag=%(doTag)s,\n" % codeEntries)
        buff.writeIndented("        tagName=\"%(tagName)s\", doSignal=%(doSignal)s,\n" % codeEntries)
        buff.writeIndented("        signalByte='%(signalByte)s')\n" % codeEntries)
    def writeFrameCode(self, buff):
        codeEntries = {
          "name": self.params["name"].val
        }
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.schedule()\n" % codeEntries);
        buff.setIndentLevel(-1, relative = True)

