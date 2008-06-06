#!/usr/local/bin/python2.4
################
import glob, os
from sys import platform
from distutils.core import setup, Extension

if platform=='darwin':
    #package_data_path='/Library/Python/2.3/psychopy'
    import bdist_mpkg, py2app

import psychopy, monitors
thisVersion=psychopy.__version__

#define the extensions to compile if necess
cExtensions = []

if platform=='win32':
    import py2exe
elif platform=='darwin':
    resources = glob.glob('psychopy/IDE/Resources/*')

dependencies = ['numpy','scipy','matplotlib',
    'pygame','wxPython>2.4',#pyopengl
    'PIL','ctypes']

if platform == 'win32':
#    requires.extend(['pymedia'])
    setup(console=["PsychoCentral.py"])
else:
    setup(app=['psychopy/IDE/PsychoPyIDE.py'],
        options=dict(py2app=dict( argv_emulation=1,
                                  resources=resources,
                                  alias=True,
                                  iconfile='psychopy/psychopy.icns')))
# on Mac use:
#python2.4 setup.py bdist_mpkg --readme=psychopy/README.txt
#python2.4 setupApp.py py2app --semi-standalone -s
