# -*- coding: utf-8 -*-
# author: Mateusz Kruszyński

from _base import *

thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, "diodes.png")

class ApplianceComponent(BaseComponent):
    ApplianceBuff = False
    def __init__(
            self, exp, parentName, name="appliance", startType="time (s)", startVal=0.0,
            stopType="duration (s)", stopVal=1.0, startEstim="", durationEstim=1.0):#, tagName="tag",
        #tagDescription="{}"):
        self.type = "Appliance"
        self.exp = exp
        self.parentName = parentName
        self.params = {}

        self.params["name"] = Param(name, valType = "code", hint = "A name for this object", label = "Name")
        self.params["startType"]=Param(startType, valType = "str", allowedVals = ["time (s)", "frame N", "condition"],
            hint = "How to specify the start time", label = "")
        self.params["stopType"] = Param(stopType, valType = "str", allowedVals = ['duration (s)', 'duration (frames)', 'time (s)', 'frame N', 'condition'],
            hint = "How duration is defined")

        self.params["startVal"] = Param(startVal, valType = "code", allowedTypes = [],
            hint = "Time of appliance timestamp")
        self.params["stopVal"] = Param(stopVal, allowedVals = [1], valType= "code", allowedTypes = [],
            updates = 'constant', allowedUpdates = [], hint = "One-shot")

        self.params['startEstim'] = Param(startEstim, valType = 'code', allowedTypes = [],
            hint = "(Optional) expected start (s), purely for representing in the timeline")
        self.params["durationEstim"] = Param(durationEstim, valType = "code", allowedVals = [0.02], allowedTypes = [],
            hint = "One-shot")

        self.order = ['startIndex', 'startValue', 'startValues', 'endIndex', 'endValue', 'endValues']
        r = 'set every repeat'

        self.params["startValues"] = Param(
            str([-1]*8), valType="code", updates="experiment", allowedUpdates=[r],
            hint="Freq values to be sent to appliance at the beginnig, shoult be either a list of 8 elements or empty to ignore this parameter and use (startIndex, startValue)", label="start all fields")
        self.params["startIndex"] = Param(
            0, valType="code", updates="experiment", allowedUpdates=[r],
            hint="Appliance's field index to be filled with startValue freq at the beginning, other fields remain the same", label="start field index")
        self.params["startValue"] = Param(
            0, valType="code", updates="experiment", allowedUpdates=[r],
            hint="Freq value to fill appliance's startIndex field at the beginning, other fields remain the same", label="start field value")

        self.params["endValues"] = Param(
            str([-1]*8), valType="code", updates="experiment", allowedUpdates=[r],
            hint="Freq values to be sent to appliance at the end, shoult be either a list of 8 elements or empty to ignore this parameter and use (endIndex, endValue)", label="end all fields")
        self.params["endIndex"] = Param(
            0, valType="code", updates="experiment", allowedUpdates=[r],
            hint="Appliance's field index to be filled with endValue freq at the beginning, other fields remain the same", label="end field index")
        self.params["endValue"] = Param(
            0, valType="code", updates="experiment", allowedUpdates=[r],
            hint="Freq value to fill appliance's endIndex field at the end, other fields remain the same", label="end field value")


    def writeStartCode(self, buff):
        buff.writeIndented("import psychopy.contrib.obci.appliance_engine\n")

    def writeInitCode(self, buff):
        ApplianceComponent.ApplianceBuff = buff
        
        appliance_type = self.exp.settings.params['applianceType'].val
        dev_path = self.exp.settings.params['applianceDevicePath'].val
        intensity = self.exp.settings.params['applianceIntensity'].val
        codeEntries = {
            "name": self.params["name"].val,
            "appliance_type":appliance_type,
            "dev_path":dev_path,
            "intensity":intensity
            }
        buff.writeIndented("%(name)s = psychopy.contrib.obci.appliance_engine.ApplianceEngine(\n" % codeEntries)
        buff.writeIndented("        '%(appliance_type)s', '%(dev_path)s', %(intensity)s)\n" % codeEntries)

    def writeRoutineStartCode(self,buff):
        """Write the code that will be called at the beginning of
        a routine (e.g. to update stimulus parameters)
        """
        codeEntries = {"name": self.params["name"].val}
        buff.writeIndented("%(name)s.start_routine()\n" % codeEntries)
        super(ApplianceComponent, self).writeRoutineStartCode(buff)

    def writeFrameCode(self, buff):
        codeEntries = {"name": self.params["name"].val}
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.start()\n" % codeEntries)
        buff.writeIndented("%(name)s.status = STARTED\n" % codeEntries)
        buff.setIndentLevel(-1, relative = True)
        self.writeStopTestCode(buff)
        buff.writeIndented("%(name)s.end()\n" % codeEntries)
        buff.writeIndented("%(name)s.status = FINISHED\n" % codeEntries)
        buff.setIndentLevel(-1, relative = True)

    def getStartAndDuration(self):
        """Always return nonSlipSafe as False, so that FrameCode including .end() will always fire."""
        startTime, duration, nonSlipSafe = super(ApplianceComponent, self).getStartAndDuration()
        return startTime, duration, False
