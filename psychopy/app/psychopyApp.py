#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import argparse
import os
import sys
import subprocess

# fix macOS locale-bug on startup: sets locale to LC_ALL (must be defined!)
import psychopy.locale_setup  # noqa


# NB the PsychoPyApp classes moved to _psychopyApp.py as of version 1.78.00
# to allow for better upgrading possibilities from the mac app bundle. this
# file now used solely as a launcher for the app, not as the app itself.


def start_app():
    from psychopy.app import startApp, quitApp
    from psychopy.preferences import prefs

    showSplash = prefs.app['showSplash']
    if '--no-splash' in sys.argv:
        showSplash = False
        del sys.argv[sys.argv.index('--no-splash')]
    _ = startApp(showSplash=showSplash)  # main loop
    quitApp()


def runPyCommand(command, env=None, printOutput=False):
    """Run a Python command in a subprocess using the current Python 
    interpreter and wait for it to complete.

    Parameters
    ----------
    command : list
        The command to run as a list of strings. The first element should be
        the module name to run, followed by any arguments.
    env : dict, optional
        The environment variables to use when running the command. Should be the 
        same as the enviornment variables used to start the app. These are set
        to the current environment if not provided. The default is None.
    printOutput : bool, optional
        Whether to print the output and error messages from the command. The
        default is `False`.

    Returns
    -------
    tuple
        A tuple containing the exit status, output, and error messages from the
        command.

    Examples
    --------
    Run a command to list installed packages:

        import os
        env = os.environ
        status, output, err = runPyCommand(['pip', 'list', '--user'], env=env)

    """
    if env is None:
        env = os.environ  # use default

    cmd = [sys.executable] + command
    proc = subprocess.Popen(cmd, env=env)
    output, err = proc.communicate()  
    status = proc.wait()

    if printOutput:
        if output is not None:
            print(output, file=sys.stdout)
        if err is not None:
            print(err, file=sys.stderr)

    return status, output, err


def getUserPrefsDir():
    """Get the user preferences directory.

    Returns
    -------
    str
        The user preferences directory path.

    """
    # TODO - try and make this work without any psychopy imports
    from psychopy.preferences import prefs
    return prefs.paths['userPrefsDir']


def main():
    """Main entry point for the PsychoPy application.

    This function is the main entry point for the PsychoPy application. It
    handles the command line arguments and starts the application in a
    subprocess.

    It also handles any pre-startup tasks, running them within the same 
    environment as the app itself.

    """
    # Setup the environment variables for running the app
    if '--show-last-log' in sys.argv:
        # Show the last startup log and exit. This reads the last startup log
        # file and prints the contents to the console.
        logFile = os.path.join(getUserPrefsDir(), 'last_app_load.log')
        if not os.path.exists(logFile):
            print("No startup log file found.")

        # open the log file in the default method for the system
        import webbrowser
        webbrowser.open(logFile)

        sys.exit()

    if '-x' in sys.argv:
        # run a .py script from the command line using StandAlone python
        targetScript = sys.argv[sys.argv.index('-x') + 1]
        from psychopy import core
        core.shellCall([sys.executable, os.path.abspath(targetScript)])
        sys.exit()

    if '-v' in sys.argv or '--version' in sys.argv:
        from psychopy import __version__
        msg = ('PsychoPy3, version %s (c)Jonathan Peirce 2018, GNU GPL license'
               % __version__)
        print(msg)
        sys.exit()

    if '-h' in sys.argv or '--help' in sys.argv:
        print("""Starts the PsychoPy3 application.

        Usage:  python PsychoPy.py [options] [file]

        Without options or files provided this starts PsychoPy using prefs to
        decide on the view(s) to open.  If optional [file] is provided action
        depends on the type of the [file]:

        Python script 'file.py' -- opens coder

        Experiment design 'file.psyexp' -- opens builder

        Options:
            -c, --coder, coder       opens coder view only
            -b, --builder, builder   opens builder view only
            -x script.py             execute script.py using StandAlone python

            -v, --version            prints version and exits
            -h, --help               prints this help and exit

            --firstrun               launches configuration wizard
            --no-splash              suppresses splash screen

            --show-last-log          show the last app startup log and exit

        """)
        sys.exit()
    
    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--builder', dest='builder', action="store_true")
    parser.add_argument('-b', dest='builder', action="store_true")
    parser.add_argument('--coder', dest='coder', action="store_true")
    parser.add_argument('-c', dest='coder', action="store_true")
    parser.add_argument('--runner', dest='runner', action="store_true")
    parser.add_argument('-r', dest='runner', action="store_true")
    parser.add_argument('-x', dest='direct', action='store_true')
    view = parser.parse_args()

    while True:  # loop if we exit and want to restart
        # Updated 2024.1.6: as of Python 3, `pythonw` and `python` can be used
        # interchangeably for wxPython applications on macOS with GUI support.
        # The defaults and conda-forge channels no longer install python with a
        # framework build (to do so: `conda install python=3.8 python.app`).
        # Therefore `pythonw` often doesn't exist, and we can just use `python`.
        env = os.environ
        PYTHONW = env.get('PYTHONW', 'False')
        pyw_exe = sys.executable

        if (('| packaged by conda-forge |' in sys.version or '|Anaconda' in sys.version)
                and sys.platform == 'darwin' and sys.version_info >= (3,9)):
            # On macOS with Anaconda, GUI applications used to need to be run using
            # `pythonw`. Since we have no way to determine whether this is currently
            # the case, we run this script again -- ensuring we're definitely using
            # pythonw.
            pyw_exe +='w'
            env.update(PYTHONW='True')

        # construct the argument string for the `startApp` function
        startArgs = []
        startArgs += ['showSplash={}'.format('--no-splash' not in sys.argv)]
        startAppView = []
        for key in ("builder", "coder", "runner", "direct"):
            if getattr(view, key):
                startAppView.append(key)
        startArgs += ['startView={}'.format(repr(startAppView))]
        startArgs = ', '.join(startArgs)

        # Start command for the PsychoPy application, can't call this file 
        # directly again like we used to as it would result in recursive 
        # execution due to the restart mechanism.
        startCmdStr = 'from psychopy.app import startApp;startApp({})'.format(
            startArgs)
        startCmd = [pyw_exe, '-c', startCmdStr]

        # run command in a subprocess and block until it finishes
        try:
            psychopyProc = subprocess.Popen(
                startCmd, 
                env=env)
        except KeyboardInterrupt:
            print("PsychoPy: Application interrupted.")
            break

        print("PsychoPy: Application started (PID: {})".format(
            psychopyProc.pid))
        stdout, stderr = psychopyProc.communicate()  
        exitCode = psychopyProc.wait()

        # print output from the subprocess (if any)
        if stdout is not None:
            print(stdout, file=sys.stdout)
        if stderr is not None:
            print(stderr, file=sys.stderr)

        print("PsychoPy: Application terminated (exit code {})".format(
            exitCode))

        # check for the restart file, if present, restart the application
        restartFile = os.path.join(getUserPrefsDir(), '.restart')
        if os.path.exists(restartFile):
            print("PsychoPy: Restarting the application...")
            os.remove(restartFile)
        else:
            break


if __name__ == '__main__':
    main()
