#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
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

from __future__ import absolute_import, print_function
from builtins import object
# from future import standard_library

from psychopy.experiment import getInitVals
from psychopy.localization import _localized, _translate
from psychopy.experiment.params import Param
from .components import getInitVals, getAllComponents

# standard_library.install_aliases()


class TrialHandler(object):
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
            name, valType='code', updates=None, allowedUpdates=None,
            label=_localized['Name'],
            hint=_translate("Name of this loop"))
        self.params['nReps'] = Param(
            nReps, valType='code', updates=None, allowedUpdates=None,
            label=_localized['nReps'],
            hint=_translate("Number of repeats (for each condition)"))
        self.params['conditions'] = Param(
            list(conditions), valType='str',
            updates=None, allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("A list of dictionaries describing the "
                            "parameters in each condition"))
        self.params['conditionsFile'] = Param(
            conditionsFile, valType='str', updates=None, allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("Name of a file specifying the parameters for "
                            "each condition (.csv, .xlsx, or .pkl). Browse "
                            "to select a file. Right-click to preview file "
                            "contents, or create a new file."))
        self.params['endPoints'] = Param(
            list(endPoints), valType='num', updates=None, allowedUpdates=None,
            label=_localized['endPoints'],
            hint=_translate("The start and end of the loop (see flow "
                            "timeline)"))
        self.params['Selected rows'] = Param(
            selectedRows, valType='str',
            updates=None, allowedUpdates=None,
            label=_localized['Selected rows'],
            hint=_translate("Select just a subset of rows from your condition"
                            " file (the first is 0 not 1!). Examples: 0, "
                            "0:5, 5:-1"))
        # NB staircase is added for the sake of the loop properties dialog:
        self.params['loopType'] = Param(
            loopType, valType='str',
            allowedVals=['random', 'sequential', 'fullRandom',
                         'staircase', 'interleaved staircases'],
            label=_localized['loopType'],
            hint=_translate("How should the next condition value(s) be "
                            "chosen?"))
        self.params['random seed'] = Param(
            randomSeed, valType='code', updates=None, allowedUpdates=None,
            label=_localized['random seed'],
            hint=_translate("To have a fixed random sequence provide an "
                            "integer of your choosing here. Leave blank to "
                            "have a new random sequence on each run of the "
                            "experiment."))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', updates=None, allowedUpdates=None,
            label=_localized["Is trials"],
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within "
                            "a trial. It alters how data files are output"))

    def writeInitCode(self, buff):
        # no longer needed - initialise the trial handler just before it runs
        pass

    def writeInitCodeJS(self, buff):
        pass

    def writeResourcesCodeJS(self, buff):
        buff.writeIndented("resourceManager.addResource({});\n"
                           .format(self.params["conditionsFile"]))

    def writeLoopStartCode(self, buff):
        """Write the code to create and run a sequence of trials
        """
        # first create the handler init values
        inits = getInitVals(self.params)
        # import conditions from file?
        if self.params['conditionsFile'].val in ['None', None, 'none', '']:
            condsStr = "[None]"
        elif self.params['Selected rows'].val in ['None', None, 'none', '']:
            # just a conditions file with no sub-selection
            _con = "data.importConditions(%s)"
            condsStr = _con % self.params['conditionsFile']
        else:
            # a subset of a conditions file
            condsStr = ("data.importConditions(%(conditionsFile)s, selection="
                        "%(Selected rows)s)") % self.params
        # also a 'thisName' for use in "for thisTrial in trials:"
        makeLoopIndex = self.exp.namespace.makeLoopIndex
        self.thisName = makeLoopIndex(self.params['name'].val)
        # write the code
        code = ("\n# set up handler to look after randomisation of conditions etc\n"
                "%(name)s = data.TrialHandler(nReps=%(nReps)s, method=%(loopType)s, \n"
                "    extraInfo=expInfo, originPath=-1,\n")
        buff.writeIndentedLines(code % inits)
        # the next line needs to be kept separate to preserve potential string formatting
        # by the user in condStr (i.e. it shouldn't be a formatted string itself
        code = "    trialList=" + condsStr + ",\n"  # conditions go here
        buff.writeIndented(code)
        code = "    seed=%(random seed)s, name='%(name)s')\n"
        buff.writeIndentedLines(code % inits)

        code = ("thisExp.addLoop(%(name)s)  # add the loop to the experiment\n" +
                self.thisName + " = %(name)s.trialList[0]  " +
                "# so we can initialise stimuli with some values\n")
        buff.writeIndentedLines(code % self.params)
        # unclutter the namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. rgb = %(name)s.rgb)\n"
                    "if %(name)s != None:\n"
                    "    for paramName in %(name)s:\n"
                    "        exec('{} = %(name)s[paramName]'.format(paramName))\n")
            buff.writeIndentedLines(code % {'name': self.thisName})

        # then run the trials loop
        code = "\nfor %s in %s:\n"
        buff.writeIndentedLines(code % (self.thisName, self.params['name']))
        # fetch parameter info from conditions
        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %s\n" % self.params['name'])
        # unclutter the namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. rgb = %(name)s.rgb)\n"
                    "if %(name)s != None:\n"
                    "    for paramName in %(name)s:\n"
                    "        exec('{} = %(name)s[paramName]'.format(paramName))\n")
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

        code = ("\nfunction {funName}LoopBegin(thisScheduler) {{\n"
                "  // set up handler to look after randomisation of conditions etc\n"
                "  {name} = new TrialHandler({{\n"
                "    psychoJS: psychoJS,\n"
                "    nReps: {params[nReps]}, method: TrialHandler.Method.{loopType},\n"
                "    extraInfo: expInfo, originPath: undefined,\n"
                "    trialList: {trialList},\n"
                "    seed: {seed}, name: '{name}'}});\n"
                "  psychoJS.experiment.addLoop({name}); // add the loop to the experiment\n"
                "  currentLoop = {name};  // we're now the current loop\n"
                .format(funName=self.params['name'].val,
                        name=self.params['name'],
                        loopType=(self.params['loopType'].val).upper(),
                        params=self.params,
                        thisName=self.thisName,
                        trialList=trialList,
                        seed=seed))
        buff.writeIndentedLines(code)
        # for the scheduler
        if modular:
            code = ("\n  // Schedule all the trials in the trialList:\n"
                    "  for (const {thisName} of {name}) {{\n"
                    "    thisScheduler.add(importConditions({name}));\n")
        else:
            code = ("\n  // Schedule all the trials in the trialList:\n"
                    "  trialIterator = {name}[Symbol.iterator]();\n"
                    "  while(true) {{\n"
                    "    let result = trialIterator.next();\n"
                    "    if (result.done);\n"
                    "      break;\n"
                    "    let {thisName} = result.value;\n"
                    "    thisScheduler.add(importConditions({name}));\n")
        buff.writeIndentedLines(code.format(name=self.params['name'],
                                            thisName=self.thisName))
        # then we need to include begin, eachFrame and end code for each entry within that loop
        loopDict = self.exp.flow.loopDict
        thisLoop = loopDict[self]  # dict containing lists of children
        code = ""
        for thisChild in thisLoop:
            if thisChild.getType() == 'Routine':
                thisType = 'Routine'
                code += (
                    "    thisScheduler.add({name}RoutineBegin);\n"
                    "    thisScheduler.add({name}RoutineEachFrame);\n"
                    "    thisScheduler.add({name}RoutineEnd);\n"
                    .format(params=self.params, name=thisChild.params['name'])
                    )
            else:  # for a LoopInitiator
                code += (
                    "    const {name}LoopScheduler = new Scheduler(psychoJS);\n"
                    "    thisScheduler.add({name}LoopBegin, {name}LoopScheduler);\n"
                    "    thisScheduler.add({name}LoopScheduler);\n"
                    "    thisScheduler.add({name}LoopEnd);\n"
                    .format(params=self.params, name=thisChild.params['name'].val)
                    )
        if self.params['isTrials'].val == True:
            code += ("    thisScheduler.add(endLoopIteration(thisScheduler, "
                     "{thisName}));\n".format(thisName=self.thisName))

        code += ("  }\n"
                "\n"
                "  return Scheduler.Event.NEXT;\n"
                "}\n")
        buff.writeIndentedLines(code)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val == True:
            buff.writeIndentedLines("thisExp.nextEntry()\n\n")
        # end of the loop. dedent
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndented("# completed %s repeats of '%s'\n"
                           % (self.params['nReps'], self.params['name']))
        buff.writeIndented("\n")
        # save data
        if self.params['isTrials'].val == True:
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
        # Just within the loop advance data line if loop is whole trials
        code = ("\nfunction {funName}LoopEnd() {{\n"
                "  psychoJS.experiment.removeLoop({name});\n\n".format(funName=self.params['name'].val,
                                                                       name=self.params['name']))
        code += ("  return Scheduler.Event.NEXT;\n"
                "}\n")
        buff.writeIndentedLines(code)

    def getType(self):
        return 'TrialHandler'


