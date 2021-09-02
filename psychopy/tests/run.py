#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import subprocess

thisDir,filename = os.path.split(os.path.abspath(__file__))
os.chdir(thisDir)

argv = sys.argv

if argv[0].endswith('run.py'):#that's this script
    argv.pop(0)  # remove run.py

#create extra args and then append main args to them
#if the user specifies a directory that should come last
extraArgs = []

#if user didn't specify a traceback deetail level then set to be short
overrideTraceBack=True
for thisArg in argv:
    if thisArg.startswith('--tb='):
        overrideTraceBack=False
if overrideTraceBack:
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

extraArgs.extend(argv)
if havePytest:
    command = 'py.test ' + ' '.join(extraArgs)
else:
    command = '%s -u runPytest.py ' %(sys.executable)
    command = command + ' ' + ' '.join(extraArgs)
print(command)
subprocess.Popen(command, shell=True)
