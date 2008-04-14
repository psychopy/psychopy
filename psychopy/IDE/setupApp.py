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
packageData = []
if platform=='win32':
    #you need the c extension for bits++ if you want to change bits modes, but not otherwise
    #cExtensions.append(Extension('psychopy.ext._bits',
    #sources = [os.path.join('psychopy','ext','_bits.c')],
    #libraries=['bits']))
    import py2exe
    cExtensions.append(Extension('psychopy.ext._win32',
    sources = [os.path.join('psychopy','ext','_win32.c')],
    library_dirs=[os.path.join('psychopy','ext')]))
    files = glob.glob('Resources/*')
    for file in files:
        loc, name = os.path.split(file)
        packageData.append( ['Resources', [file]])
elif platform=='darwin':
    cExtensions.append(Extension('psychopy.ext._darwin',
    sources = [os.path.join('psychopy','ext','_darwin.m')],
    extra_link_args=['-framework','OpenGL']))

    resources = glob.glob('Resources/*')
elif platform=='posix':
    pass
##    cExtensions.append(Extension('psychopy.ext.posix',
##                 sources = [os.path.join('psychopy','ext','posix.c')]))


if platform == 'win32':
#    requires.extend(['pymedia'])
    setup(console=["PsychoPyIDE.py"],      
          data_files=packageData)
else:
    setup(app=['PsychoPyIDE.py'],
        options=dict(py2app=dict( excludes=['PIL','pygame','monitors','psychopy'],
                                  resources=resources,
                                  semi_standalone=True,
                                  site_packages=True,
                                  packages=['wx'], #,'PIL','pygame','monitors','psychopy'],
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
# on Mac use:
#python2.4 setup.py bdist_mpkg --readme=psychopy/README.txt
#python2.4 setupApp.py py2app --semi-standalone -s