class StairHandler(object):
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
            label=_localized['Name'])
        self.params['nReps'] = Param(
            nReps, valType='code',
            label=_localized['nReps'],
            hint=_translate("(Minimum) number of trials in the staircase"))
        self.params['start value'] = Param(
            startVal, valType='code',
            label=_localized['start value'],
            hint=_translate("The initial value of the parameter"))
        self.params['max value'] = Param(
            maxVal, valType='code',
            label=_localized['max value'],
            hint=_translate("The maximum value the parameter can take"))
        self.params['min value'] = Param(
            minVal, valType='code',
            label=_localized['min value'],
            hint=_translate("The minimum value the parameter can take"))
        self.params['step sizes'] = Param(
            stepSizes, valType='code',
            label=_localized['step sizes'],
            hint=_translate("The size of the jump at each step (can change"
                            " on each 'reversal')"))
        self.params['step type'] = Param(
            stepType, valType='str', allowedVals=['lin', 'log', 'db'],
            label=_localized['step type'],
            hint=_translate("The units of the step size (e.g. 'linear' will"
                            " add/subtract that value each step, whereas "
                            "'log' will ad that many log units)"))
        self.params['N up'] = Param(
            nUp, valType='code',
            label=_localized['N up'],
            hint=_translate("The number of 'incorrect' answers before the "
                            "value goes up"))
        self.params['N down'] = Param(
            nDown, valType='code',
            label=_localized['N down'],
            hint=_translate("The number of 'correct' answers before the "
                            "value goes down"))
        self.params['N reversals'] = Param(
            nReversals, valType='code',
            label=_localized['N reversals'],
            hint=_translate("Minimum number of times the staircase must "
                            "change direction before ending"))
        # these two are really just for making the dialog easier (they won't
        # be used to generate code)
        self.params['loopType'] = Param(
            'staircase', valType='str',
            allowedVals=['random', 'sequential', 'fullRandom', 'staircase',
                         'interleaved staircases'],
            label=_localized['loopType'],
            hint=_translate("How should the next trial value(s) be chosen?"))
        # NB this is added for the sake of the loop properties dialog
        self.params['endPoints'] = Param(
            list(endPoints), valType='num',
            label=_localized['endPoints'],
            hint=_translate('Where to loop from and to (see values currently'
                            ' shown in the flow view)'))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', updates=None, allowedUpdates=None,
            label=_localized["Is trials"],
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within"
                            " a trial. It alters how data files are output"))

    def writeInitCode(self, buff):
        # not needed - initialise the staircase only when needed
        pass

    def writeResourcesCodeJS(self, buff):
        pass  # no resources needed for staircase

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
        buff.writeIndented("currentLoop = %s\n" % self.params['name'])
        buff.writeIndented("level = %s\n" % self.thisName)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val:
            buff.writeIndentedLines("thisExp.nextEntry()\n\n")
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


