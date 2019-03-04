#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function
from builtins import super  # provides Py3-style super() using python-future

from os import path
from psychopy.experiment.components import BaseVisualComponent, getInitVals, _translate

__author__ = 'Jeremy Gray, Jon Peirce'
# March 2011; builder-component for Yuri Spitsyn's visual.Aperture class
# July 2011: jwp added the code for it to be enabled only when needed

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'aperture.png')
tooltip = _translate('Aperture: restrict the drawing of stimuli to a given '
                     'region')


class ApertureComponent(BaseVisualComponent):
    """An event class for using GL stencil to restrict the viewing area to a
    circle or square of a given size and position"""

    def __init__(self, exp, parentName, name='aperture', units='norm',
                 size=1, pos=(0, 0),
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim=''):
        # initialise main parameters
        super(ApertureComponent, self).__init__(
            exp, parentName, name=name, units=units,
            pos=pos, size=size,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Aperture'
        self.url = "http://www.psychopy.org/builder/components/aperture.html"
        # params:
        # NB make some adjustments on the params defined by _visual component
        self.order = ['name', 'size', 'pos']  # make sure this is at top

        msg = _translate(
            "How big is the aperture? (a single number for diameter)")
        self.params['size'].hint = msg
        # only localize hints and labels
        self.params['size'].label = _translate("Size")
        self.params['pos'].hint = _translate("Where is the aperture centred?")

        # inherited from _visual component but not needed
        del self.params['ori']
        del self.params['color']
        del self.params['colorSpace']
        del self.params['opacity']

    def writeInitCode(self, buff):
        # do we need units code?
        if self.params['units'].val == 'from exp settings':
            unitsStr = ""
        else:
            unitsStr = "units=%(units)s, " % self.params

        # do writing of init
        inits = getInitVals(self.params)

        code = ("%(name)s = visual.Aperture(\n"
                "    win=win, name='%(name)s',\n"
                "    " + unitsStr + "size=%(size)s, pos=%(pos)s)\n"
                "%(name)s.disable()  # disable until its actually used\n")
        buff.writeIndentedLines(code % inits)

    def writeFrameCode(self, buff):
        """Only activate the aperture for the required frames
        """

        buff.writeIndented("\n")
        buff.writeIndented("# *%s* updates\n" % (self.params['name']))
        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        buff.writeIndented("%(name)s.enabled = True\n" % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.enabled = False\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)
        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            code = ("if %(name)s.status == STARTED:  # only update if being  drawn\n")
            buff.writeIndented(code % self.params)

            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdates(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block

    def writeRoutineEndCode(self, buff):
        msg = "%(name)s.enabled = False  # just in case it was left enabled\n"
        buff.writeIndented(msg % self.params)

        # get parent to write code too (e.g. store onset/offset times)
        super().writeRoutineEndCode(buff)
