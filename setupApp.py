#!/usr/bin/env python
################
# see notes at bottom for requirements
from __future__ import absolute_import, print_function
import glob
import os
import sys
from sys import platform
from distutils.core import setup
from pkg_resources import parse_version
# import versioneer
import psychopy
version = psychopy.__version__

# regenerate __init__.py only if we're in the source repos (not in a zip file)
try:
    import createInitFile  # won't exist in a sdist.zip
    writeNewInit=True
except:
    writeNewInit=False
if writeNewInit:
    vStr = createInitFile.createInitFile(dist='bdist')

#define the extensions to compile if necess
packageData = []
requires = []

if platform != 'darwin':
    raise RuntimeError("setupApp.py is only for building Mac Standalone bundle")

import bdist_mpkg
import py2app
resources = glob.glob('psychopy/app/Resources/*')
frameworks = ["/usr/lib/libxml2.2.dylib", #"libyaml.dylib",
              "libevent.dylib", "libffi.dylib",
              "libmp3lame.0.dylib",
              "/usr/local/Cellar/glfw/3.2.1/lib/libglfw.3.2.dylib",
              ]
opencvLibs = glob.glob(os.path.join(sys.exec_prefix, 'lib', 'libopencv*.2.4.dylib'))
frameworks.extend(opencvLibs)

import macholib
#print("~"*60 + "macholib version: "+macholib.__version__)

if parse_version(macholib.__version__) <= parse_version('1.7'):
    print("Applying macholib patch...")
    import macholib.dyld
    import macholib.MachOGraph
    dyld_find_1_7 = macholib.dyld.dyld_find
    def dyld_find(name, loader=None, **kwargs):
        #print("~"*60 + "calling alternate dyld_find")
        if loader is not None:
            kwargs['loader_path'] = loader
        return dyld_find_1_7(name, **kwargs)
    macholib.MachOGraph.dyld_find = dyld_find

includes = ['Tkinter', 'tkFileDialog',
            'imp', 'subprocess', 'shlex',
            'shelve',  # for scipy.io
            '_elementtree', 'pyexpat',  # for openpyxl
            'hid',
            'pyo', 'greenlet', 'zmq', 'tornado',
            'psutil',  # for iohub
            'tobii_research',  # need tobii_research file and tobiiresearch pkg
            'pysoundcard', 'soundfile', 'sounddevice', 'readline',
            'hid',
            'xlwt',  # writes excel files for pandas
            'vlc',  # install with pip install python-vlc
            'msgpack_numpy',
            'configparser',
            ]
packages = ['wx', 'psychopy',
            'pyglet', 'pytz', 'OpenGL', 'glfw',
            'scipy', 'matplotlib', 'lxml', 'xml', 'openpyxl',
            'moviepy', 'imageio', 'imageio_ffmpeg',
            '_sounddevice_data', '_soundfile_data',
            'cffi', 'pycparser',
            'PIL',  # 'Image',
            'objc', 'Quartz', 'AppKit', 'QTKit', 'Cocoa',
            'Foundation', 'CoreFoundation',
            'pkg_resources',  # needed for objc
            'pyolib', 'pyo',
            'requests', 'certifi', 'cryptography',
            'pyosf',
            # for unit testing
            'coverage',
            # handy external science libs
            'serial',
            'egi', 'pylink', 'tobiiresearch',
            'pyxid', 'pyxid2', 'ftd2xx',  # ftd2xx is used by cedrus
            'pandas', 'tables',  # 'cython',
            'msgpack', 'yaml', 'gevent',  # for ioHub
            # these aren't needed, but liked
            'psychopy_ext', 'pyfilesec',
            'bidi', 'arabic_reshaper',  # for right-left language conversions
            # for Py3 compatibility
            'future', 'past', 'lib2to3',
            'json_tricks',  # allows saving arrays/dates in json
            'git', 'gitlab',
            'astunparse', 'esprima',  # for translating/adapting py/JS
            'pylsl', 'pygaze',
            'smite',  # https://github.com/marcus-nystrom/SMITE (not pypi!)
            'cv2',
            'badapted', 'darc_toolbox',  # adaptive methods from Ben Vincent
            'questplus',
            'metapensiero.pj', 'dukpy', 'macropy',
            'jedi','parso',
            'psychtoolbox',
            'freetype', 'h5py',
            'markdown_it',
            ]

if sys.version_info.major >= 3:
    packages.extend(['PyQt5'])
else:
    # not available or not working under Python3:
    includes.extend(['UserString', 'ioLabs', 'FileDialog'])
    packages.extend(['PyQt4', 'labjack', 'rusocsci'])
    # is available but py2app can't seem to find it:
    packages.extend(['OpenGL'])

setup(
    app=['psychopy/app/psychopyApp.py'],
    options=dict(py2app=dict(
            includes=includes,
            packages=packages,
            excludes=['bsddb', 'jinja2', 'IPython','ipython_genutils','nbconvert',
                      'libsz.2.dylib', 'pygame',
                      # 'stringprep',
                      'functools32',
                      ],  # anything we need to forcibly exclude?
            resources=resources,
            argv_emulation=True,
            site_packages=True,
            frameworks=frameworks,
            iconfile='psychopy/app/Resources/psychopy.icns',
            plist=dict(
                  CFBundleIconFile='psychopy.icns',
                  CFBundleName               = "PsychoPy",
                  CFBundleShortVersionString = version,  # must be in X.X.X format
                  CFBundleVersion            = version,
                  CFBundleExecutable         = "PsychoPy",
                  CFBundleIdentifier         = "org.opensciencetools.psychopy",
                  CFBundleLicense            = "GNU GPLv3+",
                  NSHumanReadableCopyright   = "Open Science Tools Limited",
                  CFBundleDocumentTypes=[dict(CFBundleTypeExtensions=['*'],
                                              CFBundleTypeRole='Editor')],
                  LSEnvironment=dict(PATH="/usr/local/git/bin:/usr/local/bin:"
                                          "/usr/local:/usr/bin:/usr/sbin"),
            ),
    ))  # end of the options dict
)


# ugly hack for opencv2:
# As of opencv 2.4.5 the cv2.so binary used rpath to a fixed
# location to find libs and even more annoyingly it then appended
# 'lib' to the rpath as well. These were fine for the packaged
# framework python but the libs in an app bundle are different.
# So, create symlinks so they appear in the same place as in framework python
rpath = "dist/PsychoPy.app/Contents/Resources/"
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