class MultiStairHandler(object):
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
            name, valType='code',
            label=_localized['Name'],
            hint=_translate("Name of this loop"))
        self.params['nReps'] = Param(
            nReps, valType='code',
            label=_localized['nReps'],
            hint=_translate("(Minimum) number of trials in *each* staircase"))
        self.params['stairType'] = Param(
            stairType, valType='str',
            allowedVals=['simple', 'QUEST', 'quest'],
            label=_localized['stairType'],
            hint=_translate("How to select the next staircase to run"))
        self.params['switchMethod'] = Param(
            switchStairs, valType='str',
            allowedVals=['random', 'sequential', 'fullRandom'],
            label=_localized['switchMethod'],
            hint=_translate("How to select the next staircase to run"))
        # these two are really just for making the dialog easier (they won't
        # be used to generate code)
        self.params['loopType'] = Param(
            'staircase', valType='str',
            allowedVals=['random', 'sequential', 'fullRandom', 'staircase',
                         'interleaved staircases'],
            label=_localized['loopType'],
            hint=_translate("How should the next trial value(s) be chosen?"))
        self.params['endPoints'] = Param(
            list(endPoints), valType='num',
            label=_localized['endPoints'],
            hint=_translate('Where to loop from and to (see values currently'
                            ' shown in the flow view)'))
        self.params['conditions'] = Param(
            list(conditions), valType='str', updates=None,
            allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("A list of dictionaries describing the "
                            "differences between each staircase"))
        self.params['conditionsFile'] = Param(
            conditionsFile, valType='str', updates=None, allowedUpdates=None,
            label=_localized['conditions'],
            hint=_translate("An xlsx or csv file specifying the parameters "
                            "for each condition"))
        self.params['isTrials'] = Param(
            isTrials, valType='bool', updates=None, allowedUpdates=None,
            label=_localized["Is trials"],
            hint=_translate("Indicates that this loop generates TRIALS, "
                            "rather than BLOCKS of trials or stimuli within "
                            "a trial. It alters how data files are output"))
        pass  # don't initialise at start of exp, create when needed

    def writeResourcesCodeJS(self, buff):
        buff.writeIndented("resourceManager.addResource({});"
                           .format(self.params["conditionsFile"]))

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
                "    originPath=-1)\n"
                "thisExp.addLoop(%(name)s)  # add the loop to the experiment\n"
                "# initialise values for first condition\n"
                "level = %(name)s._nextIntensity  # initialise some vals\n"
                "condition = %(name)s.currentStaircase.condition\n"
                # start the loop:
                "\nfor level, condition in %(name)s:\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(1, relative=True)
        buff.writeIndented("currentLoop = %(name)s\n" % (self.params))
        # uncluttered namespace
        if not self.exp.prefsBuilder['unclutteredNamespace']:
            code = ("# abbreviate parameter names if possible (e.g. "
                    "rgb=condition.rgb)\n"
                    "for paramName in condition:\n"
                    "    exec(paramName + '= condition[paramName]')\n")
            buff.writeIndentedLines(code)

    def writeLoopEndCode(self, buff):
        # Just within the loop advance data line if loop is whole trials
        if self.params['isTrials'].val:
            buff.writeIndentedLines("thisExp.nextEntry()\n\n")
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

    def getType(self):
        return 'MultiStairHandler'

    def writeInitCode(self, buff):
        # not needed - initialise the staircase only when needed
        pass


