#!/usr/bin/env pythonw
from distutils import core, sysconfig
from distutils.core import setup, Extension
import os
from sys import platform

if platform=='darwin':
    #package_data_path='/Library/Python/2.3/psychopy'
    import bdist_mpkg, py2app
    
psychopy_data_path=os.path.join('lib','site-packages','psychopy')
monitors_data_path=os.path.join('lib','site-packages','monitors')

try:
    import psychopy, monitors
    #thisVersion = '0.51'
    thisVersion=psychopy.__version__ #automatically increments if permitted
except:
    thisVersion='0.94.0'
#define the extensions to compile if necess
cExtensions = []

if platform=='win32':
    #you need the c extension for bits++ if you want to change bits modes, but not otherwise
    #cExtensions.append(Extension('psychopy.ext._bits',
                                     #sources = [os.path.join('psychopy','ext','_bits.c')],
                                     #libraries=['bits'])) 
    pass
                                 
elif platform=='darwin':
    cExtensions.append(Extension('psychopy.ext._darwin',
                                 sources = [os.path.join('psychopy','ext','_darwin.m')],
                                 extra_link_args=['-framework','OpenGL']))
    
elif platform=='posix':
    pass
##    cExtensions.append(Extension('psychopy.ext.posix',
##                                 sources = [os.path.join('psychopy','ext','posix.c')]))
    
setup(name="PsychoPy",
      version = thisVersion,
      description = "Psychophysics toolkit for Python",
      author= "Jon Peirce",
      author_email= "jon@peirce.org.uk",
      url="http://www.psychopy.org/",
      packages=['psychopy','psychopy.demos',
        'psychopy.IDE','psychopy.IDE.Resources',
        'psychopy.ext','psychopy.serial',
        'monitors'],
      ext_modules = cExtensions,
      scripts = ['psychopy_post_inst.py'],
      package_data={ 'psychopy': ['*.txt'],
        'psychopy.demos':['*.jpg'],
        'psychopy.IDE': ['*.ico'],
        'psychopy.IDE.Resources': ['*.ico','*.png'],
        'monitors': ['*.ico'],
        'psychopy.serial':['*.txt']
        }                
      )

# on Mac use:
#sudo pythonw setup.py bdist_mpkg --readme=psychopy/README.txt
