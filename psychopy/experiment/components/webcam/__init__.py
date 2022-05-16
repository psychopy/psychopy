#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from psychopy.experiment.components import BaseComponent, Param, _translate, getInitVals
from psychopy import prefs

devices = ["default"]


class WebcamComponent(BaseComponent):
    """

    """
    categories = ['Responses']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / 'webcam.png'
    tooltip = _translate('Webcam: Record video from a webcam.')
    beta = True

    def __init__(
            # Basic
            self, exp, parentName,
            name='webcam',
            startType='time (s)', startVal='0', startEstim='',
            stopType='duration (s)', stopVal='', durationEstim='',
            device="Default",
            # Hardware
            resolution="", frameRate="",
            # Data
            saveFile=True,
            outputFileType="mp4", codec="h263",
            saveStartStop=True, syncScreenRefresh=False,
            # Testing
            disabled=False,
    ):
        # Initialise superclass
        super(WebcamComponent, self).__init__(
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
        self.type = 'Webcam'
        # Store exp references
        self.exp = exp
        self.parentName = parentName

        # Basic
        msg = _translate("What webcam device would you like the use to record? This will only affect local "
                         "experiments - online experiments ask the participant which webcam to use.")
        self.params['device'] = Param(
            device, valType='str', inputType="choice", categ="Basic",
            allowedVals=list(devices),
            allowedLabels=[d.title() for d in list(devices)],
            hint=msg,
            label=_translate("Device")
        )

        # Hardware
        msg = _translate("Resolution (w x h) to record to, leave blank to use device default.")
        self.params['resolution'] = Param(
            resolution, valType='list', inputType="single", categ="Hardware",
            hint=msg,
            label=_translate("Resolution")
        )

        msg = _translate("Frame rate (frames per second) to record at, leave blank to use device default.")
        self.params['frameRate'] = Param(
            frameRate, valType='int', inputType="num", categ="Hardware",
            hint=msg,
            label=_translate("Frame Rate")
        )

        # Data
        msg = _translate("Save webcam output to a file?")
        self.params['saveFile'] = Param(
            saveFile, valType='bool', inputType="bool", categ="Data",
            hint=msg,
            label=_translate("Save File?")
        )

        msg = _translate("What kind of video codec should the output file be encoded as?")
        self.params['codec'] = Param(
            codec, valType='str', inputType="choice", categ="Data",
            allowedVals=['a64multi', 'a64multi5', 'alias_pix', 'amv', 'apng', 'asv1', 'asv2', 'avrp', 'avui', 'ayuv', 'bmp', 'cinepak', 'cljr', 'dnxhd', 'dpx', 'dvvideo', 'ffv1', 'ffvhuff', 'fits', 'flashsv', 'flashsv2', 'flv', 'gif', 'h261', 'h263', 'h263_v4l2m2m', 'h263p', 'h264_nvenc', 'h264_omx', 'h264_v4l2m2m', 'h264_vaapi', 'hap', 'hevc_nvenc', 'hevc_v4l2m2m', 'hevc_vaapi', 'huffyuv', 'jpeg2000', 'jpegls', 'libaom-av1', 'libopenjpeg', 'libtheora', 'libvpx', 'libvpx-vp9', 'libwebp', 'libwebp_anim', 'libx264', 'libx264rgb', 'libx265', 'libxvid', 'ljpeg', 'magicyuv', 'mjpeg', 'mjpeg_vaapi', 'mpeg1video', 'mpeg2_vaapi', 'mpeg2video', 'mpeg4', 'mpeg4_v4l2m2m', 'msmpeg4', 'msmpeg4v2', 'msvideo1', 'nvenc', 'nvenc_h264', 'nvenc_hevc', 'pam', 'pbm', 'pcx', 'pgm', 'pgmyuv', 'png', 'ppm', 'prores', 'prores_aw', 'prores_ks', 'qtrle', 'r10k', 'r210', 'rawvideo', 'roqvideo', 'rv10', 'rv20', 'sgi', 'snow', 'sunrast', 'svq1', 'targa', 'tiff', 'utvideo', 'v210', 'v308', 'v408', 'v410', 'vc2', 'vp8_v4l2m2m', 'vp8_vaapi', 'vp9_vaapi', 'wmv1', 'wmv2', 'wrapped_avframe', 'xbm', 'xface', 'xwd', 'y41p', 'yuv4', 'zlib', 'zmbv'],
            hint=msg,
            label=_translate("Output Codec")
        )

        self.depends.append({
            "dependsOn": "saveFile",
            "condition": "==True",
            "param": 'codec',
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        })

        msg = _translate("What file format would you like the video to be saved as?")
        self.params['outputFileType'] = Param(
            outputFileType, valType='code', inputType="choice", categ="Data",
            allowedVals=["mp4", "mov", "mpeg", "mkv"],
            hint=msg,
            label=_translate("Output File Type")
        )

        self.depends.append({
            "dependsOn": "saveFile",
            "condition": "==True",
            "param": 'outputFileType',
            "true": "show",  # what to do with param if condition is True
            "false": "hide",  # permitted: hide, show, enable, disable
        })

    def writeRoutineStartCode(self, buff):
        pass

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

    def writeInitCode(self, buff):
        inits = getInitVals(self.params, "PsychoPy")

        code = (
            "%(name)s = hardware.webcam.Webcam(\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(+1, relative=True)
        code = (
            "win, name=%(name)s,\n"
            "resolution=%(resolution)s, frameRate=%(frameRate)s\n"
        )
        buff.writeIndentedLines(code % inits)
        buff.setIndentLevel(-1, relative=True)
        code = (
            ")\n"
            "%(name)s.initialize()\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeInitCodeJS(self, buff):
        code = (
            "\n"
            "// Unknown component ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        # Start webcam at component start
        self.writeStartTestCode(buff)
        code = (
            "%(name)s.start()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

        # Stop webcam at component stop
        self.writeStopTestCode(buff)
        code = (
            "%(name)s.stop()\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-1, relative=True)

    def writeRoutineEndCode(self, buff):
        code = (
            "# Make sure %(name)s has stopped recording\n"
            "%(name)s.stop()\n"
        )
        buff.writeIndentedLines(code % self.params)
        if self.params['saveFile']:
            code = (
            "# Save %(name)s recording\n"
            "%(name)sFilename = os.path.join(%(name)sRecFolder, 'recording_%(name)s_%%s.%(outputFileType)s' %% data.utils.getDateStr())\n"
            "%(name)s.lastClip.save(%(name)sFilename, codec=%(codec)s)\n"
            "thisExperiment.currentLoop.addData('%(name)s.clip', %(name)sFilename)\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeExperimentEndCode(self, buff):
        pass
