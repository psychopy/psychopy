#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Part of the PsychoPy library
Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
Distributed under the terms of the GNU General Public License (GPL).
"""
import copy
import textwrap
from pathlib import Path
from xml.etree.ElementTree import Element

from psychopy import prefs
from psychopy.constants import FOREVER
from ..params import Param
from psychopy.experiment.utils import canBeNumeric
from psychopy.experiment.utils import CodeGenerationException
from psychopy.experiment.utils import unescapedDollarSign_re
from psychopy.experiment.params import getCodeFromParamStr
from psychopy.alerts import alerttools
from psychopy.colors import nonAlphaSpaces

from psychopy.localization import _translate


class BaseComponent:
    """A template for components, defining the methods to be overridden"""
    # override the categories property below
    # an attribute of the class, determines the section in the components panel

    categories = ['Custom']
    targets = []
    plugin = None
    iconFile = Path(__file__).parent / "unknown" / "unknown.png"
    tooltip = ""
    # what version was this Component added in?
    version = "0.0.0"
    # is it still in beta?
    beta = False

    def __init__(self, exp, parentName, name='',
                 startType='time (s)', startVal='',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=False,
                 disabled=False):
        self.type = type(self).__name__
        self.exp = exp  # so we can access the experiment if necess
        self.parentName = parentName  # to access the routine too if needed

        self.params = {}
        self.depends = []  # allows params to turn each other off/on
        """{
         "dependsOn": "shape",
         "condition": "=='n vertices",
         "param": "n vertices",
         "true": "enable",  # what to do with param if condition is True
         "false": "disable",  # permitted: hide, show, enable, disable
         }"""
        self.order = ['name', 'startVal', 'startEstim', 'startType', 'stopVal', 'durationEstim', 'stopType']  # name first, then timing, then others

        msg = _translate(
            "Name of this Component (alphanumeric or _, no spaces)")
        self.params['name'] = Param(name,
            valType='code', inputType="single", categ='Basic',
            hint=msg,
            label=_translate("Name"))

        msg = _translate("How do you want to define your start point?")
        self.params['startType'] = Param(startType,
            valType='str', inputType="choice", categ='Basic',
            allowedVals=['time (s)', 'frame N', 'condition'],
            hint=msg, direct=False,
            label=_translate("Start type"))

        msg = _translate("How do you want to define your end point?")
        self.params['stopType'] = Param(stopType,
            valType='str', inputType="choice", categ='Basic',
            allowedVals=['duration (s)', 'duration (frames)', 'time (s)',
                         'frame N', 'condition'],
            hint=msg, direct=False,
            label=_translate("Stop type"))

        self.params['startVal'] = Param(startVal,
            valType='code', inputType="single", categ='Basic',
            hint=_translate("When does the Component start?"), allowedTypes=[],
            label=_translate("Start"))

        self.params['stopVal'] = Param(stopVal,
            valType='code', inputType="single", categ='Basic',
            updates='constant', allowedUpdates=[], allowedTypes=[],
            hint=_translate("When does the Component end? (blank is endless)"),
            label=_translate("Stop"))

        msg = _translate("(Optional) expected start (s), purely for "
                         "representing in the timeline")
        self.params['startEstim'] = Param(startEstim,
            valType='code', inputType="single", categ='Basic',
            hint=msg, allowedTypes=[], direct=False,
            label=_translate("Expected start (s)"))

        msg = _translate("(Optional) expected duration (s), purely for "
                         "representing in the timeline")
        self.params['durationEstim'] = Param(durationEstim,
            valType='code', inputType="single", categ='Basic',
            hint=msg, allowedTypes=[], direct=False,
            label=_translate("Expected duration (s)"))

        msg = _translate("Store the onset/offset times in the data file "
                         "(as well as in the log file).")
        self.params['saveStartStop'] = Param(saveStartStop,
            valType='bool', inputType="bool", categ='Data',
            hint=msg, allowedTypes=[],
            label=_translate('Save onset/offset times'))

        msg = _translate("Synchronize times with screen refresh (good for "
                         "visual stimuli and responses based on them)")
        self.params['syncScreenRefresh'] = Param(syncScreenRefresh,
            valType='bool', inputType="bool", categ="Data",
            hint=msg, allowedTypes=[],
            label=_translate('Sync timing with screen refresh'))

        msg = _translate("Disable this Component")
        self.params['disabled'] = Param(disabled,
            valType='bool', inputType="bool", categ="Testing",
            hint=msg, allowedTypes=[], direct=False,
            label=_translate('Disable Component'))

    @property
    def _xml(self):
        return self.makeXmlNode(self.__class__.__name__)

    def makeXmlNode(self, tag):
        # Make root element
        element = Element(tag)
        element.set("name", self.params['name'].val)
        element.set("plugin", str(self.plugin))
        # Add an element for each parameter
        for key, param in sorted(self.params.items()):
            # Create node
            paramNode = param._xml
            paramNode.set("name", key)
            # Add node
            element.append(paramNode)

        return element

    def __repr__(self):
        _rep = "psychopy.experiment.components.%s(name='%s', exp=%s)"
        return _rep % (self.__class__.__name__, self.name, self.exp)

    def copy(self, exp=None, parentName=None, name=None):
        # Alias None with current attributes
        if exp is None:
            exp = self.exp
        if parentName is None:
            parentName = self.parentName
        if name is None:
            name = self.name
        # Create new component of same class with bare minimum inputs
        newCompon = type(self)(exp=exp, parentName=parentName, name=name)
        # Add params
        for name, param in self.params.items():
            # Don't copy name
            if name == "name":
                continue
            # Copy other params
            newCompon.params[name] = copy.deepcopy(param)

        return newCompon

    def hideParam(self, name):
        """
        Set a param to always be hidden.

        Parameters
        ==========
        name : str
            Name of the param to hide
        """
        # Add to depends, but have it depend on itself and be hidden either way
        self.depends.append(
            {
                "dependsOn": name,  # if...
                "condition": "",  # meets...
                "param": name,  # then...
                "true": "hide",  # should...
                "false": "hide",  # otherwise...
            }
        )

    def integrityCheck(self):
        """
        Run component integrity checks for non-visual components
        """
        alerttools.testDisabled(self)
        alerttools.testStartEndTiming(self)

    def _dubiousConstantUpdates(self):
        """Return a list of fields in component that are set to be constant
        but seem intended to be dynamic. Some code fields are constant, and
        some denoted as code by $ are constant.
        """
        warnings = []
        # treat expInfo as likely to be constant; also treat its keys as
        # constant because its handy to make a short-cut in code:
        # exec(key+'=expInfo[key]')
        expInfo = self.exp.settings.getInfo()
        keywords = self.exp.namespace.nonUserBuilder[:]
        keywords.extend(['expInfo'] + list(expInfo.keys()))
        reserved = set(keywords).difference({'random', 'rand'})
        for key in self.params:
            field = self.params[key]
            if (not hasattr(field, 'val') or
                    not isinstance(field.val, str)):
                continue  # continue == no problem, no warning
            if not (field.allowedUpdates and
                    isinstance(field.allowedUpdates, list) and
                    len(field.allowedUpdates) and
                    field.updates == 'constant'):
                continue
            # now have only non-empty, possibly-code, and 'constant' updating
            if field.valType == 'str':
                if not bool(unescapedDollarSign_re.search(field.val)):
                    continue
                code = getCodeFromParamStr(field.val)
            elif field.valType == 'code':
                code = field.val
            else:
                continue
            # get var names in the code; no names == constant
            try:
                names = compile(code, '', 'eval').co_names
            except SyntaxError:
                continue
            # ignore reserved words:
            if not set(names).difference(reserved):
                continue
            warnings.append((field, key))
        return warnings or [(None, None)]

    def writeInitCode(self, buff):
        """Write any code that a component needs that should only ever be done
        at start of an experiment, BEFORE window creation.
        """
        pass

    def writeStartCode(self, buff):
        """Write any code that a component needs that should only ever be done
        at start of an experiment, AFTER window creation.
        """
        # e.g., create a data subdirectory unique to that component type.
        # Note: settings.writeStartCode() is done first, then
        # Routine.writeStartCode() will call this method for each component in
        # each routine
        pass

    def writePreCode(self, buff):
        """Write any code that a component needs that should be done before 
        the session's `run` method is called.
        """
        pass

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        pass

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the beginning of
        a routine (e.g. to update stimulus parameters)
        """
        self.writeParamUpdates(buff, 'set every repeat')

    def writeRoutineStartCodeJS(self, buff):
        """Same as writeRoutineStartCode, but for JS
        """
        self.writeParamUpdatesJS(buff, 'set every repeat')

    def writeRoutineEndCode(self, buff):
        """Write the code that will be called at the end of
        a routine (e.g. to save data)
        """
        if 'saveStartStop' in self.params and self.params['saveStartStop'].val:

            # what loop are we in (or thisExp)?
            if len(self.exp.flow._loopList):
                currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
            else:
                currLoop = self.exp._expHandler

            if 'Stair' in currLoop.type and buff.target == 'PsychoPy':
                addDataFunc = 'addOtherData'
            elif 'Stair' in currLoop.type and buff.target == 'PsychoJS':
                addDataFunc = 'psychojs.experiment.addData'
            else:
                addDataFunc = 'addData'

            loop = currLoop.params['name']
            name = self.params['name']

            # NOTE: this function does not write any code right now!

    def writeRoutineEndCodeJS(self, buff):
        """Write the code that will be called at the end of
        a routine (e.g. to save data)
        """
        pass

    def writeExperimentEndCode(self, buff):
        """Write the code that will be called at the end of
        an experiment (e.g. save log files or reset hardware)
        """
        pass

    def writeStartTestCode(self, buff, extra=""):
        """
        Test whether we need to start (if there is a start time at all)

        Returns True if start test was written, False if it was skipped. Recommended usage:
        ```
        indented = self.writeStartTestCode(buff)
        if indented:
            code = (
                "%(name)s.attribute = value\n"
            )
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(-indented, relative=True)
        ```

        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        extra : str
            Additional conditions to check, including any boolean operators (and, or, etc.). Use 
            `%(key)s` syntax to insert the values of any necessary params. Default is an empty 
            string.
        """
        # create copy of params dict so we can change stuff without harm
        params = self.params.copy()

        # Get starting indent level
        startIndent = buff.indentLevel

        if params['startVal'].val in ('', None, -1, 'None'):
            if extra:
                # if we have extra and no stop condition, extra is the only stop condition
                params['startType'] = params['startType'].copy()
                params['startVal'] = params['startVal'].copy()
                params['startType'].val = "condition"
                params['startVal'].val = "False"
            else:
                # if we just have no stop time, don't write stop code
                return buff.indentLevel - startIndent

        # Newline
        buff.writeIndentedLines("\n")

        if params['syncScreenRefresh']:
            tCompare = 'tThisFlip'
        else:
            tCompare = 't'
        t = tCompare
        # add handy comment
        code = (
            "# if %(name)s is starting this frame...\n"
        )
        buff.writeIndentedLines(code % params)
        # add starting if statement
        if params['startType'].val == 'time (s)':
            # if startVal is an empty string then set to be 0.0
            if (
                isinstance(params['startVal'].val, str) 
                and not params['startVal'].val.strip()
            ):
                params['startVal'].val = '0.0'
            code = (
                "if %(name)s.status == NOT_STARTED and {} >= %(startVal)s-frameTolerance"
            ).format(t)
        elif params['startType'].val == 'frame N':
            code = (
                "if %(name)s.status == NOT_STARTED and frameN >= %(startVal)s"
            )
        elif params['startType'].val == 'condition':
            code = (
                "if %(name)s.status == NOT_STARTED and %(startVal)s"
            )
        else:
            msg = f"Not a known startType (%(startVal)s) for %(name)s"
            raise CodeGenerationException(msg % params)
        # add any other conditions and finish the statement
        if extra and not extra.startswith(" "):
            extra = " " + extra
        code += f"{extra}:\n"
        # write if statement and indent
        buff.writeIndentedLines(code % params)
        buff.setIndentLevel(+1, relative=True)

        params = params
        code = (f"# keep track of start time/frame for later\n"
                f"{params['name']}.frameNStart = frameN  # exact frame index\n"
                f"{params['name']}.tStart = t  # local t and not account for scr refresh\n"
                f"{params['name']}.tStartRefresh = tThisFlipGlobal  # on global time\n"
                )
        if self.type != "Sound":
            # for sounds, don't update to actual frame time because it will start
            # on the *expected* time of the flip
            code += (f"win.timeOnFlip({params['name']}, 'tStartRefresh')"
                     f"  # time at next scr refresh\n")
        if params['saveStartStop']:
            code += f"# add timestamp to datafile\n"
            if self.type=='Sound' and params['syncScreenRefresh']:
                # use the time we *expect* the flip
                code += f"thisExp.addData('{params['name']}.started', tThisFlipGlobal)\n"
            elif 'syncScreenRefresh' in params and params['syncScreenRefresh']:
                # use the time we *detect* the flip (in the future)
                code += f"thisExp.timestampOnFlip(win, '{params['name']}.started')\n"
            else:
                # use the time ignoring any flips
                code += f"thisExp.addData('{params['name']}.started', t)\n"
        buff.writeIndentedLines(code)
        # validate presentation time
        validator = self.getValidator()
        if validator:
            # queue validation
            code = (
                "# tell attached validator (%(name)s) to start looking for a start flag\n"
                "%(name)s.status = STARTED\n"
            )
            buff.writeIndentedLines(code % validator.params)
        # Set status
        code = (
            "# update status\n"
            "%(name)s.status = STARTED\n"
        )
        buff.writeIndentedLines(code % params)

        # Return True if start test was written
        return buff.indentLevel - startIndent

    def writeStartTestCodeJS(self, buff, extra=""):
        """Test whether we need to start
                           
        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        extra : str
            Additional conditions to check, including any boolean operators (and, or, etc.). Use 
            `%(key)s` syntax to insert the values of any necessary params. Default is an empty 
            string.
        """
        # create copy of params dict so we can change stuff without harm
        params = self.params.copy()

        # Get starting indent level
        startIndent = buff.indentLevel

        if params['startVal'].val in ('', None, -1, 'None'):
            if extra:
                # if we have extra and no stop condition, extra is the only stop condition
                params['startType'] = params['startType'].copy()
                params['startVal'] = params['startVal'].copy()
                params['startType'].val = "condition"
                params['startVal'].val = "False"
            else:
                # if we just have no stop time, don't write stop code
                return buff.indentLevel - startIndent

        if params['startType'].val == 'time (s)':
            # if startVal is an empty string then set to be 0.0
            if (
                isinstance(params['startVal'].val, str) 
                and not params['startVal'].val.strip()
            ):
                params['startVal'].val = '0.0'
            code = (
                "if (t >= %(startVal)s && %(name)s.status === PsychoJS.Status.NOT_STARTED"
            )
        elif params['startType'].val == 'frame N':
            code = (
                "if (frameN >= %(startVal)s && %(name)s.status === PsychoJS.Status.NOT_STARTED"
            )
        elif params['startType'].val == 'condition':
            code = (
                "if ((%(startVal)s) && %(name)s.status === PsychoJS.Status.NOT_STARTED"
            )
        else:
            msg = f"Not a known startType (%(startVal)s) for %(name)s"
            raise CodeGenerationException(msg)
        # add any other conditions and finish the statement
        if extra and not extra.startswith(" "):
            extra = " " + extra
        code += f"{extra}) {{\n"
        # write if statement and indent
        buff.writeIndentedLines(code % params)
        buff.setIndentLevel(+1, relative=True)

        code = (f"// keep track of start time/frame for later\n"
                f"{params['name']}.tStart = t;  // (not accounting for frame time here)\n"
                f"{params['name']}.frameNStart = frameN;  // exact frame index\n\n")
        buff.writeIndentedLines(code)

        # Return True if start test was written
        return buff.indentLevel - startIndent

    def writeStopTestCode(self, buff, extra=""):
        """
        Test whether we need to stop (if there is a stop time at all)

        Returns True if stop test was written, False if it was skipped. Recommended usage:
        ```
        indented = self.writeStopTestCode(buff)
        if indented:
            code = (
                "%(name)s.attribute = value\n"
            )
            buff.writeIndentedLines(code % params)
            buff.setIndentLevel(-indented, relative=True)
        ```
             
        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        extra : str
            Additional conditions to check, including any boolean operators (and, or, etc.). Use 
            `%(key)s` syntax to insert the values of any necessary params. Default is an empty 
            string.
        """
        # create copy of params dict so we can change stuff without harm
        params = self.params.copy()

        # Get starting indent level
        startIndent = buff.indentLevel

        if params['stopVal'].val in ('', None, -1, 'None'):
            if extra:
                # if we have extra and no stop condition, extra is the only stop condition
                params['stopType'] = params['stopType'].copy()
                params['stopVal'] = params['stopVal'].copy()
                params['stopType'].val = "condition"
                params['stopVal'].val = "False"
            else:
                # if we just have no stop time, don't write stop code
                return buff.indentLevel - startIndent

        # Newline
        buff.writeIndentedLines("\n")

        # add handy comment
        code = (
            "# if %(name)s is stopping this frame...\n"
        )
        buff.writeIndentedLines(code % params)

        buff.writeIndentedLines(f"if {params['name']}.status == STARTED:\n")
        buff.setIndentLevel(+1, relative=True)

        # If start time is blank ad stop is a duration, raise alert
        if params['stopType'] in ('duration (s)', 'duration (frames)'):
            if ('startVal' not in params) or (params['startVal'] in ("", "None", None)):
                alerttools.alert(4120, strFields={'component': params['name']})

        if params['stopType'].val == 'time (s)':
            code = (
                "# is it time to stop? (based on local clock)\n"
                "if tThisFlip > %(stopVal)s-frameTolerance"
            )
        # duration in time (s)
        elif (params['stopType'].val == 'duration (s)'):
            code = (
                "# is it time to stop? (based on global clock, using actual start)\n"
                "if tThisFlipGlobal > %(name)s.tStartRefresh + %(stopVal)s-frameTolerance"
            )
        elif params['stopType'].val == 'duration (frames)':
            code = (
                "if frameN >= (%(name)s.frameNStart + %(stopVal)s)"
            )
        elif params['stopType'].val == 'frame N':
            code = (
                "if frameN >= %(stopVal)s"
            )
        elif params['stopType'].val == 'condition':
            code = (
                "if bool(%(stopVal)s)"
            )
        else:
            msg = (
                "Didn't write any stop line for startType=%(startType)s, stopType=%(stopType)s"
            )
            raise CodeGenerationException(msg)
        # add any other conditions and finish the statement
        if extra and not extra.startswith(" "):
            extra = " " + extra
        code += f"{extra}:\n"
        # write if statement and indent
        buff.writeIndentedLines(code % params)
        buff.setIndentLevel(+1, relative=True)

        code = (f"# keep track of stop time/frame for later\n"
                f"{params['name']}.tStop = t  # not accounting for scr refresh\n"
                f"{params['name']}.tStopRefresh = tThisFlipGlobal  # on global time\n"
                f"{params['name']}.frameNStop = frameN  # exact frame index\n"
                )
        if params['saveStartStop']:
            code += f"# add timestamp to datafile\n"
            if 'syncScreenRefresh' in params and params['syncScreenRefresh']:
                # use the time we *detect* the flip (in the future)
                code += f"thisExp.timestampOnFlip(win, '{params['name']}.stopped')\n"
            else:
                # use the time ignoring any flips
                code += f"thisExp.addData('{params['name']}.stopped', t)\n"
        buff.writeIndentedLines(code)

        # validate presentation time
        validator = self.getValidator()
        if validator:
            # queue validation
            code = (
                "# tell attached validator (%(name)s) to start looking for a start flag\n"
                "%(name)s.status = STARTED\n"
            )
            buff.writeIndentedLines(code % validator.params)

        # Set status
        code = (
            "# update status\n"
            "%(name)s.status = FINISHED\n"
        )
        buff.writeIndentedLines(code % params)

        # Return True if stop test was written
        return buff.indentLevel - startIndent

    def writeStopTestCodeJS(self, buff, extra=""):
        """Test whether we need to stop
                           
        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        extra : str
            Additional conditions to check, including any boolean operators (and, or, etc.). Use 
            `%(key)s` syntax to insert the values of any necessary params. Default is an empty 
            string.
        """
        # create copy of params dict so we can change stuff without harm
        params = self.params.copy()

        # Get starting indent level
        startIndent = buff.indentLevel

        if params['stopVal'].val in ('', None, -1, 'None'):
            if extra:
                # if we have extra and no stop time, extra is only stop condition
                params['stopType'] = params['stopType'].copy()
                params['stopVal'] = params['stopVal'].copy()
                params['stopType'].val = "condition"
                params['stopVal'].val = "false"
            else:
                # if we just have no stop time, don't write stop code
                return buff.indentLevel - startIndent

        if params['stopType'].val == 'time (s)':
            code = (
                "frameRemains = %(stopVal)s - psychoJS.window.monitorFramePeriod * 0.75;"
                "// most of one frame period left\n"
                "if ((%(name)s.status === PsychoJS.Status.STARTED || %(name)s.status === "
                "PsychoJS.Status.FINISHED) && t >= frameRemains"
            )
        # duration in time (s)
        elif (
            params['stopType'].val == 'duration (s)'
            and params['startType'].val == 'time (s)'
        ):
            code = (
                "frameRemains = %(startVal)s + %(stopVal)s - psychoJS.window.monitorFramePeriod "
                "* 0.75;"
                "// most of one frame period left\n"
                "if (%(name)s.status === PsychoJS.Status.STARTED && t >= frameRemains"
            )
        # start at frame and end with duratio (need to use approximate)
        elif params['stopType'].val == 'duration (s)':
            code = (
                "if (%(name)s.status === PsychoJS.Status.STARTED && t >= (%(name)s.tStart + "
                "%(stopVal)s)"
            )
        elif params['stopType'].val == 'duration (frames)':
            code = (
                "if (%(name)s.status === PsychoJS.Status.STARTED && frameN >= "
                "(%(name)s.frameNStart + %(stopVal)s)"
            )
        elif params['stopType'].val == 'frame N':
            code = (
                "if (%(name)s.status === PsychoJS.Status.STARTED && frameN >= %(stopVal)s"
            )
        elif params['stopType'].val == 'condition':
            code = (
                "if (%(name)s.status === PsychoJS.Status.STARTED && Boolean(%(stopVal)s)"
            )
        else:
            msg = (
                "Didn't write any stop line for startType=%(startType)s, stopType=%(stopType)s"
            )
            raise CodeGenerationException(msg)
        # add any other conditions and finish the statement
        if extra and not extra.startswith(" "):
            extra = " " + extra
        code += f"{extra}) {{\n"
        # write if statement and indent
        buff.writeIndentedLines(code % params)
        buff.setIndentLevel(+1, relative=True)

        # Return True if stop test was written
        return buff.indentLevel - startIndent

    def writeActiveTestCode(self, buff, extra=""):
        """
        Test whether component is started and has not finished.

        Recommended usage:
        ```
        self.writeActiveTestCode(buff):
        code = (
            "%(name)s.attribute = value\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)
        self.exitActiveTest(buff)
        ```
           
        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        extra : str
            Additional conditions to check, including any boolean operators (and, or, etc.). Use 
            `%(key)s` syntax to insert the values of any necessary params. Default is an empty 
            string.
        """
        # create copy of params dict so we can change stuff without harm
        params = self.params.copy()

        # Newline
        buff.writeIndentedLines("\n")
        # Get starting indent level
        startIndent = buff.indentLevel

        # construct if statement
        code = (
            "# if %(name)s is active this frame...\n"
            "if %(name)s.status == STARTED"
        )
        # add any other conditions and finish the statement
        if extra and not extra.startswith(" "):
            extra = " " + extra
        code += f"{extra}:\n"
        buff.writeIndentedLines(code % params)
        # Indent
        buff.setIndentLevel(+1, relative=True)
        # Write param updates (if needed)
        code = (
            "# update params\n"
        )
        buff.writeIndentedLines(code % params)
        if self.checkNeedToUpdate('set every frame'):
            self.writeParamUpdates(buff, 'set every frame')
        else:
            code = (
                "pass\n"
            )
            buff.writeIndentedLines(code)
        return buff.indentLevel - startIndent

    def writeActiveTestCodeJS(self, buff, extra=""):
        """
        Test whether component is started and has not finished.

        Recommended usage:
        ```
        self.writeActiveTestCodeJS(self, buff):
        code = (
            "%(name)s.attribute = value\n"
            "\n"
        )
        self.exitActiveTestJS(buff)
        ```
                   
        Parameters
        ----------
        buff : io.StringIO
            Text buffer to write code to.
        extra : str
            Additional conditions to check, including any boolean operators (and, or, etc.). Use 
            `%(key)s` syntax to insert the values of any necessary params. Default is an empty 
            string.
        """
        # create copy of params dict so we can change stuff without harm
        params = self.params.copy()

        # Get starting indent level
        startIndent = buff.indentLevel

        # Newline
        buff.writeIndentedLines("\n")

        # construct if statement
        code = (
            "// if %(name)s is active this frame...\n"
            "if (%(name)s.status == STARTED"
        )
        # add any other conditions and finish the statement
        if extra and not extra.startswith(" "):
            extra = " " + extra
        code += f"{extra}) {{\n"
        # write if statement and indent
        buff.writeIndentedLines(code % params)
        buff.setIndentLevel(+1, relative=True)

        if self.checkNeedToUpdate('set every frame'):
            # Write param updates (if needed)
            code = (
                "// update params\n"
            )
            buff.writeIndentedLines(code % params)
            self.writeParamUpdates(buff, 'set every frame')

        return buff.indentLevel - startIndent

    def writeParamUpdates(self, buff, updateType, paramNames=None,
                          target="PsychoPy"):
        """write updates to the buffer for each parameter that needs it
        updateType can be 'experiment', 'routine' or 'frame'
        """
        if paramNames is None:
            paramNames = list(self.params.keys())
        for thisParamName in paramNames:
            if thisParamName == 'advancedParams':
                continue  # advancedParams is not really a parameter itself
            thisParam = self.params[thisParamName]
            if thisParam.updates == updateType:
                self.writeParamUpdate(
                    buff, self.params['name'],
                    thisParamName, thisParam, thisParam.updates,
                    target=target)

    def writeParamUpdatesJS(self, buff, updateType, paramNames=None):
        """Pass this to the standard writeParamUpdates but with new 'target'
        """
        self.writeParamUpdates(buff, updateType, paramNames,
                               target="PsychoJS")

    def _getParamCaps(self, paramName):
        """
        Get param name in title case, useful for working out the `.set____` function in boilerplate.
        """
        if paramName == 'advancedParams':
            return  # advancedParams is not really a parameter itself
        elif paramName == 'image' and self.getType() == 'PatchComponent':
            paramCaps = 'Tex'  # setTex for PatchStim
        elif paramName == 'sf':
            paramCaps = 'SF'  # setSF, not SetSf
        elif paramName == 'coherence':
            paramCaps = 'FieldCoherence'
        else:
            paramCaps = paramName[0].capitalize() + paramName[1:]

        return paramCaps

    def writeParamUpdate(self, buff, compName, paramName, val, updateType,
                         params=None, target="PsychoPy"):
        """Writes an update string for a single parameter.
        This should not need overriding for different components - try to keep
        constant
        """
        if params is None:
            params = self.params
        # first work out the name for the set____() function call
        paramCaps = self._getParamCaps(paramName)

        # code conversions for PsychoJS
        if target == 'PsychoJS':
            endStr = ';'
            try:
                valStr = str(val).strip()
            except TypeError:
                if isinstance(val, Param):
                    val = val.val
                raise TypeError(f"Value of parameter {paramName} of component {compName} "
                                f"could not be converted to JS. Value is {val}")
            # convert (0,0.5) to [0,0.5] but don't convert "rand()" to "rand[]"
            if valStr.startswith("(") and valStr.endswith(")"):
                valStr = valStr.replace("(", "[", 1)
                valStr = valStr[::-1].replace(")", "]", 1)[
                         ::-1]  # replace from right
            # filenames (e.g. for image) need to be loaded from resources
            if paramName in ["sound"]:
                valStr = (f"psychoJS.resourceManager.getResource({valStr})")
        else:
            endStr = ''

        # then write the line
        if updateType == 'set every frame' and target == 'PsychoPy':
            loggingStr = ', log=False'
        elif updateType == 'set every frame' and target == 'PsychoJS':
            loggingStr = ', false'  # don't give the keyword 'log' in JS
        else:
            loggingStr = ''

        if target == 'PsychoPy':
            if paramName == 'color':
                buff.writeIndented(f"{compName}.setColor({params['color']}, colorSpace={params['colorSpace']}")
                buff.write(f"{loggingStr}){endStr}\n")
            elif paramName == 'sound':
                stopVal = params['stopVal'].val
                if stopVal in ['', None, -1, 'None']:
                    stopVal = '-1'
                buff.writeIndented(f"{compName}.setSound({params['sound']}, secs={stopVal}){endStr}\n")
            elif paramName == 'movie' and params['backend'].val in ('moviepy', 'avbin', 'vlc', 'opencv'):
                # we're going to do this for now ...
                if params['units'].val == 'from exp settings':
                    unitsStr = "units=''"
                else:
                    unitsStr = "units=%(units)s" % params

                if params['backend'].val == 'moviepy':
                    code = ("%s = visual.MovieStim3(\n" % params['name'] +
                            "    win=win, name='%s', %s,\n" % (
                                params['name'], unitsStr) +
                            "    noAudio = %(No audio)s,\n" % params)
                elif params['backend'].val == 'avbin':
                    code = ("%s = visual.MovieStim(\n" % params['name'] +
                            "    win=win, name='%s', %s,\n" % (
                                params['name'], unitsStr))
                elif params['backend'].val == 'vlc':
                    code = ("%s = visual.VlcMovieStim(\n" % params['name'] +
                            "    win=win, name='%s', %s,\n" % (
                                params['name'], unitsStr))
                else:
                    code = ("%s = visual.MovieStim(\n" % params['name'] +
                            "    win=win, name='%s', %s,\n" % (
                                params['name'], unitsStr) +
                            "    noAudio=%(No audio)s,\n" % params)

                code += ("    filename=%(movie)s,\n"
                         "    ori=%(ori)s, pos=%(pos)s, opacity=%(opacity)s,\n"
                         "    loop=%(loop)s, anchor=%(anchor)s,\n"
                         % params)

                buff.writeIndentedLines(code)

                if params['size'].val != '':
                    buff.writeIndented("    size=%(size)s,\n" % params)

                depth = -self.getPosInRoutine()
                code = ("    depth=%.1f,\n"
                        "    )\n")
                buff.writeIndentedLines(code % depth)

            else:
                buff.writeIndented(f"{compName}.set{paramCaps}({val}{loggingStr}){endStr}\n")
        elif target == 'PsychoJS':
            # write the line
            if paramName == 'color':
                buff.writeIndented(f"{compName}.setColor(new util.Color({params['color']})")
                buff.write(f"{loggingStr}){endStr}\n")
            elif paramName == 'fillColor':
                buff.writeIndented(f"{compName}.setFillColor(new util.Color({params['fillColor']})")
                buff.write(f"{loggingStr}){endStr}\n")
            elif paramName == 'lineColor':
                buff.writeIndented(f"{compName}.setLineColor(new util.Color({params['lineColor']})")
                buff.write(f"{loggingStr}){endStr}\n")
            elif paramName == 'emotiv_marker_label' or paramName == "emotiv_marker_value" or paramName == "emotiv_stop_marker":
                # This allows the eeg_marker to be updated by a code component or a conditions file
                # There is no setMarker_label or setMarker_value function in the eeg_marker object
                # The marker label and value are set by the variables set in the dialogue
                pass
            else:
                buff.writeIndented(f"{compName}.set{paramCaps}({val}{loggingStr}){endStr}\n")

    def checkNeedToUpdate(self, updateType):
        """Determine whether this component has any parameters set to repeat
        at this level

        usage::
            True/False = checkNeedToUpdate(self, updateType)

        """
        for thisParamName in self.params:
            if thisParamName == 'advancedParams':
                continue
            thisParam = self.params[thisParamName]
            if thisParam.updates == updateType:
                return True

        return False

    def getStart(self):
        # deduce a start time (s) if possible
        startType = self.params['startType'].val
        numericStart = canBeNumeric(self.params['startVal'].val)

        if canBeNumeric(self.params['startEstim'].val):
            startTime = float(self.params['startEstim'].val)
        elif startType == 'time (s)' and numericStart:
            startTime = float(self.params['startVal'].val)
        else:
            startTime = None

        return startTime, numericStart

    def getDuration(self, startTime=0):
        # deduce stop time (s) if possible
        stopType = self.params['stopType'].val
        numericStop = canBeNumeric(self.params['stopVal'].val)

        if stopType == 'time (s)' and numericStop:
            duration = float(self.params['stopVal'].val) - (startTime or 0)
        elif stopType == 'duration (s)' and numericStop:
            duration = float(self.params['stopVal'].val)
        else:
            # deduce duration (s) if possible. Duration used because component
            # time icon needs width
            if canBeNumeric(self.params['durationEstim'].val):
                duration = float(self.params['durationEstim'].val)
            elif self.params['stopVal'].val in ['', '-1', 'None']:
                duration = FOREVER  # infinite duration
            else:
                duration = None

        return duration, numericStop

    def getStartAndDuration(self, params=None):
        """Determine the start and duration of the stimulus
        purely for Routine rendering purposes in the app (does not affect
        actual drawing during the experiment)

        start, duration, nonSlipSafe = component.getStartAndDuration()

        nonSlipSafe indicates that the component's duration is a known fixed
        value and can be used in non-slip global clock timing (e.g for fMRI)

        Parameters
        ----------
        params : dict[Param]
            Dict of params to use. If None, will use the values in `self.params`.
        """
        # if not given any params, use from self
        if params is None:
            params = self.params

        # If has a start, calculate it
        if 'startType' in self.params:
            startTime, numericStart = self.getStart()
        else:
            startTime, numericStart = None, False

        # If has a stop, calculate it
        if 'stopType' in self.params:
            duration, numericStop = self.getDuration(startTime=startTime)
        else:
            duration, numericStop = 0, False

        nonSlipSafe = numericStop and (numericStart or self.params['stopType'].val == 'time (s)')
        return startTime, duration, nonSlipSafe

    def getPosInRoutine(self):
        """Find the index (position) in the parent Routine (0 for top)
        """
        # get Routine
        routine = self.exp.routines[self.parentName]
        # make list of non-settings components in Routine
        comps = [comp for comp in routine if not comp == routine.settings]
        # get index
        return comps.index(self)

    def getType(self):
        """Returns the name of the current object class"""
        return self.__class__.__name__

    def getShortType(self):
        """Replaces word component with empty string"""
        return self.getType().replace('Component', '')

    def getAllValidatorRoutines(self, attr="vals"):
        """
        Return a list of names for all validator Routines in the current experiment. Used to populate
        allowedVals in the `validator` param.

        Parameters
        ----------
        attr : str
            Attribute to get - either values (for allowedVals) or labels (for allowedLabels)

        Returns
        -------
        list[str]
            List of Routine names/labels
        """
        from psychopy.experiment.routines import BaseValidatorRoutine

        # iterate through all Routines in this Experiment
        names = [""]
        labels = [_translate("Do not validate")]
        for rtName, rt in self.exp.routines.items():
            # if Routine is a validator, include it
            if isinstance(rt, BaseValidatorRoutine):
                # add name
                names.append(rtName)
                # construct label
                rtType = type(rt).__name__
                labels.append(
                    f"{rtName} ({rtType})"
                )

        if attr == "labels":
            return labels
        else:
            return names

    def getAllValidatorRoutineVals(self):
        """
        Shorthand for calling getAllValidatorRoutines with `attr` as "vals"
        """
        return self.getAllValidatorRoutines(attr="vals")

    def getAllValidatorRoutineLabels(self):
        """
        Shorthand for calling getAllValidatorRoutines with `attr` as "labels"
        """
        return self.getAllValidatorRoutines(attr="labels")

    def getValidator(self):
        """
        Get the validator associated with this Component.

        Returns
        -------
        BaseStandaloneRoutine or None
            Validator Routine object
        """
        # return None if we have no such param
        if "validator" not in self.params:
            return None
        # return None if no validator is selected
        if self.params['validator'].val in ("", None, "None", "none"):
            return None
        # strip spaces from param
        name = self.params['validator'].val.strip()
        # look for Components matching validator name
        for rt in self.exp.routines.values():
            for comp in rt:
                if comp.name == name:
                    return comp

    def writeRoutineStartValidationCode(self, buff):
        """
        WWrite Routine start code to validate this stimulus against the specified validator.

        Parameters
        ----------
        buff : StringIO
            String buffer to write code to.
        """
        # get validator
        validator = self.getValidator()
        # if there is no validator, don't write any code
        if validator is None:
            return
        # if there is a validator, write its code
        indent = validator.writeRoutineStartValidationCode(buff, stim=self)
        # if validation code indented the buffer, dedent
        buff.setIndentLevel(-indent, relative=True)

    def writeEachFrameValidationCode(self, buff):
        """
        Write each frame code to validate this stimulus against the specified validator.

        Parameters
        ----------
        buff : StringIO
            String buffer to write code to.
        """
        # get validator
        validator = self.getValidator()
        # if there is no validator, don't write any code
        if validator is None:
            return
        # if there is a validator, write its code
        indent = validator.writeEachFrameValidationCode(buff, stim=self)
        # if validation code indented the buffer, dedent
        buff.setIndentLevel(-indent, relative=True)

    def getFullDocumentation(self, fmt="rst"):
        """
        Automatically generate documentation for this Component. We recommend using this as a
        starting point, but checking the documentation yourself afterwards and adding any more
        detail you'd like to include (e.g. usage examples)

        Parameters
        ----------
        fmt : str
            Format to write documentation in. One of:
            - "rst": Restructured text (numpy style)
            -"md": Markdown (mkdocs style)
        """

        # make sure format is correct
        assert fmt in ("md", "rst"), (
            f"Unrecognised format {fmt}, allowed formats are 'md' and 'rst'."
        )
        # define templates for md and rst
        h1 = {
            'md': "# %s",
            'rst': (
                "-------------------------------\n"
                "%s\n"
                "-------------------------------"
            )
        }[fmt]
        h2 = {
            'md': "## %s",
            'rst': (
                "%s\n"
                "-------------------------------"
            )
        }[fmt]
        h3 = {
            'md': "### %s",
            'rst': (
                "%s\n"
                "==============================="
            )
        }[fmt]
        h4 = {
            'md': "#### `%s`",
            'rst': "%s"
        }[fmt]

        # start off with nothing
        content = ""
        # header and class docstring
        content += (
            f"{h1 % type(self).__name__}\n"
            f"{textwrap.dedent(self.__doc__ or '')}\n"
            f"\n"
        )
        # attributes
        content += (
            f"{h4 % 'Categories:'}\n"
            f"    {', '.join(self.categories)}\n"
            f"{h4 % 'Works in:'}\n"
            f"    {', '.join(self.targets)}\n"
            f"\n"
        )
        # beta warning
        if self.beta:
            content += (
                f"**Note: Since this is still in beta, keep an eye out for bug fixes.**\n"
                f"\n"
            )
        # params heading
        content += (
            f"{h2 % 'Parameters'}\n"
            f"\n"
        )
        # sort params by category
        byCateg = {}
        for param in self.params.values():
            if param.categ not in byCateg:
                byCateg[param.categ] = []
            byCateg[param.categ].append(param)
        # iterate through categs
        for categ, params in byCateg.items():
            # write a heading for each categ
            content += (
                f"{h3 % categ}\n"
                f"\n"
            )
            # add each param...
            for param in params:
                # write basics (heading and description)
                content += (
                    f"{h4 % param.label}\n"
                    f"    {param.hint}\n"
                )
                # if there are options, display them
                if bool(param.allowedVals) or bool(param.allowedLabels):
                    # if no allowed labels, use allowed vals
                    options = param.allowedLabels or param.allowedVals
                    # handle callable methods
                    if callable(options):
                        content += (
                            f"\n"
                            f"    Options are generated live, so will vary according to your setup.\n"
                        )
                    else:
                        # write heading
                        content += (
                            f"    \n"
                            f"    Options:\n"
                        )
                        # add list item for each option
                        for opt in options:
                            content += (
                                f"    - {opt}\n"
                            )
                # add newline at the end
                content += "\n"

        return content

    @property
    def name(self):
        return self.params['name'].val

    @name.setter
    def name(self, value):
        self.params['name'].val = value

    @property
    def disabled(self):
        return bool(self.params['disabled'])

    @disabled.setter
    def disabled(self, value):
        self.params['disabled'].val = value

    @property
    def currentLoop(self):
        # Get list of active loops
        loopList = self.exp.flow._loopList

        if len(loopList):
            # If there are any active loops, return the highest level
            return self.exp.flow._loopList[-1].params['name']
        else:
            # Otherwise, we are not in a loop, so loop handler is just experiment handler
            return "thisExp"


