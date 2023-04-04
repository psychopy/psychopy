import importlib
import os
import sys
import shutil
from pathlib import Path

from psychopy import experiment, logging, constants, data
import json
from psychopy.localization import _translate


class Session:
    """
    Parameters
    ----------
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

    experiments : dict or None
        Dict of name:experiment pairs which this Session can run. Each should be the file path of a .psyexp
        file, contained somewhere within the folder supplied for `root`. Paths can be absolute or
        relative to the root folder. Leave as None for a blank dict, experiments can be added
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
            for nm, exp in experiments.items():
                self.addExperiment(exp, key=nm)
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
        # Start off with no current experiment
        self.currentExperiment = None

    def addExperiment(self, file, key=None, folder=None):
        """
        Register an experiment with this Session object, to be referred to
        later by a given key.

        Parameters
        ----------
        file : str, Path
            Path to the experiment (psyexp) file or script (py) of a Python
            experiment.
        key : str
            Key to refer to this experiment by once added. Leave as None to use
            file path relative to session root.
        folder : str, Path
            Folder for this project, if adding from outside of the root folder
            this entire folder will be moved. Leave as None to use the parent
            folder of `file`.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        # Path-ise file
        file = Path(file)
        if not file.is_absolute():
            # If relative, treat as relative to root
            file = self.root / file
        # Get project folder if not specified
        if folder is None:
            folder = file.parent
        # If folder isn't within root, copy it to root and show a warning
        if not str(folder).startswith(str(self.root)):
            # Warn user that some files are going to be copied
            logging.warning(_translate(
                f"Experiment '{file.stem}' is located outside of the root folder for this Session. All files from its "
                f"experiment folder ('{folder.stem}') will be copied to the root folder and the experiment will run "
                f"from there."
            ))
            # Create new folder
            newFolder = self.root / folder.stem
            # Copy files to it
            shutil.copytree(
                src=str(folder),
                dst=str(newFolder)
            )
            # Store new locations
            file = newFolder / file.relative_to(folder)
            folder = newFolder
            # Notify user than files are copied
            logging.info(_translate(
                f"Experiment '{file.stem}' and its experiment folder ('{folder.stem}') have been copied to {newFolder}"
            ))
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
        # Handle if key is None
        if key is None:
            key = str(file.relative_to(self.root))
        # Import python file
        self.experiments[key] = importlib.import_module(importPath)

        return True

    def getExpInfoFromExperiment(self, key):
        """
        Get the global-level expInfo object from one of this Session's experiments. This will contain all of
        the keys needed for this experiment, alongside their default values.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        return self.experiments[key].expInfo

    def showExpInfoDlgFromExperiment(self, key, expInfo=None):
        """
        Update expInfo for this Session via the 'showExpInfoDlg` method from one of this Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Run the expInfo method
        expInfo = self.experiments[key].showExpInfoDlg(expInfo=expInfo)

        return expInfo

    def setupWindowFromExperiment(self, key, expInfo=None):
        """
        Setup the window for this Session via the 'setupWindow` method from one of this
        Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Run the setupWindow method
        self.win = self.experiments[key].setupWindow(expInfo=expInfo, win=self.win)

        return True

    def setupWindowFromParams(self, params):
        """
        Create/setup a window from a dict of parameters

        Parameters
        ----------
        params : dict
            Dict of parameters to create the window from, keys should be from the
            __init__ signature of psychopy.visual.Window

        Returns
        -------
        bool or None
            True if the operation completed successfully
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

    def setupInputsFromExperiment(self, key, expInfo=None):
        """
        Setup inputs for this Session via the 'setupInputs` method from one of this Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Run the setupInputs method
        self.inputs = self.experiments[key].setupInputs(expInfo=expInfo, win=self.win)

        return True

    def addKeyboardFromParams(self, name, params):
        """
        Add a keyboard to this session's inputs dict from a dict of params.

        Parameters
        ----------
        name : str
            Name of this input, what to store it under in the inputs dict.

        params : dict
            Dict of parameters to create the keyboard from, keys should be from the
            __init__ signature of psychopy.hardware.keyboard.Keyboard

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        # Create keyboard
        from psychopy.hardware.keyboard import Keyboard
        self.inputs[name] = Keyboard(**params)

        return True

    def runExperiment(self, key, expInfo=None):
        """
        Run the `setupData` and `run` methods from one of this Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Setup data for this experiment
        thisExp = self.experiments[key].setupData(expInfo=expInfo)
        # Mark ExperimentHandler as current
        self.currentExperiment = thisExp
        # Setup window for this experiment
        self.setupWindowFromExperiment(key=key)
        self.win.flip()
        self.win.flip()
        # Hold all autodraw stimuli
        self.win.stashAutoDraw()
        # Setup logging
        self.experiments[key].run.__globals__['logFile'] = self.logFile
        # Run this experiment
        self.experiments[key].run(
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
        # Mark ExperimentHandler as no longer current
        self.currentExperiment = None

        return True

    def pauseExperiment(self):
        """
        Pause the currently running experiment.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        # warn and return failed if no experiment is running
        if self.currentExperiment is None:
            logging.warn(
                _translate("Could not pause experiment as there is none "
                           "running.")
            )
            return False

        # set ExperimentHandler status to PAUSED
        self.currentExperiment.pause()

        return True

    def resumeExperiment(self):
        """
        Resume the currently paused experiment.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        # warn and return failed if no experiment is running
        if self.currentExperiment is None:
            logging.warn(
                _translate("Could not resume experiment as there is none "
                           "running or paused.")
            )
            return False
        # set ExperimentHandler status to STARTED
        self.currentExperiment.resume()

        return True

    def stopExperiment(self):
        """
        Stop the currently running experiment.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        # warn and return failed if no experiment is running
        if self.currentExperiment is None:
            logging.warn(
                _translate("Could not pause experiment as there is none "
                           "running.")
            )
            return False
        self.currentExperiment.stop()

        return True

    # def recycleTrial(self, thisExp, trial):
    #     pass

    def saveExperimentData(self, key, thisExp):
        """
        Run the `saveData` method from one of this Session's experiments, on a given ExperimentHandler.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        thisExp : psychopy.data.ExperimentHandler
            ExperimentHandler object to save the data from.

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        self.experiments[key].saveData(thisExp)

        return True

    def sendToLiaison(self, value):
        """
        Send data to this Session's `Liaison` object.

        Parameters
        ----------
        value : str, dict, psychopy.data.ExperimentHandler
            Data to send - this can either be a single string, a dict of strings, or an
            ExperimentHandler (whose data will be sent)

        Returns
        -------
        bool or None
            True if the operation completed successfully
        """
        if self.liaison is None:
            logging.warn(_translate(
                "Could not send data to liaison server as none is initialised for this Session."
            ))
            return
        # If ExperimentHandler, get its data as a list of dicts
        if isinstance(value, data.ExperimentHandler):
            value = value.entries
        # Convert to JSON
        value = json.dumps(value)
        # Send
        self.liaison.broadcast(message=value)

    def close(self):
        """
        Safely close the current session. This will end the Python instance.
        """
        sys.exit()


if __name__ == "__main__":
    # Parse args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", dest="root")
    parser.add_argument("--host", dest="host")
    args = parser.parse_args()
    # Create session
    session = Session(
        root=args.root
    )
    if ":" in str(args.host):
        host, port = str(args.host).split(":")
        # Import liaison
        from psychopy import liaison
        # Create liaison server
        liaisonServer = liaison.WebSocketServer()
        # Add session to liaison server
        liaisonServer.registerMethods(session, "session")
        # Start liaison server
        liaisonServer.start(host=host, port=port)
    else:
        liaisonServer = None
