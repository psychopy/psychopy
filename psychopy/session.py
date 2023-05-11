import importlib
import os
import sys
import shutil
import threading
import time
import traceback
from pathlib import Path

from psychopy import experiment, logging, constants, data
import json
from psychopy.localization import _translate


class Session:
    """
    A Session is from which you can run multiple PsychoPy experiments, so long
    as they are stored within the same folder. Session uses a persistent Window
    and inputs across experiments, meaning that you don't have to keep closing
    and reopening windows to run multiple experiments.

    Through the use of multithreading, an experiment running via a Session can
    be sent commands and have variables changed while running. Methods of
    Session can be called from a second thread, meaning they don't have to wait
    for `runExperiment` to return on the main thread. For example, you could
    pause an experiment after 10s like so:

    ```
    # define a function to run in a second thread
    def stopAfter10s(thisSession):
        # wait 10s
        time.sleep(10)
        # pause
        thisSession.pauseExperiment()
    # create a second thread
    thread = threading.Thread(
        target=stopAfter10s,
        args=(thisSession,)
    )
    # start the second thread
    thread.start()
    # run the experiment (in main thread)
    thisSession.runExperiment("testExperiment")
    ```

    When calling methods of Session which have the parameter `blocking` from
    outside of the main thread, you can use `blocking=False` to force them to
    return immediately and, instead of executing, add themselves to a queue to
    be executed in the main thread by a while loop within the `start` function.
    This is important for methods like `runExperiment` or
    `setupWindowFromParams` which use OpenGL and so need to be run in the
    main thread. For example, you could alternatively run the code above like
    this:

    ```
    # define a function to run in a second thread
    def stopAfter10s(thisSession):
        # start the experiment in the main thread
        thisSession.runExperiment("testExperiment", blocking=False)
        # wait 10s
        time.sleep(10)
        # pause
        thisSession.pauseExperiment()
    # create a second thread
    thread = threading.Thread(
        target=stopAfter10s,
        args=(thisSession,)
    )
    # start the second thread
    thread.start()
    # start the Session so that non-blocking methods are executed
    thisSession.start()
    ```


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

    _queue = []

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

    def start(self):
        """
        Start this Session running its queue. Not recommended unless running
        across multiple threads.

        Returns
        -------
        bool
            True if this Session was stopped safely.
        """
        # Create attribute to keep self running
        self._alive = True
        # Show waiting message
        if self.win is not None:
            self.win.showMessage(_translate(
                "Waiting to start..."
            ))
            self.win.color = "grey"
        # Process any calls
        while self._alive:
            # Empty the queue of any tasks
            while len(self._queue):
                method, args, kwargs = self._queue.pop(0)
                method(*args, **kwargs)
            # Flip the screen and give a little time to sleep
            if self.win is not None:
                self.win.flip()
                time.sleep(0.1)

    def stop(self):
        """
        Stop this Session running its queue. Not recommended unless running
        across multiple threads.
        """
        self._alive = False

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

    def setupWindowFromExperiment(self, key, expInfo=None, blocking=True):
        """
        Setup the window for this Session via the 'setupWindow` method from one of this
        Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully
        """
        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            self._queue.append((
                self.setupWindowFromExperiment,
                (key,),
                {'expInfo': expInfo}
            ))
            return True

        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Run the setupWindow method
        self.win = self.experiments[key].setupWindow(expInfo=expInfo, win=self.win)
        # Set window title to signify that we're in a Session
        self.win.title = "PsychoPy Session"

        return True

    def setupWindowFromParams(self, params, blocking=True):
        """
        Create/setup a window from a dict of parameters

        Parameters
        ----------
        params : dict
            Dict of parameters to create the window from, keys should be from the
            __init__ signature of psychopy.visual.Window
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully
        """
        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            self._queue.append((
                self.setupWindowFromParams,
                (params,),
                {}
            ))
            return True

        if self.win is None:
            # If win is None, make a Window
            from psychopy.visual import Window
            self.win = Window(**params)
            self.win.showMessage(_translate(
                "Waiting to start..."
            ))
        else:
            # otherwise, just set the attributes which are safe to set
            self.win.color = params.get('color', self.win.color)
            self.win.colorSpace = params.get('colorSpace', self.win.colorSpace)
            self.win.backgroundImage = params.get('backgroundImage', self.win.backgroundImage)
            self.win.backgroundFit = params.get('backgroundFit', self.win.backgroundFit)
            self.win.units = params.get('units', self.win.units)
        # Set window title to signify that we're in a Session
        self.win.title = "PsychoPy Session"

        return True

    def setupInputsFromExperiment(self, key, expInfo=None, blocking=True):
        """
        Setup inputs for this Session via the 'setupInputs` method from one of this Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully
        """
        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            self._queue.append((
                self.setupInputsFromExperiment,
                (key,),
                {'expInfo': expInfo}
            ))
            return True

        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Run the setupInputs method
        self.inputs = self.experiments[key].setupInputs(expInfo=expInfo, win=self.win)

        return True

    def addKeyboardFromParams(self, name, params, blocking=True):
        """
        Add a keyboard to this session's inputs dict from a dict of params.

        Parameters
        ----------
        name : str
            Name of this input, what to store it under in the inputs dict.
        params : dict
            Dict of parameters to create the keyboard from, keys should be from the
            __init__ signature of psychopy.hardware.keyboard.Keyboard
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully
        """
        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            self._queue.append((
                self.addKeyboardFromParams,
                (name, params),
                {}
            ))
            return True

        # Create keyboard
        from psychopy.hardware.keyboard import Keyboard
        self.inputs[name] = Keyboard(**params)

        return True

    def runExperiment(self, key, expInfo=None, blocking=True):
        """
        Run the `setupData` and `run` methods from one of this Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully
        """
        # Start off assuming everything is fine
        success = True

        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            self._queue.append((
                self.runExperiment,
                (key,),
                {'expInfo': expInfo}
            ))
            return success

        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Setup data for this experiment
        thisExp = self.experiments[key].setupData(expInfo=expInfo)
        thisExp.name = key
        # Mark ExperimentHandler as current
        self.currentExperiment = thisExp
        # Hide Window message
        self.win.hideMessage()
        # Setup window for this experiment
        self.setupWindowFromExperiment(key=key)
        self.win.flip()
        self.win.flip()
        # Hold all autodraw stimuli
        self.win.stashAutoDraw()
        # Setup logging
        self.experiments[key].run.__globals__['logFile'] = self.logFile
        # Setup inputs
        self.setupInputsFromExperiment(key, expInfo=expInfo)
        # Run this experiment
        try:
            self.experiments[key].run(
                expInfo=expInfo,
                thisExp=thisExp,
                win=self.win,
                inputs=self.inputs,
                thisSession=self
            )
        except Exception as err:
            # Don't raise errors from experiment as this will terminate Python
            # process, instead note that run failed and print error to log
            success = False
            # Get traceback
            tb = traceback.format_exception(type(err), err, err.__traceback__)
            msg = "".join(tb)
            # Print traceback in log
            logging.critical(
                _translate("Experiment failed. \n") +
                msg
            )
            # If we have a liaison, send traceback to it
            if self.liaison is not None:
                self.sendToLiaison(msg)
        # Reinstate autodraw stimuli
        self.win.retrieveAutoDraw()
        # Restore original chdir
        os.chdir(str(self.root))
        # Store ExperimentHandler
        self.runs.append(thisExp)
        # Save data
        self.saveCurrentExperimentData()
        # Mark ExperimentHandler as no longer current
        self.currentExperiment = None
        # Display waiting text
        self.win.showMessage(_translate(
            "Waiting to start..."
        ))
        self.win.color = "grey"

        return success

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

    def saveExperimentData(self, key, thisExp=None, blocking=True):
        """
        Run the `saveData` method from one of this Session's experiments, on a
        given ExperimentHandler.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        thisExp : psychopy.data.ExperimentHandler
            ExperimentHandler object to save the data from. If None, save the
            last run of the given experiment.
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully
        """
        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            self._queue.append((
                self.saveExperimentData,
                (key,),
                {'thisExp': thisExp}
            ))
            return True

        # get last run
        if thisExp is None:
            # copy list of runs in reverse
            runs = self.runs.copy()
            runs.reverse()
            # iterate through runs, starting at the end
            for run in runs:
                # use the first run to match given exp
                if run.name == key:
                    thisExp = run
                    break

        self.experiments[key].saveData(thisExp)

        return True

    def saveCurrentExperimentData(self, blocking=True):
        """
        Call `.saveExperimentData` on the currently running experiment - if
        there is one.

        Parameters
        ----------
        blocking : bool
            Should calling this method block the current thread?

            If True (default), the method runs as normal and won't return until
            completed.
            If False, the method is added to a `queue` and will be run by the
            while loop within `Session.start`. This will block the main thread,
            but won't block the thread this method was called from.

            If not using multithreading, this value is ignored. If you don't
            know what multithreading is, you probably aren't using it - it's
            difficult to do by accident!

        Returns
        -------
        bool or None
            True if the operation completed/queued successfully, False if there
            was no current experiment running
        """
        if self.currentExperiment is None:
            return False

        return self.saveExperimentData(
            key=self.currentExperiment.name,
            thisExp=self.currentExperiment,
            blocking=blocking
        )

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
        # Create thread to run liaison server in
        liaisonThread = threading.Thread(
            target=liaisonServer.start,
            kwargs={
                'host': host,
                'port': port,
            }
        )
        # Start liaison server
        liaisonThread.start()
        # Start Session
        session.start()
    else:
        liaisonServer = None
