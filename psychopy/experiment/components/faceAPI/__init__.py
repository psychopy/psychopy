from pathlib import Path
from psychopy.localization import _translate
from psychopy.experiment.components import BaseVisualComponent, Param, getInitVals


class FaceAPIComponent(BaseVisualComponent):
    categories = ['Responses']
    targets = ["PsychoJS"]
    plugin = None
    iconFile = Path(__file__).parent / "faceapi.png"
    tooltip = "Use the Face API JS library to get face and emotion data from a Camera Component"
    version = "2024.2.0"
    beta = True

    def __init__(
            self, exp, parentName,
            # basic
            name='face',
            startType='time (s)',
            startVal='0',
            stopType='duration (s)',
            stopVal='',
            startEstim='',
            durationEstim='',
            camera="",
            # layout
            pos=(0, 0),
            size=(0, 0),
            ori=0,
            units='from exp settings',
            # appearance
            opacity="",
            # data
            saveStartStop=True,
            syncScreenRefresh=False,
            # testing
            validator="",
            disabled=False
    ):
        BaseVisualComponent.__init__(
            self, exp, parentName,
            # basic
            name=name,
            startType=startType,
            startVal=startVal,
            stopType=stopType,
            stopVal=stopVal,
            startEstim=startEstim,
            durationEstim=durationEstim,
            # layout
            pos=pos,
            size=size,
            ori=ori,
            units=units,
            # appearance
            opacity=opacity,
            # data
            saveStartStop=saveStartStop,
            syncScreenRefresh=syncScreenRefresh,
            # testing
            disabled=disabled
        )
        # delete unused params
        del self.params['validator']
        del self.params['color']
        del self.params['fillColor']
        del self.params['borderColor']
        del self.params['contrast']
        del self.params['colorSpace']

        # require face api lib
        self.exp.requireOnlineResource(
            "https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js",
            name="face-api.js"
        )

        # --- Basic params ---
        self.order += [
            "camera"
        ]

        self.params['camera'] = Param(
            camera, valType="code", inputType="single", categ="Basic",
            label=_translate("Camera"),
            hint=_translate("Camera Component whose footage to detect faces with.")
        )

    def writeInitCodeJS(self, buff):
        # get initial values for params
        inits = getInitVals(self.params, target="PsychoJS")
        # create face detector
        code = (
            "%(name)s = new visual.FaceDetector({\n"
            "    win: psychoJS.window,\n"
            "    name: '%(name)s',\n"
            "    faceApiUrl: 'face-api.js',\n"
            "    modelDir: 'https://pavlovia.org/assets/face-api-models',\n"
            "    units: %(units)s,\n"
            "    pos: %(pos)s,\n"
            "    size: %(size)s,\n"
            "    ori: %(ori)s,\n"
            "    opacity: %(opacity)s,\n"
            "});\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeRoutineStartCodeJS(self, buff):
        # define detection types
        detections = (
            "happy",
            "sad",
            "neutral",
            "angry",
            "disgusted",
            "surprised",
            "fearful",
        )
        # populate data fields
        code = (
            "%(name)s.landmarks = [];\n"
            "%(name)s.detections = {\n"
        )
        for attr in detections:
            code += (
            "    '%s': [],\n"
            ) % attr
        code += (
            "};\n"
        )
        buff.writeIndentedLines(code % self.params)
        # set input
        code = (
            "// set the input as the video/webcam stream\n"
            "%(name)s.setInput(%(camera)s);\n"
        )
        buff.writeIndentedLines(code % self.params)
        # function to log detections
        code = (
            "// start logging the expression detections when they are available\n"
            "%(name)s.start(100, async (detections) => {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(+1, relative=True)
        code = (
            "if (typeof detections[0] !== 'undefined') {\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(+1, relative=True)
        code = (
            "// store landmarks\n"
            "%(name)s.landmarks = detections[0].landmarks.positions.map( \n"
            "    (point) => [Math.round(point._x), Math.round(point._y)] \n"
            ");\n"
            "//extract detection of each emotion\n"
        )
        buff.writeIndentedLines(code % self.params)
        # write extraction code
        for attr in detections:
            code = (
                f"%(name)s.detections['{attr}'].push(\n"
                f"    detections[0]['expressions'].{attr}\n"
                f");\n"
            )
            buff.writeIndentedLines(code % self.params)
        # exit if statement
        buff.setIndentLevel(-1, relative=True)
        code = (
            "}\n"
        )
        buff.writeIndentedLines(code % self.params)
        # exit function def
        buff.setIndentLevel(-1, relative=True)
        code = (
            "});\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeFrameCodeJS(self, buff):
        # code to execute on first frame Component is active
        indent = self.writeStartTestCodeJS(buff)
        if indent:
            code = (
                "%(name)s.setAutoDraw(true);\n"
            )
            buff.writeIndentedLines(code % self.params)
            # to get out of the if statement
            while indent > 0:
                buff.setIndentLevel(-1, relative=True)
                buff.writeIndentedLines(
                    "}\n"
                    "\n"
                )
                indent -= 1

        # code to execute on every frame Component is active
        indent = self.writeActiveTestCodeJS(buff)
        if indent:
            # to get out of the if statement
            while indent > 0:
                buff.setIndentLevel(-1, relative=True)
                buff.writeIndentedLines(
                    "}\n"
                    "\n"
                )
                indent -= 1

        # code to execute on last frame Component is active
        indent = self.writeStopTestCodeJS(buff)
        if indent:
            code = (
                "%(name)s.setAutoDraw(false);\n"
            )
            buff.writeIndentedLines(code % self.params)
            # to get out of the if statement
            while indent > 0:
                buff.setIndentLevel(-1, relative=True)
                buff.writeIndentedLines(
                    "}\n"
                    "\n"
                )
                indent -= 1

    def writeRoutineEndCodeJS(self, buff):
        # define detection types
        detections = (
            "happy",
            "sad",
            "neutral",
            "angry",
            "disgusted",
            "surprised",
            "fearful",
        )
        # stop face detector
        code = (
            "// stop the face detector"
            "%(name)s.stop();"
        )
        buff.writeIndentedLines(code % self.params)
        # save data
        code = (
            "psychoJS.experiment.addData('%(name)s.landmarks', %(name)s.landmarks);\n"
        )
        buff.writeIndentedLines(code % self.params)
        for attr in detections:
            code = (
                f"psychoJS.experiment.addData(\n"
                f"    '%(name)s.detections.{attr}', %(name)s.detections['{attr}']\n"
                f");\n"
            )
            buff.writeIndentedLines(code % self.params)
