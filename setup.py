#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Install PsychoPy to your current Python dist, including requirements

usage::

    pip install psychopy
    pip install .  # to install from within the repository
    pip install -e .  # to install a link instead of copying the files

"""

from setuptools import setup, find_packages
from setuptools.config import read_configuration
import os
from os.path import exists, join
from sys import platform, argv


with open('version') as f:
    version = f.read().strip()

#
# Special handling for Anaconda / Miniconda
#

required = read_configuration('setup.cfg')['options']['install_requires']

# OpenCV
# Naming conflict with PyPI package.
# `opencv` package should be installed via conda instead
if 'CONDA_PREFIX' in os.environ:
    required.remove('opencv-python')

# PyQt
# Naming conflict with PyPI package.
# `pyqt` package should be installed via conda instead
# cf. https://github.com/ContinuumIO/anaconda-issues/issues/1554
if 'CONDA_PREFIX' in os.environ:
    required.remove('pyqt5')

# compress psychojs to a zip file for packaging
# only takes 0.5s but could skip if you prefer
if ('-noJS' in argv) or not exists('psychojs') or ('clean' in argv):
    pass
else:
    import shutil
    shutil.make_archive(join('psychopy', 'psychojs'),
                        'zip', 'psychojs')

# regenerate __init__.py only if we're in the source repos (not in a source
# zip file)
try:
    from building import createInitFile   # won't exist in a sdist.zip
    writeNewInit = True
except ImportError:
    writeNewInit = False

if writeNewInit:
    # determine what type of dist is being created
    # (install and bdist might do compiliing and then build platform is needed)
    for arg in argv:
        if arg.startswith('bdist') or arg.startswith('install'):
            dist = 'bdist'
        else:
            dist = 'sdist'
    createInitFile.createInitFile(dist=dist)

packages = find_packages()

# define the extensions to compile if necessary
# for the source dist this doesn't work - use the manifest.in file
dataExtensions = ['*.txt', '*.ico', '*.jpg', '*.gif', '*.png', '*.mov',
                  '*.spec', '*.csv', '*.psyexp', '*.xlsx', '.zip']
dataFiles = []

if platform == 'win32':
    pass
elif platform == 'darwin':
    dataExtensions.extend(['*.icns'])
elif platform == 'posix':
    dataFiles += [('share/applications',
                   ['psychopy/app/Resources/psychopy.desktop']),
                  ('share/pixmaps',
                   ['psychopy/app/Resources/psychopy.png'])]

setup(name='PsychoPy',
      packages=packages,
      include_package_data=True,
      package_data={
          # If any package contains *.txt or *.rst files, include them:
          '': dataExtensions,
      },
      data_files=dataFiles,
      install_requires=required,
      version=version)

# remove unwanted info about this system post-build
if writeNewInit:
    createInitFile.createInitFile(dist=None)
