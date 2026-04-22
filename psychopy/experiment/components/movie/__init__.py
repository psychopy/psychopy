#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from pathlib import Path
import copy

from psychopy.experiment.components import BaseVisualComponent, getInitVals, Param, _translate


class MovieComponent(BaseVisualComponent):
    """An event class for presenting movie-based stimuli"""

    categories = ['Stimuli']
    targets = ['PsychoPy', 'PsychoJS']
    iconFile = Path(__file__).parent / 'movie.png'
    iconSVG = Path(__file__).parent / 'MovieComponent.svg'
    tooltip = _translate('Movie: play movie files')

    def __init__(self, exp, parentName, name='movie', movie='',
                 units='from exp settings',
                 pos=(0, 0), size=(0.5, 0.5), anchor="center", ori=0,
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 forceEndRoutine=False,
                 loop=False, volume=1, noAudio=False,
                 stopWithRoutine=True
                 ):
        super(MovieComponent, self).__init__(
            exp, parentName, name=name, units=units,
            pos=pos, size=size, ori=ori,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Movie'
        self.url = "https://www.psychopy.org/builder/components/movie.html"
        # comes immediately after name and timing params
        self.order += [
            # Basic tab
            'movie',
            'forceEndRoutine', 
            'loop', 
            'No audio',
        ]

        # params
        self.params['stopVal'].hint = _translate(
            "When does the Component end? (blank to use the duration of "
            "the media)")

        msg = _translate("A filename for the movie (including path)")
        self.params['movie'] = Param(
            movie, valType='file', inputType="file", allowedTypes=[], categ='Basic',
            updates='constant', allowedUpdates=['constant', 'set every repeat'],
            hint=msg,
            label=_translate("Movie file"))

        msg = _translate("Prevent the audio stream from being loaded/processed "
               "(moviepy and opencv only)")
        self.params["No audio"] = Param(
            noAudio, valType='bool', inputType="bool", categ='Playback',
            hint=msg,
            label=_translate("No audio"))

        self.depends.append(
            {"dependsOn": "No audio",  # must be param name
             "condition": "==False",  # val to check for
             "param": "volume",  # param property to alter
             "true": "show",  # what to do with param if condition is True
             "false": "hide",  # permitted: hide, show, enable, disable
             }
        )

        msg = _translate("How loud should audio be played?")
        self.params["volume"] = Param(
            volume, valType='num', inputType="single", categ='Playback',
            hint=msg,
            label=_translate("Volume"))

        msg = _translate("Should the end of the movie cause the end of "
                         "the Routine (e.g. trial)?")
        self.params['forceEndRoutine'] = Param(
            forceEndRoutine, valType='bool', inputType="bool", allowedTypes=[], categ='Basic',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_translate("Force end of Routine"))

        msg = _translate("Whether the movie should loop back to the beginning "
                         "on completion.")
        self.params['loop'] = Param(
            loop, valType='bool', inputType="bool", categ='Playback',
            hint=msg,
            label=_translate("Loop playback"))
        self.params['stopWithRoutine'] = Param(
            stopWithRoutine, valType='bool', inputType="bool", updates='constant', categ='Playback',
            hint=_translate(
                "Should playback cease when the Routine ends? Untick to continue playing "
                "after the Routine has finished."),
            label=_translate('Stop with Routine?'))
        self.params['anchor'] = Param(
            anchor, valType='str', inputType="choice", categ='Layout',
            allowedVals=['center',
                         'top-center',
                         'bottom-center',
                         'center-left',
                         'center-right',
                         'top-left',
                         'top-right',
                         'bottom-left',
                         'bottom-right',
                         ],
            updates='constant',
            hint=_translate("Which point on the stimulus should be anchored to its exact position?"),
            label=_translate("Anchor"))

        # these are normally added but we don't want them for a movie
        del self.params['color']
        del self.params['colorSpace']
        del self.params['fillColor']
        del self.params['borderColor']

    def writeInitCode(self, buff):
        # get init values
        params = getInitVals(self.params)
        params['depth'] = -self.getPosInRoutine()
        # write code
        code = (
            "%(name)s = visual.MovieStim(\n"
            "    win, \n"
            "    name='%(name)s',\n"
            "    filename=%(movie)s,\n"
            "    loop=%(loop)s, \n"
            "    volume=%(volume)s, \n"
            "    noAudio=%(No audio)s,\n"
            "    pos=%(pos)s, \n"
            "    size=%(size)s, \n"
            "    units=%(units)s,\n"
            "    ori=%(ori)s, \n"
            "    anchor=%(anchor)s, \n"
            "    opacity=%(opacity)s, \n"
            "    contrast=%(contrast)s,\n"
            "    depth=%(depth)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code % params)

    def writeInitCodeJS(self, buff):
        # get init values
        inits = getInitVals(self.params)
        inits['depth'] = -self.getPosInRoutine()
        # choose a movie attribute
        if "youtube.com/watch" in str(inits['movie'].val):
            inits['movieAttr'] = "youtubeUrl"
        else:
            inits['movieAttr'] = "movie"
        # create a movie stim
        code = (
            "%(name)sClock = new util.Clock();\n"
            "%(name)s = new visual.MovieStim({\n"
            "  win: psychoJS.window,\n"
            "  %(movieAttr)s: %(movie)s,\n"
            "  name: '%(name)s',\n"
            "  units: %(units)s,\n"
            "  pos: %(pos)s,\n"
            "  anchor: %(anchor)s,\n"
            "  size: %(size)s,\n"
            "  ori: %(ori)s,\n"
            "  opacity: %(opacity)s,\n"
            "  loop: %(loop)s,\n"
            "  noAudio: %(No audio)s,\n"
            "  depth: %(depth)s\n"
            "})\n"
        )
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        # code to run on first active frame
        indented = self.writeStartTestCode(buff)
        if indented:
            code = (
                "%(name)s.setAutoDraw(True)\n"
                "%(name)s.play()\n"
            )
            buff.writeIndentedLines(code % self.params)
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-indented, relative=True)

        # code to run each frame while stimulus is active
        indented = self.writeActiveTestCode(buff)
        if indented:
            pass
        # dedent
        buff.setIndentLevel(-indented, relative=True)

        # write code for stopping
        indented = self.writeStopTestCode(buff, extra=" or %(name)s.isFinished")
        if indented:
            code = (
                "%(name)s.setAutoDraw(False)\n"
            )
            buff.writeIndentedLines(code % self.params)
            # write force end Routine code
            if self.params['forceEndRoutine'].val:
                code = (
                    "continueRoutine = False\n"
                )
                buff.writeIndentedLines(code % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-indented, relative=True)

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame
        """
        buff.writeIndented("\n")
        buff.writeIndented("// *{name}* updates\n".format(**self.params))
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCodeJS(buff)

        buff.writeIndentedLines("{name}.setAutoDraw(true);\n".format(**self.params))
        buff.writeIndentedLines("{name}.play();\n".format(**self.params))
        # because of the 'if' statement of the time test
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("}\n\n")
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCodeJS(buff)
            buff.writeIndentedLines("{name}.setAutoDraw(false);\n".format(**self.params))
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)
            buff.writeIndented("}\n\n")
        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            code = ("if ({name}.status === PsychoJS.Status.STARTED)  {{"
                    "  // only update if being drawn\n").format(**self.params)
            buff.writeIndentedLines(code)

            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdatesJS(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block
            buff.writeIndentedLines("}\n")
        # do force end of trial code
        if self.params['forceEndRoutine'].val is True:
            code = ("if ({name}.status === PsychoJS.Status.FINISHED) {{  // force-end the Routine\n"
                    "    continueRoutine = false;\n"
                    "}}\n".format(**self.params))
            buff.writeIndentedLines(code)

    def writeRoutineEndCode(self, buff):
        if self.params['stopWithRoutine']:
            # stop at the end of the Routine, if requested
            code = (
                "%(name)s.setAutoDraw(False)\n"
                "%(name)s.stop()  # ensure movie has stopped at end of Routine\n"
            )
            buff.writeIndentedLines(code % self.params)

    def writeRoutineEndCodeJS(self, buff):
        if self.params['stopWithRoutine']:
            # stop at the end of the Routine, if requested
            code = (
                "%(name)s.stop();  // ensure movie has stopped at end of Routine\n"
            )
            buff.writeIndentedLines(code % self.params)
