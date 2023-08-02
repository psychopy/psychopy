import asyncio
import importlib
import os
import sys
import shutil
import threading
import time
import json
import traceback
from functools import partial
from pathlib import Path

from psychopy import experiment, logging, constants, data, core, __version__
from psychopy.tools.arraytools import AliasDict

from psychopy.localization import _translate


class SessionQueue:
    def __init__(self):
        # start off alive
        self._alive = True
        # blank list of partials to run
        self.queue = []
        # blank list of outputs
        self.results = []
        # blank list of Sessions to maintain
        self.sessions = []

    def start(self):
        """
        Start a while loop which will execute any methods added to this queue via
        queueTask as well as the onIdle functions of any sessions registered with
        this queue. This while loop will keep running until `stop` is called, so
        only use this method if you're running with multiple threads!
        """
        self._alive = True
        # process any calls
        while self._alive:
            # empty the queue of any tasks
            while len(self.queue):
                # run the task
                task = self.queue.pop(0)
                try:
                    retval = task()
                except Exception as err:
                    # send any errors to server
                    tb = traceback.format_exception(type(err), err, err.__traceback__)
                    output = json.dumps({
                        'type': "error",
                        'msg': "".join(tb)
                    })
                else:
                    # process output
                    output = {
                        'method': task.func.__name__,
                        'args': task.args,
                        'kwargs': task.keywords,
                        'returned': retval
                    }
                self.results.append(output)
                # Send to liaisons
                for session in self.sessions:
                    session.sendToLiaison(output)
            # while idle, run idle functions for each session
            for session in self.sessions:
                session.onIdle()
            # take a little time to sleep so tasks on other threads can execute
            time.sleep(0.1)

    def stop(self):
        """
        Stop this queue.
        """
        # stop running the queue
        self._alive = False

    def queueTask(self, method, *args, **kwargs):
        """
        Add a task to this queue, to be executed when next possible.

        Parameters
        ----------
        method : function
            Method to execute
        args : tuple
            Tuple of positional arguments to call `method` with.
        kwargs : dict
            Dict of named arguments to call `method` with.

        Returns
        -------
        bool
            True if added successfully.
        """
        # create partial from supplied method, args and kwargs
        task = partial(method, *args, **kwargs)
        # add partial to queue
        self.queue.append(task)

        return True

    def connectSession(self, session):
        """
        Associate a Session object with this queue, meaning that its onIdle
        method will be called whenever the queue is not running anything else.

        Parameters
        ----------
        session : Session
            Session to associate with this queue.

        Returns
        -------
        bool
            True if associated successfully.
        """
        # add session to list of sessions whose onIdle function to call
        self.sessions.append(session)

    def disconnectSession(self, session):
        """
        Remove association between a Session object and this queue, meaning
        that its onIdle method will not be called by the queue.

        Parameters
        ----------
        session : Session
            Session to disconnect from this queue.

        Returns
        -------
        bool
            True if associated successfully.
        """
        # remove session from list of linked sessions
        if session in self.sessions:
            i = self.sessions.index(session)
            self.sessions.pop(i)


