#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy R. Gray, 2012
from pathlib import Path

from psychopy import logging
from psychopy.alerts import alert
from psychopy.tools import stringtools as st, systemtools as syst, audiotools as at
from psychopy.experiment.components import BaseComponent, Param, getInitVals, _translate
from psychopy.tools.audiotools import sampleRateQualityLevels

_hasPTB = True
try:
    import psychtoolbox.audio as audio
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "The 'psychtoolbox' library cannot be loaded but is required for audio "
        "capture (use `pip install psychtoolbox` to get it). Microphone "
        "recording will be unavailable this session. Note that opening a "
        "microphone stream will raise an error.")
    _hasPTB = False

# Get list of devices
if _hasPTB and not syst.isVM_CI():
    devices = syst.getAudioCaptureDevices()
    deviceIndices = [str(d['index']) for d in devices]
    deviceNames = [d['name'] for d in devices]
else:
    devices = []
    deviceIndices = []
    deviceNames = []
deviceIndices.append(None)
deviceNames.append("default")
# Get list of sample rates
sampleRates = {r[1]: r[0] for r in sampleRateQualityLevels.values()}

onlineTranscribers = {
    "Google": "GOOGLE"
}
localTranscribers = {
    "Google": "google",
    "Whisper": "whisper", 
    "Built-in": "sphinx"
}
allTranscribers = {**localTranscribers, **onlineTranscribers}


