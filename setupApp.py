#!/usr/bin/env python
################
# see notes at bottom for requirements
import glob, os, shutil
from sys import platform
from distutils.core import setup

#regenerate __init__.py only if we're in the source repos (not in a source zip file)
try:
    import createInitFile#won't exist in a sdist.zip
    writeNewInit=True
except:
    writeNewInit=False
if writeNewInit:
    vStr = createInitFile.createInitFile(dist='bdist')
    exec(vStr)#create variables __version__, __author__ etc

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
    files = glob.glob('psychopy/app/Resources/*')
    for file in files:
        loc, name = os.path.split(file)
        packageData.append( ['psychopy/app/Resources', [file]])

elif platform=='darwin':
    import bdist_mpkg, py2app
    resources = glob.glob('psychopy/app/Resources/*')
    resources.append('/Library/Frameworks/Python.framework/Versions/2.6/include/python2.6/pyconfig.h')
elif platform=='posix':
    pass

if platform == 'win32':
    requires.extend(['pymedia'])
    setup(console=[{
            "script":"psychopy/app/psychopyApp.py",
            "icon_resources":[(0, "psychopy/app/Resources/psychopy.ico")]
            }],
          options={
                'py2exe': {
                    'packages' : ['monitors','psychopy','psychopy.demos',
                        'matplotlib', 'numpy', 'scipy', 'wx',
                        'pyglet','pygame','OpenGL','pycrsltd',],
                    #"skip_archive":1,
                    }
            },
          data_files=packageData)
else:
    setup(app=['psychopy/app/psychopyApp.py'],
        options=dict(py2app=dict( includes=['Tkinter','FileDialog','tkFileDialog', 'imp', 'subprocess', 'shlex',
                                      'shelve',#for scipy.io
                                      '_elementtree', 'pyexpat',#these 2 are needed by xml, which is needed by openpyxl
                                      'ioLabs','hid',#'pypsignifit', #psignifit is not available on py2.7
                                      'pp','ppauto','ppcommon','pptransport','ppworker',#annoying non-standard structure of pp
                                      'pyo',
                                      ],
                                      excludes=['PyQt4'],#matplotlib will fetch this if posss and we don't need it
                                      frameworks = ["libavbin.dylib","/usr/lib/libxml2.2.dylib"],
                                      resources=resources,
                                      argv_emulation=True,
                                      site_packages=True,
                                      packages=['wx','pyglet','pygame','OpenGL','psychopy','pytz',
                                        'scipy','matplotlib','lxml','xml','openpyxl',
                                        'coverage',#for unit testing
                                        'serial','IPython',
                                        'egi','labjack','pylink',#handy external science interfaces
                                        'pyxid','pycrsltd',
                                        #'PIL','Image',
                                        'pyolib',
                                        'pandas','tables',
                                        ],
                                      iconfile='psychopy/app/Resources/psychopy.icns',
                                      plist=dict(
                                      CFBundleIconFile='psychopy.icns',
                                      CFBundleName               = "PsychoPy2",
                                      CFBundleShortVersionString = __version__,     # must be in X.X.X format
                                      CFBundleGetInfoString      = "PsychoPy2 "+__version__,
                                      CFBundleExecutable         = "PsychoPy2",
                                      CFBundleIdentifier         = "org.psychopy.PsychoPy2",
                                      CFBundleLicense            = "GNU GPLv3+",
                                      CFBundleDocumentTypes=[dict(CFBundleTypeExtensions=['*'],#CFBundleTypeName='Python Script',
                                                                 CFBundleTypeRole='Editor')],
                                      ),
                              )))

if writeNewInit:
    #remove unwanted info about this system post-build
    createInitFile.createInitFile(dist=None)

#running testApp from within the app raises wx errors
#shutil.rmtree("dist/PsychoPy2.app/Contents/Resources/lib/python2.6/psychopy/tests/testTheApp")

"""
I struggled getting the app to build properly. These were some of the problems:

Mac OS X - you need to install
setuptools0.6c9
    (svn co http://svn.python.org/projects/sandbox/branches/setuptools-0.6 then go to the directory and
    do a sudo python setup.py install)
    DO NOT use version 0.7, nor version 0.6.8 - they are both broken!
macholib (> 1.2 to avoid "Unkown load command: 27")
modulegraph
altgraph

More recently there was a problem with pytz failing to find pyconfig.h
Fixed this by modifying the use of get_config_vars() in distutils/util around line 80:
        macver = os.environ.get('MACOSX_DEPLOYMENT_TARGET')
        if not macver:
            try:
                cfgvars = get_config_vars()
                macver = cfgvars.get('MACOSX_DEPLOYMENT_TARGET')
            except:
                pass#we couldn't load up pyconfig.h

to make avbin work from the mac standalone:
    In pyglet/lib.py, around line 166, do this:
        search_path.append(join(sys.prefix, '..', 'Frameworks'))
    instead (or as well as) of
        search_path.append(os.path.join(
                    os.environ['RESOURCEPATH'],
                    '..',
                    'Frameworks',
                    libname))
"""

# on Mac use:
#python2.6 setup.py bdist_mpkg --readme=psychopy/README.txt
#python2.6 setupApp.py py2app