_queue = SessionQueue()


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

    def __init__(self,
                 root,
                 dataDir=None,
                 clock="iso",
                 win=None,
                 experiments=None,
                 loggingLevel="info",
                 priorityThreshold=constants.priority.EXCLUDE+1,
                 inputs=None,
                 params=None,
                 liaison=None):
        # Store root and add to Python path
        self.root = Path(root)
        sys.path.insert(1, str(self.root))
        # Create data folder
        if dataDir is None:
            dataDir = self.root / "data" / str(core.Clock().getTime(format="%Y-%m-%d_%H-%M-%S-%f"))
        dataDir = Path(dataDir)
        if not dataDir.is_dir():
            os.makedirs(str(dataDir), exist_ok=True)
        # Store data folder
        self.dataDir = dataDir
        # Create log file
        wallTime = data.getDateStr(fractionalSecondDigits=6)
        self.logFile = logging.LogFile(
            dataDir / f"session_{wallTime}.log",
            level=getattr(logging, loggingLevel.upper())
        )
        # Store priority threshold
        self.priorityThreshold = priorityThreshold
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
        # Setup Session clock
        if clock in (None, "float"):
            clock = core.Clock()
        elif clock == "iso":
            clock = core.Clock(format=str)
        elif isinstance(clock, str):
            clock = core.Clock(format=clock)
        self.sessionClock = clock
        # Store params as an aliased dict
        if params is None:
            params = {}
        self.params = AliasDict(params)
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
            True if this Session was started safely.
        """
        # register self with queue
        _queue.connectSession(self)
        # start queue if we're in the main branch and it's not alive yet
        if threading.current_thread() == threading.main_thread() and not _queue._alive:
            _queue.start()

        return True

    def onIdle(self):
        """
        Function to be called continuously while a SessionQueue is idle.

        Returns
        -------
        bool
            True if this Session was stopped safely.
        """
        if self.win is not None and not self.win._closed:
            # Show waiting message
            self.win.showMessage(_translate(
                "Waiting to start..."
            ))
            self.win.color = "grey"
            # Flip the screen
            self.win.flip()
            # Flush log
            self.logFile.logger.flush()

    def stop(self):
        """
        Stop this Session running the queue. Not recommended unless running
        across multiple threads.
        """
        _queue.disconnectSession(self)

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
                dst=str(newFolder),
                dirs_exist_ok=True
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
        if "psyexp" in file.suffix:
            exp = experiment.Experiment()
            exp.loadFromXML(file)
            script = exp.writeScript(target="PsychoPy")
            pyFile.write_text(script, encoding="utf8")
        # Handle if key is None
        if key is None:
            key = str(file.relative_to(self.root))
        # Check that first part of import path isn't the name of an already existing module
        try:
            isPackage = importlib.import_module(relPath[0])
            # If we imported successfully, check that the module imported is in the root dir
            if not hasattr(isPackage, "__file__") or not isPackage.__file__.startswith(str(self.root)):
                raise NameError(_translate(
                    "Experiment could not be loaded as name of folder {} is also the name of an installed Python "
                    "package. Please rename."
                ).format(self.root / relPath[0]))
        except ImportError:
            # If we can't import, it's not a package and so we're good!
            pass
        # Import python file
        self.experiments[key] = importlib.import_module(importPath)

        return True

    def getStatus(self):
        """
        Get an overall status flag for this Session. Will be one of either:

        Returns
        -------
        int
            A value `psychopy.constants`, either:
            - NOT_STARTED: If no experiment is running
            - STARTED: If an experiment is running
            - PAUSED: If an experiment is paused
            - FINISHED: If an experiment is in the process of terminating
        """
        if self.currentExperiment is None:
            # If no current experiment, return NOT_STARTED
            return constants.NOT_STARTED
        else:
            # Otherwise, return status of experiment handler
            return self.currentExperiment.status

    def getPsychoPyVersion(self):
        return __version__

    def getTime(self, format=str):
        """
        Get time from this Session's clock object.

        Parameters
        ----------
        format : type, str or None
            Can be either:
            - `float`: Time will return as a float as number of seconds
            - time format codes: Time will return as a string in that format, as in time.strftime
            - `str`: Time will return as a string in ISO 8601 (YYYY-MM-DD_HH:MM:SS.mmmmmmZZZZ)
            - `None`: Will use the Session clock object's `defaultStyle` attribute

        Returns
        -------
        str or float
            Time in format requested.
        """
        return self.sessionClock.getTime(format=format)

    def getExpInfoFromExperiment(self, key, sessionParams=True):
        """
        Get the global-level expInfo object from one of this Session's experiments. This will contain all of
        the keys needed for this experiment, alongside their default values.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        sessionParams : bool
            Should expInfo be extended with params from the Session, overriding experiment params
            where relevant (True, default)? Or return expInfo as it is in the experiment (False)?

        Returns
        -------
        dict
            Experiment info dict
        """
        # Get params from experiment
        expInfo = self.experiments[key].expInfo
        if sessionParams:
            # If alias of a key in params exists in expInfo, delete it
            for key in self.params.aliases:
                if key in expInfo:
                    del expInfo[key]
            # Replace with Session params
            for key in self.params:
                expInfo[key] = self.params[key]

        return expInfo

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
            _queue.queueTask(
                self.setupWindowFromExperiment,
                key, expInfo=expInfo
            )
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
            _queue.queueTask(
                self.setupWindowFromParams,
                params
            )
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

    def setupInputsFromExperiment(self, key, expInfo=None, thisExp=None, blocking=True):
        """
        Setup inputs for this Session via the 'setupInputs` method from one of this Session's experiments.

        Parameters
        ----------
        key : str
            Key by which the experiment is stored (see `.addExperiment`).
        expInfo : dict
            Information about the experiment, created by the `setupExpInfo` function.
        thisExp : psychopy.data.ExperimentHandler
            Handler object for this experiment, contains the data to save and information about where to save it to.
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
            _queue.queueTask(
                self.setupInputsFromExperiment,
                key, expInfo=expInfo
            )
            return True

        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Run the setupInputs method
        self.inputs = self.experiments[key].setupInputs(expInfo=expInfo, thisExp=thisExp, win=self.win)

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
            _queue.queueTask(
                self.addKeyboardFromParams,
                name, params
            )
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
        err = None
        # If not in main thread and not requested blocking, use queue and return now
        if threading.current_thread() != threading.main_thread() and not blocking:
            # The queue is emptied each iteration of the while loop in `Session.start`
            _queue.queueTask(
                self.runExperiment,
                key, expInfo=expInfo
            )
            return True

        if expInfo is None:
            expInfo = self.getExpInfoFromExperiment(key)
        # Setup data for this experiment
        thisExp = self.experiments[key].setupData(expInfo=expInfo, dataDir=str(self.dataDir))
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
        self.setupInputsFromExperiment(key, expInfo=expInfo, thisExp=thisExp)
        # Log start
        logging.info(_translate(
            "Running experiment via Session: name={key}, expInfo={expInfo}"
        ).format(key=key, expInfo=expInfo))
        # Run this experiment
        try:
            self.experiments[key].run(
                expInfo=expInfo,
                thisExp=thisExp,
                win=self.win,
                inputs=self.inputs,
                globalClock=self.sessionClock,
                thisSession=self
            )
        except Exception as _err:
            err = _err
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
        # Raise any errors now
        if err is not None:
            raise err
        # Log finished and flush logs
        logging.info(_translate(
            "Finished running experiment via Session: name={key}, expInfo={expInfo}"
        ).format(key=key, expInfo=expInfo))
        logging.flush()
        # Send finished data to liaison
        if self.liaison is not None:
            self.sendToLiaison({
                    'type': "experiment_status",
                    'name': thisExp.name,
                    'status': thisExp.status
                })

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
                _translate("Could not stop experiment as there is none "
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
            _queue.queueTask(
                self.saveExperimentData,
                key, thisExp=thisExp
            )
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
        # save to Session folder
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

    def addAnnotation(self, value):
        """
        Add an annotation in the data file at the current point in the
        experiment and to the log.

        Parameters
        ----------
        value : str
            Value of the annotation

        Returns
        -------
        bool
            True if completed successfully
        """
        # add to experiment data if there's one running
        if hasattr(self.currentExperiment, "addAnnotation"):
            # annotate
            self.currentExperiment.addAnnotation(value)
        # log regardless
        logging.info(value)

        return True

    def addData(self, name, value, row=None, priority=None):
        """
        Add data in the data file at the current point in the experiment, and to the log.

        Parameters
        ----------
        name : str
            Name of the column to add data as.
        value : any
            Value to add
        row : int or None
            Row in which to add this data. Leave as None to add to the current entry.
        priority : int
            Priority value to set the column to - higher priority columns appear nearer to the start of
            the data file. Use values from `constants.priority` as landmark values:
            - CRITICAL: Always at the start of the data file, generally reserved for Routine start times
            - HIGH: Important columns which are near the front of the data file
            - MEDIUM: Possibly important columns which are around the middle of the data file
            - LOW: Columns unlikely to be important which are at the end of the data file
            - EXCLUDE: Always at the end of the data file, actively marked as unimportant

        Returns
        -------
        bool
            True if completed successfully
        """
        # add to experiment data if there's one running
        if hasattr(self.currentExperiment, "addData"):
            # add
            self.currentExperiment.addData(name, value, row=row, priority=priority)
        # log regardless
        logging.data(f"NAME={name}, PRIORITY={priority}, VALUE={value}")

        return True

    def sendExperimentData(self, key=None):
        """
        Send last ExperimentHandler for an experiment to liaison. If no experiment is given, sends the currently
        running experiment.

        Parameters
        ----------
        key : str or None
            Name of the experiment whose data to send, or None to send the current experiment's data.

        Returns
        -------
        bool
            True if data was sent, otherwise False
        """
        # Skip if there's no liaison
        if self.liaison is None:
            return

        # Sub None for current
        if key is None and self.currentExperiment is not None:
            key = self.currentExperiment.name
        elif key is None:
            key = self.runs[-1].name
        # Get list of runs (including current)
        runs = self.runs.copy()
        if self.currentExperiment is not None:
            runs.append(self.currentExperiment)
        # Get last experiment data
        for run in reversed(runs):
            if run.name == key:
                # Send experiment data
                self.sendToLiaison(run)
                return True

        # Return False if nothing sent
        return False

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
            value = value.getJSON(priorityThreshold=self.priorityThreshold)
        # Convert to JSON
        if not isinstance(value, str):
            value = json.dumps(value)
        # Send
        asyncio.run(self.liaison.broadcast(message=value))

    def close(self):
        """
        Safely close the current session. This will end the Python instance.
        """
        # if there is a Liaison object, re-register Session class
        if self.liaison is not None:
            self.liaison.registerClass(Session, "session")
        # close any windows
        if self.win is not None:
            self.win.close()
            self.win = None
        # delete self
        del self


if __name__ == "__main__":
    """
    Create a Session with parameters passed by command line.
    
    Parameters
    ----------
    --root
        Root directory for the Session
    --host
        Port address of host server (if any)
    --timing
        How to handle timing, can be either:
        - "float": Start a timer when Session is created and do timing relative to that (default)
        - "iso": Do timing via wall clock in ISO 8601 format 
        - any valid strftime string: Do timing via wall clock in the given format
    --session-data-dir
        Folder to store all data from this Session in, including the log file.
    """
    # Parse args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", dest="host")
    args, _ = parser.parse_known_args()

    if ":" in str(args.host):
        host, port = str(args.host).split(":")
        # Import liaison
        from psychopy import liaison
        # Create liaison server
        liaisonServer = liaison.WebSocketServer()
        # Add session to liaison server
        liaisonServer.registerClass(Session, "session")
        # Register queue with liaison
        liaisonServer.registerMethods(_queue, "SessionQueue")
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
        # Start processing script queue
        _queue.start()
    else:
        liaisonServer = None
