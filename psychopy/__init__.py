"""
PsychoPy is a pure Python module using OpenGL, PyGame
and numpy.

To get started see/run the demo scripts.
"""

import string, sys, os, time
try: import numpy
except: pass

__version__ = '1.00.02'#string.split('$Branch: 1.19 $')[1]
__date__ = string.join(string.split('$Date$')[1:3], ' ')
__svn__= '$Id$'
__rev__= '$Revision$'
__author__ = 'Jon Peirce'
__author_email__='jon@peirce.org.uk'
__maintainer_email__='psychopy-users@googlegroups.com'

# these modules are loaded by import psychopy
#from core import *
# these modules are loaded if the user performs
# from psychopy import *
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
    
    #try to import monitors from old location (PsychoPy <0.93 used site-packages/monitors instead)
    import glob, shutil #these are just to copy old calib files across
    try: 
        calibFiles = glob.glob('C:\Python24\Lib\site-packages\monitors\*.calib')
        for thisFile in calibFiles:
            thisPath, fileName = os.path.split(thisFile)
            shutil.copyfile(thisFile, join(appDataLoc,fileName))
    except:
        pass #never mind - the user will have to do it!


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
#sys.stdout = FlushFile(sys.stdout)
