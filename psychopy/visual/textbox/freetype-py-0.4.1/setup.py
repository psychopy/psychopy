#!/usr/bin/env python
# -----------------------------------------------------------------------------
#  FreeType high-level python API - copyright 2011 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
# -----------------------------------------------------------------------------
from distutils.core import setup

setup( name        = 'freetype-py',
       version     = '0.4.1',
       description = 'Freetype python bindings',
       author      = 'Nicolas P. Rougier',
       author_email= 'Nicolas.Rougier@inria.fr',
       url         = 'http://code.google.com/p/freetype-py/',
       packages    = ['freetype', 'freetype.ft_enums'],
       data_files  = ['examples/Vera.ttf',],
       classifiers = [
          'Development Status :: 5 - Production/Stable',
          'Environment :: X11 Applications',
          'Environment :: MacOS X',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: MacOS',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Graphics',
          ],
     )
