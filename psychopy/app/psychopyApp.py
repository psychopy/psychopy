#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""PsychoPy application launcher.
"""

import sys
import subprocess

# fix macOS locale-bug on startup: sets locale to LC_ALL (must be defined!)
import psychopy.locale_setup  # noqa

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
                pipCmd = ['-m', 'pip'] + cmd + extraCmd

                # run command in a subprocess and block until it finishes
                exitCode, _, _ = runPyCommand(pipCmd, env=env, printOutput=True)
                
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

    It also handles any pre-startup tasks, running them within the same 
    environment as the app itself.

    """
    # Setup the environment variables for running the app
    import os
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

    env = os.environ.copy()  # get environment variables for this process

    # priority flags
    if '--no-pkg-dir' not in sys.argv:
        # Configure the user site-packages directory to a custom location if 
        # the flag is not present. This isolates user packages to a separate
        # directory to avoid conflicts with system packages or other user 
        # packages.
        userBasePath = os.path.join(getUserPrefsDir(), 'packages')
        env['PYTHONUSERBASE'] = userBasePath
        env['PYTHONNOUSERSITE'] = '1'  # isolate user packages for plugins

        # Package paths for custom user site-packages, these should be compiant
        # with platform specify conventions.
        if sys.platform == 'win32':  # windows 
            pyDirName = "Python" + sys.winver.replace(".", "")
            userPackagePath = os.path.join(
                userBasePath, pyDirName, "site-packages")
        elif sys.platform == 'darwin' and sys._framework:  # macos + framework
            userPackagePath = os.path.join(
                userBasePath, "lib", "python", "site-packages")
        else:  # posix (including linux and macos without framework)
            pyVersion = sys.version_info
            pyDirName = "python{}.{}".format(pyVersion[0], pyVersion[1])
            userPackagePath = os.path.join(
                userBasePath, "lib", pyDirName, "site-packages")

        # add the custom user site-packages to the PYTHONPATH
        pyPath = env.get('PYTHONPATH', '')
        if pyPath:
            env['PYTHONPATH'] = pyPath + os.pathsep + userPackagePath
        else:
            env['PYTHONPATH'] = userPackagePath

        print("PsychoPy: Using user site-packages directory: {}".format(
            userBasePath))
    else:
        print("PsychoPy: Using default user site-packages directory.")
        
    if '--list-pkgs' in sys.argv:
        # List installed packages and exit. This calls `pip list` on one of the
        # specified package list types (base or user) and then exits. 
        try:
            pkgListType = sys.argv[sys.argv.index('--list-pkgs') + 1]
        except (ValueError, IndexError):
            print("Error: Missing package list type (base or user).")
            sys.exit()

        if pkgListType == 'base':
            # list installed packages and versions
            cmd = ['-m', 'pip', 'list']
            runPyCommand(cmd, env=env, printOutput=True)
        elif pkgListType == 'user':
            # list installed user packages and versions
            cmd = ['-m', 'pip', 'list', '--user']
            runPyCommand(cmd, env=env, printOutput=True)
        else:
            print("Error: Invalid package list type '{}'.".format(pkgListType))
        sys.exit()

    if '--install-pkg' in sys.argv:
        # Install a package and exit. This calls `pip install` with the 
        # specified arguments and then exits. 
        try:
            inputCmd = sys.argv[sys.argv.index('--install-pkg') + 1:]
            pipCmd = [x.strip() for x in inputCmd]
            if '--user' not in pipCmd:    # add --user flag if not present
                pipCmd.append('--user')
            if '--prefer-binary' not in pipCmd:  # usually do
                pipCmd.append('--prefer-binary')
        except (ValueError, IndexError):
            print("Error: Missing package name.")
            sys.exit()
        cmd = ['-m', 'pip', 'install'] + pipCmd
        runPyCommand(cmd, env=env, printOutput=True)
        sys.exit()

    if '--uninstall-pkg' in sys.argv:
        # Uninstall a package and exit. This calls `pip uninstall` with the 
        # specified arguments and then exits. 
        try:
            inputCmd = sys.argv[sys.argv.index('--uninstall-pkg') + 1:]
            pipCmd = [x.strip() for x in inputCmd]
            if '--yes' not in pipCmd:    # add --yes flag if not present
                pipCmd.append('--yes')
        except (ValueError, IndexError):
            print("Error: Missing package name.")
            sys.exit()
        cmd = ['-m', 'pip', 'uninstall'] + pipCmd
        runPyCommand(cmd, env=env, printOutput=True)
        sys.exit()

    if '--pip' in sys.argv:
        # Run a PIP command and exit. This calls `pip` with the specified
        # arguments and then exits. The environment variables are set to the
        # same as the current environment.
        try:
            pipCmd = sys.argv[sys.argv.index('--pip') + 1:]
            # split the command and remove whitespace
            pipCmd = ['-m', 'pip'] + [x.strip() for x in pipCmd]
            
        except (ValueError, IndexError):
            print("Error: Malfomed pip command.")
            sys.exit()
        runPyCommand(pipCmd, env=env, printOutput=True)
        sys.exit()
    
    if '-x' in sys.argv:
        # run a .py script from the command line using StandAlone python
        targetScript = sys.argv[sys.argv.index('-x') + 1]
        from psychopy import core
        core.shellCall(
            [sys.executable, os.path.abspath(targetScript)], 
            env=env)
        sys.exit()

    if '-v' in sys.argv or '--version' in sys.argv:
        # Print the version string and exit
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
    -c, --coder, coder       opens coder view only
    -b, --builder, builder   opens builder view only
    -x script.py             execute script.py using StandAlone python

    -v, --version            prints version and exits
    -h, --help               prints this help and exit

    --firstrun               launches configuration wizard
    --no-splash              suppresses splash screen

    --no-pkg-dir             use default user site-packages directory
    --list-pkgs <type>       list packages then exit, type: base or user
    --install-pkg <pkg>      install a user package then exit
    --uninstall-pkg <pkg>    uninstall a user package then exit
    --pip <args>             run pip command then exit
    --skip-pkg-tasks         skip pip tasks on startup this session

    --show-last-log          show the last app startup log and exit

""")
        sys.exit()

    # if we get here, then we're starting the app itself

    # show a specific app window if requested
    startAppView = None
    if '-b' in sys.argv or '--builder' in sys.argv:
        startAppView = 'builder'
    elif '-c' in sys.argv or '--coder' in sys.argv:
        startAppView = 'coder'
    elif '-r' in sys.argv or '--runner' in sys.argv:
        startAppView = 'runner'

    # special envionment variables for the app
    PYTHONW = None
    sysVer = sys.version
    if (('| packaged by conda-forge |' in sysVer or '|Anaconda' in sysVer)
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

    # construct the argument string for the `startApp` function
    startArgs = []
    startArgs += ['showSplash={}'.format('--no-splash' not in sys.argv)]
    if startAppView is not None:
        startArgs += ['startView={}'.format(repr(startAppView))]
    startArgs = ', '.join(startArgs)

    # construct the command to start the app
    startCmdStr = 'from psychopy.app import startApp;startApp({})'.format(
        startArgs)
    startCmd = [execPath, '-c', startCmdStr]

    # run command in a subprocess and block until it finishes
    psychopyProc = subprocess.Popen(startCmd, env=env)
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
