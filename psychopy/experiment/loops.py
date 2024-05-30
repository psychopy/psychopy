#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Experiment classes:
    Experiment, Flow, Routine, Param, Loop*, *Handlers, and NameSpace

The code that writes out a *_lastrun.py experiment file is (in order):
    experiment.Experiment.writeScript() - starts things off, calls other parts
    settings.SettingsComponent.writeStartCode()
    experiment.Flow.writeBody()
        which will call the .writeBody() methods from each component
    settings.SettingsComponent.writeEndCode()
"""

from copy import deepcopy
from pathlib import Path
from xml.etree.ElementTree import Element

from psychopy.experiment import getInitVals
from psychopy.localization import _translate
from psychopy.experiment.params import Param
from .components import getInitVals, getAllComponents


class _BaseLoopHandler:

    def writeInitCode(self, buff):
        # no longer needed - initialise the trial handler just before it runs
        pass

    def writeInitCodeJS(self, buff):
        pass

    def writeLoopEndIterationCodeJS(self, buff):
        """Ends this iteration of a loop (calling nextEntry if needed)"""
        endLoopInteration = (f"\nfunction {self.name}LoopEndIteration(scheduler, snapshot) {{\n"
                             "  // ------Prepare for next entry------\n"
                             "  return async function () {\n")
        # check if the loop has ended prematurely and stop() if needed
        endLoopInteration += (
                             "    if (typeof snapshot !== 'undefined') {\n"
                             "      // ------Check if user ended loop early------\n"
                             "      if (snapshot.finished) {\n"
                             "        // Check for and save orphaned data\n"
                             "        if (psychoJS.experiment.isEntryEmpty()) {\n"
                             "          psychoJS.experiment.nextEntry(snapshot);\n"
                             "        }\n"
                             "        scheduler.stop();\n")
        # if isTrials then always perform experiment.nextEntry
        if self.params['isTrials']:
            endLoopInteration += (
                             "      } else {\n"
                             "        psychoJS.experiment.nextEntry(snapshot);\n")
        # then always close the loop and return NEXT to scheduler
        endLoopInteration += (
                             "      }\n"
                             "    return Scheduler.Event.NEXT;\n"
                             "    }\n"
                             "  };\n"
                             "}\n")

        buff.writeIndentedLines(endLoopInteration)


class TrialHandler(_BaseLoopHandler):
    """A looping experimental control object
            (e.g. generating a psychopy TrialHandler or StairHandler).
            """

    def __init__(self, exp, name, loopType='random', nReps=5,
                 conditions=(), conditionsFile='', endPoints=(0, 1),
                 randomSeed='', selectedRows='', isTrials=True):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param loopType:
        @type loopType: string ('rand', 'seq')
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        @param conditions: list of different trial conditions to be used
        @type conditions: list (of dicts?)
        @param conditionsFile: filename of the .csv file that
            contains conditions info
        @type conditions: string (filename)
        """
        super(TrialHandler, self).__init__()
        self.type = 'TrialHandler'
        self.exp = exp
        self.order = ['name']  # make name come first (others don't matter)
        self.params = {}
        self.params['name'] = Param(
            name, valType='code', inputType="single", updates=None, allowedUpdates=None,
            label=_translate('Name'),
            hint=_translate("Name of this loop"))
        self.params['nReps'] = Param(
            nReps, valType='num', inputType="spin", updates=None, allowedUpdates=None,
            label=_translate('Num. repeats'),
            hint=_translate("Number of repeats (for each condition)"))
        self.params['conditions'] = Param(
            list(conditions), valType='str', inputType="single",
            updates=None, allowedUpdates=None,
            label=_translate('Conditions'),
            hint=_translate("A list of dictionaries describing the "
                            "parameters in each condition"))
        self.params['conditionsFile'] = Param(
            conditionsFile, valType='file', inputType="table", updates=None, allowedUpdates=None,
            label=_translate('Conditions'),
            hint=_translate("Name of a file specifying the parameters for "
                            "each condition (.csv, .xlsx, or .pkl). Browse "
                            "to select a file. Right-click to preview file "
                            "contents, or create a new file."),
            ctrlParams={
                'template': Path(__file__).parent / "loopTemplate.xltx"
            }
        )
        self.params['endPoints'] = Param(
            list(endPoints), valType='num', inputType="single", updates=None, allowedUpdates=None,
            label=_translate('End points'),
            hint=_translate("The start and end of the loop (see flow "
                            "timeline)"))
        self.params['Selected rows'] = Param(
            selectedRows, valType='str', inputType="single",
            updates=None, allowedUpdates=None,
            label=_translate('Selected rows'),
            hint=_translate("Select just a subset of rows from your condition"
                            " file (the first is 0 not 1!). Examples: 0, "
                            "0:5, 5:-1"))
        # NB staircase is added for the sake of the loop properties dialog:
        self.params['loopType'] = Param(
            loopType, valType='str', inputType="choice",
            allowedVals=['random', 'sequential', 'fullRandom',
                         'staircase', 'interleaved staircases'],
            label=_translate('Loop type'),
            hint=_translate("How should the next condition value(s) be "
                            "chosen?"))
        self.params['random seed'] = Param(
            randomSeed, valType='code', inputType="single", updates=None, allowedUpdates=None,
            label=_translate('Random seed'),
            hint=_translate("To have a fixed random sequence provide an "
                            "integer of your choosing here. Leave blank to "
                            "have a new random sequence on each run of the "
                            "experiment."))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', inputType="bool", updates=None, allowedUpdates=None,
            label=_translate("Is trials"),
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within "
                            "a trial. It alters how data files are output"))

    def writeLoopStartCode(self, buff):
        """Write the code to create and run a sequence of trials
        """
        # first create the handler init values
        inits = getInitVals(self.params)
        # import conditions from file?
        if self.params['conditionsFile'].val in ['None', None, 'none', '']:
            inits['trialList'] = (
                "[None]"
            )
        elif self.params['Selected rows'].val in ['None', None, 'none', '']:
            # just a conditions file with no sub-selection
            inits['trialList'] = (
                "data.importConditions(%(conditionsFile)s)"
            ) % inits
        else:
            # a subset of a conditions file
            inits['trialList'] = (
                 "data.importConditions(\n"
                 "    %(conditionsFile)s, \n"
                 "    selection=%(Selected rows)s\n"
                 ")\n"
            ) % inits
        # also a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = inits['loopIndex'] = makeLoopIndex(self.params['name'].val)
        # write the code
        code = (
            "\n"
            "# set up handler to look after randomisation of conditions etc\n"
            "%(name)s = data.TrialHandler2(\n"
            "    name='%(name)s',\n"
            "    nReps=%(nReps)s, \n"
            "    method=%(loopType)s, \n"
            "    extraInfo=expInfo, \n"
            "    originPath=-1, \n"
            "    trialList=%(trialList)s, \n"
            "    seed=%(random seed)s, \n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)
        code = (
            "thisExp.addLoop(%(name)s)  # add the loop to the experiment\n" 
            "%(loopIndex)s = %(name)s.trialList[0]  # so we can initialise stimuli with some values\n"
        )
        buff.writeIndentedLines(code % inits)
        # unclutter the namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. rgb = %(name)s.rgb)\n"
                    "if %(name)s != None:\n"
                    "    for paramName in %(name)s:\n"
                    "        globals()[paramName] = %(name)s[paramName]\n")
            buff.writeIndentedLines(code % {'name': self.thisName})

        # send data to Liaison before loop starts
        if self.params['isTrials'].val:
            buff.writeIndentedLines(
                "if thisSession is not None:\n"
                "    # if running in a Session with a Liaison client, send data up to now\n"
                "    thisSession.sendExperimentData()\n"
            )

        # then run the trials loop
        code = "\nfor %s in %s:\n"
        buff.writeIndentedLines(code % (self.thisName, self.params['name']))
        # fetch parameter info from conditions
        buff.setIndentLevel(1, relative=True)
        code = (
            "currentLoop = %(name)s\n"
            "thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)\n"
        )
        buff.writeIndentedLines(code % self.params)

        # send data to Liaison at start of each iteration
        if self.params['isTrials'].val:
            buff.writeIndentedLines(
                "if thisSession is not None:\n"
                "    # if running in a Session with a Liaison client, send data up to now\n"
                "    thisSession.sendExperimentData()\n"
            )

        # handle pausing
        code = (
            "# pause experiment here if requested\n"
            "if thisExp.status == PAUSED:\n"
            "    pauseExperiment(\n"
            "        thisExp=thisExp, \n"
            "        win=win, \n"
            "        timers=[routineTimer], \n"
            "        playbackComponents=[]\n"
            ")\n"
        )
        buff.writeIndentedLines(code)
        # unclutter the namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. rgb = %(name)s.rgb)\n"
                    "if %(name)s != None:\n"
                    "    for paramName in %(name)s:\n"
                    "        globals()[paramName] = %(name)s[paramName]\n")
            buff.writeIndentedLines(code % {'name': self.thisName})

    def writeLoopStartCodeJS(self, buff, modular):
        """Write the code to create and run a sequence of trials
        """
        # some useful variables
        # create the variable "thisTrial" from "trials"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)

        # Convert filepath separator
        conditionsFile = self.params['conditionsFile'].val
        self.params['conditionsFile'].val = conditionsFile.replace('\\\\', '/').replace('\\', '/')
        # seed might be undefined
        seed = self.params['random seed'].val or 'undefined'
        if self.params['conditionsFile'].val in ['None', None, 'none', '']:
            trialList='undefined'
        elif self.params['Selected rows'].val in ['None', None, 'none', '']:
            trialList = self.params['conditionsFile']
        else:
            trialList = ("TrialHandler.importConditions"
                         "(psychoJS.serverManager, {}, {})"
                         ).format(self.params['conditionsFile'],
                                  self.params['Selected rows'])

        nReps = self.params['nReps'].val
        if nReps in ['None', None, 'none', '']:
            nReps = 'undefined'
        elif isinstance(nReps, str):
            nReps = nReps.strip("$")

        code = ("\nfunction {loopName}LoopBegin({loopName}LoopScheduler, snapshot) {{\n"
                "  return async function() {{\n"
                .format(loopName=self.params['name'],
                        loopType=(self.params['loopType'].val).upper(),
                        nReps=nReps,
                        trialList=trialList,
                        seed=seed))
        buff.writeIndentedLines(code)
        buff.setIndentLevel(2, relative=True)

        code = ("TrialHandler.fromSnapshot(snapshot); // update internal variables (.thisN etc) of the loop\n\n"
                "// set up handler to look after randomisation of conditions etc\n"
                "{loopName} = new TrialHandler({{\n"
                "  psychoJS: psychoJS,\n"
                "  nReps: {nReps}, method: TrialHandler.Method.{loopType},\n"
                "  extraInfo: expInfo, originPath: undefined,\n"
                "  trialList: {trialList},\n"
                "  seed: {seed}, name: '{loopName}'\n"
                "}});\n"
                "psychoJS.experiment.addLoop({loopName}); // add the loop to the experiment\n"
                "currentLoop = {loopName};  // we're now the current loop\n"
                .format(loopName=self.params['name'],
                        loopType=(self.params['loopType'].val).upper(),
                        nReps=nReps,
                        trialList=trialList,
                        seed=seed))
        buff.writeIndentedLines(code)
        
        # for the scheduler
        if modular:
            code = ("\n// Schedule all the trials in the trialList:\n"
                    "for (const {thisName} of {loopName}) {{\n"
                    "  snapshot = {loopName}.getSnapshot();\n"
                    "  {loopName}LoopScheduler.add(importConditions(snapshot));\n")
        else:
            code = ("\n// Schedule all the trials in the trialList:\n"
                    "{loopName}.forEach(function() {{\n"
                    "  snapshot = {loopName}.getSnapshot();\n\n"
                    "  {loopName}LoopScheduler.add(importConditions(snapshot));\n")
        buff.writeIndentedLines(code.format(loopName=self.params['name'],
                                            thisName=self.thisName))
        # then we need to include begin, eachFrame and end code for each entry within that loop
        loopDict = self.exp.flow.loopDict
        thisLoop = loopDict[self]  # dict containing lists of children
        code = ""
        for thisChild in thisLoop:
            if isinstance(thisChild, (LoopInitiator, _BaseLoopHandler)):
                # for a LoopInitiator
                code += (
                    "  const {childName}LoopScheduler = new Scheduler(psychoJS);\n"
                    "  {loopName}LoopScheduler.add({childName}LoopBegin({childName}LoopScheduler, snapshot));\n"
                    "  {loopName}LoopScheduler.add({childName}LoopScheduler);\n"
                    "  {loopName}LoopScheduler.add({childName}LoopEnd);\n"
                        .format(childName=thisChild.params['name'],
                                loopName=self.params['name'])
                )
            else:
                code += (
                    "  {loopName}LoopScheduler.add({childName}RoutineBegin(snapshot));\n"
                    "  {loopName}LoopScheduler.add({childName}RoutineEachFrame());\n"
                    "  {loopName}LoopScheduler.add({childName}RoutineEnd(snapshot));\n"
                    .format(childName=thisChild.params['name'],
                            loopName=self.params['name'])
                    )

        code += "  {loopName}LoopScheduler.add({loopName}LoopEndIteration({loopName}LoopScheduler, snapshot));\n"
        code += "}}%s\n" % ([');', ''][modular])
        code += ("\n"
                 "return Scheduler.Event.NEXT;\n")
        buff.writeIndentedLines(code.format(loopName=self.params['name']))
        buff.setIndentLevel(-2, relative=True)
        buff.writeIndentedLines(
                 "  }\n"
                 "}\n"
        )

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val == True:
            buff.writeIndentedLines(
                "thisExp.nextEntry()\n"
                "\n"
            )
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# completed %s repeats of '%s'\n"
                           % (self.params['nReps'], self.params['name']))
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val:
            # send final data to Liaison
            buff.writeIndentedLines(
                "if thisSession is not None:\n"
                "    # if running in a Session with a Liaison client, send data up to now\n"
                "    thisSession.sendExperimentData()\n"
            )
            # a string to show all the available variables (if the conditions
            # isn't just None or [None])
            saveExcel = self.exp.settings.params['Save excel file'].val
            saveCSV = self.exp.settings.params['Save csv file'].val
            # get parameter names
            if saveExcel or saveCSV:
                code = ("# get names of stimulus parameters\n"
                        "if %(name)s.trialList in ([], [None], None):\n"
                        "    params = []\n"
                        "else:\n"
                        "    params = %(name)s.trialList[0].keys()\n")
                buff.writeIndentedLines(code % self.params)
            # write out each type of file
            if saveExcel or saveCSV:
                buff.writeIndented("# save data for this loop\n")
            if saveExcel:
                code = ("%(name)s.saveAsExcel(filename + '.xlsx', sheetName='%(name)s',\n"
                        "    stimOut=params,\n"
                        "    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
                buff.writeIndentedLines(code % self.params)
            if saveCSV:
                code = ("%(name)s.saveAsText(filename + '%(name)s.csv', "
                        "delim=',',\n"
                        "    stimOut=params,\n"
                        "    dataOut=['n','all_mean','all_std', 'all_raw'])\n")
                buff.writeIndentedLines(code % self.params)

    def writeLoopEndCodeJS(self, buff):
        code = (
            "\n"
            "async function %(name)sLoopEnd() {\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        code = (
                "// terminate loop\n"
                "psychoJS.experiment.removeLoop(%(name)s);\n"
                "// update the current loop from the ExperimentHandler\n"
                "if (psychoJS.experiment._unfinishedLoops.length>0)\n"
                "  currentLoop = psychoJS.experiment._unfinishedLoops.at(-1);\n"
                "else\n"
                "  currentLoop = psychoJS.experiment;  // so we use addData from the experiment\n"
                "return Scheduler.Event.NEXT;\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = (
            "}"
        )
        buff.writeIndentedLines(code % self.params)

    def getType(self):
        return 'TrialHandler'

    @property
    def name(self):
        return self.params['name'].val


class StairHandler(_BaseLoopHandler):
    """A staircase experimental control object.
    """

    def __init__(self, exp, name, nReps='50', startVal='', nReversals='',
                 nUp=1, nDown=3, minVal=0, maxVal=1,
                 stepSizes='[4,4,2,2,1]', stepType='db', endPoints=(0, 1),
                 isTrials=True):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        """
        super(StairHandler, self).__init__()
        self.type = 'StairHandler'
        self.exp = exp
        self.order = ['name']  # make name come first (others don't matter)
        self.children = []
        self.params = {}
        self.params['name'] = Param(
            name, valType='code',
            hint=_translate("Name of this loop"),
            label=_translate('Name'))
        self.params['nReps'] = Param(
            nReps, valType='num', inputType='spin',
            label=_translate('nReps'),
            hint=_translate("(Minimum) number of trials in the staircase"))
        self.params['start value'] = Param(
            startVal, valType='num', inputType='single',
            label=_translate('Start value'),
            hint=_translate("The initial value of the parameter"))
        self.params['max value'] = Param(
            maxVal, valType='num', inputType='single',
            label=_translate('Max value'),
            hint=_translate("The maximum value the parameter can take"))
        self.params['min value'] = Param(
            minVal, valType='num', inputType='single',
            label=_translate('Min value'),
            hint=_translate("The minimum value the parameter can take"))
        self.params['step sizes'] = Param(
            stepSizes, valType='list', inputType='single',
            label=_translate('Step sizes'),
            hint=_translate("The size of the jump at each step (can change"
                            " on each 'reversal')"))
        self.params['step type'] = Param(
            stepType, valType='str', inputType='choice', allowedVals=['lin', 'log', 'db'],
            label=_translate('Step type'),
            hint=_translate("The units of the step size (e.g. 'linear' will"
                            " add/subtract that value each step, whereas "
                            "'log' will ad that many log units)"))
        self.params['N up'] = Param(
            nUp, valType='num', inputType='spin',
            label=_translate('N up'),
            hint=_translate("The number of 'incorrect' answers before the "
                            "value goes up"))
        self.params['N down'] = Param(
            nDown, valType='num', inputType='spin',
            label=_translate('N down'),
            hint=_translate("The number of 'correct' answers before the "
                            "value goes down"))
        self.params['N reversals'] = Param(
            nReversals, valType='num', inputType='spin',
            label=_translate('N reversals'),
            hint=_translate("Minimum number of times the staircase must "
                            "change direction before ending"))
        # these two are really just for making the dialog easier (they won't
        # be used to generate code)
        self.params['loopType'] = Param(
            'staircase', valType='str', inputType='choice',
            allowedVals=['random', 'sequential', 'fullRandom', 'staircase',
                         'interleaved staircases'],
            label=_translate('Loop type'),
            hint=_translate("How should the next trial value(s) be chosen?"))
        # NB this is added for the sake of the loop properties dialog
        self.params['endPoints'] = Param(
            list(endPoints), valType='num', inputType='spin',
            label=_translate('End points'),
            hint=_translate('Where to loop from and to (see values currently'
                            ' shown in the flow view)'))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', inputType='bool', updates=None, allowedUpdates=None,
            label=_translate("Is trials"),
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within"
                            " a trial. It alters how data files are output"))

    @property
    def name(self):
        return self.params['name'].val

    def writeInitCode(self, buff):
        # not needed - initialise the staircase only when needed
        pass

    def writeLoopStartCode(self, buff):
        # create the staircase
        # also a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)
        if self.params['N reversals'].val in ("", None, 'None'):
            self.params['N reversals'].val = '0'
        # write the code
        code = ('\n# --------Prepare to start Staircase "%(name)s" --------\n'
                "# set up handler to look after next chosen value etc\n"
                "%(name)s = data.StairHandler(startVal=%(start value)s, extraInfo=expInfo,\n"
                "    stepSizes=%(step sizes)s, stepType=%(step type)s,\n"
                "    nReversals=%(N reversals)s, nTrials=%(nReps)s, \n"
                "    nUp=%(N up)s, nDown=%(N down)s,\n"
                "    minVal=%(min value)s, maxVal=%(max value)s,\n"
                "    originPath=-1, name='%(name)s')\n"
                "thisExp.addLoop(%(name)s)  # add the loop to the experiment")
        buff.writeIndentedLines(code % self.params)
        code = "level = %s = %s  # initialise some vals\n"
        buff.writeIndented(code % (self.thisName, self.params['start value']))
        # then run the trials
        # work out a name for e.g. thisTrial in trials:
        code = "\nfor %s in %s:\n"
        buff.writeIndentedLines(code % (self.thisName, self.params['name']))
        buff.setIndentLevel(1, relative=True)
        code = (
            "currentLoop = %(name)s\n"
            "thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)\n"
        )
        buff.writeIndentedLines(code % self.params)
        buff.writeIndented("level = %s\n" % self.thisName)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val:
            buff.writeIndentedLines(
                "thisExp.nextEntry()\n"
                "\n"
                "if thisSession is not None:\n"
                "    # if running in a Session with a Liaison client, send data up to now\n"
                "    thisSession.sendExperimentData()\n"
            )
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# staircase completed\n")
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val:
            if self.exp.settings.params['Save excel file'].val:
                code = ("%(name)s.saveAsExcel(filename + '.xlsx',"
                        " sheetName='%(name)s')\n")
                buff.writeIndented(code % self.params)
            if self.exp.settings.params['Save csv file'].val:
                code = ("%(name)s.saveAsText(filename + "
                        "'%(name)s.csv', delim=',')\n")
                buff.writeIndented(code % self.params)

    def getType(self):
        return 'StairHandler'


class MultiStairHandler(_BaseLoopHandler):
    """To handle multiple interleaved staircases
    """

    def __init__(self, exp, name, nReps='50', stairType='simple',
                 switchStairs='random',
                 conditions=(), conditionsFile='', endPoints=(0, 1),
                 isTrials=True):
        """
        @param name: name of the loop e.g. trials
        @type name: string
        @param nReps: number of reps (for all conditions)
        @type nReps:int
        """
        super(MultiStairHandler, self).__init__()
        self.type = 'MultiStairHandler'
        self.exp = exp
        self.order = ['name']  # make name come first
        self.params = {}
        self.params['name'] = Param(
            name, valType='code', inputType='single',
            label=_translate('Name'),
            hint=_translate("Name of this loop"))
        self.params['nReps'] = Param(
            nReps, valType='num', inputType='spin',
            label=_translate('nReps'),
            hint=_translate("(Minimum) number of trials in *each* staircase"))
        self.params['stairType'] = Param(
            stairType, valType='str', inputType='choice',
            allowedVals=['simple', 'QUEST', 'questplus'],
            label=_translate('Stair type'),
            hint=_translate("How to select the next staircase to run"))
        self.params['switchMethod'] = Param(
            switchStairs, valType='str', inputType='choice',
            allowedVals=['random', 'sequential', 'fullRandom'],
            label=_translate('Switch method'),
            hint=_translate("How to select the next staircase to run"))
        # these two are really just for making the dialog easier (they won't
        # be used to generate code)
        self.params['loopType'] = Param(
            'staircase', valType='str', inputType='choice',
            allowedVals=['random', 'sequential', 'fullRandom', 'staircase',
                         'interleaved staircases'],
            label=_translate('Loop type'),
            hint=_translate("How should the next trial value(s) be chosen?"))
        self.params['endPoints'] = Param(
            list(endPoints), valType='num', inputType='spin',
            label=_translate('End points'),
            hint=_translate('Where to loop from and to (see values currently'
                            ' shown in the flow view)'))
        self.params['conditions'] = Param(
            list(conditions), valType='list', inputType='single',
            updates=None, allowedUpdates=None,
            label=_translate('Conditions'),
            hint=_translate("A list of dictionaries describing the "
                            "differences between each staircase"))

        def getTemplate():
            """
            Method to get the template for this loop's chosen stair type. This is specified as a
            method rather than a simple value as the control needs to update its target according
            to the current value of stairType.

            Returns
            -------
            pathlib.Path
                Path to the appropriate template file
            """
            # root folder
            root = Path(__file__).parent
            # get file path according to stairType param
            if self.params['stairType'] == "QUEST":
                return root / "questTemplate.xltx"
            elif self.params['stairType'] == "questplus":
                return root / "questPlusTemplate.xltx"
            else:
                return root / "staircaseTemplate.xltx"

        self.params['conditionsFile'] = Param(
            conditionsFile, valType='file', inputType='table', updates=None, allowedUpdates=None,
            label=_translate('Conditions'),
            hint=_translate("An xlsx or csv file specifying the parameters "
                            "for each condition"),
            ctrlParams={
                'template': getTemplate
            }
        )
        self.params['isTrials'] = Param(
            isTrials, valType='bool', inputType='bool', updates=None, allowedUpdates=None,
            label=_translate("Is trials"),
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within "
                            "a trial. It alters how data files are output"))
        pass  # don't initialise at start of exp, create when needed

    @property
    def name(self):
        return self.params['name'].val

    def writeLoopStartCode(self, buff):
        # create a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)
        # create the MultistairHander
        code = ("\n# set up handler to look after randomisation of trials etc\n"
                "conditions = data.importConditions(%(conditionsFile)s)\n"
                "%(name)s = data.MultiStairHandler(stairType=%(stairType)s, "
                "name='%(name)s',\n"
                "    nTrials=%(nReps)s,\n"
                "    conditions=conditions,\n"
                "    method=%(switchMethod)s,\n"
                "    originPath=-1)\n"
                "thisExp.addLoop(%(name)s)  # add the loop to the experiment\n"
                "# initialise values for first condition\n"
                "level = %(name)s._nextIntensity  # initialise some vals\n"
                "condition = %(name)s.currentStaircase.condition\n"
                # start the loop:
                "\nfor level, condition in %(name)s:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        code = (
            "currentLoop = %(name)s\n"
            "thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)\n"
        )
        buff.writeIndentedLines(code % self.params)
        # uncluttered namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. "
                    "rgb=condition.rgb)\n"
                    "for paramName in condition:\n"
                    "    globals()[paramName] = condition[paramName]\n")
            buff.writeIndentedLines(code)

    def writeLoopStartCodeJS(self, buff, modular):
        inits = deepcopy(self.params)
        # For JS, stairType needs to be code
        inits['stairType'].valType = "code"
        # Method needs to be code and upper
        inits['switchMethod'].valType = "code"
        inits['switchMethod'].val = inits['switchMethod'].val.upper()

        code = (
            "\nfunction %(name)sLoopBegin(%(name)sLoopScheduler, snapshot) {\n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(1, relative=True)
        code = (
                "return async function() {\n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(1, relative=True)
        code = (
                    "// setup a MultiStairTrialHandler\n"
                    "%(name)sConditions = TrialHandler.importConditions(psychoJS.serverManager, %(conditionsFile)s);\n"
                    "%(name)s = new data.MultiStairHandler({stairType:MultiStairHandler.StaircaseType.%(stairType)s, \n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(1, relative=True)
        code = (
                        "psychoJS: psychoJS,\n"
                        "name: '%(name)s',\n"
                        "varName: 'intensity',\n"
                        "nTrials: %(nReps)s,\n"
                        "conditions: %(name)sConditions,\n"
                        "method: TrialHandler.Method.%(switchMethod)s\n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(-1, relative=True)
        code = (
                    "});\n"
                    "psychoJS.experiment.addLoop(%(name)s); // add the loop to the experiment\n"
                    "currentLoop = %(name)s;  // we're now the current loop\n"
                    "// Schedule all the trials in the trialList:\n"
                    "for (const thisQuestLoop of %(name)s) {\n"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(1, relative=True)
        thisLoop = self.exp.flow.loopDict[self]
        buff.writeIndentedLines(
                        "%(name)sLoopScheduler.add(%(name)sLoopBeginIteration(snapshot));\n" % inits)
        for thisChild in thisLoop:
            if thisChild.getType() == 'Routine':
                code = (
                        "snapshot = %(name)s.getSnapshot();\n"
                        "{loopName}LoopScheduler.add(importConditions(snapshot));\n"
                        "{loopName}LoopScheduler.add({childName}RoutineBegin(snapshot));\n"
                        "{loopName}LoopScheduler.add({childName}RoutineEachFrame());\n"
                        "{loopName}LoopScheduler.add({childName}RoutineEnd());\n"
                        .format(childName=thisChild.params['name'],
                                loopName=self.params['name'])
                    )
            else:  # for a LoopInitiator
                code = (
                        "snapshot = %(name)s.getSnapshot();\n"
                        "const {childName}LoopScheduler = new Scheduler(psychoJS);\n"
                        "{loopName}LoopScheduler.add(importConditions(snapshot));\n"
                        "{loopName}LoopScheduler.add({childName}LoopBegin({childName}LoopScheduler, snapshot));\n"
                        "{loopName}LoopScheduler.add({childName}LoopScheduler);\n"
                        "{loopName}LoopScheduler.add({childName}LoopEnd);\n"
                        .format(childName=thisChild.params['name'],
                                loopName=self.params['name'])
                        )
            buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(-1, relative=True)

        code = ("// then iterate over this loop (%(name)s)\n"
                "%(name)sLoopScheduler.add(%(name)sLoopEndIteration(%(name)sLoopScheduler, snapshot));\n"
                "}"
                "\n\n"
                "return Scheduler.Event.NEXT;\n"
                )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(-1, relative=True)
        code = (
                "}"
        )
        buff.writeIndentedLines(code % inits)

        buff.setIndentLevel(-1, relative=True)
        code = (
            "}"
        )
        buff.writeIndentedLines(code % inits)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val:
            buff.writeIndentedLines(
                "thisExp.nextEntry()\n"
                "\n"
                "if thisSession is not None:\n"
                "    # if running in a Session with a Liaison client, send data up to now\n"
                "    thisSession.sendExperimentData()\n"
            )
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# all staircases completed\n")
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val:
            if self.exp.settings.params['Save excel file'].val:
                code = "%(name)s.saveAsExcel(filename + '.xlsx')\n"
                buff.writeIndented(code % self.params)
            if self.exp.settings.params['Save csv file'].val:
                code = ("%(name)s.saveAsText(filename + '%(name)s.csv', "
                        "delim=',')\n")
                buff.writeIndented(code % self.params)

    def writeLoopBeginIterationCodeJS(self, buff):
        startLoopInteration = (f"\nfunction {self.name}LoopBeginIteration(snapshot) {{\n"
                               f"  return async function() {{\n"
                               f"    // ------Prepare for next entry------\n"
                               f"    level = {self.name}.intensity;\n\n"
                               f"    return Scheduler.Event.NEXT;\n"
                               f"  }}\n"
                               f"}}\n")
        buff.writeIndentedLines(startLoopInteration % self.params)

    def writeLoopEndCodeJS(self, buff):
        code = (
            "\n"
            "async function %(name)sLoopEnd() {\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        code = (
                "// terminate loop\n"
                "psychoJS.experiment.removeLoop(%(name)s);\n"
                "// update the current loop from the ExperimentHandler\n"
                "if (psychoJS.experiment._unfinishedLoops.length>0)\n"
                "  currentLoop = psychoJS.experiment._unfinishedLoops.at(-1);\n"
                "else\n"
                "  currentLoop = psychoJS.experiment;  // so we use addData from the experiment\n"\
                "return Scheduler.Event.NEXT;\n"
        )
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(-1, relative=True)
        code = (
            "}"
        )
        buff.writeIndentedLines(code % self.params)

    def getType(self):
        return 'MultiStairHandler'

    def writeInitCode(self, buff):
        # not needed - initialise the staircase only when needed
        pass


class LoopInitiator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""

    def __init__(self, loop):
        super(LoopInitiator, self).__init__()
        self.loop = loop
        self.exp = loop.exp
        loop.initiator = self

    def __eq__(self, obj):
        if isinstance(obj, str):
            return self.loop.name == obj
        elif isinstance(obj, LoopInitiator):
            return self.loop.name == obj.loop.name

    def __ne__(self, obj):
        return not (self == obj)

    @property
    def _xml(self):
        # Make root element
        element = Element("LoopInitiator")
        element.set("loopType", self.loop.__class__.__name__)
        element.set("name", self.loop.params['name'].val)
        # Add an element for each parameter
        for key, param in sorted(self.loop.params.items()):
            # Create node
            paramNode = Element("Param")
            paramNode.set("name", key)
            # Assign values
            if hasattr(param, 'updates'):
                paramNode.set('updates', "{}".format(param.updates))
            if hasattr(param, 'val'):
                paramNode.set('val', u"{}".format(param.val).replace("\n", "&#10;"))
            if hasattr(param, 'valType'):
                paramNode.set('valType', param.valType)
            element.append(paramNode)
        return element

    @property
    def name(self):
        return self.loop.name

    def getType(self):
        return 'LoopInitiator'

    def writePreCodeJS(self, buff):
        if hasattr(self.loop, 'writePreCodeJS'):
            self.loop.writePreCodeJS(buff)

    def writeInitCode(self, buff):
        self.loop.writeInitCode(buff)

    def writeInitCodeJS(self, buff):
        if hasattr(self.loop, "writeInitCodeJS"):
            # the loop may not have/need this option
            self.loop.writeInitCodeJS(buff)

    def writeMainCode(self, buff):
        self.loop.writeLoopStartCode(buff)
        # we are now the inner-most loop
        self.exp.flow._loopList.append(self.loop)

    def writeMainCodeJS(self, buff, modular):
        self.loop.writeLoopStartCodeJS(buff, modular)
        # some loops do extra things in their beginIteration
        if hasattr(self.loop, 'writeLoopBeginIterationCodeJS'):
            self.loop.writeLoopBeginIterationCodeJS(buff)
        # we are now the inner-most loop
        self.exp.flow._loopList.append(self.loop)

    def writeExperimentEndCode(self, buff):  # not needed
        pass


class LoopTerminator:
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""

    def __init__(self, loop):
        super(LoopTerminator, self).__init__()
        self.loop = loop
        self.exp = loop.exp
        loop.terminator = self

    @property
    def _xml(self):
        # Make root element
        element = Element("LoopTerminator")
        element.set("name", self.loop.params['name'].val)

        return element

    @property
    def name(self):
        return self.loop.name

    def getType(self):
        return 'LoopTerminator'

    def writeInitCode(self, buff):
        pass

    def writeMainCode(self, buff):
        self.loop.writeLoopEndCode(buff)
        # _loopList[-1] will now be the inner-most loop
        self.exp.flow._loopList.remove(self.loop)

    def writeMainCodeJS(self, buff, modular):
        self.loop.writeLoopEndCodeJS(buff)
        self.loop.writeLoopEndIterationCodeJS(buff)
        # _loopList[-1] will now be the inner-most loop
        self.exp.flow._loopList.remove(self.loop)

    def writeExperimentEndCode(self, buff):  # not needed
        pass
