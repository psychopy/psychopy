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
packageData = []
requires=[]

if platform=='win32':
    import py2exe    
    
    #get matplotlib data files
    from distutils.filelist import findall
    import os
    import matplotlib
    packageData.extend(matplotlib.get_py2exe_datafiles())
    #get resources (icons etc)        
    files = glob.glob('Resources/*')
    for file in files:
        loc, name = os.path.split(file)
        packageData.append( ['Resources', [file]])
        
elif platform=='darwin':
    resources = glob.glob('Resources/*')
elif platform=='posix':
    pass
    
if platform == 'win32':
    requires.extend(['pymedia'])
    setup(console=[{
            "script":"PsychoPyIDE.py",
            "icon_resources":[(0, "psychopy.ico")]
            }],
          options={
                'py2exe': {
                    'packages' : ['monitors','psychopy','psychopy.demos',
                        'matplotlib', 'numpy', 'scipy', 'pytz','wx',
                        'pyglet','pygame','OpenGL',],
                    #"skip_archive":1,
                    }          
            },
          data_files=packageData)
else:
    setup(app=['PsychoPyIDE.py'],
        options=dict(py2app=dict( includes=['Tkinter','FileDialog','setuptools'],
                                  frameworks = ["libavbin.dylib"],
                                  resources=resources,
                                  #semi_standalone=True,
                                  site_packages=True,
                                  packages=['wx','scipy','matplotlib','pyglet','pygame','OpenGL','monitors','psychopy'],
                                  iconfile='psychopy.icns',
                                  plist=dict(
                                      CFBundleIconFile='psychopy.icns',
                                      CFBundleName               = "PsychoPyIDE",
                                      CFBundleShortVersionString = psychopy.__version__,     # must be in X.X.X format
                                      CFBundleGetInfoString      = "PsychoPyIDE "+psychopy.__version__,
                                      CFBundleExecutable         = "PsychoPyIDE",
                                      CFBundleIdentifier         = "org.psychopy.PsychoPyIDE",
                                      CFBundleDocumentTypes=[dict(CFBundleTypeExtensions=['*'],
                                                                 #CFBundleTypeName='Python Script',
                                                                 CFBundleTypeRole='Editor')],
                                      ),                              
                              )))
"""
I struggled getting this to work 

Mac OS X - you need to install 
setuptools0.6c9
    (svn co http://svn.python.org/projects/sandbox/branches/setuptools-0.6 then go to the directory and
    do a sudo python setup.py install)
    DO NOT use version 0.7, nor version 0.6.8 - they are both broken!
macholib (> 1.2 to avoid "Unkown load command: 27")
modulegraph
altgraph
"""

# on Mac use:
#python2.4 setup.py bdist_mpkg --readme=psychopy/README.txt
#python2.4 setupApp.py py2app --semi-standalone -s
