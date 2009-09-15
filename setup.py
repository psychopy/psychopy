#!/usr/bin/env python
"""Requires setuptools and uses the manifest.in file for data files"""

from setuptools import setup, Extension, find_packages
################
import glob, os
from sys import platform

import psychopy
thisVersion=psychopy.__version__

#define the extensions to compile if necess
packages = find_packages()
#for the source dist this doesn't work - use the manifest.in file
dataExtensions = ['*.txt', '*.ico', '*.jpg', '*.gif', '*.png', '*.mpg', '*.cfg', '*.csv','*.psyexp']

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
	# No need for win32 postinst script in Debian
    # scripts = ['psychopy_post_inst.py'],
    include_package_data =True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': dataExtensions,
    },
    #metadata
    version = thisVersion,
    description = "Psychophysics toolkit for Python",
    long_description = "PsychoPy uses OpenGL and Python to create a toolkit" + \
        " for running psychology/neuroscience/psychophysics experiments",
    author= psychopy.__author__,
    author_email= psychopy.__author_email__,
    maintainer_email= psychopy.__maintainer_email__,
    url=psychopy.__url__,
    license=psychopy.__license__,
    download_url=psychopy.__downloadUrl__,
    classifiers=['Development Status :: 4 - Beta',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: Linux',
          'Programming Language :: Python'],
    )
