import importlib
import sys
from pathlib import Path
import shutil

from psychopy import experiment


class PsychopySession:
    def __init__(self,
                 expInfo,
                 win,
                 inputs,
                 root,
                 experiments=None):
        self.expInfo = expInfo
        self.win = win
        self.inputs = inputs
        # Add root to Python path
        self.root = Path(root)
        sys.path.insert(1, str(self.root))
        # Add experiments
        self.experiments = {}
        if experiments is not None:
            for exp in experiments:
                self.addExperiment(exp)

    def close(self):
        shutil.rmtree(self.root)

    def addExperiment(self, file, folder=None):
        # Path-ise file
        file = Path(file)
        if not file.is_absolute():
            # If relative, treat as relative to root
            file = self.root / file
        # Get project folder
        if folder is None:
            folder = file.parent
        # Initialise as module
        (folder / "__init__.py").write_text("")
        # Construct relative path starting from root
        relPath = []
        for parent in file.relative_to(self.root).parents:
            if parent.stem:
                relPath.append(parent.stem)
        relPath.reverse()
        # Add experiment name
        relPath.append(file.stem)
        # Join with . so it's a valid import path
        importPath = ".".join(relPath)
        # Write experiment as Python script
        exp = experiment.Experiment()
        exp.loadFromXML(file)
        script = exp.writeScript(target="PsychoPy")
        (file.parent / (file.stem + ".py")).write_text(script, encoding="utf8")
        # Import python file
        self.experiments[file.stem] = importlib.import_module(importPath)

    def runExperiment(self, stem):
        thisExp = self.experiments[stem].setupData(self.expInfo)
        self.experiments[stem].run(expInfo=self.expInfo, thisExp=thisExp, win=self.win, inputs=self.inputs)
