#!/usr/local/bin/python
"""Requires setuptools and uses the manifest.in file for data files"""

from setuptools import setup, Extension
################
import glob, os
from sys import platform

import psychopy, monitors
thisVersion=psychopy.__version__

#define the extensions to compile if necess
packages = ['psychopy','psychopy.ext','psychopy.serial','psychopy.demos',
              'PsychoPyIDE','PsychoPyIDE.Resources','monitors']

dataExtensions = ['*.txt', '*.ico', '*.jpg', '*.gif', '*.png']

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
    version = thisVersion,
    description = "Psychophysics toolkit for Python",
    author= psychopy.__author__,
    author_email= psychopy.__author_email__,
    maintainer_email= psychopy.__maintainer_email__,
    url="http://www.psychopy.org/",
    download_url="http://sourceforge.net/project/showfiles.php?group_id=48949&package_id=42326",
    packages=packages,
    scripts = ['psychopy_post_inst.py'],
    include_package_data =True,
    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': dataExtensions
    },
    #install_requires = dependencies,
    #dependency_links = ["http://www.python.org/pypi/",
    #"http://sourceforge.net/project/showfiles.php?group_id=71702",#ctypes
    #"http://sourceforge.net/project/showfiles.php?group_id=5988",#pyopengl
    #]
    )

# on Mac use:
#sudo python2.4 setup.py bdist_mpkg --readme=psychopy/README.txt
