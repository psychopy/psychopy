"""
PsychoPy is a pure Python module using OpenGL, PyGame
and numpy.

To get started see/run the demo scripts.
"""

import string, sys, os, time
try: import numpy
except: pass

__version__ = '1.00.05'#string.split('$Branch: 1.19 $')[1]
__date__ = string.join(string.split('$Date$')[1:3], ' ')
__svn__= '$Id$'
__rev__= '$Revision$'
__author__ = 'Jon Peirce'
__author_email__='jon@peirce.org.uk'
__maintainer_email__='psychopy-users@googlegroups.com'

__all__ = ["gui", "misc", "visual", "core", "event", "data", "filters"]

#set and create (if necess) the application data folder
#this will be the 
#   Linux/Mac:  ~/PsychoPy
#   win32:   <UserDocs>/Application Data/.PsychoPy
join = os.path.join
if sys.platform=='win32':
    appDataLoc = join(os.environ['USERPROFILE'],'.PsychoPy') #this is the folder that this file is stored in
else:
    appDataLoc = join(os.environ['HOME'],'.PsychoPy') #this is the folder that this file is stored in
if not os.path.isdir(appDataLoc):
    os.mkdir(appDataLoc)
    