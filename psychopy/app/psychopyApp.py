#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys

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


def main():
    if '-x' in sys.argv:
        # run a .py script from the command line using StandAlone python
        targetScript = sys.argv[sys.argv.index('-x') + 1]
        from psychopy import core
        import os
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

    -v, --version    prints version and exits
    -h, --help       prints this help and exit

    --firstrun       launches configuration wizard
    --no-splash      suppresses splash screen

""")
        sys.exit()

    if (('| packaged by conda-forge |' in sys.version or '|Anaconda' in sys.version)
        and sys.platform == 'darwin' and sys.version_info > (3,9)):

        # On macOS with Anaconda, GUI applications need to be run using
        # `pythonw`. Since we have no way to determine whether this is currently
        # the case, we run this script again -- ensuring we're definitely using
        # pythonw.
        import os
        env = os.environ
        PYTHONW = env.get('PYTHONW', 'False')

        if PYTHONW != 'True':
            from psychopy import core
            cmd = [sys.executable + 'w', __file__]
            if '--no-splash' in sys.argv:
                cmd.append('--no-splash')

            stdout, stderr = core.shellCall(cmd,
                                            env=dict(env, PYTHONW='True'),
                                            stderr=True)
            print(stdout, file=sys.stdout)
            print(stderr, file=sys.stderr)
            sys.exit()
        else:
            start_app()
    else:
        start_app()


if __name__ == '__main__':
    main()