class BaseDeviceComponent(BaseComponent):
    """
    Base class for most components which interface with a hardware device.
    """
    # list of class strings (readable by DeviceManager) which this component's device could be
    deviceClasses = []

    def __init__(
            self, exp, parentName,
            # basic
            name='',
            startType='time (s)', startVal='',
            stopType='duration (s)', stopVal='',
            startEstim='', durationEstim='',
            # device
            deviceLabel="",
            # data
            saveStartStop=True, syncScreenRefresh=False,
            # testing
            disabled=False
    ):
        # initialise base component
        BaseComponent.__init__(
            self, exp, parentName,
            name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            saveStartStop=saveStartStop, syncScreenRefresh=syncScreenRefresh,
            disabled=disabled
        )
        # require hardware
        self.exp.requirePsychopyLibs(
            ['hardware']
        )
        # --- Device params ---
        self.order += [
            "deviceLabel"
        ]
        # label to refer to device by
        self.params['deviceLabel'] = Param(
            deviceLabel, valType="str", inputType="single", categ="Device",
            label=_translate("Device label"),
            hint=_translate(
                "A label to refer to this Component's associated hardware device by. If using the "
                "same device for multiple components, be sure to use the same label here."
            )
        )


class BaseVisualComponent(BaseComponent):
    """Base class for most visual stimuli
    """

    categories = ['Stimuli']
    targets = []
    iconFile = Path(__file__).parent / "unknown" / "unknown.png"
    tooltip = ""

    def __init__(self, exp, parentName, name='',
                 units='from exp settings', color='white', fillColor="", borderColor="",
                 pos=(0, 0), size=(0, 0), ori=0, colorSpace='rgb', opacity="", contrast=1,
                 startType='time (s)', startVal='',
                 stopType='duration (s)', stopVal='',
                 startEstim='', durationEstim='',
                 saveStartStop=True, syncScreenRefresh=True,
                 validator="", disabled=False):

        super(BaseVisualComponent, self).__init__(
            exp, parentName, name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim,
            saveStartStop=saveStartStop,
            syncScreenRefresh=syncScreenRefresh, disabled=disabled)

        self.exp.requirePsychopyLibs(
            ['visual'])  # needs this psychopy lib to operate

        self.order += [
            "color",
            "fillColor",
            "borderColor",
            "colorSpace",
            "opacity",
            "size",
            "pos",
            "units",
            "anchor",
            "ori",
        ]

        msg = _translate("Units of dimensions for this stimulus")
        self.params['units'] = Param(units,
            valType='str', inputType="choice", categ='Layout',
            allowedVals=['from exp settings', 'deg', 'cm', 'pix', 'norm',
                         'height', 'degFlatPos', 'degFlat'],
            hint=msg,
            label=_translate("Spatial units"))

        msg = _translate("Foreground color of this stimulus (e.g. $[1,1,0], red )")
        self.params['color'] = Param(color,
            valType='color', inputType="color", categ='Appearance',
            allowedTypes=[],
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Foreground color"))

        msg = _translate("In what format (color space) have you specified "
                         "the colors? (rgb, dkl, lms, hsv)")
        self.params['colorSpace'] = Param(colorSpace,
            valType='str', inputType="choice", categ='Appearance',
            allowedVals=['rgb', 'dkl', 'lms', 'hsv'],
            updates='constant',
            hint=msg,
            label=_translate("Color space"))

        msg = _translate("Fill color of this stimulus (e.g. $[1,1,0], red )")
        self.params['fillColor'] = Param(fillColor,
            valType='color', inputType="color", categ='Appearance',
            updates='constant', allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Fill color"))

        msg = _translate("Border color of this stimulus (e.g. $[1,1,0], red )")
        self.params['borderColor'] = Param(borderColor,
            valType='color', inputType="color", categ='Appearance',
            updates='constant',allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Border color"))

        msg = _translate("Opacity of the stimulus (1=opaque, 0=fully transparent, 0.5=translucent). "
                         "Leave blank for each color to have its own opacity (recommended if any color is None).")
        self.params['opacity'] = Param(opacity,
            valType='num', inputType="single", categ='Appearance',
            updates='constant', allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Opacity"))

        msg = _translate("Contrast of the stimulus (1.0=unchanged contrast, "
                         "0.5=decrease contrast, 0.0=uniform/no contrast, "
                         "-0.5=slightly inverted, -1.0=totally inverted)")
        self.params['contrast'] = Param(contrast,
            valType='num', inputType='single', allowedTypes=[], categ='Appearance',
            updates='constant',
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Contrast"))

        msg = _translate("Position of this stimulus (e.g. [1,2] )")
        self.params['pos'] = Param(pos,
            valType='list', inputType="single", categ='Layout',
            updates='constant', allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Position [x,y]"))

        msg = _translate("Size of this stimulus (either a single value or "
                         "x,y pair, e.g. 2.5, [1,2] ")
        self.params['size'] = Param(size,
            valType='list', inputType="single", categ='Layout',
            updates='constant', allowedTypes=[],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=msg,
            label=_translate("Size [w,h]"))

        self.params['ori'] = Param(ori,
            valType='num', inputType="spin", categ='Layout',
            updates='constant', allowedTypes=[], allowedVals=[-360,360],
            allowedUpdates=['constant', 'set every repeat', 'set every frame'],
            hint=_translate("Orientation of this stimulus (in deg)"),
            label=_translate("Orientation"))

        self.params['syncScreenRefresh'].readOnly = True

        # --- Testing ---
        self.params['validator'] = Param(
            validator, valType="code", inputType="choice", categ="Testing",
            allowedVals=self.getAllValidatorRoutineVals,
            allowedLabels=self.getAllValidatorRoutineLabels,
            label=_translate("Validate with..."),
            hint=_translate(
                "Name of validator Component/Routine to use to check the timing of this stimulus."
            )
        )

    def integrityCheck(self):
        """
        Run component integrity checks.
        """
        super().integrityCheck()  # run parent class checks first

        win = alerttools.TestWin(self.exp)

        # get units for this stimulus
        if 'units' in self.params:  # e.g. BrushComponent doesn't have this
            units = self.params['units'].val
        else:
            units = None
        if units == 'use experiment settings':
            units = self.exp.settings.params[
                'Units'].val  # this 1 uppercase
        if not units or units == 'use preferences':
            units = prefs.general['units']

        # tests for visual stimuli
        alerttools.testSize(self, win, units)
        alerttools.testPos(self, win, units)
        alerttools.testAchievableVisualOnsetOffset(self)
        alerttools.testValidVisualStimTiming(self)
        alerttools.testFramesAsInt(self)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame
        """
        params = self.params
        buff.writeIndented(f"\n")
        buff.writeIndented(f"# *{params['name']}* updates\n")
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCode(buff)
        if indented:
            buff.writeIndented(f"{params['name']}.setAutoDraw(True)\n")
            # to get out of the if statement
            buff.setIndentLevel(-indented, relative=True)

        # test for started (will update parameters each frame as needed)
        indented = self.writeActiveTestCode(buff)
        if indented:
            # to get out of the if statement
            buff.setIndentLevel(-indented, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        indented = self.writeStopTestCode(buff)
        if indented:
            buff.writeIndented(f"{params['name']}.setAutoDraw(False)\n")
            # to get out of the if statement
            buff.setIndentLevel(-indented, relative=True)

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame
        """
        params = self.params
        if "PsychoJS" not in self.targets:
            buff.writeIndented(f"// *{params['name']}* not supported by PsychoJS\n")
            return

        # set parameters that need updating every frame
        # do any params need updating? (this method inherited from _base)
        if self.checkNeedToUpdate('set every frame'):
            buff.writeIndentedLines(f"\nif ({params['name']}.status === PsychoJS.Status.STARTED){{ "
                                    f"// only update if being drawn\n")
            buff.setIndentLevel(+1, relative=True)  # to enter the if block
            self.writeParamUpdatesJS(buff, 'set every frame')
            buff.setIndentLevel(-1, relative=True)  # to exit the if block
            buff.writeIndented("}\n")

        buff.writeIndentedLines(f"\n// *{params['name']}* updates\n")
        # writes an if statement to determine whether to draw etc
        indented = self.writeStartTestCodeJS(buff)
        if indented:
            buff.writeIndentedLines(f"{params['name']}.setAutoDraw(true);\n")
            # to get out of the if statement
            while indented > 0:
                buff.setIndentLevel(-1, relative=True)
                buff.writeIndentedLines(
                    "}\n"
                    "\n"
                )
                indented -= 1
        # writes an if statement to determine whether to draw etc
        indented = self.writeStopTestCodeJS(buff)
        if indented:
            buff.writeIndentedLines(f"{params['name']}.setAutoDraw(false);\n")
            # to get out of the if statement
            while indented > 0:
                buff.setIndentLevel(-1, relative=True)
                buff.writeIndentedLines(
                    "}\n"
                    "\n"
                )
                indented -= 1