class LoopInitiator(object):
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""

    def __init__(self, loop):
        super(LoopInitiator, self).__init__()
        self.loop = loop
        self.exp = loop.exp
        loop.initiator = self

    def getType(self):
        return 'LoopInitiator'

    def writeResourcesCodeJS(self, buff):
        self.loop.writeResourcesCodeJS(buff)

    def writeInitCode(self, buff):
        self.loop.writeInitCode(buff)

    def writeInitCodeJS(self, buff):
        self.loop.writeInitCodeJS(buff)

    def writeMainCode(self, buff):
        self.loop.writeLoopStartCode(buff)
        # we are now the inner-most loop
        self.exp.flow._loopList.append(self.loop)

    def writeMainCodeJS(self, buff, modular):
        self.loop.writeLoopStartCodeJS(buff, modular)
        # we are now the inner-most loop
        self.exp.flow._loopList.append(self.loop)

    def writeExperimentEndCode(self, buff):  # not needed
        pass


class LoopTerminator(object):
    """A simple class for inserting into the flow.
    This is created automatically when the loop is created"""

    def __init__(self, loop):
        super(LoopTerminator, self).__init__()
        self.loop = loop
        self.exp = loop.exp
        loop.terminator = self

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
        # _loopList[-1] will now be the inner-most loop
        self.exp.flow._loopList.remove(self.loop)

    def writeExperimentEndCode(self, buff):  # not needed
        pass
