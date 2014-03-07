#!/usr/bin/env python2
"""Requires setuptools and uses the manifest.in file for data files"""

from setuptools import setup, Extension, find_packages
################
import glob, os
from sys import platform, argv

#regenerate __init__.py only if we're in the source repos (not in a source zip file)
try:
    import createInitFile#won't exist in a sdist.zip
    writeNewInit=True
except:
    writeNewInit=False
if writeNewInit:
    #determine what type of dist is being created
    #(install and bdist might do compiliing and then build platform is needed)
    for arg in argv:
        if arg.startswith('bdist') or arg.startswith('install'):
            dist='bdist'
        else: dist='sdist'
    vStr = createInitFile.createInitFile(dist=dist)
else:
    #import the metadata from file we just created (or retrieve previous)
    f = open('psychopy/__init__.py', 'r')
    vStr = f.read()
    f.close()
exec(vStr)

#define the extensions to compile if necess
packages = find_packages()
#for the source dist this doesn't work - use the manifest.in file
dataExtensions = ['*.txt', '*.ico', '*.jpg', '*.gif', '*.png', '*.mov', '*.spec', '*.csv','*.psyexp', '*.xlsx']
dataFiles = []

scripts = ['psychopy/app/psychopyApp.py',
           'psychopy_post_inst.py'] #although post_install only needs installing on win32 it needs packaging in the zip
if platform=='win32':
    #you need the c extension for bits++ if you want to change bits modes, but not otherwise
    #cExtensions.append(Extension('psychopy.ext._bits',
    #sources = [os.path.join('psychopy','ext','_bits.c')],
    #libraries=['bits']))
    pass
elif platform=='darwin':
    #from py2app import bdist_mpkg
    dataExtensions.extend(['*.icns'])
elif platform=='posix':
    dataFiles += [('share/applications', ['psychopy/app/Resources/psychopy.desktop']),
                  ('share/pixmaps', ['psychopy/app/Resources/psychopy.png'])]


setup(name="PsychoPy",
    packages=packages,
    scripts = scripts,
    include_package_data =True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': dataExtensions,
    },
    data_files = dataFiles,
    #metadata
    version = __version__,
    description = "Psychophysics toolkit for Python",
    long_description = "PsychoPy uses OpenGL and Python to create a toolkit" + \
        " for running psychology/neuroscience/psychophysics experiments",
    author= __author__,
    author_email= __author_email__,
    maintainer_email= __maintainer_email__,
    url=__url__,
    license=__license__,
    download_url=__downloadUrl__,
    classifiers=['Development Status :: 4 - Beta',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python'],
    )

#remove unwanted info about this system post-build
if writeNewInit:
    createInitFile.createInitFile(dist=None)
