from .. import BaseStandaloneRoutine
from pathlib import Path


class UnknownRoutine(BaseStandaloneRoutine):
    categories = ['Custom']
    targets = []
    iconFile = Path(__file__).parent / "unknown.png"
    tooltip = "Unknown routine"

    def __init__(self, name, exp):
        BaseStandaloneRoutine.__init__(self, name, exp)
        self.type = 'UnknownStandaloneRoutine'
