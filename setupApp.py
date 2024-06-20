#!/usr/bin/env python
################
# see notes at bottom for requirements

import glob
import os
import sys
from sys import platform
import setuptools  # noqa: setuptools complains if it isn't implicitly imported before distutils
from distutils.core import setup
from packaging.version import Version
import bdist_mpkg  # noqa: needed to build bdist, even though not explicitly used here
import py2app  # noqa: needed to build app bundle, even though not explicitly used here
from ctypes.util import find_library
import importlib
import building.compile_po

import psychopy
version = psychopy.__version__

building.compile_po.compilePoFiles()

# regenerate __init__.py only if we're in the source repos (not in a zip file)
try:
    from building import createInitFile  # won't exist in a sdist.zip
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

resources = glob.glob('psychopy/app/Resources/*')
frameworks = [ # these installed using homebrew
              find_library("libevent"),
              find_library("libmp3lame"),
              find_library("libglfw"),
              # libffi comes in the system
              "/usr/local/opt/libffi/lib/libffi.dylib",
              ]
opencvLibs = glob.glob(os.path.join(sys.exec_prefix, 'lib', 'libopencv*.2.4.dylib'))
frameworks.extend(opencvLibs)

import macholib
#print("~"*60 + "macholib version: "+macholib.__version__)

if Version(macholib.__version__) <= Version('1.7'):
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

includes = ['_sitebuiltins',  # needed for help()
            'imp', 'subprocess', 'shlex',
            'shelve',  # for scipy.io
            '_elementtree', 'pyexpat',  # for openpyxl
            'pyo', 'greenlet', 'zmq', 'tornado',
            'psutil',  # for iohub
            'tobii_research',  # need tobii_research file and tobiiresearch pkg
            'soundfile', 'sounddevice', 'readline',
            'xlwt',  # writes excel files for pandas
            'msgpack_numpy',
            'configparser',
            'ntplib',  # for egi-pynetstation
            ]
packages = ['pydoc',  # needed for help()
            'setuptools', 'wheel', # for plugin installing
            'wx', 'psychopy',
            'PyQt6',
            'pyglet', 'pytz',
            'scipy', 'matplotlib', 'openpyxl', 'pandas',
            'xml', 'xmlschema',
            'ffpyplayer', 'cython', 'AVFoundation',
            'imageio', 'imageio_ffmpeg',
            '_sounddevice_data', '_soundfile_data',
            'cffi', 'pycparser',
            'PIL',  # 'Image',
            'freetype',
            'objc', 'Quartz', 'AppKit', 'Cocoa',
            'Foundation', 'CoreFoundation',
            'pkg_resources',  # needed for objc
            'requests', 'certifi', 'cryptography',
            'json_tricks',  # allows saving arrays/dates in json
            'git', 'gitlab',
            'msgpack', 'yaml', 'gevent',  # for ioHub
            'astunparse', 'esprima',  # for translating/adapting py/JS
            'metapensiero.pj', 'dukpy', 
            'jedi', 'parso',
            'bidi', 'arabic_reshaper', 'charset_normalizer', # for (natural) language conversions
            'ujson',  # faster than built-in json
            'six',  # needed by configobj
            # hardware
            'serial',
            # handy science tools
            'tables',  # 'cython',
            # these aren't needed, but liked
            'pylsl', 'pygaze',
            #'smite',  # https://github.com/marcus-nystrom/SMITE (not pypi!)
            'cv2',
            'questplus',
            'psychtoolbox',
            'h5py',
            'markdown_it',
            'zeroconf', 'ifaddr',  # for pupillabs plugin (fail to build)
            'websocket', # dependency for emotiv that doesn't install nicely from plugins
            ]

# Add packages that older PsychoPy (<=2023.1.x) shipped, for useVersion() compatibility
# In PsychoPy 2023.2.0 these packages were removed from Standalone Py3.10+ builds
if sys.version_info < (3, 9):
    packages.extend(
        [
            'moviepy', 
            'OpenGL', 'glfw',
            'googleapiclient',
            'badapted', #'darc_toolbox',  # adaptive methods from Ben Vincent
            'egi_pynetstation', 'pylink', 'tobiiresearch',
            'pyxid2', 'ftd2xx',  # ftd2xx is used by cedrus
            'Phidget22',
            'hid',
            'macropy',
        ]
    )
    packages.append('PyQt5')
    packages.remove('PyQt6')  # PyQt6 is not compatible with earlier PsychoPy versions

# check the includes and packages are all available
missingPkgs = []
pipInstallLines = ''
packagePipNames = { # packages that are imported as one thing but installed as another
    'OpenGL': 'pyopengl',
    'opencv': 'opencv-python',
    'googleapiclient': 'google-api-python-client',
    'macropy': 'macropy3',

}
for pkg in includes+packages:
    
    try:
        importlib.import_module(pkg)
    except ModuleNotFoundError:
        if pkg in packagePipNames:
            missingPkgs.append(packagePipNames[pkg])
        elif pkg == 'pylink':
            pipInstallLines += 'pip install --index-url=https://pypi.sr-support.com sr-research-pylink\n'
        else:
            missingPkgs.append(pkg)
    except OSError as err:
        if 'libftd2xx.dylib' in str(err):
            raise ImportError(f"Missing package: ftd2xx. Please install the FTDI D2XX drivers from "
                              "https://www.ftdichip.com/Drivers/D2XX.htm")
    except ImportError as err:
        if 'eyelink' in str(err):
            raise ImportError(f"It looks like the Eyelink dev kit is not installed "
                              "https://www.sr-research.com/support/thread-13.html")

if missingPkgs or pipInstallLines:
    helpStr = f"You're missing some packages to include in standalone. Fix with:\n"
    if missingPkgs:
        helpStr += f"pip install {' '.join(missingPkgs)}\n"
    helpStr += pipInstallLines
    raise ImportError(helpStr)
else:
    print("All packages appear to be present. Proceeding to build...")

setup(
    app=['psychopy/app/psychopyApp.py'],
    options=dict(py2app=dict(
            includes=includes,
            packages=packages,
            excludes=['bsddb', 'jinja2', 'IPython','ipython_genutils','nbconvert',
                      'tkinter', 'Tkinter', 'tcl',
                      'libsz.2.dylib', 'pygame',
                      # 'stringprep',
                      'functools32',
                      'sympy',
                      '/usr/lib/libffi.dylib',
                      'libwebp.7.dylib'
                      ],  # anything we need to forcibly exclude?
            resources=resources,
            argv_emulation=False,  # must be False or app bundle pauses (py2app 0.21 and 0.24 tested)
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
                  CFBundleURLTypes=[dict(CFBundleURLName='psychopy',  # respond to psychopy://
                                         CFBundleURLSchemes='psychopy',
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
