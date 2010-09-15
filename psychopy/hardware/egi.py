"""Interface to EGI Netstation

This is currently a simple import of pynetstation (http://code.google.com/p/pynetstation/)
pynetstation needs to be installed - it is included in the Standalone distributions
of PsychoPy as of version 1.62.01.

usage::
    from psychopy.hardware import egi
    
For an example see the demos menu of the PsychoPy Coder
For further documentation see the pynetstation website

--------
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import log
try:
    from egi import *
except:
    msg="""Failed to import egi (pynetstation). If you're using your own copy of 
python (not the Standalone distribution of PsychoPy) then try installing pynetstation.
See:
    http://code.google.com/p/pynetstation/wiki/Installation
    
"""
    log.error(msg)