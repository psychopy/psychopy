"""Interface to `ioLab button box <http://www.iolab.co.uk>`_

This is currently a simple import of the `ioLab python library 
<http://github.com/ioLab/python-ioLabs>`_. 
That needs to be installed (but is included in the *Standalone* distributions
of PsychoPy as of version 1.62.01).

installation::

    easy_install iolabs

usage::

    from psychopy.hardware import ioLabs
    
for examples see the demos menu of the PsychoPy Coder or go to the URL above.

"""
# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from psychopy import logging
try:
    from ioLabs import *
except:
    msg="""Failed to import the ioLabs library. If you're using your own copy of 
python (not the Standalone distribution of PsychoPy) then try installing it with:
    > easy_install ioLabs
    
"""
    logging.error(msg)
