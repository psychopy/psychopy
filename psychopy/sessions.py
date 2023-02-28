import importlib
import sys
from pathlib import Path
import shutil

from psychopy import experiment, logging


class PsychopySession:
    """
    Parameters
    ==========
    root : str or pathlib.Path
        Root folder for this session - should contain all of the experiments to be run.

    loggingLevel : str
    How much output do you want in the log files? Should be one of the following:
        - 'error'
        - 'warning'
        - 'data'
        - 'exp'
        - 'info'
        - 'debug'
    ('error' is fewest messages, 'debug' is most)

    expInfo : dict, str or None
        Dictionary in which to store information for this session. Leave as None for a blank dict,
        or supply the name of an experiment to use the `setupExpInfo` method from that experiment.

    inputs: dict, str or None
        Dictionary of input objects for this session. Leave as None for a blank dict, or supply the
        name of an experiment to use the `setupInputs` method from that experiment.

    win : psychopy.visual.Window, str or None
        Window in which to run experiments this session. Leave as None for a blank dict, or supply
        the name of an experiment to use the `setupInputs` method from that experiment.

    experiments : list or None
        List of experiments which this Session can run. Each should be the file path of a .psyexp
        file, contained somewhere within the folder supplied for `root`. Paths can be absolute or
        relative to the root folder. Leave as None for a blank list, experiments can be added
        later on via `addExperiment()`.
    """
    def __init__(self,
                 root,
                 loggingLevel="info",
                 expInfo=None,
                 inputs=None,
                 win=None,
                 experiments=None):
        # Store root and add to Python path
        self.root = Path(root)
        sys.path.insert(1, str(self.root))
        # Create log file
        self.logFile = logging.LogFile(
            self.root / (self.root.stem + '.log'),
            level=getattr(logging, loggingLevel)
        )
        # Add experiments
        self.experiments = {}
        if experiments is not None:
            for exp in experiments:
                self.addExperiment(exp)
        # Store/create expInfo dict
        self.expInfo = {}
        if isinstance(expInfo, dict):
            self.expInfo = expInfo
        elif expInfo in self.experiments:
            # If expInfo is the name of an experiment, setup from that experiment's method
            self.setupExpInfoFromExperiment(expInfo)
        # Store/create window object
        self.win = win
        if win in self.experiments:
            # If win is the name of an experiment, setup from that experiment's method
            self.setupWindowFromExperiment(win)
        # Store/create inputs dict
        self.inputs = {}
        if isinstance(inputs, dict):
            self.inputs = inputs
        elif inputs in self.experiments:
            # If inputs is the name of an experiment, setup from that experiment's method
            self.setupInputsFromExperiment(inputs)

    def addExperiment(self, file, folder=None):
        # Path-ise file
        file = Path(file)
        if not file.is_absolute():
            # If relative, treat as relative to root
            file = self.root / file
        # Get project folder if not specified
        if folder is None:
            folder = file.parent
        # Initialise as module
        moduleInitFile = (folder / "__init__.py")
        if not moduleInitFile.is_file():
            moduleInitFile.write_text("")
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
        pyFile = file.parent / (file.stem + ".py")
        if not pyFile.is_file():
            exp = experiment.Experiment()
            exp.loadFromXML(file)
            script = exp.writeScript(target="PsychoPy")
            pyFile.write_text(script, encoding="utf8")
        # Import python file
        self.experiments[file.stem] = importlib.import_module(importPath)

    def setupExpInfoFromExperiment(self, stem):
        """
        Update expInfo for this Session via the 'setupExpInfo` method from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        """
        # Run the expInfo method
        self.expInfo = self.experiments[stem].setupExpInfo()

    def setupWindowFromExperiment(self, stem):
        """
        Setup the window for this Session via the 'setupWindow` method from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        """
        # Run the setupWindow method
        self.win = self.experiments[stem].setupWindow(expInfo=self.expInfo, win=self.win)

    def setupInputsFromExperiment(self, stem):
        """
        Setup inputs for this Session via the 'setupInputs` method from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        """
        # Run the setupInputs method
        self.inputs = self.experiments[stem].setupInputs(expInfo=self.expInfo, win=self.win)

    def runExperiment(self, stem):
        """
        Run the `setupData` and `run` methods from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        """
        # Setup data for this experiment
        thisExp = self.experiments[stem].setupData(self.expInfo)
        # Setup logging
        self.experiments[stem].run.__globals__['logFile'] = self.logFile
        # Run this experiment
        self.experiments[stem].run(
            expInfo=self.expInfo,
            thisExp=thisExp,
            win=self.win,
            inputs=self.inputs
        )

        return thisExp

    def saveDataToExperiment(self, stem, thisExp):
        """
        Run the `saveData` method from one of this Session's experiments, on a given ExperimentHandler.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        thisExp : psychopy.data.ExperimentHandler
            ExperimentHandler object to save the data from.
        """
        self.experiments[stem].saveData(thisExp)
