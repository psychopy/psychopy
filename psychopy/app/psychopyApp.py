#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

#NB the PsychoPyApp classes moved to _psychopyApp.py as of version 1.78.00
#to allow for better upgrading possibilities from the mac app bundle. this file
#now used solely as a launcher for the app, not as the app itself.
import sys
if __name__=='__main__':
    if '-v' in sys.argv or '--version' in sys.argv:
        print 'PsychoPy2, version %s (c)Jonathan Peirce, 2014, GNU GPL license' %psychopy.__version__
        sys.exit()
    elif '-h' in sys.argv or '--help' in sys.argv:
        print """Starts the PsychoPy2 application.

Usage:  python PsychoPy.py [options] [file]

Without options or files provided starts the psychopy using prefs to
decide on the view(s) to open.  If optional [file] is provided action
depends on the type of the [file]:

 Python script 'file.py' -- opens coder

 Experiment design 'file.psyexp' -- opens builder

Options:
    -c, --coder, coder       opens coder view only
    -b, --builder, builder   opens builder view only

    -v, --version    prints version and exits
    -h, --help       prints this help and exit

    --run or -r followed by python (.py) file will run that file without loading the app

    --firstrun       launches configuration wizard
    --no-splash       suppresses splash screen

"""
        sys.exit()
    elif '-r' in sys.argv or '--run' in sys.argv:
        try:
            cmdIndex = sys.argv.index('-r')
        except ValueError:
            cmdIndex = sys.argv.index('--run')
        if not len(sys.argv)>cmdIndex+1:
            print "PsychoPy app was started with the %r option but no filename followed" %(sys.argv[cmdIndex])
            sys.exit()
        else:
            filename = sys.argv[cmdIndex+1]
            if not filename.endswith(".py"):
                print "PsychoPy app was started with the %r option but the next argument was not a py file" %(sys.argv[cmdIndex])
                sys.exit()
        #try to run the script then!
        import imp
        src = open(filename)
        try:
            #this is a way to run the file and make it think its __name__=="__main__"
            imp.load_module('__main__', src, filename, (".py", "r", imp.PY_SOURCE))
        finally:
            src.close()
    else:
        #only do the importing if we're loading the application
        from psychopy.app._psychopyApp import *

        showSplash = True
        if '--no-splash' in sys.argv:
            showSplash = False
            del sys.argv[sys.argv.index('--no-splash')]
        app = PsychoPyApp(0, showSplash=showSplash)
        app.MainLoop()
