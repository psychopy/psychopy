#!/usr/bin/env python
################
# see notes at bottom for requirements
import glob, os, shutil, sys
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

if platform != 'darwin':
    raise "As of Aug 2013, setupApp.py is strictly for building the Mac Standalone bundle"

import bdist_mpkg, py2app
resources = glob.glob('psychopy/app/Resources/*')
resources.append('/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7/pyconfig.h')
frameworks = ["libavbin.dylib","/usr/lib/libxml2.2.dylib", #"libyaml.dylib",
            "libevent.dylib","libffi.dylib",
            ]
opencvLibs = glob.glob(os.path.join(sys.exec_prefix, 'lib', 'libopencv*.2.4.dylib'))
frameworks.extend(opencvLibs)
                  
setup(app=['psychopy/app/psychopyApp.py'],
    options=dict(py2app=dict( includes=['Tkinter','FileDialog','tkFileDialog', 'imp', 'subprocess', 'shlex',
                                  'shelve',#for scipy.io
                                  '_elementtree', 'pyexpat',#these 2 are needed by xml, which is needed by openpyxl
                                  'ioLabs','hid',#'pypsignifit', #psignifit is not available on py2.7
                                  'pp','ppauto','ppcommon','pptransport','ppworker',#annoying non-standard structure of pp
                                  'pyo','greenlet','vlc',
                                  'PyQt4','zmq','tornado',
                                  'psutil',#for iohub
                                  'pysoundcard','pysoundfile',
                                  'cv2',
                                  ],
                              packages=['wx','pyglet','pygame','OpenGL','psychopy','pytz',
                                'scipy','matplotlib','lxml','xml','openpyxl',
                                'coverage',#for unit testing
                                'serial','IPython',
                                'egi','labjack','pylink',#handy external science interfaces
                                'pyxid','pycrsltd',
                                #'PIL','Image',
                                'objc','Quartz','AppKit','QTKit','Cocoa','Foundation','CoreFoundation',
                                'pyolib',
                                'pandas','tables',#'cython',
                                'msgpack','yaml','gevent',#ioHub
                                #these aren't needed, but liked
                                'psychopy_ext','pyfilesec','rusocsci',
                                ],
                              excludes=[],#anything we need to forcibly exclude?
                              resources=resources,
                              argv_emulation=True,
                              site_packages=True,
                              frameworks=frameworks,
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


#ugly hack for opencv2:
#    As of opencv 2.4.5 the cv2.so binary used rpath to a fixed location to find libs and
#    even more annoyingly it then appended 'lib' to the rpath as well. These were fine
#    for the packaged framework python but the libs in an app bundle are different.
#    We'll create some links so the appear in the same place as in the framework python
rpath = "dist/PsychoPy2.app/Contents/Resources/"
for libPath in opencvLibs:
    libname = os.path.split(libPath)[-1]
    realPath = "../../Frameworks/"+libname #relative path (w.r.t. the fake)
    fakePath = os.path.join(rpath, "lib", libname)
    os.symlink(realPath, fakePath)
#they even did this for Python lib itself, which is in diff location
realPath = "../Frameworks/Python.framework/Python" #relative path (w.r.t. the fake)
fakePath = os.path.join(rpath, "Python")
os.symlink(realPath, fakePath)

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
