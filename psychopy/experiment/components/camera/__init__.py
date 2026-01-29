#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import functools
from pathlib import Path
from psychopy.alerts import alert
from psychopy import logging
from psychopy.experiment.components import (
    BaseComponent, BaseDeviceComponent, Param, _translate, getInitVals
)
from psychopy.preferences import prefs
from psychopy.experiment.components.microphone import MicrophoneDeviceBackend
from psychopy.experiment.devices import DeviceBackend
from psychopy.tools import stringtools as st, systemtools as syst, audiotools as at


class CameraComponent(BaseDeviceComponent):
    """
    This component provides a way to use the webcam to record participants during an experiment.

    **Note: For online experiments, the browser will notify participants to allow use of webcam before the start of the task.**

    When recording via webcam, specify the starting time relative to the start of the routine (see `start` below) and a stop time (= duration in seconds).
    A blank duration evaluates to recording for 0.000s.

    The resulting video files are saved in .mp4 format if recorded locally and saved in .webm if recorded online. There will be one file per recording. The files appear in a new folder within the data directory in a folder called data_cam_recorded. The file names include the unix (epoch) time of the onset of the recording with milliseconds, e.g., `recording_cam_2022-06-16_14h32.42.064.mp4`.

    **Note: For online experiments, the recordings can only be downloaded from the "Download results" button from the study's Pavlovia page.**
    """

    categories = ['Responses']
    targets = ["PsychoPy", "PsychoJS"]
    version = "2022.2.0"
    iconFile = Path(__file__).parent / 'webcam.png'
    iconSVG = Path(__file__).parent / 'CameraComponent.svg'
    tooltip = _translate('Webcam: Record video from a webcam.')
    beta = False
    deviceClasses = ["psychopy.hardware.camera.CameraDevice"]
    legacyParams = [
        # old device setup params, no longer needed as this is handled by DeviceManager
        "cameraLib",
        "device",
        "deviceManual",
        "frameRate",
        "frameRateManual",
        "mic",
        "micChannels",
        "micMaxRecSize",
        "micSampleRate",
        "resolution",
        "resolutionManual"
    ]

    def __init__(
            # Basic
            self, exp, parentName,
            name='cam',
            startType='time (s)', startVal='0', startEstim='',
            stopType='duration (s)', stopVal='', durationEstim='',
            # Device
            deviceLabel="",
            # audio
            micDeviceLabel="",
            # Data
            saveFile=True,
            saveStartStop=True, syncScreenRefresh=False,
            # Testing
            disabled=False,
            # legacy
            outputFileType="mp4", 
            codec="h263",
            mic=None,
            channels='auto', 
            sampleRate='DVD Audio (48kHz)', 
            maxSize=24000,
            cameraLib="ffpyplayer", 
            device="default", 
            resolution="", 
            frameRate="",
            deviceManual="", 
            resolutionManual="", 
            frameRateManual="",
    ):
        # Initialise superclass
        super(CameraComponent, self).__init__(
            exp, parentName,
            name=name,
            startType=startType, startVal=startVal, startEstim=startEstim,
            stopType=stopType, stopVal=stopVal, durationEstim=durationEstim,
            # Device
            deviceLabel=deviceLabel,
            # Data
            saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
            # Testing
            disabled=disabled,
        )
        # Mark as type
        self.type = 'Camera'
        # Store exp references
        self.exp = exp
        self.parentName = parentName
        # Add requirement
        self.exp.requireImport(importName="camera", importFrom="psychopy.hardware")
        self.exp.requireImport(importName="microphone", importFrom="psychopy.sound")
        
        # --- Audio params ---
        # --- Device params ---
        self.order += [
            "deviceLabel"
        ]
        # label to refer to device by
        self.params['micDeviceLabel'] = Param(
            micDeviceLabel, valType="device", inputType="device", categ="Device",
            allowedVals=[MicrophoneDeviceBackend],
            label=_translate("Microphone device"),
            hint=_translate(
                "The named device from Device Manager to use for this Component."
            )
        )

        # --- Data params ---
        msg = _translate("Save webcam output to a file?")
        self.params['saveFile'] = Param(
            saveFile, valType='bool', inputType="bool", categ="Data",
            hint=msg,
            label=_translate("Save file?")
        )

    @staticmethod
    def setupMicNameInInits(inits):
        # substitute component name + "Microphone" for mic device name if blank
        if not inits['micDeviceLabel']:
            # if deviceName exists but is blank, use component name
            inits['micDeviceLabel'].val = inits['name'].val + "Microphone"
            inits['micDeviceLabel'].valType = 'str'
        # make a code version of mic device name
        inits['micDeviceLabelCode'] = copy.copy(inits['micDeviceLabel'])
        inits['micDeviceLabelCode'].valType = "code"

    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        inits = getInitVals(self.params)
        # Use filename with a suffix to store recordings
        code = (
            "# make folder to store recordings from %(name)s\n"
            "%(name)sRecFolder = filename + '_%(name)s_recorded'\n"
            "if not os.path.isdir(%(name)sRecFolder):\n"
            "    os.mkdir(%(name)sRecFolder)\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")

        # if specified, get camera from device manager
        code = (
            "%(name)s = camera.Camera(\n"
            "    win=win,\n"
            "    device=%(deviceLabel)s,\n"
            "    mic=%(micDeviceLabel)s,\n"
            ")"
        )
        buff.writeIndentedLines(code % inits)
        if self.params['saveFile']:
            code = (
                "# connect camera save method to experiment handler so it's called when data saves\n"
                "thisExp.connectSaveMethod(%(name)s.save, os.path.join(%(name)sRecFolder, '_recovered.mp4'))\n"
            )
            buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        inits = getInitVals(self.params, target="PsychoJS")

        # Write code
        code = (
            "%(name)s = new hardware.Camera({\n"
            "    name:'%(name)s',\n"
            "    win: psychoJS.window,"
            "});\n"
            "// Get permission from participant to access their camera\n"
            "await %(name)s.authorize()\n"
            "// Switch on %(name)s\n"
            "await %(name)s.open()\n"
            "\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        # start webcam at component start
        indented = self.writeStartTestCode(buff)
        if indented:
            code = (
                "# start %(name)s recording\n"
                "%(name)s.record()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # update any params while active
        indented = self.writeActiveTestCode(buff)
        if indented:
            code = (
                "# get current frame data from camera\n"
                "%(name)s.poll()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # stop webcam at component stop
        indented = self.writeStopTestCode(buff)
        if indented:
            code = (
                "# stop %(name)s recording\n"
                "%(name)s.stop()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

    def writeFrameCodeJS(self, buff):
        # Start webcam at component start
        indent = self.writeStartTestCodeJS(buff)
        if indent:
            code = (
                "await %(name)s.record()\n"
            )
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-indent, relative=True)
            code = (
                "};\n"
            )
            buff.writeIndentedLines(code)

        # Stop webcam at component stop
        indent = self.writeStopTestCodeJS(buff)
        if indent:
            code = (
                "await %(name)s.stop()\n"
            )
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-indent, relative=True)
            code = (
                "};\n"
            )
            buff.writeIndentedLines(code)

    def writeRoutineEndCode(self, buff):
        code = (
            "# Make sure %(name)s has stopped recording\n"
            "if %(name)s.status == STARTED:\n"
            "    %(name)s.stop()\n"
        )
        buff.writeIndentedLines(code % self.params)
        if self.params['saveFile']:
            code = (
            "# Save %(name)s recording\n"
            "%(name)sFilename = os.path.join(\n"
            "    %(name)sRecFolder, \n"
            "    'recording_%(name)s_%%s.mp4' %% data.utils.getDateStr()\n"
            ")\n"
            "%(name)s.save(%(name)sFilename)\n"
            "thisExp.currentLoop.addData('%(name)s.clip', %(name)sFilename)\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCodeJS(self, buff):
        code = (
            "// Ensure that %(name)s is stopped\n"
            "if (%(name)s.status === PsychoJS.Status.STARTED) {\n"
            "    await %(name)s.stop()\n"
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
        if self.params['saveFile']:
            code = (
            "// Save %(name)s recording\n"
            "let %(name)sFilename = `recording_%(name)s_${util.MonotonicClock.getDateStr()}`;\n"
            "await %(name)s.save({\n"
            "    tag: %(name)sFilename,\n"
            "    waitForCompletion: true,\n"
            "    showDialog: true,\n"
            "    dialogMsg: \"Please wait a few moments while the video is uploading to the server...\"\n"
            "});\n"
            "psychoJS.experiment.addData('%(name)s.clip', %(name)sFilename);\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeExperimentEndCode(self, buff):
        code = (
            "# Switch off %(name)s\n"
            "%(name)s.close()\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeExperimentEndCodeJS(self, buff):
        code = (
            "// Switch off %(name)s\n"
            "%(name)s.close()\n"
        )
        buff.writeIndentedLines(code % self.params)


class CameraDeviceBackend(DeviceBackend):
    # name of this backend to display in Device Manager
    backendLabel = "Camera"
    # class of the device which this backend corresponds to
    deviceClass = "psychopy.hardware.camera.CameraDevice"
    # icon to show in device manager
    icon = "light/webcam.png"

    def writeDeviceCode(self, buff):
        # write base setup
        self.writeBaseDeviceCode(buff, close=False)
        # add params
        code = (
            "    frameRate=%(frameRate)s,\n"
            "    frameSize=%(frameSize)s\n"
            ")"
        )
        buff.writeIndentedLines(code % self.params)
    
    def getParams(self):
        from psychopy.hardware.camera import CameraDevice

        # get supported resolutions and framerates
        resolutions = set()
        frameRates = set()
        for profile in CameraDevice.getAvailableDevices(best=False):
            if profile['deviceName'] == self.profile['deviceName']:
                resolutions.add(profile['frameSize'])
                frameRates.add(profile['frameRate'])
        
        order = [
            'frameSize',
            'frameRate',
        ]
        params = {}
        
        self.params['frameSize'] = Param(
            "", valType='list', inputType="choice",
            allowedVals=[""] + list(sorted(resolutions)), allowedLabels=["Default"] + list(sorted(resolutions)),
            hint=_translate(
                "Resolution (w x h) to record to, leave blank to use device default."
            ),
            label=_translate("Resolution")
        )
        params['frameRate'] = Param(
            None, valType='int', inputType="choice",
            allowedVals=[""] + list(frameRates), allowedLabels=["Default"] + list(frameRates),
            hint=_translate(
                "Frame rate (frames per second) to record at, leave blank to use device default."
            ),
            label=_translate("Frame rate")
        )

        return params, order


# register backend with Component
CameraComponent.registerBackend(CameraDeviceBackend)


if __name__ == "__main__":
    pass
