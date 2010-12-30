#!/usr/bin/env python
import nose, sys, os

thisDir,filename = os.path.split(os.path.abspath(__file__))
os.chdir(thisDir)

argv = sys.argv
argv.append('--verbosity=3')
if 'cover' in argv: 
    argv.remove('cover')
    argv.append('--with-coverage')
    argv.append('--cover-package=psychopy')

argv.append('--with-doctest')

nose.run(argv=argv)
