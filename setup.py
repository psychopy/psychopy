#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Install PsychoPy to your current Python dist, including requirements

usage::

    pip install psychopy
    pip install .  # to install from within the repository
    pip install -e .  # to install a link instead of copying the files

"""

from setuptools import setup, find_packages
################
import os
from os.path import exists, join
from sys import platform, argv, version_info


PY3 = version_info >= (3, 0)

# use pip module to parse the
required = ['requests[security]',
            'numpy', 'scipy', 'matplotlib', 'pandas', 'pillow',
            'wxPython', 'pyglet', 'pygame', 'configobj', 'pyopengl',
            'soundfile', 'sounddevice',
            'python-bidi', 'cffi',
            'future', 'json_tricks',
            'pyosf',
            'xlrd', 'openpyxl',  # MS Excel
            'pyserial', 'pyparallel',
            'pyyaml', 'gevent', 'msgpack-python', 'psutil', 'tables', 'zmq',
            'moviepy']

# `opencv` package should be installed via conda instead
# cf. https://github.com/ContinuumIO/anaconda-issues/issues/1554
if 'CONDA_PREFIX' not in os.environ:
    required.append('opencv-python')

# some optional dependencies
if platform == 'win32':
    required.extend(['pypiwin32'])
if platform == 'darwin':
    required.extend(['pyobjc-core', 'pyobjc-framework-Quartz'])

# `pyqt` package should be installed via conda instead
# cf. https://github.com/ContinuumIO/anaconda-issues/issues/1554
if PY3 and ('CONDA_PREFIX' not in os.environ):
    required.append('pyqt5')

# for dev you also want:
# 'sphinx','pytest'
# 'lxml', 'pyopengl'


# compress psychojs to a zip file for packaging
# only takes 0.5s but could skip if you prefer
if ('-noJS' in argv) or not exists('psychojs'):
    pass
else:
    import shutil
    shutil.make_archive(join('psychopy', 'psychojs'),
                        'zip', 'psychojs')

# regenerate __init__.py only if we're in the source repos (not in a source zip file)
try:
    import createInitFile  # won't exist in a sdist.zip
    writeNewInit=True
except:
    writeNewInit=False
if writeNewInit:
    # determine what type of dist is being created
    # (install and bdist might do compiliing and then build platform is needed)
    for arg in argv:
        if arg.startswith('bdist') or arg.startswith('install'):
            dist='bdist'
        else:
            dist='sdist'
    vStr = createInitFile.createInitFile(dist=dist)
else:
    # import the metadata from file we just created (or retrieve previous)
    f = open('psychopy/__init__.py', 'r')
    vStr = f.read()
    f.close()
installing = True
exec(vStr)

# define the extensions to compile if necess
packages = find_packages()
# for the source dist this doesn't work - use the manifest.in file
dataExtensions = ['*.txt', '*.ico', '*.jpg', '*.gif', '*.png', '*.mov',
                  '*.spec', '*.csv', '*.psyexp', '*.xlsx', '.zip']
dataFiles = ['psychopy/psychojs.zip']

# post_install only needs installing on win32 but needs packaging in the zip
scripts = ['psychopy/app/psychopyApp.py',
           'psychopy_post_inst.py']
if platform=='win32':
    pass
elif platform=='darwin':
    dataExtensions.extend(['*.icns'])
elif platform=='posix':
    dataFiles += [('share/applications',
                   ['psychopy/app/Resources/psychopy.desktop']),
                  ('share/pixmaps',
                   ['psychopy/app/Resources/psychopy.png'])]


setup(name="PsychoPy",
    packages=packages,
    scripts = scripts,
    include_package_data =True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': dataExtensions,
    },
    data_files = dataFiles,
    install_requires = required,
    # metadata
    version = __version__,
    description = "Psychology experiment software in Python",
    long_description = ("PsychoPy uses OpenGL and Python to create a toolkit "
                        "for running psychology/neuroscience/psychophysics "
                        "experiments"),
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

