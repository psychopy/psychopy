"""
PsychoPy is a pure Python module using OpenGL, PyGame
and numpy.

To get started see/run the demo scripts.
"""

import string, sys
try: import numpy
except: pass

__version__ = '0.93.6'#string.split('$Branch: 1.19 $')[1]
__date__ = string.join(string.split('$Date: 2005/08/01 15:05:34 $')[1:3], ' ')
__author__ = 'Jon Peirce'
__author_email__='jon@peirce.org.uk'
__maintainer_email__='psychpy-users@lists.sourceforge.net'

# these modules are loaded by import psychopy
from core import *
# these modules are loaded if the user performs
# from psychopy import *
__all__ = ["gui", "misc", "visual", "core", "event", "sound", "data", "filters"]

#force stdout to flush after every print statement.
#this is useful for PsychoPy IDE but may slow things down for fast drawing if you 
#print a lot. 
class FlushFile: #we want to force flushing
    def __init__(self, f):
        self.orig = f
    def write(self, txt):
        self.orig.write(txt)
        self.orig.flush()
    def flush(self):
        self.orig.flush()
sys.stdout = FlushFile(sys.stdout)