class MicrophoneComponent(BaseComponent):
    """An event class for capturing short sound stimuli"""
    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']
    version = "2021.2.0"
    iconFile = Path(__file__).parent / 'microphone.png'
    tooltip = _translate('Microphone: basic sound capture (fixed onset & '
                         'duration), okay for spoken words')

    def __init__(self, exp, parentName, name='mic',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=2.0,
                 startEstim='', durationEstim='',
                 channels='auto', device=None,
                 sampleRate='DVD Audio (48kHz)', maxSize=24000,
                 outputType='default', speakTimes=True, trimSilent=False,
                 transcribe=False, transcribeBackend="Whisper",
                 transcribeLang="en-US", transcribeWords="",
                 transcribeWhisperModel="base",
                 transcribeWhisperDevice="auto",
                 #legacy
                 stereo=None, channel=None):
        super(MicrophoneComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Microphone'
        self.url = "https://www.psychopy.org/builder/components/microphone.html"
        self.exp.requirePsychopyLibs(['sound'])

        self.order += []

        self.params['stopType'].allowedVals = ['duration (s)']
        msg = _translate(
            'The duration of the recording in seconds; blank = 0 sec')
        self.params['stopType'].hint = msg

        # params
        msg = _translate("What microphone device would you like the use to record? This will only affect local "
                         "experiments - online experiments ask the participant which mic to use.")
        self.params['device'] = Param(
            device, valType='str', inputType="choice", categ="Basic",
            allowedVals=deviceIndices,
            allowedLabels=deviceNames,
            hint=msg,
            label=_translate("Device")
        )

        msg = _translate(
            "Record two channels (stereo) or one (mono, smaller file). Select 'auto' to use as many channels "
            "as the selected device allows.")
        if stereo is not None:
            # If using a legacy mic component, work out channels from old bool value of stereo
            channels = ['mono', 'stereo'][stereo]
        self.params['channels'] = Param(
            channels, valType='str', inputType="choice", categ='Hardware',
            allowedVals=['auto', 'mono', 'stereo'],
            hint=msg,
            label=_translate("Channels"))

        msg = _translate(
            "How many samples per second (Hz) to record at")
        self.params['sampleRate'] = Param(
            sampleRate, valType='num', inputType="choice", categ='Hardware',
            allowedVals=list(sampleRates),
            hint=msg, direct=False,
            label=_translate("Sample rate (hz)"))

        msg = _translate(
            "To avoid excessively large output files, what is the biggest file size you are likely to expect?")
        self.params['maxSize'] = Param(
            maxSize, valType='num', inputType="single", categ='Hardware',
            hint=msg,
            label=_translate("Max recording size (kb)"))

        msg = _translate(
            "What file type should output audio files be saved as?")
        self.params['outputType'] = Param(
            outputType, valType='code', inputType='choice', categ='Data',
            allowedVals=["default"] + at.AUDIO_SUPPORTED_CODECS,
            hint=msg,
            label=_translate("Output file type")
        )

        msg = _translate(
            "Tick this to save times when the participant starts and stops speaking")
        self.params['speakTimes'] = Param(
            speakTimes, valType='bool', inputType='bool', categ='Data',
            hint=msg,
            label=_translate("Speaking start / stop times")
        )

        msg = _translate(
            "Trim periods of silence from the output file")
        self.params['trimSilent'] = Param(
            trimSilent, valType='bool', inputType='bool', categ='Data',
            hint=msg,
            label=_translate("Trim silent")
        )

        # Transcription params
        self.order += [
            'transcribe',
            'transcribeBackend',
            'transcribeLang',
            'transcribeWords',
        ]
        self.params['transcribe'] = Param(
            transcribe, valType='bool', inputType='bool', categ='Transcription',
            hint=_translate("Whether to transcribe the audio recording and store the transcription"),
            label=_translate("Transcribe audio")
        )

        # whisper specific params
        whisperParams = [
            'transcribeBackend', 
            'transcribeLang', 
            'transcribeWords', 
            'transcribeWhisperModel',
            'transcribeWhisperDevice'
        ]

        for depParam in whisperParams:
            self.depends.append({
                "dependsOn": "transcribe",
                "condition": "==True",
                "param": depParam,
                "true": "enable",  # what to do with param if condition is True
                "false": "disable",  # permitted: hide, show, enable, disable
            })

        self.params['transcribeBackend'] = Param(
            transcribeBackend, valType='code', inputType='choice', categ='Transcription',
            allowedVals=list(allTranscribers), direct=False,
            hint=_translate("What transcription service to use to transcribe audio?"),
            label=_translate("Transcription backend")
        )

        self.params['transcribeLang'] = Param(
            transcribeLang, valType='str', inputType='single', categ='Transcription',
            hint=_translate("What language you expect the recording to be spoken in, e.g. en-US for English"),
            label=_translate("Transcription language")
        )
        self.depends.append({
            "dependsOn": "transcribeBackend",
            "condition": "=='Google'",
            "param": "transcribeLang",
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        })

        self.params['transcribeWords'] = Param(
            transcribeWords, valType='list', inputType='single', categ='Transcription',
            hint=_translate("Set list of words to listen for - if blank will listen for all words in chosen language. \n\n"
                            "If using the built-in transcriber, you can set a minimum % confidence level using a colon "
                            "after the word, e.g. 'red:100', 'green:80'. Otherwise, default confidence level is 80%."),
            label=_translate("Expected words")
        )
        self.depends.append({
            "dependsOn": "transcribeBackend",
            "condition": "=='Google'",
            "param": "transcribeWords",
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        })

        self.params['transcribeWhisperModel'] = Param(
            transcribeWhisperModel, valType='code', inputType='choice', categ='Transcription',
            allowedVals=["tiny", "base", "small", "medium", "large", "tiny.en", "base.en", "small.en", "medium.en"],
            hint=_translate(
                "Which model of Whisper AI should be used for transcription? Details of each model are available here at github.com/openai/whisper"),
            label=_translate("Whisper model")
        )
        self.depends.append({
            "dependsOn": "transcribeBackend",
            "condition": "=='Whisper'",
            "param": "transcribeWhisperModel",
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        })

        # settings for whisper we might want, we'll need to get these from the
        # plugin itself at some point
        self.params['transcribeWhisperDevice'] = Param(
            transcribeWhisperDevice, valType='code', inputType='choice', 
            categ='Transcription',
            allowedVals=["auto", "gpu", "cpu"],
            hint=_translate(
                "Which device to use for transcription?"),
            label=_translate("Whisper device")
        )
        self.depends.append({
            "dependsOn": "transcribeBackend",
            "condition": "=='Whisper'",
            "param": "transcribeWhisperDevice",
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        })


    def writeDeviceCode(self, buff):
        """
        Code to setup the CameraDevice for this component.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        inits = getInitVals(self.params)

        # --- setup mic ---

        # Substitute default if device not found
        if inits['device'].val not in deviceIndices:
            alert(4330, strFields={'device': self.params['device'].val})
            inits['device'].val = None
        # Substitute sample rate value for numeric equivalent
        inits['sampleRate'] = sampleRates[inits['sampleRate'].val]
        # Substitute channel value for numeric equivalent
        inits['channels'] = {'mono': 1, 'stereo': 2, 'auto': None}[self.params['channels'].val]
        # Get device names
        inits['deviceName'] = getDeviceName(inits['device'].val)
        # initialise mic device
        code = (
            "# initialise microphone\n"
            "if deviceManager.getDevice('%(deviceName)s') is None:\n"
            "    deviceManager.addDevice(\n"
            "        deviceClass='microphone',\n"
            "        deviceName='%(deviceName)s',\n"
            "        index=%(device)s,\n"
            "        channels=%(channels)s, \n"
            "        sampleRateHz=%(sampleRate)s, \n"
            "        maxRecordingSize=%(maxSize)s\n"
            "    )\n"
        )
        buff.writeOnceIndentedLines(code % inits)

    def writeStartCode(self, buff):
        inits = getInitVals(self.params)
        # Use filename with a suffix to store recordings
        code = (
            "# Make folder to store recordings from %(name)s\n"
            "%(name)sRecFolder = filename + '_%(name)s_recorded'\n"
            "if not os.path.isdir(%(name)sRecFolder):\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "os.mkdir(%(name)sRecFolder)\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)

    def writeStartCodeJS(self, buff):
        inits = getInitVals(self.params)
        code = (
            "// Define folder to store recordings from %(name)s"
            "%(name)sRecFolder = filename + '_%(name)s_recorded"
        )
        buff.writeIndentedLines(code % inits)

    def writeRunOnceInitCode(self, buff):
        inits = getInitVals(self.params)
        # check if the user wants to do transcription
        if inits['transcribe'].val:
            code = (
                "# Setup speech-to-text transcriber for audio recordings\n"
                "from psychopy.sound.transcribe import setupTranscriber\n"
                "setupTranscriber(\n"
                "    '%(transcribeBackend)s'")
        
            # handle advanced config options
            if inits['transcribeBackend'].val == 'Whisper':
                code += (
                    ",\n    config={'device': '%(transcribeWhisperDevice)s'})\n")
            else:
                code += (")\n")

            buff.writeOnceIndentedLines(code % inits)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params)
        # Get device names
        inits['deviceName'] = getDeviceName(inits['device'].val)
        # Assign name to device var name
        code = (
            "# link %(name)s to device object\n"
            "%(name)s = sound.microphone.Microphone(device='%(deviceName)s')\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params)
        inits['sampleRate'] = sampleRates[inits['sampleRate'].val]
        # Alert user if non-default value is selected for device
        if inits['device'].val != 'default':
            alert(5055, strFields={'name': inits['name'].val})
        # Write code
        code = (
            "%(name)s = new sound.Microphone({\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "win : psychoJS.window, \n"
                "name:'%(name)s',\n"
                "sampleRateHz : %(sampleRate)s,\n"
                "channels : %(channels)s,\n"
                "maxRecordingSize : %(maxSize)s,\n"
                "loopback : true,\n"
                "policyWhenFull : 'ignore',\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            "});\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        inits = getInitVals(self.params)
        inits['routine'] = self.parentName

        # If stop time is blank, substitute max stop
        if self.params['stopVal'] in ('', None, -1, 'None'):
            self.params['stopVal'].val = at.audioMaxDuration(
                bufferSize=float(self.params['maxSize'].val) * 1000,
                freq=float(sampleRates[self.params['sampleRate'].val])
            )
            # Show alert
            alert(4125, strFields={'name': self.params['name'].val, 'stopVal': self.params['stopVal'].val})

        # Start the recording
        indented = self.writeStartTestCode(buff)
        if indented:
            code = (
                "# start recording with %(name)s\n"
                "%(name)s.start()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # Get clip each frame
        indented = self.writeActiveTestCode(buff)
        code = (
                "# update recorded clip for %(name)s\n"
                "%(name)s.poll()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # Stop recording
        indented = self.writeStopTestCode(buff)
        if indented:
            code = (
                "# stop recording with %(name)s\n"
                "%(name)s.stop()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

    def writeFrameCodeJS(self, buff):
        inits = getInitVals(self.params)
        inits['routine'] = self.parentName
        # Start the recording
        self.writeStartTestCodeJS(buff)
        code = (
                "await %(name)s.start();\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            "}"
        )
        buff.writeIndentedLines(code % inits)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # Stop the recording
            self.writeStopTestCodeJS(buff)
            code = (
                    "%(name)s.pause();\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(-1, relative=True)
            code = (
                "}"
            )
            buff.writeIndentedLines(code % inits)

    def writeRoutineEndCode(self, buff):
        inits = getInitVals(self.params)
        # Alter inits
        if len(self.exp.flow._loopList):
            inits['loop'] = self.exp.flow._loopList[-1].params['name']
            inits['filename'] = f"'recording_{inits['name']}_{inits['loop']}_%s.{inits['outputType']}' % {inits['loop']}.thisTrialN"
        else:
            inits['loop'] = "thisExp"
            inits['filename'] = f"'recording_{inits['name']}'"
        transcribe = inits['transcribe'].val
        if inits['transcribe'].val == False:
            inits['transcribeBackend'].val = None
        if inits['outputType'].val == 'default':
            inits['outputType'].val = 'wav'
        # Warn user if their transcriber won't work locally
        if inits['transcribe'].val:
            if  inits['transcribeBackend'].val in localTranscribers:
                inits['transcribeBackend'].val = localTranscribers[self.params['transcribeBackend'].val]
            else:
                default = list(localTranscribers.values())[0]
                alert(4610, strFields={"transcriber": inits['transcribeBackend'].val, "default": default})
        # Store recordings from this routine
        code = (
            "# tell mic to keep hold of current recording in %(name)s.clips and transcript (if applicable) in %(name)s.scripts\n"
            "# this will also update %(name)s.lastClip and %(name)s.lastScript\n"
            "%(name)s.stop()\n"
        )
        buff.writeIndentedLines(code % inits)
        if inits['transcribeBackend'].val:
            code = (
                "tag = data.utils.getDateStr()\n"
                "%(name)sClip, %(name)sScript = %(name)s.bank(\n"
            )
        else:
            code = (
                "tag = data.utils.getDateStr()\n"
                "%(name)sClip = %(name)s.bank(\n"
            )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
            "tag=tag, transcribe='%(transcribeBackend)s',\n"
        )
        buff.writeIndentedLines(code % inits)
        if transcribe:
            code = (
                "language=%(transcribeLang)s, expectedWords=%(transcribeWords)s\n"
            )
        else:
            code = (
                "config=None\n"
            )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
            "%(loop)s.addData('%(name)s.clip', os.path.join(%(name)sRecFolder, 'recording_%(name)s_%%s.%(outputType)s' %% tag))\n"
        )
        buff.writeIndentedLines(code % inits)
        if transcribe:
            code = (
                "%(loop)s.addData('%(name)s.script', %(name)sScript)\n"
            )
            buff.writeIndentedLines(code % inits)
        if inits['speakTimes'] and inits['transcribeBackend'].val == "whisper":
            code = (
                "# save transcription data\n"
                "with open(os.path.join(%(name)sRecFolder, 'recording_%(name)s_%%s.json' %% tag), 'w') as fp:\n"
                "    fp.write(%(name)sScript.response)\n"
                "# save speaking start/stop times\n"
                "%(name)sWordData = []\n"
                "%(name)sSegments = %(name)s.lastScript.responseData.get('segments', {})\n"
                "for thisSegment in %(name)sSegments.values():\n"
                "    # for each segment...\n"
                "    for thisWord in thisSegment.get('words', {}).values():\n"
                "        # append word data\n"
                "        %(name)sWordData.append(thisWord)\n"
                "# if there were any words, store the start of first & end of last \n"
                "if len(%(name)sWordData):\n"
                "    thisExp.addData('%(name)s.speechStart', %(name)sWordData[0]['start'])\n"
                "    thisExp.addData('%(name)s.speechEnd', %(name)sWordData[-1]['end'])\n"
                "else:\n"
                "    thisExp.addData('%(name)s.speechStart', '')\n"
                "    thisExp.addData('%(name)s.speechEnd', '')\n"
            )
            buff.writeIndentedLines(code % inits)
        # Write base end routine code
        BaseComponent.writeRoutineEndCode(self, buff)

    def writeRoutineEndCodeJS(self, buff):
        inits = getInitVals(self.params)
        inits['routine'] = self.parentName
        if inits['transcribeBackend'].val in allTranscribers:
            inits['transcribeBackend'].val = allTranscribers[self.params['transcribeBackend'].val]
        # Warn user if their transcriber won't work online
        if inits['transcribe'].val and inits['transcribeBackend'].val not in onlineTranscribers.values():
            default = list(onlineTranscribers.values())[0]
            alert(4605, strFields={"transcriber": inits['transcribeBackend'].val, "default": default})

        # Write base end routine code
        BaseComponent.writeRoutineEndCodeJS(self, buff)
        # Store recordings from this routine
        code = (
            "// stop the microphone (make the audio data ready for upload)\n"
            "await %(name)s.stop();\n"
            "// construct a filename for this recording\n"
            "thisFilename = 'recording_%(name)s_' + currentLoop.name + '_' + currentLoop.thisN\n"
            "// get the recording\n"
            "%(name)s.lastClip = await %(name)s.getRecording({\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "tag: thisFilename + '_' + util.MonotonicClock.getDateStr(),\n"
                "flush: false\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            "});\n"
            "psychoJS.experiment.addData('%(name)s.clip', thisFilename);\n"
            "// start the asynchronous upload to the server\n"
            "%(name)s.lastClip.upload();\n"
        )
        buff.writeIndentedLines(code % inits)
        if self.params['transcribe'].val:
            code = (
                "// transcribe the recording\n"
                "const transcription = await %(name)s.lastClip.transcribe({\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(1, relative=True)
            code = (
                    "languageCode: %(transcribeLang)s,\n"
                    "engine: sound.AudioClip.Engine.%(transcribeBackend)s,\n"
                    "wordList: %(transcribeWords)s\n"
            )
            buff.writeIndentedLines(code % inits)
            buff.setIndentLevel(-1, relative=True)
            code = (
                "});\n"
                "%(name)s.lastScript = transcription.transcript;\n"
                "%(name)s.lastConf = transcription.confidence;\n"
                "psychoJS.experiment.addData('%(name)s.transcript', %(name)s.lastScript);\n"
                "psychoJS.experiment.addData('%(name)s.confidence', %(name)s.lastConf);\n"
            )
            buff.writeIndentedLines(code % inits)

    def writeExperimentEndCode(self, buff):
        """Write the code that will be called at the end of
        an experiment (e.g. save log files or reset hardware)
        """
        inits = getInitVals(self.params)
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler
        inits['loop'] = currLoop.params['name']
        if inits['outputType'].val == 'default':
            inits['outputType'].val = 'wav'
        # Save recording
        code = (
            "# save %(name)s recordings\n"
            "for tag in %(name)s.clips:"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                "for i, clip in enumerate(%(name)s.clips[tag]):\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                    "clipFilename = 'recording_%(name)s_%%s.%(outputType)s' %% tag\n"
        )
        buff.writeIndentedLines(code % inits)
        code = (
                    "# if there's more than 1 clip with this tag, append a counter for all beyond the first\n"
                    "if i > 0:\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(1, relative=True)
        code = (
                        "clipFilename += '_%%s' %% i"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
                    "clip.save(os.path.join(%(name)sRecFolder, clipFilename))\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-2, relative=True)


def getDeviceName(index):
    """
    Get device name from a given index

    Parameters
    ----------
    index : int or None
        Index of the device to use
    """
    name = "defaultMicrophone"
    if isinstance(index, str) and index.isnumeric():
        index = int(index)
    for dev in syst.getAudioCaptureDevices():
        if dev['index'] == index:
            name = dev['name']

    return name


def getDeviceVarName(index, case="camel"):
    """
    Get device name from a given index and convert it to a valid variable name.

    Parameters
    ----------
    index : int or None
        Index of the device to use
    case : str
        Format of the variable name (see stringtools.makeValidVarName for info on accepted formats)
    """
    # Get device name
    name = getDeviceName(index)
    # If device name is just default, add "microphone" for clarity
    if name == "default":
        name += "_microphone"
    # Make valid
    varName = st.makeValidVarName(name, case=case)

    return varName
