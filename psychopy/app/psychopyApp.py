#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import subprocess

# fix macOS locale-bug on startup: sets locale to LC_ALL (must be defined!)
# import psychopy.locale_setup  # noqa

# NB the PsychoPyApp classes moved to _psychopyApp.py as of version 1.78.00
# to allow for better upgrading possibilities from the mac app bundle. this
# file now used solely as a launcher for the app, not as the app itself.

def start_app():
    """Start the GUI application.
    """
    from psychopy.app import startApp, quitApp
    from psychopy.preferences import prefs

    showSplash = prefs.app['showSplash']
    if '--no-splash' in sys.argv:
        showSplash = False
        del sys.argv[sys.argv.index('--no-splash')]
    _ = startApp(showSplash=showSplash)  # main loop
    quitApp()


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


def runStartupPackageTasks(env=None):
    """Run startup package tasks.

    This checks for a file called 'pip_tasks.list' in the user preferences
    directory. If the file exists, it will install the modules listed in it.

    The format of the file is a list of pip commands, one per line. Each line
    should start with a valid pip command, followed by any flags or options.

    Parameters
    ----------
    env : dict, optional
        The environment variables to use when running the tasks. Should be the 
        same as the enviornment variables used to start the app. These are set
        to the current environment if not provided. The default is None.

    """
    import os

    # get the current environment if not provided
    if env is None:
        env = os.environ

    # preload install tasks are writen to a file in the user prefs directory
    installFile = os.path.join(getUserPrefsDir(), 'pip_tasks.list')

    # if the file exists, install each module listed in it
    if os.path.exists(installFile):
        print("PsychoPy: Found 'pip_tasks.list' file.")
        pipTaskList = []
        with open(installFile) as f:
            for line in f:
                cmdVals = line.strip().split()  # clean up the line
                
                # check if the line starts with a valid command
                if cmdVals[0] not in ['install', 'uninstall']:
                    print("Invalid command in 'pip_tasks.list' file: {}".format(
                        cmdVals[0]))
                    continue

                pipTaskList.append(cmdVals)

        # for valid commands, install the modules
        if pipTaskList:
            print('PsychoPy: Running pre-startup package tasks...')
            # construct executable path depending on the platform
            execPath = sys.executable

            for cmd in pipTaskList:
                failed = False
                # run the pip commands
                extraCmd = []  # extra commands for pip
                if cmd[0] == 'install':
                    if '--user' not in cmd:
                        extraCmd.append('--user')
                elif cmd[0] == 'uninstall':
                    if '--yes' not in cmd:
                        extraCmd = ['--yes']
                
                # run the pip command
                pipCmd = [execPath, '-m', 'pip'] + cmd + extraCmd

                # run command in a subprocess and block until it finishes
                pipProc = subprocess.Popen(pipCmd, env=env)
                output, err = pipProc.communicate()  
                exitCode = pipProc.wait()  # block until done

                if output is not None:
                    print(output, file=sys.stdout)
                
                if err is not None:
                    print(err, file=sys.stderr)
                
        # delete the file after installing all modules
        os.remove(installFile)

        msg = ("PsychoPy: Completed pre-startup package tasks, see above for "
               "warnings and errors.")
        print(msg)

    # else:
    #     print("PsychoPy: No pre-startup package tasks to run.")


def main():
    """Main entry point for the PsychoPy application.

    This function is the main entry point for the PsychoPy application. It
    handles the command line arguments and starts the application in a
    subprocess.

    It also handles any pre-startup tasks that need to be run before the app
    starts, but within the same environment.

    """
    # Setup the environment variables for running the app
    import os
    env = os.environ

    if '--no-pkg-dir' not in sys.argv:
        userBaseDir = os.path.join(getUserPrefsDir(), 'packages')
        env['PYTHONUSERBASE'] = userBaseDir
        env['PYTHONNOUSERSITE'] = '1'  # isolate user packages for plugins

    if '-x' in sys.argv:
        # run a .py script from the command line using StandAlone python
        targetScript = sys.argv[sys.argv.index('-x') + 1]
        from psychopy import core
        core.shellCall(
            [sys.executable, os.path.abspath(targetScript)], 
            env=env)
        sys.exit()
    if '-v' in sys.argv or '--version' in sys.argv:
        from psychopy import __version__
        msg = ('PsychoPy3, version %s (c) Jonathan Peirce 2018, GNU GPL license'
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
    -c, --coder, coder       pens coder view only
    -b, --builder, builder   opens builder view only
    -x script.py             execute script.py using StandAlone python

    -v, --version            prints version and exits
    -h, --help               prints this help and exit

    --firstrun               launches configuration wizard
    --no-splash              suppresses splash screen
    --skip-pkg-tasks         skip pip tasks on startup this session
    --no-pkg-dir             use default user site-packages directory

""")
        sys.exit()

    # special envionment variables for the app
    PYTHONW = None
    if (('| packaged by conda-forge |' in sys.version or '|Anaconda' in sys.version)
            and sys.platform == 'darwin' and sys.version_info >= (3,9)):
        PYTHONW = env.get('PYTHONW', 'False')
        if PYTHONW != 'True':
            env['PYTHONW'] = 'True'

    # run the pre-startup tasks if not ignored
    if '--skip-pkg-tasks' not in sys.argv:
        runStartupPackageTasks(env)

    # construct executable path depending on the platform
    execPath = sys.executable
    if PYTHONW is not None:
        execPath = execPath + 'w'  # macOS

    # construct the command to run the app in a subprocess
    cmd = [execPath, '-c', 'from psychopy.app import startApp;startApp()']

    # run command in a subprocess and block until it finishes
    psychopyProc = subprocess.Popen(cmd, env=env)

    print("PsychoPy: Application started (PID: {})".format(psychopyProc.pid))

    output, err = psychopyProc.communicate()  
    exitCode = psychopyProc.wait()

    # print output from the subprocess (if any)
    if output is not None:
        print(output, file=sys.stdout)
    if err is not None:
        print(err, file=sys.stderr)

    print("PsychoPy: Application terminated (exit code {})" .format(exitCode))

    sys.exit(exitCode)  # forwarded exit code from the subprocess


if __name__ == '__main__':
    main()
