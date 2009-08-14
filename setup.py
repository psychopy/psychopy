#!/usr/bin/env python
"""Requires setuptools and uses the manifest.in file for data files"""

from setuptools import setup, Extension
################
import glob, os
from sys import platform

import psychopy
thisVersion=psychopy.__version__

#define the extensions to compile if necess
packages = ['psychopy','psychopy.ext','psychopy.serial','psychopy.demos',
			'psychopy.monitors',
            'psychopy.app','psychopy.app.coder',
			'psychopy.app.builder','psychopy.app.builder.components',
			'psychopy.app.Resources',
			]

dataExtensions = ['*.txt', '*.ico', '*.jpg', '*.gif', '*.png', '*.mpg']

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
    pass

setup(name="PsychoPy",
    packages=packages,
    scripts = ['psychopy_post_inst.py'],
    include_package_data =True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': dataExtensions
    },
    #metadata
    version = thisVersion,
    description = "Psychophysics toolkit for Python",
    long_description = "PsychoPy uses OpenGL and Python to create a toolkit"
	  " for running psychology/neuroscience/psychophysics experiments",
    author= psychopy.__author__,
    author_email= psychopy.__author_email__,
    maintainer_email= psychopy.__maintainer_email__,
    url="http://www.psychopy.org/",
    license="BSD",
    download_url="http://code.google.com/p/psychopy/",
    classifiers=['Development Status :: 4 - Beta',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python'],
    #install_requires = dependencies,
    #dependency_links = ["http://www.python.org/pypi/",
    #"http://sourceforge.net/project/showfiles.php?group_id=71702",#ctypes
    #"http://sourceforge.net/project/showfiles.php?group_id=5988",#pyopengl
    #]
    )

# on Mac use:
#sudo python2.4 setup.py bdist_mpkg --readme=psychopy/README.txt
