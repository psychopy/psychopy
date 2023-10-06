from .. import BaseStandaloneRoutine
from pathlib import Path
from psychopy.localization import _translate


class UnknownRoutine(BaseStandaloneRoutine):
    categories = ['Other']
    targets = []
    iconFile = Path(__file__).parent / "unknown.png"
    label = _translate("Unknown")
    tooltip = _translate("Unknown routine")

    def __init__(self, exp, name=''):
        BaseStandaloneRoutine.__init__(self, exp, name=name)

    def writeMainCode(self, buff):
        code = (
            "\n"
            "# Unknown standalone routine ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)

    def writeRoutineBeginCodeJS(self, buff):
        code = (
            "\n"
            "// Unknown standalone routine ignored: %(name)s\n"
            "\n"
        )
        buff.writeIndentedLines(code % self.params)
