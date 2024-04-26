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
from psychopy.sound.audiodevice import sampleRateQualityLevels
from psychopy.tools import stringtools as st, systemtools as syst, audiotools as at


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
# Get list of sample rates
micSampleRates = {r[1]: r[0] for r in sampleRateQualityLevels.values()}


class CameraComponent(BaseDeviceComponent):
    categories = ['Responses']
    targets = ["PsychoPy", "PsychoJS"]
    version = "2022.2.0"
    iconFile = Path(__file__).parent / 'webcam.png'
    tooltip = _translate('Webcam: Record video from a webcam.')
    beta = True
    deviceClasses = ["psychopy.hardware.camera.Camera"]

    def __init__(
            # Basic
            self, exp, parentName,
            name='cam',
            startType='time (s)', startVal='0', startEstim='',
            stopType='duration (s)', stopVal='', durationEstim='',
            # Device
            deviceLabel="",
            cameraLib="ffpyplayer", 
            device="default", 
            resolution="", 
            frameRate="",
            deviceManual="", 
            resolutionManual="", 
            frameRateManual="",
            # audio
            micDeviceLabel="",
            mic=None,
            channels='auto', 
            sampleRate='DVD Audio (48kHz)', 
            maxSize=24000,
            # Data
            saveFile=True,
            outputFileType="mp4", codec="h263",
            saveStartStop=True, syncScreenRefresh=False,
            # Testing
            disabled=False,
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

        # Define some functions for live populating listCtrls
        def getResolutionsForDevice(cameraLib, deviceName):
            """
                Get a list of resolutions available for the given device.

                Parameters
                ----------
                cameraLib : Param
                    Param object containing name of backend library
                deviceName : Param
                    Param object containing device name/index

                Returns
                -------
                list
                    List of resolutions, specified as strings in the format `(width, height)`
                """
            if cameraLib == "opencv":
                return [""]
            try:
                from psychopy.hardware.camera import Camera
                # get all devices
                if isinstance(cameraLib, Param):
                    cameraLib = cameraLib.val
                connectedCameras = Camera.getCameras(cameraLib=cameraLib)
                # if device is a param, get its val
                if isinstance(deviceName, Param):
                    deviceName = deviceName.val
                # get first device if default
                if deviceName in (None, "", "default") and len(connectedCameras):
                    deviceName = list(connectedCameras)[0]
                # get formats for this device
                formats = connectedCameras.get(deviceName, [])
                # extract resolutions
                formats = [_format.frameSize for _format in formats]
                # remove duplicates and sort
                formats = list(set(formats))
                formats.sort(key=lambda res: res[0], reverse=True)

                return [""] + formats
            except:
                return [""]

        def getFrameRatesForDevice(cameraLib, deviceName, resolution=None):
            """
                Get a list of frame rates available for the given device.

                Parameters
                ----------
                cameraLib : Param
                    Param object containing name of backend library
                deviceName : Param
                    Param object containing device name/index

                Returns
                -------
                list
                    List of frame rates
                """
            if cameraLib == "opencv":
                return [""]
            try:
                from psychopy.hardware.camera import Camera
                # get all devices
                if isinstance(cameraLib, Param):
                    cameraLib = cameraLib.val
                connectedCameras = Camera.getCameras(cameraLib=cameraLib)
                # if device is a param, get its val
                if isinstance(deviceName, Param):
                    deviceName = deviceName.val
                # get first device if default
                if deviceName in (None, "", "default") and len(connectedCameras):
                    deviceName = list(connectedCameras)[0]
                # get formats for this device
                formats = connectedCameras.get(deviceName, [])
                # if frameRate is a param, get its val
                if isinstance(resolution, Param):
                    resolution = resolution.val
                # filter for current frame rate
                if resolution not in (None, "", "default"):
                    formats = [f for f in formats if f.frameSize == resolution]
                # extract resolutions
                formats = [_format.frameRate for _format in formats]
                # remove duplicates and sort
                formats = list(set(formats))
                formats.sort(reverse=True)

                return [""] + formats
            except:
                return [""]

        # --- Device params ---
        self.order += [
            "cameraLib",
            "device",
            "deviceManual",
            "resolution",
            "resolutionManual",
            "frameRate",
            "frameRateManual",
        ]
        self.params['cameraLib'] = Param(
            cameraLib, valType='str', inputType="choice", categ="Device",
            allowedVals=["ffpyplayer", "opencv"], allowedLabels=["FFPyPlayer", "OpenCV"],
            hint=_translate("Python package to use behind the scenes."),
            label=_translate("Backend")
        )
        msg = _translate(
                "What device would you like to use to record video? This will only affect local "
                "experiments - online experiments ask the participant which device to use."
            )

        def getCameraNames():
            """
            Similar to getCameraDescriptions, only returns camera names
            as a list of strings.

            Returns
            -------
            list
                Array of camera device names, preceeded by "default"
            """
            if self.params['cameraLib'] == "opencv":
                return ["default"]
            # enter a try statement in case ffpyplayer isn't installed
            try:
                # import
                from psychopy.hardware.camera import Camera
                connectedCameras = Camera.getCameras(cameraLib=self.params['cameraLib'].val)

                return ["default"] + list(connectedCameras)
            except:
                return ["default"]

        self.params['device'] = Param(
            device, valType='str', inputType="choice", categ="Device",
            allowedVals=getCameraNames, allowedLabels=getCameraNames,
            hint=msg,
            label=_translate("Video device")
        )
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "",  # meets...
            "param": 'device',  # then...
            "true": "populate",  # should...
            "false": "populate",  # otherwise...
        })
        self.params['deviceManual'] = Param(
            deviceManual, valType='code', inputType="single", categ="Device",
            hint=msg,
            label=_translate("Video device")
        )
        msg = _translate("Resolution (w x h) to record to, leave blank to use device default.")
        conf = functools.partial(getResolutionsForDevice, self.params['cameraLib'], self.params['device'])
        self.params['resolution'] = Param(
            resolution, valType='list', inputType="choice", categ="Device",
            allowedVals=conf, allowedLabels=conf,
            hint=msg,
            label=_translate("Resolution")
        )
        self.depends.append({
            "dependsOn": 'device',  # if...
            "condition": "",  # meets...
            "param": 'resolution',  # then...
            "true": "populate",  # should...
            "false": "populate",  # otherwise...
        })
        self.params['resolutionManual'] = Param(
            resolutionManual, valType='list', inputType="single", categ="Device",
            hint=msg,
            label=_translate("Resolution")
        )
        msg = _translate("Frame rate (frames per second) to record at, leave "
                         "blank to use device default.")
        conf = functools.partial(
            getFrameRatesForDevice, 
            self.params['cameraLib'], 
            self.params['device'], 
            self.params['resolution'])
        self.params['frameRate'] = Param(
            frameRate, valType='int', inputType="choice", categ="Device",
            allowedVals=conf, allowedLabels=conf,
            hint=msg,
            label=_translate("Frame rate")
        )
        self.depends.append({
            "dependsOn": 'device',  # if...
            "condition": "",  # meets...
            "param": 'frameRate',  # then...
            "true": "populate",  # should...
            "false": "populate",  # otherwise...
        })

        msg += _translate(
            " For some cameras, you may need to use "
            "`camera.CAMERA_FRAMERATE_NTSC` or "
            "`camera.CAMERA_FRAMERATE_NTSC / 2`.")
        self.params['frameRateManual'] = Param(
            frameRateManual, valType='int', inputType="single", categ="Device",
            hint=msg,
            label=_translate("Frame rate")
        )

        # add dependencies for manual spec under open cv
        for param in ("device", "resolution", "frameRate"):
            # hide the choice ctrl
            self.depends.append({
                "dependsOn": 'cameraLib',  # if...
                "condition": "=='opencv'",  # meets...
                "param": param,  # then...
                "true": "hide",  # should...
                "false": "show",  # otherwise...
            })
            # show to manual ctrl
            self.depends.append({
                "dependsOn": 'cameraLib',  # if...
                "condition": "=='opencv'",  # meets...
                "param": param + "Manual",  # then...
                "true": "show",  # should...
                "false": "hide",  # otherwise...
            })

        # --- Audio params ---
        self.order += [
            "micDeviceLabel",
            "mic",
            "micChannels",
            "micSampleRate",
            "micMaxRecSize"
        ]
        self.params['micDeviceLabel'] = Param(
            micDeviceLabel, valType="str", inputType="single", categ="Audio",
            label=_translate("Microphone device label"),
            hint=_translate(
                "A label to refer to this Component's associated microphone device by. If using "
                "the same device for multiple components, be sure to use the same label here."
            )
        )

        def getMicDeviceIndices():
            from psychopy.hardware.microphone import MicrophoneDevice
            profiles = MicrophoneDevice.getAvailableDevices()

            return [None] + [profile['index'] for profile in profiles]

        def getMicDeviceNames():
            from psychopy.hardware.microphone import MicrophoneDevice
            profiles = MicrophoneDevice.getAvailableDevices()

            return ["default"] + [profile['deviceName'] for profile in profiles]

        msg = _translate(
            "What microphone device would you like the use to record? This "
            "will only affect local experiments - online experiments ask the "
            "participant which mic to use.")
        self.params['mic'] = Param(
            mic, valType='str', inputType="choice", categ="Audio",
            allowedVals=getMicDeviceIndices,
            allowedLabels=getMicDeviceNames,
            hint=msg,
            label=_translate("Microphone")
        )
        msg = _translate(
            "Record two channels (stereo) or one (mono, smaller file). Select "
            "'auto' to use as many channels as the selected device allows.")
        
        self.params['micChannels'] = Param(
            channels, valType='str', inputType="choice", categ='Audio',
            allowedVals=['auto', 'mono', 'stereo'],
            hint=msg,
            label=_translate("Channels"))

        msg = _translate(
            "How many samples per second (Hz) to record at")
        self.params['micSampleRate'] = Param(
            sampleRate, valType='num', inputType="choice", categ='Audio',
            allowedVals=list(micSampleRates),
            hint=msg, direct=False,
            label=_translate("Sample rate (hz)"))

        msg = _translate(
            "To avoid excessively large output files, what is the biggest file "
            "size you are likely to expect?")
        self.params['micMaxRecSize'] = Param(
            maxSize, valType='num', inputType="single", categ='Audio',
            hint=msg,
            label=_translate("Max recording size (kb)"))

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

    def writeDeviceCode(self, buff):
        """
        Code to setup the CameraDevice for this component.

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        """
        inits = getInitVals(self.params)
        self.setupMicNameInInits(inits)
        # --- setup mic ---
        # substitute sample rate value for numeric equivalent
        inits['micSampleRate'] = micSampleRates[inits['micSampleRate'].val]
        # substitute channel value for numeric equivalent
        inits['micChannels'] = {'mono': 1, 'stereo': 2, 'auto': None}[self.params['micChannels'].val]
        # initialise mic device
        code = (
            "# initialise microphone\n"
            "deviceManager.addDevice(\n"
            "    deviceClass='psychopy.hardware.microphone.MicrophoneDevice',\n"
            "    deviceName=%(micDeviceLabel)s,\n"
            "    index=%(mic)s,\n"
            "    channels=%(micChannels)s, \n"
            "    sampleRateHz=%(micSampleRate)s, \n"
            "    maxRecordingSize=%(micMaxRecSize)s\n"
            ")\n"
        )
        buff.writeOnceIndentedLines(code % inits)

        # --- setup camera ---
        # initialise camera device
        code = (
            "# initialise camera\n"
            "cam = deviceManager.addDevice(\n"
            "    deviceClass='psychopy.hardware.camera.Camera',\n"
            "    deviceName=%(deviceLabel)s,\n"
            "    cameraLib=%(cameraLib)s, \n"
            "    device=%(device)s, \n"
            "    mic=%(micDeviceLabel)s, \n"
            "    frameRate=%(frameRate)s, \n"
            "    frameSize=%(resolution)s\n"
            ")\n"
            "cam.open()\n"
            "\n"
        )
        buff.writeOnceIndentedLines(code % inits)

    def writeRoutineStartCode(self, buff):
        pass

    def writeStartCode(self, buff):
        inits = getInitVals(self.params)
        # Use filename with a suffix to store recordings
        code = (
            "# Make folder to store recordings from %(name)s\n"
            "%(name)sRecFolder = filename + '_%(name)s_recorded'\n"
            "if not os.path.isdir(%(name)sRecFolder):\n"
            "    os.mkdir(%(name)sRecFolder)\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")

        # Create Microphone object
        code = (
            "# get camera object\n"
            "%(name)s = deviceManager.getDevice(%(deviceLabel)s)\n"
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
        # Start webcam at component start
        indented = self.writeStartTestCode(buff)
        if indented:
            code = (
                "# Start %(name)s recording\n"
                "%(name)s.record()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

        # Update any params while active
        indented = self.writeActiveTestCode(buff)
        buff.setIndentLevel(-indented, relative=True)

        # Stop webcam at component stop
        indented = self.writeStopTestCode(buff)
        if indented:
            code = (
                "# Stop %(name)s recording\n"
                "%(name)s.stop()\n"
            )
            buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-indented, relative=True)

    def writeFrameCodeJS(self, buff):
        # Start webcam at component start
        self.writeStartTestCodeJS(buff)
        code = (
            "await %(name)s.record()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
        code = (
            "};\n"
        )
        buff.writeIndentedLines(code)

        # Stop webcam at component stop
        self.writeStopTestCodeJS(buff)
        code = (
            "await %(name)s.stop()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)
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
            "%(name)s.save(%(name)sFilename, encoderLib='ffpyplayer')\n"
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


if __name__ == "__main__":
    pass
