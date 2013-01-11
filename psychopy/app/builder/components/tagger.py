# -*- coding: utf-8 -*-
# author: Piotr Iwaniuk

from _base import *

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, "tagger.png")

class TagOnFlipComponent(BaseComponent):
    requestedTriggerPort = False
    def __init__(
            self, exp, parentName, name="tagger", startType="time (s)", startVal=0.0,
            stopType="duration (frames)", stopVal=1, startEstim="", durationEstim=0.02, tagName="tag",
            tagDescription="{}"):
        self.type = "TagOnFlip"
        self.exp = exp
        self.parentName = parentName
        self.params = {}
        self.order = ["tagName", "tagDescription"]
        self.params["name"] = Param(name, valType = "code", hint = "A name for this object", label = "Name")
        self.params["startType"]=Param(startType, valType = "str", allowedVals = ["time (s)", "frame N", "condition"],
            hint = "How to specify the start time", label = "")
        self.params["stopType"] = Param(stopType, valType = "str", allowedVals = ['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint = "How duration is defined")
        self.params["startVal"] = Param(startVal, valType = "code", allowedTypes = [],
            hint = "Time of tag timestamp")
        self.params["stopVal"] = Param(stopVal, valType= "code", allowedTypes = [],
            updates = 'constant', allowedUpdates = [], hint = "Tagged event duration")
        self.params['startEstim'] = Param(startEstim, valType = 'code', allowedTypes = [],
            hint = "(Optional) expected start (s), purely for representing in the timeline")
        self.params["durationEstim"] = Param(durationEstim, valType = "code", allowedVals = [0.02], allowedTypes = [],
            hint = "One-shot")
        self.params["tagName"] = Param(
            tagName, valType="str", updates="experiment", allowedUpdates=["experiment", "routine", "frame"],
            hint="Name of tag to be sent", label="tag name")
        self.params["tagDescription"] = Param(
            tagDescription, valType="code", updates="experiment", allowedUpdates=["experiment", "routine", "frame"],
            label="tag description", hint="A dictionary of parameters attached to the tag.")
            
    
    def writeStartCode(self, buff):
        triggerDevice = self.exp.settings.params['serialTriggerDevice'].val
        buff.writeIndented("import psychopy.contrib.obci\n")
        buff.writeIndented("import psychopy.contrib as contrib\n")
        # ensure line is generated only once
        if self.exp.settings.params["doSignal"].val and TagOnFlipComponent.requestedTriggerPort != buff:
            buff.writeIndented("win.requestTriggerPort(\"%s\")\n" % triggerDevice)
            TagOnFlipComponent.requestedTriggerPort = buff

    def writeRoutineStartCode(self, buff):
        self.writeParamUpdates(buff, "routine")
    
    def writeInitCode(self, buff):
        codeEntries = {
            "name": self.params["name"].val,
            "tagName": self.params["tagName"].val,
            "tagDescription": {},
            "doSignal": self.exp.settings.params["doSignal"].val,
        }
        buff.writeIndented("%(name)s = contrib.obci.TagOnFlip(\n" % codeEntries)
        buff.writeIndented("        window=win,\n" % codeEntries)
        buff.writeIndented("        tagName=\"%(tagName)s\", tagDescription=%(tagDescription)s," % codeEntries)
        buff.writeIndented("        doSignal=%(doSignal)s,\n" % codeEntries)
        buff.writeIndented("        sendTags=thisExp.sendTags, saveTags=thisExp.saveTags)\n" % codeEntries)
        self.writeParamUpdates(buff, "experiment")
        
    def writeFrameCode(self, buff):
        codeEntries = {
            "name": self.params["name"].val
        }
        self.writeStartTestCode(buff)
        self.writeParamUpdates(buff, "frame")
        buff.writeIndented("%(name)s.scheduleStart()\n" % codeEntries)
        buff.writeIndented("%(name)s.status = STARTED\n" % codeEntries)
        buff.setIndentLevel(-1, relative = True)
        self.writeStopTestCode(buff)
        buff.writeIndented("%(name)s.scheduleStop()\n" % codeEntries)
        buff.writeIndented("%(name)s.status = FINISHED\n" % codeEntries)
        buff.setIndentLevel(-1, relative = True)

