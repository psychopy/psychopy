import importlib
import os
import sys
from pathlib import Path
import shutil

from psychopy import experiment, logging


class Session:
    """
    Parameters
    ==========
    root : str or pathlib.Path
        Root folder for this session - should contain all of the experiments to be run.

    liaison : liaison.WebSocketServer
        Liaison server from which to receive run commands, if running via a liaison setup.

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
        Dictionary in which to store information for this session. Leave as None for a blank dict.

    inputs: dict, str or None
        Dictionary of input objects for this session. Leave as None for a blank dict, or supply the
        name of an experiment to use the `setupInputs` method from that experiment.

    win : psychopy.visual.Window, str or None
        Window in which to run experiments this session. Supply a dict of parameters to make a Window
        from them, or supply the name of an experiment to use the `setupWindow` method from that experiment.

    experiments : list or None
        List of experiments which this Session can run. Each should be the file path of a .psyexp
        file, contained somewhere within the folder supplied for `root`. Paths can be absolute or
        relative to the root folder. Leave as None for a blank list, experiments can be added
        later on via `addExperiment()`.
    """
    def __init__(self,
                 root,
                 liaison=None,
                 loggingLevel="info",
                 inputs=None,
                 win=None,
                 experiments=None):
        # Store root and add to Python path
        self.root = Path(root)
        sys.path.insert(1, str(self.root))
        # Create log file
        self.logFile = logging.LogFile(
            self.root / (self.root.stem + '.log'),
            level=getattr(logging, loggingLevel.upper())
        )
        # Add experiments
        self.experiments = {}
        if experiments is not None:
            for exp in experiments:
                self.addExperiment(exp)
        # Store/create window object
        self.win = win
        if isinstance(win, dict):
            from psychopy import visual
            self.win = visual.Window(**win)
        if win in self.experiments:
            # If win is the name of an experiment, setup from that experiment's method
            self.win = None
            self.setupWindowFromExperiment(win)
        # Store/create inputs dict
        self.inputs = {
            'defaultKeyboard': None,
            'eyetracker': None
        }
        if isinstance(inputs, dict):
            self.inputs = inputs
        elif inputs in self.experiments:
            # If inputs is the name of an experiment, setup from that experiment's method
            self.setupInputsFromExperiment(inputs)
        # List of ExperimentHandlers from previous runs
        self.runs = []
        # Store ref to liaison object
        self.liaison = liaison

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

        return True

    def getExpInfoFromExperiment(self, stem):
        """
        Get the global-level expInfo object from one of this Session's experiments. This will contain all of
        the keys needed for this experiment, alongside their default values.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        """
        return self.experiments[stem].expInfo

    def showExpInfoDlgFromExperiment(self, stem, expInfo=None):
        """
        Update expInfo for this Session via the 'showExpInfoDlg` method from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(stem)
        # Run the expInfo method
        expInfo = self.experiments[stem].showExpInfoDlg(expInfo=expInfo)

        return expInfo

    def setupWindowFromExperiment(self, stem, expInfo=None):
        """
        Setup the window for this Session via the 'setupWindow` method from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(stem)
        # Run the setupWindow method
        self.win = self.experiments[stem].setupWindow(expInfo=expInfo, win=self.win)

        return True

    def setupWindowFromParams(self, params):
        """
        Create/setup a window from a dict of parameters

        Parameters
        ==========
        params : dict
            Dict of parameters to create the window from, keys should be from the
            __init__ signature of psychopy.visual.Window
        """
        if self.win is None:
            # If win is None, make a Window
            from psychopy.visual import Window
            self.win = Window(**params)
        else:
            # otherwise, just set the attributes which are safe to set
            self.win.color = params.get('color', self.win.color)
            self.win.colorSpace = params.get('colorSpace', self.win.colorSpace)
            self.win.backgroundImage = params.get('backgroundImage', self.win.backgroundImage)
            self.win.backgroundFit = params.get('backgroundFit', self.win.backgroundFit)
            self.win.units = params.get('units', self.win.units)

        return True

    def setupInputsFromExperiment(self, stem, expInfo=None):
        """
        Setup inputs for this Session via the 'setupInputs` method from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(stem)
        # Run the setupInputs method
        self.inputs = self.experiments[stem].setupInputs(expInfo=expInfo, win=self.win)

        return True

    def addKeyboardFromParams(self, name, params):
        """
        Add a keyboard to this session's inputs dict from a dict of params.

        Parameters
        ==========
        name : str
            Name of this input, what to store it under in the inputs dict.

        params : dict
            Dict of parameters to create the keyboard from, keys should be from the
            __init__ signature of psychopy.hardware.keyboard.Keyboard
        """
        # Create keyboard
        from psychopy.hardware.keyboard import Keyboard
        self.inputs[name] = Keyboard(**params)

        return True

    def runExperiment(self, stem, expInfo=None):
        """
        Run the `setupData` and `run` methods from one of this Session's experiments.

        Parameters
        ==========
        stem : str
            Stem of the experiment file - in other words, the name of the experiment.
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(stem)
        # Setup data for this experiment
        thisExp = self.experiments[stem].setupData(expInfo=expInfo)
        # Setup window for this experiment
        self.setupWindowFromExperiment(stem=stem)
        self.win.flip()
        self.win.flip()
        # Hold all autodraw stimuli
        self.win.stashAutoDraw()
        # Setup logging
        self.experiments[stem].run.__globals__['logFile'] = self.logFile
        # Run this experiment
        self.experiments[stem].run(
            expInfo=expInfo,
            thisExp=thisExp,
            win=self.win,
            inputs=self.inputs,
            session=self
        )
        # Reinstate autodraw stimuli
        self.win.retrieveAutoDraw()
        # Restore original chdir
        os.chdir(str(self.root))
        # Store ExperimentHandler
        self.runs.append(thisExp)

        return True

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

        return True


if __name__ == "__main__":
    # Parse args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", dest="root")
    parser.add_argument("--host", dest="host")
    args = parser.parse_args()
    if ":" in str(args.host):
        host, port = str(args.host).split(":")
        # Create liaison server
        try:
            import liaison
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError("Package 'liaison' is needed to run psychopy.session with --host.")
        liaisonServer = liaison.WebSocketServer()
        liaisonServer.start(host=host, port=port)
    else:
        liaisonServer = None
    # Create session
    session = Session(
        root=args.root
    )
