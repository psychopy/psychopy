#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
Distributed under the terms of the GNU General Public License (GPL).
"""

from pathlib import Path
from psychopy.experiment.components import BaseDeviceComponent, Param, getInitVals, \
    _translate
from psychopy.experiment.utils import canBeNumeric
from psychopy.tools.audiotools import knownNoteNames


class SoundComponent(BaseDeviceComponent):
    """An event class for presenting sound stimuli"""
    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'sound.png'
    tooltip = _translate('Sound: play recorded files or generated sounds', )
    deviceClasses = ["psychopy.hardware.speaker.SpeakerDevice"]

    def __init__(self,
                 exp, parentName,
                 # basic
                 name='sound_1',
                 sound='A',
                 startType='time (s)', startVal='0.0',
                 stopType='duration (s)', stopVal='1.0',
                 startEstim='', durationEstim='',
                 syncScreenRefresh=True,
                 # device
                 deviceLabel="",
                 speakerIndex=-1,
                 # playback
                 volume=1,
                 stopWithRoutine=True,
                 forceEndRoutine=False):
        super(SoundComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            deviceLabel=deviceLabel
        )
        self.type = 'Sound'
        self.url = "https://www.psychopy.org/builder/components/sound.html"
        self.exp.requirePsychopyLibs(['sound'])
        self.order += [
            "sound",  # Basic tab
            "volume", "hammingWindow",  # Playback tab
        ]
        # params
        hnt = _translate("When does the Component end? (blank to use the "
                         "duration of the media)")
        self.params['stopVal'].hint = hnt

        hnt = _translate("A sound can be a note name (e.g. A or Bf), a number"
                         " to specify Hz (e.g. 440) or a filename")
        self.params['sound'] = Param(
            sound, valType='str', inputType="file", allowedTypes=[], updates='constant', categ='Basic',
            allowedUpdates=['set every repeat'],
            hint=hnt,
            label=_translate("Sound"))
        _allowed = ['constant', 'set every repeat', 'set every frame']
        self.params['volume'] = Param(
            volume, valType='num', inputType="single", allowedTypes=[], updates='constant', categ='Playback',
            allowedUpdates=_allowed[:],  # use a copy
            hint=_translate("The volume (in range 0 to 1)"),
            label=_translate("Volume"))
        msg = _translate(
            "A reaction time to a sound stimulus should be based on when "
            "the screen flipped")
        self.params['syncScreenRefresh'] = Param(
            syncScreenRefresh, valType='bool', inputType="bool", categ='Basic',
            updates='constant',
            hint=msg,
            label=_translate("Sync start with screen"))
        # --- Playback params ---
        self.order += [
            "hamming",
            "stopWithRoutine",
            "forceEndRoutine"
        ]
        self.params['hamming'] = Param(
            True, valType='bool', inputType="bool", updates='constant', categ='Playback',
            hint=_translate(
                  "For tones we can apply a hamming window to prevent 'clicks' that "
                  "are caused by a sudden onset. This delays onset by roughly 1ms."),
            label=_translate("Hamming window"))
        self.params['stopWithRoutine'] = Param(
            stopWithRoutine, valType='bool', inputType="bool", updates='constant', categ='Playback',
            hint=_translate(
                "Should playback cease when the Routine ends? Untick to continue playing "
                "after the Routine has finished."),
            label=_translate('Stop with Routine?'))
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType="bool", inputType="bool", updates="constant", categ="Playback",
            hint=_translate(
                "Should the end of the sound cause the end of the Routine (e.g. trial)?"
            ),
            label=_translate("Force end of Routine")
        )

        # --- Device params ---
        self.order += [
            "speaker"
        ]

        def getSpeakerLabels():
            from psychopy.hardware.speaker import SpeakerDevice
            labels = [_translate("Default")]
            for profile in SpeakerDevice.getAvailableDevices():
                labels.append(profile['deviceName'])

            return labels

        def getSpeakerValues():
            from psychopy.hardware.speaker import SpeakerDevice
            vals = [-1]
            for profile in SpeakerDevice.getAvailableDevices():
                vals.append(profile['index'])

            return vals

        self.params['speakerIndex'] = Param(
            speakerIndex, valType="str", inputType="choice", categ="Device",
            allowedVals=getSpeakerValues,
            allowedLabels=getSpeakerLabels,
            hint=_translate(
                "What speaker to play this sound on"
            ),
            label=_translate("Speaker")
        )

    def writeDeviceCode(self, buff):
        inits = getInitVals(self.params)
        # initialise speaker
        code = (
            "# create speaker %(deviceLabel)s\n"
            "deviceManager.addDevice(\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    deviceClass='psychopy.hardware.speaker.SpeakerDevice',\n"
            "    index=%(speakerIndex)s\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)

    def writeInitCode(self, buff):
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if not canBeNumeric(inits['stopVal'].val):
            inits['stopVal'].val = -1
        else:
            if inits['stopVal'].val in ['', None, 'None']:
                inits['stopVal'].val = -1
            elif float(inits['stopVal'].val) > 2:
                inits['stopVal'].val = -1
        # are we forcing stereo?
        inits['forceStereo'] = self.exp.settings.params['Force stereo']
        # write init code
        code = (
            "%(name)s = sound.Sound(\n"
            "    %(sound)s, \n"
            "    secs=%(stopVal)s, \n"
            "    stereo=%(forceStereo)s, \n"
            "    hamming=%(hamming)s, \n"
            "    speaker=%(deviceLabel)s,"
            "    name='%(name)s'\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.writeIndented("%(name)s.setVolume(%(volume)s)\n" % inits)

    def writeRoutineStartCode(self, buff):
        if self.params['stopVal'].val in [None, 'None', '']:
            buff.writeIndentedLines("%(name)s.setSound(%(sound)s, hamming=%(hamming)s)\n"
                                    "%(name)s.setVolume(%(volume)s, log=False)\n" % self.params)
        else:
            buff.writeIndentedLines("%(name)s.setSound(%(sound)s, secs=%(stopVal)s, hamming=%(hamming)s)\n"
                                    "%(name)s.setVolume(%(volume)s, log=False)\n" % self.params)
        code = (
            "%(name)s.seek(0)\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeInitCodeJS(self, buff):
        # replaces variable params with sensible defaults
        inits = getInitVals(self.params)
        if not canBeNumeric(inits['stopVal'].val):
            inits['stopVal'].val = -1
        elif inits['stopVal'].val in ['', None, 'None']:
            inits['stopVal'].val = -1
        elif float(inits['stopVal'].val) > 2:
            inits['stopVal'].val = -1
        buff.writeIndented("%s = new sound.Sound({\n"
                           "    win: psychoJS.window,\n"
                           "    value: %s,\n"
                           "    secs: %s,\n"
                           "    });\n" % (inits['name'],
                                          inits['sound'],
                                          inits['stopVal']))
        buff.writeIndented("%(name)s.setVolume(%(volume)s);\n" % (inits))
        # until isFinished and isPlaying are added in JS, we can immitate them here
        code = (
            "%(name)s.isPlaying = false;\n"
            "%(name)s.isFinished = false;\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCodeJS(self, buff):
        stopVal = self.params['stopVal']
        if stopVal in ['', None, 'None']:
            stopVal = -1

        if self.params['sound'].updates == 'set every repeat':
            buff.writeIndented("%(name)s.setValue(%(sound)s);\n" % self.params)
        if stopVal == -1:
            buff.writeIndentedLines("%(name)s.setVolume(%(volume)s);\n" % self.params)
        else:
            buff.writeIndentedLines("%(name)s.secs=%(stopVal)s;\n"
                                    "%(name)s.setVolume(%(volume)s);\n" % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # Write start code to update parameters. Unlike BaseVisualComponents, which
        # inserts writeActiveTestCode() after the start code, we need to insert it
        # here before the start code to provide the correct parameters for calling
        # the play() method.

        buff.writeIndented("\n")
        buff.writeIndented(f"# *{self.params['name']}* updates\n")
        self.writeParamUpdates(buff, 'set every frame')

        # write code for starting
        indented = self.writeStartTestCode(buff)
        if indented:
            if self.params['syncScreenRefresh'].val:
                code = ("%(name)s.play(when=win)  # sync with win flip\n")
            else:
                code = "%(name)s.play()  # start the sound (it finishes automatically)\n"
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # write code for stopping
        indented = self.writeStopTestCode(buff, extra=" or %(name)s.isFinished")
        if indented:
            # stop playback
            code = (
                "%(name)s.stop()\n"
            )
            buff.writeIndentedLines(code % self.params)
            # force end of Routine
            code = (
                "# %(name)s has finished playback, so force end Routine\n"
                "continueRoutine = False\n"
            )
            buff.writeIndentedLines(code % self.params)
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-indented, relative=True)

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame
        """
        # until isFinished and isPlaying are added in JS, we can immitate them here
        code = (
            "if (%(name)s.status === STARTED) {\n"
            "    %(name)s.isPlaying = true;\n"
            "    if (t >= (%(name)s.getDuration() + %(name)s.tStart)) {\n"
            "        %(name)s.isFinished = true;\n"
            "    }\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)

        # the sound object is unusual, because it is
        buff.writeIndented("// start/stop %(name)s\n" % (self.params))
        # do this EVERY frame, even before/after playing?
        self.writeParamUpdates(buff, 'set every frame', target="PsychoJS")
        self.writeStartTestCodeJS(buff)
        if self.params['syncScreenRefresh'].val:
            code = ("psychoJS.window.callOnFlip(function(){ %(name)s.play(); });  // screen flip\n")
        else:
            code = "%(name)s.play();  // start the sound (it finishes automatically)\n"
        code += "%(name)s.status = PsychoJS.Status.STARTED;\n"
        buff.writeIndentedLines(code % self.params)
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines('}\n')
        
        # are we stopping this frame?
        indented = self.writeStopTestCodeJS(buff, extra=" || %(name)s.isFinished")
        if indented:
            # stop playback
            code = (
                "// stop playback\n"
            )
            if self.params['syncScreenRefresh'].val:
                code += (
                    "psychoJS.window.callOnFlip(function(){ %(name)s.stop(); });\n"
                )
            else:
                code += (
                    "%(name)s.play();\n"
                )
            buff.writeIndentedLines(code % self.params)
            # end Routine if asked
            if self.params['forceEndRoutine']:
                code = (
                    "// %(name)s has finished playback, so force end Routine\n"
                    "continueRoutine = false;\n"
                )
                buff.writeIndentedLines(code % self.params)
            # exit if statement(s)
            for n in range(indented):
                buff.setIndentLevel(-1, relative=True)
                buff.writeIndentedLines("}\n")

    def writeRoutineEndCode(self, buff):
        if self.params['stopWithRoutine']:
            # stop at the end of the Routine, if requested
            code = (
                "%(name)s.pause()  # ensure sound has stopped at end of Routine\n"
            )
            buff.writeIndentedLines(code % self.params)
        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)  # noinspection

    def writeRoutineEndCodeJS(self, buff):
        if self.params['stopWithRoutine']:
            # stop at the end of the Routine, if requested
            code = (
                "%(name)s.stop();  // ensure sound has stopped at end of Routine\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeParamUpdate(
            self, 
            buff, 
            compName, 
            paramName, 
            val, 
            updateType,
            params=None, 
            target="PsychoPy",
    ):
        """
        Overload BaseComponent.writeParamUpdate to handle special case for SoundComponent
        """
        # when writing param updates for Sound.sound, needs to be `setValue` in JS
        # (this is intended as a temporary patch - please delete when `setSound` in JS can accept 
        # the same range of values as in Py)
        if target == 'PsychoJS' and paramName == "sound":
            # get logging string
            if updateType == 'set every frame' and target == 'PsychoJS':
                loggingStr = ', false'
            else:
                loggingStr = ''
            # write setValue code
            code = (
                f"{compName}.setValue({val}{loggingStr});\n"
            )
            buff.writeIndented(code)
        else:
            # do normal stuff for every other param
            BaseDeviceComponent.writeParamUpdate(
                self, 
                buff, 
                compName, 
                paramName, 
                val, 
                updateType,
                params=params, 
                target=target,
            )
