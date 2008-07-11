#!/usr/local/bin/python2.4
################
# see notes at bottom for requirements
import glob, os
from sys import platform
from distutils.core import setup

if platform=='darwin':
    #package_data_path='/Library/Python/2.3/psychopy'
    import bdist_mpkg, py2app

import psychopy, monitors
thisVersion=psychopy.__version__

#define the extensions to compile if necess
cExtensions = []
packageData = []
if platform=='win32':
    import py2exe    
    files = glob.glob('Resources/*')
    for file in files:
        loc, name = os.path.split(file)
        packageData.append( ['Resources', [file]])
elif platform=='darwin':
    resources = glob.glob('Resources/*')
elif platform=='posix':
    pass
##    cExtensions.append(Extension('psychopy.ext.posix',
##                 sources = [os.path.join('psychopy','ext','posix.c')]))


import pytz
pytz.zoneinfo = pytz.tzinfo
pytz.zoneinfo.UTC = pytz.UTC
if platform == 'win32':
    requires.extend(['pymedia'])
    setup(console=["PsychoPyIDE.py"],      
          data_files=packageData)
else:
    setup(app=['PsychoPyIDE.py'],
        options=dict(py2app=dict( excludes=['OpenGL', 'pygame'],
                                  includes=['Tkinter','FileDialog'],
                                  resources=resources,
                                  #semi_standalone=True,
                                  site_packages=True,
                                  packages=['wx','scipy','matplotlib','pyglet','monitors','psychopy'],
                                  iconfile='psychopy.icns',
                                  plist=dict(
                                      CFBundleIconFile='psychopy.icns',
                                      CFBundleName               = "PsychoPyIDE",
                                      CFBundleShortVersionString = psychopy.__version__,     # must be in X.X.X format
                                      CFBundleGetInfoString      = "PsychoPyIDE "+psychopy.__version__,
                                      CFBundleExecutable         = "PsychoPyIDE",
                                      CFBundleIdentifier         = "org.psychopy.PsychoPyIDE",
                                      CFBundleDocumentTypes=dict(CFBundleTypeExtensions='py',
                                                                 CFBundleTypeName='Python Script',
                                                                 CFBundleTypeRole='Editor'),
                                      ),                              
                              )))
"""
I struggled getting this to work 

Mac OS X - you need to install 
macholib (> 1.2 to avoid "Unkown load command: 27")
modulegraph
"""

# on Mac use:
#python2.4 setup.py bdist_mpkg --readme=psychopy/README.txt
#python2.4 setupApp.py py2app --semi-standalone -s
