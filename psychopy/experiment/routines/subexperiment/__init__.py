from psychopy.alerts import alert
from psychopy.tools.versionchooser import _translate
from .. import BaseStandaloneRoutine
from pathlib import Path

from ... import Param, Experiment
from ...loops import LoopInitiator, LoopTerminator


class SubExperimentRoutine(BaseStandaloneRoutine):
    categories = ['Custom']
    targets = ["PsychoPy"]
    iconFile = Path(__file__).parent / "subexp.png"
    tooltip = "Inject another experiment into this one"
    beta = True

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
        # Check element against namespace
        for item in subexp.flow:
            if hasattr(item, "name"):
                if self.exp.namespace.exists(item.name):
                    alert(4410, strFields={'name': self.params['name'], 'clash': f"<{item.__class__.__name__}: {item.name}>"})
            if isinstance(item, list):
                for comp in item:
                    if self.exp.namespace.exists(comp.params['name'].val):
                        alert(4410, strFields={'name': self.params['name'], 'clash': f"<{comp.__class__.__name__}: {comp.params['name']}>"})
        # Make sub handler
        code = (
            "\n"
            "# Run experiment %(name)s from %(file)s\n"
            "%(name)s = data.SubExperimentHandler(thisExp)\n"
            "%(name)s.status = STARTED\n"
            "%(name)s.tStart = globalClock.getTime()\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)
        # Write each item in experiment flow
        subexp.flow.writeBody(buff)
        # End sub handler
        code = (
            "# End experiment %(name)s from %(file)s\n"
            "%(name)s.status = FINISHED\n"
            "%(name)s.tStop = globalClock.getTime()\n"
        )
        buff.writeIndentedLines(code % self.params)
