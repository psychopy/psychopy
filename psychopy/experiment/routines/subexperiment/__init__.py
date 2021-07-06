from psychopy.tools.versionchooser import _translate
from .. import BaseStandaloneRoutine
from pathlib import Path

from ... import Param, Experiment
from ...loops import LoopInitiator, LoopTerminator


class SubexperimentRoutine(BaseStandaloneRoutine):
    categories = ['Custom']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / "unknown.png"
    tooltip = "Inject another experiment into this one"

    def __init__(self, exp, name='subexp', experiment=""):
        BaseStandaloneRoutine.__init__(self, exp, name=name)
        self.type = 'SubexperimentStandaloneRoutine'

        del self.params['stopVal']
        del self.params['stopType']

        self.params['file'] = Param(experiment,
            valType='file', inputType="file", categ='Basic',
            updates='constant', allowedUpdates=[], allowedTypes=[],
            hint=_translate("Experiment file to run when this routine is reached"),
            label=_translate('Experiment File'))

    def writeMainCode(self, buff):
        # Make experiment object from param
        subexp = Experiment()
        absPath = Path(self.params['file'].val).absolute()
        subexp.loadFromXML(absPath)
        # Rename all components and routines to preserve namespace
        routineNames = list(subexp.routines)
        for routine in routineNames:
            # Rename routine
            newRoutineName = self.params['name'].val + "_" + routine[0].upper() + routine[1:]
            subexp.routines[routine].name = newRoutineName
            subexp.routines[newRoutineName] = subexp.routines.pop(routine)
            # Rename components in routine
            if isinstance(subexp.routines[newRoutineName], list):
                for comp in subexp.routines[newRoutineName]:
                    name = str(comp.params['name'])
                    comp.params['name'].val = self.params['name'].val + "_" + name[0].upper() + name[1:]
                    # Rename routine references
                    comp.parentName = newRoutineName
        # Rename loops to preserve namespace
        for item in subexp.flow:
            if isinstance(item, LoopInitiator):
                item.name = self.params['name'].val + "_" + item.name[0].upper() + item.name[1:]
        # Make sub handler
        code = (
            "\n"
            "# Run experiment %(name)s from %(file)s\n"
            "%(name)s = data.SubexperimentHandler(thisExp)\n"
            "%(name)s.status = STARTED\n"
            "%(name)s.tStart = t\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)
        # Write each item in experiment flow
        subexp.flow.writeBody(buff)
        # End sub handler
        code = (
            "# End experiment %(name)s from %(file)s\n"
            "%(name)s.status = FINISHED\n"
            "%(name)s.tStop = t\n"
        )
        buff.writeIndentedLines(code % self.params)
