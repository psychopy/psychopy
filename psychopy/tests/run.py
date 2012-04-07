#!/usr/bin/env python
import sys, os

thisDir,filename = os.path.split(os.path.abspath(__file__))
os.chdir(thisDir)

try:
    import pytest
    pytest.main()
except:
    import nose
    argv = sys.argv
    argv.append('--verbosity=3')
    if 'cover' in argv:
        argv.remove('cover')
        argv.append('--with-coverage')
        argv.append('--cover-package=psychopy')

    argv.append('--with-doctest')

    nose.run(argv=argv)
