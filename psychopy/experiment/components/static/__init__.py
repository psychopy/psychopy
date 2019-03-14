#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2018 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, print_function

from builtins import str
from os import path
from psychopy.experiment.components import BaseComponent, Param, _translate

__author__ = 'Jon Peirce'

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'static.png')
tooltip = _translate('Static: Static screen period (e.g. an ISI). '
                     'Useful for pre-loading stimuli.')
_localized = {'Custom code': _translate('Custom code')}


class StaticComponent(BaseComponent):
    """A Static Component, allowing frame rendering to pause.

    E.g., pause while disk is accessed for loading an image
    """
    # override the categories property below
    # an attribute of the class, determines the section in the components panel
    categories = ['Custom']

    def __init__(self, exp, parentName, name='ISI',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=0.5,
                 startEstim='', durationEstim=''):
        BaseComponent.__init__(self, exp, parentName, name=name)
        self.updatesList = []  # a list of dicts {compParams, fieldName}
        self.type = 'Static'
        self.url = "http://www.psychopy.org/builder/components/static.html"
        hnt = _translate(
            "Custom code to be run during the static period (after updates)")
        self.params['code'] = Param("", valType='code',
                                    hint=hnt,
                                    label=_localized['Custom code'])
        self.order = ['name']  # make name come first (others don't matter)

        hnt = _translate("How do you want to define your start point?")
        self.params['startType'] = Param(startType, valType='str',
                                         allowedVals=['time (s)', 'frame N'],
                                         hint=hnt)
        hnt = _translate("How do you want to define your end point?")
        _allow = ['duration (s)', 'duration (frames)', 'time (s)', 'frame N']
        self.params['stopType'] = Param(stopType, valType='str',
                                        allowedVals=_allow,  # copy not needed
                                        hint=hnt)
        hnt = _translate("When does the component start?")
        self.params['startVal'] = Param(startVal, valType='code',
                                        allowedTypes=[],
                                        hint=hnt)
        hnt = _translate("When does the component end? (blank is endless)")
        self.params['stopVal'] = Param(stopVal, valType='code',
                                       allowedTypes=[],
                                       updates='constant', allowedUpdates=[],
                                       hint=hnt)
        hnt = _translate("(Optional) expected start (s), purely for "
                         "representing in the timeline")
        self.params['startEstim'] = Param(startEstim, valType='code',
                                          allowedTypes=[],
                                          hint=hnt)
        hnt = _translate("(Optional) expected duration (s), purely for "
                         "representing in the timeline")
        self.params['durationEstim'] = Param(durationEstim, valType='code',
                                             allowedTypes=[],
                                             hint=hnt)

    def addComponentUpdate(self, routine, compName, fieldName):
        self.updatesList.append({'compName': compName,
                                 'fieldName': fieldName,
                                 'routine': routine})

    def remComponentUpdate(self, routine, compName, fieldName):
        # have to do this in a loop rather than a simple remove
        target = {'compName': compName, 'fieldName': fieldName,
                  'routine': routine}
        for item in self.updatesList:
            if item == target:
                self.updatesList.remove(item)

    def writeInitCode(self, buff):
        code = ("%(name)s = clock.StaticPeriod(win=win, "
                "screenHz=expInfo['frameRate'], name='%(name)s')\n")
        buff.writeIndented(code % self.params)

    def writeFrameCode(self, buff):
        self.writeStartTestCode(buff)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)
        self.writeStopTestCode(buff)

    def writeStartTestCode(self, buff):
        """This will be executed as the final component in the routine
        """
        buff.writeIndented("# *%s* period\n" % (self.params['name']))
        BaseComponent.writeStartTestCode(self, buff)

        if self.params['stopType'].val == 'time (s)':
            durationSecsStr = "%(stopVal)s-t" % (self.params)
        elif self.params['stopType'].val == 'duration (s)':
            durationSecsStr = "%(stopVal)s" % (self.params)
        elif self.params['stopType'].val == 'duration (frames)':
            durationSecsStr = "%(stopVal)s*frameDur" % (self.params)
        elif self.params['stopType'].val == 'frame N':
            durationSecsStr = "(%(stopVal)s-frameN)*frameDur" % (self.params)
        else:
            msg = ("Couldn't deduce end point for startType=%(startType)s, "
                   "stopType=%(stopType)s")
            raise Exception(msg % self.params)
        vals = (self.params['name'], durationSecsStr)
        buff.writeIndented("%s.start(%s)\n" % vals)

    def writeStopTestCode(self, buff):
        """Test whether we need to stop
        """
        code = ("elif %(name)s.status == STARTED:  # one frame should "
                "pass before updating params and completing\n")
        buff.writeIndented(code % self.params)
        buff.setIndentLevel(+1, relative=True)  # entered an if statement
        self.writeParamUpdates(buff)
        code = "%(name)s.complete()  # finish the static period\n"
        buff.writeIndented(code % self.params)
        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # pass  # the clock.StaticPeriod class handles its own stopping

    def writeParamUpdates(self, buff, updateType=None, paramNames=None):
        """Write updates. Unlike most components, which us this method
        to update themselves, the Static Component uses this to update
        *other* components
        """
        if updateType == 'set every repeat':
            return  # the static component doesn't need to change itself
        if len(self.updatesList):
            code = "# updating other components during *%s*\n"
            buff.writeIndented(code % self.params['name'])
            for update in self.updatesList:
                # update = {'compName':compName,'fieldName':fieldName,
                #    'routine':routine}
                compName = update['compName']
                fieldName = update['fieldName']
                routine = self.exp.routines[update['routine']]
                if hasattr(compName, 'params'):
                    prms = compName.params  # it's already a compon so get params
                else:
                    # it's a name so get compon and then get params
                    prms = self.exp.getComponentFromName(str(compName)).params
                self.writeParamUpdate(buff, compName=compName,
                                      paramName=fieldName,
                                      val=prms[fieldName],
                                      updateType=prms[fieldName].updates,
                                      params=prms)
            code = "# component updates done\n"

            # Write custom code
            if self.params['code']:
                code += ("# Adding custom code for {name}\n"
                         "{code}\n".format(name=self.params['name'],
                                           code=self.params['code']))

            buff.writeIndentedLines(code)
