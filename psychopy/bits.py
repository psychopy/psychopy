# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import logging
#deprecated warning present since 1.60.00
logging.error("""
DEPRECATED: In future versions of PsychoPy you will need to call:
    from psychopy.hardware.crs import bits
rather than:
    from psychopy import bits""")
    
from psychopy.hardware.crs.bits import *
