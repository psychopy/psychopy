#!/usr/bin/env python
################
# see notes at bottom for requirements
import glob
import os
import sys
from sys import platform
from distutils.core import setup

# regenerate __init__.py only if we're in the source repos (not in a zip file)
try:
    import createInitFile  # won't exist in a sdist.zip
    writeNewInit=True
except:
    writeNewInit=False
if writeNewInit:
    vStr = createInitFile.createInitFile(dist='bdist')
    exec(vStr)#create variables __version__, __author__ etc

#define the extensions to compile if necess
packageData = []
requires = []

if platform != 'darwin':
    raise "As of Aug 2013, setupApp.py is strictly for building the Mac Standalone bundle"

import bdist_mpkg
import py2app
resources = glob.glob('psychopy/app/Resources/*')
resources.append('/Library/Frameworks/Python.framework/Versions/2.7/include/python2.7/pyconfig.h')
frameworks = ["libavbin.dylib", "/usr/lib/libxml2.2.dylib", #"libyaml.dylib",
              "libevent.dylib", "libffi.dylib",
              ]
opencvLibs = glob.glob(os.path.join(sys.exec_prefix, 'lib', 'libopencv*.2.4.dylib'))
frameworks.extend(opencvLibs)

setup(
    app=['psychopy/app/psychopyApp.py'],
    options=dict(py2app=dict(
            includes=['Tkinter', 'FileDialog', 'tkFileDialog',
                      'imp', 'subprocess', 'shlex',
                      'shelve',  # for scipy.io
                      '_elementtree', 'pyexpat',  # for openpyxl
                      'ioLabs', 'hid',
                      'pp', 'ppauto', 'ppcommon', 'pptransport', 'ppworker',
                      'pyo', 'greenlet', 'vlc', 'zmq', 'tornado',
                      'psutil',  # for iohub
                      'pysoundcard', 'soundfile',
                      'cv2',
                      'xlwt',  # writes excel files for pandas
                      ],
            packages=['wx', 'pyglet', 'pygame', 'OpenGL', 'psychopy', 'pytz',
                      'scipy', 'matplotlib', 'lxml', 'xml', 'openpyxl',
                      'moviepy', 'imageio',
                      'PyQt4',
                      'PIL',  # 'Image',
                      'objc', 'Quartz', 'AppKit', 'QTKit', 'Cocoa',
                      'Foundation', 'CoreFoundation',
                      'pyolib',
                      'requests',  # for efficient uploading to servers
                      'pyosf',
                      # for unit testing
                      'coverage',
                      # handy external science libs
                      'serial', 'IPython',
                      'egi', 'labjack', 'pylink',
                      'pyxid',
                      'pandas', 'tables',  # 'cython',
                      'msgpack', 'yaml', 'gevent',  # for ioHub
                      # these aren't needed, but liked
                      'psychopy_ext', 'pyfilesec', 'rusocsci',
                      'bidi',  # for right-left language conversions
                      ],
            excludes=['bsddb'],  # anything we need to forcibly exclude?
            resources=resources,
            argv_emulation=True,
            site_packages=True,
            frameworks=frameworks,
            iconfile='psychopy/app/Resources/psychopy.icns',
            plist=dict(
                  CFBundleIconFile='psychopy.icns',
                  CFBundleName               = "PsychoPy2",
                  CFBundleShortVersionString = __version__,  # must be in X.X.X format
                  CFBundleGetInfoString      = "PsychoPy2 "+__version__,
                  CFBundleExecutable         = "PsychoPy2",
                  CFBundleIdentifier         = "org.psychopy.PsychoPy2",
                  CFBundleLicense            = "GNU GPLv3+",
                  CFBundleDocumentTypes=[dict(CFBundleTypeExtensions=['*'],
                                              CFBundleTypeRole='Editor')],
                  ),
              )))


# ugly hack for opencv2:
# As of opencv 2.4.5 the cv2.so binary used rpath to a fixed
# location to find libs and even more annoyingly it then appended
# 'lib' to the rpath as well. These were fine for the packaged
# framework python but the libs in an app bundle are different.
# So, create symlinks so they appear in the same place as in framework python
rpath = "dist/PsychoPy2.app/Contents/Resources/"
for libPath in opencvLibs:
    libname = os.path.split(libPath)[-1]
    realPath = "../../Frameworks/"+libname  # relative path (w.r.t. the fake)
    fakePath = os.path.join(rpath, "lib", libname)
    os.symlink(realPath, fakePath)
# they even did this for Python lib itself, which is in diff location
realPath = "../Frameworks/Python.framework/Python"  # relative to the fake path
fakePath = os.path.join(rpath, "Python")
os.symlink(realPath, fakePath)

if writeNewInit:
    # remove unwanted info about this system post-build
    createInitFile.createInitFile(dist=None)

# running testApp from within the app raises wx errors
# shutil.rmtree("dist/PsychoPy2.app/Contents/Resources/lib/python2.6/psychopy/tests/testTheApp")
