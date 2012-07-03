#!/usr/bin/env python
import sys, os

thisDir,filename = os.path.split(os.path.abspath(__file__))
os.chdir(thisDir)

argv = sys.argv

if argv[0]=='run.py':
    argv.pop(0)  # remove run.py

#create extra args and then append main args to them
#if the user specifies a directory that should come last
extraArgs = []

#if user didn't specify a traceback deetail level then set to be short
for thisArg in argv:
    if thisArg.startswith('--tb='):
        break
    extraArgs.append('--tb=short')

#always add doctests if not included
if '--doctest-modules' not in argv:
    extraArgs.append('--doctest-modules') #doctests
#add coverage if requested
if 'cover' in argv:
    argv.remove('cover')
    extraArgs.extend(['--cov','psychopy'])

#use the pytest module itself if available
#otherwise use the precompiled pytest script
try:
    import pytest
    havePytest=True
except ImportError:
    havePytest=False
if havePytest:
    pytest.main(' '.join(argv))
else:
    import subprocess
    command = '%s -u runPytest.py ' %(sys.executable)
    command = command + ' ' + ' '.join(extraArgs)
    command = command + ' ' + ' '.join(argv)
    print command
    subprocess.Popen(command, shell=True)
