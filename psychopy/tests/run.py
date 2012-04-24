#!/usr/bin/env python
import sys, os

thisDir,filename = os.path.split(os.path.abspath(__file__))
os.chdir(thisDir)

argv = sys.argv

try:
    import pytest
    usePytest=True
except:
    usePytest=False

if usePytest:
    #argv.append('--doctest-modules') #doctests
    if 'cover' in argv:
        argv.remove('cover')
        argv.extend(['--cov-report','html','--cov','psychopy'])
    print ' '.join(argv)
    pytest.main(' '.join(argv))
else:
    import nose
    argv.append('--verbosity=3')
    if 'cover' in argv:
        argv.remove('cover')
        argv.append('--with-coverage')
        argv.append('--cover-package=psychopy')

    argv.append('--with-doctest')

    nose.run(argv=argv)