"""
Helper script to quickly update all Builder demos to be saved in the current version.
"""

from pathlib import Path
from psychopy.experiment import Experiment

# get root demos folder
root = Path(__file__).parent

# iterate through all psyexp files
for file in root.glob("**/*.psyexp"):
    # load experiment
    exp = Experiment.fromFile(file)
    # save experiment
    exp.saveToXML(file, makeLegacy=False)
