#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools
from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate, getInitVals
from psychopy.experiment import params
from psychopy import prefs

mics = ["default"]


class CameraComponent(BaseComponent):
    """

    """
    categories = ['Responses']
    targets = ["PsychoPy", "PsychoJS"]
    iconFile = Path(__file__).parent / 'webcam.png'
    tooltip = _translate('Webcam: Record video from a webcam.')
    beta = True

    def __init__(
            # Basic
            self, exp, parentName,
            name='cam',
            startType='time (s)', startVal='0', startEstim='',
            stopType='duration (s)', stopVal='', durationEstim='',
            # Basic
            cameraLib="ffpyplayer", device="default", mic="default",
            resolution="default", frameRate="default",
            deviceManual="", resolutionManual="", frameRateManual="",
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
        def fallbackPopulator(*args, **kwargs):
            """
            Fallback in case Camera functions can't be imported. Will return a list with
            a blank string in.
            """
            return ["default"]

        try:
            from psychopy.hardware.camera import getCameras

            def getCameraNames(cameraLib):
                """
                Similar to getCameraDescriptions, only returns camera names
                as a list of strings.

                Parameters
                ----------
                cameraLib : Param
                    Param object containing name of backend library

                Returns
                -------
                list
                    Array of camera device names, preceeded by "default"
                """
                from psychopy.hardware.camera import Camera
                # get all devices
                if isinstance(cameraLib, Param):
                    cameraLib = cameraLib.val
                connectedCameras = Camera.getCameras(cameraLib=cameraLib)

                return ["default"] + list(connectedCameras)

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

                return ["default"] + formats

            def getFrameRatesForDevice(cameraLib, deviceName):
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
                formats = [_format.frameRate for _format in formats]
                # remove duplicates and sort
                formats = list(set(formats))
                formats.sort(reverse=True)

                return ["default"] + formats
        except:
            getCameraNames = fallbackPopulator
            getResolutionsForDevice = fallbackPopulator
            getFrameRatesForDevice = fallbackPopulator

        # Basic
        self.order += [
            'cameraLib',
            'device',
            'deviceManual',
            'resolution',
            'resolutionManual',
            'frameRate',
            'frameRateManual',
            'mic'
        ]

        msg = _translate("Python package to use behind the scenes.")
        self.params['cameraLib'] = Param(
            cameraLib, valType='str', inputType="choice", categ="Basic",
            allowedVals=["ffpyplayer", "opencv"], allowedLabels=["FFPyPlayer", "OpenCV"],
            hint=msg,
            label=_translate("Backend")
        )

        msg = _translate("What device would you like to use to record video? This will only affect local "
                         "experiments - online experiments ask the participant which device to use.")
        conf = functools.partial(getCameraNames, self.params['cameraLib'])
        self.params['device'] = Param(
            device, valType='str', inputType="choice", categ="Basic",
            allowedVals=conf, allowedLabels=conf,
            hint=msg,
            label=_translate("Video Device")
        )
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "",  # meets...
            "param": 'device',  # then...
            "true": "populate",  # should...
            "false": "populate",  # otherwise...
        })
        self.params['deviceManual'] = Param(
            deviceManual, valType='code', inputType="single", categ="Basic",
            hint=msg,
            label=_translate("Video Device")
        )
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "=='opencv'",  # meets...
            "param": 'deviceManual',  # then...
            "true": "show",  # should...
            "false": "hide",  # otherwise...
        })
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "=='opencv'",  # meets...
            "param": 'device',  # then...
            "true": "hide",  # should...
            "false": "show",  # otherwise...
        })

        msg = _translate("What device would you like to use to record audio? This will only affect local "
                         "experiments - online experiments ask the participant which device to use.")
        self.params['mic'] = Param(
            mic, valType='str', inputType="choice", categ="Basic",
            allowedVals=list(range(len(mics))),
            allowedLabels=[d.title() for d in list(mics)],
            hint=msg,
            label=_translate("Audio Device")
        )

        msg = _translate("Resolution (w x h) to record to, leave blank to use device default.")
        conf = functools.partial(getResolutionsForDevice, self.params['cameraLib'], self.params['device'])
        self.params['resolution'] = Param(
            resolution, valType='list', inputType="choice", categ="Basic",
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
            resolutionManual, valType='list', inputType="single", categ="Basic",
            hint=msg,
            label=_translate("Resolution")
        )
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "=='opencv'",  # meets...
            "param": 'resolutionManual',  # then...
            "true": "show",  # should...
            "false": "hide",  # otherwise...
        })
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "=='opencv'",  # meets...
            "param": 'resolution',  # then...
            "true": "hide",  # should...
            "false": "show",  # otherwise...
        })

        msg = _translate("Frame rate (frames per second) to record at, leave blank to use device default.")
        conf = functools.partial(getFrameRatesForDevice, self.params['cameraLib'], self.params['device'])
        self.params['frameRate'] = Param(
            frameRate, valType='int', inputType="choice", categ="Basic",
            allowedVals=conf, allowedLabels=conf,
            hint=msg,
            label=_translate("Frame Rate")
        )
        self.depends.append({
            "dependsOn": 'device',  # if...
            "condition": "",  # meets...
            "param": 'frameRate',  # then...
            "true": "populate",  # should...
            "false": "populate",  # otherwise...
        })
        self.params['frameRateManual'] = Param(
            frameRateManual, valType='int', inputType="single", categ="Basic",
            hint=msg,
            label=_translate("Frame Rate")
        )
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "=='opencv'",  # meets...
            "param": 'frameRateManual',  # then...
            "true": "show",  # should...
            "false": "hide",  # otherwise...
        })
        self.depends.append({
            "dependsOn": 'cameraLib',  # if...
            "condition": "=='opencv'",  # meets...
            "param": 'frameRate',  # then...
            "true": "hide",  # should...
            "false": "show",  # otherwise...
        })

        # Data
        msg = _translate("Save webcam output to a file?")
        self.params['saveFile'] = Param(
            saveFile, valType='bool', inputType="bool", categ="Data",
            hint=msg,
            label=_translate("Save File?")
        )

        # msg = _translate("What kind of video codec should the output file be encoded as?")
        # self.params['codec'] = Param(
        #     codec, valType='str', inputType="choice", categ="Data",
        #     allowedVals=['a64multi', 'a64multi5', 'alias_pix', 'amv', 'apng', 'asv1', 'asv2', 'avrp', 'avui', 'ayuv', 'bmp', 'cinepak', 'cljr', 'dnxhd', 'dpx', 'dvvideo', 'ffv1', 'ffvhuff', 'fits', 'flashsv', 'flashsv2', 'flv', 'gif', 'h261', 'h263', 'h263_v4l2m2m', 'h263p', 'h264_nvenc', 'h264_omx', 'h264_v4l2m2m', 'h264_vaapi', 'hap', 'hevc_nvenc', 'hevc_v4l2m2m', 'hevc_vaapi', 'huffyuv', 'jpeg2000', 'jpegls', 'libaom-av1', 'libopenjpeg', 'libtheora', 'libvpx', 'libvpx-vp9', 'libwebp', 'libwebp_anim', 'libx264', 'libx264rgb', 'libx265', 'libxvid', 'ljpeg', 'magicyuv', 'mjpeg', 'mjpeg_vaapi', 'mpeg1video', 'mpeg2_vaapi', 'mpeg2video', 'mpeg4', 'mpeg4_v4l2m2m', 'msmpeg4', 'msmpeg4v2', 'msvideo1', 'nvenc', 'nvenc_h264', 'nvenc_hevc', 'pam', 'pbm', 'pcx', 'pgm', 'pgmyuv', 'png', 'ppm', 'prores', 'prores_aw', 'prores_ks', 'qtrle', 'r10k', 'r210', 'rawvideo', 'roqvideo', 'rv10', 'rv20', 'sgi', 'snow', 'sunrast', 'svq1', 'targa', 'tiff', 'utvideo', 'v210', 'v308', 'v408', 'v410', 'vc2', 'vp8_v4l2m2m', 'vp8_vaapi', 'vp9_vaapi', 'wmv1', 'wmv2', 'wrapped_avframe', 'xbm', 'xface', 'xwd', 'y41p', 'yuv4', 'zlib', 'zmbv'],
        #     hint=msg,
        #     label=_translate("Output Codec")
        # )
        #
        # self.depends.append({
        #     "dependsOn": "saveFile",
        #     "condition": "==True",
        #     "param": 'codec',
        #     "true": "show",  # what to do with param if condition is True
        #     "false": "hide",  # permitted: hide, show, enable, disable
        # })
        #
        # msg = _translate("What file format would you like the video to be saved as?")
        # self.params['outputFileType'] = Param(
        #     outputFileType, valType='code', inputType="choice", categ="Data",
        #     allowedVals=["mp4", "mov", "mpeg", "mkv"],
        #     hint=msg,
        #     label=_translate("Output File Extension")
        # )
        #
        # self.depends.append({
        #     "dependsOn": "saveFile",
        #     "condition": "==True",
        #     "param": 'outputFileType',
        #     "true": "show",  # what to do with param if condition is True
        #     "false": "hide",  # permitted: hide, show, enable, disable
        # })

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
        # subtitute manual values if backend is opencv
        if self.params['cameraLib'] == "opencv":
            inits['device'] = inits['deviceManual']
            inits['resolution'] = inits['resolutionManual']
            inits['frameRate'] = inits['frameRateManual']

        code = (
            "%(name)s = camera.Camera(\n"
            "    name='%(name)s', \n"
            "    cameraLib=%(cameraLib)s, \n"
            "    device=%(device)s, mic=microphone.Microphone(device=%(mic)s), \n"
            "    frameRate=%(frameRate)s, frameSize=%(resolution)s\n"
            ")\n"
            "# Switch on %(name)s\n"
            "%(name)s.open()\n"
            "\n"
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
